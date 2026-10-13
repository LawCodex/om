#!/usr/bin/env python3
"""Fetch Omani legislation from qanoon.om through its public WordPress REST API.

Usage: om_fetch.py RAW_DIR
  RAW_DIR/categories.json
  RAW_DIR/posts/<category>_<page>.json   pages of 50 posts (with rendered content)
"""
import json, os, sys, time
import requests

UA = 'LawCodex/1.0 (+https://github.com/LawCodex)'
API = 'https://qanoon.om/wp-json/wp/v2'
# categories collected (see README): royal decrees, ministerial decisions, high orders, amended
# (consolidated) laws, legacy laws, amended regulations, circulars, Covid-19 committee decisions,
# uncategorized. Skipped: gazette issue indexes (131), treaties (156), fatwas (349), rulings (327).
CATS = [2, 3, 133, 152, 311, 344, 367, 313, 1]
FIELDS = 'id,date,modified,slug,link,title,content,categories,tags'
S = requests.Session()
S.headers['User-Agent'] = UA


def get(url, params):
    delay = 5
    for attempt in range(10):
        try:
            r = S.get(url, params=params, timeout=180)
            if r.status_code == 200:
                return r
            if r.status_code == 400:  # past the last page
                return None
            print('  HTTP', r.status_code, r.url, file=sys.stderr, flush=True)
        except requests.RequestException as e:
            print('  ERR', type(e).__name__, url, file=sys.stderr, flush=True)
        time.sleep(delay)
        delay = min(delay * 2, 300)
    raise SystemExit('giving up on ' + url)


def main():
    raw = sys.argv[1]
    os.makedirs(os.path.join(raw, 'posts'), exist_ok=True)
    cats = get(f'{API}/categories', {'per_page': 100}).json()
    json.dump(cats, open(os.path.join(raw, 'categories.json'), 'w'), ensure_ascii=False)
    for cat in CATS:
        page, total = 1, None
        while total is None or page <= total:
            out = os.path.join(raw, 'posts', f'{cat}_{page:04d}.json')
            if os.path.exists(out) and total is not None:
                page += 1
                continue
            r = get(f'{API}/posts', {'categories': cat, 'per_page': 50, 'page': page, '_fields': FIELDS,
                                     'orderby': 'id', 'order': 'asc'})
            if r is None:
                break
            total = int(r.headers.get('X-WP-TotalPages', 1))
            open(out, 'w').write(r.text)
            print('cat', cat, 'page', page, '/', total, flush=True)
            page += 1
            time.sleep(1)


if __name__ == '__main__':
    main()
