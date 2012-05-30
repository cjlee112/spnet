import datetime
import os
import pickle
import re
import time
import feedparser

a_re = re.compile(r"""<a.*?>(.*?)</a>""", re.DOTALL)
p_re = re.compile(r"""<p>(.*?)</p>""", re.DOTALL)
title_re = re.compile(r"""(.*?)\.\s\(arXiv:(.*?)\[(.*?)\].*?\)""", re.DOTALL)

arvix_categories = map(lambda x: x.strip(), "astro-ph, cond-mat, cs, gr-qc, hep-ex, hep-lat, hep-ph, hep-th, math, math-ph, nlin, nucl-ex, nucl-th, physics, q-bio, q-fin, quant-ph, stat".split(','))

cache_filename = "arxiv.pickle"

#def load_categories(filename="arxiv_categories.txt"):
    #categories = []
    #with open(filename) as handle:
        #for line in handle:
            #categories.append(line.strip())
    #return categories

def rss_gen(categories=None, base_url="http://export.arxiv.org/rss/", verbose=False):
    """Generator for Arxiv RSS feeds."""
    #attribute_map = {'title': 'title', 'url': 'link', 'author': 'authors', }
    if not categories:
        categories = arvix_categories
    for category in categories:
        url = base_url + category
        feed = feedparser.parse(url)
        if verbose:
            print "Downloading category %s: %s" %(category, url)
        num_entries = len(feed['entries'])
        for feed_entry in feed['entries']:
            paper = dict()
            paper['url'] = feed_entry['links'][0]['href'].strip()
            paper['authors'] = tuple(a_re.findall(feed_entry['author']))
            m = p_re.findall(feed_entry['summary'])
            paper['abstract'] = m[0].strip()
            m = title_re.findall(feed_entry['title'])[0]
            paper['title'] = m[0].strip()
            paper['arxiv-topic-area'] = m[2].strip()
            paper['id'] = m[1].strip()
            paper['year'] = datetime.datetime.now().year
            yield paper
        if verbose:
            print "  Received %s entries. Sleeping for 20 seconds as requested in robots.txt" % str(num_entries)
        time.sleep(20) #robots.txt

def load_cache(filename=cache_filename):
    with open(cache_filename) as cache_file:
        papers = pickle.load(cache_file)
    return papers

def append_to_cache(papers, filename=cache_filename):
    """Add newly downloaded files to the cache, making sure not to add duplicates. May not scale well for a large number of papers."""
    hashable_papers = set()
    if os.path.isfile(cache_filename):
        with open(cache_filename) as cache_file:
            cached_papers = pickle.load(cache_file)
            for paper in cached_papers:
                hashable_papers.add(frozenset(tuple(paper.items())))
    for paper in papers:
        hashable_papers.add(frozenset(tuple(paper.items())))
    new_cache = []
    for paper in hashable_papers:
        new_cache.append(dict(paper))
    with open(cache_filename, 'w') as cache_file:
        pickle.dump(new_cache, cache_file)
        
def get_papers(download=False, verbose=False):
    """Returns the papers in the cache. Downloads new papers if the cache is empty or if cache=True."""
    if not download:
        if os.path.isfile(cache_filename):
            return load_cache()
    all_papers = []
    for paper in rss_gen(verbose=verbose):
        all_papers.append(paper)
    append_to_cache(all_papers)
    if verbose:
        "Papers cached in %s ." % cache_filename 
    return load_cache()
        
if __name__ == '__main__':
    if os.path.isfile(cache_filename):
        papers = load_cache()
        print "Cache contains %s papers." % str(len(papers))
    else:
        print "No cache file. Downloading papers from the Arxiv."
    papers = get_papers(download=True, verbose=True)
    papers = load_cache()
    print "Cache contains %s papers." % str(len(papers))

    