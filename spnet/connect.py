
from dbconn import DBConnection
from core import Paper, Person, Recommendation, EmailAddress, Issue, IssueVote, SIG, GplusPersonData, Post, Reply, ArxivPaperData, PubmedPaperData, DoiPaperData, PaperInterest, GplusSubscriptions, Subscription, TopicOptions
import json
from pymongo.errors import ConnectionFailure

connectDict = {
    Paper:'spnet.paper',
    Person:'spnet.person',
    Recommendation:'spnet.paper',
    EmailAddress:'spnet.person',
    Issue:'spnet.issue',
    IssueVote:'spnet.issue',
    SIG:'spnet.sig',
    GplusPersonData:'spnet.person',
    GplusSubscriptions:'spnet.gplus_subs',
    Post:'spnet.paper',
    Reply:'spnet.paper',
    ArxivPaperData:'spnet.paper',
    PubmedPaperData:'spnet.paper',
    DoiPaperData:'spnet.paper',
    PaperInterest:'spnet.paper',
    Subscription:'spnet.person',
    TopicOptions:'spnet.person',
    }



def init_connection(spnetUrlBase='https://selectedpapers.net', **kwargs):
    'set klass.coll on each db class to give it db connection'
    try:
        dbconn = DBConnection(connectDict, **kwargs)
    except ConnectionFailure:
        try:
            with open('../data.json') as ifile:
                dbconfig = json.load(ifile)
        except IOError:
            print '''ERROR: default database connection failed and 
database connection parameters file not found.  If you are running
a test / development platform, make sure that your mongod is running
and accepting connections (from localhost, without a password).'''
            raise
        kwargs.update(dbconfig)
        dbconn = DBConnection(connectDict, **kwargs)
    for klass in connectDict: # set default URL
        klass._spnet_url_base = spnetUrlBase
    return dbconn
    
