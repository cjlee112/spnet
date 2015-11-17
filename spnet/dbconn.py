import pymongo


class DBConnection(object):
    'store different collection objects on specified classes'
    def __init__(self, classDict, user=None, password=None, dbname='spnet',
                 **kwargs):
        '''Each keyword argument specifies an attr:collection pair.
        If collection is a string, it must be of the form dbname.collname.
        Otherwise it must be a collection object to be saved as-is.'''
        self._conn = pymongo.connection.Connection(**kwargs)
        if dbname: # authenticating to access DB
            accessDB = self._conn[dbname]
            accessDB.authenticate(user, password)
        for klass, v in classDict.items():
            if isinstance(v, str):
                db, coll = v.split('.')
                klass.coll = self._conn[db][coll]
            else:
                klass.coll = v
