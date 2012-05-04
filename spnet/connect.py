
from dbconn import DBSet, DBConnection

paperDBdict = dict(
    arxiv={}
    )

connectDict = dict(
    dbset=DBSet(paperDBdict, 'arxiv'),
    person='spnet.person',
    )


dbconn = DBConnection(**connectDict)
