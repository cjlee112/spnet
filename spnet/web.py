import cherrypy
import thread
import core, connect
from jinja2 import Template
import os
import glob
import sys

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
    for fname in glob.glob(path):
        ifile = open(fname, 'rU')
        name = os.path.basename(fname).split('.')[0]
        d[name] = Template(ifile.read())
        ifile.close()
    return d

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
        recAuthor = ObjectId(d['recAuthor'])
    except KeyError:
        pass
    else:
        d['rec'] = core.Recommendation((recPaper, recAuthor))
        del d['recPaper']
        del d['recAuthor']

class Server(object):
    def __init__(self, dbconn, views):
        self.dbconn = dbconn
        self.views = views

    def start(self):
        'start cherrypy server as background thread, retaining control of main thread'
        self.threadID = thread.start_new_thread(self.serve_forever, ())

    def serve_forever(self):
        cherrypy.quickstart(self, '/', 'cp.conf')

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
            s = func(**d) # run the requested view function
        except Exception, e:
            cherrypy.log.error('view function error', traceback=True)
            cherrypy.response.status = 500
            return 'server error'
        return s
    view.exposed = True

    def get_json(self, **kwargs):
        pass
        

if __name__ == '__main__':
    print 'loading templates...'
    templateDict = load_templates()
    templateVars, templateViews = load_template_vars()
    views = init_template_views(templateDict, templateVars, templateViews)
    dbconn = connect.init_connection()
    s = Server(dbconn, views)
    print 'starting server...'
    s.serve_forever()
