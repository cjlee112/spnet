####################
Ways to Get Involved
####################

* write posts tagged #spnetwork and use the selectedpapers.net website (and if it won't do what you need, tell us).
* spread the word whenever (and to whomever) this is relevant.  For example if you want to discuss a paper online with someone, why not do it including #spnetwork tags?
* tell us how you want selectedpapers.net to work, e.g. right now there are 14 issues marked "needsInput" waiting for recommendations from users on various questions.
* test our latest features and fixes as part of our ongoing release cycles.
* be an ambassador: increasingly, selectedpapers.net needs to link up with organizations such as arXiv and MathOverflow to share data, work together etc.  This requires contacting the right people and discussing specific proposals (already we have a number such ideas in our issue tracker).  Other examples: should we write a Kickstarter funding proposal, or apply for foundation or agency funding?  Connect with other Open Science groups and projects?
* identify aspects of the site that are confusing or poorly explained; write website text, documentation, FAQs.
* start working with the spnet HTML, AJAX and Python code (easy example: look at the latest error logs and propose simple fixes to prevent those errors).
* release cycle, website and database work: run test suites and user tests prior to release; deploy new release to the website.  Website security.  Mongodb database optimization, backup, security.
* design and implement new features, using AJAX and Python code.

By Using SelectedPapers.net
---------------------------

* by tagging papers as interesting, you help define those topic tags.
* by discussing papers and tagging your posts for a specific topic(s),
  you help create a public forum for that research topic, and
  invite a larger audience (everyone following you
  on Google+) to join in.
* by writing recommendations, you identify important new research
  that will interest others in your field.
* by suggesting new features or reporting problems, you help
  improve selectedpapers.net.

By Helping Build a Research Community Without Walls
---------------------------------------------------

* learn about what we're trying to do, by reading the original paper,
  `Open peer review by a selected-papers network <https://selectedpapers.net/shortDOI/fzkjw8>`_.
* by getting the word out about SelectedPapers.net, on your blog,
  in Google+ posts or communities.
* by getting involved in the SelectedPapers.net community group
  to make contacts with other Open Science efforts, journals,
  Pubmed etc.  Come talk with us on the
  `Open Science community <https://plus.google.com/communities/113901282230153759827>`_
  on Google+; please tag your posts ``#spnetwork``.

By Making SelectedPapers.net Better
-----------------------------------

For Everyone
............

* by helping organize and manage the ongoing development and
  release cycle process.
* by helping develop coherent plans for new capabilities, and
  managing its implementation.
* by improving its styles and graphic design (CSS and templates)
* by improving the site's text and documentation

For Coders
..........

Add new capabilities to SelectedPapers.net in one or more of the
following ways (suggested background knowledge in parentheses):

* by extending the site's underlying services (REST):
  `get started <https://github.com/cjlee112/spnet/blob/master/spnet/apptree.py>`_
* by improving user interaction (AJAX and JavaScript):
  `get started <https://github.com/cjlee112/spnet/blob/master/spnet/_templates/get_paper.html>`_
* by writing signin and query code for additional social networks
  (OAuth, Twitter API, Facebook API etc.):
  `get started <https://github.com/cjlee112/spnet/blob/master/spnet/twitter.py>`_
* by improving and adding backend query services (e.g. Pubmed):
  `get started <https://github.com/cjlee112/spnet/blob/master/spnet/pubmed.py>`_
* by developing NoSQL code (MongoDB)
* improving the automated test suite:
  `get started <https://github.com/cjlee112/spnet/blob/master/spnet/test.py>`_
* by helping administer the web server (Python / CherryPy)
  and database server (MongoDB),
  including rollout of new versions (via Git).

To learn more, see the 
`Developer's overview <developer/overview.html>`_.

Measuring Interest: Scientometrics
..................................

A selected-papers network can greatly assist its users
by directly measuring the interest level of specific papers,
topics, etc. and applying that to rank what is most likely to
be of interest for each user.  If you wish to be part of
this analytics and scientometrics research and development,
get involved.


