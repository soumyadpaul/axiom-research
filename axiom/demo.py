from .workspace import empty_workspace


def demo_workspace():
    workspace = empty_workspace()
    workspace['projects'] = [{'id': 'demo-lung', 'title': 'Lung microbiome & host immunity',
                              'question': 'How does the lung microbiome influence immune responses in bacterial pneumonia?',
                              'framework': 'PECO', 'demo': True, 'createdAt': '2026-09-30T00:00:00Z'}]
    titles = ['The lung microbiome and host immunity in bacterial pneumonia',
              'Microbial metabolites and neutrophil responses: an experimental perspective',
              'Mapping the evidence on respiratory dysbiosis and sepsis']
    for i, title in enumerate(titles):
        paper = dict(id=f'demo-{i+1}', title=title, authors=['Example Researcher'],
                     journal='Illustrative record — not a publication', year=2025-i,
                     abstract='This fictional record demonstrates the interface. It is not a citable publication and supplies no scientific findings. Search live literature for real evidence.',
                     doi=None, citations=None, openAccess=None, type='review' if i == 2 else 'article',
                     provider='Demo', url=None, fullTextUrl=None, demo=True)
        workspace['saved'].append(dict(paper=paper, projectId='demo-lung', status='Reading' if i == 0 else 'Unread',
                                       collection='Background', notes='', favorite=i == 0))
    return workspace
