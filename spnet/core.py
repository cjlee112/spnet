#import spn_config
from bson.objectid import ObjectId
from hashlib import sha1


class LinkDescriptor(object):
    '''property that fetches data only when accessed.
    caches obj.ATTR link data as obj._ATTR_link'''
    def __init__(self, attr, fetcher, noData=False, **kwargs):
        self.attr = attr
        self.fetcher = fetcher
        self.kwargs = kwargs
        self.noData = noData
    def __get__(self, obj, objtype):
        'actually fetch the object(s) specified by cached data'
        if self.noData: # just fetch using object
            target = self.fetcher(obj, **self.kwargs)
        else: # fetching using cached data
            data = getattr(obj, '_' + self.attr + '_link')
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
        for attr, v in d.items():
            try:
                saveFunc = attrHandler[attr]
            except KeyError:
                setattr(self, attr, v)
            else:
                saveFunc(self, attr, v)

    def insert(self):
        self._id = self.coll.insert(self._dbDocDict)

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
    def insert(self):
        'append to the target array in the parent document'
        arrayField = self._dbfield.split('.')[0]
        self.coll.update({'_id': self._parentID},
                         {'$push': {arrayField: self._dbDocDict}})
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

def fetch_authors(obj, authors):
    'fetch Person objects for non-null author IDs'
    l = []
    for personID in authors:
        if personID:
            l.append(Person(obj._dbconn, personID))
        else:
            l.append(None)
    return l

def fetch_recs(person, papers):
    'return list of Recommendation objects for specified list of paperIDs'
    papers = fetch_papers(obj, papers)
    for paper in papers:
        for rec in paper.recommendations:
            if rec._author_link == person._id:
                l.append(rec)
    return l

def fetch_paper(obj, paperID):
    'return Paper object for specified paperID'
    return Paper(obj._dbconn, paperID)

def fetch_papers(obj, papers):
    'return list of Paper objects for specified list of paperIDs'
    l = []
    for paperID in papers:
        l.append(Paper(obj._dbconn, paperID))
    return l

def fetch_subscribers(person):
    'return list of Person obj who subscribe to specified person'
    l = []
    query = dict(subscriptions=ObjectId(person._id))
    for subscriberDict in person.coll.find(query):
        l.append(Person(person._dbconn,
                        mongoDict=subscriberDict)) # construct from dict
    return l

# custom attribute unwrappers

def saveattr_recs(self, attr, recData):
    'construct Recommendation objects and store list on attr'
    l = []
    for d in recData:
        l.append(Recommendation(paper=self, insertNew=False, **d))
    setattr(self, attr, l)




######################################################

# main object classes

class Recommendation(ArrayDocument):

    _dbname = 'dbset' # default collection to obtain from dbconn

    # attrs that will only be fetched if accessed by user
    paper = LinkDescriptor('paper', fetch_paper)
    author = LinkDescriptor('author', fetch_person)
    forwards = LinkDescriptor('forwards', fetch_authors)

    _dbfield = 'recommendations.author' # dot.name for updating

    def __init__(self, paper, paperID=None, dbconn=None, insertNew=True,
                 **kwargs):
        if paper:
            self.__dict__['paper'] = paper # bypass LinkDescriptor mechanism
            self._parentID = paper._id
            self.coll = paper.coll
        elif paperID:
            self._paper_link = paperID
            self._set_coll(dbconn) # get our dbset
            self.coll, self._parentID = self.coll.get_collection(paperID)
        else:
            raise ValueError('must provide Paper or paperID')
        self._arrayKey = kwargs['author']
        self.store_attrs(kwargs)
        if insertNew:
            self.insert()



class Person(Document):
    '''interface to a stable identity tied to a set of publications '''

    _dbname = 'person' # default collection to obtain from dbconn

    # attrs that will only be fetched if accessed by user
    papers = LinkDescriptor('papers', fetch_papers)
    recommendations = LinkDescriptor('recommendations', fetch_recs)
    subscriptions = LinkDescriptor('subscriptions', fetch_authors)
    subscribers = LinkDescriptor('subscribers', fetch_subscribers,
                                 noData=True)

    def __init__(self, dbconn, personID=None, **kwargs):
        self._set_coll(dbconn)
        if personID: # fetch basic data, make sure personID valid.
            d = self.coll.find_one(ObjectId(personID))
            if not d:
                raise KeyError('personID %s not found' % personID)
            self.store_attrs(d)
        elif kwargs:
            self.store_attrs(kwargs)
            if '_id' not in kwargs:
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
    authors = LinkDescriptor('authors', fetch_authors)
    references = LinkDescriptor('references', fetch_papers)

    # custom attr constructors
    _attrHandler = dict(recommendations=saveattr_recs)

    def __init__(self, dbconn, paperID=None, paperDB='arxiv',
                 mongoDict=None):
        self._set_coll(dbconn)
        self.dbset = self.coll
        del self.coll
        if paperID:
            if mongoDict: # record what collection this came from
                self.coll, self._id = self.dbset.get_collection(paperID)
            else: # retrieve document dict
                mongoDict = self._get_doc(paperID)
            try: # handle redirect to primary record in another paperDB
                paperID = mongoDict['redirectID']
            except KeyError:
                pass
            else:
                mongoDict = self._get_doc(paperID)
            self.store_attrs(mongoDict)
            self.paperID = paperID
        elif mongoDict: # create new db document
            self.coll = self.dbset.get_collection(None, paperDB)[0]
            self.store_attrs(mongoDict)
            self.insert()
        else:
            raise ValueError('no paperID or mongoDict?')

    def _get_doc(self, paperID):
        'get document from appropriate paperDB based on paperID'
        self.coll, self._id = self.dbset.get_collection(paperID)
        d = self.coll.find_one(ObjectId(self._id))
        if not d:
            raise KeyError('paperID %s not found' % paperID)
        return d



