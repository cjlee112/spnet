##############################################################################
Implementing a Selected-Papers Network via Tagging in Existing Social Networks
##############################################################################

What we need: WHO + WHAT subscription
-------------------------------------

A `Selected-Papers Network <http://thinking.bioinformatics.ucla.edu/2011/07/02/open-peer-review-by-a-selected-papers-network>`_
enables open peer review via individuals recommending papers that they
like, and choosing whose recommendations they wish to subscribe to
(in selected topics).  A core feature of this is the ability
to subscribe to an intersection of WHO + WHAT, i.e. to select
people whose interests overlap mine and whose judgment I trust,
and to filter just those topics that interest me.  First of all,
note that this is different from what most social networks show you, e.g.

* Facebook: you select people to follow ("friend") but you get
  everything they post (typically "I'm at the mall buying shoes now!").
  Unfortunately, Facebook lacks tagging and filtering support.
  For me, that makes Facebook just an avalanche of spam (which not
  coincidentally seems to match their current business model
  of shoving as much advertising in my face as possible).
* Google+: you can define different groups of people ("Circles")...
  but then you get everything they post, same as in Facebook.
* Reddit: shows you everyone's posts on a specific topic (WHAT);
  alternatively, shows all your friends' posts (WHO) on *all* topics.

Sorry, but for productive work we need to filter on *both* WHO+WHAT.
Even with people whose every post is fascinating (e.g. John Baez),
I don't have time to dig manually through all that traffic to
find the one topic that I need to work on at a given moment.
Multiply that traffic times all the people whose posts I might
want to see, and you see the scale of the problem.
Fortunately, WHO+WHAT subscription is possible, in some cases
fairly directly (e.g. Twitter) or with a bit of work (e.g.
Google+, Reddit).

Why not "roll your own" SP Net website?
.......................................

Many sites (connotea.org, mendeley.com, researchgate.com etc.) have tried
to create a nice garden for researchers to link to literature.
Why not implement an SP net within such a site?  It's been tried
many times and just hasn't taken off because this walled-garden
model suffers insoluble dilemmas:

* such a site first demands that a
  prospective user change how they work (i.e. register for and start
  using the new website); few people will do that.
* second, such a site yields no benefit -- 
  because any posts he writes are locked into a website that no one else
  reads.  

Each such site aspires to be the "Facebook of 
research communications", but the whole walled-garden dynamic
is an insuperable barrier to uptake.

Embrace Fragmentation via Federation
....................................

Instead, I propose to solve these two dilemmas by working within
the existing social networks

* people can just keep using the social network they're used to,
  using the standard hashtag mechanism they already know how to use
  (and whatever hashtags they already using as relevant to their work);
* their posts will be seen by huge numbers of people within 
  those networks.
* of course, this usage is strictly "Balkanized" by the separate
  walled gardens: e.g. a Google+ user will only see traffic from 
  other Google+ users.  But it's a reasonable way to start
  experimenting with the approach and getting people to try
  it with very little effort.

In my view, it's a *good* thing there is no single, dominant
player that owns the whole research social network space.
I don't want a single player to own these data, control how
they can be used, or lock out others from developing new usages.
SP net data should be public and usable by anyone who wants
to develop a better interface for publishing or peer review
(such as the many existing websites like ResearchGate, Mendeley etc.).
In other words, the SP net should be *federated*, a data-exchange
standard and network, in which public data are shared among
all sites that work with such data.  That network standard 
("Uniform Publish & Subscribe Locator") will take
time to develop, but in the meantime we can establish a de
facto *cultural standard* for how people tag recommendations
and peer review comments.  Everyone can immediately start
using these tag conventions in their current social networks,
as basic SP net working today.

An SP Net Tagging Standard Proposal
-----------------------------------

Any post could include simple "tag sentences" that each express 
a basic peer review statement, e.g.::

  #spnetwork #compbio #mustread #arxiv12345

means the post author recommends arXiv paper 12345 as
crucial for his work in computational biology.
The basic elements:

* prefix ``#spnetwork`` identifies this as an SP network sentence.
* basic sentence structure: **audience-subject-verb-object**,
  where individual elements may be omitted depending on context.
  e.g. ``#compbio #mustread #arxiv12345``.
* *audience* means the intended audience to whom the sentence
  is addressed, i.e. one or more topic-groups. 
* *subject* if omitted, the post-author.
* *object* is the ID of the publication being discussed.
* *verb* allows us to make different statements about that publication.
* *adverb*: e.g. to express different levels of confidence in a
  statement.
 
Peer review and recommendation verbs
....................................

* ``#recommend``: document worth reading for the specified audience. e.g.::

    #spnetwork #rnaseq #recommend #pubmed12345

* ``#mustread``: document essential for the specified audience. e.g.::

    #spnetwork #compbio #mustread #arxiv12345

* ``#submit``: invites the specified audience to read the document;
  typically by its author.  e.g.::

    #spnetwork #compbio #submit #arxiv12345

* ``#comment``: this post comments on the specified publication.
* ``#agree``: I agree with the specified publication.
* ``#disagree``: I disagree with the specified publication.
* ``#falsepositive``: the specified publication makes a claim
  that appears to be invalid.
* ``#falsenegative``: the specified publication misses an important
  conclusion that appears to be valid.
* ``#precedes``: an important claim of the specified publication
  appears to have already been published by previous publication A.  e.g.::

    #spnetwork #pubmed12345 #precedes #arxiv12345

