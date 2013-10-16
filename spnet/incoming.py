import re
import core
import errors
from datetime import datetime
import bulk

#################################################################
# hashtag processors
def hashtag_to_spnetID(s, subs=((re.compile('([a-z])_([a-z])'), r'\1-\2'),
                                (re.compile('([0-9])_([0-9])'), r'\1.\2'))):
    'convert 1234_5678 --> 1234.5678 and gr_qc_12345 --> gr-qc_12345'
    for pattern, replace in subs:
        s = pattern.sub(replace, s)
    return s

def get_hashtag_arxiv(m):
    arxivID = hashtag_to_spnetID(str(m.group(1)))
    return core.ArxivPaperData(arxivID, insertNew='findOrInsert').parent

def get_arxiv_paper(m):
    arxivID = str(m.group(1)).replace('/', '_')
    return core.ArxivPaperData(arxivID, insertNew='findOrInsert').parent

def get_hashtag_pubmed(m):
    pubmedID = str(m.group(1))
    try: # eutils horribly unreliable, handle its failure gracefully
        return core.PubmedPaperData(pubmedID, insertNew='findOrInsert').parent
    except errors.TimeoutError:
        raise KeyError('eutils timed out, unable to retrive pubmedID')

def get_hashtag_doi(m):
    shortDOI = str(m.group(1))
    return core.DoiPaperData(shortDOI, insertNew='findOrInsert').parent

def get_doi_paper(m):
    DOI = m.group(1) # look out, DOI can include any unicode character
    return core.DoiPaperData(DOI=DOI, insertNew='findOrInsert').parent

#################################################################
# hashtag recognizers
hashTagPats = (
    (re.compile('#arxiv_([a-z0-9_]+)'), 'paper', get_hashtag_arxiv),
    (re.compile('ar[xX]iv:\s?[a-zA-Z.-]+/([0-9]+\.[0-9]+v?[0-9]+)'), 'paper', 
     get_arxiv_paper),
    (re.compile('ar[xX]iv:\s?([a-zA-Z.-]+/[0-9]+v?[0-9]+)'), 'paper', 
     get_arxiv_paper),
    (re.compile('ar[xX]iv:\s?([0-9]+\.[0-9]+v?[0-9]+)'), 'paper', 
     get_arxiv_paper),
    (re.compile('http://arxiv.org/[abspdf]{3}/[a-zA-Z.-]+/([0-9]+\.[0-9]+v?[0-9]+)'), 'paper', 
     get_arxiv_paper),
    (re.compile('http://arxiv.org/[abspdf]{3}/([a-zA-Z.-]+/[0-9]+v?[0-9]+)'), 'paper', 
     get_arxiv_paper),
    (re.compile('http://arxiv.org/[abspdf]{3}/([0-9]+\.[0-9]+v?[0-9]+)'), 'paper', 
     get_arxiv_paper),
    (re.compile('#pubmed_([0-9]+)'), 'paper', get_hashtag_pubmed),
    (re.compile('PMID:\s?([0-9]+)'), 'paper', get_hashtag_pubmed),
    (re.compile('#shortDOI_([a-zA-Z0-9]+)'), 'paper', get_hashtag_doi),
    (re.compile('[dD][oO][iI]:\s?(10\.\S+)'), 'paper', get_doi_paper),
    (re.compile('shortDOI:\s?([a-zA-Z0-9]+)'), 'paper', get_hashtag_doi),
    (re.compile('#([a-zA-Z][a-zA-Z0-9_]+)'), 'topic', lambda m:m.group(1)),
    )

class CategoryList(object):
    'ensures each string matched only once'
    recats={'recommend':'rec', 'mustread':'rec', 'spnetwork':'header'}
    def __init__(self):
        self.d = {}
    def append(self, start, k, v):
        if start in self.d: # ignore duplicate match to same string
            return
        try:
            k = self.recats[v] # recategorize hashtag
        except KeyError:
            pass
        self.d[start] = (k, v)
    def get_dict(self):
        'dict of {category:[results]}; results in order of occurence in text'
        l = self.d.items()
        l.sort()
        d = {}
        primaryPaper = False
        for pos, (k, v) in l:
            if v == 'spnetwork': # 1st paper after tag is primary paper
                primaryPaper = True
            try:
                if primaryPaper and k == 'paper':
                    d.setdefault(k, []).insert(0, v) # make it 1st entry
                    primaryPaper = False
                else:
                    d[k].append(v)
            except KeyError:
                d[k] = [v]
        for k,l in d.items(): # filter out any duplicate entries
            d[k] = [v for (i,v) in enumerate(l) if v not in l[:i]]
        return d
    

