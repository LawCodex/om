#!/usr/bin/env python3
"""Convert qanoon.om posts (see om_fetch.py) to LawCodex Markdown.

Usage: om_convert.py RAW_DIR REPO_DIR
"""
import collections, datetime, glob, html as htmlmod, json, os, re, sys
from bs4 import BeautifulSoup, NavigableString, Tag, Comment

TODAY = datetime.date.today().isoformat()
AR_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
MONTHS = {m: i + 1 for i, m in enumerate(
    ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'])}
MONTHS.update({'ابريل': 4, 'إبريل': 4, 'اغسطس': 8})
# category id -> (directory, type, year subdirectories?)
CATS = {
    2: ('royal-decrees', 'royal_decree', True),
    152: ('consolidated-laws', 'consolidated_law', True),
    344: ('consolidated-regulations', 'consolidated_regulation', True),
    311: ('legacy-laws', 'legacy_law', False),
    133: ('royal-orders', 'royal_order', True),
    3: ('ministerial-decisions', 'ministerial_decision', True),
    1: ('ministerial-decisions', 'ministerial_decision', True),
    313: ('covid-19-committee-decisions', 'committee_decision', False),
    367: ('circulars', 'circular', False),
}
SECTION_RANK = [('الكتاب', 0), ('القسم', 1), ('الباب', 2), ('الفصل', 3), ('الفرع', 4), ('المبحث', 5)]


def clean(s):
    return re.sub(r'[ \t\u00a0\u200b\r]+', ' ', s).strip()


def yq(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ') + '"'


def inline(node):
    out = []
    for c in node.children:
        if isinstance(c, Comment):
            continue
        if isinstance(c, NavigableString):
            out.append(re.sub(r'\s+', ' ', str(c)))
        elif isinstance(c, Tag):
            n = c.name.lower()
            if n == 'br':
                out.append('\n')
            elif n in ('script', 'style', 'img', 'svg'):
                continue
            elif n in ('strong', 'b'):
                parts = [p.strip() for p in inline(c).split('\n')]
                out.append('\n'.join(f'**{p}**' if p else '' for p in parts))
            elif n == 'table':
                out.append('\n\n' + table(c) + '\n\n')
            elif n in ('p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'tr', 'blockquote', 'figure'):
                out.append('\n\n' + inline(c) + '\n\n')
            else:
                out.append(inline(c))
    return ''.join(out)


def table(t):
    rows = []
    for tr in t.find_all('tr'):
        cells = tr.find_all(['td', 'th'], recursive=False)
        if any(c.get('rowspan') or c.get('colspan') for c in cells):
            for tag in t.find_all(True):
                tag.attrs = {k: v for k, v in tag.attrs.items() if k in ('rowspan', 'colspan')}
            return re.sub(r'\s+', ' ', str(t))
        rows.append([clean(inline(c)).replace('\n', '<br>').replace('|', '\\|').replace('**', '') for c in cells])
    rows = [r for r in rows if r]
    if not rows:
        return ''
    n = max(len(r) for r in rows)
    rows = [r + [''] * (n - len(r)) for r in rows]
    md = ['| ' + ' | '.join(rows[0]) + ' |', '|' + ' --- |' * n]
    md += ['| ' + ' | '.join(r) + ' |' for r in rows[1:]]
    return '\n'.join(md)


def lines_of(node):
    ls = [clean(l.replace('****', '')) for l in inline(node).split('\n')]
    return [l for l in ls if l and l not in ('**', '****')]


def heading_text(node):
    """If node is a heading or a centred, fully bold paragraph, return its plain text."""
    if node.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
        return ' — '.join(clean(l.replace('**', '')) for l in inline(node).split('\n') if clean(l.replace('**', ''))) or None
    style = (node.get('style') or '').replace(' ', '')
    centred = 'text-align:center' in style or 'has-text-align-center' in (node.get('class') or [])
    if not centred:
        return None
    txt = clean(node.get_text(' ', strip=True))
    bold = clean(' '.join(b.get_text(' ', strip=True) for b in node.find_all(['strong', 'b'])))
    if not txt or bold != txt:
        return None
    return ' — '.join(clean(l.replace('**', '')) for l in inline(node).split('\n') if clean(l.replace('**', '')))


def section_rank(t):
    for k, r in SECTION_RANK:
        if t.startswith(k):
            return r
    return None


def body(content):
    s = BeautifulSoup(content, 'lxml')
    root = s.body or s
    blocks = [c for c in root.find_all(recursive=False)]
    meta = {}
    # first paragraph = links (consolidated text / PDF / English)
    if blocks and blocks[0].name == 'p' and blocks[0].find('a', class_=['law', 'pdf-link', 'decree-link']):
        for a in blocks[0].find_all('a', href=True):
            cls = a.get('class') or []
            if 'pdf-link' in cls:
                meta['pdf'] = a['href']
            elif 'decree-link' in cls:
                meta['english'] = a['href']
            elif 'law' in cls:
                meta['consolidated'] = a['href']
            a.decompose()
        if not clean(blocks[0].get_text(' ', strip=True)):
            blocks = blocks[1:]
    heads = {}
    for b in blocks:
        if b.name in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            t = heading_text(b)
            if t:
                heads[id(b)] = t
    ranks = sorted({r for t in heads.values() for r in [section_rank(t)] if r is not None})
    lvl = {r: min(2 + i, 5) for i, r in enumerate(ranks)}
    cur = 1
    out = []
    for b in blocks:
        t = heads.get(id(b))
        if t:
            if t.startswith('المادة') or t.startswith('مادة'):
                out.append('#' * min(cur + 1, 6) + ' ' + t)
                continue
            r = section_rank(t)
            if r is not None:
                cur = lvl[r]
                out.append('#' * cur + ' ' + t)
                continue
        if b.name == 'table' or (b.name == 'figure' and b.find('table')):
            out.append(table(b if b.name == 'table' else b.find('table')))
            continue
        ls = lines_of(b)
        if ls:
            out.append('\n\n'.join(ls))
    return '\n\n'.join(out), meta


def num_year(title):
    t = title.translate(AR_DIGITS)
    m = re.search(r'رقم\s*(\d+)\s*/\s*(\d{2,4})', t)
    if not m:
        return None, None
    y = m.group(2)
    if len(y) == 2:
        y = ('19' if int(y) > 30 else '20') + y
    return m.group(1), y


def issued(text):
    t = text.translate(AR_DIGITS).replace('ـ', '')
    k = t.rfind('صدر في')
    if k >= 0:
        t = t[k:]
    m = re.search(r'الموافق\s*:?\s*(\d{1,2})\s*(?:من\s*)?(\S+?)\s*(?:سنة\s*)?(\d{4})', t)
    try:
        if m and m.group(2) in MONTHS:
            return datetime.date(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1))).isoformat()
        m = re.search(r'الموافق\s*:?\s*(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})', t)
        if m:
            return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
    except ValueError:
        return None
    return None


def gazette(text):
    t = text.translate(AR_DIGITS)
    m = re.search(r'(?:ملحق\s*)?عدد\s*الجريدة\s*الرسمية\s*رقم\s*\((\d+)\)\s*الصادر\s*في\s*(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})', t)
    if m:
        return f'{"Supplement to " if "ملحق" in m.group(0) else ""}Official Gazette No. {m.group(1)}, {m.group(4)}-{int(m.group(3)):02d}-{int(m.group(2)):02d}'
    return None


def main():
    raw, repo = sys.argv[1], sys.argv[2]
    posts = {}
    for f in sorted(glob.glob(os.path.join(raw, 'posts', '*.json'))):
        for p in json.load(open(f)):
            posts[p['id']] = p
    counts = collections.Counter()
    basic = None
    for p in posts.values():
        cats = [c for c in p['categories'] if c in CATS]
        if not cats:
            continue
        cat = cats[0]
        d, typ, by_year = CATS[cat]
        slug = re.sub(r'[^a-z0-9-]+', '-', p['slug'].lower()).strip('-')
        title = clean(htmlmod.unescape(BeautifulSoup(p['title']['rendered'], 'lxml').get_text(' ')))
        b, meta = body(p['content']['rendered'])
        if len(b) < 20:
            print('EMPTY', p['slug'], file=sys.stderr)
            continue
        num, year = num_year(title)
        m = re.match(r'[a-z]+((?:19|20)\d\d)', slug)
        y = (m.group(1) if m else None) or year or p['date'][:4]
        rel = d
        if slug in ('l2021006',) or (slug == 'rd2021006' and 'l2021006' not in {x['slug'] for x in posts.values()}):
            rel, typ = 'basic-statute', 'basic_statute'
        elif by_year:
            rel = f'{d}/{y}'
        fm = ['---', f'title: {yq(title)}', f'identifier: {yq(p["slug"])}', f'type: {typ}',
              'jurisdiction: om', 'language: ar']
        if num:
            fm += [f'number: {yq(num)}', f'year: {year}']
        dt = issued(BeautifulSoup(p['content']['rendered'], 'lxml').get_text(''))
        if dt and not '1900' < dt < '2100':
            dt = None
        if dt:
            fm.append(f'date: {dt}')
        if cat in (152, 344):
            fm.append(f'last_amended: {p["modified"][:10]}')
        fm.append('status: unknown')
        g = gazette(BeautifulSoup(p['content']['rendered'], 'lxml').get_text(' '))
        if g:
            fm.append(f'gazette: {yq(g)}')
        if meta.get('consolidated'):
            fm.append(f'consolidated_version: {yq(meta["consolidated"])}')
        if meta.get('pdf'):
            fm.append(f'gazette_pdf: {yq(meta["pdf"])}')
        if meta.get('english'):
            fm.append(f'english_translation: {yq(meta["english"])}')
        fm += [f'source: {yq(p["link"])}', f'source_modified: {p["modified"][:10]}', f'retrieved: {TODAY}', '---']
        path = os.path.join(repo, 'ar', rel, slug + '.md')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(fm) + '\n\n# ' + title + '\n\n' + b.strip() + '\n')
        counts[rel.split('/')[0]] += 1
    for k in sorted(counts):
        print(k, counts[k])


if __name__ == '__main__':
    main()
