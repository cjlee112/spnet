import core
import connect
import pickle
from bson.objectid import ObjectId

cache_filename = 'arxiv.pickle'

def drop_paper_db():
    'empty the paper database table'
    core.Paper.coll.database.drop_collection(core.Paper.coll)
def drop_person_db():
    'empty the person database table'
    core.Person.coll.database.drop_collection(core.Person.coll)

def load_papers(papers):
    'insert the set of paper dictionaries into the database'
    n = 0
    for paper in papers:
        paper['_id'] = paperID = 'arxiv:' + paper['id'].split('/')[-1]
        if not list(core.Paper.find(dict(_id=paperID), limit=1)):
            p = core.Paper(docData=paper) # creates new record in DB
            n += 1
    return n

def update_person_db():
    'use Paper database authors to construct Person db'
    authors = set()
    papersToUpdate = []
    for paper in core.Paper.find(fields=dict(authors=1), idOnly=False):
        if isinstance(paper['authors'][0], ObjectId):
            continue # already saved as Person records
        paperID = paper['_id']
        papersToUpdate.append(paperID)
        for a in paper['authors']:
            authors.add(a)
    people = {}
    print 'Saving %d new author records...' % len(authors)
    for a in authors:
        p = core.Person(docData=dict(name=a))
        people[a] = p._id
    print 'Updating %d paper records...' % len(papersToUpdate)
    for paperID in papersToUpdate:
        paper = core.Paper(paperID)
        authorIDs = [people[a] for a in paper._dbDocDict['authors']]
        paper.update(dict(authors=authorIDs))

if __name__ == '__main__':
    connect.init_connection()
    with open(cache_filename) as cache_file:
        papers = pickle.load(cache_file)
    print 'Loading %d papers...' % len(papers)
    n = load_papers(papers)
    print 'Loaded %d new papers.' % n
