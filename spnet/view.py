import cherrypy
from jinja2 import Environment, FileSystemLoader
import urllib
from datetime import datetime, timedelta
import collections

def redirect(path='/', body=None, delay=0):
    'redirect browser, if desired after showing a message'
    s = '<HTML><HEAD>\n'
    s += '<meta http-equiv="Refresh" content="%d; url=%s">\n' % (delay, path)
    s += '</HEAD>\n'
    if body:
        s += '<BODY>%s</BODY>\n' % body
    s += '</HTML>\n'
    return s

def people_link_list(people, maxNames=2):
    l = []
    for p in people[:maxNames]:
        l.append('<A HREF="%s">%s</A>' % (p.get_local_url(), p.name))
    s = ', '.join(l)
    if len(people) > maxNames:
        s += ' and %d others' % (len(people) - maxNames)
    return s

timeUnits = (('seconds', timedelta(minutes=1), lambda t:int(t.seconds)),
             ('minutes', timedelta(hours=1), lambda t:int(t.seconds / 60)),
             ('hours', timedelta(1), lambda t:int(t.seconds / 3600)),
             ('days', timedelta(7), lambda t:t.days))

monthStrings = ('Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'Jun.', 'Jul.',
                'Aug.', 'Sep.', 'Oct.', 'Nov.', 'Dec.')

def display_datetime(dt):
    'get string that sidesteps timezone issues thus: 27 minutes ago'
    def singularize(i, s):
        if i == 1:
            return s[:-1]
        return s
    diff = datetime.utcnow() - dt
    for unit, td, f in timeUnits:
        if diff < td:
            n = f(diff)
            return '%d %s ago' % (n, singularize(n, unit))
    return '%s %d, %d' % (monthStrings[dt.month - 1], dt.day, dt.year)

def timesort(stuff, cmpfunc=lambda x,y:cmp(x.published,y.published),
             reverse=True, **kwargs):
    'sort items by timestamp, most recent first by default'
    l = list(stuff)
    l.sort(cmpfunc, reverse=reverse, **kwargs)
    return l

def map_helper(it, attr=None, **kwargs):
    '''jinja2 lacks list-comprehensions, map, lambda, etc... so we need
    some help with those kind of operations'''
    if attr:
        f = lambda x: getattr(x, attr)
    return map(f, it)

################################################################
# error reporting template

class ErrorPage(object):
    def __call__(self, logMsg='Trapped exception', status=404,
                 webMsg="""Drat!  Something went wrong during
the rendering of this page.  The error has been logged, to aid debugging.
If this problem is inconveniencing you, please add your information
on how to reproduce this error, on 
<A HREF="https://github.com/cjlee112/spnet/issues">our issue tracker</A>.
That will accelerate efforts to track down and squish
this bug.""", traceback=True):
        'log traceback if desired, set status code'
        cherrypy.log.error(logMsg, traceback=traceback)
        cherrypy.response.status = status
        try:
            tv = self.templateView
        except AttributeError:
            return webMsg # no template, so just return error string as is
        else: # apply our template to the error message
            return tv(webMsg)
    def bind_template(self, env, templateName, name='errorMessage'):
        template = env.get_template(templateName)
        self.templateView = TemplateView(template, name)

report_error = ErrorPage() # our standard error reporting function

#################################################################
# template loading and rendering

def get_template_env(dirpath):
    loader = FileSystemLoader(dirpath)
    return Environment(loader=loader)

class TemplateView(object):
    exposed = True
    def __init__(self, template, name=None, **kwargs):
        self.template = template
        self.kwargs = kwargs
        self.name = name

    def __call__(self, doc=None, **kwargs):
        f = self.template.render
        kwargs.update(self.kwargs)
        try:
            kwargs.update(cherrypy.session['viewArgs'])
        except KeyError:
            pass
        if doc is not None:
            kwargs[self.name] = doc
        try:
            user = cherrypy.session['person']
        except KeyError:
            user = cherrypy.session['person'] = None
        if getattr(user, '_forceReload', False):
            user = user.__class__(user._id) # reload from DB
            cherrypy.session['person'] = user # save on session
        return f(kwargs=kwargs, hasattr=hasattr, enumerate=enumerate,
                 urlencode=urllib.urlencode, list_people=people_link_list,
                 getattr=getattr, str=str, map=map_helper, user=user,
                 display_datetime=display_datetime, timesort=timesort,
                 recentEvents=recentEventsDeque, **kwargs) # apply template

