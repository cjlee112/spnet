import rest
import core
import view
import gplus
import errors
from bson import ObjectId
import json
from sessioninfo import get_session
from urllib import urlencode


class ArrayDocCollection(rest.Collection):
    def _GET(self, docID, parents):
        return self.klass.find_obj_in_parent(parents.values()[0], docID)

class InterestCollection(ArrayDocCollection):
    '/papers/PAPER/likes/PERSON REST interface for AJAX calls'
    def check_permission(self, method, personID, *args, **kwargs):
        if method == 'GET': # permitted
            return False
        try:
            if personID != get_session()['person']._id:
                return view.report_error('TRAP set_interest by different user!', 403,
                                      "You cannot change someone else's settings!")
        except (KeyError,AttributeError):
            return view.report_error('TRAP set_interest, not logged in!', 401,
                                     'You must log in to access this interface')
    def _POST(self, personID, topic, state, parents, topic2=''):
        'add or remove topic from PaperInterest depending on state'
        topic = topic or topic2 # use whichever is non-empty
        topic = core.SIG.standardize_id(topic) # must follow hashtag rules
        personID = ObjectId(personID)
        state = int(state)
        if state: # make sure topic exists
            sig = core.SIG.find_or_insert(topic)
        interest = self.set_interest(personID, topic, state, parents)
        get_session()['person'].force_reload(True) # refresh user
        return interest
    def set_interest(self, personID, topic, state, parents):
        try:
            interest = self._GET(personID, parents)
        except KeyError:
            if state:
                person = core.Person(personID)
                docData = dict(author=personID, topics=[topic],
                               authorName=person.name)
                return core.PaperInterest(docData=docData,
                                          parent=parents['paper'])
            else: # trying to rm something that doesn't exist
                raise
        if state:
            interest.add_topic(topic)
        else:
            interest.remove_topic(topic)
        return interest
    def post_json(self, interest, **kwargs):
        return json.dumps(dict(interest='very good'))
    def post_html(self, interest, **kwargs):
        'display interest change by re-displaying the paper page'
        return view.redirect(interest.parent.get_value('local_url'))


class PaperCollection(rest.Collection):
    def _search(self, searchString, searchType):
        searchString = searchString.strip()
        if not searchString:
            s = view.report_error('empty searchString', 400,
                                  'You did not provide a search string.')
            return rest.Response(s)
        # user may type "Google Search:..." into Google Search box
        if searchString.lower().startswith('arxiv:'):
            searchString = searchString[6:].strip()
            searchType = 'arxivID'
        if searchType == 'arxivID':
            return rest.Redirect('/arxiv/%s' % searchString.replace('/', '_'))
        elif searchType == 'arxiv':
            return rest.Redirect('/arxiv?' + urlencode(dict(searchString=searchString)))
        elif searchType == 'PMID':
            return rest.Redirect('/pubmed/%s' % searchString)
        elif searchType == 'pubmed':
            return rest.Redirect('/pubmed?' + urlencode(dict(searchString=searchString)))
        elif searchType == 'ncbipubmed':
            return rest.Redirect('http://www.ncbi.nlm.nih.gov/sites/entrez?'
                                 + urlencode(dict(term=searchString,
                                                  db='pubmed')))
        elif searchType == 'shortDOI':
            return rest.Redirect('/shortDOI/%s' % searchString)
        elif searchType == 'DOI':
            dpd = core.DoiPaperData(DOI=searchString, insertNew='findOrInsert')
            return rest.Redirect('/shortDOI/%s' % dpd.id)
        elif searchType == 'spnetPerson':
            return rest.Redirect('/people?' + urlencode(dict(searchString=searchString)))
        else:
            raise KeyError('unknown searchType ' + searchType)
                                 
    

class ParentCollection(rest.Collection):
    def _GET(self, docID, parents=None):
        try: # use cached query results if present
            queryResults = get_session()['queryResults']
        except (AttributeError, KeyError):
            pass
        else:
            try: # use cached docData if found for this docID
                docData = queryResults.get_doc_data(docID,
                                           self.collectionArgs['uri'])
            except KeyError: # not in query results
                pass
            else:
                return self.klass(docData=docData,
                                  insertNew='findOrInsert').parent
        return self.klass(docID, insertNew='findOrInsert').parent
    def _search(self, searchID):
        return rest.Redirect('%s/%s' % (self.collectionArgs['uri'], 
                                        searchID.replace('/', '_')))

