from __future__ import annotations

import html
import math
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from urllib.parse import urlparse

import requests


def safe_url(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = urlparse(value)
        return value if parsed.scheme in ('https', 'http') and parsed.netloc else None
    except ValueError:
        return None


def clean_text(value):
    if not isinstance(value, str):
        return None
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]*>', ' ', value))).strip() or None


def normalize_doi(value):
    if not isinstance(value, str):
        return None
    return re.sub(r'^https?://(?:dx\.)?doi\.org/', '', value.strip(), flags=re.I) or None


def reconstruct_abstract(index):
    if not isinstance(index, dict):
        return None
    words = {}
    for word, positions in index.items():
        if isinstance(word, str) and isinstance(positions, list):
            for position in positions:
                if isinstance(position, int) and 0 <= position < 50000:
                    words[position] = word
    if not words:
        return None
    return ' '.join(words.get(i, '') for i in range(max(words) + 1)).strip()


def normalize_openalex(work):
    location = work.get('primary_location') or {}
    oa = work.get('open_access') or {}
    best = work.get('best_oa_location') or {}
    doi = normalize_doi(work.get('doi'))
    return dict(
        id=work.get('id') or (f'https://doi.org/{doi}' if doi else ''),
        title=clean_text(work.get('title') or work.get('display_name')) or 'Untitled record',
        authors=[a['author']['display_name'] for a in work.get('authorships', [])
                 if (a.get('author') or {}).get('display_name')],
        journal=(location.get('source') or {}).get('display_name'),
        year=work.get('publication_year'), abstract=reconstruct_abstract(work.get('abstract_inverted_index')),
        doi=doi, citations=work.get('cited_by_count'), openAccess=oa.get('is_oa'),
        type=work.get('type') or 'unknown', provider='OpenAlex',
        url=safe_url(location.get('landing_page_url')) or safe_url(work.get('doi')),
        fullTextUrl=safe_url(best.get('pdf_url')) or safe_url(oa.get('oa_url')),
        demo=False,
    )


def normalize_crossref(work):
    doi = normalize_doi(work.get('DOI'))
    dates = (work.get('published') or {}).get('date-parts') or []
    authors = [a.get('name') or ' '.join(filter(None, [a.get('given'), a.get('family')]))
               for a in work.get('author', [])]
    return dict(
        id=f'https://doi.org/{doi.lower()}' if doi else '',
        title=clean_text((work.get('title') or ['Untitled record'])[0]) or 'Untitled record',
        authors=[a for a in authors if a], journal=(work.get('container-title') or [None])[0],
        year=dates[0][0] if dates and dates[0] else None,
        abstract=clean_text(work.get('abstract')), doi=doi,
        citations=work.get('is-referenced-by-count'), openAccess=None,
        type=work.get('type') or 'unknown', provider='Crossref',
        url=safe_url(work.get('URL')) or (f'https://doi.org/{doi}' if doi else None),
        fullTextUrl=None, demo=False,
    )


def deduplicate(papers):
    output, indices, duplicates = [], {}, 0
    for paper in papers:
        doi = normalize_doi(paper.get('doi'))
        key = ('doi', doi.lower()) if doi else ('id', paper['id'])
        if key not in indices:
            indices[key] = len(output)
            output.append(dict(paper))
        else:
            duplicates += 1
            existing = output[indices[key]]
            for field in ('abstract', 'openAccess', 'fullTextUrl', 'journal', 'year', 'citations', 'url'):
                if existing.get(field) is None:
                    existing[field] = paper.get(field)
    return output, duplicates


def rank(paper, query):
    stop = {'the', 'and', 'for', 'with', 'from', 'how', 'does', 'are', 'what', 'during'}
    terms = sorted({t for t in re.findall(r'\w+', query.lower()) if len(t) > 2 and t not in stop})
    title, abstract = paper['title'].lower(), (paper.get('abstract') or '').lower()
    matched = [t for t in terms if t in title or t in abstract]
    denom = len(terms) or 1
    recent = min(1, max(0, 1 - (date.today().year - paper['year']) / 15)) if paper.get('year') else 0
    cited = min(1, math.log10(1 + max(0, paper.get('citations') or 0)) / 4)
    score = round(100 * (.45 * sum(t in title for t in terms) / denom
                         + .25 * sum(t in abstract for t in terms) / denom
                         + .2 * len(matched) / denom + .07 * recent + .03 * cited))
    return {**paper, 'score': score, 'matchedTerms': matched}


