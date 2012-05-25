#import spn_config
from bson.objectid import ObjectId
from hashlib import sha1


class LinkDescriptor(object):
    '''property that fetches data only when accessed.
    caches obj.ATTR link data as obj._ATTR_link'''
    def __init__(self, attr, fetcher, noData=False,
                 missingData=False, **kwargs):
        self.attr = attr
        self.fetcher = fetcher
        self.kwargs = kwargs
        self.noData = noData
        self.missingData = missingData
    def __get__(self, obj, objtype):
        'actually fetch the object(s) specified by cached data'
        try: # return the cached attribute
            return obj.__dict__[self.attr]
        except KeyError:
            pass
        if self.noData: # just fetch using object
            target = self.fetcher(obj, **self.kwargs)
        else: # fetching using cached data
            try:
                data = getattr(obj, '_' + self.attr + '_link')
            except AttributeError:
                if self.missingData is not False:
                    return self.missingData
                raise
            target = self.fetcher(obj, data, **self.kwargs)
        # Save in __dict__ to evade __set__.
        obj.__dict__[self.attr] = target
        return target
    def __set__(self, obj, data):
        'cache some link data for fetching later'
        setattr(obj, '_' + self.attr + '_link', data)

# base document classes

class Document(object):
    'base class provides flexible method for storing dict as attr objects'
    def __init__(self, fetchID=None, docData=None, docLinks={},
                 insertNew=True):
        if fetchID:
            d = self._get_doc(fetchID)
            self.store_attrs(d)
        else:
            self.store_data_links(docData, docLinks)
            if insertNew:
                self.insert()

    def _get_doc(self, fetchID):
        'get doc dict from DB'
        d = self.coll.find_one(fetchID)
        if not d:
            raise KeyError('%s %s not found'
                           % (self.__class__.__name__, fetchID))
        return d

    def store_data_links(self, docData, docLinks):
        'store IDs and objects properly'
        self.store_attrs(docData)
        for k,v in docLinks.items():
            self._dbDocDict[k] = v._id
            self.__dict__[k] = v # bypass LinkDescriptor mechanism
            
    def store_attrs(self, d):
        'store as both dict for saving to DB, and processed attributes'
        try: # keep a copy
            self._dbDocDict.update(d)
        except AttributeError:
            self._dbDocDict = d.copy()
        attrHandler = getattr(self, '_attrHandler', {})
        l = []
        for attr, v in d.items():
            try:
                saveFunc = attrHandler[attr]
            except KeyError:
                setattr(self, attr, v)
            else:
                l.append((saveFunc, attr, v))
        for saveFunc, attr, v in l: # run saveFuncs after regular attrs
            saveFunc(self, attr, v)

    def insert(self, saveDict=None):
        'insert into DB'
        d = self._dbDocDict
        if saveDict:
            d = d.copy()
            d.update(saveDict)
        self._id = self.coll.insert(d)

    def update(self, updateDict):
        'update the specified fields in the DB'
        self.coll.update({'_id': self._id}, {'$set': updateDict})
        self.store_attrs(updateDict)
        
    def delete(self):
        'delete this record from the DB'
        self.coll.remove(self._id)

    def __cmp__(self, other):
        return cmp(self._id, other._id)

class EmbeddedDocument(Document):
    'stores a document inside another document in mongoDB'
    def insert(self):
        self.coll.update({'_id': self._parent_link},
                         {'$set': {self._dbfield: self._dbDocDict}})
    def update(self, updateDict):
        'update the existing embedded doc fields in the parent document'
        self._dbDocDict.update(updateDict)
        d = {}
        for k,v in updateDict.items():
            d['.'.join((self._dbfield, k))] = v
        self.coll.update({'_id': self._parent_link}, {'$set': d})
    def __cmp__(self, other):
        return cmp((self._parent_link,self._dbfield),
                   (other._parent_link,other._dbfield))
        
class ArrayDocument(Document):
    'stores a document inside an array in mongoDB'
    def __init__(self, fetchID=None, docData=None, docLinks={},
                 parent=None, insertNew=True):
        if hasattr(parent, 'coll'):
            self._parent_link = parent._id # save its ID
            self.__dict__['parent'] = parent # bypass LinkDescriptor mech
        else:
            self._parent_link = parent
        Document.__init__(self, fetchID, docData, docLinks, insertNew)
    def _get_doc(self, fetchID):
        'retrieve DB array record containing this document'
        self._parent_link,subID = fetchID
        arrayField, keyField = self._dbfield.split('.')
        d = self.coll.find_one(self._parent_link, {arrayField: 1})
        if not d:
            raise KeyError('no such record: _id=%s' % self._parent_link)
        return self._extract_doc(d, arrayField, keyField, subID)
    def _extract_doc(self, d, arrayField, keyField, subID):
        'find record in the array with keyField matching fetchID'
        for record in d[arrayField]:
            if record[keyField] == subID:
                return record
        raise ValueError('no matching ArrayDocument!')
    def _get_id(self):
        'return subID for this array record'
        keyField = self._dbfield.split('.')[1]
        return self._dbDocDict[keyField]
    def insert(self, saveDict=None):
        'append to the target array in the parent document'
        arrayField = self._dbfield.split('.')[0]
        d = self._dbDocDict
        if saveDict:
            d = d.copy()
            d.update(saveDict)
        self.coll.update({'_id': self._parent_link}, {'$push': {arrayField: d}})
    def update(self, updateDict):
        'update the existing record in the array in the parent document'
        self._dbDocDict.update(updateDict)
        arrayField = self._dbfield.split('.')[0]
        d = {}
        for k,v in updateDict.items():
            d['.'.join((arrayField, '$', k))] = v
        subID = self._get_id()
        self.coll.update({'_id': self._parent_link, self._dbfield: subID},
                         {'$set': d})

    def delete(self):
        'delete this record from the array in the parent document'
        arrayField, keyField = self._dbfield.split('.')
        subID = self._get_id()
        self.coll.update({'_id': self._parent_link},
                         {'$pull': {arrayField: {keyField: subID}}})
        
    def __cmp__(self, other):
        try:
            return cmp((self._parent_link, self._get_id()),
                       (other._parent_link, other._get_id()))
        except AttributeError:
            return False


