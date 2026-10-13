from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parents[1] / 'streamlit_app.py')


def test_app_navigation_and_project_creation():
    app = AppTest.from_file(APP).run(timeout=20)
    assert not app.exception
    for view in ['Discover papers', 'Research projects', 'My library', 'Backup & settings', 'Research roadmap', 'Overview']:
        app.sidebar.radio[0].set_value(view).run()
        assert not app.exception, view
    app.sidebar.radio[0].set_value('Research projects').run()
    app.text_input[0].set_value('Topology research')
    app.text_area[0].set_value('How does algebraic K-theory connect to topology?')
    app.button[0].click().run()
    assert not app.exception
    assert len(app.session_state['workspace']['projects']) == 1
    app.sidebar.radio[0].set_value('Overview').run()
    assert app.metric[0].value == '1'
    app.sidebar.toggle[0].set_value(True).run()
    assert app.metric[0].value == '1' and app.metric[1].value == '3'
    assert not app.exception


def test_password_gate_and_incomplete_storage_fail_closed():
    app = AppTest.from_file(APP)
    app.secrets['APP_PASSWORD'] = 'a-long-test-password'
    app.run()
    assert not app.exception and app.text_input[0].label == 'Workspace password'
    app.text_input[0].set_value('incorrect')
    app.button[0].click().run()
    assert app.error and not app.exception
    app.text_input[0].set_value('a-long-test-password')
    app.button[0].click().run()
    assert not app.exception and app.sidebar.radio[0].value == 'Overview'
    broken = AppTest.from_file(APP)
    broken.secrets['CF_ACCOUNT_ID'] = 'a'*32
    broken.run()
    assert broken.error and not broken.exception


def test_search_save_notes_and_pagination(monkeypatch):
    from axiom.research import normalize_crossref
    record = normalize_crossref({'DOI': '10.1/test-ui', 'title': ['Test record for interface validation'], 'abstract': 'Test abstract, not scientific evidence'})
    monkeypatch.setattr('axiom.research._fetch', lambda *a, **k: ([record], 41))
    app = AppTest.from_file(APP).run()
    app.sidebar.radio[0].set_value('Research projects').run()
    app.text_input[0].set_value('Interface validation')
    app.text_area[0].set_value('Does the UI preserve notes and favorites?')
    next(b for b in app.button if b.label == 'Create project').click().run()
    app.sidebar.radio[0].set_value('Discover papers').run()
    app.text_input[0].set_value('Interface validation test query')
    next(b for b in app.button if b.label == 'Search literature').click().run()
    assert not app.exception and len(app.session_state['search_results']['papers']) == 1
    next(b for b in app.button if b.label == 'Save paper').click().run()
    assert len(app.session_state['workspace']['saved']) == 1
    next(b for b in app.button if b.label == 'Next page').click().run()
    assert app.session_state['search_page'] == 2 and not app.exception
    app.sidebar.radio[0].set_value('My library').run()
    app.text_area[0].set_value('Verified interface notes')
    next(c for c in app.checkbox if c.label == 'Favorite').check()
    next(b for b in app.button if b.label == 'Save notes and progress').click().run()
    saved = app.session_state['workspace']['saved'][0]
    assert saved['notes'] == 'Verified interface notes' and saved['favorite'] is True
    assert not app.exception
