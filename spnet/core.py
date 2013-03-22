from base import *
from hashlib import sha1
import re



##########################################################

# fetch functions for use with LinkDescriptor 

def fetch_recs(person):
    'return list of Recommendation objects for specified person'
    coll = Recommendation.coll
    results = coll.find({'recommendations.author':person._id},
                        {'recommendations':1})
    l = []
    for r in results:
        paperID = r['_id']
        for recDict in r['recommendations']:
            if recDict['author'] == person._id:
                l.append(Recommendation(docData=recDict, parent=paperID,
                                        insertNew=False))
                break
    return l

def merge_sigs(person, attr, sigLinks):
    'postprocess list of SIGLinks to handle mergeIn requests'
    d = {}
    merges = []
    for sl in sigLinks:
        d[sl.dbDocDict['sig']] = sl
        if hasattr(sl, 'mergeIn'):
            merges.append(sl)
    for sl in merges:
        d[sl.mergeIn]._add_merge(sl)
    


######################################################

# forward declarations to avoid circular ref problem
fetch_paper = FetchObj(None)
fetch_person = FetchObj(None)
fetch_post = FetchObj(None)
fetch_sig = FetchObj(None)
fetch_sigs = FetchList(None)
fetch_people = FetchList(None)
fetch_papers = FetchList(None)
fetch_parent_issue = FetchParent(None)
fetch_parent_person = FetchParent(None)
fetch_parent_paper = FetchParent(None)
fetch_author_papers = FetchQuery(None, lambda author:dict(authors=author._id))
fetch_subscribers = FetchQuery(None, lambda person:
                               dict(subscriptions=person._id))
fetch_sig_members = FetchQuery(None, lambda sig: {'sigs.sig':sig._id})
fetch_sig_papers = FetchQuery(None, lambda sig: {'sigs':sig._id})
fetch_sig_recs = FetchQuery(None, lambda sig:
                            {'recommendations.sigs':sig._id})
fetch_sig_interests = FetchQuery(None, lambda sig:
                                 {'interests.topics':sig._id})
fetch_issues = FetchQuery(None, lambda paper:dict(paper=paper._id))
fetch_person_posts = FetchQuery(None, lambda author:
                            {'posts.author':author._id})
fetch_person_replies = FetchQuery(None, lambda author:
                            {'replies.author':author._id})
fetch_person_interests = FetchQuery(None, lambda author:
                            {'interests.author':author._id})
fetch_gplus_by_id = FetchObjByAttr(None, '_id')
fetch_gplus_subs = FetchObjByAttr(None, 'id')

# main object classes

class EmailAddress(UniqueArrayDocument):
    _dbfield = 'email.address' # dot.name for updating

    parent = LinkDescriptor('parent', fetch_parent_person, noData=True)


class Recommendation(ArrayDocument):
    _dbfield = 'recommendations.author' # dot.name for updating
    useObjectId = False # input data will supply _id
    _timeStampField = 'published' # auto-add timestamp if missing
    # attrs that will only be fetched if accessed by user
    parent = LinkDescriptor('parent', fetch_parent_paper, noData=True)
    author = LinkDescriptor('author', fetch_person)
    forwards = LinkDescriptor('forwards', fetch_people)
    sigs = LinkDescriptor('sigs', fetch_sigs, missingData=())

    def get_replies(self):
        try:
            recID = self.id
        except AttributeError:
            return
        for r in getattr(self.parent, 'replies', ()):
            if r._dbDocDict['replyTo'] == recID:
                yield r
    def get_local_url(self):
        return '/papers/' + str(self._parent_link) + '/recs/' + \
               str(self._dbDocDict['author'])

class Post(UniqueArrayDocument):
    _dbfield = 'posts.id' # dot.name for updating
    _timeStampField = 'published' # auto-add timestamp if missing
    # attrs that will only be fetched if accessed by getattr
    parent = LinkDescriptor('parent', fetch_parent_paper, noData=True)
    author = LinkDescriptor('author', fetch_person)
    def get_replies(self):
        for r in getattr(self.parent, 'replies', ()):
            if r.replyTo == self:
                yield r

def fetch_post_or_rec(obj, fetchID):
    try:
        return fetch_post(obj, fetchID)
    except KeyError:
        for rec in obj.parent.recommendations:
            if getattr(rec, 'id', ('uNmAtChAbLe',)) == fetchID:
                return rec
    raise KeyError('No post or rec found with id=' + str(fetchID))


