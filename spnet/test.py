import core, connect

# start test from a blank slate
connect.dbconn._conn.drop_database('spnet')
connect.dbconn._conn.drop_database('paperDB')

jojo = core.Person(connect.dbconn, name='jojo', age=37)
a1 = core.EmailAddress('jojo@nowhere.edu', jojo, current=True)
fred = core.Person(connect.dbconn, name='fred', age=56)
a2 = core.EmailAddress('fred@dotzler.com', fred, authenticated=False)
a3 = core.EmailAddress('fred@gmail.com', fred, note='personal account')
paper1 = core.Paper(connect.dbconn, title='boring article', year=2011,
                    authors=[jojo._id])
paper2 = core.Paper(connect.dbconn, title='great article', year=2012,
                    authors=[fred._id,jojo._id])

rec1 = core.Recommendation(paper1, author=fred._id, text='I like this paper')
rec2 = core.Recommendation(None, 'arxiv:' + str(paper2._id), connect.dbconn,
                           author=jojo._id, text='must read!')



assert len(rec1.paper.authors) == 1
assert rec1.paper.authors[0] == jojo
assert len(rec2.paper.authors) == 2
assert jojo in rec2.paper.authors
assert fred in rec2.paper.authors
assert len(rec2.paper.recommendations) == 1
assert len(jojo.recommendations) == 1
assert jojo.recommendations[0] == rec2
assert len(jojo.papers) == 2
assert len(fred.papers) == 1
assert len(paper2.authors[0].email) == 2

rec2.update(dict(text='simply dreadful!', score=27))
rec3 = core.Recommendation(None, 'arxiv:' + str(paper2._id), connect.dbconn,
                           author=jojo._id, fetch=True)
assert rec3.score == 27

a4 = core.EmailAddress('fred@dotzler.com', dbconn=connect.dbconn, fetch=True)
assert a4._parentID == fred._id
assert a4.person == fred

try:
    p = core.Person(connect.dbconn, 'abcdefg')
except KeyError:
    pass
else:
    raise AssertionError('failed to trap bad personID')

try:
    a = core.EmailAddress('bob@yoyo.com', dbconn=connect.dbconn, fetch=True)
except KeyError:
    pass
else:
    raise AssertionError('failed to trap bad email')
