import core
import connect
import pickle

cache_filename = 'arxiv.pickle'

def drop_paper_db():
    core.Paper.coll.database.drop_collection(core.Paper.coll)

def load_papers(papers):
    n = 0
    for paper in papers:
        paper['_id'] = paperID = 'arxiv:' + paper['id'].split('/')[-1]
        if not list(core.Paper.find(dict(_id=paperID), limit=1)):
            p = core.Paper(docData=paper) # creates new record in DB
            n += 1
    return n

if __name__ == '__main__':
    connect.init_connection()
    with open(cache_filename) as cache_file:
        papers = pickle.load(cache_file)
    print 'Loading %d papers...' % len(papers)
    n = load_papers(papers)
    print 'Loaded %d new papers.' % n