class Reply(UniqueArrayDocument):
    _dbfield = 'replies.id' # dot.name for updating
    _timeStampField = 'published' # auto-add timestamp if missing
    # attrs that will only be fetched if accessed by getattr
    parent = LinkDescriptor('parent', fetch_parent_paper, noData=True)
    author = LinkDescriptor('author', fetch_person)
    replyTo = LinkDescriptor('replyTo', fetch_post_or_rec)

class PaperInterest(ArrayDocument):
    _dbfield = 'interests.author' # dot.name for updating
    # attrs that will only be fetched if accessed by getattr
    parent = LinkDescriptor('parent', fetch_parent_paper, noData=True)
    author = LinkDescriptor('author', fetch_person)
    topics = LinkDescriptor('topics', fetch_sigs, missingData=())
    def add_topic(self, topic):
        topics = set(self._dbDocDict.get('topics', ()))
        topics.add(topic)
        self.update(dict(topics=list(topics)))
        return self
    def remove_topic(self, topic):
        topics = set(self._dbDocDict.get('topics', ()))
        topics.remove(topic)
        if topics:
            self.update(dict(topics=list(topics)))
            return self
        else: # PaperInterest empty, so remove completely
            self.delete()
            return None
    def get_local_url(self):
        return '/papers/' + str(self._parent_link) + '/likes/' + \
               str(self._dbDocDict['author'])

class IssueVote(ArrayDocument):
    _dbfield = 'votes.person' # dot.name for updating
    person = LinkDescriptor('person', fetch_person)
    parent = LinkDescriptor('parent', fetch_parent_issue, noData=True)


class Issue(Document):
    '''interface for a question raised about a paper '''

    # attrs that will only be fetched if accessed by user
    paper = LinkDescriptor('paper', fetch_paper)
    author = LinkDescriptor('author', fetch_person)

    # custom attr constructors
    _attrHandler = dict(
        votes=SaveAttrList(IssueVote, insertNew=False),
        )

class SIG(Document):
    '''interface for a Specific Interest Group'''
    useObjectId = False # input data will supply _id
    _requiredFields = ('name',)

    # attrs that will only be fetched if accessed by user
    members = LinkDescriptor('members', fetch_sig_members, noData=True)
    papers = LinkDescriptor('papers', fetch_sig_papers, noData=True)
    recommendations  = LinkDescriptor('recommendations', fetch_sig_recs,
                                      noData=True)
    interests  = LinkDescriptor('interests', fetch_sig_interests, noData=True)
    def get_interests(self):
        'return dict of paper:[people]'
        d = {}
        for interest in self.interests:
            try:
                d[interest.parent].append(interest.author)
            except KeyError:
                d[interest.parent] = [interest.author]
        return d
    def get_local_url(self):
        return '/topics/' + str(self._id)


# current unused
class SIGLink(ArrayDocument):
    _dbfield = 'sigs.sig' # dot.name for updating
    sig = LinkDescriptor('sig', fetch_sig)
    parent = LinkDescriptor('parent', fetch_parent_person, noData=True)

    def _add_merge(self, other):
        try:
            self._mergeLinks.append(other)
        except AttributeError:
            self._mergeLinks = [other]

class GplusPersonData(EmbeddedDocument):
    'store Google+ data for a user as subdocument of Person'
    _dbfield = 'gplus.id'
    parent = LinkDescriptor('parent', fetch_parent_person, noData=True)
    subscriptions = LinkDescriptor('subscriptions', fetch_gplus_subs,
                                   noData=True)
    def _query_external(self, userID):
        'obtain user info from Google+ API server'
        import gplus
        return gplus.publicAccess.get_person_info(userID)
    def _insert_parent(self, d):
        'create Person document in db for this gplus.id'
        gps = GplusSubscriptions(docData=dict(_id=d['id']))
        self.__dict__['subscriptions'] =  gps # bypass LinkDescriptor
        p = Person(docData=dict(name=d['displayName']))
        gps.update_subscribers(p._id)
        return p
    def update_posts(self, maxDays=20):
        'get new posts from this person, updating old posts with new replies'
        import gplus
        oauth = gplus.publicAccess
        postIt = oauth.get_person_posts(self.id)
        l = [p for p in oauth.load_recent_posts(postIt, maxDays)
             if getattr(p, '_isNewInsert', False)]
        return l
    def update_subs_from_gplus(self, subs=None):
        oldSubs = self.parent._dbDocDict.get('subscriptions', [])
        gplusSubs = set()
        if subs is None:
            subs = getattr(self.subscriptions, 'subs', ())
        for d in subs:
            try: # find subset that map to Person
                p = self.__class__(d['id']).parent # find Person record
                gplusSubs.add(p._id)
            except KeyError:
                pass
        oldSubsSet = set(oldSubs)
        if gplusSubs == oldSubsSet:
            return False
        l = filter(lambda x:x in gplusSubs, oldSubs) # preserve order
        l += list(gplusSubs - oldSubsSet) # append new additions
        self.parent.update(dict(subscriptions=l)) # save to db
        return True



