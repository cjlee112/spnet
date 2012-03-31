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


class ObjectProxy(object):
    'base class provides flexible method for storing dict as attr objects'
    def save_dict(self, d):
        attrHandler = getattr(self, '_attrHandler', {})
        for attr, v in d.items():
            try:
                saveFunc = attrHandler[attr]
            except KeyError:
                setattr(self, attr, v)
            else:
                saveFunc(self, attr, v)
        


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


class Recommendation(ObjectProxy):

    # attrs that will only be fetched if accessed by user
    author = LinkDescriptor('author', fetch_person)
    forwards = LinkDescriptor('forwards', fetch_authors)

    def __init__(self, paper, **kwargs):
        self.paper = paper
        self.save_dict(kwargs)


def saveattr_recs(self, attr, recData):
    'construct Recommendation objects and store list on attr'
    l = []
    for d in recData:
        l.append(Recommendation(paper=self, **d))
    setattr(self, attr, l)

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


class Person(ObjectProxy):
    '''interface to a stable identity tied to a set of publications '''

    # attrs that will only be fetched if accessed by user
    papers = LinkDescriptor('papers', fetch_papers)
    recommendations = LinkDescriptor('recommendations', fetch_recs)
    subscriptions = LinkDescriptor('subscriptions', fetch_authors)
    subscribers = LinkDescriptor('subscribers', fetch_subscribers,
                                 noData=True)

    def __init__(self, coll, personID=None, mongoDict=None):
        self.coll = coll
        if personID: # fetch basic data, make sure personID valid.
            d = coll.find_one(ObjectId(personID)))
            if not d:
                raise KeyError('personID %s not found' % personID)
            self.save_dict(d)
        elif mongoDict:
            self.save_dict(mongoDict)

    def authenticate(self, password):
        return self.password == sha1(password).hexdigest()

    def __cmp__(self, other):
        return cmp(self._id, other._id)


class Paper(ObjectProxy):
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
            self.save_dict(mongoDict)
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


