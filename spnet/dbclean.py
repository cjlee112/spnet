import core
import incoming

##############################################################
# utilities for converting old Paper.recommendations storage
# to new unified Paper.posts storage
def convert_recs_to_posts():
    '''convert all recommendation records to post records
    with proper citationType'''
    for p in core.Post.find_obj(): # add citationType to existing posts
        p.update(dict(citationType='discuss'))
    for rec in core.Recommendation.find_obj():
        d = rec._dbDocDict
        s = rec.get_text()
        if s.find('#mustread') >= 0: # label with citation type
            d['citationType'] = 'mustread'
        else:
            d['citationType'] = 'recommend'
        post = core.Post(docData=d, parent=rec._parent_link)

def test_conversion():
    'move recs to post array and test that new interfaces match old record set'
    d = {}
    for p in core.Post.find_obj(): # add citationType to existing posts
        d.setdefault(p._parent_link, set()).add(p.id)
    d2 = {}
    for rec in core.Recommendation.find_obj():
        d2.setdefault(rec._parent_link, set()).add(rec.id)
    convert_recs_to_posts()
    papers = set(d.keys() + d2.keys())
    for pid in papers:
        p = core.Paper(pid)
        posts = set([post.id for post in p.posts if not post.is_rec()])
        assert posts == d.get(pid, set())
        recs = set([post.id for post in p.recommendations])
        assert recs == d2.get(pid, set())
        

def delete_recs(q={'recommendations':{'$exists':True}}):
    'delete the old Paper.recommendations storage'
    core.Paper.coll.update(q, {'$unset': {'recommendations':''}}, multi=True)

def add_delivery_post_id():
    'add postID to each Person.received record'
    d = {} # construct mapping of (paperID,authorID) to postID
    for p in core.Post.find_obj():
        if p.is_rec():
            d[(p._parent_link,p._dbDocDict['author'])] = p.id
    for person in core.Person.find_obj({'received':{'$exists':True}}):
        received = person._dbDocDict['received']
        for r in received:
            r['post'] = d[(r['paper'],r['from'])] # add postID
        person.update(dict(received=received))

def add_post_citations(citationType2='discuss'):
    for p in core.Post.find_obj(): # add citationType to existing posts
        content = p.get_text()
        hashtagDict = incoming.get_hashtag_dict(content) # extract tags and IDs
        papers = hashtagDict['paper']
        if len(papers) > 1:
            print 'multiple citations for %s: primary %s' \
                % (p.id, papers[0].get_value('local_url'))
            if papers[0] != p.parent:
                print 'fixing primary paper mismatch %s -> %s' \
                    % (p.parent.get_value('local_url'), 
                       papers[0].get_value('local_url'))
                data = p._dbDocDict
                p.delete() # delete Post record from p.parent paper
                p = core.Post(docData=data, parent=papers[0])
            for paper2 in papers[1:]: # save 2ary citations
                d2 = dict(post=p.id, authorName=p.author.name,
                          title=p.title, published=p.published,
                          citationType=citationType2)
                core.Citation(docData=d2, parent=paper2) # save citation to db
                print '  added citation to %s' % paper2.get_value('local_url')
            
#################################################################
# make sure all Reply records indicate post vs. rec sourcetype

def add_reply_sourcetype():
    '''Mark all Reply records as coming from a post or rec'''
    for p in core.Post.find_obj():
        for r in p.get_replies():
            r.update(dict(sourcetype='post'))
    for p in core.Recommendation.find_obj():
        for r in p.get_replies():
            r.update(dict(sourcetype='rec'))

################################################################
# utilities for cleaning up / merging Paper records

def delete_papers(query={'arxiv.id': {'$regex':'error'}},
                  paperColl=core.Paper.coll, personColl=core.Person.coll):
    '''delete papers matching query from both paper collection
    and Person reading lists'''
    n = 0
    for d in paperColl.find(query, {'_id':1}):
        paperID = d['_id']
        personColl.update({'readingList': paperID}, 
                          {'$pull': {'readingList': paperID}}, 
                          multi=True) # delete from readingLists
        personColl.update({'received.paper': paperID}, 
                          {'$pull': {'received': {'paper': paperID}}}, 
                          multi=True) # update readingLists
        n += 1
    paperColl.remove(query) # delete papers
    print 'deleted %d papers.' % n

