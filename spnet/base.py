from bson.objectid import ObjectId
from bson.errors import InvalidId
from time import mktime, struct_time
from datetime import datetime


class IdString(str):
    def __cmp__(self, other):
        if isinstance(other, ObjectId):
            return cmp(ObjectId(self), other)
        else:
            return cmp(self, other)

class LinkDescriptor(object):
    '''property that fetches data only when accessed.
    Typical usage: for a foreign key that accesses another collection.
    Caches obj.ATTR link data as obj._ATTR_link'''
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
        if isinstance(data, Document):
            obj.__dict__[self.attr] = data # bypass LinkDescriptor mechanism
            data = data._id # get its ID
        setattr(obj, '_' + self.attr + '_link', data)

def _get_object_id(fetchID):
    try:
        return ObjectId(fetchID)
    except InvalidId, e:
        raise KeyError(str(e))

def del_list_value(l, v):
    for i,v2 in enumerate(l):
        if v2 == v:
            del l[i]
            return True

def convert_to_id(v):
    try:
        return v._id
    except AttributeError:
        return v

def convert_times(d):
    'convert times to format that pymongo can serialize'
    for k,v in d.items():
        if isinstance(v, struct_time):
            d[k] = datetime.fromtimestamp(mktime(v))
            

# base document classes

# two different mechanisms for subobject references:
#
# LinkDescriptor: for foreign key; defers construction until getattr()
# _attrHandler: for subdocuments; constructs them immediately on loading
#               the parent document.

def base_find_or_insert(klass, fetchID, **kwargs):
    'save to db if not already present'
    try:
        return klass(fetchID)
    except KeyError:
        return klass(docData=dict(_id=fetchID, **kwargs))

class Document(object):
    'base class provides flexible method for storing dict as attr objects'
    useObjectId = True
    
    def __init__(self, fetchID=None, docData=None, insertNew=True):
        '''data can be passed in either as object IDs or as objects

        If fetchID provided, retrieves that doc, or raises KeyError.
        Otherwise, the object is initialized from docData,
        and if insertNew, ALSO inserted into the database.'''
        if fetchID:
            docData = self._get_doc(fetchID)
        elif insertNew:
            self.check_required_fields(docData)
            self.insert(docData) # save to database
        self._dbDocDict = docData
        self.set_attrs(docData) # expose as object attributes

    def check_required_fields(self, docData):
        for attr in getattr(self, '_requiredFields', ()):
            if attr not in docData:
                raise ValueError('missing required field %s' % attr)

    def _get_doc(self, fetchID):
        'get doc dict from DB'
        if getattr(self, 'useObjectId', False):
            fetchID = _get_object_id(fetchID)
        d = self.coll.find_one(fetchID)
        if not d:
            raise KeyError('%s %s not found'
                           % (self.__class__.__name__, fetchID))
        return d

    def set_attrs(self, d):
        'set attributes based on specified dict of items'
        attrHandler = getattr(self, '_attrHandler', {})
        l = []
        for attr, v in d.items():
            try:
                l.append((attrHandler[attr], attr, v))
            except KeyError:
                setattr(self, attr, v)
        for saveFunc, attr, v in l: # run saveFuncs after regular attrs
            saveFunc(self, attr, v)

    def insert(self, d):
        'insert into DB'
        try: # if class defines _idField, store it as mongodb _id
            d['_id'] = d[self._idField]
        except AttributeError:
            pass
        self._id = self.coll.insert(convert_obj_to_id(d))
        self._dbDocDict = d
        self._isNewInsert = True

    def update(self, updateDict):
        'update the specified fields in the DB'
        self.coll.update({'_id': self._id}, {'$set': updateDict})
        self._dbDocDict.update(updateDict)
        self.set_attrs(updateDict)
        
    def delete(self):
        'delete this record from the DB'
        self.coll.remove(self._id)

    def array_append(self, attr, v):
        'append v to array stored as attr'
        v = convert_to_id(v)
        self.coll.update({'_id': self._id}, {'$push': {attr: v}})

    def array_del(self, attr, v):
        'remove element v from array stored as attr'
        v = convert_to_id(v)
        self.coll.update({'_id': self._id}, {'$pull': {attr: v}})

    def __cmp__(self, other):
        try:
            return cmp(self._id, other._id)
        except AttributeError:
            return cmp(id(self), id(other))

    def __hash__(self):
        return hash(self._id)

    def get_value(self, stem='spnet_url'):
        'get specified kind of value by dispatching to specific paper type'
        for b in getattr(self, '_get_value_attrs', ()):
            try:
                o = getattr(self, b)
            except AttributeError:
                pass
            else:
                return getattr(o, 'get_' + stem)()
        return getattr(self, 'get_' + stem)()
    def get_spnet_url(self):
        return self._spnet_url_base + self.get_local_url()

    @classmethod
    def find(klass, queryDict={}, fields=None, idOnly=True,
             sortKeys=None, limit=None, **kwargs):
        'generic class method for searching a specific collection'
        if fields:
            idOnly = False
        if idOnly:
            fields = {'_id':1}
        if sortKeys or limit: # use new mongodb aggregation framework
            pipeline = []
            if sortKeys:
                pipeline.append({'$sort':sortKeys})
            if limit:
                pipeline.append({'$limit':limit})
            r = klass.coll.aggregate(pipeline)
            it = iter(r['result'])
        else:
            it = klass.coll.find(queryDict, fields, **kwargs)
        for d in it:
            if idOnly:
                yield d['_id']
            else:
                yield d

    @classmethod
    def find_obj(klass, queryDict={}, **kwargs):
        'same as find() but returns objects'
        for d in klass.find(queryDict, None, False, **kwargs):
            yield klass(docData=d, insertNew=False)
    find_or_insert = classmethod(base_find_or_insert)

