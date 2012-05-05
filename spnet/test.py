import core, connect

# start test from a blank slate
connect.dbconn._conn.drop_database('spnet')
connect.dbconn._conn.drop_database('paperDB')

jojo = core.Person(connect.dbconn, name='jojo', email='jojo@nowhere.edu',
                   age=37)
fred = core.Person(connect.dbconn, name='fred', email='fred@dotzler.com',
                   age=56)
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

