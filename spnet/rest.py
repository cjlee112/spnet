import cherrypy
import glob
import os.path
from base import IdString
import view

def request_tuple():
    accept = cherrypy.request.headers['Accept']
    if 'text/html' in accept:
        mimeType = 'html'
    if 'application/json' in accept or accept == '*/*':
        mimeType = 'json'
    return cherrypy.request.method, mimeType

class Redirect(object):
    '_GET etc. methods can return this to force redirection to a URL'
    def __init__(self, url):
        self.url = url
    def __call__(self):
        return view.redirect(self.url)


class Collection(object):
    '''subclass this by adding the following kinds of methods:

    1. HTTP verbs, e.g. GET, POST, DELETE, as follows
    _POST(self, docID, **kwargs): create the specified document.
    _search(self, **kwargs): search the collection based on kwargs.

    2. representation generators for a specific verb and mimeType, e.g.
    get_html(self, doc, **kwargs): for a GET request,
    return HTML representation of the doc object.
    This will typically be a renderer of a Jinja2 template.
    '''
    def __init__(self, name, klass, templateEnv=None, templateDir='_templates',
                 docArgs=None, collectionArgs=None, **templateArgs):
        self.name = name
        self.klass = klass
        if docArgs is None:
            docArgs = {}
        self.docArgs = docArgs
        self.collectionArgs = collectionArgs
        if templateEnv: # load our template files
            self.bind_templates(templateEnv, templateDir, **templateArgs)

    def default(self, docID=None, *args, **kwargs):
        'process all requests for this collection'
        try:
            method, mimeType = request_tuple()
            if docID: # a specific document from this collection
                docID = IdString(docID) # implements proper cmp() vs. ObjectId
                if not args: # perform the request
                    return self._request(method, mimeType, docID, **kwargs)
                else: # pass request on to subcollection
                    try:
                        subcoll = getattr(self, args[0])
                    except AttributeError:
                        return view.report_error('no such subcollection: %s.%s'
                                                 % (self.name, args[0]), 404)
                    try:
                        parents = kwargs['parents'].copy()
                    except KeyError:
                        parents = {}
                    try:
                        parents[self.name] = self._GET(docID, parents=parents)
                    except KeyError:
                        return view.report_error('invalid ID: %s' % docID, 404,
                                                 """Sorry, the data ID %s that
    you requested does not exist in the database.
    Please check whether you have the correct ID.""" % docID)
                    kwargs['parents'] = parents # pass dict of parents
                    return subcoll.default(*args[1:], **kwargs)
            elif method == 'GET': # search the collection
                return self._request('search', mimeType, **kwargs)
            else:
                return view.report_error('REST does not permit collection-%s' 
                                         % method, 405)
        except Exception:
            return view.report_error('REST collection error', 500)
    default.exposed = True

    def _request(self, method, mimeType, *args, **kwargs):
        'dispatch to proper handler method, or return appropriate error'
        try: # do we support this method?
            action = getattr(self, '_' + method)
        except AttributeError:
            return view.report_error('%s objects do not allow %s' 
                                     % (self.name, method), 405)
        try: # execute the request
            o = action(*args, **kwargs)
        except KeyError:
            return view.report_error('Not found: %s: args=%s, kwargs=%s'
                   % (self.name, str(args), str(kwargs)), status=404,
                                     webMsg="""Sorry, the data ID %s that
you requested does not exist in the database.
Please check whether you have the correct ID.""" % args[0])
        if isinstance(o, Redirect):
            return o() # send the redirect
        try: # do we support this mimeType?
            viewFunc = getattr(self, method.lower() + '_' + mimeType)
        except AttributeError:
            return view.report_error('%s objects cannot return %s' 
                                     % (self.name, mimeType), 406)
        try:
            return viewFunc(o, **kwargs)
        except Exception:
            return view.report_error('view function error', 500)

    def _GET(self, docID, parents={}, **kwargs):
        'default GET method'
        kwargs.update(self.docArgs)
        if not parents: # works with documents with unique ID
            return self.klass(docID, **kwargs)
        elif len(parents) == 1: # works with ArrayDocument
            return self.klass((parents.values()[0]._id, docID), **kwargs)
        else: # multiple parents
            return self.klass(docID, parents=parents, **kwargs)
            
    def bind_templates(self, env, dirpath, **kwargs):
        '''load template files of the form get_paper.html, bind as
        attrs of the form get_html'''
        for fname in glob.glob(os.path.join(dirpath,
                                            '*_%s.html' % self.name)):
            basename = os.path.basename(fname)
            template = env.get_template(basename)
            methodName = basename.split('_')[0] + '_html'
            v = view.TemplateView(template, self.name, **kwargs)
            setattr(self, methodName, v)
            

    
