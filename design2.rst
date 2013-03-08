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


Minimal milestones
------------------


prototype 1
...........

* some arxiv papers in the database
* G+ login presumably at home page, then show papers they've
  discussed.
* view a paper
* enter an spnetwork message.  Presumably it just sends you to
  G+ with link back to paper page.
* get #spnetwork comments from G+
* show spnetwork comments on paper page


