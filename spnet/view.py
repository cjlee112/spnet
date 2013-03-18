import cherrypy
from jinja2 import Environment, FileSystemLoader
import urllib

def people_link_list(people, maxNames=2):
    l = []
    for p in people[:maxNames]:
        l.append('<A HREF="/view?view=person&person=%s">%s</A>'
                 % (p._id, p.name))
    s = ','.join(l)
    if len(people) > maxNames:
        s += ' and %d others' (len(people) - maxNames)
    return s


#################################################################
# template loading and rendering

def get_template_env(dirpath):
    loader = FileSystemLoader(dirpath)
    return Environment(loader=loader)

class TemplateView(object):
    def __init__(self, template, name, **kwargs):
        self.template = template
        self.kwargs = kwargs
        self.name = name

    def __call__(self, doc, **kwargs):
        f = self.template.render
        kwargs.update(self.kwargs)
        kwargs[self.name] = doc
        try:
            return f(kwargs=kwargs, hasattr=hasattr, enumerate=enumerate,
                     urlencode=urllib.urlencode, list_people=people_link_list,
                     getattr=getattr, 
                     user=cherrypy.session.get('person', None),
                     **kwargs) # apply template
        except Exception, e:
            cherrypy.log.error('view function error', traceback=True)
            cherrypy.response.status = 500
            return 'server error'
