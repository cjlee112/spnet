import datetime
import re
import time
import feedparser

a_re = re.compile(r"""<a.*?>(.*?)</a>""", re.DOTALL)
p_re = re.compile(r"""<p>(.*?)</p>""", re.DOTALL)
title_re = re.compile(r"""(.*?)\.\s\(arXiv:(.*?)\[(.*?)\].*?\)""", re.DOTALL)

#def load_categories(filename="arxiv_categories.txt"):
    #categories = []
    #with open(filename) as handle:
        #for line in handle:
            #categories.append(line.strip())
    #return categories

def rss_gen(categories, base_url="http://export.arxiv.org/rss/"):
    #attribute_map = {'title': 'title', 'url': 'link', 'author': 'authors', }
    for category in categories:
        url = base_url + category
        feed = feedparser.parse(url)
        for feed_entry in feed['entries']:
            paper = dict()
            paper['url'] = feed_entry['links'][0]['href']
            paper['authors'] = a_re.findall(feed_entry['author'])
            m = p_re.findall(feed_entry['summary'])
            paper['abstract'] = m[0]
            m = title_re.findall(feed_entry['title'])[0]
            paper['title'] = m[0]
            paper['arxiv-topic-area'] = m[2]
            paper['id'] = m[1]
            paper['year'] = datetime.datetime.now().year
            yield paper
        time.sleep(20) #robots.txt
        
if __name__ == '__main__':
    categories = map(lambda x: x.strip(), "astro-ph, cond-mat, cs, gr-qc, hep-ex, hep-lat, hep-ph, hep-th, math, math-ph, nlin, nucl-ex, nucl-th, physics, q-bio, q-fin, quant-ph, stat".split(','))
    for paper in rss_gen(categories):
        print paper

