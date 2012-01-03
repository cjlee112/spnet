##############################
Peer Review Interface Proposal
##############################


Submission
----------

Authors enter

* title
* abstract
* list of advances: the paper's key claims

  * title of 

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

Authors previously entered a list of claimed *advances* for their paper.

Reviewers begin by reviewing this list, the list of issues already
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

* advance(s) it affects;
* assumptions: grounds on which the referee based this concern.
* relevant citations
* reviewer assessments
* comments, each linked to the paper version (commit) it was made on.

**Reviewer assessments**: each reviewer can make an assessment on a given
issue.  It consists of:

* rating:

  * Crucial: I cannot recommend the paper without this resolved.
  * important: my decision will depend at least in part on this.
  * nice to have: I would like this resolved but it is not required.
  * not needed: I see no need to address this.
  * no opinion

* linked comment where the referee explains his position, suggests
  possible resolutions etc.

* reviewer's expertise on this issue: "I have published similar analysis
  <citations>..."

  * Using same / very similar / similar / different methodology;
  * On same / very similar / similar / different dataset;
  * Addressing same / very similar / similar / different scientific question.

Process
.......

Generate issues (two weeks):

* reviewers start adding issues;
* they can invite additional reviewers;
* each reviewer sees the changes since his last view of the issues;
* each reviewer rates each issue;

Authors respond with a proposed resolution type for each issue:

* resolved by evidence: data or citations
* invalid assumptions: they assert that an issue is based on assumptions
  that do not apply to these data;
* negligible: they assert the issue has little or no effect on the claimed
  advance;
* still an advance: they assert that the issue does not undercut
  the fact that the result is a significant advance over previous work.
* re-categorize: they assert that the issue category should be changed
  (e.g. doubt to extension).
* duplicate: they assert that the issue duplicates another issue
  and should be merged with it.
* accepted: the authors accept the issue and attempt to fix it.

The proposed fix is shown by a diff showing exactly what was changed
in the manuscript.

Each proposed fix is linked to a comment where the authors explain
their position.

Along with this list of proposed fixes,
the authors submit a new version either as *prospective*
(referees are allowed to choose Maybe as a decision),
or *final* (referees can only choose Yes / No as a decision).

Reviewers assess the authors' responses on each issue:

* if a reviewer accepts a fix, that issue is *resolved* for that referee.
* if a reviewer rejects a fix, that issue remains unresolved for that referee.
* each assessment decision is recorded as a comment where the
  referee explains his position.

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

Control
.......

Reviewers are in control of

* their own ratings;
* their decision

Both authors and reviewers can change

* the category of an issue.





  
