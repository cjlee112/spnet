import core
import connect
import pickle
import random
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
    authors = {}
    for d in core.Person.find(fields=dict(name=1)):
        authors[d['name']] = d['_id']
    papersToUpdate = []
    n = 0
    for paper in core.Paper.find(fields=dict(authors=1), idOnly=False):
        if isinstance(paper['authors'][0], ObjectId):
            continue # already saved as Person records
        paperID = paper['_id']
        papersToUpdate.append(paperID)
        for a in paper['authors']:
            if a not in authors: # create new person record
                p = core.Person(docData=dict(name=a))
                authors[a] = p._id
                n += 1
    print 'Saved %d new author records...' % n
    print 'Updating %d paper records...' % len(papersToUpdate)
    for paperID in papersToUpdate:
        paper = core.Paper(paperID)
        authorIDs = [authors[a] for a in paper._dbDocDict['authors']]
        paper.update(dict(authors=authorIDs))
    return n

def add_random_recs():
    'for each person, add one rec to a randomly selected paper'
    papers = list(core.Paper.find()) # get all paperID
    for personID in core.Person.find():
        paperID = random.choice(papers)
        core.Recommendation(docData=dict(author=personID,
                                         text='I like this paper'),
                            parent=paperID)

def new_email(email, name):
    'add an email address to the specified name'
    l = list(core.Person.find(dict(name=name)))
    if l:
        return core.EmailAddress(docData=dict(address=email), parent=l[0])
    else:
        raise ValueError('Person "%s" not found' % name)

def set_password(password, name):
    'set password on the specified name'
    l = list(core.Person.find_obj(dict(name=name)))
    if l:
        l[0].set_password(password)
    else:
        raise ValueError('Person "%s" not found' % name)

def add_dummy_login(email='me@u.edu', password='testme', query={}):
    for person in core.Person.find_obj(query):
        print 'Adding login for %s: %s, %s' % (person.name, email, password)
        person.set_password(password)
        return core.EmailAddress(docData=dict(address=email), parent=person)
    raise ValueError('No person matching query: ' + str(query))

def add_paper_sigs(field='arxiv-topic-area'):
    'add SIGs based on paper field strings, and tag papers accordingly'
    sigs = {}
    n = 0
    ntag = 0
    for sig in core.SIG.find_obj():
        sigs[sig.name] = sig
    for paper in core.Paper.find_obj():
        try:
            name = paper._dbDocDict[field]
        except KeyError:
            continue # paper has no field name, so nothing to do 
        try:
            sig = sigs[name]
        except KeyError:
            sig = core.SIG(docData=dict(name=name))
            sigs[name] = sig
            n += 1
        if sig not in paper.sigs:
            paper.array_append('sigs', sig)
            ntag += 1
    return n, ntag


if __name__ == '__main__':
    import sys
    dbconn = connect.init_connection()
    if len(sys.argv) > 1 and sys.argv[1] == '--drop':
        dbconn._conn.drop_database('spnet')
        print 'Erased existing spnet database.'
    with open(cache_filename) as cache_file:
        papers = pickle.load(cache_file)
    print 'Loading %d papers...' % len(papers)
    n = load_papers(papers)
    print 'Loaded %d new papers.' % n
    n = update_person_db()
    if n:
        add_dummy_login()
        print 'Adding random recommendations...'
        add_random_recs()
        n, ntag = add_paper_sigs()
        print 'Added %d SIGs, tagged %d papers.' % (n, ntag)
