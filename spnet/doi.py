import urllib
import requests
from lxml import etree
import unicodedata

def map_to_shortdoi(doi, uri='http://shortdoi.org/'):
    'find shortDOI for the specified DOI'
    s = urllib.urlencode(dict(a=doi))[2:]
    r = requests.get(uri + s, params=dict(format='json'))
    if r.status_code == 400:
        raise KeyError('DOI not found: ' + doi)
    return r.json()['ShortDOI'].split('/')[-1]


def decode_url_chars(s):
    'replace %hh by ASCII char, and %% by %'
    out = ''
    while s:
        try:
            i = s.index('%')
        except ValueError:
            return out + s
        out = out + s[:i]
        if s[i + 1] == '%':
            out = out + '%'
            s = s[i + 2:]
        else:
            out = out + chr(int(s[i + 1:i + 3], 16))
            s = s[i + 3:]
    return out
    

def map_to_doi(shortdoi, uri='http://doi.org/'):
    'find DOI for the specified shortDOI'
    r = requests.get(uri + shortdoi, allow_redirects=False)
    if r.status_code == 301:
        url = r.headers['location']
        i = url.index('doi.org/')
        return decode_url_chars(url[i + 8:]) # return the DOI
    elif r.status_code == 404:
        raise KeyError('shortdoi not found: ' + shortdoi)
    raise ValueError('unexpected status_code %d' % r.status_code)

def find_doi_metadata(doi, uri='http://www.crossref.org/openurl/', pid='leec@chem.ucla.edu', format='unixref', noredirect='true', **kwargs):
    params = dict(id=doi, pid=pid, format=format, noredirect=noredirect,
                  **kwargs)
    r = requests.get(uri, params=params)
    return r.content # lxml can't handle unicode encoded...

def doi_dict_from_xml(xml, title='title', year='publication_date.year',
                      volume='journal_volume.volume',
                      source_url='doi_data.resource', **kwargs):
    import pubmed
    d, root = pubmed.dict_from_xml(xml, title=title, year=year, volume=volume,
                                   source_url=source_url, **kwargs)
    authorNames = [] # extract list of author names
    for o in root.findall('.//person_name'):
        authorNames.append(o.find('given_name').text + ' ' +
                           o.find('surname').text)
    d['authorNames'] = authorNames
    return d

def extract_html_elements(html, minLength=100):
    'get text elements from HTML doc above specified size, biggest first'
    root = etree.HTML(html)
    l = [(len(e.text), e.text) for e in root.iterdescendants() if e.text
         and len(e.text) > minLength]
    l.sort(reverse=True)
    return l

# trick for counting non-letter/space characters in a string
textTrans = ''.join(['a' if chr(c).isalpha() or chr(c).isspace() else '_'
                     for c in range(256)])

def count_nonletterspace(t):
    'get count of chars that are not letter or space, len(t)'
    if isinstance(t, unicode): # force it to simple string
        t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore')
    return t.translate(textTrans).count('_'), float(len(t))


def find_abstract(uri, minLength=200, maxFrac=0.11):
    'abstract should have the lowest fraction of non-letter/space chars'
    r = requests.get(uri)
    l = extract_html_elements(r.content, minLength)
    m = []
    for c, t in l:
        f, total = count_nonletterspace(t) 
        m.append((f / total, t))
    m.sort()
    if m[0][0] <= maxFrac:
        return m[0][1]
    else:
        raise KeyError('(no abstract found)')

def get_pubmed_and_doi(doi):
    import pubmed
    xml = find_doi_metadata(doi)
    doiDict = doi_dict_from_xml(xml)
    xml = pubmed.search_pubmed(doi, retmax='1', field='LID')
    try:
        d, root = pubmed.dict_from_xml(xml, pubmedID='!Id')
    except KeyError: # some DOI not properly indexed in pubmed?!?!
        xml = pubmed.search_pubmed(doi, retmax='1')
        try:
            d, root = pubmed.dict_from_xml(xml, pubmedID='!Id')
        except KeyError:
            pass
        else: # have to check whether title matches
            pubmedDict = pubmed.get_pubmed_dict(d['pubmedID'])
            if pubmedDict.get('title')[:50].lower() == \
               doiDict.get('title')[:50].lower():
                return doiDict, pubmedDict
            
    else:
        return doiDict, pubmed.get_pubmed_dict(d['pubmedID'])
    try:
        doiDict['summary'] = find_abstract(doiDict['source_url'])
    except KeyError:
        doiDict['summary'] = '(no abstract found)'
    return doiDict, None
        
    

#def get_doi_paper_dict(doi):
#    try:
        

        