class GplusSubscriptions(Document):
    'for a gplus member, store his array of gplus subscriptions (his circles)'
    useObjectId = False # input data will supply _id
    gplusPerson = LinkDescriptor('gplusPerson', fetch_gplus_by_id,
                                 noData=True)
    def update_subscriptions(self, doc, subs):
        if getattr(self, 'etag', None) != doc['etag']:
            subs = list(subs) # actually get the data from iterator
            self.update(dict(subs=subs, etag=doc['etag'],
                             totalItems=doc['totalItems'])) # save to db
            return subs # subscriptions changed
    def update_subscribers(self, personID):
        '''when Person first inserted to db, connect to pending
        subscriptions by appending our new personID.'''
        for gplusID in self.find({'subs.id':self._id}):
            Person.coll.update({'gplus.id': gplusID},
                               {'$push': {'subscriptions':personID}})


def get_interests_sorted(d):
    'get topics sorted from most-used to least-used'
    l = [(len(v),k) for (k,v) in d.items()]
    l.sort(reverse=True)
    return [(t[1], d[t[1]]) for t in l]


class Person(Document):
    '''interface to a stable identity tied to a set of publications '''
    _requiredFields = ('name',)
    # attrs that will only be fetched if accessed by user
    papers = LinkDescriptor('papers', fetch_author_papers, noData=True)
    recommendations = LinkDescriptor('recommendations', fetch_recs,
                                     noData=True)
    subscriptions = LinkDescriptor('subscriptions', fetch_people,
                                   missingData=())
    subscribers = LinkDescriptor('subscribers', fetch_subscribers,
                                 noData=True)
    posts = LinkDescriptor('posts', fetch_person_posts, noData=True)
    replies = LinkDescriptor('replies', fetch_person_replies, noData=True)
    interests = LinkDescriptor('interests', fetch_person_interests, noData=True)

    # custom attr constructors
    _attrHandler = dict(
        email=SaveAttrList(EmailAddress, insertNew=False),
        gplus=SaveAttr(GplusPersonData, insertNew=False),
        ## sigs=SaveAttrList(SIGLink, postprocess=merge_sigs, insertNew=False),
        )

    def authenticate(self, password):
        try:
            return self.password == sha1(password).hexdigest()
        except AttributeError:
            return False
    def set_password(self, password):
        self.update(dict(password=sha1(password).hexdigest()))
    def get_interests(self, sorted=False):
        'return dict of topic:[papers]'
        d = {}
        for interest in self.interests:
            for topic in interest.topics:
                try:
                    d[topic].append(interest.parent)
                except KeyError:
                    d[topic] = [interest.parent]
        if sorted:
            return get_interests_sorted(d)
        return d
    def get_local_url(self):
        return '/people/' + str(self._id)

class ArxivPaperData(EmbeddedDocument):
    'store arxiv data for a paper as subdocument of Paper'
    _dbfield = 'arxiv.id'
    def _query_external(self, arxivID):
        'obtain arxiv data from arxiv.org'
        import arxiv
        arxivID = arxivID.replace('_', '/')
        return arxiv.lookup_papers((arxivID,)).next()
    parent = LinkDescriptor('parent', fetch_parent_paper, noData=True)
    def _insert_parent(self, d):
        'create Paper document in db for this arxiv.id'
        authorNames = [ad['name'] for ad in d['authors']]
        return Paper(docData=dict(title=d['title'], authorNames=authorNames))
    def get_local_url(self):
        return '/arxiv/' + self.id
    def get_source_url(self):
        return 'http://arxiv.org/abs/' + self.id.replace('_', '/')
    def get_downloader_url(self):
        return 'http://arxiv.org/pdf/%s.pdf' % self.id.replace('_', '/')
    def get_hashtag(self):
        return '#arxiv_' + self.id.replace('.', '_').replace('-', '_')
    def get_abstract(self):
        return self.summary

