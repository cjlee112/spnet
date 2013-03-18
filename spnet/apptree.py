import rest
import core
import view
import gplus

class ArrayDocCollection(rest.Collection):
    def _GET(self, docID, parents):
        return self.klass.find_obj_in_parent(parents.values()[0], docID)

class InterestCollection(ArrayDocCollection):
    def _POST(self, personID, sigID, state, parents):
        'add or remove SIG from PaperInterest depending on state'
        state = int(state)
        try:
            interest = self._GET(personID, parents)
        except KeyError:
            if state:
                docData = dict(author=personID, sigs=[sigID])
                return core.PaperInterest(docData=docData,
                                          parent=parents['paper'])
            else: # trying to rm something that doesn't exist
                raise
        if state:
            return interest.add_sig(sigID)
        else:
            return interest.remove_sig(sigID)

class ParentCollection(rest.Collection):
    def _GET(self, docID, parents=None):
        return self.klass(docID, insertNew='findOrInsert').parent
class DoiCollection(rest.Collection):
    def _GET(self, shortDOI, parents=None):
        return self.klass(shortDOI=shortDOI, insertNew='findOrInsert').parent

    
def get_collections(templateDir='_templates'):
    gplusClientID = gplus.get_keys()['client_ID'] # most templates need this
    templateEnv = view.get_template_env(templateDir)

    # access Papers using our object ID
    papers = rest.Collection('paper', core.Paper, templateEnv, templateDir,
                             gplusClientID=gplusClientID)
    # using arxivID
    arxivPapers = ParentCollection('paper', core.ArxivPaperData, templateEnv,
                                   templateDir, gplusClientID=gplusClientID)
    # using shortDOI
    doiPapers = DoiCollection('paper', core.DoiPaperData, templateEnv,
                              templateDir, gplusClientID=gplusClientID)
    # using pubmedID
    pubmedPapers = ParentCollection('paper', core.PubmedPaperData,
                                    templateEnv, templateDir,
                                    gplusClientID=gplusClientID)

    recs = ArrayDocCollection('rec', core.Recommendation,
                              templateEnv, templateDir,
                              gplusClientID=gplusClientID)
    papers.recs = recs # bind as subcollection

    likes = InterestCollection('like', core.PaperInterest, templateEnv,
                               templateDir, gplusClientID=gplusClientID)
    papers.likes = likes # bind as subcollection

    people = rest.Collection('person', core.Person, templateEnv, templateDir,
                             gplusClientID=gplusClientID)
    topics = rest.Collection('topic', core.Person, templateEnv, templateDir,
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
