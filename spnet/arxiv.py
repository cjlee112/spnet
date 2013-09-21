import feedparser
import twitter
#import core
from time import mktime
from datetime import datetime
import urllib
import re

arxivApiUrl = 'http://export.arxiv.org/api/query?'

def get_arxiv_id(arxivURL):
    'extract arxivID from arxiv URL, replacing / --> _'
    l = arxivURL.split('/')
    s = '_'.join(l[4:])
    try:
        return s[:s.rindex('v')] # remove version info
    except ValueError:
        return s

def normalize_arxiv_dict(d):
    'convert id and author names to fit our standard'
    d['id'] = get_arxiv_id(d['id']) # replace URL by arxivID
    d['authorNames'] = [ad['name'] for ad in d['authors']]
    return d


def is_id_string(s,
                 dottedNumber=re.compile(
                     r'[0-9][0-9][0-9]+\.[0-9]+[0-9v][0-9]+$'),
                 fieldSlashNumber=re.compile(
                     '[a-z][a-z]+[a-z-][a-z]+/[0-9]+[0-9v][0-9]+$')):
    'True if s looks like an arXiv paper string'
    return dottedNumber.match(s) or fieldSlashNumber.match(s)

def lookup_papers(id_list, **kwargs):
    'retrieve a list of arxiv IDs, as a generator function'
    d = kwargs.copy()
    for i in range(0, len(id_list), 10):
        d['id_list'] = ','.join(id_list[i:i + 10])
        url = arxivApiUrl + urllib.urlencode(d)
        f = feedparser.parse(url)
        for e in f.entries:
            paper = normalize_arxiv_dict(e)
            if not paper['id'].startswith('error'):
                yield paper

def search_arxiv(searchString, start=0, block_size=25):
    'retrieve list of block_size results for specified search'
    q = dict(search_query=searchString, max_results=str(block_size),
             start=str(start))
    url = arxivApiUrl + urllib.urlencode(q)
    f = feedparser.parse(url)
    l = []
    for e in f.entries:
        l.append(normalize_arxiv_dict(e))
    return l


def search_arxiv_iter(search_query, block_size=25):
    'iterate over arxiv papers matching search_query'
    start = 0
    q = dict(search_query=search_query, max_results=str(block_size))
    while True:
        q['start'] = str(start)
        url = arxivApiUrl + urllib.urlencode(q)
        f = feedparser.parse(url)
        for e in f.entries:
            yield normalize_arxiv_dict(e)
        start += block_size
        if len(f.entries) < block_size:
            break
        

excludeUsers = set((154769981,)) # just a robot, so ignore!


def recent_tweets(query='http://arxiv.org'):
    'latest tweets of arxiv paper references'
    for tweet in twitter.get_recent(query):
        if tweet.from_user_id in excludeUsers:
            continue
        for arxivID in twitter.extract_arxiv_id(tweet):
            yield arxivID, tweet
            
    
