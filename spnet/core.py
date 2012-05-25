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
    def _set_coll(self, dbconn):
        self._dbconn = dbconn
        self.coll = getattr(dbconn, self._dbname)
    def store_attrs(self, d):
        ''
        try:
            self._dbDocDict.update(d)
        except AttributeError:
            self._dbDocDict = d
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
        d = self._dbDocDict
        if saveDict:
            d = d.copy()
            d.update(saveDict)
        self._id = self.coll.insert(d)

    def update(self, updateDict):
        self.coll.update({'_id': self._id}, {'$set': updateDict})
        self.store_attrs(updateDict)
        
    def delete(self):
        self.coll.remove(self._id)

    def __cmp__(self, other):
        return cmp(self._id, other._id)

class EmbeddedDocument(Document):
    'stores a document inside another document in mongoDB'
    def insert(self):
        self.coll.update({'_id': self._parentID},
                         {'$set': {self._dbfield: self._dbDocDict}})
    def update(self, updateDict):
        'update the existing embedded doc fields in the parent document'
        self._dbDocDict.update(updateDict)
        d = {}
        for k,v in updateDict.items():
            d['.'.join((self._dbfield, k))] = v
        self.coll.update({'_id': self._parentID}, {'$set': d})
    def __cmp__(self, other):
        return cmp((self._parentID,self._dbfield),
                   (other._parentID,other._dbfield))
        
class ArrayDocument(Document):
    'stores a document inside an array in mongoDB'
    def _get_doc(self, useArrayKey=False):
        'retrieve DB array record containing this document'
        arrayField, keyField = self._dbfield.split('.')
        if useArrayKey:
            d = self.coll.find_one({self._dbfield: self._arrayKey},
                                   {arrayField: 1})
            if not d:
                raise KeyError('no such record: %s=%s'
                               % (self._dbfield, self._arrayKey))
            self._parentID = d['_id']
        else:
            d = self.coll.find_one(self._parentID, {arrayField: 1})
            if not d:
                raise KeyError('no such record: _id=%s' % self._parentID)
        for record in d[arrayField]:
            if record[keyField] == self._arrayKey:
                return record
        raise ValueError('no matching ArrayDocument!')
    def insert(self, saveDict=None):
        'append to the target array in the parent document'
        arrayField = self._dbfield.split('.')[0]
        d = self._dbDocDict
        if saveDict:
            d = d.copy()
            d.update(saveDict)
        self.coll.update({'_id': self._parentID},
                         {'$push': {arrayField: d}})
    def update(self, updateDict):
        'update the existing record in the array in the parent document'
        self._dbDocDict.update(updateDict)
        arrayField = self._dbfield.split('.')[0]
        d = {}
        for k,v in updateDict.items():
            d['.'.join((arrayField, '$', k))] = v
        self.coll.update({'_id': self._parentID,
                          self._dbfield: self._arrayKey}, {'$set': d})

    def delete(self):
        'delete this record from the array in the parent document'
        arrayField, keyField = self._dbfield.split('.')
        self.coll.update({'_id': self._parentID},
                         {'$pull': {arrayField: {keyField: self._arrayKey}}})
        
    def __cmp__(self, other):
        return cmp((self._parentID,self._arrayKey),
                   (other._parentID,other._arrayKey))


##########################################################

# fetch functions for use with LinkDescriptor 

def fetch_person(obj, personID):
    'fetch Person object from the default personColl collection'
    return Person(obj._dbconn, personID)

def fetch_people(obj, people):
    'fetch Person objects for non-null author IDs'
    l = []
    for personID in people:
        if personID:
            l.append(Person(obj._dbconn, personID))
        else:
            l.append(None)
    return l

def fetch_recs(person):
    'return list of Recommendation objects for specified person'
    coll = person._dbconn.dbset.defaultDB
    results = coll.find({'recommendations.author':person._id},
                        {'recommendations':1})
    l = []
    for r in results:
        paperID = person._dbconn.dbset.get_paperID(r['_id'])
        for recDict in r['recommendations']:
            if recDict['author'] == person._id:
                l.append(Recommendation(paperID, person._dbconn,
                                        False, **recDict))
                break
    return l

def fetch_paper(obj, paperID):
    'return Paper object for specified paperID'
    return Paper(obj._dbconn, paperID)

def fetch_issue(obj, issueID):
    'return Paper object for specified paperID'
    return Issue(obj._dbconn, paperID)