def convert_obj_to_id(d):
    'replace Document objects by their IDs'
    d = d.copy()
    for k,v in d.items():
        if isinstance(v, Document):
            d[k] = v._id
    return d

class EmbeddedDocBase(Document):
    def _set_parent(self, parent):
        if hasattr(parent, 'coll'):
            self._parent_link = parent._id # save its ID
            self.__dict__['parent'] = parent # bypass LinkDescriptor mech
        else:
            self._parent_link = parent

class EmbeddedDocument(EmbeddedDocBase):
    'stores a document inside another document in mongoDB'
    def __init__(self, fetchID=None, docData=None, parent=None,
                 insertNew=True):
        if parent is not None:
            self._set_parent(parent)
        if insertNew == 'findOrInsert':
            if not fetchID:
                fetchID = docData[self._dbfield.split('.')[-1]]
            try: # retrieve from database
                Document.__init__(self, fetchID)
            except KeyError: # insert new record in database
                if not docData: # get data from external query
                    docData = self._query_external(fetchID)
                if parent is None:
                    self._set_parent(self._insert_parent(docData))
                    subdocField = self._dbfield.split('.')[0]
                    setattr(self.parent, subdocField, self)
                self.insert(docData) # save to database
                self.set_attrs(docData) # expose as object attributes
        else:
            Document.__init__(self, fetchID, docData, insertNew)
    def _get_doc(self, fetchID):
        'retrieve DB array record containing this document'
        subdocField = self._dbfield.split('.')[0]
        d = self.coll.find_one({self._dbfield: fetchID},
                               {subdocField: 1, '_id':1})
        if not d:
            raise KeyError('no such record: _id=%s' % fetchID)
        self._parent_link = d['_id']
        return d[subdocField]
    def insert(self, d):
        subdocField = self._dbfield.split('.')[0]
        convert_times(d)
        self.coll.update({'_id': self._parent_link},
                         {'$set': {subdocField: convert_obj_to_id(d)}})
        self._dbDocDict = d
        self._isNewInsert = True
    def update(self, updateDict):
        'update the existing embedded doc fields in the parent document'
        subdocField = self._dbfield.split('.')[0]
        d = {}
        for k,v in updateDict.items():
            d[subdocField + '.' + k] = v
        self.coll.update({'_id': self._parent_link}, {'$set': d})
        self._dbDocDict.update(updateDict)
        self.set_attrs(updateDict)
    def __cmp__(self, other):
        try:
            return cmp((self._parent_link,self._dbfield),
                       (other._parent_link,other._dbfield))
        except AttributeError:
            return cmp(id(self), id(other))
    def __hash__(self):
        return hash((self._parent_link,self._dbfield))

def find_one_array_doc(array, keyField, subID):
    'find record in the array with keyField matching subID'
    for record in array:
        if record[keyField] == subID:
            return record
    raise KeyError('no matching ArrayDocument!')
        
