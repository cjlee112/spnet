:mod:`core` --- the spnet data model
====================================

.. module:: core
   :synopsis: the spnet data model
.. moduleauthor:: Christopher Lee <leec@chem.ucla.edu>
.. sectionauthor:: Christopher Lee <leec@chem.ucla.edu>

This module defines the spnet data collections.
These are stored as MongoDB collections:

* :class:`core.Person`: a participant in the spnet, either 
  because they've signed in to selectedpapers.net, or
  wrote recommendations / posts etc.
* :class:`core.Paper`: a paper, either from arXiv, Pubmed,
  or the DOI database.  Note that since the primary activity
  on selectedpapers.net is working with a paper and its
  associated data, we embed these associated datatypes
  (e.g. Recommendation) in the Papers collection.
* :class:`core.SIG`: a Specific Interest Group, i.e. a research topic.
* :class:`core.GplusSubscriptions`: lists a Google+ member's
  subscriptions (to other Google+ members).

The following data are embedded in Paper documents in MongoDB:

* :class:`core.ArxivPaperData`: information about an arXiv paper.
* :class:`core.PubmedPaperData`: information about a Pubmed paper.
* :class:`core.DoiPaperData`: information about a DOI paper.
* :class:`core.Recommendation`: an spnet recommendation for a paper,
  typically tagged for one or more topics.
* :class:`core.Post`: a post discussing a paper,
  typically tagged for one or more topics.
* :class:`core.Reply`: a reply to a post.
* :class:`core.PaperInterest`: tags a paper as interesting for
  a specific person, in one or more topics.

The following data are embedded in Person documents in MongoDB:

* :class:`core.GplusPersonData`: Google+ information about a 
  specific Person.
* :class:`core.EmailAddress`: email address associated with a Person.
* :class:`core.Subscription`: a subscription for a given person,
  to receive recommendations from a specific person, typically for
  one or more topics.

Paper Data
----------

.. class:: Paper(fetchID=None, docData=None, insertNew=True)

   Subclass of :class:`base.Document`; each instance represents a paper.
   Guarantees the existing of the following attributes:

.. attribute:: Paper.title

   Title of the paper.

.. attribute:: Paper.authorNames

   A list of strings each representing an author name.

   In addition, regardless of the source of the paper,
   you can call the paper's ``get_value()`` method with
   any of the following argument values:

   * ``'spnet_url'``: full selectedpapers.net URL for the current paper,
     e.g. ``https://selectedpapers.net/arxiv/1234.5678``
   * ``'local_url'``: path for the current paper, e.g. ``/arxiv/1234.5678``
   * ``'source_url'``: URL for the source database's page for this paper.
   * ``'downloader_url'``: URL for full-text access (if available).
   * ``'doctag'``: ID tag for this paper
   * ``'abstract'``: abstract for this paper, if available.

   Typically also contains one or more of the following subdocuments:

.. attribute:: Paper.arxiv

   :class:`core.ArxivPaperData` object representing arXiv record
   for this paper from arXiv.

.. attribute:: Paper.pubmed

   :class:`core.PubmedPaperData` object representing Pubmed record
   for this paper from Pubmed.

.. attribute:: Paper.doi

   :class:`core.DoiPaperData` object representing DOI record
   for this paper.

.. attribute:: Paper.recommendations

   list of :class:`core.Recommendation` objects for this paper (if any).

.. attribute:: Paper.posts

   list of :class:`core.Post` objects for this paper (if any).

.. attribute:: Paper.replies

   list of :class:`core.Reply` objects for this paper (if any).

.. attribute:: Paper.interests

   list of :class:`core.PaperInterest` objects for this paper (if any).

.. method:: Paper.get_interests(people=None, sorted=False)

   Returns dictionary of topics for which people have tagged
   this paper as interesting.  The keys are :class:`core.SIG` topic objects,
   and their associated values are lists of people
   (:class:`core.Person` objects) who tagged the paper as interesting
   for that topic.

   *people*, if not None, must be a set of people for filtering
   the results; i.e. only topics tagged by those people will be
   returned.

   if *sorted* is True, the results will be returned as a list of
   (topic, people) tuples sorted in descending order of ``len(people)``.

Person data
-----------

.. class:: Person(fetchID=None, docData=None, insertNew=True)

   Subclass of :class:`base.Document`; each instance represents a person.
   Guarantees the existing of the following attributes:

.. attribute:: Person.name

   string representing the person's name.

   In addition, regardless of the source of the person record,
   you can call its ``get_value()`` method with
   any of the following argument values:

   * ``'spnet_url'``: full selectedpapers.net URL for this person,
     e.g. ``https://selectedpapers.net/people/123456``
   * ``'local_url'``: path for this person, e.g. ``/people/123456``

   Typically also contains one or more of the following subdocuments:

