########################################
SPNet Redesign: plug in to many services
########################################

We want to figure out how to populate our basic categories

* people
* papers
* topic groups
* subscriptions
* hypotheses

  * when people login via Twitter et al., we can see who they're
    following (and maybe who follows them).


Problems:

* initially there is no way to link people against papers (authorship)
* typically, no way even to see which papers are by the same
  author.
* all we can do is *invite* people to claim authorship on specific papers.
* twitter 140 char limit can't even show title of the paper.
  So on what basis can readers decide whether to click-through?

Ideas:

* user should declare topic-groups at the start, then offer those
  choices to him whenever he writes a post

  * choose from some keywords, or propose your own.  For each
    keyword optionally choose a search criterion or define your own.

* user should declare people whose interests most overlap his own,
  as email, social-network ID, RSS etc.  Actually, even just getting a
  name and institution would be helpful (for others to match against).
* definitely want users to claim their own papers (unverified, of course).
* being able to see who clicks through is KEY!
* note that even if reader is not logged in, we can keep a cookie
  and thus recognize repeat visits.
* arxiv lets you download source, so in principle you could extract
  bibtex and analyze references.  Could use this to build a 
  citation graph and citation-similarity graph.  But this is 
  a whole separate scientometrics analysis.
* hold "spnetathon" to collect topic-groups (tags) etc.
* useful to rank people by #followers (ideally spnet subscriptions)
* things that can "bring people together"

  * refering to the same papers
  * someone else recommends your paper (or vice versa)
  * refering to the same people
  * (refering to) the same topic-groups
  * applying the same search criteria

Views
-----

Home
....

User Home
.........

(if user logged in)

* messages ranked by interest



Paper
.....

* title, authors, abstract as usual
* "tag this paper": make this a very lightweight interface that lets
  you do just about any spnet action.
* discussion of this paper

  * need an interface for comments... not just recommendations!!!


Topics
......

* browse and search topics


Topic Group
...........

home for discussion on a topic

* show comments and papers on this topic (default: ranked by interest
  since last view).
* let users add "channels" to this topic (later the system can 
  measure level of interest in this topic on that channel
  and level of interest in this channel from users from this topic).

  * RSS feed
  * twitter list, G+ community, reddit etc.
* join this topic


Sources
.......


Schema Decisions
----------------

* the database takes all responsibility for atomicity and
  synchronization.  We do *not* want to burden the web server code 
  with any of that responsibility.  Therefore, web server code
  must always query the database; caching objects on the
  server would expose it to all the update and synchronization
  burdens.

* paper comments should be stored on the paper; external source
  document should be stored separately (e.g. tweet).
* comments can "reply-to" another comment, to enable threaded
  discussion view.
* paper stores text author list.  Cross-reference against Person
  record only if it's someone "in our system".  No point creating
  record for a singleton connected to nothing else.
* so we need an authorname view that lets people annotate that
  author.
* use batch processing pipelines where appropriate, totally
  independent of the web server.  For example, processing
  tweets requires resolving each short URL to a real URL,
  which is slow.  Don't do that during a http request!
  
  * These pipelines will process separate "input" db collections
    and update the core db collections as their output.
  * e.g. user might enter email address for an author: it
    goes into a processing pipeline that sends email and
    creates a record for email-verification.  If verification
    comes back, web server will create Person record.

* Person record means someone authenticated by at least one
  method (email, twitter, G+ etc.).  Or conceivably if we 
  could link multiple papers against one person, we'd create
  a Person record to reflect that.

* one paper can be linked to multiple external IDs (e.g.
  arxiv, DOI, pubmed).

* let user block a specific source (user, channel etc.)

* reality: we can run a streaming filter on #spnetwork but
  we'll probably also have to run searches on all topic hashtags,
  to pick up messages from "outside" the spnetwork community.

* we need to support both time and interest ranking.  So
  every message has to be time-stamped and we mark user
  record for when they last viewed results.  In general
  the view will consist of two sections ("new" vs. "old"),
  each ranked by interest, showing a maximum number with
  link to view more.

* need to extract comments for a given #spnetwork post.

* possible benefit of using paper hashtag: in principle you could just
  search for all posts with that hashtag, not just those also
  labeled #spnetwork??

* keep Recommendations separate from Posts and Comments.
  Each will be an array stored within a Paper document.
  Posts and Comments have unique IDs, so use UniqueArrayDocument.
 