def fetch_papers(obj, papers):
    'return list of Paper objects for specified list of paperIDs'
    l = []
    for paperID in papers:
        l.append(Paper(obj._dbconn, paperID))
    return l

def fetch_author_papers(author):
    'return list of Papers with this author'
    l = []
    query = dict(authors=author._id)
    for paperDict in author._dbconn.dbset.defaultDB.find(query):
        l.append(Paper(author._dbconn, insertNew=False,
                       paperDB=author._dbconn.dbset._defaultDB, **paperDict))
    return l

def fetch_subscribers(person):
    'return list of Person obj who subscribe to specified person'
    l = []
    query = dict(subscriptions=person._id)
    for subscriberDict in person.coll.find(query):
        l.append(Person(person._dbconn, insertNew=False,
                        **subscriberDict)) # construct from dict
    return l

def fetch_email_person(email):
    'return Person obj for this email address'
    return Person(email._dbconn, email._parentID)

def fetch_issues(paper):
    'return list of Person obj who subscribe to specified person'
    l = []
    query = dict(paper=paper.paperID)
    coll = paper.coll.database['issues']
    for issueDict in coll.find(query):
        l.append(Issue(dbconn=paper._dbconn, insertNew=False,
                        **issueDict)) # construct from dict
    return l

# custom attribute unwrappers

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
            kwargs.update(d)
            l.append(self.klass(**kwargs))
        setattr(obj, attr, l)



######################################################

# main object classes

class EmailAddress(ArrayDocument):
    _dbname = 'person' # default collection to obtain from dbconn
    _dbfield = 'email.address' # dot.name for updating

    person = LinkDescriptor('person', fetch_email_person, noData=True)

    def __init__(self, address, person=None, dbconn=None, insertNew=True,
                 fetch=False, **kwargs):
        useArrayKey = False
        if isinstance(person, Person):
            self._parentID = person._id
            self.coll = person.coll
            self._dbconn = person._dbconn
        else:
            self._set_coll(dbconn) # get our dbset
            if person:
                self._parentID = person
            else:
                useArrayKey = True
        self._arrayKey = address
        if fetch:
            d = self._get_doc(useArrayKey)
            self.store_attrs(d)
        else:
            d = kwargs.copy()
            d['address'] = address
            self.store_attrs(d)
            if insertNew:
                self.insert()

class Recommendation(ArrayDocument):

    _dbname = 'dbset' # default collection to obtain from dbconn

    # attrs that will only be fetched if accessed by user
    paper = LinkDescriptor('paper', fetch_paper)
    author = LinkDescriptor('author', fetch_person)
    forwards = LinkDescriptor('forwards', fetch_people)

    _dbfield = 'recommendations.author' # dot.name for updating

    def __init__(self, paper, dbconn=None, insertNew=True,
                 fetch=False, **kwargs):
        set_paper_or_id(self, paper, dbconn)
        self._arrayKey = kwargs['author']
        if fetch:
            d = self._get_doc()
            self.store_attrs(d)
        else:
            self.store_attrs(kwargs)
            if insertNew:
                self.insert()

def set_paper_or_id(self, paper, dbconn, collection=None):
    'properly handle paper either as Paper object or ID'
    if isinstance(paper, Paper):
        self.__dict__['paper'] = paper # bypass LinkDescriptor mechanism
        self._parentID = paper._id
        if collection:
            self.coll = paper.coll.database[collection]
        else:
            self.coll = paper.coll
        self._dbconn = paper._dbconn
        return paper.paperID
    elif isinstance(paper, basestring): # treat string as paper ID
        self.paper = paper # use LinkDescriptor mechanism
        self._set_coll(dbconn) # get our dbset
        self.coll, self._parentID = self.coll.get_collection(paper,
                                                    collection=collection)
        return paper
    else:
        raise ValueError('must provide Paper or paperID')

