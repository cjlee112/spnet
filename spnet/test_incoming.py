import incoming
import core
from datetime import datetime

post1 = dict(
    id='temporaryPost',
    content='''this is my post.
It talks about two papers including  arXiv:0910.4103
#spnetwork arXiv:0804.2682 #gt  arXiv:0910.4103 arXiv:0804.2682 #gt''',
    user='114744049040264263224',
    title='Such an interesting Post!',
)

def submit_post(d=post1):
    it = incoming.find_or_insert_posts([d], None, 
        lambda x:core.GplusPersonData(x, insertNew='findOrInsert').parent,
        lambda x:x['content'], lambda x:x['user'], lambda x:0,
        lambda x:x['id'], lambda x:datetime.now(),
        lambda x:False, 'gplusPost')
    return list(it)

def test1():
    l = submit_post(post1) # create test post
    assert len(l) == 1
    post = l[0]
    assert post.parent.arxiv.id == '0804.2682'
    assert len(post.papers) == 1
    assert post.papers[0].arxiv.id == '0910.4103'
    assert len(post.papers[0].citations) == 1
    assert post.papers[0].citations[0].title == 'Such an interesting Post!'
    # finally clean up by deleting our test post
    post.papers[0].citations[0].delete()
    post.delete()
    print 'tests passed'
