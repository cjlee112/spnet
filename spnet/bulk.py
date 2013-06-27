import core

def get_people_topics():
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