def get_hashtag_dict(t, pats=hashTagPats):
    '''extracts a dict of hashtags, of the form {k:[v,...]}
    with the following possible keys:
    paper: list of core.Paper objects
    topic: topic names (leading # removed)
    rec: recommend or mustread
    header: spnetwork'''
    cl = CategoryList()
    for pat, k, f in pats: # try all the patterns
        m = pat.search(t)
        while m:
            try:
                result = f(m) # retrieve its output
                cl.append(m.start(), k, result)
            except KeyError:
                pass # bad ID or false positive, so ignore
            m = pat.search(t, m.end()) # search for next hashtag
    return cl.get_dict()


#################################################################
# process post content looking for #spnetwork tags

# replace this by class that queries for ignore=1 topics just once,
# keeps cache
def screen_topics(topicWords, skipAttr='ignore', **kwargs):
    'return list of topic object, filtered by the skipAttr attribute'
    l = []
    for t in topicWords:
        topic = core.SIG.find_or_insert(t, **kwargs)
        if not getattr(topic, skipAttr, False):
            l.append(topic)
    return l



def get_topicIDs(hashtagDict, docID, timestamp, source):
    'return list of topic IDs for a post, saving to db if needed'
    topics = screen_topics(hashtagDict.get('topic', ()),
                           origin=dict(source=source, id=docID),
                           published=timestamp)
    return [t._id for t in topics] # IDs for storing to db, etc.


def find_or_insert_posts(posts, get_post_comments, find_or_insert_person,
                         get_content, get_user, get_replycount,
                         get_id, get_timestamp, is_reshare, source,
                         process_post=None, process_reply=None,
                         recentEvents=None, maxDays=None,
                         citationType='discuss', citationType2='discuss',
                         get_title=lambda x:x['title'],
                         spnetworkOnly=True):
    'generate each post that has a paper hashtag, adding to DB if needed'
    now = datetime.utcnow()
    saveEvents = []
    for d in posts:
        post = None
        timeStamp = get_timestamp(d)
        if maxDays is not None and (now - timeStamp).days > maxDays:
            break
        if is_reshare(d): # just a duplicate (reshared) post, so skip
            continue
        content = get_content(d)
        if spnetworkOnly and content.find('#spnetwork') < 0:
            continue # ignore posts lacking our spnetwork hashtag
        isRec = content.find('#recommend') >= 0 or \
                content.find('#mustread') >= 0
        try:
            post = core.Post(get_id(d))
            if getattr(post, 'etag', None) == d.get('etag', ''):
                yield post
                continue # matches DB record, so nothing to do
        except KeyError:
            pass
        hashtagDict = get_hashtag_dict(content) # extract tags and IDs
        if post is None: # extract data for saving post to DB
            try:
                papers = hashtagDict['paper']
                paper = papers[0] # link to first paper
            except KeyError:
                continue # no link to a paper, so nothing to save.
            userID = get_user(d)
            author = find_or_insert_person(userID)
            d['author'] = author._id
        d['text'] =  content
        if process_post:
            process_post(d)
        d['sigs'] = get_topicIDs(hashtagDict, get_id(d),
                                 timeStamp, source)
        if isRec: # record rec type
            try:
                d['citationType'] = hashtagDict['rec'][0]
            except KeyError: # handle bad rec hashtag
                d['citationType'] = 'recommend'
        else: # use default citation type
            d['citationType'] = citationType
        if post is None: # save to DB
            post = core.Post(docData=d, parent=paper)
            if len(papers) > 1: # save 2ary citations
                post.add_citations(papers[1:], citationType2)
            try:
                topicsDict
            except NameError:
                topicsDict, subsDict = bulk.get_people_subs()
            bulk.deliver_rec(paper._id, d, topicsDict, subsDict)
            if recentEvents is not None: # add to monitor deque
                saveEvents.append(post)
        else: # update DB with new data and etag
            post.update(d)
        yield post
        if get_replycount(d) > 0:
            for c in get_post_comments(get_id(d)):
                if process_reply:
                    process_reply(c)
                try:
                    r = core.Reply(get_id(c))
                    if getattr(r, 'etag', None) != c.get('etag', ''):
                        # update DB record with latest data
                        r.update(dict(etag=c.get('etag', ''),
                                      text=get_content(c),
                                      updated=c.get('updated', '')))
                    continue # already stored in DB, no need to save
                except KeyError:
                    pass
                userID = get_user(c)
                author = find_or_insert_person(userID)
                c['author'] = author._id
                c['text'] =  get_content(c)
                c['replyTo'] = get_id(d)
                if isRec: # record the type of post
                    c['sourcetype'] = 'rec'
                else:
                    c['sourcetype'] = 'post'
                r = core.Reply(docData=c, parent=post._parent_link)
                if recentEvents is not None: # add to monitor deque
                    saveEvents.append(r)

    if saveEvents and recentEvents is not None:
        saveEvents.sort(lambda x,y:cmp(x.published, y.published))
        for r in saveEvents:
            recentEvents.appendleft(r) # add to monitor deque

