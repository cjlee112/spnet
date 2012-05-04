import pymongo

class DBSet(object):
    '''Supports usage of multiple paper databases, using paperID
    given as dbname:id'''
    def __init__(self, dbsetDict, defaultDB=None):
        self.dbMap = {}
        for dbname, kwargs in dbsetDict.items():
            self.dbMap[dbname] = self.connect_db(**kwargs)
        if defaultDB:
            setattr(self, defaultDB, self.dbMap[defaultDB])
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


class DBConnection(object):
    'store different collection objects as named attributes'
    def __init__(self, connectArgs={}, **kwargs):
        '''Each keyword argument specifies an attr:collection pair.
        If collection is a string, it must be of the form dbname.collname.
        Otherwise it must be a collection object to be saved as-is.'''
        self._conn = pymongo.connection.Connection(**connectArgs)
        for attr, v in kwargs.items():
            if isinstance(v, str):
                db, coll = v.split('.')
                setattr(self, attr, self._conn[db][coll])
            else:
                setattr(self, attr, v)
