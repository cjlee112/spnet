import core, connect
import gplus
##import pubmed
import pickle
import doi
from bson import ObjectId
import apptree
import incoming
from datetime import datetime
import time

# start test from a blank slate
dbconn = connect.init_connection()
dbconn._conn.drop_database('spnet')
dbconn._conn.drop_database('paperDB')

rootColl = apptree.get_collections()

lorem = '''Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'''

jojo = core.Person(docData=dict(name='jojo', age=37))
assert jojo != None
a1 = core.EmailAddress(docData=dict(address='jojo@nowhere.edu', current=True),
                       parent=jojo)
fred = core.Person(docData=dict(name='fred', age=56))
a2 = core.EmailAddress(docData=dict(address='fred@dotzler.com',
                                    authenticated=False), parent=fred)
a3 = core.EmailAddress(docData=dict(address='fred@gmail.com',
                                    note='personal account'), parent=fred)

paper1 = core.ArxivPaperData('1302.4871', insertNew='findOrInsert').parent
paper1.update(dict(authors=[jojo._id]))
paper2 = core.ArxivPaperData('1205.6541', insertNew='findOrInsert').parent
paper2.update(dict(authors=[fred._id, jojo._id]))

assert paper1.arxiv.id == '1302.4871'
assert paper2.arxiv.id == '1205.6541'

jojoGplus = core.GplusPersonData(docData=dict(id=1234, displayName='Joseph Nye', image={'url':'http://www.nobelprize.org/nobel_prizes/physics/laureates/1921/einstein.jpg'}),
                                parent=jojo)
jojoGplus.update(dict(etag='oldversion'))

sig1 = core.SIG.find_or_insert('cosmology')
sig2 = core.SIG.find_or_insert('lambdaCDMmodel')

topicWords = incoming.get_topicIDs(dict(topic=['cosmology', 'astrophysics']),
                                   1, datetime.utcnow(), 'test')
assert topicWords == ['cosmology', 'astrophysics']
astroSIG = core.SIG('astrophysics')
assert astroSIG.name == '#astrophysics'
assert astroSIG.origin == dict(source='test', id=1)


int1 = core.PaperInterest(docData=dict(author=jojo._id, topics=[sig1._id]),
                          parent=paper1)
assert core.Paper(paper1._id).interests == [int1]
assert core.Paper(paper1._id).get_interests() == {sig1._id:[jojo]}
assert core.Person(jojo._id).interests == [int1]
assert core.SIG(sig1._id).interests == [int1]
assert core.SIG(sig1._id).get_interests() == {paper1:[jojo]}

intAgain = core.PaperInterest((paper1._id, jojo._id))
assert intAgain == int1
try:
    intAgain.remove_topic(sig2._id)
except KeyError:
    pass
else:
    raise AssertionError('failed to catch bad remove_topic()')
assert intAgain.remove_topic(sig1._id) is None
assert core.Paper(paper1._id).interests == []

# test creation via POST
paperLikes = rootColl['papers'].likes
int2 = paperLikes._POST(fred._id, sig2._id, '1',
                        parents=dict(paper=paper2))
assert int2.parent == paper2
assert int2.author == fred
assert int2.topics == [sig2]
assert core.Paper(paper2._id).interests == [int2]
assert core.Person(fred._id).interests == [int2]
assert core.SIG(sig2._id).interests == [int2]
try:
    paperLikes._POST(fred._id, 'this is not allowed', '1',
                     parents=dict(paper=paper2))
except KeyError:
    pass
else:
    raise AssertionError('failed to trap bad topic string')
# test removal via POST
assert paperLikes._POST(fred._id, sig2._id, '0',
                        parents=dict(paper=core.Paper(paper2._id))) == int2
assert core.Paper(paper2._id).interests == []

int3 = paperLikes._POST(fred._id, '#silicene', '1',
                        parents=dict(paper=paper2))
assert core.SIG('silicene').interests == [int3]


gplus2 = core.GplusPersonData(docData=dict(id=1234, displayName='Joseph Nye'),
                              insertNew='findOrInsert')

assert gplus2 == jojoGplus

gplus3 = core.GplusPersonData(docData=dict(id=5678, displayName='Fred Eiserling'),
                              insertNew='findOrInsert')
assert gplus3.parent.name == 'Fred Eiserling'

rec1 = core.Recommendation(docData=dict(author=fred._id,
                                        title='Why You Need to Read This Important Extension of the CDM Model',
                                        text=lorem),
                           parent=paper1)
rec2 = core.Recommendation(docData=dict(author=jojo._id, text='must read!',
                                        sigs=[sig1._id, sig2._id]),
                           parent=paper2._id)

