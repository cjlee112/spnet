from base import *
from hashlib import sha1
import re
from datetime import datetime
import errors
import thread
import latex


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
fetch_sig = FetchObj(None)
fetch_sigs = FetchList(None)
fetch_people = FetchList(None)
fetch_papers = FetchList(None)
fetch_parent_issue = FetchParent(None)
fetch_parent_person = FetchParent(None)
fetch_parent_paper = FetchParent(None)
fetch_author_papers = FetchQuery(None, lambda author:dict(authors=author._id))
fetch_subscribers = FetchQuery(None, lambda person:
                               {'subscriptions.author':person._id})
fetch_sig_members = FetchQuery(None, lambda sig: {'sigs.sig':sig._id})
fetch_sig_papers = FetchQuery(None, lambda sig: {'sigs':sig._id})
fetch_sig_recs = FetchQuery(None, lambda sig:
                            {'recommendations.sigs':sig._id})
fetch_sig_posts = FetchQuery(None, lambda sig:
                            {'posts.sigs':sig._id})
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


class AuthorInfo(object):
    def get_author_name(self):
        try:
            return self.actor['displayName']
        except (AttributeError, KeyError):
            return self.author.name # fall back to database query
    def get_author_url(self):
        return '/people/' + str(self._dbDocDict['author'])
    def get_text(self, showLatex=True):
        if showLatex:
            return latex.convert_tex_dollars(self.text)
        else:
            return self.text

def get_replies(self):
    'used by both Post and Recommendation to find replies'
    try:
        docID = self.id
    except AttributeError:
        return
    for r in getattr(self.parent, 'replies', ()):
        if r._dbDocDict['replyTo'] == docID:
            yield r

def report_topics(self, d, attr='sigs', method='insert', personAttr='author'):
    'wrap insert() or update() to insert topics into author Person record'
    try:
        topics = d[attr]
    except KeyError:
        pass
    else:
        personID = d[personAttr]
        Person.coll.update({'_id': personID},
                           {'$addToSet': {'topics': {'$each':topics}}})
    return getattr(super(self.__class__, self), method)(d)

class Recommendation(ArrayDocument, AuthorInfo):
    _dbfield = 'recommendations.author' # dot.name for updating
    useObjectId = False # input data will supply _id
    _timeStampField = 'published' # auto-add timestamp if missing
    # attrs that will only be fetched if accessed by user
    parent = LinkDescriptor('parent', fetch_parent_paper, noData=True)
    author = LinkDescriptor('author', fetch_person)
    forwards = LinkDescriptor('forwards', fetch_people)
    sigs = LinkDescriptor('sigs', fetch_sigs, missingData=())

    get_replies = get_replies
    insert = lambda self,d:report_topics(self, d)
    update = lambda self,d:report_topics(self, d, method='update')
    def get_local_url(self):
        return '/papers/' + str(self._parent_link) + '/recs/' + \
               str(self._dbDocDict['author'])

class Post(UniqueArrayDocument, AuthorInfo):
    _dbfield = 'posts.id' # dot.name for updating
    _timeStampField = 'published' # auto-add timestamp if missing
    # attrs that will only be fetched if accessed by getattr
    parent = LinkDescriptor('parent', fetch_parent_paper, noData=True)
    author = LinkDescriptor('author', fetch_person)
    sigs = LinkDescriptor('sigs', fetch_sigs, missingData=())
    get_replies = get_replies
    insert = lambda self,d:report_topics(self, d)
    update = lambda self,d:report_topics(self, d, method='update')

def fetch_post_or_rec(obj, fetchID):
    for post in getattr(obj.parent, 'posts', ()):
        if getattr(post, 'id', ('uNmAtChAbLe',)) == fetchID:
            return post
    for rec in getattr(obj.parent, 'recommendations', ()):
        if getattr(rec, 'id', ('uNmAtChAbLe',)) == fetchID:
            return rec
    raise KeyError('No post or rec found with id=' + str(fetchID))


