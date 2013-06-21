###########################
SelectedPapers.net Overview
###########################

Open Scientific Sharing with No Walls
-------------------------------------

SelectedPapers.net lets you recommend papers, comment on them, 
discuss them, or simply add them to your reading list.  

But instead of "locking up" your comments within its own 
website - the "walled garden"
strategy followed by other services - it explicitly shares 
these data in a way that people *not* on SelectedPapers.net
can easily see.  Any other service can see and use them
too.  It does this by using *existing* social networks 
such as Google+, so users of those social networks can see your
recommendations and discuss them, 
even if they've never heard of SelectedPapers.net.

For example, if you're a Google+ user, you post comments
on SelectedPapers.net using your usual Google+ identity
and posting process,
with key hashtags automatically added to identify the
paper you are discussing.  And of course your post will be
seen by your usual Google+ audience -- in addition to people
who see it on SelectedPapers.net.

So: if you want to strip the idea down to one sentence, it's this:
given that social networks already exist, all we need
for truly open scientific communication is a 
`convention on a consistent set of tags and IDs <hashtags.html>`_ for
discussing papers.  That makes it possible to integrate
discussion from *all* social networks -- big and small -- 
as a single unified forum.

Getting Started
---------------

To see how it works, take a look here:

https://selectedpapers.net.

Under 'Recent activity' you'll see comments and recommendations
of different papers, so far mostly on the arXiv.  

Right now SelectedPapers.net works
with Google+.  Support for other social networks such as Twitter
is coming soon.  But here's how you can use it now:

* We suggest that you first create (in your Google+ account) a Google+ Circle 
  specifically for discussing research with (e.g. call it “Research”),
  unless you already have such a circle.

* Click **Sign in with Google** on https://selectedpapers.net or on  a paper discussion page.

* The usual Google sign-in window will appear (unless you are already signed  in).   
  Google will ask if you want to use the Selected Papers network,
  and specifically for what Circle(s) to let it see the membership
  list(s) (i.e. the names of people you have added to that Circle).
  SelectedPapers.net uses this as your initial "subscriptions",
  i.e. the list of people whose recommendations you want to receive.
  You should include all Circles that contain researchers who work
  in your field (including your new Research Circle, if you created one).

  Note the only information
  you are giving SelectedPapers.net access to is this list of names;
  in all other respects SelectedPapers.net is limited by Google+
  to the same information that anyone on the internet can see,
  i.e. your *public* posts.  For example, SelectedPapers.net cannot
  ever see your private posts within *any* of your Circles.

* Now you can initiate and join discussions of papers
  directly on any SelectedPapers.net page.

* Alternatively, without even signing in to SelectedPapers.net,
  you can just write posts on Google+ containing the hashtag **#spnetwork**,
  and they will automatically be included within the SelectedPapers.net
  discussions (i.e. indexed and displayed so that other people can
  reply to them etc.).
  Here's an example of a Google+ post example::

    This article by Perelman outlines a proof of the Poincare conjecture!  

    #spnetwork #mustread #geometry #poincareConjecture arXiv:math/0211159

  You need the tag **#spnetwork** for SelectedPapers.net to notice your post.  Tags like 
  **#mustread**, **#recommend**, and so on indicate your attitude to a paper. Tags like **#geometry**, 
  **#poincareConjecture** and so on indicate a subject area: they let people search for papers
  by subject.  A tag of the form **arXiv:1234.5678** (i.e. the official
  arXiv ID for the paper) is necessary for arXiv papers; 
  note that this does *not* include a # symbol.  

  For PubMed papers, include a tag of the form **PMID:22291635**.  Other published papers usually
  have a DOI (digital object identifier), so for those include a tag of the form **doi:10.3389/fncom.2012.00001**.

  Tags are the backbone of SelectedPapers.net; you can read more about 
  them `here <hashtags.html>`_.

* you can include LaTeX in your posts and comments.  Click here for
  `details <#latex>`_