class PubmedPaperData(EmbeddedDocument):
    'store pubmed data for a paper as subdocument of Paper'
    _dbfield = 'pubmed.id'
    def _query_external(self, pubmedID):
        'obtain pubmed doc data from NCBI'
        import pubmed
        return pubmed.get_pubmed_dict(str(pubmedID))
    parent = LinkDescriptor('parent', fetch_parent_paper, noData=True)
    def _insert_parent(self, d):
        'create Paper document in db for this arxiv.id'
        return Paper(docData=dict(title=d['title'],
                                  authorNames=d['authorNames']))
    def get_local_url(self):
        return '/pubmed/' + self.id
    def get_source_url(self):
        return 'http://www.ncbi.nlm.nih.gov/pubmed/' + str(self.id)
    def get_downloader_url(self):
        return 'http://dx.doi.org/' + self.doi
    def get_hashtag(self):
        return '#pubmed_' + str(self.id)
    def get_abstract(self):
        return self.summary


class DoiPaperData(EmbeddedDocument):
    'store DOI data for a paper as subdocument of Paper'
    _dbfield = 'doi.id'
    def __init__(self, fetchID=None, docData={}, parent=None, insertNew=True,
                 DOI=None):
        '''Note the fetchID must be shortDOI; to search for DOI, pass
        DOI kwarg.
        docData, if provided should include keys: id=shortDOI, doi=DOI'''
        import doi
        if fetchID is None and DOI: # must convert to shortDOI
            # to implement case-insensitive search, convert to uppercase
            d = self.coll.find_one({'doi.DOI':DOI.upper()}, {'doi':1})
            if d: # found DOI in our DB
                insertNew = False 
                docData = d['doi']
                self._parent_link = d['_id']
            else: # have to query shortdoi.org to get shortDOI
                fetchID = doi.map_to_shortdoi(DOI)
                self._DOI = DOI # cache this temporarily
        EmbeddedDocument.__init__(self, fetchID, docData, parent, insertNew)
    def _query_external(self, fetchID):
        'obtain doc data from crossref / NCBI'
        import doi
        try:
            DOI = self._DOI # use cached value
        except AttributeError: # retrieve from shortdoi.org
            DOI = doi.map_to_doi(fetchID)
        doiDict, pubmedDict = doi.get_pubmed_and_doi(DOI)
        doiDict['id'] = fetchID # shortDOI
        if pubmedDict:
            self._pubmedDict = pubmedDict
            try: # use abstract from pubmed if available
                doiDict['summary'] = pubmedDict['summary']
            except KeyError:
                pass
        doiDict['doi'] = DOI
        return doiDict
    parent = LinkDescriptor('parent', fetch_parent_paper, noData=True)
    def _insert_parent(self, d):
        'create Paper document in db for this arxiv.id'
        d = dict(title=d['title'], authorNames=d['authorNames'])
        try:
            d['pubmed'] = self._pubmedDict
        except AttributeError:
            pass
        return Paper(docData=d)
    def insert(self, d):
        d['DOI'] = d['doi'].upper() # for case-insensitive search
        return EmbeddedDocument.insert(self, d)
    def get_local_url(self):
        return '/shortDOI/' + self.id
    def get_source_url(self):
        try:
            return 'http://www.ncbi.nlm.nih.gov/pubmed/' + \
                   str(self.parent.pubmed.id)
        except AttributeError:
            return self.get_downloader_url()
    def get_downloader_url(self):
        return 'http://dx.doi.org/' + self.doi
    def get_hashtag(self):
        return '#shortDOI_' + str(self.id)
    def get_abstract(self):
        return self.summary


class Paper(Document):
    '''interface to a specific paper '''
    # attrs that will only be fetched if accessed by user
    authors = LinkDescriptor('authors', fetch_people)
    references = LinkDescriptor('references', fetch_papers,
                                missingData=())
    issues = LinkDescriptor('issues', fetch_issues,
                            noData=True, missingData=())
    sigs = LinkDescriptor('sigs', fetch_sigs, missingData=())

    # custom attr constructors
    _attrHandler = dict(
        recommendations=SaveAttrList(Recommendation, insertNew=False),
        posts=SaveAttrList(Post, insertNew=False),
        replies=SaveAttrList(Reply, insertNew=False),
        interests=SaveAttrList(PaperInterest, insertNew=False),
        arxiv=SaveAttr(ArxivPaperData, insertNew=False),
        pubmed=SaveAttr(PubmedPaperData, insertNew=False),
        doi=SaveAttr(DoiPaperData, insertNew=False),
        )
    _get_value_attrs = ('arxiv', 'pubmed', 'doi')
    def get_interests(self, sorted=False):
        'return dict of SIG:[people]'
        d = {}
        for interest in getattr(self, 'interests', ()):
            for topic in interest.topics:
                try:
                    d[topic].append(interest.author)
                except KeyError:
                    d[topic] = [interest.author]
        if sorted:
            return get_interests_sorted(d)
        return d
    def get_local_url(self):
        return '/paper/' + str(self._id)
                

