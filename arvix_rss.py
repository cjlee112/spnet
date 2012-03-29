import datetime
import re
import feedparser

a_re = re.compile(r"""<a.*?>(.*?)</a>""", re.DOTALL)
p_re = re.compile(r"""<p>(.*?)</p>""", re.DOTALL)
title_re = re.compile(r"""(.*?)\.\s\(arXiv:(.*?)\[(.*?)\].*?\)""", re.DOTALL)

def rss_gen(url):
    attribute_map = {'title': 'title', 'url': 'link', 'author': 'authors', }
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
        
if __name__ == '__main__':
    url = 'http://export.arxiv.org/rss/cs'
    for paper in rss_gen(url):
        print paper

