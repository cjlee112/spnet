from bson.objectid import ObjectId
from bson.errors import InvalidId

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

def _get_object_id(fetchID):
    try:
        return ObjectId(fetchID)
    except InvalidId, e:
        raise KeyError(str(e))

# base document classes

class Document(object):
    'base class provides flexible method for storing dict as attr objects'
    useObjectId = True
    
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
        if getattr(self, 'useObjectId', False):
            fetchID = _get_object_id(fetchID)
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
        if getattr(self, 'useObjectId', False):
            self._parent_link = _get_object_id(self._parent_link)
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