class ArxivCollection(ParentCollection):
    def _POST(self, docID, showLatex=None):
        paper = self._GET(docID)
        if showLatex: # save on user session
            showLatex = int(showLatex)
            paper.update({'texDollars': showLatex and 1 or -1}, op='$inc')
            viewArgs = view.get_view_options()
            viewArgs.setdefault('showLatex', {})[paper] = showLatex
        return paper
    def post_html(self, paper, **kwargs):
        return self.get_html(paper, **kwargs)
    def _search(self, searchString=None, searchID=None, ipage=0,
                block_size=10, session=None):
        import arxiv
        ipage = int(ipage)
        block_size = int(block_size)
        if session is None:
            session = get_session()
        if searchID: # just get this ID
            return ParentCollection._search(self, searchID)
        if not searchString:
            s = view.report_error('empty searchString', 400,
                                  'You did not provide a search string.')
            return rest.Response(s)
        elif arxiv.is_id_string(searchString): # just get this ID
            return ParentCollection._search(self, searchString)
        try: # get from existing query results
            queryResults = session['queryResults']
            if queryResults.get_page(ipage, self.collectionArgs['uri'],
                                     searchString=searchString):
                return queryResults
        except KeyError:
            pass # no stored queryResults, so construct it
        pbl = view.PaperBlockLoader(arxiv.search_arxiv,
                                    uri=self.collectionArgs['uri'])
        queryResults = view.MultiplePages(pbl, block_size, ipage,
                                          self.collectionArgs['uri'],
                                          'arXiv.org Search Results',
                                          searchString=searchString)
        session['queryResults'] = queryResults # keep for this user
        return queryResults

class PubmedCollection(ParentCollection):
    def _search(self, searchString=None, searchID=None, ipage=0,
                block_size=20):
        import pubmed
        if not searchString:
            s = view.report_error('empty searchString', 400,
                                  'You did not provide a search string.')
            return rest.Response(s)
        ipage = int(ipage)
        block_size = int(block_size)
        try: # get from existing query results
            queryResults = get_session()['queryResults']
            if queryResults.get_page(ipage, self.collectionArgs['uri'],
                                     searchString=searchString):
                return queryResults
        except KeyError:
            pass # no stored queryResults, so construct it
        try:
            ps = pubmed.PubmedSearch(searchString, block_size)
            pbl = view.PaperBlockLoader(ps, uri=self.collectionArgs['uri'])
            queryResults = view.MultiplePages(pbl, block_size, ipage,
                                              self.collectionArgs['uri'],
                                              'Pubmed Search Results',
                                              searchString=searchString)
        except (errors.BackendFailure,KeyError):
            s = view.report_error('eutils error: ' + searchString, 502,
                                  '''Unfortunately, the NCBI eutils server
failed to perform the requested query.  
To run the <A HREF="/papers?%s">same search</A> on
NCBI Pubmed, please click here.  When you find a paper
of interest, you can copy its PMID (Pubmed ID) and
paste it in the search box on this page.''' 
                                  % urlencode(dict(searchType='ncbipubmed',
                                                   searchString=searchString)))
            return rest.Response(s)
        get_session()['queryResults'] = queryResults # keep for this user
        return queryResults
        


class PersonCollection(rest.Collection):
    def _GET(self, docID, getUpdates=False, timeframe=None, **kwargs):
        user = get_session().get('person', None)
        if user and docID == user._id:
            person = user # use cached Person object so we can mark it for refresh
        else:
            person = rest.Collection._GET(self, docID, **kwargs)
        if getUpdates:
            try:
                gpd = person.gplus
            except AttributeError:
                pass
            else: # get list of new posts
                if timeframe == 'all': # get last 10 years
                    l = gpd.update_posts(3650, recentEvents=view.recentEventsDeque)
                else:
                    l = gpd.update_posts(recentEvents=view.recentEventsDeque)
                if l: # need to update our object representation to see them
                    person = rest.Collection._GET(self, docID, **kwargs)
        return person
    def _search(self, searchString):
        if not searchString:
            raise KeyError('empty query')
        l = list(core.Person.find_obj({'name': {'$regex': searchString}}))
        if not l:
            raise KeyError('no matches')
        return l

