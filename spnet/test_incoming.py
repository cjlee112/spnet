import connect
import incoming
import core
from datetime import datetime

def setup():
    'get a db connection prior to running tests'
    connect.init_connection()


post1 = dict(
    id='temporaryPost',
    content='''this is my post.
It talks about three papers including  arXiv:0910.4103
and http://arxiv.org/abs/1310.2239
#spnetwork arXiv:0804.2682 #gt  arXiv:0910.4103 arXiv:0804.2682 #gt''',
    user='114744049040264263224',
    etag='old data',
    title='Such an interesting Post!',
)

def submit_posts(posts):
    it = incoming.find_or_insert_posts([d.copy() for d in posts], None, 
        lambda x:core.GplusPersonData(x, insertNew='findOrInsert').parent,
        lambda x:x['content'], lambda x:x['user'], lambda x:0,
        lambda x:x['id'], lambda x:datetime.now(),
        lambda x:False, 'gplusPost')
    return list(it)

def cleanup_post(post):
    for c in post.citations:
        c.delete()
    post.delete()

def test_multiple_citations(d=post1, citationType='discuss'):
    'add post with multiple citations, redundancy, ordering issues'
    l = submit_posts([d]) # create test post
    assert len(l) == 1
    post = l[0]
    assert post.parent.arxiv.id == '0804.2682'
    assert post.citationType == citationType
    assert len(post.citations) == 2
    ids = [c.parent.arxiv.id for c in post.citations]
    assert '0910.4103' in ids and '1310.2239' in ids
    assert len(post.citations[0].parent.citations) == 1
    assert post.citations[0].title == 'Such an interesting Post!'
    assert len(post.citations[1].parent.citations) == 1
    # finally clean up by deleting our test post
    cleanup_post(post)

def test_post_update(newText='update #spnetwork arXiv:0804.2682 #cat'):
    'check that etag value will force updating'
    submit_posts([post1])
    d = post1.copy()
    d['content'] = newText
    submit_posts([d])
    p = core.Post(d['id']) # retrieve from DB
    assert p.get_text() == post1['content'] # no update b/c etag unchanged!
    d = post1.copy()
    d['content'] = newText
    d['etag'] = 'new and improved'
    submit_posts([d])
    p = core.Post(d['id']) # retrieve from DB
    assert p.etag == 'new and improved'
    assert p.get_text() == newText
    cleanup_post(p)

def test_bad_tag():
    'check if #recommended crashes incoming'
    postDict = dict(
        id='temporaryPost',
        content='''this is my post.
    It talks about three papers including  arXiv:0910.4103
    and http://arxiv.org/abs/1310.2239
    #spnetwork #recommended arXiv:0804.2682 #gt  arXiv:0910.4103 arXiv:0804.2682 #gt''',
        user='114744049040264263224',
        title='Such an interesting Post!',
    )
    test_multiple_citations(postDict)

def test_arxiv_href():
    'check handling of arxiv URL in HTML <A HREF>'
    content = '''
I want to discuss <A HREF="http://arxiv.org/abs/0906.0213">this paper</A>
#spnetwork
'''
    check_parse(content)

def test_no_spnetwork():
    'check proper handling of post lacking #spnetwork tag'
    d = post1.copy()
    d['content'] = '''
I want to discuss <A HREF="http://arxiv.org/abs/0906.0213">this paper</A>
'''
    l = submit_posts([d, post1])
    assert len(l) == 1
    cleanup_post(l[0])
    

def check_parse(t, primaryID='0906.0213', primaryType='arxiv', 
                primaryRole='discuss', tags=[]):
    refs, topics, primary = incoming.get_references_and_tags(t)
    assert (topics == tags)
    assert primary == primaryID
    assert refs[primary][1] == primaryType
    assert refs[primary][0] == primaryRole
    

def test_arxiv_versions(arxivIDs=('1108.1172', '1108.1172v3')):
    'check if versioned arxiv IDs create duplicate records'
    l = [core.ArxivPaperData(s, insertNew='findOrInsert').parent
         for s in arxivIDs]
    for p in l[1:]:
        if p._id != l[0]._id:
            raise AssertionError('arxiv versions map to different Paper records!')

def test_arxiv_versions2(arxivIDs=('math.HO_9404236', 'math.HO_9404236')):
    'check if math.HO/9404236 style arxiv IDs create duplicate records'
    test_arxiv_versions(arxivIDs)
