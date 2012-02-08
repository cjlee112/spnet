##############################
Peer Review Interface Proposal
##############################


Submission
----------

Authors enter

* title
* abstract
* paper and figures
* list of people whom this paper should interest (as both
  audience and possible reviewers).


Alpha: pre-review audience search
---------------------------------

Informal: main measure is *does the SPR read the paper*.

* send title in email with link to abstract;
* email also has link for "No time to look at anything this week."
* email also has link for "Not of sufficient interest for my work."
* email also has link for "Potential conflict of interest."
* view of abstract is linked to full paper;
* view of full paper is linked to figures.

If SPR views these, he's asked to rate its interest for him:

* high: this paper is must-read for my work or someone I know.
* medium: I will cite this paper in my next paper in this area.
* low: I think this paper will be of interest to <email addresses>.
* not of interest in my area.

He can also type informal comments in a text box.  He can choose
privacy options:

* comments only for the authors;
* comments viewable by other reviewers;

Finally, the SPR is asked whether he will participate in the
review: "We follow a collaborative peer review process in which
multiple reviewers pool their expertise to identify possible
issues for the validation of the paper.  Thus you do not need to 
be an expert on all aspects to contribute to this review process.
This has two phases:

* raising issues and questions about the claims' validity;
* deciding whether you would recommend the paper (to colleagues
  who share your interests) as a valid advance over previous work,
  based on the authors' responses and revisions."

Participate?: Yes / No

Reasons not: don't have time / conflict of interest / other.

Anonymity:

* show my name on my review comments (default)
* keep my identity anonymous during this review.

Beta: validity assessment
-------------------------

Data model
..........

Reviewers begin by reviewing the list of issues already
raised by other reviewers, and 
entering additional proposed **issues**.  Each issue consists
of

* title
* category: one of
  
  * Doubts: issues that could render a specific claim invalid;
  * Prior work: citations that could subsume part or all of the claimed
    advance;
  * Extensions: issues that could indicate additional results are possible;
  * Writing: issues concerning the clarity, accessibility, conciseness
    and appropriateness of text, figures, supplements.
  * Data sharing:

* description: what is the issue?
* suggestions: what could be done to address this issue?
* opinions: each reviewer can assign either an open or closed status
  to this issue

  * Crucial: I cannot recommend the paper without this resolved.
  * important: my decision will depend at least in part on this.
  * nice to have: I would like this resolved but it is not required.
  * not needed: I see no need to address this.
  * FATAL: I've decided not to recommend, because of this issue.
  * RESOLVED: this issue has been resolved to my satisfaction.

* responses: changes made by the authors to address this issue.

* Each of these can have any number of linked comments, each tied
  to (selected text of) a specific version.

The paper and the issue database will be kept under version control;
that is, each addition or change will be tracked as a new commit.

Each reviewer controls:

* his recommendation decision
* issue title, category and description of issues he defined;
* his opinion on each issue;
* can add any number of comments on each issue;

The authors control:

* what to do (responses) for each issue;
* add any number of comments on each issue;
* create new versions of the paper;
* when to release the paper, and where;

Each author response should specify what kind of resolution
they assert:

* resolved by evidence: data or citations
* invalid assumptions: they assert that an issue is based on assumptions
  that do not apply to these data;
* still an advance: they assert that the issue does not undercut
  the result as a significant advance over previous work.
* duplicate: they assert that the issue duplicates another issue
  and should be merged with it.
* accepted and revised: the authors accept the criticism
  as valid and revised the manuscript accordingly (e.g. by
  removing the claim).


Decision
........

The reviewer is asked to decide whether he recommends the paper.
He is shown the current status of his own and other referees'
ratings of the issues, with a default setting based on his
ratings:

* if he has unresolved crucial issues, the default is NO.
* if he has unresolved important issues, the default is Maybe.
* otherwise, the default is YES (since he already rated the paper
  as high interest).





  
