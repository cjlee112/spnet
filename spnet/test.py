import core, connect

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
paper1 = core.Paper(docData=dict(title='boring article', year=2011,
                                 authors=[jojo._id], _id='1'))
paper2 = core.Paper(docData=dict(title='great article', year=2012,
                                 authors=[fred._id,jojo._id], _id='2'))

rec1 = core.Recommendation(docData=dict(author=fred._id,
                                        text='I like this paper'),
                           parent=paper1)
rec2 = core.Recommendation(docData=dict(author=jojo._id, text='must read!'),
                           parent=paper2._id)

issue1 = core.Issue(docLinks=dict(paper=paper1),
                    docData=dict(title='The claims are garbage',
                                 category='validity', author=jojo._id,
                                 description='there is a major flaw in the first step of your proof'))

vote1 = core.IssueVote(docLinks=dict(person=jojo),
                       docData=dict(rating='crucial', status='open'),
                       parent=issue1)

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
assert p.issues[0] == issue1
assert len(p.issues[0].votes) == 1

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
