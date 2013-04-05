from lxml import etree
import xmltodict
import requests
import time
import errors


def bfs_search_results(d, searches, results):
    '''find all keys in searches, and save values to results.
    WARNING: deletes keys from searches dict!'''
    try:
        l = d.items()
    except AttributeError:
        return
    for k, v in l:
        try:
            f = searches[k] # found a match
        except KeyError:
            continue
        if callable(f): # let f generate whatever results it wants
            try:
                r = f(v, k, results)
            except KeyError: # didn't find what it wanted, so ignore
                pass
            else:
                results.update(r)
        elif f: # save with alias key
            results[f] = v
        else: # save with original key
            results[k] = v
        del searches[k]
        if not searches: # nothing more to do
            return
    for k, v in l:
        bfs_search_results(v, searches, results)
        if not searches: # nothing more to do
            return

def bfs_search(d, searches):
    'find all keys in searches, and save values to results.'
    results = {}
    bfs_search_results(d, searches.copy(), results)
    return results

def get_val(v, k, r):
    return {k:v['#text']}

def get_author_names(v, k, r):
    return {'authorNames':[d['ForeName'] + ' ' + d['LastName']
                           for d in list_wrap(v)]}

def get_abstract(v, k, r):
    'properly handle multi-part AbstractText'
    if isinstance(v, list):
        l = [('%s: %s' % (d.get('@Label', ''), d['#text'])) for d in v]
        return {'summary':'  '.join(l)}
    else:
        return {'summary':v}

def list_wrap(v):
    if isinstance(v, list):
        return v
    else:
        return [v]

def get_doi(v, k, r):
    for d in list_wrap(v):
        if d.get('@IdType', '') == 'doi':
            return {'doi':d['#text']}
    raise KeyError('no doi found')

pubmedExtracts = dict(ArticleTitle='title', AbstractText=get_abstract,
                      PMID=lambda v,k,r:{'id':v['#text']},
                      ArticleDate=lambda v,k,r:{'year':v['Year']},
                      ISOAbbreviation='journal', ISSN=None,
                      Affiliation='affiliation', Author=get_author_names,
                      ArticleId=get_doi)

def normalize_pubmed_dict(d, extracts=pubmedExtracts):
    return bfs_search(d, extracts)


def extract_subtrees(xml, extractDicts):
    'extract subtrees as OrderedDict objects'
    d = {}
    doc = xmltodict.parse(xml)
    for xd in extractDicts: # extract desired subtrees
        dd = doc
        required = False
        for k in xd:
            if k.startswith('!'):
                required = True
                k = k[1:]
            if k == '*': # copy all items in dd to d
                d.update(dd)
                k = None # nothing further to save
                break
            try: # go one level deeper in doc
                dd = dd[k]
            except (TypeError,KeyError):
                if required:
                    raise KeyError('required subtree missing')
                k = None # nothing to save
                break
        if k: # save to result dictionary
            d[k] = dd
    return d

def dict_from_xml(xml, **kwargs):
    root = etree.XML(xml)
    d = {}
    for k,v in kwargs.items():
        if v is None:
            continue
        if v[0] == '!': # required field
            required = True
            v = v[1:]
        else:
            required = False
        f = v.split('.')
        o = root.find('.//' + f[0]) # search for top field
        for subfield in f[1:]: # contains subfield
            if o is None:
                break
            o = o.find(subfield)
        if o is not None:
            d[k] = o.text
        elif required:
            raise KeyError('required field not found: ' + v)
    return d, root

