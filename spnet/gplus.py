import random
import urllib
import string
import json
import requests
from datetime import datetime, timedelta
import dateutil.parser
from oauth2client.client import OAuth2Credentials, _extract_id_token
# supposed to work but doesn't... maybe in a newer version?
#from oauth2client import GOOGLE_AUTH_URI
#from oauth2client import GOOGLE_REVOKE_URI
#from oauth2client import GOOGLE_TOKEN_URI
import httplib2
from apiclient.discovery import build


# Question: what's worse than an F+ ?
# Answer: this.

GOOGLE_AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_REVOKE_URI = 'https://accounts.google.com/o/oauth2/revoke'
GOOGLE_TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'

def get_keys(keyfile='../google/keys.json'):
    with open(keyfile, 'r') as ifile:
        keys = json.loads(ifile.read())
    return keys


# we could just use Google's oauth2client.OAuth2WebServerFlow
# but for some reason it doesn't implement the state check
# protection against CSRF attack.  So I implemented simple code
# that does protect against that.

class OAuth(object):
    def __init__(self, auth_uri=GOOGLE_AUTH_URI,
                 token_uri=GOOGLE_TOKEN_URI,
                 revoke_uri=GOOGLE_REVOKE_URI,
                 scope='https://www.googleapis.com/auth/plus.login',
                 requestvisibleactions='http://schemas.google.com/AddActivity',
                 response_type='code', access_type='offline', user_agent=None,
                 keys=None, **kwargs):
        self.auth_uri = auth_uri
        self.token_uri = token_uri
        self.revoke_uri = revoke_uri
        self.user_agent = None
        self.state = ''.join([random.choice(string.ascii_uppercase + string.digits)
                              for x in xrange(32)])
        if not keys:
            keys = get_keys()
        self.keys = keys
        d = dict(state=self.state, redirect_uri=self.keys['redirect_uri'],
                 client_id=self.keys['client_ID'], access_type=access_type,
                 response_type=response_type, scope=scope,
                 requestvisibleactions=requestvisibleactions)
        d.update(kwargs)
        self.login_url = auth_uri + '?' + urllib.urlencode(d)

    def get_authorize_url(self):
        'get URL to redirect user to sign-in with Google'
        return self.login_url
        
    def get_credentials(self, code, state):
        'use callback data to get an access token'
        if state != self.state:
            return False # CSRF attack?!?
        d = dict(code=code, client_id=self.keys['client_ID'],
                 client_secret=self.keys['client_secret'],
                 redirect_uri=self.keys['redirect_uri'],
                 grant_type='authorization_code')
        r = requests.post(self.token_uri, data=d)
        self.access_data = ad = r.json()
        try:
            token_expiry = datetime.utcnow() \
                           + timedelta(seconds=int(ad['expires_in']))
        except KeyError:
            token_expiry = None
        if 'id_token' in ad:
            ad['id_token'] = _extract_id_token(ad['id_token'])
        c = OAuth2Credentials(ad['access_token'], d['client_id'],
                              d['client_secret'],
                              ad.get('refresh_token', None), token_expiry,
                              self.token_uri, self.user_agent,
                              id_token=ad.get('id_token', None))
        self.credentials = c
        return c

    def get_person(self):
        'get Person record (or create one) for authenticated user'
        import core
        http = httplib2.Http()
        self.http = http = self.credentials.authorize(http)
        self.service = service = build('plus', 'v1', http=http)
        person = service.people().get(userId='me').execute(http=http)
        gpd = core.GplusPersonData(docData=person, insertNew='findOrInsert')
        p = gpd.parent
        if 'refresh_token' in self.access_data:
            p.update(dict(gplusAccess=self.access_data))
        return p

    # direct access to Google APIs
    # -- because Google's apiclient search is currently broken!!
    def request(self, uri, headers=None, **params):
        'perform API query using our access token or API key'
        if 'access_token' in getattr(self, 'access_data', ()):
            try:
                headers = headers.copy()
            except AttributeError:
                headers = {}
            headers['Authorization'] = 'Bearer ' + \
                                       self.access_data['access_token']
        else: # use simple API key
            params = params.copy()
            params['key'] = self.keys['apikey']
        r = requests.get(uri, params=params, headers=headers)
        return r.json()

    def request_iter(self, uri, **kwargs):
        'generate results from query using paging'
        params = kwargs.copy()
        results = self.request(uri, **params)
        while results['items']:
            for item in results['items']:
                yield item
            try:
                params['pageToken'] = results['nextPageToken'] # get next page
            except KeyError:
                break
            results = self.request(uri, **params)

    def search_activities(self, uri='https://www.googleapis.com/plus/v1/activities', **kwargs):
        'like activities().search() only it WORKS'
        return self.request_iter(uri, **kwargs)

    def get_person_info(self, userID):
        'short cut to people().get(), does authentication for you'
        return self.request('https://www.googleapis.com/plus/v1/people/'
                            + str(userID))

    def get_person_posts(self, userID):
        'short cut to activities().list(), does authentication for you'
        return self.request_iter('https://www.googleapis.com/plus/v1/people/'
                                 + str(userID) + '/activities/public')

    def get_post_comments(self, postID):
        'short cut to comments().list(), does authentication for you'
        return self.request_iter('https://www.googleapis.com/plus/v1/activities/'
                                 + str(postID) + '/comments')

    def find_or_insert_posts(self, posts,
                             get_content=lambda x:x['object']['content'],
                             get_user=lambda x:x['actor']['id'],
                             get_replycount=lambda x:
                             x['object']['replies']['totalItems']):
        'save google+ posts to core.find_or_insert_posts()'
        import core
        return core.find_or_insert_posts(posts, self.get_post_comments,
                                         lambda x:core.GplusPersonData(x,
                               insertNew='findOrInsert').parent,
                                         get_content, get_user,
                                         get_replycount, convert_timestamps,
                                         convert_timestamps)

    def api_iter(self, resourceName='activities', verb='list', **kwargs):
        'use Google apiclient to iterate over results from request'
        try:
            service = self.service
            http = self.http
        except AttributeError:
            service = build('plus', 'v1', developerKey=self.keys['apikey'])
            http = None
        rsrc = getattr(service, resourceName)()
        request = getattr(rsrc, verb)(**kwargs)
        while request is not None:
            doc = request.execute(http=http)
            for item in doc['items']:
                yield item
            request = getattr(rsrc, verb + '_next')(request, doc)

    #def load_recent_spnetwork(self):

def convert_timestamps(d, fields=('published', 'updated')):
    'convert G+ timestamp string fields to datetime objects'
    for f in fields:
        try:
            d[f] = dateutil.parser.parse(d[f])
        except KeyError:
            pass


publicAccess = OAuth() # gives API key based access (search public data)

