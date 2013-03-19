
from dbconn import DBConnection
from core import Paper, Person, Recommendation, EmailAddress, Issue, IssueVote, SIG, GplusPersonData, Post, Reply, ArxivPaperData, PubmedPaperData, DoiPaperData, PaperInterest

connectDict = {
    Paper:'spnet.paper',
    Person:'spnet.person',
    Recommendation:'spnet.paper',
    EmailAddress:'spnet.person',
    Issue:'spnet.issue',
    IssueVote:'spnet.issue',
    SIG:'spnet.sig',
    GplusPersonData:'spnet.person',
    Post:'spnet.paper',
    Reply:'spnet.paper',
    ArxivPaperData:'spnet.paper',
    PubmedPaperData:'spnet.paper',
    DoiPaperData:'spnet.paper',
    PaperInterest:'spnet.paper',
    }



def init_connection(spnetUrlBase='http://selectedpapers.net', **kwargs):
    'set klass.coll on each db class to give it db connection'
    dbconn = DBConnection(connectDict, **kwargs)
    for klass in connectDict: # set default URL
        klass._spnet_url_base = spnetUrlBase
    return dbconn
    
