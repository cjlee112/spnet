####################
Developer's Overview
####################

Quick Start
-----------

* Fork the code at https://github.com/cjlee112/spnet
* If you wish, `run your own spnet server <#running-your-own-spnet-server>`_
  for testing your code changes.
* Read on to learn about the basic design and specific components.


The spnet Design
----------------

Background
..........

The spnet codebase is in `Python <http://www.python.org>`_.

The spnet design follows 
`REST principles <http://www.slideshare.net/nicolaiarocci/developing-restful-web-apis-with-python-flask-and-mongodb>`_
both externally (it is a 
REST server) and internally (each data class is a collection
that supports the standard Create, Read, Update, Delete (CRUD)
methods; in REST these correspond to the HTTP verbs POST, GET,
PUT, DELETE).  You can read more about REST
`here <https://news.ycombinator.com/item?id=717010>`_
and `here <https://ep2013.europython.eu/conference/talks/developing-restful-web-apis-with-python-flask-and-mongodb>`_.

The actual data is stored in the 
`MongoDB <http://www.mongodb.org>`_ NoSQL database, which basically
stores JSON documents.
However, the MongoDB details are (mostly) hidden behind our
simple Document interface, so most code does not need to know about
MongoDB.

HTML views are generated using 
`Jinja2 <http://jinja.pocoo.org/docs/>`_ templates.

The web server is a standalone Python process using the lightweight
`CherryPy <http://www.cherrypy.org>`_ framework 
as the dispatcher.  However, our dependency on
CherryPy is very limited (basically just 
`web.py <https://github.com/cjlee112/spnet/blob/master/spnet/web.py>`_), 
so chances are you won't need to deal with it at all.

Scalability
...........

The design follows a few basic scalability principles:

* all aspects of synchronization and atomicity are delegated to
  the database.  The spnet server code does not retain
  *state* information; all state data are stored in the database.
  So the server code needs no complications such as checks
  for whether its data have changed.  It serves all requests
  by simply querying the database and returning the response.
  We take advantage of the fact that MongoDB updates are
  guaranteed
  `atomic <https://wiki.10gen.com/pages/viewpage.action?pageId=54001699>`_.
* thus any number of separate server processes (running the same
  server code and connected to the same database) could cooperate
  to serve page requests.
* thus the main scalability bottleneck is the database.  MongoDB
  provides clustering and sharding scalability options.
* MongoDB is a NoSQL ("schema-less") database that permits storing
  "documents within documents" (embedding and arrays).  We exploit
  this to store all the different data needed for a given Paper
  view (e.g. Posts, Recommendations, Replies, etc.) embedded
  in the Paper document, so that the entire page view for the
  Paper and associated data can be served with only a single
  database query.

Components
..........

The design consists of several separate components:

* simple document interface (:mod:`base`):
  CRUD interface to NoSQL (MongoDB) backend.
  Defines classes like :class:`base.Document`,
  :class:`base.EmbeddedDocument`, :class:`base.ArrayDocument`.
* REST server
  (`rest <https://github.com/cjlee112/spnet/blob/master/spnet/rest.py>`_).
  Defines Collection class.
* the spnet data classes (:mod:`core`):
  :class:`core.Person`, :class:`core.Paper`, :class:`core.SIG`,
  :class:`core.Recommendation`, :class:`core.Post`, etc.
* the spnet REST application tree
  (`apptree <https://github.com/cjlee112/spnet/blob/master/spnet/apptree.py>`_):
  PaperCollection, get_collections() etc.
* HTML templates for REST responses
* indexing incoming posts, replies etc.
  (`incoming <https://github.com/cjlee112/spnet/blob/master/spnet/incoming.py>`_)
* social network backends:
  `gplus <https://github.com/cjlee112/spnet/blob/master/spnet/gplus.py>`_,
  `twitter <https://github.com/cjlee112/spnet/blob/master/spnet/twitter.py>`_
* query backends:
  `arxiv <https://github.com/cjlee112/spnet/blob/master/spnet/arxiv.py>`_,
  `doi <https://github.com/cjlee112/spnet/blob/master/spnet/doi.py>`_,
  `pubmed <https://github.com/cjlee112/spnet/blob/master/spnet/pubmed.py>`_

Running your own spnet server
-----------------------------

You can run your own instance of the spnet server.  It's pretty
easy to install, mainly a matter of getting its dependencies

* download MongoDB from http://www.mongodb.org/downloads
  and get it running as follows (details may vary depending on your platform)::

    tar xzf mongodb-linux-x86_64-2.4.2.tgz
    cd mongodb-linux-x86_64-2.4.2
    mkdir db
    bin/mongod --dbpath db

  For simple testing purposes I usually run this inside a screen
  session so I can detach / re-attach to see detailed debugging info.

* install dependencies as follows::

    pip install feedparser lxml Jinja2 google-api-python-client requests pymongo cherrypy xmltodict

  Also download python ``dateutils`` package (get the version for Python 2),
  and run ``python setup.py install`` to install it.  One way you can
  do this is::

    pip install dateutils

* Now create and edit the configuration files for your local install.
  These files are not tracked in the git repository because they need
  to be customized for each installation.  You might not want to
  publicize these settings to the world, and you definitely don't want
  them to be overridden by someone else's settings.  We do include
  template files for these, so you should begin by copying from these
  templates.

  - Issue the following commands inside the top-level spnet directory::

      cp spnet/cp.template.conf spnet/cp.conf
      cp google/keys.template.json google/keys.json
      cp twitter/keys.template twitter/keys

  - Open ``cp.conf`` with a text editor and update the paths to
    match your system.

  - Generate a new Google+ API OAuth2 key at
    https://code.google.com/apis/console.  When you do this, you'll
    need to use the IP address and port number from cp.conf.  The default
    127.0.0.1 is "localhost", so that's a good choice.  

    Unless you want (and know how) to serve secure http connections
    from your local machine to itself, you should change the "https"
    to "http" for the redirect URI and javascript origin fields.

    Download the JSON file containing your Client ID, open it, and
    paste the appropriate values into ``google/keys.json``.  Also add
    your API key, found in the "Simple API Access" section of the
    Google API Console.
    
  - You don't need to do anything with ``twitter/keys`` for now. 

  

* You can test your setup by running the test suite::

    python test.py

   Note that currently this test suite will not finish successfully.

* Run ``spnet/spnet/web.py``.  I usually do this inside a screen session,
  retaining access to the interpreter prompt, so I can inspect data
  while running a test server::

    python -i web.py

* Point your web browser at ``http://localhost:8000``
  to verify that your server is running.




