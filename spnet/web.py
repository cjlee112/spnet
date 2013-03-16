import cherrypy
import thread
import core, connect
from jinja2 import Environment, FileSystemLoader
import os
import glob
import sys
import twitter
import gplus
from bson.objectid import ObjectId
import urllib

def redirect(path='/', body=None, delay=0):
    'redirect browser, if desired after showing a message'
    s = '<HTML><HEAD>\n'
    s += '<meta http-equiv="Refresh" content="%d; url=%s">\n' % (delay, path)
    s += '</HEAD>\n'
    if body:
        s += '<BODY>%s</BODY>\n' % body
    s += '</HTML>\n'
    return s

def load_templates(path='_templates/*.html'):
    'return dictionary of Jinja2 templates from specified path/*.html'
    d = {}
    loader = FileSystemLoader(os.path.dirname(path))
    env = Environment(loader=loader)
    for fname in glob.glob(path):
        basename = os.path.basename(fname)
        name = basename.split('.')[0]
        d[name] = env.get_template(basename)
    return d, env

def load_template_vars(path='_templates'):
    sys.path.append(path)
    spnet_base = os.path.dirname(os.path.realpath(core.__file__))
    sys.path.append(spnet_base)
    try:
        import template_vars
        return template_vars.templates, template_vars.views
    except ImportError:
        print 'Warning: no %s/template_vars.py?' % path
    except AttributeError:
        raise ImportError('template_vars.py must define templates, views')


def render_jinja(template, **kwargs):
    'apply the template to kwargs'
    return template.render(**kwargs)

def init_template_views(templateDict, templateVars={}, templateViews={}):
    'set up views for jinja templates'
    d = {}
    for k,viewFunc in templateViews.items(): # add view functions
        funcArgs = {}
        try:
            funcArgs['template'] = templateDict[k]
        except KeyError:
            pass
        funcArgs.update(templateVars.get(k, {}))
        d[k] = (viewFunc, funcArgs)
    for k,v in templateDict.items():
        if k not in d: # use render_jinja trivial view function
            funcArgs = dict(template=v)
            funcArgs.update(templateVars.get(k, {}))
            d[k] = (render_jinja, funcArgs)
    return d

def fetch_data(dbconn, d):
    'just a dumb prototype for general-purpose obj retrieval'
    try: # get requested paper
        paperID = d['paper']
    except KeyError:
        pass
    else:
        d['paper'] = core.Paper(paperID)
    try:
        arxivID = d['arxivID']
        d['paper'] = core.ArxivPaperData(arxivID,
                                         insertNew='findOrInsert').parent
    except KeyError:
        pass
    try:
        pubmedID = d['pubmedID']
        d['paper'] = core.PubmedPaperData(pubmedID,
                                          insertNew='findOrInsert').parent
    except KeyError:
        pass
    try:
        shortDOI = d['shortDOI']
        d['paper'] = core.DoiPaperData(shortDOI=shortDOI,
                                       insertNew='findOrInsert').parent
    except KeyError:
        pass
    try: # get requested person
        personID = d['person']
    except KeyError:
        pass
    else:
        d['person'] = core.Person(personID)
    try: # get requested email
        email = d['email']
    except KeyError:
        pass
    else:
        d['email'] = core.EmailAddress(email)
    try: # get requested SIG
        sig = d['sig']
    except KeyError:
        pass
    else:
        d['sig'] = core.SIG(sig)
    try: # get requested recommendation
        recPaper = d['recPaper']
        recAuthor = d['recAuthor']
    except KeyError:
        pass
    else:
        d['rec'] = core.Recommendation((ObjectId(recPaper),
                                        ObjectId(recAuthor)))
        del d['recPaper']
        del d['recAuthor']

