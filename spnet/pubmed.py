from lxml import etree
import xmltodict
import requests

def extract_subtrees(xml, extractDicts):
    'extract subtrees as OrderedDict objects'
    d = {}
    doc = xmltodict.parse(xml)
    for xd in extractDicts: # extract desired subtrees
        dd = doc
        for k in xd:
            if k == '*': # copy all items in dd to d
                d.update(dd)
                k = None # nothing further to save
                break
            try: # go one level deeper in doc
                dd = dd[k]
            except KeyError:
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

def pubmed_dict_from_xml(xml, title='ArticleTitle',
                         summary='AbstractText', id='PMID',
                         year='ArticleDate.Year', journal='ISOAbbreviation',
                         ISSN='ISSN', affiliation='Affiliation',
                         extractDicts=('PubmedArticleSet.PubmedArticle.MedlineCitation'.split('.'),),
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
    return d

def query_pubmed(uri='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi',
                    tool='example', email='leec@chem.ucla.edu', db='pubmed',
                    retmode='xml', **kwargs):
    d = kwargs.copy()
    if tool:
        d['tool'] = tool
    if email:
        d['email'] = tool
    params = dict(db=db, retmode=retmode, **d)
    r = requests.get(uri, params=params)
    return r.content

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

