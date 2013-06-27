import cherrypy

class SessionInfo(object):
    def __call__(self):
        try:
            return cherrypy.session
        except AttributeError:
            if hasattr(self, 'sessionDict'):
                return self.sessionDict
            raise

get_session = SessionInfo()
