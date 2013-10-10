import incoming
import core
from datetime import datetime

post1 = dict(
    id='temporaryPost',
    content='''this is my post.
It talks about three papers including  arXiv:0910.4103
and http://arxiv.org/abs/1310.2239
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
    assert len(post.citations) == 2
    ids = [c.parent.arxiv.id for c in post.citations]
    assert '0910.4103' in ids and '1310.2239' in ids
    assert len(post.citations[0].parent.citations) == 1
    assert post.citations[0].title == 'Such an interesting Post!'
    assert len(post.citations[1].parent.citations) == 1
    # finally clean up by deleting our test post
    post.citations[0].delete()
    post.citations[1].delete()
    post.delete()
    print 'tests passed'

def test_arxiv_versions(arxivIDs=('1108.1172', '1108.1172v3')):
    l = [core.ArxivPaperData(s, insertNew='findOrInsert').parent
         for s in arxivIDs]
    for p in l[1:]:
        if p._id != l[0]._id:
            raise AssertionError('arxiv versions map to different Paper records!')
    print 'tests passed.'

def test_arxiv_versions2(arxivIDs=('math.HO_9404236', 'math.HO_9404236')):
    test_arxiv_versions(arxivIDs)