def _fetch(provider, options, key='', email=''):
    query, page, start, end, oa, kind = options
    headers = {'Accept': 'application/json', 'User-Agent': 'AxiomResearch/1.0'}
    if provider == 'OpenAlex':
        filters = [f'from_publication_date:{start}-01-01', f'to_publication_date:{end}-12-31']
        if oa:
            filters.append('is_oa:true')
        if kind == 'Review':
            filters.append('type:review')
        elif kind == 'Journal article':
            filters.append('type:article')
        params = dict(search=query, page=page, **{'per-page': 20}, filter=','.join(filters))
        if key:
            headers['Authorization'] = f'Bearer {key}'
        url = 'https://api.openalex.org/works'
    else:
        filters = [f'from-pub-date:{start}-01-01', f'until-pub-date:{end}-12-31']
        if kind == 'Journal article':
            filters.append('type:journal-article')
        params = {'query.bibliographic': query, 'rows': 20, 'offset': (page - 1) * 20, 'filter': ','.join(filters)}
        if email:
            params['mailto'] = email
        url = 'https://api.crossref.org/works'
    try:
        response = requests.get(url, params=params, headers=headers, timeout=(8, 20))
        if response.status_code in (401, 403):
            raise ValueError(f'{provider}: API access needs valid credentials.')
        if response.status_code == 429:
            raise ValueError(f'{provider}: request limit reached. Try again later.')
        response.raise_for_status()
        data = response.json()
        if provider == 'OpenAlex':
            return [normalize_openalex(w) for w in data['results']], int(data['meta']['count'])
        return [normalize_crossref(w) for w in data['message']['items']], int(data['message']['total-results'])
    except (requests.RequestException, KeyError, TypeError) as exc:
        raise ValueError(f'{provider}: unavailable or returned an unexpected response. Try again later.') from exc


def search(query, providers, page=1, start=2000, end=None, oa=False, kind='All', key='', email=''):
    end = end or date.today().year
    if not 2 <= len(query.strip()) <= 500 or not 1900 <= start <= end <= 2100 or not 1 <= page <= 100:
        raise ValueError('Enter a question of 2–500 characters, a valid year range and a page from 1–100.')
    selected = [p for p in ('OpenAlex', 'Crossref') if p in providers]
    if not selected:
        raise ValueError('Select at least one provider.')
    warnings, totals, found, successful = [], {}, [], 0
    results = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        tasks = {pool.submit(_fetch, p, (query.strip(), page, start, end, oa, kind), key, email): p for p in selected}
        for task in as_completed(tasks):
            provider = tasks[task]
            try:
                results[provider] = task.result()
                successful += 1
            except ValueError as exc:
                warnings.append(str(exc))
    for provider in selected:
        if provider in results:
            papers, total = results[provider]
            found.extend(papers)
            totals[provider] = total
    merged, duplicates = deduplicate(found)
    if oa:
        merged = [p for p in merged if p['openAccess'] is True]
    if kind == 'Review':
        merged = [p for p in merged if p['type'] == 'review']
    elif kind == 'Journal article':
        merged = [p for p in merged if p['type'] in ('article', 'journal-article')]
    if 'Crossref' in results and (oa or kind == 'Review'):
        warnings.append('Crossref lacks reliable open-access/review labels here; records without the requested label are excluded.')
    return {'papers': sorted([rank(p, query) for p in merged], key=lambda p: p['score'], reverse=True),
            'warnings': warnings, 'duplicates': duplicates, 'totals': totals,
            'hasMore': any(n > page * 20 for n in totals.values()), 'successful': successful}
