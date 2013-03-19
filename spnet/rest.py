import cherrypy
import glob
import os.path
from base import IdString

def request_tuple():
    accept = cherrypy.request.headers['Accept']
    if 'text/html' in accept:
        mimeType = 'html'
    if 'application/json' in accept or accept == '*/*':
        mimeType = 'json'
    return cherrypy.request.method, mimeType

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
                 docArgs={}, **templateArgs):
        self.name = name
        self.klass = klass
        self.docArgs = docArgs
        if templateEnv: # load our template files
            self.bind_templates(templateEnv, templateDir, **templateArgs)

    def default(self, docID=None, *args, **kwargs):
        'process all requests for this collection'
        try:
            method, mimeType = request_tuple()
        except KeyError: # purely for testing / debugging
            method, mimeType = ('GET', 'html')
        if docID: # a specific document from this collection
            docID = IdString(docID) # implements proper cmp() vs. ObjectId
            if not args: # perform the request
                return self._request(method, mimeType, docID, **kwargs)
            else: # pass request on to subcollection
                try:
                    subcoll = getattr(self, args[0])
                except AttributeError:
                    cherrypy.response.status = 404
                    return 'no such subcollection: %s.%s' \
                           % (self.name, args[0])
                try:
                    parents = kwargs['parents'].copy()
                except KeyError:
                    parents = {}
                parents[self.name] = self._GET(docID, parents=parents)
                kwargs['parents'] = parents # pass dict of parents
                return subcoll.default(*args[1:], **kwargs)
        elif method == 'GET': # search the collection
            return self._request('search', mimeType, **kwargs)
        else:
            cherrypy.response.status = 405
            return 'REST does not permit collection-%s' % method
    default.exposed = True

    def _request(self, method, mimeType, *args, **kwargs):
        'dispatch to proper handler method, or return appropriate error'
        try: # do we support this method?
            action = getattr(self, '_' + method)
        except AttributeError:
            cherrypy.response.status = 405
            return '%s objects do not allow %s' % (self.name, method)
        try: # do we support this mimeType?
            view = getattr(self, method.lower() + '_' + mimeType)
        except AttributeError:
            cherrypy.response.status = 406
            return '%s objects cannot return %s' % (self.name,
                                                    mimeType)
        try: # execute the request
            o = action(*args, **kwargs)
        except KeyError:
            cherrypy.response.status = 404
            return 'Not found: %s: args=%s, kwargs=%s' \
                   % (self.name, str(args), str(kwargs))
        return view(o, **kwargs)

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
        import view
        for fname in glob.glob(os.path.join(dirpath,
                                            '*_%s.html' % self.name)):
            basename = os.path.basename(fname)
            template = env.get_template(basename)
            methodName = basename.split('_')[0] + '_html'
            v = view.TemplateView(template, self.name, **kwargs)
            setattr(self, methodName, v)
            

    
