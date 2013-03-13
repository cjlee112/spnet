import feedparser
import twitter
#import core
from time import mktime
from datetime import datetime
import urllib

arxivApiUrl = 'http://export.arxiv.org/api/query?'

def lookup_papers(id_list, **kwargs):
    'retrieve a list of arxiv IDs, as a generator function'
    d = kwargs.copy()
    for i in range(0, len(id_list), 10):
        d['id_list'] = ','.join(id_list[i:i + 10])
        url = arxivApiUrl + '&'.join(['%s=%s' % t for t in d.items()])
        f = feedparser.parse(url)
        for e in f.entries:
            l = e['id'].split('/')
            e['id'] = l[4].split('v')[0] # replace URL by arxivID
            yield e

def search_arxiv(search_query, block_size=25):
    'iterate over arxiv papers matching search_query'
    start = 0
    q = dict(search_query=search_query, max_results=str(block_size))
    while True:
        q['start'] = str(start)
        url = arxivApiUrl + urllib.urlencode(q)
        f = feedparser.parse(url)
        for e in f.entries:
            yield e
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
            
    
def get_paper(arxivID):
    import core
    try:
        return core.Paper.find_obj({'arxiv.id':arxivID}).next()
    except StopIteration: # no matching record
        try:
            d = lookup_papers((arxivID,)).next()
        except StopIteration: # no matching record
            raise KeyError('arxiv ID %s not found in arXiv!' % arxivID)
        a = core.ArxivPaperData(docData=d, insertNew='findOrInsert')
        return a.parent