* How to handle variants (e.g. gplus user, twitter user etc.)?
  Keep a subdocument representing that extra data, within the
  main document.  E.g. Person.gplus.  Don't really want to use
  a class interface, because one person can be belong to many
  variants...  Should I use EmbeddedDocument interface??
  Probably.  It provides the insert() and update() methods.

Minimal milestones
------------------

* prototype 1: work solely with Google+, just use the Google+
  interface to look at paper stream?  Benefit of the spn interface?
  Inserts the tags for you...



prototype 1
...........

* some arxiv papers in the database
* G+ login presumably at home page, then show papers they've
  discussed.
* view a paper

  * show a choice of tags ranked by relevance for the user to
    declare their interest, or let user add his own tag.
  * show spnetwork posts (and comments) on paper page

* enter an spnetwork message.  Presumably it just sends you to
  G+ with link back to paper page.  Key question: does it insert
  a lot of hashtags for you?

  * default: #spnetwork, #arxiv_1234_5678
  * URL link to the paper's homepage.
  * Add a share button that records the event, redirect user
    to G+ share URL.

* get #spnetwork posts (and comments) from G+: if they're retrieved
  in order from newest to oldest, presumably you can stop as soon as
  you hit a post already stored in spn database. No.  The only
  way to see if someone edited or added comments would be to
  look at etag of every post.  Yuck.  These kind of annoyances
  suggest we need an async mechanism...

  * query all posts for a given time duration, and check them against
    their etag.  Need to see if etag or other fields reflect comment.
    Yes!  The etag changes and the doc['object']['replies']['totalItems']
    count changes.  So you requery that document if etag changed... get
    the new comments.


deprecated
..........

* stamp outgoing messages with a thread ID, e.g. #spnthread12345 ?
  For the moment ignore this.  Assume that we're going to 

Google+ puzzles
---------------

* no mechanism for app to add post or comment directly, instead you
  can prefill a post form for the user (which they can change).
  Commenting is just plain impossible; your only option is to
  send the user out to the G+ page for the post.
* posts and comment search restricted to PUBLIC posts only.
  Frankly, in that case, why bother with OAuth sign-in?  API key
  (or even just a public Google search!) will find the same
  posts and comments!
* dilemma: which of the following interface flows is least awful?

  * user clicks button on paper homepage, (google sign-in), gets
    G+ share dialog, addresses it and / or revises it.  Then
    spn must search G+ activities in order to see the actual
    message the user sent (which could be quite different from
    what spn pre-filled for them).  Note that if the user doesn't
    post it *publicly*, the SPN won't see it at all!
  * user fills out form on paper homepage, SPN records it, puts
    up another button for passing this on to G+, user clicks it,
    gets G+ share dialog, addresses it...
  * for simple "share", user clicks a link, spn records the event,
    redirects user to SHARE url with link back to this paper homepage.
    User addresses it as usual, sends it.  At least this way the 
    spn site can record the event.  Note this would NOT include
    #spnetwork tags in the share message.  That seems OK.
    https://plus.google.com/share?url=
  * Probably the ideal solution would be to reverse-engineer the G+
    javascript for interactive sharing.  Then we could 
    figure out how to do it directly, either in javascript
    or server-side.

    * tried that, no joy.
    * hmm: the obvious method of using JS to set the values doesn't
      succeed in changing what G+ shows as prefilltext. Grr.
    * I found the GET request it uses, but using that directly looks
      non-trivial.  In general, hacking their plusone.js looks 
      unpleasant -- nothing obvious works.  They process the
      button on load, so using JS to modify the DOM attributes
      doesn't affect the request.  Any little glitch in the
      GET vars seems to make their share dialog just hang forever. 

* app *can* post Moments but not to specific addresses.  So it's useless
  as a "share" mechanism!  (you want to share to specific people).

* grr, post hashtags don't seem to get indexed by Google+ right
  away.  If you post with #spnetwork, then view your own post
  and click on the #spnetwork hashtag, it takes you to a search
  page... which claims there are no posts with that hashtag!
  Even if you use a known hashtag like #numbertheory... your
  post will not show up in the search results, at least not right
  away.  Grr.  You are stuck having to list all the posts from
  that user. OK, now #spnetwork search worked.  Took about an hour
  for it to show up in search results.


Makes twitter look really great!