class UniqueArrayDocument(ArrayDocument):
    def _get_doc(self, fetchID):
        'retrieve DB array record containing this document'
        arrayField, keyField = self._dbfield.split('.')
        d = self.coll.find_one({self._dbfield: fetchID}, {arrayField: 1})
        if not d:
            raise KeyError('no such record: %s=%s' % (self._dbfield, fetchID))
        self._parent_link = d['_id'] # save parent ID
        return self._extract_doc(d, arrayField, keyField, fetchID)


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

def fetch_subscribers(person):
    'return list of Person obj who subscribe to specified person'
    l = []
    query = dict(subscriptions=person._id)
    for subscriberDict in person.coll.find(query):
        l.append(Person(person._dbconn, insertNew=False,
                        **subscriberDict)) # construct from dict
    return l


# generic retrieval classes

class FetchObj(object):
    def __init__(self, klass, **kwargs):
        self.klass = klass
        self.kwargs = kwargs
    def __call__(self, obj, fetchID):
        return self.klass(fetchID, **self.kwargs)


class FetchList(FetchObj):
    def __call__(self, obj, fetchIDs):
        l = []
        for fetchID in fetchIDs:
            l.append(self.klass(fetchID, **self.kwargs))
        return l

class FetchQuery(FetchObj):
    def __init__(self, klass, queryFunc, **kwargs):
        FetchObj.__init__(self, klass, **kwargs)
        self.queryFunc = queryFunc
    def __call__(self, obj, **kwargs):
        query = self.queryFunc(obj, **kwargs)
        data = self.klass.coll.find(query)
        l = []
        for d in data:
            l.append(self.klass(docData=d, insertNew=False))
        return l

class FetchParent(FetchObj):
    def __call__(self, obj):
        return self.klass(obj._parent_link, **self.kwargs)


class SaveAttr(object):
    'unwrap list of dicts using specified klass'
    def __init__(self, klass, arg, **kwargs):
        self.klass = klass
        self.kwargs = kwargs
        self.arg = arg
    def __call__(self, obj, attr, data):
        l = []
        for d in data:
            kwargs = self.kwargs.copy()
            kwargs[self.arg] = obj
            l.append(self.klass(docData=d, **kwargs))
        setattr(obj, attr, l)



######################################################

# forward declarations to avoid circular ref problem
fetch_paper = FetchObj(None)
fetch_person = FetchObj(None)
fetch_people = FetchList(None)
fetch_papers = FetchList(None)
fetch_parent_issue = FetchParent(None)
fetch_parent_person = FetchParent(None)
fetch_parent_paper = FetchParent(None)
fetch_author_papers = FetchQuery(None, lambda author:dict(authors=author._id))
fetch_subscribers = FetchQuery(None, lambda person:
                               dict(subscriptions=person._id))
fetch_issues = FetchQuery(None, lambda paper:dict(paper=paper._id))

# main object classes

class EmailAddress(UniqueArrayDocument):
    _dbfield = 'email.address' # dot.name for updating

    parent = LinkDescriptor('parent', fetch_parent_person, noData=True)


class Recommendation(ArrayDocument):
    # attrs that will only be fetched if accessed by user
    parent = LinkDescriptor('parent', fetch_parent_paper, noData=True)
    author = LinkDescriptor('author', fetch_person)
    forwards = LinkDescriptor('forwards', fetch_people)

    _dbfield = 'recommendations.author' # dot.name for updating


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
        votes=SaveAttr(IssueVote, 'parent', insertNew=False),
        )



class Person(Document):
    '''interface to a stable identity tied to a set of publications '''

    # attrs that will only be fetched if accessed by user
    papers = LinkDescriptor('papers', fetch_author_papers, noData=True)
    recommendations = LinkDescriptor('recommendations', fetch_recs,
                                     noData=True)
    subscriptions = LinkDescriptor('subscriptions', fetch_people,
                                   missingData=())
    subscribers = LinkDescriptor('subscribers', fetch_subscribers,
                                 noData=True)

    # custom attr constructors
    _attrHandler = dict(
        email=SaveAttr(EmailAddress, 'parent', insertNew=False),
        )

    def authenticate(self, password):
        return self.password == sha1(password).hexdigest()



class Paper(Document):
    '''interface to a specific paper '''

    # attrs that will only be fetched if accessed by user
    authors = LinkDescriptor('authors', fetch_people)
    references = LinkDescriptor('references', fetch_papers,
                                missingData=())
    issues = LinkDescriptor('issues', fetch_issues,
                            noData=True, missingData=())

    # custom attr constructors
    _attrHandler = dict(
        recommendations=SaveAttr(Recommendation, 'parent', insertNew=False),
        )


# connect forward declarations to their target classes
fetch_paper.klass = Paper
fetch_parent_issue.klass = Issue
fetch_person.klass = Person
fetch_papers.klass = Paper
fetch_people.klass = Person
fetch_parent_person.klass = Person
fetch_parent_paper.klass = Paper
fetch_author_papers.klass = Paper
fetch_subscribers.klass = Person
fetch_issues.klass = Issue

