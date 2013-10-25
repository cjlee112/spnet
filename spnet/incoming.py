import re
import core
import errors
from datetime import datetime
import bulk

#################################################################
# hashtag processors
def get_paper(ID, paperType):
    if paperType == 'arxiv':
        return core.ArxivPaperData(ID, insertNew='findOrInsert').parent
    elif paperType == 'pubmed':
        try: # eutils horribly unreliable, handle its failure gracefully
            return core.PubmedPaperData(ID, insertNew='findOrInsert').parent
        except errors.TimeoutError:
            raise KeyError('eutils timed out, unable to retrive pubmedID')
    elif paperType == 'DOI':
        return core.DoiPaperData(DOI=ID, insertNew='findOrInsert').parent
    elif paperType == 'shortDOI':
        return core.DoiPaperData(ID, insertNew='findOrInsert').parent
    else:
        raise Exception('Unrecognized paperType')


def hashtag_to_spnetID(s, subs=((re.compile('([a-z])_([a-z])'), r'\1-\2'),
                                (re.compile('([0-9])_([0-9])'), r'\1.\2'))):
    'convert 1234_5678 --> 1234.5678 and gr_qc_12345 --> gr-qc_12345'
    for pattern, replace in subs:
        s = pattern.sub(replace, s)
    return s

def get_hashtag_arxiv(m):
    arxivID = hashtag_to_spnetID(str(m))
    return arxivID

def get_arxiv_paper(m):
    arxivID = str(m).replace('/', '_')
    return arxivID

def get_hashtag_pubmed(m):
    pubmedID = str(m)
    return pubmedID

def get_hashtag_doi(m):
    shortDOI = str(m)
    return shortDOI

def get_doi_paper(m):
    DOI = m # look out, DOI can include any unicode character
    return DOI

#################################################################
# hashtag parsing
refPats = (
    (re.compile('#arxiv_([a-z0-9_]+)'), 'arxiv', get_hashtag_arxiv),
    (re.compile('ar[xX]iv:\s?[a-zA-Z.-]+/([0-9]+\.[0-9]+v?[0-9]+)'),
     'arxiv', get_arxiv_paper),
    (re.compile('ar[xX]iv:\s?([a-zA-Z.-]+/[0-9]+v?[0-9]+)'), 'arxiv',
     get_arxiv_paper),
    (re.compile('ar[xX]iv:\s?([0-9]+\.[0-9]+v?[0-9]+)'), 'arxiv',
     get_arxiv_paper),
    (re.compile('http://arxiv.org/[abspdf]{3}/[a-zA-Z.-]+/([0-9]+\.[0-9]+v?[0-9]+)'),
     'arxiv', get_arxiv_paper),
    (re.compile('http://arxiv.org/[abspdf]{3}/([a-zA-Z.-]+/[0-9]+v?[0-9]+)'),
     'arxiv', get_arxiv_paper),
    (re.compile('http://arxiv.org/[abspdf]{3}/([0-9]+\.[0-9]+v?[0-9]+)'),
     'arxiv', get_arxiv_paper),
    (re.compile('#pubmed_([0-9]+)'), 'pubmed', get_hashtag_pubmed),
    (re.compile('PMID:\s?([0-9]+)'), 'pubmed', get_hashtag_pubmed),
    (re.compile('#shortDOI_([a-zA-Z0-9]+)'), 'shortDOI', get_hashtag_doi),
    (re.compile('[dD][oO][iI]:\s?(10\.\S+)'), 'DOI', get_doi_paper),
    (re.compile('shortDOI:\s?([a-zA-Z0-9]+)'), 'shortDOI', get_hashtag_doi)
    )

tagPattern = re.compile('#([a-zA-Z][a-zA-Z0-9_]+)')
citationTypes = ('recommend', 'discuss', 'announce', 'mustread')

