import csv
import io
import json

import pytest

from axiom.research import deduplicate, normalize_crossref, normalize_openalex, rank, reconstruct_abstract, safe_url, search
from axiom.workspace import SessionStore, backup_json, new_project, papers_bibtex, papers_csv, read_backup, saved_record, validate_workspace


def paper():
    return normalize_crossref({'DOI': '10.1234/example', 'title': ['Algebraic K-theory'], 'author': [{'given': 'A', 'family': 'Researcher'}]})


def test_missing_metadata_is_not_invented():
    p = paper()
    assert p['abstract'] is None and p['year'] is None and p['openAccess'] is None


def test_abstract_reconstruction():
    assert reconstruct_abstract({'theory': [1], 'K': [0, 2]}) == 'K theory K'
    assert reconstruct_abstract(None) is None


def test_openalex_normalization():
    p = normalize_openalex({'id': 'W1', 'title': 'Example', 'doi': 'https://doi.org/10.1/ABC', 'open_access': {'is_oa': True}})
    assert p['doi'] == '10.1/ABC' and p['openAccess'] is True


def test_doi_deduplication_preserves_false():
    a = {**paper(), 'openAccess': False}
    b = {**paper(), 'doi': 'https://doi.org/10.1234/EXAMPLE', 'abstract': 'Original abstract', 'openAccess': True}
    result, n = deduplicate([a, b])
    assert n == 1 and result[0]['abstract'] == 'Original abstract' and result[0]['openAccess'] is False


def test_title_matches_rank_above_popular_irrelevant_work():
    assert rank(paper(), 'algebraic K-theory')['score'] > rank({**paper(), 'title': 'Cooking', 'citations': 1000000}, 'algebraic K-theory')['score']


def test_links_are_http_only():
    assert safe_url('javascript:alert(1)') is None
    assert safe_url('https://example.test') == 'https://example.test'


def test_csv_escapes_formula_and_multiline_quotes():
    p = {**paper(), 'title': ' =DANGEROUS()', 'journal': 'a,"b"\nline'}
    rows = list(csv.reader(io.StringIO(papers_csv([p]))))
    assert rows[1][0].startswith("'") and rows[1][3] == p['journal']


def test_bibtex_omits_demo_and_has_valid_field_separators():
    text = papers_bibtex([paper(), {**paper(), 'demo': True}])
    assert text.count('@') == 1 and 'doi = {10.1234/example}' in text


def test_save_notes_backup_and_session_isolation():
    one, two = SessionStore({}), SessionStore({})
    project = new_project('Test project', 'What is algebraic K-theory?', 'Custom')
    one.create(project)
    s = saved_record(paper(), project['id'])
    one.save(s)
    one.save(s)
    one.update({**s, 'notes': 'Read the original proof', 'favorite': True})
    restored = read_backup(backup_json(one.load()).encode())
    assert len(restored['saved']) == 1 and restored['saved'][0]['favorite']
    assert two.load()['projects'] == []
    two.merge(restored)
    assert two.load()['saved'][0]['notes'] == 'Read the original proof'
    one.remove(s['paper']['id'], project['id'])
    assert one.load()['saved'] == []


def test_import_preserves_existing_notes():
    state = SessionStore({})
    p = new_project('Test project', 'Question about evidence?', 'PICO')
    state.create(p)
    s = saved_record(paper(), p['id'])
    state.save({**s, 'notes': 'Current notes'})
    state.merge({'projects': [p], 'saved': [{**s, 'notes': 'Old backup notes'}]})
    assert state.load()['saved'][0]['notes'] == 'Current notes'


def test_backup_rejects_orphans_unsafe_links_and_demo():
    p = new_project('Test project', 'Question about evidence?', 'PICO')
    for record in [saved_record(paper(), 'missing'),
                   {**saved_record(paper(), p['id']), 'paper': {**paper(), 'url': 'javascript:alert(1)'}},
                   {**saved_record(paper(), p['id']), 'paper': {**paper(), 'provider': 'Demo', 'demo': True}}]:
        with pytest.raises(ValueError):
            validate_workspace({'projects': [p], 'saved': [record]})


def test_backup_rejects_malformed_json_and_oversize():
    with pytest.raises(ValueError):
        read_backup(b'{')
    with pytest.raises(ValueError):
        read_backup(b'x' * (10 * 1024 * 1024 + 1))


def test_partial_provider_failure_keeps_other_results(monkeypatch):
    def fetch(provider, *args):
        if provider == 'OpenAlex':
            raise ValueError('OpenAlex: request limit reached.')
        return [paper()], 21
    monkeypatch.setattr('axiom.research._fetch', fetch)
    result = search('algebraic theory', ['OpenAlex', 'Crossref'])
    assert result['successful'] == 1 and len(result['papers']) == 1 and result['warnings'] and result['hasMore']


def test_review_and_oa_filters_do_not_invent_labels(monkeypatch):
    monkeypatch.setattr('axiom.research._fetch', lambda *args: ([paper()], 1))
    result = search('algebraic theory', ['Crossref'], oa=True, kind='Review')
    assert result['papers'] == [] and result['warnings']


def test_search_requires_question_and_providers():
    with pytest.raises(ValueError):
        search('x', ['Crossref'])
    with pytest.raises(ValueError):
        search('valid query', [])
