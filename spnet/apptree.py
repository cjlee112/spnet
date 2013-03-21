import rest
import core
import view
import gplus
from bson import ObjectId
import json
import cherrypy

class ArrayDocCollection(rest.Collection):
    def _GET(self, docID, parents):
        return self.klass.find_obj_in_parent(parents.values()[0], docID)

class InterestCollection(ArrayDocCollection):
    def _POST(self, personID, topic, state, parents):
        'add or remove topic from PaperInterest depending on state'
        personID = ObjectId(personID)
        if topic[0] == '#': # don't include hash in ID
            topic = topic[1:]
        state = int(state)
        if state: # make sure topic exists
            try:
                sig = core.SIG(topic)
            except KeyError: # create a new topic
                sig = core.SIG(docData=dict(_id=topic, name='#' + topic))
        try:
            interest = self._GET(personID, parents)
        except KeyError:
            if state:
                docData = dict(author=personID, topics=[topic])
                return core.PaperInterest(docData=docData,
                                          parent=parents['paper'])
            else: # trying to rm something that doesn't exist
                raise
        if state:
            return interest.add_topic(topic)
        else:
            return interest.remove_topic(topic)
    def post_json(self, interest, **kwargs):
        return json.dumps(dict(interest='very good'))

class ParentCollection(rest.Collection):
    def _GET(self, docID, parents=None):
        return self.klass(docID, insertNew='findOrInsert').parent
    def _search(self, searchID):
        return rest.Redirect('%s/%s' % (self.collectionArgs['uri'], searchID))

class PaperBlockLoader(object):
    def __init__(self, f, klass, **kwargs):
        '''wraps function f so its results [d,...] are returned as
        [klass(docData=d, **kwargs),...]'''
        self.f = f
        self.klass = klass
        self.kwargs = kwargs
    def __call__(self, **kwargs):
        l = []
        for d in self.f(**kwargs):
            l.append(self.klass(docData=d, **self.kwargs).parent)
        return l

class ArxivCollection(ParentCollection):
    def _search(self, searchString=None, searchID=None, ipage=0,
                block_size=10, session=None):
        import arxiv
        ipage = int(ipage)
        block_size = int(block_size)
        if session is None:
            session = cherrypy.session
        if searchID: # just get this ID
            return ParentCollection._search(self, searchID)
        elif arxiv.is_id_string(searchString): # just get this ID
            return ParentCollection._search(self, searchString)
        try: # get from existing query results
            queryResults = session['queryResults']
            if queryResults.get_page(ipage, self.collectionArgs['uri'],
                                     searchString=searchString):
                return queryResults
        except KeyError:
            pass # no stored queryResults, so construct it
        pbl = PaperBlockLoader(arxiv.search_arxiv, self.klass,
                               insertNew='findOrInsert')
        queryResults = view.MultiplePages(pbl, block_size, ipage,
                                          self.collectionArgs['uri'],
                                          searchString=searchString)
        session['queryResults'] = queryResults # keep for this user
        return queryResults
        

class PersonCollection(rest.Collection):
    def _GET(self, docID, getUpdates=False, **kwargs):
        person = rest.Collection._GET(self, docID, **kwargs)
        if getUpdates:
            try:
                gpd = person.gplus
            except AttributeError:
                pass
            else:
                l = gpd.update_posts() # list of new posts
                if l: # need to update our object representation to see them
                    person = rest.Collection._GET(self, docID, **kwargs)
        return person
    
def get_collections(templateDir='_templates'):
    gplusClientID = gplus.get_keys()['client_ID'] # most templates need this
    templateEnv = view.get_template_env(templateDir)

    # access Papers using our object ID
    papers = rest.Collection('paper', core.Paper, templateEnv, templateDir,
                             gplusClientID=gplusClientID)
    # using arxivID
    arxivPapers = ArxivCollection('paper', core.ArxivPaperData, templateEnv,
                                   templateDir, gplusClientID=gplusClientID,
                             collectionArgs=dict(uri='/arxiv'))
    # using shortDOI
    doiPapers = ParentCollection('paper', core.DoiPaperData, templateEnv,
                                 templateDir, gplusClientID=gplusClientID,
                          collectionArgs=dict(uri='/shortDOI'))
    # using pubmedID
    pubmedPapers = ParentCollection('paper', core.PubmedPaperData,
                                    templateEnv, templateDir,
                                    gplusClientID=gplusClientID,
                             collectionArgs=dict(uri='/pubmed'))

    recs = ArrayDocCollection('rec', core.Recommendation,
                              templateEnv, templateDir,
                              gplusClientID=gplusClientID)
    papers.recs = recs # bind as subcollection

    likes = InterestCollection('like', core.PaperInterest, templateEnv,
                               templateDir, gplusClientID=gplusClientID)
    papers.likes = likes # bind as subcollection

    people = PersonCollection('person', core.Person, templateEnv, templateDir,
                              gplusClientID=gplusClientID)
    topics = rest.Collection('topic', core.SIG, templateEnv, templateDir,
                             gplusClientID=gplusClientID)

    # load homepage template
    homePage = view.TemplateView(templateEnv.get_template('index.html'))

    # what collections to bind on the server root
    return dict(papers=papers,
                arxiv=arxivPapers,
                shortDOI=doiPapers,
                pubmed=pubmedPapers,
                people=people,
                topics=topics,
                index=homePage)