def get_citations_types_and_topics(content, spnetworkOnly=True):
    """Process the body of a post.  Return
        - a dictionary with each entry of the form {reference: (refType, citationType}.  Here
          reference is a reference to a paper and citationType is one of
          {recommend discuss announce mustread}
          while refType is one of
          {arxiv pubmed DOI shortDOI}
        - and a list of topic tags

        Assumptions:
        - Each citationType or topic begins with a hash '#'
        - Only one citationType can be applied to each reference in a given post
        - The citationType for each reference must appear in the same line as the reference
        - The following are considered (user) errors:
            - multiple citations appear in a line with a citationType
            - multiple citationTypes appear in a line with a reference
            - a citationType appears in a line with no citations
    """
    citations = {}
    topics = []
    primary = None

    # Split post by lines
    lines = content.split('\n') # Also need to handle HTML "line breaks"
    # For each line:
    for line in lines:
        linerefs = []
        # Find all citations in line
        for refpat, reftype, patfun in refPats:
            ref_matches = refpat.findall(line)
            for reference in ref_matches:
                ref = patfun(reference)
                linerefs.append( (ref, reftype) )
        # Find topics and citationTypes in line
        tags = tagPattern.findall(line)
        tags = [t for t in tags if t != 'spnetwork']
        topicTags = [t for t in tags if t not in citationTypes]
        citationTags = [t for t in tags if t in citationTypes]
        topics.extend(topicTags)
        # Keep valid pair if no error
        if len(citationTags)==1 and len(linerefs)==1:
            cite = linerefs[0][0]
            refType = linerefs[0][1]
            citeType = citationTags[0]
            if not (cite in citations.keys()) or (citations[cite]=='discuss'):
                citations[cite] = (citeType, refType)
        # Otherwise keep all citations with 'discuss' as type
        else:
            for cite, refType in linerefs:
                if not (cite in citations.keys()):
                    citations[cite] = ('discuss', refType)

    # Remove duplicates
    topics = list(set(topics))

    # Now find location of #spnetwork and figure out which is the first reference after it
    # This seems a bit wasteful, but shouldn't be a bottleneck
    # Of course, we could check above for the simplest case
    try:
        sptagloc = re.compile('#spnetwork').search(content).start()
    except: # no spnetwork tag in this string
        if spnetworkOnly:
            raise Exception('No #spnetwork tag in post')
        else: # Take first reference as primary
            sptagloc = 0
    remainder = content[sptagloc:]
    first_ref_loc = len(remainder)
    for refpat, reftype, patfun in refPats:
        ref = refpat.search(remainder)
        if ref is not None:
            refloc = ref.start()
            if refloc < first_ref_loc:
                first_ref_loc = refloc
                primary = patfun(ref.group(1))
    if primary is None: # if no tags after #spnetwork, use first tag
        sptagloc = 0
        remainder = content[sptagloc:]
        first_ref_loc = len(remainder)
        for refpat, reftype, patfun in refPats:
            ref = refpat.search(remainder)
            if ref is not None:
                refloc = ref.start()
                if refloc < first_ref_loc:
                    first_ref_loc = refloc
                    primary = patfun(ref.group(1))


    return citations, topics, primary


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



def get_topicIDs(topics, docID, timestamp, source):
    """return list of topic IDs for a post, saving to db if needed

        Input variable topics should be a list of strings."""
    topics = screen_topics(topics, origin=dict(source=source, id=docID),
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
        try:
            post = core.Post(get_id(d))
            if getattr(post, 'etag', None) == d.get('etag', ''):
                yield post
                continue # matches DB record, so nothing to do
        except KeyError:
            pass
        # extract tags and IDs:
        citations, topics, primary = get_citations_types_and_topics(content)
        if post is None: # extract data for saving post to DB
            try:
                primary_paper_ID = citations[primary]
                paper = get_paper(primary,primary_paper_ID[1])
            except KeyError:
                continue # no link to a paper, so nothing to save.
            userID = get_user(d)
            author = find_or_insert_person(userID)
            d['author'] = author._id
        d['text'] =  content
        if process_post:
            process_post(d)
        d['sigs'] = get_topicIDs(topics, get_id(d),timeStamp, source)
        d['citationType'] = citations[primary][0]
        if post is None: # save to DB
            post = core.Post(docData=d, parent=paper)
            for ref, meta in citations.iteritems():
                if ref != primary:
                    paper = get_paper(ref, meta[1])
                    post.add_citations([paper], meta[0])
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
                r = core.Reply(docData=c, parent=post._parent_link)
                if recentEvents is not None: # add to monitor deque
                    saveEvents.append(r)

    if saveEvents and recentEvents is not None:
        saveEvents.sort(lambda x,y:cmp(x.published, y.published))
        for r in saveEvents:
            recentEvents.appendleft(r) # add to monitor deque

