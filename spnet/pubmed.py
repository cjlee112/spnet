from lxml import etree
import requests

def pubmed_dict_from_xml(xml, fields=dict(title='ArticleTitle',
                                          summary='AbstractText',
                                          id='PMID',
                                          year='ArticleDate.Year',
                                          journal='ISOAbbreviation',
                                          ISSN='ISSN',
                                          affiliation='Affiliation')):
    'extract fields + authorNames + DOI from xml, return as dict'
    root = etree.XML(xml)
    d = {}
    for k,v in fields.items():
        f = v.split('.')
        o = root.find('.//' + f[0]) # search for top field
        for subfield in f[1:]: # contains subfield
            o = o.find(subfield)
        d[k] = o.text
    authorNames = [] # extract list of author names
    for o in root.findall('.//Author'):
        authorNames.append(o.find('ForeName').text + ' ' +
                           o.find('LastName').text)
    d['authorNames'] = authorNames
    for o in root.findall('.//ELocationID'): # extract DOI
        if o.get('EIdType', '') == 'doi':
            d['doi'] = o.text
    return d

def query_pubmed_id(pubmedID,
               uri='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi',
                    tool='example', email='leec@chem.ucla.edu',
                    retmode='xml'):
    params = dict(id=pubmedID, db='pubmed', tool=tool, email=email,
                  retmode=retmode)
    r = requests.get(uri, params=params)
    return r.text

def get_pubmed_dict(pubmedID):
    'get paper data for specified pubmed ID, from NCBI eutils API'
    xml = query_pubmed_id(pubmedID)
    return pubmed_dict_from_xml(xml)