.. attribute:: Person.gplus

   :class:`core.GplusPersonData` object representing Google+ record
   for this person.

.. attribute:: Person.subscriptions

   list of :class:`core.Subscription` objects representing this
   person's current subscriptions.

   Also provides attributes that link to other documents ("foreign keys"):

.. attribute:: Person.papers

   Papers for which this person is an author, as a
   list of :class:`core.Paper` objects.

.. attribute:: Person.recommendations

   Recommendations written by this person, as a
   list of :class:`core.Recommendation` objects.

.. attribute:: Person.subscribers

   People who have subscribed to this person, as a
   list of :class:`core.Person` objects.

.. attribute:: Person.posts

   Posts written by this person, as a
   list of :class:`core.Post` objects.

.. attribute:: Person.replies

   Replies written by this person, as a
   list of :class:`core.Reply` objects.

.. attribute:: Person.interests

   Papers tagged as interesting by this person, as a
   list of :class:`core.PaperInterest` objects.

.. attribute:: Person.readingList

   Papers added by this person to their reading list, as a
   list of :class:`core.Paper` objects.

.. method:: Person.get_interests(sorted=False)

   Returns dictionary of topics for which this person tagged
   papers as interesting.  The keys are :class:`core.SIG` topic objects,
   and their associated values are lists of papers
   (:class:`core.Paper` objects) tagged as interesting
   for that topic.

   if *sorted* is True, the results will be returned as a list of
   (topic, papers) tuples sorted in descending order of ``len(papers)``.

.. method:: Person.update_subscribers(klass, docData, subscriptionID)

   To be called when new Person first added to the database.
   Converts other peoples' pending subscriptions to this person,
   to a new entry in their ``subscriptions`` field.

Google+ Person data
...................

.. class:: GplusPersonData(fetchID=None, docData=None, parent=None, insertNew=True)

   Subclass of :class:`base.EmbeddedDocument`;
   each instance stores Google+ data for one person.
   Detailed information about
   `its content <https://developers.google.com/+/api/latest/people#resource>`_
   is available from Google.  Here we just list some key fields:

.. attribute:: GplusPersonData.id

   String representing the person's Google+ unique ID.

.. attribute:: GplusPersonData.displayName

   String representing name to display for this person.  

.. method:: GplusPersonData.update_posts(maxDays=20, **kwargs)

   get new posts from this person, updating old posts with new replies.
   Queries Google+ for the data (for changes up to *maxDays* old),
   and saves any changes (as Recommendations, Posts, Replies) to
   the database.

.. method:: GplusPersonData.update_subscriptions(doc, subs)

   Update the :class:`core.GplusSubscriptions` record for this
   person with new data *subs*, and then use them to add
   to our ``Person.subscriptions``.

   *doc* must be the response document from Google+ People list
   request; *subs* should be iterator object for the corresponding
   list of people.
   


Topic data
----------

.. class:: SIG(fetchID=None, docData=None, insertNew=True)

   Subclass of :class:`base.Document`; each instance represents a topic.
   Guarantees the existing of the following attributes:

.. attribute:: SIG.name

   string representing the topic name.  This is just its ``_id`` with
   a hash (#) prefix.  I.e. if ``_id`` is ``numberTheory``, then
   ``name`` is ``#numberTheory``.

   In addition, you can call its ``get_value()`` method with
   any of the following argument values:

   * ``'spnet_url'``: full selectedpapers.net URL for this topic,
     e.g. ``https://selectedpapers.net/topics/numberTheory``
   * ``'local_url'``: path for this topic, e.g. ``/topics/numberTheory``

   Also provides attributes that link to other documents ("foreign keys"):

.. attribute:: SIG.recommendations

   Recommendations tagged for this topic, as a
   list of :class:`core.Recommendation` objects.

.. attribute:: SIG.posts

   Posts tagged for this topic, as a
   list of :class:`core.Post` objects.

.. attribute:: SIG.interests

   Papers tagged as interesting for this topic, as a
   list of :class:`core.PaperInterest` objects.

.. classmethod:: SIG.standardize_id(fetchID)

   Checks whether *fetchID* fits hashtag character rules.
   Returns the ``_id`` value for the new topic (i.e. with # character
   stripped off), or raises ``KeyError`` if it is invalid as a hashtag.

.. classmethod:: SIG.find_or_insert(fetchID, published=None, **kwargs)

   save new topic to db if not already present, after checking
   its hashtag format validity.

.. method:: SIG.get_interests()

   Returns dictionary of papers tagged as interesting
   for this topic.  The keys are :class:`core.Paper` objects,
   and their associated values are lists of people
   (:class:`core.Person` objects) who tagged the paper as interesting
   for this topic.

