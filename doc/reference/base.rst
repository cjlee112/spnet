:mod:`base` --- Simple Document Interface
=========================================

.. module:: base
   :synopsis: A simple document interface
.. moduleauthor:: Christopher Lee <leec@chem.ucla.edu>
.. sectionauthor:: Christopher Lee <leec@chem.ucla.edu>

Overview
--------

This module provides a simple document interface that stores
its data in the MongoDB database, while saving you from dealing with
the details of MongoDB operations.  It provides a :class:`base.Document` 
base class, which you subclass to instantiate to represent
a specific document collection, e.g. Paper.
It provides the four standard 
`CRUD <http://docs.mongodb.org/manual/crud/>`_ operations::

  p = Paper(docData=dict(title='My Paper', authors=[person._id],
                         summary='Lorem ipsem...')) # CREATE doc

  p = Paper(docID) # READ doc
  print p.title, p.summary # data bound as attributes
  for person in p.authors: # get linked objects
      print person.name, len(person.subscriptions)

  p.update(dict(year=2009, pages='45-60')) # UPDATE doc

  p.delete() # DELETE from collection in database

What It Isn't
.............

Note: this is **not** an Object-Relational Mapper.  
ORM objects have to worry about *data synchronization*,
in both directions.  That is, if you change an attribute on
the object, that must be saved to the database so anyone else
who may be viewing this document will see the new value.  Conversely,
this object needs to know if any change occurred in the database
(and update its attribute values accordingly).  One way of
saying this is that the ORM is itself responsible for 
ensuring synchronization over (any number of) object instances
(across many threads?  many processes?  many machines connected
to the same database?).  We did not want this complexity and
potential inefficiency.

What It Is
..........