def people_link_list(people, maxNames=2):
    l = []
    for p in people[:maxNames]:
        l.append('<A HREF="/view?view=person&person=%s">%s</A>'
                 % (p._id, p.name))
    s = ','.join(l)
    if len(people) > maxNames:
        s += ' and %d others' (len(people) - maxNames)
    return s

class Server(object):
    def __init__(self, dbconn, views):
        self.dbconn = dbconn
        self.views = views
        self.gplus_keys = gplus.get_keys()

    def start(self):
        'start cherrypy server as background thread, retaining control of main thread'
        self.threadID = thread.start_new_thread(self.serve_forever, ())

    def serve_forever(self):
        cherrypy.quickstart(self, '/', 'cp.conf')

    def reload_views(self):
        'reload view templates from disk'
        self.views = get_views()

    def login(self, email, password):
        'check password and create session if authenticated'
        try:
            a = core.EmailAddress(email)
        except KeyError:
            return 'no such email address'
        p = a.parent
        if p.authenticate(password):
            cherrypy.session['email'] = email
            cherrypy.session['person'] = p
        else:
            return 'bad password'
        return redirect('/view?view=person&person=' + str(p._id))
    login.exposed = True

    def twitter_login(self):
        redirect_url, tokens = twitter.start_oauth('http://localhost:8000/twitter_oauth')
        cherrypy.session['twitter_request_token'] = tokens
        return redirect(redirect_url)
    twitter_login.exposed = True

    def twitter_oauth(self, oauth_token, oauth_verifier):
        t = cherrypy.session['twitter_request_token']
        auth = twitter.complete_oauth(t[0], t[1], oauth_verifier)
        p, user, api = twitter.get_auth_person(auth)
        cherrypy.session['person'] = p
        cherrypy.session['twitter_user'] = user
        cherrypy.session['twitter_api'] = api
        self.twitter_auth = auth # just for hand testing
        return 'Logged in to twitter'
    twitter_oauth.exposed = True

    def gplus_login(self):
        oauth = gplus.OAuth(keys=self.gplus_keys)
        cherrypy.session['gplus_oauth'] = oauth
        return redirect(oauth.get_authorize_url())
    gplus_login.exposed = True

    def oauth2callback(self, error=False, **kwargs):
        if error:
            return error
        oauth = cherrypy.session['gplus_oauth']
        oauth.get_credentials(**kwargs)
        self.gplus_oauth = oauth # just for hand testing
        cherrypy.session['person'] = oauth.get_person()
        return 'Logged in to Google+'
    oauth2callback.exposed = True

    def index(self):
        'just reroute to our standard index view'
        return self.view('index')
    index.exposed = True
        
    def view(self, view, **kwargs):
        'generic view method, primarily for HTML pages'
        try:
            v = self.views[view]
        except KeyError:
            cherrypy.response.status = 404
            return 'invalid request'
        l = [0, {}, {}]
        l[0:len(v)] = v
        func, funcargs, intargs = l
        # use intargs to check things like privileges before calling func
        d = funcargs.copy()
        d.update(kwargs)
        try:
            fetch_data(self.dbconn, d) # retrieve objects from DB
            s = func(kwargs=d, hasattr=hasattr, enumerate=enumerate,
                     gplusClientID=self.gplus_keys['client_ID'],
                     urlencode=urllib.urlencode, list_people=people_link_list,
                     **d) # run the requested view function
        except Exception, e:
            cherrypy.log.error('view function error', traceback=True)
            cherrypy.response.status = 500
            return 'server error'
        return s
    view.exposed = True

    def get_json(self, **kwargs):
        pass


def get_views():
    templateDict, env = load_templates()
    templateVars, templateViews = load_template_vars()
    return init_template_views(templateDict, templateVars, templateViews)

def init_data():
    views = get_views()
    dbconn = connect.init_connection()
    return dbconn, views

if __name__ == '__main__':
    print 'loading templates...'
    dbconn, views = init_data()
    s = Server(dbconn, views)
    print 'starting server...'
    s.start()