class PersonAuthBase(rest.Collection):
    'only allow logged-in user to POST his own settings'
    def check_permission(self, method, *args, **kwargs):
        if method == 'GET': # permitted
            return False
        user = get_session().get('person', None)
        if not user:
            return view.report_error('TRAP set_interest, not logged in!', 401,
                                     'You must log in to access this interface')
        person = kwargs['parents'].values()[0]
        if person != user:
            return view.report_error('TRAP set_interest by different user!', 403,
                                     "You cannot change someone else's settings!")

class ReadingList(PersonAuthBase):
    '/people/PERSON/reading/PAPER REST interface for AJAX calls'
    def _POST(self, paperID, state, parents):
        person = parents.values()[0]
        paperID = ObjectId(paperID)
        included = paperID in person._dbDocDict.get('readingList', ())
        state = (int(state) or False) and True # convert to boolean
        if state == included: # matches current state, so nothing to do
            return 0
        elif state: # add to reading list
            person.array_append('readingList', paperID)
            result = 1
        else:
            person.array_del('readingList', paperID)
            result = -1
        person.force_reload(True) # refresh user
        return result
    def post_json(self, status, **kwargs):
        return json.dumps(dict(status=status))

class PersonTopics(PersonAuthBase):
    '/people/PERSON/topics/TOPIC REST interface for AJAX calls'
    def _POST(self, topic, field, state, parents):
        person = parents.values()[0]
        try:
            tOpt = core.TopicOptions.find_obj_in_parent(person, topic)
        except KeyError:
            tOpt = core.TopicOptions(docData={'topic':topic, field:state}, 
                                     parent=person)
        else:
            tOpt.update({field:state})
        person.force_reload(True) # refresh user
        return 1
    def post_json(self, status, **kwargs):
        return json.dumps(dict(status=status))

class PersonSubscriptions(PersonAuthBase):
    '/people/PERSON/subscriptions/PERSON REST interface for AJAX calls'
    def _POST(self, author, field, state, parents):
        person = parents.values()[0]
        author = ObjectId(author)
        try:
            sub = core.Subscription.find_obj_in_parent(person, author)
        except KeyError:
            sub = core.Subscription(docData={'author':author, field:state}, 
                                     parent=person)
        else:
            sub.update({field:state})
        person.force_reload(True) # refresh user
        return 1
    def post_json(self, status, **kwargs):
        return json.dumps(dict(status=status))

class TopicCollection(rest.Collection):
    def _search(self, stem): # return list of topics beginning with stem
        if not stem:
            return []
        return list(self.klass.find({'_id': {'$regex': '^' + stem}}))
    def search_json(self, data, **kwargs):
        return json.dumps(data)
    
def get_collections(templateDir='_templates'):
    gplusClientID = gplus.get_keys()['client_id'] # most templates need this
    templateEnv = view.get_template_env(templateDir)
    view.report_error.bind_template(templateEnv, 'error.html') # error page

    # access Papers using our object ID
    papers = PaperCollection('paper', core.Paper, templateEnv, templateDir,
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
    pubmedPapers = PubmedCollection('paper', core.PubmedPaperData,
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
    readingList = ReadingList('reading', core.Paper, templateEnv, templateDir,
                              gplusClientID=gplusClientID)
    people.reading = readingList
    personTopics = PersonTopics('topics', core.SIG, templateEnv, templateDir,
                                gplusClientID=gplusClientID)
    people.topics = personTopics
    personSubs = PersonSubscriptions('subscriptions', core.Subscription, 
                                     templateEnv, templateDir,
                                     gplusClientID=gplusClientID)
    people.subscriptions = personSubs
    topics = TopicCollection('topic', core.SIG, templateEnv, templateDir,
                             gplusClientID=gplusClientID)

    # load homepage template
    homePage = view.TemplateView(templateEnv.get_template('index.html'),
                                 gplusClientID=gplusClientID)

    # what collections to bind on the server root
    return dict(papers=papers,
                arxiv=arxivPapers,
                shortDOI=doiPapers,
                pubmed=pubmedPapers,
                people=people,
                topics=topics,
                index=homePage)