post1 = core.Post(docData=dict(author=fred._id, text='interesting paper!',
                               id=98765, sigs=[sig1._id]), parent=paper1)
reply1 = core.Reply(docData=dict(author=jojo._id, text='I disagree with Fred.',
                                 id=7890, replyTo=98765), parent=paper1)

issue1 = core.Issue(docData=dict(paper=paper1, title='The claims are garbage',
                                 category='validity', author=jojo._id,
                                 description='there is a major flaw in the first step of your proof'))

vote1 = core.IssueVote(docData=dict(person=jojo, rating='crucial',
                                    status='open'),
                       parent=issue1)

assert core.Person(jojo._id).email == [a1]
assert core.Person(jojo._id).replies == [reply1]
jgp = core.GplusPersonData(1234)
assert jgp.parent == jojo
assert jgp.etag == 'oldversion'
assert len(rec1.parent.authors) == 1
assert rec1.parent.authors[0] == jojo
assert len(rec2.parent.authors) == 2
assert jojo in rec2.parent.authors
assert fred in rec2.parent.authors
assert len(rec2.parent.recommendations) == 1
assert len(jojo.recommendations) == 1
assert jojo.recommendations[0] == rec2
assert len(jojo.papers) == 2
assert len(fred.papers) == 1
assert len(paper2.authors[0].email) == 2
assert issue1.author == jojo
p = core.Paper(paper1._id)
assert len(p.issues) == 1
assert len(p.posts) == 1
assert p.posts == [post1]
assert p.posts[0].text == 'interesting paper!'
assert list(p.posts[0].get_replies()) == [reply1]
assert core.Post(98765).author == fred
assert core.Reply(7890).replyTo == post1
assert core.Reply(7890).parent == paper1
assert core.Person(fred._id).posts == [post1]
assert core.SIG(sig1._id).posts == [post1]
assert core.Post(98765).sigs == [sig1]

replyAgain = core.Reply(docData=dict(author=fred._id, text='interesting paper!',
                                 id=7890, replyTo=98765), parent=paper1,
                        insertNew='findOrInsert')
assert replyAgain == reply1
assert core.Paper(paper1._id).replies == [reply1]

reply2 = core.Reply(docData=dict(author=jojo._id, text='This paper really made me think.',
                                 id=7891, replyTo=98765), parent=paper1,
                        insertNew='findOrInsert')

assert core.Paper(paper1._id).replies == [reply1, reply2]
assert core.Paper(str(paper1._id)) == paper1, 'auto ID conversion failed'

assert p.issues[0] == issue1
assert len(p.issues[0].votes) == 1
assert len(rec2.sigs) == 2
assert rec2.sigs[0] == sig1
assert sig1.recommendations == [rec2]

rec1.array_append('sigs', sig2)

assert len(sig2.recommendations) == 2
assert core.Recommendation((rec1.parent._id, rec1._get_id())).sigs == [sig2]

rec2.update(dict(text='totally fascinating!', score=27))
rec3 = core.Recommendation((paper2._id, jojo._id))
assert rec3.score == 27

a4 = core.EmailAddress('fred@dotzler.com')
assert a4._parent_link == fred._id
assert a4.parent == fred

try:
    p = core.Person('abcdefg')
except KeyError:
    pass
else:
    raise AssertionError('failed to trap bad personID')

try:
    a = core.EmailAddress('bob@yoyo.com')
except KeyError:
    pass
else:
    raise AssertionError('failed to trap bad email')

try:
    jojo = core.Person(docData=dict(name2='jojo', age=37))
except ValueError:
    pass
else:
    raise AssertionError('failed to trap Person w/o name')

fred.array_append('numbers', 17)
assert core.Person(fred._id).numbers == [17]
fred.array_append('numbers', 6)
assert core.Person(fred._id).numbers == [17, 6]
fred.array_del('numbers', 17)
assert core.Person(fred._id).numbers == [6]

a4.array_append('numbers', 17)
assert core.EmailAddress(a4.address).numbers == [17]
a4.array_append('numbers', 6)
assert core.EmailAddress(a4.address).numbers == [17, 6]
a4.array_del('numbers', 17)
assert core.EmailAddress(a4.address).numbers == [6]

rec3 = core.Recommendation(docData=dict(author=fred._id,
                         text='I think this is a major breakthrough.',
                                        sigs=[sig2._id], id=3456),
                           parent=paper2._id)

assert core.SIG(sig1._id).recommendations == [rec2]
assert len(core.SIG(sig2._id).recommendations) == 3

it = gplus.publicAccess.get_person_posts('107295654786633294692')
testPosts = list(gplus.publicAccess.find_or_insert_posts(it))
assert len(testPosts) > 0