* ``#inappropriate``: the specified publication violates a
  specific basic guideline of the forum.  e.g.::

    #spnetwork #msg12345 #inappropriate #adhominemattack

  (assuming that #adhominemattack designates a specific forum guideline).

Adverbs
.......

* ``#maybe``: to raise a possibility, without asserting high probability.
* ``#probably``: greater than 50%.
* ``#highconfidence``: greater than 1-epsilon (field-dependent)
* ``#nodoubt``: absolutely certain.
* ``#provisional``: statement is conditional on resolution of
  one or more questions about the document.
* ``#bad``: attaches blame to the statement, e.g.::

    #spnetwork #pubmed12345 #precedes #arxiv12345 #bad

  suggests that the later authors have either misappropriated results from
  the previous publication or mis-cited it.


Phase 1: using SP Net tagging in existing social networks
---------------------------------------------------------

* Many existing services such as Google+, Twitter, Reddit
  etc. support tagging and tag search.  Users of these services
  can start using SP Net tagging, and can use tag searches to
  give basic "subscription" and "peer review" capabilities.
  If you already use one of these services, just start adding the
  spnetwork tags to your posts as outlined above.
* If you're trying to choose which service is best for this,
  I'd recommend Twitter.  It's closest to the spnet vision.

Twitter
.......

Twitter is the original home of general-purpose tagging
and subscriptions, so it works well there:

* search on a specified combination of tags e.g.::

    #spnetwork #bioinformatics #recommend

  Unfortunately ``#spnet`` appears to be used already RE:
  a Sao Paulo football team; ``#spnetwork`` appears to be
  (mostly) unused.

* Click on **People you follow** to filter the results just to
  your subscriptions.

Google+
.......

Google+ supports both "friends" (via its Circles feature) and
general-purpose tagging.  It's possible to perform a join on
these two criteria, but this is not prominently featured.  
Here's how to do it:

* search for a specified set of tags (e.g. ``#spnetwork`` and ``#compbio``);
* filter the results to just items coming from people in your circles.
* You can then save this search, so you can later view your
  latest "subscription" results by rerunning this saved search.

Example::

  https://plus.google.com/s/%23spnetwork%20%23compbio

Reddit
......

Reddit allows you to "subscribe" to specific people and
then view their posts in different areas.  

* click on a username to see their posts / profile.
* click the **Friend** button to add them to your subscriptions.
* go to https://friends.reddit.com to see their latest posts.
* filter to a specific topic by running a search like
  ``reddit:bioinformatics`` and also click the checkbox
  "limit my search to /r/friends".

Problem: Reddit appears to be limited to a flat "category" space,
without a general tagging capability.  Puzzles:

* how to restrict this to spnet traffic?  Mandating the
  creation of a separate subreddit for spnet traffic (e.g.
  spnetbioinformatics instead of bioinformatics) seems unhelpful.
  Instead, perhaps each post title should include the word
  spnet.  Then a search would be something like::

    reddit:bioinformatics spnetwork

* hashtags don't seem to do anything in reddit.  That is,
  searching for #foobar seems exactly the same as searching for foobar.
* perhaps we should mandate putting the spnet tags in parentheses
  at the end of the title, e.g. (spnet recommend arxiv12345).

Facebook
........

Facebook just doesn't seem to support tagging or tag searching.
I don't see an easy way of implementing an spnet subscription within
their existing website.



Phase 2: building a SP Net service layer on top of the internet
------------------------------------------------------------

For the moment, let's refer to this as a 
"Uniform Publish & Subscribe Locator" (UPSL) service, which
positions this as analogous to the URL as an essential
public infrastructure standard.

* anyone can include these tags in any post, anywhere,
  e.g. a blog post, a tweet, a comment on a news site, a forum etc.
* the UPS service will automatically find and aggregate these posts
  (via the #spnet tag).
* many domains link posts to authenticated identities (accounts),
  e.g. Google, Facebook, Twitter, Reddit etc.
* anyone can use UPS website to consolidate their different
  accounts into one identity.
* UPS website lets people browse the recommendation network,
  create subscriptions, view their subscription stream,
  make recommendations, comments, etc.
* UPS service provides standard interface (UPSL) to aggregated
  data: identities; topics; subscriptions.  Other websites or
  software can use these services to create their own
  ways of browsing or searching the recommendations network.
  For example, you could create an Arxiv peer review site
  specialized for mathematics.


Goals
.....

* free social networking from the "walled garden": an individual
  should be able to publish, or subscribe to others, without
  barriers of "service providers" getting in the way.  Users
  should be able to employ a wide range of services, but
  refer to them in a uniform, integrated way.

* in particular, the intersection of **WHO** and **WHAT** and
  public subscription networks are an essential public good
  that require a public standard, not warring walled-gardens.

* standardize the basic operations of social networking in
  the same limited way that URLs standardized resource requests
  (e.g. #, GET, POST).

* provide a public standard on which a diverse ecology of
  useful specialized social networking services can grow and
  flourish, through "information federation" instead of the
  all-or-nothing dynamic of walled-garden monopolization.

Standard Operators
..................

Do a few fundamental operations well and simply.

* identity federation: enable a user to aggregate their many
  outputs as a single identity, a stable, unique ID.  Then all
  their publications on those different outputs aggregate into
  a single history and reference system.

* topic federation: enable users to tag all of their publications
  in different services in a single consistent way.

* subscription federation: enable users to subscribe to an intersection
  of WHO+WHAT, that works on top of all underlying services (i.e.
  it works on top of the federated publication space).  If a user
  opts to subscribe "publicly" 