class Reply(UniqueArrayDocument, AuthorInfo):
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
    insert = lambda self,d:report_topics(self, d, 'topics')
    update = lambda self,d:report_topics(self, d, 'topics', method='update')
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
    posts  = LinkDescriptor('posts', fetch_sig_posts, noData=True)
    interests  = LinkDescriptor('interests', fetch_sig_interests, noData=True)
    tagRE = re.compile('[A-Za-z][A-Za-z0-9_]+$') # string allowed after #
    @classmethod
    def standardize_id(klass, fetchID):
        'ID must follow hashtag rules (or raise KeyError); rm leading #'
        if fetchID.startswith('#'): # don't include hash in ID
            fetchID = fetchID[1:]
        if not klass.tagRE.match(fetchID):
            raise KeyError('topic does not satisfy hashtag character rules: '
                           + fetchID)
        return fetchID
    @classmethod
    def find_or_insert(klass, fetchID, published=None, **kwargs):
        'save to db if not already present, after checking ID validity'
        fetchID = klass.standardize_id(fetchID)
        if published is None:
            published = datetime.utcnow() # ensure timestamp
        return base_find_or_insert(klass, fetchID, name='#' + fetchID,
                                   published=published, **kwargs)
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



class TopicOptions(ArrayDocument):
    _dbfield = 'topicOptions.topic' # dot.name for updating
    topic = LinkDescriptor('topic', fetch_sig)

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
        p = Person(docData=dict(name=d['displayName']))
        docData = dict(author=p._id, gplusID=d['id'], topics=[])
        thread.start_new_thread(p.update_subscribers,
                                (GplusSubscriptions, docData, d['id']))
        return p
    def update_posts(self, maxDays=20, **kwargs):
        'get new posts from this person, updating old posts with new replies'
        import gplus
        oauth = gplus.publicAccess
        postIt = oauth.get_person_posts(self.id)
        l = [p for p in oauth.find_or_insert_posts(postIt, maxDays=maxDays,
                                                   **kwargs)
             if getattr(p, '_isNewInsert', False)]
        return l
    def init_subscriptions(self, doc, subs):
        'save GplusSubscriptions to db, from doc and subs data'
        d = dict(_id=self.id, subs=list(subs), etag=doc['etag'],
                 totalItems=doc['totalItems'])
        gps = GplusSubscriptions(docData=d)
        self.__dict__['subscriptions'] =  gps # bypass LinkDescriptor
    def update_subscriptions(self, doc, subs):
        try:
            gplusSub = self.subscriptions # use existing record
        except KeyError:
            newSubs = self.init_subscriptions(doc, subs) # create new
        else: # see if we have new subscriptions
            newSubs = gplusSub.update_subscriptions(doc, subs)
            if newSubs is None: # nothing to do
                return
        self.update_subs_from_gplus(newSubs) # update Person.subscriptions

    def update_subs_from_gplus(self, subs=None):
        '''see if we can update Person.subscriptions based on
        subs (list of NEW gplus person IDs).
        If subs is None, update based on our GplusSubscriptions.subs'''
        gplusSubs = set([d['id'] for d in self.subscriptions.subs])
        l = []
        for d in self.parent._dbDocDict.get('subscriptions', ()):
            try: # filter old subscriptions
                if d['gplusID'] in gplusSubs: # still in our subscriptions
                    l.append(d)
            except KeyError:
                l.append(d) # from some other service, so keep
        if subs is None: # all subscriptions are new
            subs = gplusSubs
        for gplusID in subs: # append new additions
            try: # find subset that map to Person
                p = self.__class__(gplusID).parent # find Person record
                l.append(dict(author=p._id, gplusID=gplusID, topics=[]))
            except KeyError:
                pass
        self.parent.update(dict(subscriptions=l)) # save to db
        self.parent._forceReload = True # safe way to refresh view



class GplusSubscriptions(Document):
    'for a gplus member, store his array of gplus subscriptions (his circles)'
    useObjectId = False # input data will supply _id
    _subscriptionIdField = 'subs.id' # query to find a subscription by ID
    gplusPerson = LinkDescriptor('gplusPerson', fetch_gplus_by_id,
                                 noData=True)
    def update_subscriptions(self, doc, subs):
        '''if G+ subscriptions changed, save and return the new list;
        otherwise return None'''
        if getattr(self, 'etag', None) == doc['etag']:
            return None # no change, so nothing to do
        subs = list(subs) # actually get the data from iterator
        oldSubsSet = set([d['id'] for d in self.subs])
        self.update(dict(subs=subs, etag=doc['etag'],
                         totalItems=doc['totalItems'])) # save to db
        self.subs = subs
        newSubsSet = set([d['id'] for d in subs])
        return newSubsSet - oldSubsSet # new subscriptions


