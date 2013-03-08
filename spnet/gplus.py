import random
import urllib
import string
import json
import requests

def get_keys(keyfile='../google/keys.json'):
    with open(keyfile, 'r') as ifile:
        keys = json.loads(ifile.read())
    return keys

class OAuth(object):
    def __init__(self, auth_url='https://accounts.google.com/o/oauth2/auth',
                 scope='https://www.googleapis.com/auth/userinfo.profile',
                 response_type='code', access_type='offline',
                 keys=None, **kwargs):
        self.auth_url = auth_url
        self.state = ''.join([random.choice(string.ascii_uppercase + string.digits)
                              for x in xrange(32)])
        if not keys:
            keys = get_keys()
        self.keys = keys
        d = dict(state=self.state, redirect_uri=self.keys['redirect_uri'],
                 client_id=self.keys['client_ID'], access_type=access_type,
                 response_type=response_type, scope=scope)
        d.update(kwargs)
        self.login_url = auth_url + '?' + urllib.urlencode(d)
        
    def complete_oauth(self, code, state,
                       auth_url='https://accounts.google.com/o/oauth2/token'):
        if state != self.state:
            return False # CSRF attack?!?
        d = dict(code=code, client_id=self.keys['client_ID'],
                 client_secret=self.keys['client_secret'],
                 redirect_uri=self.keys['redirect_uri'],
                 grant_type='authorization_code')
        r = requests.post(auth_url, data=d)
        self.access_data = r.text
        if 'access_token' not in r.text:
            raise ValueError(str(r.text))

    
