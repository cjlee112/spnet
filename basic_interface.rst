###################################
Basic SP Network Interface Proposal
###################################


I propose that the review site would present each paper 
with a basic tabbed interface, initially with just two tabs, 
Recommendations and Discussion.  The main difference is that 
whereas recommendations are automatically forwarded to the 
recommender's subscribers, discussion comments are not; they 
are simply displayed on the Discussion tab for the paper.  
The Recommendations tab would show who recommended the paper, 
for what area(s), and what they said about it.  The Discussions 
tab would show the usual threaded discussion interface that 
everyone is used to.

The Recommendations tab
-----------------------

This would show the following simple interface that lets you view 
and make recommendations.  It should be designed to look like 
the arXiv main page for a paper (e.g. sidebox for accessing PDF, 
PostScript etc. for the paper), but with the main content of the 
page shown in the following order (see explanatory notes below 
on the interactive elements):

* paper title, authors
* [+] abstract
* "Flagging papers that interest you will help this system predict 
  other papers that may interest you.
  Subscribing to people who recommended this paper will alert you
  to other papers they recommend.
  Writing recommendations that other people find useful will
  attract them to subscribe to receive your future recommendations
  and papers."
* [STAR] Rated must-read by John Baez, Ian Fleming and 37 others [+]
* If this paper interests you, flag the group(s) you would recommend read it:
[ ] logtree phylogeny: rec'd by John Baez, Kevin Costner and 21 others [+]
[ ] ultimate wrestling: rec'd by Herbert Spencer... [+]
... (more topics) ...
Add a topic-group: _____________

* News & Views

  * [+] John Baez: The most exciting paper since...
  * [+] Ian Fleming: A license to kill...
  * [+] 5 others
  * Tell the world!  Write a News & Views:

Interface Notes
...............

* clicking +/- sign shows or hides the text of the abstract.
* clicking the STAR icon toggles whether you rate the paper must-read
  or not; clicking the +/- sign toggles viewing of the list of
  other recommenders.
* the list of candidate topic-groups would be the superset of what
  other people (including the authors) suggested as groups that
  would be interested in this paper, and the groups the user belongs to.
* Add a topic group would let the user enter text to search the
  database of existing topic-groups and pick one or alternatively
  create a completely new group.
* "News & Views" is just a provisional title, suggestive of
  *alerting others to something new and interesting* and of
  *communicating your opinion about what matters*.  "News & Views"
  is what Nature calls these kind of highlight pieces.
* A News & Views item is implemented essentially a discussion item
  that gets forwarded to its authors subscribers, who in turn can
  recommend it to their subscribers, and so on.  (in this sense it
  is like a publication in its own right, but of course we won't
  allow people to write News & Views on a News & Views item!).
  As a discussion item, it can be commented on by others just
  like any discussion item).
* expanding a News & Views will show its text, as well as a link
  for viewing comments / commenting on it in the Discussion tab.
* you can add a News & Views by giving a DOI or URL for something
  published elsewhere (e.g. on your blog), or by simply entering
  text into a textbox here.


The Discussion tab
------------------

This would be a generic threaded discussion for this paper.  
As long as people can add new topics for discussion and comment 
on existing topics, it will be adequate for an initial release.  
Over time it would add peer review features (e.g. you could flag 
a discussion item as raising doubt about the validity of a major 
claim in the paper).  However that is not needed at first.

User registration
-----------------

* users would be asked to register with email address that matches
  their arXiv account, and would then receive an email for activating
  their account.  This way we link each user to their papers etc.
  in arXiv.
* to seed the system for recommending papers to them, new users
  would be asked to list recent papers they considered must-read
  for their own work, and / or other researchers whose interests
  they consider to be most similar to their own.
* users would be asked to select topic-groups that fit their
  research interests.  Initial topics can be suggested by the
  system based on the papers and people they listed, e.g. if any
  of those people already listed some topic-groups, offer those as
  options.  Of if any other people listed those same papers or
  people, offer the topic-groups that those people listed.
  Of course the user can add his own topic-group terms.
* the site would follow the Amazon model of remembering the user
  (i.e. based on their last login to this site on this computer,
  show their personal recommendations), but authenticate them
  (i.e. ask for password) if they want to publish a recommendation.

Look & Feel
-----------

I suggest the look & feel of the site draw from two main sources:

* mainly, make it look like arXiv;
* where appropriate, copy the clean, simple model of Google Code, 
  e.g. http://code.google.com/p/pygr/.
