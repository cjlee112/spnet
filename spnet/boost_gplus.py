import core

def find_user_posts(**kwargs):
    'query gplus for posts from all users with posts in our db'
    oldposts = set(core.Post.find())
    l = []
    gplusUsers = set([d['actor']['id'] for d in  core.Post.find(fields={'posts.actor.id':1})])
    for gplusID in gplusUsers:
        gpd = core.GplusPersonData(gplusID)
        print 'retrieving', gpd.displayName, gplusID
        for post in gpd.update_posts(**kwargs):
            if post.id not in oldposts:
                print '  new post', post.id
                l.append(post)
    return l
