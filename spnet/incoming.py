import re
import core

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

def get_hashtag_pubmed(m):
    pubmedID = str(m.group(1))
    return core.PubmedPaperData(pubmedID, insertNew='findOrInsert').parent

def get_hashtag_doi(m):
    shortDOI = str(m.group(1))
    return core.DoiPaperData(shortDOI, insertNew='findOrInsert').parent

#################################################################
# hashtag recognizers
hashTagPats = (
    (re.compile('#arxiv_([a-z0-9_]+)'), 'paper', get_hashtag_arxiv),
    (re.compile('#pubmed_([0-9]+)'), 'paper', get_hashtag_pubmed),
    (re.compile('#shortDOI_([a-zA-Z0-9]+)'), 'paper', get_hashtag_doi),
    (re.compile('#spnetwork'), 'header', lambda m:m.group(0)),
    (re.compile('#recommend'), 'rec', lambda m:m.group(0)),
    (re.compile('#mustread'), 'rec', lambda m:m.group(0)),
    (re.compile('#([a-zA-Z0-9_]+)'), 'topic', lambda m:m.group(1)),
    )


def get_hashtag_dict(t, pats=hashTagPats):
    '''extracts a dict of hashtags, of the form {k:[v,...]}
    with the following possible keys:
    paper: list of core.Paper objects
    topic: topic names (leading # removed)
    rec: #recommend or #mustread
    header: #spnetwork'''
    i = 0
    d = {}
    while True:
        try:
            i = t.index('#', i)
        except ValueError:
            break # no more hashtags
        for pat, k, f in pats: # try all the patterns to find the next hashtag
            m = pat.match(t, i)
            if m:
                result = f(m) # retrieve its output
                i = m.end() # advance past this hashtag
                try:
                    d[k].append(result)
                except KeyError:
                    d[k] = [result]
                break
        if not m: # no match, so skip #
            i += 1
    return d


#################################################################
# process post content looking for #spnetwork tags
def find_or_insert_posts(posts, get_post_comments, find_or_insert_person,
                         get_content, get_user, get_replycount,
                         process_post=None, process_reply=None):
    'generate each post that has a paper hashtag, adding to DB if needed'
    for d in posts:
        post = None
        content = get_content(d)
        isRec = content.find('#recommend') >= 0 or \
                content.find('#mustread') >= 0
        if not isRec:
            try:
                post = core.Post(d['id'])
                if getattr(post, 'etag', None) == d.get('etag', ''):
                    yield post
                    continue # matches DB record, so nothing to do
            except KeyError:
                pass
        if post is None: # extract data for saving post to DB
            hashtagDict = get_hashtag_dict(content)
            try:
                paper = hashtagDict['paper'][0] # link to first paper
            except KeyError:
                continue # no link to a paper, so nothing to save.
            userID = get_user(d)
            author = find_or_insert_person(userID)
            d['author'] = author._id
            d['text'] =  content
            if process_post:
                process_post(d)
            if isRec: # see if rec already in DB
                try:
                    post = core.Recommendation((paper._id, author._id))
                    if getattr(post, 'etag', None) == d.get('etag', ''):
                        yield post
                        continue # matches DB record, so nothing to do
                except KeyError: # need to save new record to DB
                    post = core.Recommendation(docData=d, parent=paper)
            else:
                post = core.Post(docData=d, parent=paper)
        yield post
        if get_replycount(d) > 0:
            for c in get_post_comments(d['id']):
                if process_reply:
                    process_reply(c)
                try:
                    r = core.Reply(c['id'])
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
                c['replyTo'] = d['id']
                r = core.Reply(docData=c, parent=post._parent_link)

