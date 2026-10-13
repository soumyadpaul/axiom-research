"""Optional durable personal workspace using the user's existing D1 database.

This uses Cloudflare's database API, not Cloudflare Access or Zero Trust.
Protect this single-owner app with APP_PASSWORD and Community Cloud private sharing.
"""
import json
import re

import requests

from .workspace import empty_workspace, validate_workspace


class D1Store:
    def __init__(self, account_id, database_id, token, owner='axiom-streamlit-owner'):
        if not re.fullmatch(r'[a-fA-F0-9]{32}', account_id) or not re.fullmatch(r'[a-fA-F0-9-]{36}', database_id):
            raise ValueError('Check the D1 account and database IDs in app secrets.')
        self.url = f'https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}/query'
        self.token = token
        self.owner = owner

    def query(self, sql, params=()):
        try:
            response = requests.post(self.url, json={'sql': sql, 'params': list(params)},
                                     headers={'Authorization': f'Bearer {self.token}'}, timeout=(8, 20))
            response.raise_for_status()
            body = response.json()
            if not body.get('success') or not body.get('result'):
                raise ValueError('Database query failed.')
            result = body['result'][0]
            if result.get('success') is False:
                raise ValueError('Database query failed.')
            return result.get('results') or []
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            raise ValueError('Could not access your database. Check the D1 secret values, token permissions and database tables.') from exc

    def load(self):
        projects = self.query('SELECT * FROM projects WHERE owner_id = ? ORDER BY created_at DESC', [self.owner])
        saved = self.query('SELECT * FROM saved_papers WHERE owner_id = ?', [self.owner])
        ws = empty_workspace()
        ws['projects'] = [{'id': p['id'], 'title': p['title'], 'question': p['question'],
                           'framework': p['framework'], 'demo': p['demo'] == 'true', 'createdAt': p['created_at']} for p in projects]
        ws['saved'] = [{'paper': json.loads(s['metadata']), 'projectId': s['project_id'],
                        'status': s['status'], 'collection': s['collection'], 'notes': s['notes'],
                        'favorite': s['favorite'] == 'true'} for s in saved]
        return validate_workspace(ws)

    def create(self, p):
        self.query('INSERT INTO projects (id,owner_id,title,question,framework,demo,created_at) VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING',
                   [p['id'], self.owner, p['title'], p['question'], p['framework'], 'false', p['createdAt']])
        if not self.query('SELECT id FROM projects WHERE id = ? AND owner_id = ?', [p['id'], self.owner]):
            raise ValueError('This project ID belongs to a different workspace.')

    def save(self, s):
        self.query('INSERT INTO saved_papers (owner_id,paper_id,project_id,metadata,status,collection,notes,favorite) SELECT ?,?,?,?,?,?,?,? WHERE EXISTS (SELECT 1 FROM projects WHERE id = ? AND owner_id = ?) ON CONFLICT(owner_id,paper_id,project_id) DO NOTHING',
                   [self.owner, s['paper']['id'], s['projectId'], json.dumps(s['paper']), s['status'],
                    s['collection'], s['notes'], str(s['favorite']).lower(), s['projectId'], self.owner])

    def update(self, s):
        self.query('UPDATE saved_papers SET status=?,collection=?,notes=?,favorite=? WHERE owner_id=? AND paper_id=? AND project_id=?',
                   [s['status'], s['collection'], s['notes'], str(s['favorite']).lower(), self.owner, s['paper']['id'], s['projectId']])

    def remove(self, paper_id, project_id):
        self.query('DELETE FROM saved_papers WHERE owner_id=? AND paper_id=? AND project_id=?', [self.owner, paper_id, project_id])

    def merge(self, ws):
        # Non-destructive import: existing rows remain. Partial imports can be retried.
        for p in ws['projects']:
            self.create(p)
        for s in ws['saved']:
            self.save(s)
