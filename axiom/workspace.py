from __future__ import annotations

import copy
import csv
import io
import json
import math
import re
import uuid
from datetime import datetime, timezone

from .research import safe_url

STATUSES = ['Unread', 'Reading', 'Completed']
FRAMEWORKS = ['PICO', 'PICOS', 'PECO', 'SPIDER', 'Custom']


def empty_workspace():
    return {'projects': [], 'saved': []}


def _text(value, limit, required=False):
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ValueError('Invalid or oversized text in workspace data.')
    return value


def validate_paper(p):
    if not isinstance(p, dict):
        raise ValueError('Invalid paper record.')
    result = {k: _text(p.get(k), lim, True) for k, lim in [('id', 500), ('title', 3000), ('type', 100)]}
    provider = p.get('provider')
    if provider not in ['OpenAlex', 'Crossref', 'Demo'] or type(p.get('demo')) is not bool or p['demo'] != (provider == 'Demo'):
        raise ValueError('Invalid paper source or demo label.')
    result.update(provider=provider, demo=p['demo'])
    authors = p.get('authors')
    if not isinstance(authors, list) or len(authors) > 500:
        raise ValueError('Invalid authors.')
    result['authors'] = [_text(a, 500) for a in authors]
    for name, lim in [('journal', 2000), ('abstract', 80000), ('doi', 500)]:
        result[name] = None if p.get(name) is None else _text(p[name], lim)
    year = p.get('year')
    if year is not None and (type(year) is not int or not 1000 <= year <= 2100):
        raise ValueError('Invalid publication year.')
    result['year'] = year
    citations = p.get('citations')
    if citations is not None and (type(citations) not in (int, float) or not math.isfinite(citations) or citations < 0):
        raise ValueError('Invalid citation count.')
    result['citations'] = citations
    oa = p.get('openAccess')
    if oa is not None and type(oa) is not bool:
        raise ValueError('Invalid open-access value.')
    result['openAccess'] = oa
    for field in ['url', 'fullTextUrl']:
        value = p.get(field)
        if value is not None and (not isinstance(value, str) or len(value) > 2000 or not safe_url(value)):
            raise ValueError('Invalid source link.')
        result[field] = value
    return result


def new_project(title, question, framework):
    title, question = title.strip(), question.strip()
    if not 3 <= len(title) <= 150 or not 5 <= len(question) <= 2000 or framework not in FRAMEWORKS:
        raise ValueError('Use a title of 3–150 characters and a question of 5–2000 characters.')
    return {'id': str(uuid.uuid4()), 'title': title, 'question': question, 'framework': framework,
            'demo': False, 'createdAt': datetime.now(timezone.utc).isoformat()}


def saved_record(paper, project_id):
    paper = validate_paper(paper)
    if paper['demo']:
        raise ValueError('Fictional demo papers cannot be saved as real research.')
    return {'paper': paper, 'projectId': project_id, 'status': 'Unread',
            'collection': 'Background', 'notes': '', 'favorite': False}


def validate_workspace(data):
    if not isinstance(data, dict):
        raise ValueError('Expected a workspace JSON object.')
    if 'workspace' in data:
        if data.get('schemaVersion') != 1:
            raise ValueError('Unsupported backup version.')
        data = data['workspace']
    if not isinstance(data, dict) or not isinstance(data.get('projects'), list) or not isinstance(data.get('saved'), list):
        raise ValueError('Backup must contain projects and saved records.')
    if len(data['projects']) > 500 or len(data['saved']) > 2000:
        raise ValueError('This backup exceeds the supported workspace size.')
    projects, saved, ids, pairs = [], [], set(), set()
    for p in data['projects']:
        if not isinstance(p, dict) or p.get('framework') not in FRAMEWORKS or p.get('demo') is not False:
            raise ValueError('Import only real research workspaces.')
        project = {k: _text(p.get(k), lim, True) for k, lim in
                   [('id', 500), ('title', 150), ('question', 2000), ('createdAt', 100)]}
        if project['id'] in ids:
            raise ValueError('Duplicate project ID in backup.')
        ids.add(project['id'])
        project.update(framework=p['framework'], demo=False)
        projects.append(project)
    for s in data['saved']:
        if not isinstance(s, dict) or not isinstance(s.get('projectId'), str) or s.get('projectId') not in ids or s.get('status') not in STATUSES or type(s.get('favorite')) is not bool:
            raise ValueError('Invalid saved record or missing project.')
        paper = validate_paper(s.get('paper'))
        if paper['demo']:
            raise ValueError('Demo records cannot be imported as research.')
        pair = (paper['id'], s['projectId'])
        if pair in pairs:
            raise ValueError('Duplicate saved paper in project.')
        pairs.add(pair)
        saved.append({'paper': paper, 'projectId': s['projectId'], 'status': s['status'],
                      'collection': _text(s.get('collection'), 80, True),
                      'notes': _text(s.get('notes'), 20000), 'favorite': s['favorite']})
    return {'projects': projects, 'saved': saved}