def get_view_options():
    'get dict of session kwargs passed to view templates'
    try:
        return cherrypy.session['viewArgs']
    except KeyError:
        d = {}
        cherrypy.session['viewArgs'] = d
        return d

##################################################################

class MultiplePages(object):
    'Interface for paging through result sets'
    def __init__(self, f, block_size, ipage, uri, title='Search Results', 
                 **queryArgs):
        self.f = f
        self.pages = []
        self.block_size = block_size
        self.queryArgs = queryArgs
        self.uri = uri
        self.title = title
        self.results = () # default: no results
        self.get_page(ipage, uri, **queryArgs)
    def get_page(self, ipage, uri, **queryArgs):
        '''returns True if we can serve the specified query;
        otherwise False.  Raises StopIteration'''
        if self.uri != uri or queryArgs != self.queryArgs:
            return False # a different search!
        self.error = '' # default: no error
        while ipage >= len(self.pages):
            l = self.f(start=ipage * self.block_size,
                       block_size=self.block_size, **self.queryArgs)
            if l:
                self.pages.append(l)
            if len(l) < self.block_size:
                self.totalPages = len(self.pages)
                if not self.pages:
                    self.error = 'No results matched your query.'
                    return True # report these search results
                if not l:
                    self.error = 'There are no more results matching your query.'
                ipage = len(self.pages) - 1 # last page
                break
        self.ipage = ipage
        self.start = ipage * self.block_size + 1
        self.results = self.pages[ipage]
        self.end = self.start + len(self.results) - 1
        return True # report these search results
    def get_page_url(self, step=1):
        'get URL for page incremented by step'
        return self.uri + '?' + \
               urllib.urlencode(dict(ipage=self.ipage + step,
                                     **self.queryArgs))
    def get_doc_data(self, docID, uri=None):
        'return docData dict for specified ID and collection URI'
        if uri and uri != self.uri:
            raise KeyError('request from different URI: ' + uri)
        return self.f.get_doc_data(docID)

class SimpleObj(object):
    'wrapper looks like a Paper object, for storing search results'
    def __init__(self, docData, **kwargs):
        self.__dict__.update(docData)
        self.__dict__.update(kwargs)
        self.parent = self
    def get_value(self, val='spnet_url'):
        f = getattr(self, 'get_' + val)
        return f()
    def get_local_url(self):
        return self.uri + '/' + self.id

class PaperBlockLoader(object):
    'callable that loads one list of dicts into paper objects'
    def __init__(self, f, klass=SimpleObj, **kwargs):
        '''wraps function f so its results [d,...] are returned as
        [klass(docData=d, **kwargs),...]'''
        self.f = f
        self.klass = klass
        self.kwargs = kwargs
        self.docs = {}
    def __call__(self, **kwargs):
        l = []
        for d in self.f(**kwargs):
            l.append(self.klass(docData=d, **self.kwargs).parent)
            try:
                docID = d['id']
                self.docs[docID] = d
            except KeyError:
                pass
        return l
    def get_doc_data(self, docID):
        'return docData dict for specified ID'
        return self.docs[docID]


#######################################################################
# recent events deque

recentEventsDeque = collections.deque(maxlen=20)

def load_recent_events(paperClass, topicClass, dq=recentEventsDeque,
                       limit=20):
    'obtain list of recent events stored in our database'
    l = []
    for paper in paperClass.find_obj(sortKeys={'recommendations.published':-1},
                                     limit=limit):
        for r in getattr(paper, 'recommendations', ()):
            l.append(r)
    for paper in paperClass.find_obj(sortKeys={'posts.published':-1},
                                     limit=limit):
        for r in getattr(paper, 'posts', ()):
            l.append(r)
    for paper in paperClass.find_obj(sortKeys={'replies.published':-1},
                                     limit=limit):
        for r in getattr(paper, 'replies', ()):
            l.append(r)
    for topic in topicClass.find_obj(sortKeys={'published':-1}, limit=limit):
        l.append(topic)
    l.sort(lambda x,y:cmp(x.published, y.published)) # oldest first
    for r in l:
        dq.appendleft(r)
        
        
def poll_recent_events(paperClass, topicClass, interval=300):
    'update recentEventsDeque every interval; run in separate thread'
    import time
    import gc
    dq = collections.deque(maxlen=20)
    while True:
        load_recent_events(paperClass, topicClass, dq)
        recentEventsDeque.clear()
        recentEventsDeque.extend(dq)
        dq.clear()
        gc.collect() # frequent GC seems to keep RSS from growing unsustainably
        time.sleep(interval)
