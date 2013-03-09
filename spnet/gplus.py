import random
import urllib
import string
import json
import requests
from datetime import datetime, timedelta
from oauth2client.client import OAuth2Credentials, _extract_id_token
# supposed to work but doesn't... maybe in a newer version?
#from oauth2client import GOOGLE_AUTH_URI
#from oauth2client import GOOGLE_REVOKE_URI
#from oauth2client import GOOGLE_TOKEN_URI
import httplib2
from apiclient.discovery import build
import core


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
                 scope='https://www.googleapis.com/auth/plus.me',
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
                 response_type=response_type, scope=scope)
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
        http = httplib2.Http()
        http = self.credentials.authorize(http)
        service = build('plus', 'v1', http=http)
        person = service.people().get(userId='me').execute(http=http)
        return core.get_or_create_person(person, 'gplus', 'id',
                                         'displayName')

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
            params['pageToken'] = results['nextPageToken'] # get next page
            results = self.request(uri, **params)
