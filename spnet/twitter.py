try:
    import tweepy
except ImportError:
    pass
import urllib2
#import core

###############################################################
# OAuth functions

def read_keyfile(keyfile='../twitter/keys'):
    'read our application keys for twitter'
    d = {}
    with open(keyfile, 'rU') as ifile:
        for line in ifile:
            line = line.strip()
            t = line.split('\t')
            d[t[0]] = t[1]
    return d

def get_auth(callback=None, keyDict=read_keyfile(), **kwargs):
    'create an authentication object, using optional kwargs'
    d = keyDict.copy()
    d.update(kwargs) # allow kwargs to override stored settings
    auth = tweepy.OAuthHandler(d['consumer_key'], d['consumer_secret'],
                               callback)
    if d.get('access_token', False):
        auth.set_access_token(d['access_token'], d['access_token_secret'])
    return auth

def start_oauth(callback_url):
    'get URL for user to login to twitter'
    auth = get_auth(callback=callback_url, access_token=None)
    redirect_url = auth.get_authorization_url()
    return redirect_url, (auth.request_token.key, auth.request_token.secret)

def complete_oauth(request_token, request_token_secret, oauth_verifier):
    'get access token using info passed on by twitter'
    auth = get_auth(access_token=None)
    auth.set_request_token(request_token, request_token_secret)
    auth.get_access_token(oauth_verifier)
    return auth

######################################################################
# search functions

def get_recent(query, api=None, **kwargs):
    if api is None:
        api = tweepy.API(get_auth())
    for tweet in tweepy.Cursor(api.search, q=query, count=100,
                               result_type='recent',
                               include_entities=True, **kwargs).items():
        yield tweet


class HeadRequest(urllib2.Request):
    def get_method(self): return 'HEAD'
 
def get_real_url(url):
    res = urllib2.urlopen(HeadRequest(url))
    return res.geturl()

def extract_arxiv_id(tweet, arxivFormats=('abs', 'pdf', 'other')):
    'get arxiv ID from URLs in tweet'
    for u in tweet.entities.get('urls', ()):
        if u.get('expanded_url', '') == 'http://arxiv.org':
            continue
        try:
            url = get_real_url(u['url'])
        except KeyError:
            continue
        l = url.split('/')
        if url.startswith('http://arxiv.org/') and len(l) > 4 and \
               l[3] in arxivFormats:
            arxivID = l[4].split('v')[0]
            yield arxivID
    
def extract_pubmed_id(tweet):
    'get PMID from both #pubmed12345 hashtags and URLs'
    for hdict in tweet.entities.get('hashtags', ()):
        hashtag = hdict.get('text', '')
        if hashtag.startswith('pubmed') and hashtag[6:].isdigit():
            yield hashtag[6:]
    for u in tweet.entities.get('urls', ()):
        if u.get('expanded_url', '') == 'http://www.ncbi.nlm.nih.gov':
            continue
        try:
            url = get_real_url(u['url'])
            print u['url'], '-->', url
        except KeyError:
            continue
        l = url.split('/')
        if url.startswith('http://www.ncbi.nlm.nih.gov/'):
            for i,word in enumerate(l[3:-1]):
                if word == 'pubmed':
                    pubmedID = l[i + 4]
                    yield pubmedID
                    break

####################################################################
# user functions

def get_auth_user(auth, api):
    username = auth.get_username()
    return api.get_user(username)
    
def get_person(u, access_token):
    try:
        p = core.Person.find_obj({'twitter.id_str':u.id_str}).next()
    except StopIteration: # no matching record
        twitterData = dict(id_str=u.id_str,screen_name=u.screen_name,
                           created_at=u.created_at,
                           access_token=access_token.key,
                           access_secret=access_token.secret)
        p = core.Person(docData=dict(name=u.name, twitter=twitterData))
    return p

def get_auth_person(auth):
    'get Person record (or create one) for authenticated user'
    api = tweepy.API(auth)
    user = get_auth_user(auth, api)
    p = get_person(user, auth.access_token)
    return p, user, api

    

    