* You can also post and see comments at https://selectedpapers.net.  This page also
  lets you search for papers in the arXiv and search for published papers via their DOI 
  or Pubmed ID.  If you are signed in, the homepage will also show the latest recommendations 
  (from people you're subscribed to), papers on your reading list, and papers you tagged as 
  interesting for your work.

Papers
------

Papers are the center of just about everything here.
Here's what you can do with a paper:

* click to see the full text of the paper via arXiv.org or
  the publisher's website.

* read other people's recommendations and discussion of the paper.

* add it to your **Reading List**.  This is simply a private list
  of papers -- a convenient way of marking a paper for further
  attention later.  When you are logged in, your Reading list
  is shown on the homepage.  No one else can see your reading list.

* **share** the paper with others (such as your Google+ Circles or 
  Google+ communities that you are part of).

* **tag** it as interesting for a specific topic.  You do this either
  by clicking the checkbox of a topic (it shows topics that other
  readers have tagged the paper), by selecting from a list of
  topics that you have previously tagged as interesting to you,
  or by simply typing a tag name.  These tags are public; that
  is, everyone can see what topics the paper has been tagged with,
  and who tagged them.

* **post** a question or comment about the paper, or **reply** to
  what other people have said about it.  This traffic is public.
  Specifically, clicking the Discuss this Paper button
  gives you a Google+ window (with appropriate tags
  already filled in) for writing a post.  Note that in order
  for the spnet to see your post, you **must** include Public in
  the list of recipients for your post (this is an inherent limitation
  of Google+, which limits apps to see only the
  same posts that *any* internet user would see -- even when you
  are *signed-in* to the app as yourself on Google+).

* **recommend** it to others.  Once again, you **must** include Public in
  the list of recipients for your post, or the spnet cannot see it.


  We strongly suggest that you include a
  **topic hashtag** for your research interest area.  E.g. if there
  is a hashtag that people in your field commonly use for
  posting on Twitter, use it.  If you have to make up a new
  hashtag, keep it intuitive and follow "camelCase" capitalization
  e.g. #openPeerReview.

LaTeX
-----

SelectedPapers.net supports the use of 
`LaTeX <http://www.latex-project.org/>`_ equations, both
"inline" and "display" math.  Specifically, it uses 
`MathJax <http://mathjax.org>`_
to convert LaTeX to the format that will best display equations
in your particular browser.  A few notes:

* LaTeX is supported in all user content: recommendations, posts,
  and comments.
* the **recommended** delimiters for inline math and display math are
  ``\( ... \)`` and ``\[ ... \]`` respectively.  These are the defaults
  recommended by both LaTeX and MathJax.  If you use these, your equations
  will display correctly in a very wide variety of settings, from LaTeX
  to the web.
* the use of ``$`` as a delimiter for inline math is **deprecated** but
  allowed, mainly to support old, legacy content.  For any new writing
  that you do, we *strongly recommend* that you use ``\( ... \)``
  instead.  Note:

  * ``\$`` is ignored (i.e. not treated as inline math delimiter).
  * to protect against text like "it costs $5 for five minutes and $15
    for the full half hour" (and errors like omitting one of the ``$``
    delimiting an equation), ``$`` will only be treated as the start
    of inline math if it's followed by a character that is *not* whitespace
    or comma (,), period (.), colon (:) or semi-colon (;).  Similarly,
    ``$`` will only be treated as a the end of inline math if it's
    preceded by a *non-whitespace* character.

* of course, Google+ will display LaTeX in your posts as text, not as equations.
  But that's a bit beyond our control.

LaTeX in arXiv Abstracts
........................

Usage of LaTeX in arXiv abstracts is unfortunately rather inconsistent:
some papers include it (typically as $inlinemath$); others don't;
and some abstracts have serious errors in their $inlinemath$
(such as unbalanced $).  Hence, it would not be appropriate to activate
$inlinemath$ on all arXiv abstracts; that would turn some abstracts
into an ugly mess.  Instead, selectedpapers.net gives you control
over whether you want a specific abstract: just click the 
"Treat $ as inline math" button in the Next Steps box on the right
(or click it again to toggle it off).  Furthermore, selectedpapers.net
"crowdsources" the default setting: if multiple people turn it on
(as opposed to turning it off), that becomes the default setting
for that abstract.

Why are you so anti-$?
......................

We have no antipathy to capitalism, but we do hate $ 
as a marker for inline math.
If you're habituated to $inlinemath$ and loath to change, please
consider: why do you bother typing all those $ anyway?  What's the 
point?  A human being can tell which parts of a text are
math (vs. not) without needing the $.  Thus their only
purpose is to inform a *computer* which parts are math (vs. not).
But do they do this?  No: $ is supposed to indicate a *transition*
between math and text, but it does not indicate whether the math
is *starting* or *ending*.  Would you replace all the parentheses 
(...) in your equations with $...$?  No -- you wouldn't be able to 
tell whether $ means open or close. 
Similarly, a computer can't tell whether $ means start-inlinemath 
or stop-inlinemath (even though that may seem obvious to you), 
for the very simple reason that it can't tell the difference between 
math vs. text -- that's why it needed a delimiter in the first place!
Concretely, if a user accidentally forgets one $ for an equation
(or, perish the thought, writes "$15"), then $ immediately shows
its worthlessness by reversing the correct calls (all subsequent text gets called
as inline math, and all inline math gets called as text).

To make a long story short, $inlinemath$ must die, because

* people make mistakes;
* computers must be able to detect and handle those mistakes sanely;
* $inlinemath$ makes that impossible.

If you want more gory details, for a start see 
`this discussion <https://github.com/cjlee112/spnet/issues/24>`_.

Open Design
-----------

Note that thanks to our open design, you do not even need
to create a SelectedPapers.net login.  Instead, SelectedPapers.net
authenticates with Google (for example) that you are signed in
to Google+; you never give SelectedPapers.net your Google
password or access to any confidential information.  

Moreover, even when you are signed in
to SelectedPapers.net using your Google sign-in,
it cannot see any of your private posts, only those
you posted publicly - in other words, exactly the same 
as what anybody on the Internet can see.  




