import sqlite3
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from axiom.storage import D1Store
from axiom.workspace import new_project, saved_record
from axiom.research import normalize_crossref


def test_d1_crud_with_actual_sqlite_sql(monkeypatch):
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    connection.executescript((Path(__file__).parents[1] / 'schema.sql').read_text())
    def api(url, json, headers, timeout):
        cursor = connection.execute(json['sql'], json['params'])
        results = [dict(row) for row in cursor.fetchall()] if cursor.description else []
        connection.commit()
        return Mock(raise_for_status=lambda: None, json=lambda: {'success': True, 'result': [{'success': True, 'results': results}]})
    monkeypatch.setattr('axiom.storage.requests.post', api)
    store = D1Store('a'*32, '12345678-1234-1234-1234-123456789abc', 'private-token')
    project = new_project('D1 test', 'Does SQL persistence work?', 'Custom')
    store.create(project)
    p = normalize_crossref({'DOI': '10.1/test', 'title': ['Original test record']})
    record = saved_record(p, project['id'])
    store.save(record)
    store.update({**record, 'notes': 'Persistent note', 'favorite': True})
    assert store.load()['saved'][0]['notes'] == 'Persistent note'
    assert store.load()['saved'][0]['favorite'] is True
    other = D1Store('a'*32, '12345678-1234-1234-1234-123456789abc', 'private-token', owner='another-owner')
    assert other.load() == {'projects': [], 'saved': []}
    store.remove(p['id'], project['id'])
    assert store.load()['saved'] == []


def test_d1_failure_does_not_expose_token(monkeypatch):
    monkeypatch.setattr('axiom.storage.requests.post', lambda *a, **k: Mock(raise_for_status=lambda: None, json=lambda: {'success': False}))
    store = D1Store('a'*32, '12345678-1234-1234-1234-123456789abc', 'private-token')
    with pytest.raises(ValueError) as exc:
        store.load()
    assert 'private-token' not in str(exc.value)
