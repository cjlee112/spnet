
from dbconn import DBConnection
from core import Paper, Person, Recommendation, EmailAddress, Issue, IssueVote

connectDict = {
    Paper:'spnet.paper',
    Person:'spnet.person',
    Recommendation:'spnet.paper',
    EmailAddress:'spnet.person',
    Issue:'spnet.issue',
    IssueVote:'spnet.issue',
    }



def init_connection(**kwargs):
    'set klass.coll on each db class to give it db connection'
    dbconn = DBConnection(connectDict, **kwargs)
    return dbconn
    
