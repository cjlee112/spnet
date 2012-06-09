import core
import cherrypy

templates = dict(
    )

def new_recommendation(template, paper, text):
    try:
        author = cherrypy.session['person']
    except KeyError:
        raise cherrypy._cperror.HTTPError(404, 'you must login!')
    r = core.Recommendation(parent=paper,
                            docData=dict(author=author._id, text=text))
    return template.render(paper=paper, text=text)


def basic_search(template, collection, query, options='i'):
    papers = authors = ()
    if collection == 'paper':
        papers = core.Paper.find_obj(dict(title={'$regex':query,
                                                 '$options':options}))
    elif collection == 'person':
        authors = core.Person.find_obj(dict(name={'$regex':query,
                                                  '$options':options}))
    return template.render(papers=papers, authors=authors)

views = dict(
    new_rec=new_recommendation,
    search=basic_search,
    )