def read_backup(raw):
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError('Backup must be smaller than 10 MB.')
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError('The backup is not valid UTF-8 JSON.') from exc
    return validate_workspace(data)


def backup_json(workspace):
    return json.dumps({'schemaVersion': 1, 'exportedAt': datetime.now(timezone.utc).isoformat(),
                       'workspace': workspace}, indent=2, ensure_ascii=False)


def papers_csv(papers):
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['Title', 'Authors', 'Year', 'Journal', 'DOI', 'Provider', 'Demo'])
    for p in papers:
        row = [p['title'], '; '.join(p['authors']), p.get('year'), p.get('journal'), p.get('doi'), p['provider'], p['demo']]
        values = []
        for value in row:
            text = '' if value is None else str(value)
            if re.match(r'^[\s]*[=+@-]', text) or text.startswith(('\t', '\r')):
                text = "'" + text
            values.append(text)
        writer.writerow(values)
    return output.getvalue()


def papers_bibtex(papers):
    def esc(text):
        return str(text).replace('\\', '').replace('{', '').replace('}', '').replace('\n', ' ')
    output = []
    for i, p in enumerate(p for p in papers if not p['demo']):
        fields = [('title', p['title']), ('author', ' and '.join(p['authors'])),
                  ('year', p.get('year')), ('journal', p.get('journal')), ('doi', p.get('doi'))]
        fields = [f'  {key} = {{{esc(value)}}}' for key, value in fields if value is not None and value != '']
        entry = 'article' if p['type'] in ['article', 'journal-article', 'review'] else 'misc'
        output.append(f'@{entry}{{axiom{i+1},\n' + ',\n'.join(fields) + '\n}')
    return '\n\n'.join(output)


class SessionStore:
    def __init__(self, state):
        self.state = state
        self.state.setdefault('workspace', empty_workspace())

    def load(self):
        return copy.deepcopy(self.state['workspace'])

    def create(self, project):
        if not any(p['id'] == project['id'] for p in self.state['workspace']['projects']):
            self.state['workspace']['projects'].append(copy.deepcopy(project))

    def save(self, record):
        if not any(p['id'] == record['projectId'] for p in self.state['workspace']['projects']):
            raise ValueError('Project not found.')
        if not any(s['paper']['id'] == record['paper']['id'] and s['projectId'] == record['projectId'] for s in self.state['workspace']['saved']):
            self.state['workspace']['saved'].append(copy.deepcopy(record))

    def update(self, record):
        for i, s in enumerate(self.state['workspace']['saved']):
            if (s['paper']['id'], s['projectId']) == (record['paper']['id'], record['projectId']):
                self.state['workspace']['saved'][i] = copy.deepcopy(record)
                return
        raise ValueError('Saved paper not found.')

    def remove(self, paper_id, project_id):
        self.state['workspace']['saved'] = [s for s in self.state['workspace']['saved']
                                           if (s['paper']['id'], s['projectId']) != (paper_id, project_id)]

    def merge(self, workspace):
        # Keep existing records and notes when an import has a matching ID.
        next_state = SessionStore({'workspace': self.load()})
        for p in workspace['projects']:
            next_state.create(p)
        for s in workspace['saved']:
            next_state.save(s)
        self.state['workspace'] = next_state.load()