def check_papers_unique():
    '''Search for duplicate paper records with same arxiv.id
    (or pubmed.id, or doi.id).  '''
    d = {}
    for p in core.Paper.find_obj():
        try:
            pid = p.arxiv.id
        except AttributeError:
            try:
                pid = p.pubmed.id
            except AttributeError:
                pid = p.doi.id

        d.setdefault(pid, []).append(p)
    counts = {}
    for pid,papers in d.items():
        c = len(papers)
        if c > 1:
            counts.setdefault(c, []).append(pid)
    return counts, d

def get_index(p, attr, keyAttr='id'):
    d = {}
    for r in getattr(p, attr, ()):
        d[r._dbDocDict[keyAttr]] = r
    return d

def update_index(p, attr, d, keyAttr='id'):
    changed = 0
    for r in getattr(p, attr, ()):
        rid = getattr(r, keyAttr)
        if rid not in d or r.updated > d[rid].updated:
            d[rid] = r
            changed = 1
    return changed

def update_interests(p, attr, d):
    changed = 0
    for r in getattr(p, attr, ()):
        try:
            iset1 = set(d[r._dbDocDict['author']]._dbDocDict['topics'])
            iset2 = set(r._dbDocDict['topics'])
            if iset2.issubset(iset1):
                continue # no new topics, so nothing to save
            r._dbDocDict['topics'] = list(iset1 | iset2) # union of topics
        except KeyError:
            pass
        d[r._dbDocDict['author']] = r
        changed = 1
    return changed

def update_paper_array(p, attr, pleaseUpdate, docs, pid):
    if pleaseUpdate:
        data = [doc._dbDocDict for doc in docs.values()]
        p.update({attr: data})
        print 'unified %d %s on paper %s' % (len(docs), attr, pid)

def replace_paper(p, newID, savecoll=None, personColl=core.Person.coll):
    '''delete paper and update reading lists to repliace ir with newID'''
    personColl.update({'readingList': p._id}, 
                      {'$set': {'readingList.$': newID}}, 
                      multi=True) # update readingLists
    personColl.update({'received.paper': p._id}, 
                      {'$set': {'received.$.paper': newID}}, 
                      multi=True) # update readingLists
    if savecoll: # backup to another collection
        savecoll.insert(p._dbDocDict)
    p.delete() # delete from papers collection
    print 'deleted paper %s' % p._id

def merge_duplicate_papers(d, savecoll=None):
    '''Merge duplicate paper records found by check_papers_unique(),
    combining recs, posts, replies, interests onto a unique paper
    record for a given arxiv.id (or pubmed.id or doi.id)
    and deleting duplicate records of that paper.
    If savecoll is not None, duplicate records are archived to
    that mongodb collection.

    Usage:
    >>> import core, dbclean, connect
    >>> dbconn = connect.init_connection()
    >>> counts, d = dbclean.check_papers_unique()
    >>> duplicate_papers = core.Paper.coll.database.duplicate_papers
    >>> dbclean.merge_duplicate_papers(d, duplicate_papers)
    '''
    for pid, papers in d.items():
        if len(papers) == 1:
            continue # no duplicates to merge
        p0 = papers[0]
        citations = get_index(p0, 'citations', 'post')
        posts = get_index(p0, 'posts')
        replies = get_index(p0, 'replies')
        interests = get_index(p0, 'interests', 'author')
        newCits = newPosts = newReplies = newInterests = 0
        for p in papers[1:]:
            newCits |= update_index(p, 'citations', citations, 'post')
            newPosts |= update_index(p, 'posts', posts)
            newReplies |= update_index(p, 'replies', replies)
            newInterests |= update_interests(p, 'interests', interests)
        update_paper_array(p0, 'citations', newCits, citations, pid)
        update_paper_array(p0, 'posts', newPosts, posts, pid)
        update_paper_array(p0, 'replies', newReplies, replies, pid)
        update_paper_array(p0, 'interests', newInterests, interests, pid)

        for p in papers[1:]: # finally, delete duplicate papers
            replace_paper(p, p0._id, savecoll)