def get_interests_sorted(d):
    'get topics sorted from most-used to least-used'
    l = [(len(v),k) for (k,v) in d.items()]
    l.sort(reverse=True)
    return [(t[1], d[t[1]]) for t in l]


class Subscription(ArrayDocument):
    _dbfield = 'subscriptions.author' # dot.name for updating
    # attrs that will only be fetched if accessed by user
    author = LinkDescriptor('author', fetch_person)
    topics = LinkDescriptor('topics', fetch_sigs, missingData=())



class Person(Document):
    '''interface to a stable identity tied to a set of publications '''
    _requiredFields = ('name',)
    # attrs that will only be fetched if accessed by user
    papers = LinkDescriptor('papers', fetch_author_papers, noData=True)
    recommendations = LinkDescriptor('recommendations', fetch_recs,
                                     noData=True)
    subscribers = LinkDescriptor('subscribers', fetch_subscribers,
                                 noData=True)
    posts = LinkDescriptor('posts', fetch_person_posts, noData=True)
    replies = LinkDescriptor('replies', fetch_person_replies, noData=True)
    interests = LinkDescriptor('interests', fetch_person_interests, noData=True)
    readingList = LinkDescriptor('readingList', fetch_papers, missingData=())

    # custom attr constructors
    _attrHandler = dict(
        email=SaveAttrList(EmailAddress, insertNew=False),
        gplus=SaveAttr(GplusPersonData, insertNew=False),
        subscriptions = SaveAttrList(Subscription, insertNew=False),
        topicOptions = SaveAttrList(TopicOptions, insertNew=False),
        )

    def authenticate(self, password):
        try:
            return self.password == sha1(password).hexdigest()
        except AttributeError:
            return False
    def set_password(self, password):
        self.update(dict(password=sha1(password).hexdigest()))
    def get_interests(self, sorted=False):
        'return dict of {topicID:[paperID,]}'
        d = {}
        for interest in self.interests:
            for topicID in interest._dbDocDict['topics']:
                try:
                    d[topicID].append(interest._parent_link)
                except KeyError:
                    d[topicID] = [interest._parent_link]
        if sorted:
            return get_interests_sorted(d)
        return d
    def get_local_url(self):
        return '/people/' + str(self._id)
    def update_subscribers(self, klass, docData, subscriptionID):
        '''when Person first inserted to db, connect to pending
        subscriptions by appending our new personID.'''
        for subID in klass.find({klass._subscriptionIdField: subscriptionID}):
            p = self.coll.find_one({'gplus.id': subID}, {'_id':1})
            if p is not None:
                personID = p['_id']
                Subscription((personID, self._id), docData=docData,
                             parent=personID, insertNew='findOrInsert')
    def get_topics(self):
        topicOptions = {}
        for tOpt in self.topicOptions:
            topicOptions[tOpt._dbDocDict['topic']] = tOpt
        l = []
        for topic in getattr(self, 'topics', ()):
            try:
                tOpt = topicOptions[topic]
                l.append((topic, getattr(tOpt, 'fromMySubs', 'low'),
                         getattr(tOpt, 'fromOthers', 'low')))
            except KeyError:
                l.append((topic, 'low', 'low'))
        order = dict(hide=0, low=1, medium=2, high=3)
        l.sort(lambda x,y:cmp(order.get(x[1], -1), order.get(y[1], -1)), 
               reverse=True)
        return l
            