class IssueVote(ArrayDocument):
    _dbname = 'dbset' # default collection to obtain from dbconn
    _collname = 'issues'
    _dbfield = 'votes.person' # dot.name for updating
    person = LinkDescriptor('person', fetch_person)
    issue = LinkDescriptor('issue', fetch_issue)
    def __init__(self, person, issue, dbconn=None, insertNew=True,
                 paperDB='arxiv', fetch=False, **kwargs):
        if isinstance(issue, Issue):
            self._parentID = issue._id
            self.coll = issue.coll
            self._dbconn = issue._dbconn
            self.__dict__['issue'] = issue # bypass LinkDescriptor mechanism
        else: # treat as issue _id
            self._parentID = issue
            self.issue = issue # use LinkDescriptor mechanism
            if not dbconn:
                dbconn = person._dbconn
            self._set_coll(dbconn)
            dbset = self.coll
            self.coll = dbset.get_collection(None, paperDB, self._collname)[0]
        if isinstance(person, Person):
            self._arrayKey = person._id
            self.__dict__['person'] = person # bypass LinkDescriptor mechanism
        else:
            self._arrayKey = person # use LinkDescriptor mechanism
            self.person = person
        if fetch:
            d = self._get_doc()
            self.store_attrs(d)
        else:
            self.store_attrs(kwargs)
            if insertNew:
                self.insert(dict(person=self._arrayKey))


class Issue(Document):
    '''interface for a question raised about a paper '''

    _dbname = 'dbset' # default collection to obtain from dbconn
    _collname = 'issues'

    # attrs that will only be fetched if accessed by user
    paper = LinkDescriptor('paper', fetch_paper)
    author = LinkDescriptor('author', fetch_person)

    # custom attr constructors
    _attrHandler = dict(
        votes=SaveAttr(IssueVote, 'issue', insertNew=False),
        )


    def __init__(self, issueID=None, paper=None, dbconn=None, insertNew=True,
                 paperDB='arxiv', **kwargs):
        saveDict = None
        if paper:
            paperID = set_paper_or_id(self, paper, dbconn, self._collname)
            saveDict = dict(paper=paperID)
            del self._parentID
        else:
            self._set_coll(dbconn)
            dbset = self.coll
            self.coll = dbset.get_collection(None, paperDB, self._collname)[0]
        if issueID:
            d = self.coll.find_one(issueID)
            self.store_attrs(d)
        else:
            self.store_attrs(kwargs)
            if insertNew:
                self.insert(saveDict)


class Person(Document):
    '''interface to a stable identity tied to a set of publications '''

    _dbname = 'person' # default collection to obtain from dbconn

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
        email=SaveAttr(EmailAddress, 'person', insertNew=False),
        )

    def __init__(self, dbconn, personID=None, insertNew=True, **kwargs):
        self._set_coll(dbconn)
        if personID: # fetch basic data, make sure personID valid.
            d = self.coll.find_one(personID)
            if not d:
                raise KeyError('personID %s not found' % personID)
            self.store_attrs(d)
        elif kwargs:
            self.store_attrs(kwargs)
            if insertNew:
                self.insert()
        else:
            raise ValueError('''you must specify either personID for
            retrieval or kwargs for save new record''')

    def authenticate(self, password):
        return self.password == sha1(password).hexdigest()

class Paper(Document):
    '''interface to a specific paper '''

    _dbname = 'dbset' # default collection to obtain from dbconn

    # attrs that will only be fetched if accessed by user
    authors = LinkDescriptor('authors', fetch_people)
    references = LinkDescriptor('references', fetch_papers)
    issues = LinkDescriptor('issues', fetch_issues,
                            noData=True)

    # custom attr constructors
    _attrHandler = dict(
        recommendations=SaveAttr(Recommendation, 'paper', insertNew=False),
        )

    def __init__(self, dbconn, paperID=None, paperDB='arxiv',
                 insertNew=True, **kwargs):
        self._set_coll(dbconn)
        self.dbset = self.coll
        del self.coll
        if paperID:
            if kwargs: # record what collection this came from
                self.coll, self._id = self.dbset.get_collection(paperID)
            else: # retrieve document dict
                kwargs = self._get_doc(paperID)
            try: # handle redirect to primary record in another paperDB
                paperID = kwargs['redirectID']
            except KeyError:
                pass
            else:
                kwargs = self._get_doc(paperID)
            self.paperID = paperID
            self.store_attrs(kwargs)
        elif kwargs: # create new db document
            self.coll = self.dbset.get_collection(None, paperDB)[0]
            try:
                self.paperID = self.dbset.get_paperID(kwargs['_id'], paperDB)
            except KeyError:
                pass
            self.store_attrs(kwargs)
            if insertNew:
                self.insert()
                self.paperID = self.dbset.get_paperID(self._id, paperDB)
        else:
            raise ValueError('no paperID or mongoDict?')

    def _get_doc(self, paperID):
        'get document from appropriate paperDB based on paperID'
        self.coll, self._id = self.dbset.get_collection(paperID)
        d = self.coll.find_one(self._id)
        if not d:
            raise KeyError('paperID %s not found' % paperID)
        return d