def filter_array_docs(array, keyField, subID):
    'find records in the array with keyField matching subID'
    for record in array:
        try:
            v = record[keyField]
        except KeyError:
            continue # lacks this field, so no match
        if isinstance(v, list): # handle array fields specially
            if subID in v:
                yield record
        elif v == subID: # regular field
            yield record
        
class ArrayDocument(EmbeddedDocBase):
    '''stores a document inside an array in mongoDB.
    Assumes we need to use a tuple of (parentID,subID) to
    uniquely identify each document.  For example, we specify
    a Recommendation by (paperID,authorID).
    Subclasses MUST provide _dbfield attribute of the form
    field.subfield, indicating how to search for fetchID in the parent
    document.'''
    def __init__(self, fetchID=None, docData=None, parent=None,
                 insertNew=True):
        self._set_parent(parent)
        if insertNew == 'findOrInsert':
            try: # retrieve from database
                if fetchID is None:
                    if parent is None:
                        raise ValueError('missing parent ID')
                    fetchID = self._extract_fetchID(docData)
                Document.__init__(self, fetchID)
                return # found our data, nothing further to do
            except KeyError: # insert new record in database
                fetchID = None
        Document.__init__(self, fetchID, docData, insertNew)
    def _get_doc(self, fetchID):
        'retrieve DB array record containing this document'
        self._parent_link,subID = fetchID
        if getattr(self, 'useObjectId', False):
            self._parent_link = _get_object_id(self._parent_link)
        arrayField, keyField = self._dbfield.split('.')
        d = self.coll.find_one(self._parent_link, {arrayField: 1})
        if not d:
            raise KeyError('no such record: _id=%s' % self._parent_link)
        return find_one_array_doc(d[arrayField], keyField, subID)
    def _extract_fetchID(self, docData):
        return (self._parent_link, docData[self._dbfield.split('.')[-1]])
    def _get_id(self):
        'return subID for this array record'
        keyField = self._dbfield.split('.')[1]
        return self._dbDocDict[keyField]
    def insert(self, d):
        'append to the target array in the parent document'
        try:
            if self._timeStampField not in d:
                d[self._timeStampField] = datetime.utcnow() # add timestamp
        except AttributeError:
            pass
        self._dbDocDict = d
        arrayField = self._dbfield.split('.')[0]
        self.coll.update({'_id': self._parent_link},
                         {'$push': {arrayField: convert_obj_to_id(d)}})
        self._isNewInsert = True
    def update(self, updateDict):
        'update the existing record in the array in the parent document'
        arrayField = self._dbfield.split('.')[0]
        d = {}
        for k,v in updateDict.items():
            d['.'.join((arrayField, '$', k))] = v
        subID = self._get_id()
        self.coll.update({'_id': self._parent_link, self._dbfield: subID},
                         {'$set': d})
        self._dbDocDict.update(updateDict)
        self.set_attrs(updateDict)

    def delete(self):
        'delete this record from the array in the parent document'
        arrayField, keyField = self._dbfield.split('.')
        subID = self._get_id()
        self.coll.update({'_id': self._parent_link},
                         {'$pull': {arrayField: {keyField: subID}}})

    def _array_update(self, attr, l):
        'replace attr array in db by the specified list l'
        arrayField = self._dbfield.split('.')[0]
        subID = self._get_id()
        target = '.'.join((arrayField, '$', attr))
        self.coll.update({'_id': self._parent_link, self._dbfield: subID},
                         {'$set': {target: l}})

    def array_append(self, attr, v):
        'append v to array stored as attr'
        v = convert_to_id(v)
        try:
            self._dbDocDict[attr].append(v)
        except KeyError:
            self._dbDocDict[attr] = [v]
        self._array_update(attr, self._dbDocDict[attr])

    def array_del(self, attr, v):
        'remove element v from array stored as attr'
        v = convert_to_id(v)
        l = self._dbDocDict[attr]
        if del_list_value(l, v):
            self._array_update(attr, l)
        else:
            raise IndexError('array %s does not contain %s'
                             % (attr, str(v)))
        
    def __cmp__(self, other):
        try:
            return cmp((self._parent_link, self._get_id()),
                       (other._parent_link, other._get_id()))
        except AttributeError:
            return cmp(id(self), id(other))
    def __hash__(self):
        return hash((self._parent_link, self._get_id()))

    @classmethod
    def _id_only(klass, d, d2, keyField):
        return d['_id'], d2[keyField]

    @classmethod
    def find(klass, queryDict={}, fields=None, idOnly=True, parentID=False,
             **kwargs):
        'generic class method for searching a specific collection'
        if fields:
            idOnly = False
        if idOnly:
            fields = {klass._dbfield:1}
        arrayField, keyField = klass._dbfield.split('.')
        filters = []
        for k,v in queryDict.items():
            queryFields = k.split('.')
            if queryFields[0] == arrayField:
                filters.append((queryFields[1], v))
        for d in klass.coll.find(queryDict, fields, **kwargs):
            try:
                array = d[arrayField]
            except KeyError:
                continue # not present in this record, so skip
            for k,v in filters: # apply filters consecutively
                array = list(filter_array_docs(array, k, v))
            for d2 in array: # return the filtered results appropriately
                if idOnly:
                    yield klass._id_only(d, d2, keyField)
                elif parentID:
                    yield d['_id'], d2
                else:
                    yield d2

    @classmethod
    def find_obj(klass, queryDict={}, **kwargs):
        'same as find() but returns objects'
        arrayField = klass._dbfield.split('.')[0]
        for parentID, d in klass.find(queryDict, {arrayField:1},
                                      False, True, **kwargs):
            yield klass(docData=d, parent=parentID, insertNew=False)

    @classmethod
    def find_obj_in_parent(klass, parent, subID):
        'search parent document for specified ArrayDocument'
        arrayField = klass._dbfield.split('.')[0]
        for o in getattr(parent, arrayField, ()):
            if o._get_id() == subID:
                return o
        raise KeyError('%s not found in %s' % (subID, klass._dbfield))