Instead, we provide the *convenience* of an object interface
to the data, with the *simplicity* of the "stateless" CRUD model.

  * the *database* is solely responsible for synchronization
    and atomicity (as it is designed to be);
  * you only interact with the database through the four CRUD methods,
    so to change a document you must call its update() method;
  * you use an object to render a page view (or whatever you're doing),
    and then throw it away.  The spnet server is stateless; state
    is stored in the database, not the spnet server.

Embedded Documents
..................

NoSQL documents can contain any structure of data, i.e.
sub-documents "embedded" in a top-level document.  This module
provides convenient ways of declaring that a field (sub-document)
should itself be represented as a Document object (with the same
CRUD interface).  This allows us to create a modular (object)
interface to all these documents, enabling our code to work with
them in the same way regardless of whether they are top-level
documents or embedded subdocuments.  The module provides
both :class:`base.EmbeddedDocument` and 
:class:`base.ArrayDocument` classes.

Linked Documents
................

Document fields that reference another document ("foreign key")
are automatically transformed into Document objects for you.
To make this efficient, the linked document data is actually
*retrieved* only when you explicitly request that attribute
of the linking Document.  This enables Documents to have a rich
interface of attribute links to all other relevant documents
without paying any "database transactions" price.  I.e. unless
you actually view a specific attribute, it incurs no database
query.

Document classes
----------------

Document
........

The :class:`base.Document` class is a base class for defining
a MongoDB collection.
You use this by declaring a subclass, with (at minimum) a
``coll`` attribute set to the pymongo.Collection you want it
to use as its MongoDB datastore.  Typically you also "decorate"
your subclass with :meth:`base.LinkDescriptor` attributes
to link it to other document collections,
custom methods and other useful data.  For a simple example,
see :class:`core.GplusSubscriptions` in 
`core.py <https://github.com/cjlee112/spnet/blob/master/spnet/core.py>`_,
or :class:`core.Paper` for a more complex example.

.. class:: Document(fetchID=None, docData=None, insertNew=True)

   Base class for defining a specific document collection.

   *fetchID*, if not None, is the unique ID for a specific
   document you want to retrieve.

   *docData*, if not None, is a dictionary of data representing
   the document.

   *insertNew=True* will **INSERT** *docData* as a new record in
   the MongoDB collection associated with your specific Document
   subclass.  If *docData* has an ``_id`` key, it will be used as
   the MongoDB ID of the inserted document; otherwise a unique ID will
   be auto-generated for you.

   *insertNew=False* will simply initialize an object representing
   *docData*, without storing anything to MongoDB.

.. attribute:: Document._id

   All MongoDB documents have a unique identifier ``_id`` field.

.. method:: Document.update(updateDict)

   Update the MongoDB document record atomically, setting just the
   specific field values given by *updateDict*.

.. method:: Document.delete()

   Delete this record from the MongoDB collection.

.. classmethod:: Document.find(queryDict={}, fields=None, idOnly=True, sortKeys=None, limit=None, **kwargs)

   A convenience wrapper for the pymongo.Collection.find() method.

   *queryDict*, if not empty, specifies a MongoDB query to perform
   on your collection.

   *fields*, if not None, specifies the fields to be returned from
   matching records, in the usual MongoDB way.

   *idOnly=True* makes it simply iterate over the database ID values
   of matching records (overrides the *fields* argument).

   *sortKeys* and *limit* allow you to specify both the order
   and maximum number of results to be returned.  Uses the efficient
   new MongoDB aggregation framework.

   *kwargs* are passed through to pymongo.Collection.find().

.. classmethod:: Document.find_obj(queryDict={}, **kwargs)
   
   Same as find(), but returns an object represenation of each
   matching record.

.. method:: get_value(stem='spnet_url')

   Gets a desired value via precedence rules defined by your
   subclass' ``_get_value_attrs`` attribute, which must be a 
   list of subdocument field names.  It finds the first of these subdocuments
   that actually exists in this document, and calls its method
   named ``get_STEM()`` (where STEM is the value of the *stem* argument,
   i.e. in the default case this would be ``get_spnet_url()``).
   If none of the subdocuments is found, it calls the same
   method name on itself.
   

EmbeddedDocument
................

Base class for defining subclasses that represent
subdocuments embedded as a specified field 
in "parent" documents in a specified
MongoDB collection.  Your subclass must define the following:

* ``_dbfield`` attribute must be a string of the form ``'field.subfield'``,
  where *field* is the name of the field in the top-level
  document that will store the embedded document, and
  *subfield* is the name of the field in the embedded document
  that will store its ID value, which must be unique across
  all documents in this collection.

Your subclass may define the following optional methods:

* ``_query_external(self, fetchID)``: must return *docData*
  for the embedded document, based on querying some external
  resource using the embedded document's ID (*fetchID*).

* ``_insert_parent(self, docData)``: must *create* a parent
   document (i.e. make a docData dictionary representing it
   (based on the *docData* from your embedded document),
   and save it in the database), and return a document object
   representing it.



.. class:: EmbeddedDocument(fetchID=None, docData=None, parent=None, insertNew=True)

   Same arguments as for :class:`base.Document` except as follows:

   *parent*, if not None, must be either the ID of the parent
   document (containing this embedded document), or an object
   representing that parent document.

   *insertNew='findOrInsert'* will make it first query the database
   to see if the specified document already exists (in which case
   it returns an object representing it).  If not, it stores
   *docData* to the database, as a field of a specified parent
   document.  If *parent* is not None, the new document will
   be embedded in the record specified by *parent*.  If *parent*
   is None, then your subclass **must** implement an
   ``_insert_parent()`` method that will *create* a parent
   document (i.e. create a docData dictionary representing it,
   and save it in the database), and return a document object
   representing it.

   Note that ``findOrInsert`` first queries the database using
   either *fetchID*, or if that is None, by extracting the
   *fetchID* value from ``docData[subfield]``, where ``subfield``
   is obtained from ``self._dbfield`` (see above).
   

.. method:: EmbeddedDocument.update(updateDict)

   Update the MongoDB document record atomically, setting just the
   specific field values given by *updateDict*.

.. method:: EmbeddedDocument.delete()

   Delete this subdocument from its parent document.


ArrayDocument
.............

Base class for defining subclasses that represent
subdocuments stored as an array in a specified field 
of a "parent" document in a specified
MongoDB collection.  Your subclass must define at least the following:

* ``_dbfield`` attribute must be a string of the form ``'field.subfield'``,
  where *field* is the name of the field in the top-level
  document that will store the array, and
  *subfield* is the name of the field in each array document
  that will store its ID value.

.. class:: ArrayDocument(fetchID=None, docData=None, parent=None, insertNew=True)

   Same arguments as for :class:`base.EmbeddedDocument` except as follows:

   *fetchID*, if not None, must be a tuple ``(parentID, subID)``,
   where ``parentID`` gives the ID of the parent (top-level)
   document containing this ArrayDocument, and ``subID`` gives
   gives the ID stored in the subdocument's ``subfield`` field
   (see ``_dbfield`` attr explanation above).

   *insertNew='findOrInsert'* does not support use of
   ``_insert_parent()`` or ``_query_external()`` methods.
   Instead, you must provide both *parent* and *docData* arguments.

.. classmethod:: ArrayDocument.find_obj_in_parent(parent, subID)

   Returns the desired ArrayDocument whose *fetchID* is
   ``(parent._id, subID)``, from the already retrieved *parent*
   object, *without* performing any database query.

   *parent* must be ``base.Document`` instance representing document
   containing this subdocument.  

UniqueArrayDocument
...................

Same as :class:`base.ArrayDocument`, but for the case where each
subdocument has an identifier field that is unique, i.e. no other subdocument
in the same named array in any document in the same collection will
have the same value of this identifier field.  This means that
we can just use this ``subID`` as its *fetchID* (instead of
a *(parentID, subID)* tuple as in the regular :class:`base.ArrayDocument`
case).

"Foreign Key" Convenience Classes
---------------------------------

This module also provides several classes that provide convenient
ways of linking an object to other objects.

.. class:: LinkDescriptor(attr, fetcher, noData=False, missingData=False, **kwargs)

   Returns an attribute descriptor that a subclass can use
   to define an object attribute that will only be retrieved
   when someone actually tries to get its value (i.e. getattr).

   *attr* is the name of the attribute.

   *fetcher* must be a callable that will actually retrieve the
   desired object(s).

   if *noData* is True, ``getattr(doc, attr)`` will simply return
   ``fetcher(doc, **kwargs)``.  Otherwise, it will return
   ``fetcher(doc, data, **kwargs)``, where ``data`` is the
   raw data stored in the database as fieldname ``attr``.

   if *missingData* is False, an exception will be raised
   if no raw data for ``attr`` is stored in the database record.
   Otherwise in that case it will simply return the value
   specified by *missingData*.

   You should not write directly to ``doc.attr`` (i.e. setattr);
   its data should come only from the database.  If you want to
   change the raw data stored as ``attr`` in the database,
   use ``doc.update({attr:newValue})`` in the usual CRUD way.

The module also provides a number of convenient classes to use
as *fetchers*:

.. class:: FetchObj(klass, **kwargs)

   For retrieving the document object specified by a "foreign key"
   giving its ID.
   When a :class:`base.FetchObj` instance is used as a fetcher
   function, it interprets *data* as a *fetchID*, i.e. it
   returns ``klass(fetchID=data, **kwargs)``.

.. class:: FetchList(klass, **kwargs)

   For retrieving a list of document objects specified by a 
   list of foreign keys.  I.e. returns
   ``[klass(fetchID, **kwargs) for fetchID in data]``.

.. class:: FetchQuery(klass, queryFunc, **kwargs)

   For retrieving the results of a database query on the mongoDB
   collection ``klass.coll``.  *queryFunc* does not perform the
   query, it simply *formulates* the query to be performed
   (as always in mongoDB, the query is a dictionary).
   When a :class:`base.FetchQuery` instance is used as a fetcher
   function, requesting ``getattr(doc, attr)`` will call
   ``queryFunc(doc, **kwargs)``, and will finally return
   ``list(klass.find_obj(query))`` where ``query`` was the
   value returned by *queryFunc*.

   You must always use the LinkDescriptor(noData=True) option
   when using this fetcher.
 
.. class:: FetchParent(klass, **kwargs)

   Retrieves object representing parent document containing this
   subdocument.


EmbeddedDocument wrapping
---------------------------

This class converts the raw database data for a field representing
a subdocument, into its associated :class:`base.EmbeddedDocument` object.

.. class:: SaveAttr(klass, arg='parent', postprocess=None, **kwargs)

   Returns ``klass(docData=data, **kwargs)`` where
   *klass* is the desired subdocument class to apply, and
   *data* is the raw database data for this subdocument.

ArrayDocument wrapping
----------------------

This class converts the raw database data for a field representing
an array, into a list of :class:`base.ArrayDocument` objects.

.. class:: SaveAttrList(klass, arg='parent', postprocess=None, **kwargs)

   Returns ``[klass(docData=d, **kwargs) for d in data]`` where
   *klass* is the desired subdocument class to apply, and
   *data* is the raw database data for this array.

  
