"""Streamlit entry point for Axiom. No Cloudflare Workers/Zero Trust deployment needed."""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import date

import streamlit as st

from axiom.demo import demo_workspace
from axiom.research import search, safe_url
from axiom.storage import D1Store
from axiom.workspace import (FRAMEWORKS, STATUSES, SessionStore, backup_json, new_project,
                             papers_bibtex, papers_csv, read_backup, saved_record)

st.set_page_config(page_title='Axiom · Research workspace', page_icon='📚', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
.block-container {max-width:1200px; padding-top:2rem; padding-bottom:3rem;}
[data-testid="stSidebar"] {background:var(--secondary-background-color);}
[data-testid="stMetric"] {border:1px solid #e6e2f0; border-radius:14px; padding:16px;}
h1,h2,h3 {letter-spacing:-.03em;}
.stButton>button[kind="primary"] {border-radius:9px;}
</style>''', unsafe_allow_html=True)


def setting(name, default=''):
    try:
        return str(st.secrets.get(name, default))
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default


password = setting('APP_PASSWORD')
d1_values = [setting(n) for n in ['CF_ACCOUNT_ID', 'CF_DATABASE_ID', 'CF_API_TOKEN']]
if any(d1_values) and (not all(d1_values) or len(password) < 16):
    st.error('For persistent storage, configure all three D1 secrets and an APP_PASSWORD of at least 16 characters. See DEPLOY_STREAMLIT.md.')
    st.stop()
if password:
    fingerprint = hashlib.sha256(password.encode()).hexdigest()
    if st.session_state.get('auth_fingerprint') != fingerprint:
        st.title('Axiom')
        st.caption('Sign in to your personal research workspace.')
        with st.form('login'):
            submitted_password = st.text_input('Workspace password', type='password')
            login = st.form_submit_button('Sign in', type='primary')
        if login:
            if hmac.compare_digest(submitted_password.encode(), password.encode()):
                st.session_state['auth_fingerprint'] = fingerprint
                st.rerun()
            else:
                st.error('Incorrect password.')
        st.stop()

try:
    store = D1Store(*d1_values, owner=setting('AXIOM_OWNER_ID', 'axiom-streamlit-owner')) if all(d1_values) else SessionStore(st.session_state)
    real = store.load()
except ValueError as exc:
    st.error(str(exc))
    st.info('Your database has not been replaced with an empty workspace. Fix the connection and reload.')
    st.stop()

st.session_state.setdefault('search_results', None)
st.session_state.setdefault('search_options', None)
st.session_state.setdefault('search_page', 1)


def mutate(method, *args):
    try:
        getattr(store, method)(*args)
        st.session_state['notice'] = 'Workspace updated.'
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))


with st.sidebar:
    st.title('axiom')
    st.caption('RESEARCH INTELLIGENCE WORKSPACE')
    demo = st.toggle('Explore fictional demo', value=False, key='demo_mode')
    view = st.radio('Workspace', ['Overview', 'Discover papers', 'Research projects', 'My library', 'Backup & settings', 'Research roadmap'], key='view')
    advanced = st.toggle('Advanced metadata', value=False)
    st.divider()
    if all(d1_values):
        st.caption('Persistent personal workspace · D1')
        st.caption('Everyone authorized for this app shares this owner workspace.')
    else:
        st.caption('Session workspace · save a backup before closing or reloading.')
    if password and st.button('Sign out'):
        st.session_state.clear()
        st.rerun()
    st.caption('Phase 1 · Evidence before inference')

workspace = demo_workspace() if demo else real
if demo:
    st.warning('Fictional demo workspace. These records are illustrative and cannot be cited or saved as research.')
elif not all(d1_values):
    st.info('Your work is kept in this browser session. Download a workspace backup before closing or reloading. Optional durable storage is available in Backup & settings.')
if notice := st.session_state.pop('notice', ''):
    st.success(notice)


@st.cache_data(ttl=120, show_spinner=False)
def cached_search(options, key, email):
    return search(**options, key=key, email=email)


def exports(papers, prefix):
    cols = st.columns(3)
    cols[0].download_button('Download CSV', papers_csv(papers), 'axiom-literature.csv', 'text/csv', key=f'{prefix}-csv')
    cols[1].download_button('Download BibTeX', papers_bibtex(papers), 'axiom-literature.bib', 'application/x-bibtex', key=f'{prefix}-bib')
    cols[2].download_button('Download JSON', json.dumps(papers, indent=2, ensure_ascii=False), 'axiom-literature.json', 'application/json', key=f'{prefix}-json')


def paper_card(paper, key, editable=None):
    identity = paper["id"] + (editable["projectId"] if editable else "")
    key = key + "-" + hashlib.sha256(identity.encode()).hexdigest()[:16]
    with st.container(border=True):
        st.subheader(paper['title'])
        st.caption(' · '.join([paper['provider'], str(paper.get('year') or 'Year unavailable'), paper.get('journal') or 'Journal unavailable']))
        st.write('; '.join(paper['authors']) or 'Authors unavailable')
        if advanced:
            oa = 'Open access' if paper.get('openAccess') is True else 'Not open access' if paper.get('openAccess') is False else 'Access status unknown'
            st.caption(f"{paper['type']} · {oa} · Citations: {paper.get('citations') if paper.get('citations') is not None else 'unavailable'}")
            if paper.get('doi'):
                st.caption(f"DOI: {paper['doi']}")
            if 'score' in paper:
                st.caption(f"Metadata relevance: {paper['score']}/100 · {'; '.join(paper.get('matchedTerms', [])) or 'No matching terms'}")
        links = st.columns(2)
        if safe_url(paper.get('url')):
            links[0].link_button('View original source', paper['url'])
        if safe_url(paper.get('fullTextUrl')):
            links[1].link_button('Open-access location', paper['fullTextUrl'])
        with st.expander('Read abstract'):
            st.write(paper.get('abstract') or 'This provider did not supply an abstract. Consult the original source.')
        if editable is not None and not demo:
            with st.form(f'edit-{key}'):
                status = st.selectbox('Reading status', STATUSES, index=STATUSES.index(editable['status']))
                collection = st.text_input('Collection', value=editable['collection'], max_chars=80)
                notes = st.text_area('Your notes', value=editable['notes'], max_chars=20000)
                favorite = st.checkbox('Favorite', value=editable['favorite'])
                if st.form_submit_button('Save notes and progress'):
                    if not collection.strip():
                        st.error('Enter a collection name.')
                    else:
                        mutate('update', {**editable, 'status': status, 'collection': collection.strip(), 'notes': notes, 'favorite': favorite})
            if st.checkbox('Confirm removal from this project', key=f'confirm-{key}'):
                if st.button('Remove saved paper', key=f'remove-{key}'):
                    mutate('remove', paper['id'], editable['projectId'])
        elif not paper['demo']:
            eligible = [p for p in real['projects'] if not any(s['paper']['id'] == paper['id'] and s['projectId'] == p['id'] for s in real['saved'])]
            if eligible:
                choice = st.selectbox('Save to project', [p['id'] for p in eligible],
                                      format_func=lambda pid: next(p['title'] for p in eligible if p['id'] == pid), key=f'project-{key}')
                if st.button('Save paper', key=f'save-{key}', type='primary', disabled=demo):
                    mutate('save', saved_record(paper, choice))
            elif not real['projects']:
                st.caption('Create a research project before saving this paper.')
            else:
                st.caption('Already saved to all your projects.')


if view == 'Overview':
    st.title('Research begins with a clear question.')
    st.write('Discover literature, organize evidence, and keep your reading connected to your research.')
    cols = st.columns(4)
    cols[0].metric('Research projects', len(workspace['projects']))
    cols[1].metric('Saved papers', len(workspace['saved']))
    cols[2].metric('Favorites', sum(s['favorite'] for s in workspace['saved']))
    cols[3].metric('Completed', sum(s['status'] == 'Completed' for s in workspace['saved']))
    st.subheader('Your research questions')
    if not workspace['projects']:
        st.info('Open Research projects in the sidebar to create your first project. Then use Discover papers to search live literature.')
    for p in workspace['projects']:
        with st.container(border=True):
            st.subheader(p['title'])
            st.write(p['question'])
            st.caption(f"{p['framework']} · {sum(s['projectId'] == p['id'] for s in workspace['saved'])} saved papers")
    st.subheader('Recently saved')
    for i, s in enumerate(workspace['saved'][-3:]):
        paper_card(s['paper'], f'home-{i}')

elif view == 'Discover papers':
    st.title('Discover papers')
    st.caption('Live OpenAlex and Crossref metadata. Relevance is lexical metadata ranking, not an AI judgment of scientific quality.')
    with st.form('search'):
        query = st.text_input('Your research question or keywords', placeholder='e.g. algebraic K-theory and topological Hochschild homology', max_chars=500)
        cols = st.columns(2)
        providers = cols[0].multiselect('Sources', ['OpenAlex', 'Crossref'], default=['OpenAlex', 'Crossref'])
        years = cols[1].slider('Publication years', 1900, date.today().year, (2000, date.today().year))
        cols = st.columns(2)
        kind = cols[0].selectbox('Publication type', ['All', 'Journal article', 'Review'])
        oa = cols[1].checkbox('Only confirmed open-access records')
        submitted = st.form_submit_button('Search literature', type='primary')
    if submitted:
        options = dict(query=query, providers=providers, page=1, start=years[0], end=years[1], oa=oa, kind=kind)
        try:
            with st.spinner('Searching scholarly providers…'):
                result = cached_search(options, setting('OPENALEX_API_KEY'), setting('CROSSREF_MAILTO'))
            st.session_state.update(search_results=result, search_options=options, search_page=1)
        except ValueError as exc:
            st.session_state['search_results'] = None
            st.error(str(exc))
    result = st.session_state['search_results']
    if result is not None:
        options = st.session_state['search_options']
        st.write(f"Results for: {options['query']}")
        st.caption(f"Page {st.session_state['search_page']} · {len(result['papers'])} displayed · {result['duplicates']} DOI duplicates merged")
        for warning in result['warnings']:
            st.warning(warning)
        if not result['successful']:
            st.error('No provider responded successfully. Check provider credentials or try again later.')
        elif not result['papers']:
            st.info('No matching records on this fetched page. Adjust the filters or search question.')
        st.caption('Provider totals are source totals, not unique combined results. Metadata filters and ranking apply to the fetched page.')
        if advanced:
            st.json(result['totals'])
        exports(result['papers'], 'search-export')
        cols = st.columns(2)
        previous = cols[0].button('Previous page', disabled=st.session_state['search_page'] <= 1)
        following = cols[1].button('Next page', disabled=not result['hasMore'] or st.session_state['search_page'] >= 100)
        if previous or following:
            next_page = st.session_state['search_page'] + (1 if following else -1)
            new_options = {**options, 'page': next_page}
            try:
                with st.spinner('Loading page…'):
                    new_result = cached_search(new_options, setting('OPENALEX_API_KEY'), setting('CROSSREF_MAILTO'))
                st.session_state.update(search_results=new_result, search_options=new_options, search_page=next_page)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        for i, paper in enumerate(result['papers']):
            paper_card(paper, f'search-{st.session_state["search_page"]}-{i}')

elif view == 'Research projects':
    st.title('Research projects')
    if not demo:
        with st.expander('Create a project', expanded=not real['projects']):
            with st.form('project'):
                title = st.text_input('Project title', max_chars=150)
                question = st.text_area('Research question', max_chars=2000)
                framework = st.selectbox('Question framework', FRAMEWORKS)
                if st.form_submit_button('Create project', type='primary'):
                    try:
                        project = new_project(title, question, framework)
                        mutate('create', project)
                    except ValueError as exc:
                        st.error(str(exc))
    for p in workspace['projects']:
        with st.container(border=True):
            st.subheader(p['title'])
            st.write(p['question'])
            st.caption(f"Framework: {p['framework']} · Created: {p['createdAt'][:10]}")
            records = [s for s in workspace['saved'] if s['projectId'] == p['id']]
            st.write(f'{len(records)} saved papers')
            for s in records:
                st.write('• ' + s['paper']['title'])
            if records:
                exports([s['paper'] for s in records], f'project-{p["id"]}')

elif view == 'My library':
    st.title('My library')
    project_names = {p['id']: p['title'] for p in workspace['projects']}
    cols = st.columns(3)
    project = cols[0].selectbox('Project', ['All projects'] + list(project_names), format_func=lambda value: project_names.get(value, value))
    status = cols[1].selectbox('Reading status', ['All statuses'] + STATUSES)
    favorites = cols[2].checkbox('Favorites only')
    filter_text = st.text_input('Find in titles, authors, collections and notes').lower().strip()
    records = [s for s in workspace['saved'] if (project == 'All projects' or s['projectId'] == project)
               and (status == 'All statuses' or s['status'] == status) and (not favorites or s['favorite'])
               and (not filter_text or filter_text in ' '.join([s['paper']['title'], *s['paper']['authors'], s['notes'], s['collection']]).lower())]
    st.caption(f'{len(records)} saved records match your filters.')
    exports([s['paper'] for s in records], 'library-export')
    st.download_button('Download saved records with notes (JSON)', json.dumps(records, indent=2, ensure_ascii=False),
                       'axiom-saved-records.json', 'application/json')
    if not records:
        st.info('Save live search results to a project to build your library.')
    for i, record in enumerate(records):
        st.caption(f"Project: {project_names.get(record['projectId'], 'Unknown')} · {record['status']} · {record['collection']}")
        paper_card(record['paper'], f'library-{i}', editable=record)

elif view == 'Backup & settings':
    st.title('Backup & settings')
    st.subheader('Keep a portable copy of your work')
    st.write('A workspace backup includes projects, saved papers, notes, favorites and reading progress. CSV and BibTeX exports contain paper metadata only.')
    st.download_button('Download full workspace backup', backup_json(real), 'axiom-workspace-backup.json', 'application/json', type='primary')
    uploaded = st.file_uploader('Import an Axiom workspace backup', type=['json'])
    if uploaded:
        try:
            imported = read_backup(uploaded.getvalue())
            st.write(f"Backup contains {len(imported['projects'])} projects and {len(imported['saved'])} saved papers.")
            st.caption('Import adds missing records. Existing project IDs and saved papers keep their current values and notes.')
            if st.button('Merge backup into my workspace', disabled=demo):
                mutate('merge', imported)
        except ValueError as exc:
            st.error(str(exc))
    st.divider()
    st.subheader('Storage')
    if all(d1_values):
        st.success('Durable database connected. Saves are stored in your existing Cloudflare D1 database.')
        st.write('This is a single-owner workspace. Anyone authorized for this app can access it. Keep the app private and the workspace password confidential.')
    else:
        st.warning('Session storage is temporary. Reloading the browser, ending a session, or a server restart can lose the workspace. Download a backup and import it in your next session.')
        st.write('For automatic saving across visits, follow the optional D1 instructions in DEPLOY_STREAMLIT.md. They reuse your existing database and do not require Zero Trust.')
    st.subheader('Search provider settings')
    st.write('Optional OPENALEX_API_KEY and CROSSREF_MAILTO settings are configured through Streamlit app secrets. API keys are never entered into research forms.')
    st.caption('Use the Streamlit settings menu for theme changes. Source abstracts are metadata; verify scientific claims against original publications.')

else:
    st.title('Research roadmap')
    st.write('This release implements literature discovery, organization, notes and exports.')
    st.info('Systematic review protocols, screening, PRISMA, numerical meta-analysis, grounded PDF/AI synthesis, citation networks and knowledge graphs remain planned. These tools are not implemented in this app.')

st.divider()
st.caption('Axiom · Built around evidence. Designed for discovery. · Streamlit edition')
