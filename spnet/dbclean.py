import core

def add_reply_sourcetype():
    '''Mark all Reply records as coming from a post or rec'''
    for p in core.Post.find_obj():
        for r in p.get_replies():
            r.update(dict(sourcetype='post'))
    for p in core.Recommendation.find_obj():
        for r in p.get_replies():
            r.update(dict(sourcetype='rec'))

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

def update_index(p, attr, d):
    changed = 0
    for r in getattr(p, attr, ()):
        if r.id not in d or r.updated > d[r.id].updated:
            d[r.id] = r
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
        recs = get_index(p0, 'recommendations')
        posts = get_index(p0, 'posts')
        replies = get_index(p0, 'replies')
        interests = get_index(p0, 'interests', 'author')
        newRecs = newPosts = newReplies = newInterests = 0
        for p in papers[1:]:
            newRecs |= update_index(p, 'recommendations', recs)
            newPosts |= update_index(p, 'posts', posts)
            newReplies |= update_index(p, 'replies', replies)
            newInterests |= update_interests(p, 'interests', interests)
        update_paper_array(p0, 'recommendations', newRecs, recs, pid)
        update_paper_array(p0, 'posts', newPosts, posts, pid)
        update_paper_array(p0, 'replies', newReplies, replies, pid)
        update_paper_array(p0, 'interests', newInterests, interests, pid)

        for p in papers[1:]:
            if savecoll: # backup to another collection
                savecoll.insert(p._dbDocDict)
            p.delete() # delete from papers collection
            print 'deleted paper %s' % p._id
