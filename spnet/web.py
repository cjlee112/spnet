import cherrypy
import thread
import core, connect
import twitter
import gplus
import apptree

def redirect(path='/', body=None, delay=0):
    'redirect browser, if desired after showing a message'
    s = '<HTML><HEAD>\n'
    s += '<meta http-equiv="Refresh" content="%d; url=%s">\n' % (delay, path)
    s += '</HEAD>\n'
    if body:
        s += '<BODY>%s</BODY>\n' % body
    s += '</HTML>\n'
    return s

class Server(object):
    def __init__(self, dbconn=None, colls=None):
        if not dbconn:
            dbconn = connect.init_connection()
        self.dbconn = dbconn
        self.gplus_keys = gplus.get_keys()
        self.reload_views(colls)

    def start(self):
        'start cherrypy server as background thread, retaining control of main thread'
        self.threadID = thread.start_new_thread(self.serve_forever, ())

    def serve_forever(self):
        cherrypy.quickstart(self, '/', 'cp.conf')

    def reload_views(self, colls=None):
        'reload view templates from disk'
        if not colls:
            colls = apptree.get_collections()
        for attr, c in colls.items(): # bind collections to server root
            setattr(self, attr, c)

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
        return redirect('/')
    oauth2callback.exposed = True


if __name__ == '__main__':
    s = Server()
    print 'starting server...'
    s.start()
