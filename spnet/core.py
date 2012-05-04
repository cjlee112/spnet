#import spn_config
import pymongo
from bson.objectid import ObjectId
import datetime
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


class Document(object):
    'base class provides flexible method for storing dict as attr objects'
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
        
    def __cmp__(self, other):
        return cmp(self._id, other._id)

class EmbeddedDocument(Document):
    'stores a document inside another document in mongoDB'
    def insert(self):
        self.coll.update({'_id': self._parentID},
                         {'$set': {self._dbfield: self._dbDocDict}})
        
class ArrayDocument(Document):
    'stores a document inside an array in mongoDB'
    def insert(self):
        'append to the target array in the parent document'
        target = '.'.join(self._dbfield.split('.')[:-1])
        self.coll.update({'_id': self._parentID},
                         {'$push': {target: self._dbDocDict}})
    def update(self, updateDict):
        'replace the existing record in the array in the parent document'
        self._dbDocDict.update(updateDict)
        target = '.'.join(self._dbfield.split('.')[:-1]) + '.$'
        self.coll.update({'_id': self._parentID,
                          self._dbfield: self._arrayKey},
                         {'$set': {target: self._dbDocDict}})
        
    def __cmp__(self, other):
        return cmp((self._parentID,self._arrayKey),
                   (other._parentID,other._arrayKey))


def fetch_person(obj, personID):
    'fetch Person object from the default personColl collection'
    return Person(personColl, personID)

def fetch_authors(obj, authors):
    'fetch Person objects for non-null author IDs'
    l = []
    for personID in authors:
        if personID:
            l.append(Person(personColl, personID))
        else:
            l.append(None)
    return l


class Recommendation(ArrayDocument):

    # attrs that will only be fetched if accessed by user
    paper = LinkDescriptor('paper', fetch_paper)
    author = LinkDescriptor('author', fetch_person)
    forwards = LinkDescriptor('forwards', fetch_authors)

    _dbfield = 'recommendations.author' # dot.name for updating

    def __init__(self, paper, paperID=None, coll=None, insertNew=True,
                 **kwargs):
        if paper:
            self.__dict__['paper'] = paper # bypass LinkDescriptor mechanism
            self._parentID = paper._id
            self.coll = paper.coll
        elif paperID:
            self._paper_link = self._parentID = paperID
            self.coll = coll
        else:
            raise ValueError('must provide Paper or paperID')
        self._arrayKey = kwargs['author']
        self.store_attrs(kwargs)
        if insertNew:
            self.insert()


def saveattr_recs(self, attr, recData):
    'construct Recommendation objects and store list on attr'
    l = []
    for d in recData:
        l.append(Recommendation(paper=self, insertNew=False, **d))
    setattr(self, attr, l)

def fetch_recs(person, papers):
    'return list of Recommendation objects for specified list of paperIDs'
    papers = fetch_papers(obj, papers)
    for paper in papers:
        for rec in paper.recommendations:
            if rec._author_link == person._id:
                l.append(rec)
    return l

def fetch_paper(obj, paperID):
    'return list of Paper objects for specified list of paperIDs'
    return Paper(paperDBset, paperID)

def fetch_papers(obj, papers):
    'return list of Paper objects for specified list of paperIDs'
    l = []
    for paperID in papers:
        l.append(Paper(paperDBset, paperID))
    return l

def fetch_subscribers(person):
    'return list of Person obj who subscribe to specified person'
    l = []
    query = dict(subscriptions=ObjectId(person._id))
    for subscriberDict in person.coll.find(query):
        l.append(Person(mongoDict=subscriberDict)) # construct from dict
    return l


class Person(Document):
    '''interface to a stable identity tied to a set of publications '''

    # attrs that will only be fetched if accessed by user
    papers = LinkDescriptor('papers', fetch_papers)
    recommendations = LinkDescriptor('recommendations', fetch_recs)
    subscriptions = LinkDescriptor('subscriptions', fetch_authors)
    subscribers = LinkDescriptor('subscribers', fetch_subscribers,
                                 noData=True)

    def __init__(self, coll, personID=None, **kwargs):
        self.coll = coll
        if personID: # fetch basic data, make sure personID valid.
            d = coll.find_one(ObjectId(personID)))
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

    # attrs that will only be fetched if accessed by user
    authors = LinkDescriptor('authors', fetch_authors)
    references = LinkDescriptor('references', fetch_papers)

    # custom attr constructors
    _attrHandler = dict(recommendations=saveattr_recs)

    def __init__(self, dbset, paperID=None, mongoDict=None):
        self.dbset = dbset
        if paperID:
            if mongoDict: # record what collection this came from
                self.coll, _id = self.dbset.get_collection(paperID)
            else: # retrieve document dict
                mongoDict = self._get_dict(paperID)
            try: # handle redirect to primary record in another paperDB
                paperID = mongoDict['redirectID']
            except KeyError:
                pass
            else:
                mongoDict = self._get_dict(paperID)
            self.store_attrs(mongoDict)
            self.paperID = paperID

    def _get_dict(self, paperID):
        'get document from appropriate paperDB based on paperID'
        self.coll, _id = self.dbset.get_collection(paperID)
        d = self.coll.find_one(ObjectId(_id))
        if not d:
            raise KeyError('paperID %s not found' % paperID)
        return d



class DBSet(object):
    '''Supports usage of multiple paper databases, using paperID
    given as dbname:id'''
    def __init__(self, dbsetDict, defaultDB):
        self.dbMap = {}
        for dbname, kwargs in dbsetDict.items():
            self.dbMap[dbname] = self.connect_db(**kwargs)
        self.defaultDB = self.dbMap[defaultDB]
    def connect_db(self, db='paperDB', collection='papers', **kwargs):
        c = pymongo.connection.Connection(**kwargs)
        paper_db = c[db]
        paper_coll = paper_db[collection]
        return paper_coll
    def get_collection(self, paperID, dbname=None, collection=None):
        'get collection object containing paper specified as dbname:id'
        _id = None
        if paperID:
            t = paperID.split(':')
            if len(t) < 2:
                raise ValueError('bad paperID: ' + paperID)
            dbname = t[0]
            _id = paperID[len(dbname) + 1:]
        paper_coll = self.dbMap[dbname]
        if collection:
            return paper_coll.database[collection], _id
        else:
            return paper_coll, _id