nposts = len(core.Paper(paper1._id).posts)
nreplies = len(core.Paper(paper1._id).replies)
it = gplus.publicAccess.get_person_posts('107295654786633294692')
testPosts2 = list(gplus.publicAccess.find_or_insert_posts(it))
assert testPosts == testPosts2
assert nposts == len(core.Paper(paper1._id).posts)
assert nreplies == len(core.Paper(paper1._id).replies)

gpd = core.GplusPersonData('112634568601116338347',
                           insertNew='findOrInsert')
assert gpd.displayName == 'Meenakshi Roy'
gpd.update_subscriptions(dict(etag='foo', totalItems=1),
                         [dict(id='114744049040264263224')])
gps = gpd.subscriptions
assert gps.gplusPerson == gpd
mrID = gpd.parent._id
subscriptions = core.Person(mrID).subscriptions
assert len(subscriptions) == 0

gpd2 = core.GplusPersonData('114744049040264263224',
                            insertNew='findOrInsert')
time.sleep(2)
subscriptions = core.Person(mrID).subscriptions
assert len(subscriptions) == 1
assert subscriptions[0].author == gpd2.parent

gpd2.update_posts() # retrieve some recs

recReply = core.Reply(docData=dict(author=jojo._id, id=78901, replyTo=3456,
                      text='Fred, thanks for your comments!  Your insights are really helpful.'),
                      parent=paper2._id)

# make sure timestamps present on all recs
l = [r.published for r in core.Recommendation.find_obj()]
l = [r.published for r in core.Post.find_obj()]
l = [r.published for r in core.Reply.find_obj()]

assert recReply.replyTo == rec3
assert list(recReply.replyTo.get_replies()) == [recReply]

# pubmed eutils network server constantly failing now??
## pubmedDict = pubmed.get_pubmed_dict('23482246')
## with open('../pubmed/test1.pickle') as ifile:
##     correctDict = pickle.load(ifile)
## assert pubmedDict == correctDict

## paper3 = core.PubmedPaperData('23482246', insertNew='findOrInsert').parent
## paper3.update(dict(authors=[fred._id]))

## ppd = core.PubmedPaperData('23139441', insertNew='findOrInsert')
## assert ppd.doi.upper() == '10.1016/J.MSEC.2012.05.020'

## assert paper3.pubmed.id == '23482246'
## assert paper3.title[:40] == correctDict['title'][:40]

s = 'aabbe'
t = doi.map_to_doi(s)
assert t == '10.1002/(SICI)1097-0258(19980815/30)17:15/16<1661::AID-SIM968>3.0.CO;2-2'
assert s == doi.map_to_shortdoi(t)

paper4 = core.DoiPaperData(DOI=t, insertNew='findOrInsert').parent
paper4.update(dict(authors=[fred._id]))
assert paper4.doi.id == s
assert paper4.doi.doi == t
assert paper4.doi.DOI == t.upper()
paper5 = core.DoiPaperData(s, insertNew='findOrInsert').parent
assert paper4 == paper5
assert rootColl['shortDOI']._GET(s) == paper4
txt = 'some text ' + paper4.doi.get_hashtag()
assert incoming.get_hashtag_dict(txt)['paper'] == [paper4]

spnetPaper = core.DoiPaperData(DOI='10.3389/fncom.2012.00001',
                               insertNew='findOrInsert').parent
assert spnetPaper.title.lower() == 'open peer review by a selected-papers network'
txt = 'a long comment ' + spnetPaper.doi.get_doctag() + ', some more text'
assert incoming.get_hashtag_dict(txt)['paper'] == [spnetPaper]

## t = 'this is text #spnetwork #recommend #arxiv_1302_4871 #pubmed_22291635 #cosmology'
## d = incoming.get_hashtag_dict(t)
## assert d == {'header': ['spnetwork'], 'topic': ['cosmology'], 'paper': [paper1, spnetPaper], 'rec': ['recommend']}

## t = 'this is text #spnetwork #recommend arXiv:1302.4871 PMID: 22291635 #cosmology'
## d = incoming.get_hashtag_dict(t)
## assert d == {'header': ['spnetwork'], 'topic': ['cosmology'], 'paper': [paper1, spnetPaper], 'rec': ['recommend']}

t = 'this is text #spnetwork #recommend doi: 10.3389/fncom.2012.00001 i like doi: this #cosmology'
d = incoming.get_hashtag_dict(t)
assert d == {'header': ['spnetwork'], 'topic': ['cosmology'], 'paper': [spnetPaper], 'rec': ['recommend']}