class ArxivPaperData(EmbeddedDocument):
    'store arxiv data for a paper as subdocument of Paper'
    _dbfield = 'arxiv.id'
    def _query_external(self, arxivID):
        'obtain arxiv data from arxiv.org'
        import arxiv
        arxivID = arxivID.replace('_', '/')
        try:
            return arxiv.lookup_papers((arxivID,)).next()
        except StopIteration:
            raise KeyError('arxivID not found: ' + arxivID)
    parent = LinkDescriptor('parent', fetch_parent_paper, noData=True)
    def _insert_parent(self, d):
        'create Paper document in db for this arxiv.id'
        return Paper(docData=dict(title=d['title'],
                                  authorNames=d['authorNames']))
    def get_local_url(self):
        return '/arxiv/' + self.id
    def get_source_url(self):
        return 'http://arxiv.org/abs/' + self.id.replace('_', '/')
    def get_downloader_url(self):
        return 'http://arxiv.org/pdf/%s.pdf' % self.id.replace('_', '/')
    def get_hashtag(self):
        return '#arxiv_' + self.id.replace('.', '_').replace('-', '_')
    def get_doctag(self):
        return 'arXiv:' + self.id.replace('_', '/')
    def get_abstract(self, showLatex=False):
        if showLatex:
            return latex.convert_tex_dollars(self.summary)
        else:
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
        try: # connect with DOI record
            DOI = d['doi']
            return DoiPaperData(DOI=DOI, insertNew='findOrInsert',
                                getPubmed=False).parent
        except KeyError: # no DOI, so save as usual
            return Paper(docData=dict(title=d['title'],
                                      authorNames=d['authorNames']))
    def get_local_url(self):
        return '/pubmed/' + self.id
    def get_source_url(self):
        return 'http://www.ncbi.nlm.nih.gov/pubmed/' + str(self.id)
    def get_downloader_url(self):
        try:
            return 'http://dx.doi.org/' + self.doi
        except AttributeError:
            return self.get_source_url()
    def get_hashtag(self):
        return '#pubmed_' + str(self.id)
    def get_doctag(self):
        return 'PMID:' + str(self.id)
    def get_abstract(self, **kwargs):
        return self.summary


class DoiPaperData(EmbeddedDocument):
    'store DOI data for a paper as subdocument of Paper'
    _dbfield = 'doi.id'
    def __init__(self, fetchID=None, docData=None, parent=None,
                 insertNew=True, DOI=None, getPubmed=False):
        '''Note the fetchID must be shortDOI; to search for DOI, pass
        DOI kwarg.
        docData, if provided should include keys: id=shortDOI, doi=DOI'''
        import doi
        self._getPubmed = getPubmed
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
        doiDict = doi.get_doi_dict(DOI)
        doiDict['id'] = fetchID # shortDOI
        doiDict['doi'] = DOI
        if self._getPubmed:
            try:
                pubmedDict = doi.get_pubmed_from_doi(DOI)
                if pubmedDict:
                    self._pubmedDict = pubmedDict # cache for saving to parent
            except errors.TimeoutError:
                pass
        return doiDict
    parent = LinkDescriptor('parent', fetch_parent_paper, noData=True)
    def _insert_parent(self, d):
        'create Paper document in db for this arxiv.id'
        d = dict(title=d['title'], authorNames=d['authorNames'])
        try:
            d['pubmed'] = self._pubmedDict # save associated pubmed data
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
    def get_doctag(self):
        return 'shortDOI:' + str(self.id)
    def get_abstract(self, **kwargs):
        try:
            return self.summary
        except AttributeError:
            return 'Click <A HREF="%s">here</A> for the Abstract' \
                   % self.get_downloader_url()


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
    def get_interests(self, people=None, sorted=False):
        'return dict of {topicID:[person,]}'
        d = {}
        for interest in getattr(self, 'interests', ()):
            personID = interest._dbDocDict['author']
            if people and personID not in people:
                continue # only include interests of these people
            p = Person(docData=dict(_id=personID, name=interest._dbDocDict.
                                    get('authorName', 'user')), 
                       insertNew=False) # dummy object only has name attr
            for topicID in interest._dbDocDict['topics']: # no db query!
                try:
                    d[topicID].append(p)
                except KeyError:
                    d[topicID] = [p]
        if sorted:
            return get_interests_sorted(d)
        return d
    def get_local_url(self):
        return '/paper/' + str(self._id)
                



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
fetch_sig_posts.klass = Post
fetch_sig_interests.klass = PaperInterest
fetch_issues.klass = Issue
fetch_person_posts.klass = Post
fetch_person_replies.klass = Reply
fetch_person_interests.klass = PaperInterest
fetch_gplus_by_id.klass = GplusPersonData
fetch_gplus_subs.klass = GplusSubscriptions

##################################################################