def hashtag_to_spnetID(s, subs=((re.compile('([a-z])_([a-z])'), r'\1-\2'),
                                (re.compile('([0-9])_([0-9])'), r'\1.\2'))):
    'convert 1234_5678 --> 1234.5678 and gr_qc_12345 --> gr-qc_12345'
    for pattern, replace in subs:
        s = pattern.sub(replace, s)
    return s


def get_paper_from_hashtag(t, arxivRE=re.compile('#arxiv_([a-z0-9_]+)'),
                           pubmedRE=re.compile('#pubmed_([0-9]+)'),
                           shortdoiRE=re.compile('#shortDOI_([a-zA-Z0-9]+)')):
    'search text for first paper hashtag and return paper object for that ID'
    m = arxivRE.search(t)
    if m:
        arxivID = hashtag_to_spnetID(str(m.group(1)))
        return ArxivPaperData(arxivID, insertNew='findOrInsert').parent
    m = pubmedRE.search(t)
    if m:
        pubmedID = str(m.group(1))
        return PubmedPaperData(pubmedID, insertNew='findOrInsert').parent
    m = shortdoiRE.search(t)
    if m:
        shortDOI = str(m.group(1))
        return DoiPaperData(shortDOI, insertNew='findOrInsert').parent


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
                post = Post(d['id'])
                if getattr(post, 'etag', None) == d.get('etag', ''):
                    yield post
                    continue # matches DB record, so nothing to do
            except KeyError:
                pass
        if post is None: # extract data for saving post to DB
            paper = get_paper_from_hashtag(content)
            if paper is None:
                continue # no link to a paper, so nothing to save.
            userID = get_user(d)
            author = find_or_insert_person(userID)
            d['author'] = author._id
            d['text'] =  content
            if process_post:
                process_post(d)
            if isRec: # see if rec already in DB
                try:
                    post = Recommendation((paper._id, author._id))
                    if getattr(post, 'etag', None) == d.get('etag', ''):
                        yield post
                        continue # matches DB record, so nothing to do
                except KeyError: # need to save new record to DB
                    post = Recommendation(docData=d, parent=paper)
            else:
                post = Post(docData=d, parent=paper)
        yield post
        if get_replycount(d) > 0:
            for c in get_post_comments(d['id']):
                if process_reply:
                    process_reply(c)
                try:
                    r = Reply(c['id'])
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
                r = Reply(docData=c, parent=post._parent_link)


class Tag(Document):
    'a specific keyword tag'
    pass
    ## def _new_fields(self):
    ##     'check that new tag is unique before inserting'
    ##     try:
    ##         name = self._dbDocDict['name']
    ##     except KeyError:
    ##         raise ValueError('new Tag has no name attribute!')
    ##     if list(self.__class__.find(dict(name=name))):
    ##         raise ValueError('Tag "%s" already exists!' % name)

# connect forward declarations to their target classes
fetch_paper.klass = Paper
fetch_parent_issue.klass = Issue
fetch_post.klass = Post
fetch_sig.klass = SIG
fetch_sigs.klass = SIG
fetch_person.klass = Person
fetch_papers.klass = Paper
fetch_people.klass = Person
fetch_parent_person.klass = Person
fetch_parent_paper.klass = Paper
fetch_author_papers.klass = Paper
fetch_subscribers.klass = Person
fetch_sig_members.klass = Person
fetch_sig_papers.klass = Paper
fetch_sig_recs.klass = Recommendation
fetch_sig_interests.klass = PaperInterest
fetch_issues.klass = Issue
fetch_person_posts.klass = Post
fetch_person_replies.klass = Reply
fetch_person_interests.klass = PaperInterest
fetch_gplus_by_id.klass = GplusPersonData
fetch_gplus_subs.klass = GplusSubscriptions

##################################################################

def get_or_create_person(d, subdoc, idField, nameField):
    try:
        p = Person.find_obj({subdoc + '.' + idField:d[idField]}).next()
    except StopIteration:
        p = Person(docData={'name':d[nameField], subdoc:d})
    return p