def pubmed_dict_from_xml(xml, title='!ArticleTitle',
                         summary='AbstractText', id='!PMID',
                         year='ArticleDate.Year', journal='ISOAbbreviation',
                         ISSN='ISSN', affiliation='Affiliation',
                         extractDicts=('!PubmedArticleSet.PubmedArticle.MedlineCitation'.split('.'),),
                         **kwargs):
    'extract fields + authorNames + DOI from xml, return as dict'
    d, root = dict_from_xml(xml, title=title, summary=summary, id=id,
                            year=year, journal=journal, ISSN=ISSN,
                            affiliation=affiliation, **kwargs)
    d.update(extract_subtrees(xml, extractDicts))
    authorNames = [] # extract list of author names
    for o in root.findall('.//Author'):
        authorNames.append(o.find('ForeName').text + ' ' +
                           o.find('LastName').text)
    d['authorNames'] = authorNames
    for o in root.findall('.//ELocationID'): # extract DOI
        if o.get('EIdType', '') == 'doi':
            d['doi'] = o.text
    if 'doi' not in d:
        for o in root.findall('.//ArticleId'): # extract DOI
            if o.get('IdType', '') == 'doi':
                d['doi'] = o.text
    return d

def query_pubmed(uri='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi',
                 tool='spnet', email='leec@chem.ucla.edu', db='pubmed',
                 retmode='xml', nretry=3, acceptStatus=(200,),
                 retryStatus=(404, 502, 503), retryTime=1, **kwargs):
    '''perform a query using eutils API, retrying if service unavailable
    WARNING: eutils is flaky!  lots of 503s, 502, 404 (when searching
    for "cancer"!?!), who knows what else!'''
    d = kwargs.copy()
    if tool:
        d['tool'] = tool
    if email:
        d['email'] = email
    params = dict(db=db, retmode=retmode, **d)
    for i in range(nretry): # often service unavailable (503), so retry
        r = requests.get(uri, params=params)
        if r.status_code in acceptStatus: # success
            return r.content
        elif r.status_code == 400: # badly formed query
            raise KeyError('invalid query: ' + str(kwargs))
        elif r.status_code not in retryStatus: # unexpected status
            raise errors.UnexpectedStatus('query_pubmed: status=%d, query=%s'
                                   % (r.status_code, str(d)))
        if retryTime:
            time.sleep(retryTime)
    raise errors.TimeoutError('%s still unavailable after %d retries'
                              % (uri, nretry))

def search_pubmed(term, uri='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
                  **kwargs):
    return query_pubmed(uri, term=term, **kwargs)
    

def query_pubmed_id(pubmedID, **kwargs):
    return query_pubmed(id=pubmedID, **kwargs)

def get_pubmed_dict(pubmedID):
    'get paper data for specified pubmed ID, from NCBI eutils API'
    xml = query_pubmed_id(pubmedID)
    return pubmed_dict_from_xml(xml)

def get_training_abstracts(terms=('cancer', 'transcription', 'evolution',
                                  'physics', 'statistics', 'review'),
                           **kwargs):
    'generate a training set of 20 abstracts per search term'
    for t in terms:
        xml = search_pubmed(t, usehistory='y', tool=None, email=None,
                            **kwargs)
        d, root = dict_from_xml(xml, WebEnv='!WebEnv', query_key='!QueryKey')
        xml = query_pubmed(retstart='0', retmax='20', tool=None, email=None,
                           **d)
        root = etree.XML(xml)
        for o in root.findall('.//AbstractText'):
            yield o.text

class PubmedSearch(object):
    def __init__(self, searchString, block_size=20,
                 email='leec@chem.ucla.edu', **kwargs):
        self.block_size =  block_size
        self.email = email
        xml = search_pubmed(searchString, usehistory='y', tool='spnet',
                            email=email, retmax=str(block_size), **kwargs)
        d, root = dict_from_xml(xml, WebEnv='!WebEnv', query_key='!QueryKey')
        self.queryArgs = d
    def __call__(self, searchString, start=0, block_size=20):
        'get list of PubmedArticle dicts'
        xml = query_pubmed(retstart=str(start), retmax=str(block_size),
                           tool='spnet', email=self.email, **self.queryArgs)
        d = extract_subtrees(xml, ('PubmedArticleSet.PubmedArticle'.split('.'),))
        l = []
        for dd in d['PubmedArticle']:
            dd.update(normalize_pubmed_dict(dd))
            l.append(dd)
        return l

