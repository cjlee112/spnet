import core

def find_people_topics():
    'construct dict of person:topics from Recs, Posts, PaperInterests'
    people = {}
    for r in core.Recommendation.find_obj():
        authorID = r._dbDocDict['author']
        topics = r._dbDocDict.get('sigs', ())
        try:
            people[authorID].update(topics)
        except KeyError:
            people[authorID] = set(topics)
    for r in core.Post.find_obj():
        authorID = r._dbDocDict['author']
        topics = r._dbDocDict.get('sigs', ())
        try:
            people[authorID].update(topics)
        except KeyError:
            people[authorID] = set(topics)
    for r in core.PaperInterest.find_obj():
        authorID = r._dbDocDict['author']
        topics = r._dbDocDict['topics']
        try:
            people[authorID].update(topics)
        except KeyError:
            people[authorID] = set(topics)
    return people

def insert_people_topics(peopleTopics):
    'add topics to each Person.topics array'
    for personID,topics in peopleTopics.items():
        core.Person.coll.update({'_id':personID},
                                {'$addToSet': {'topics': {'$each':list(topics)}}})

def get_people_subs():
    topics = {}
    subs = {}
    for d in core.Person.find({}, {'topics':1, 'topicOptions':1, 'subscriptions':1}):
        personID = d['_id']
        hideSet = set([dd['topic'] for dd in d.get('topicOptions', ())
                       if dd.get('fromOthers', 0) == 'hide'])
        for topic in d.get('topics', ()): # index topics this person wants to get
            if topic in hideSet: # user doesn't want all recs on this topic
                continue
            try:
                topics[topic].append(personID)
            except KeyError:
                topics[topic] = [personID]
        for sub in d.get('subscriptions', ()): # index people this person wants to get
            author = sub['author']
            try:
                subs[author].append(personID)
            except KeyError:
                subs[author] = [personID]
    return topics, subs



def deliver_recs(topics, subs):
    for d in core.Paper.find({'recommendations': {'$exists':True}}, 
                             {'recommendations':1}):
        paperID = d['_id']
        for r in d['recommendations']:
            author = r['author']
            sigs = r.get('sigs', ())
            for personID in subs.get(author, ()): # deliver to subscribers
                core.Person.coll.update({'_id':personID},
                    {'$addToSet': {'received': 
                                   {'paper':paperID, 'from':author, 'topics':sigs}}})
            for topic in sigs:
                for personID in topics.get(topic, ()): # deliver to subscribers
                    if personID == author: # don't deliver back to author!
                        continue
                    core.Person.coll.update({'_id':personID},
                        {'$addToSet': {'received': 
                                  {'paper':paperID, 'from':author, 'topics':sigs}}})