class UniqueArrayDocument(ArrayDocument):
    '''For array documents with unique ID values '''
    def _extract_fetchID(self, docData):
        return docData[self._dbfield.split('.')[-1]]
    def _get_doc(self, fetchID):
        'retrieve DB array record containing this document'
        arrayField, keyField = self._dbfield.split('.')
        d = self.coll.find_one({self._dbfield: fetchID}, {arrayField: 1})
        if not d:
            raise KeyError('no such record: %s=%s' % (self._dbfield, fetchID))
        self._parent_link = d['_id'] # save parent ID
        return find_one_array_doc(d[arrayField], keyField, fetchID)

    @classmethod
    def _id_only(klass, d, d2, keyField):
        return d2[keyField]

class AutoIdArrayDocument(UniqueArrayDocument):
    'makes a unique ID automatically for you'
    def __init__(self, fetchID=None, docData=(), parent=None, insertNew=True):
        keyField = self._dbfield.split('.')[1]
        if fetchID is None and keyField not in docData: # create an ID
            try: # copy dict before modifying it, to prevent side-effects
                docData = docData.copy()
            except AttributeError:
                docData = {}
            docData[keyField] = ObjectId() # use pymongo's ID generator
        elif fetchID and not isinstance(fetchID, ObjectId):
            fetchID = ObjectId(fetchID)
        super(AutoIdArrayDocument, self).__init__(fetchID, docData, parent,
                                                  insertNew)
            

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
        return list(self.klass.find_obj(query))

class FetchParent(FetchObj):
    def __call__(self, obj):
        return self.klass(obj._parent_link, **self.kwargs)

class FetchObjByAttr(FetchObj):
    def __init__(self, klass, attr, **kwargs):
        self.attr = attr
        FetchObj.__init__(self, klass, **kwargs)
    def __call__(self, obj):
        return self.klass(getattr(obj, self.attr), **self.kwargs)

class SaveAttr(object):
    'unwrap dict using specified klass'
    def __init__(self, klass, arg='parent', postprocess=None, **kwargs):
        self.klass = klass
        self.kwargs = kwargs
        self.arg = arg
        self.postprocess = postprocess
    def __call__(self, obj, attr, data):
        kwargs = self.kwargs.copy()
        kwargs[self.arg] = obj
        o = self.klass(docData=data, **kwargs)
        if self.postprocess:
            self.postprocess(obj, attr, o)
        setattr(obj, attr, o)

class SaveAttrList(SaveAttr):
    'unwrap list of dicts using specified klass'
    def __call__(self, obj, attr, data):
        l = []
        for d in data:
            kwargs = self.kwargs.copy()
            kwargs[self.arg] = obj
            l.append(self.klass(docData=d, **kwargs))
        if self.postprocess:
            self.postprocess(obj, attr, l)
        setattr(obj, attr, l)

