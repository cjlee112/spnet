import core, connect, arxiv

# start test from a blank slate
dbconn = connect.init_connection()
dbconn._conn.drop_database('spnet')
dbconn._conn.drop_database('paperDB')

jojo = core.Person(docData=dict(name='jojo', age=37))
a1 = core.EmailAddress(docData=dict(address='jojo@nowhere.edu', current=True),
                       parent=jojo)
fred = core.Person(docData=dict(name='fred', age=56))
a2 = core.EmailAddress(docData=dict(address='fred@dotzler.com',
                                    authenticated=False), parent=fred)
a3 = core.EmailAddress(docData=dict(address='fred@gmail.com',
                                    note='personal account'), parent=fred)
l = list(arxiv.lookup_papers(('1302.4871', '1205.6541')))
paper1 = core.ArxivPaperData(docData=l[0], insertNew='findOrInsert').parent
paper1.update(dict(authors=[jojo._id]))
paper2 = core.ArxivPaperData(docData=l[1], insertNew='findOrInsert').parent
paper2.update(dict(authors=[fred._id, jojo._id]))

assert paper1.arxiv.id == '1302.4871'
assert paper2.arxiv.id == '1205.6541'

jojoGplus = core.GplusPersonData(docData=dict(id=1234, displayName='Joseph Nye'),
                                parent=jojo)
jojoGplus.update(dict(etag='oldversion'))

sig1 = core.SIG(docData=dict(name='math'))
sig2 = core.SIG(docData=dict(name='physics'))

gplus2 = core.GplusPersonData(docData=dict(id=1234, displayName='Joseph Nye'),
                              insertNew='findOrInsert')

assert gplus2 == jojoGplus

gplus3 = core.GplusPersonData(docData=dict(id=5678, displayName='Fred Eiserling'),
                              insertNew='findOrInsert')
assert gplus3.parent.name == 'Fred Eiserling'

rec1 = core.Recommendation(docData=dict(author=fred._id,
                                        text='I like this paper'),
                           parent=paper1)
rec2 = core.Recommendation(docData=dict(author=jojo._id, text='must read!',
                                        sigs=[sig1._id, sig2._id]),
                           parent=paper2._id)

post1 = core.Post(docData=dict(author=fred._id, text='interesting paper!',
                               id=98765), parent=paper1)
reply1 = core.Reply(docData=dict(author=fred._id, text='interesting paper!',
                                 id=7890, replyTo=98765), parent=paper1)

issue1 = core.Issue(docLinks=dict(paper=paper1),
                    docData=dict(title='The claims are garbage',
                                 category='validity', author=jojo._id,
                                 description='there is a major flaw in the first step of your proof'))

vote1 = core.IssueVote(docLinks=dict(person=jojo),
                       docData=dict(rating='crucial', status='open'),
                       parent=issue1)

assert core.Person(jojo._id).email == [a1]
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
assert core.Post(98765).author == fred
assert core.Reply(7890).replyTo == post1
assert core.Reply(7890).parent == paper1

replyAgain = core.Reply(docData=dict(author=fred._id, text='interesting paper!',
                                 id=7890, replyTo=98765), parent=paper1,
                        insertNew='findOrInsert')
assert replyAgain == reply1
assert core.Paper(paper1._id).replies == [reply1]

reply2 = core.Reply(docData=dict(author=jojo._id, text='boring paper',
                                 id=7891, replyTo=98765), parent=paper1,
                        insertNew='findOrInsert')

assert core.Paper(paper1._id).replies == [reply1, reply2]


assert p.issues[0] == issue1
assert len(p.issues[0].votes) == 1
assert len(rec2.sigs) == 2
assert rec2.sigs[0] == sig1
assert sig1.recommendations == [rec2]

rec1.array_append('sigs', sig2)

assert len(sig2.recommendations) == 2

rec2.update(dict(text='simply dreadful!', score=27))
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

rec3 = core.Recommendation(docData=dict(author=fred._id, text='big_deal',
                                        sigs=[sig2._id]),
                           parent=paper2._id)

assert core.SIG(sig1._id).recommendations == [rec2]
assert len(core.SIG(sig2._id).recommendations) == 3
