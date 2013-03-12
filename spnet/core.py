from base import *
from hashlib import sha1



##########################################################

# fetch functions for use with LinkDescriptor 

def fetch_recs(person):
    'return list of Recommendation objects for specified person'
    coll = Recommendation.coll
    results = coll.find({'recommendations.author':person._id},
                        {'recommendations':1})
    l = []
    for r in results:
        paperID = r['_id']
        for recDict in r['recommendations']:
            if recDict['author'] == person._id:
                l.append(Recommendation(docData=recDict, parent=paperID,
                                        insertNew=False))
                break
    return l

def merge_sigs(person, attr, sigLinks):
    'postprocess list of SIGLinks to handle mergeIn requests'
    d = {}
    merges = []
    for sl in sigLinks:
        d[sl.dbDocDict['sig']] = sl
        if hasattr(sl, 'mergeIn'):
            merges.append(sl)
    for sl in merges:
        d[sl.mergeIn]._add_merge(sl)
    


######################################################

# forward declarations to avoid circular ref problem
fetch_paper = FetchObj(None)
fetch_person = FetchObj(None)
fetch_sig = FetchObj(None)
fetch_sigs = FetchList(None)
fetch_people = FetchList(None)
fetch_papers = FetchList(None)
fetch_parent_issue = FetchParent(None)
fetch_parent_person = FetchParent(None)
fetch_parent_paper = FetchParent(None)
fetch_author_papers = FetchQuery(None, lambda author:dict(authors=author._id))
fetch_subscribers = FetchQuery(None, lambda person:
                               dict(subscriptions=person._id))
fetch_sig_members = FetchQuery(None, lambda sig: {'sigs.sig':sig._id})
fetch_sig_papers = FetchQuery(None, lambda sig: {'sigs':sig._id})
fetch_sig_recs = FetchQuery(None, lambda sig:
                            {'recommendations.sigs':sig._id})
fetch_issues = FetchQuery(None, lambda paper:dict(paper=paper._id))

# main object classes

class EmailAddress(UniqueArrayDocument):
    _dbfield = 'email.address' # dot.name for updating

    parent = LinkDescriptor('parent', fetch_parent_person, noData=True)


class Recommendation(ArrayDocument):
    useObjectId = False # input data will supply _id
    # attrs that will only be fetched if accessed by user
    parent = LinkDescriptor('parent', fetch_parent_paper, noData=True)
    author = LinkDescriptor('author', fetch_person)
    forwards = LinkDescriptor('forwards', fetch_people)
    sigs = LinkDescriptor('sigs', fetch_sigs, missingData=())

    _dbfield = 'recommendations.author' # dot.name for updating


class IssueVote(ArrayDocument):
    _dbfield = 'votes.person' # dot.name for updating
    person = LinkDescriptor('person', fetch_person)
    parent = LinkDescriptor('parent', fetch_parent_issue, noData=True)


class Issue(Document):
    '''interface for a question raised about a paper '''

    # attrs that will only be fetched if accessed by user
    paper = LinkDescriptor('paper', fetch_paper)
    author = LinkDescriptor('author', fetch_person)

    # custom attr constructors
    _attrHandler = dict(
        votes=SaveAttrList(IssueVote, insertNew=False),
        )

class SIG(Document):
    '''interface for a Specific Interest Group'''
    _requiredFields = ('name',)

    # attrs that will only be fetched if accessed by user
    members = LinkDescriptor('members', fetch_sig_members, noData=True)
    papers = LinkDescriptor('papers', fetch_sig_papers, noData=True)
    recommendations  = LinkDescriptor('recommendations', fetch_sig_recs,
                                      noData=True)


# current unused
class SIGLink(ArrayDocument):
    _dbfield = 'sigs.sig' # dot.name for updating
    sig = LinkDescriptor('sig', fetch_sig)
    parent = LinkDescriptor('parent', fetch_parent_person, noData=True)

    def _add_merge(self, other):
        try:
            self._mergeLinks.append(other)
        except AttributeError:
            self._mergeLinks = [other]

class GplusPersonData(EmbeddedDocument):
    _dbfield = 'gplus.id'
    parent = LinkDescriptor('parent', fetch_parent_person, noData=True)
    def _insert_parent(self):
        'create Person document in db for this gplus.id'
        return Person(docData=dict(name=self.displayName))


class Person(Document):
    '''interface to a stable identity tied to a set of publications '''
    _requiredFields = ('name',)
    # attrs that will only be fetched if accessed by user
    papers = LinkDescriptor('papers', fetch_author_papers, noData=True)
    recommendations = LinkDescriptor('recommendations', fetch_recs,
                                     noData=True)
    subscriptions = LinkDescriptor('subscriptions', fetch_people,
                                   missingData=())
    subscribers = LinkDescriptor('subscribers', fetch_subscribers,
                                 noData=True)

    # custom attr constructors
    _attrHandler = dict(
        email=SaveAttrList(EmailAddress, insertNew=False),
        gplus=SaveAttr(GplusPersonData, insertNew=False),
        ## sigs=SaveAttrList(SIGLink, postprocess=merge_sigs, insertNew=False),
        )

    def authenticate(self, password):
        try:
            return self.password == sha1(password).hexdigest()
        except AttributeError:
            return False
    def set_password(self, password):
        self.update(dict(password=sha1(password).hexdigest()))


class Paper(Document):
    '''interface to a specific paper '''
    useObjectId = False # input data will supply _id

    # attrs that will only be fetched if accessed by user
    authors = LinkDescriptor('authors', fetch_people)
    references = LinkDescriptor('references', fetch_papers,
                                missingData=())
    issues = LinkDescriptor('issues', fetch_issues,
                            noData=True, missingData=())
    sigs = LinkDescriptor('sigs', fetch_sigs, missingData=())

    # custom attr constructors
    _attrHandler = dict(
        recommendations=SaveAttrList(Recommendation, insertNew=False),
        )


class Tag(Document):
    'a specific keyword tag'
    pass
    ## def _new_fields(self):
    ##     'check that new tag is unique before inserting'
    ##     try:
    ##         name = self._dbDocDict['name']
    ##     except KeyError:
    ##         raise ValueError('new Tag has no name attribute!')
    ##     if list(self.__class__.find(dict(name=name))):
    ##         raise ValueError('Tag "%s" already exists!' % name)

# connect forward declarations to their target classes
fetch_paper.klass = Paper
fetch_parent_issue.klass = Issue
fetch_sig.klass = SIG
fetch_sigs.klass = SIG
fetch_person.klass = Person
fetch_papers.klass = Paper
fetch_people.klass = Person
fetch_parent_person.klass = Person
fetch_parent_paper.klass = Paper
fetch_author_papers.klass = Paper
fetch_subscribers.klass = Person
fetch_sig_members.klass = Person
fetch_sig_papers.klass = Paper
fetch_sig_recs.klass = Recommendation
fetch_issues.klass = Issue

##################################################################

def get_or_create_person(d, subdoc, idField, nameField):
    try:
        p = Person.find_obj({subdoc + '.' + idField:d[idField]}).next()
    except StopIteration:
        p = Person(docData={'name':d[nameField], subdoc:d})
    return p
