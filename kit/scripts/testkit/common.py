"""Shared helpers of the test-kit library (standard library only). Run scripts with: /usr/bin/python3 -I script.py ...

Kit layout: a folder holding kit.json (see kit.schema.json), labels.json, a case-data JSON and entry text. Scripts take the
path of kit.json as an argument; no path is written into code.
"""
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
from difflib import SequenceMatcher
from decimal import Decimal, InvalidOperation

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, 'tests', 'fixtures')
DEFAULT_DIRS = {'cases': 'cases', 'keys': 'keys', 'runs': 'runs', 'scores': 'scores', 'prompts': 'prompts'}
KINDS = ('text', 'number', 'date', 'money', 'list', 'code', 'name', 'label')   # name and label: added for the allergy kit (see ADAPTATIONS below)


def utcnow():
    return dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')


def sha_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def sha_text(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def jload(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def jdump(obj):
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + '\n'


# ---------------------------------------------------------------- kit
class Kit:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.dir = os.path.dirname(self.path)
        self.cfg = jload(self.path)
        self.labels = jload(self.p(self.cfg.get('labels', 'labels.json')))
        self.header = list(self.labels.get('header', []))
        self.pages = self.labels['pages']
        self.dirs = dict(DEFAULT_DIRS)
        self.dirs.update(self.cfg.get('dirs', {}))
        self._plugin = None
        for pg, spec in self.pages.items():
            for lb in spec['labels']:
                if lb.get('kind', 'text') not in KINDS:
                    raise ValueError('bad kind for %s.%s' % (pg, lb['name']))

    def p(self, rel):
        return os.path.join(self.dir, rel)

    def d(self, name):
        return self.p(self.dirs[name])

    def kind(self, page, label):
        for lb in self.pages[page]['labels']:
            if lb['name'] == label:
                return lb.get('kind', 'text')
        return 'text'

    def has_label(self, page, label):
        return page in self.pages and any(lb['name'] == label for lb in self.pages[page]['labels'])

    def case_data(self):
        return jload(self.p(self.cfg['case_data']))

    def key(self, case):
        return jload(os.path.join(self.d('keys'), case + '-key.json'))

    def plugin(self):
        if self._plugin is None and self.cfg.get('plugin'):
            import importlib.util
            spec = importlib.util.spec_from_file_location('kit_plugin', self.p(self.cfg['plugin']))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self._plugin = mod
        return self._plugin


def load_kit(path):
    return Kit(path)


# ---------------------------------------------------------------- text tolerance
MONTHS = {m: i for i, m in enumerate(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october',
                                      'november', 'december'], 1)}
_MN = '|'.join(MONTHS)


def iso_dates(s):
    s = re.sub(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(%s),?\s+(\d{4})\b' % _MN,
               lambda m: '%s-%02d-%02d' % (m.group(3), MONTHS[m.group(2)], int(m.group(1))), s)
    return re.sub(r'\b(%s)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b' % _MN,
                  lambda m: '%s-%02d-%02d' % (m.group(3), MONTHS[m.group(1)], int(m.group(2))), s)


def norm(s):
    """Lower case, one space, no markup stars, no thousands commas, dates in ISO form."""
    s = '' if s is None else str(s)
    s = iso_dates(s.lower().replace('’', "'").replace('‘', "'"))
    s = re.sub(r'[*`]+', ' ', s)
    s = re.sub(r'(?<=\d),(?=\d{3}(?!\d))', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def alnum(s):
    return re.sub(r'[^a-z0-9]', '', norm(s))


def lab(s):
    s = re.sub(r'\([^)]*\)', ' ', s)
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()


ATOM = re.compile(r'\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}|\d+(?:[.\-]\d+)*')
STOPW = {'the', 'and', 'for', 'not', 'one', 'are', 'was', 'any', 'its', 'has'}


def words_ok(actual, expected):
    """Every number, date, time and word (3+ letters) of the expected value appears in the actual value."""
    a, e = norm(actual), norm(expected)
    if not e:
        return not a
    if e == 'none':
        return norm(re.sub(r'\([^)]*\)|\[[^\]]*\]', ' ', str(actual))) == 'none'
    for at in ATOM.findall(e):
        if not re.search(r'(?<![\d])' + re.escape(at) + r'(?![\d])', a):
            return False
    aw = set(re.findall(r'[a-z]{3,}', a))
    for w in re.findall(r'[a-z]{3,}', ATOM.sub(' ', e)):
        if w not in STOPW and w not in aw:
            return False
    return True


def money(s):
    m = re.search(r'-?\d+(?:\.\d+)?', norm(s).replace(' ', ''))
    try:
        return Decimal(m.group(0)) if m else None
    except InvalidOperation:
        return None


def first_date(s):
    m = re.search(r'\d{4}-\d{2}-\d{2}', norm(s))
    return m.group(0) if m else None


def items(s):
    n = norm(re.sub(r'\[[^\]]*\]', ' ', '' if s is None else str(s)))
    return sorted({re.sub(r'\s+', ' ', x).strip() for x in re.split(r'[;,/\n]|\band\b', n) if x.strip()})


# ADAPTATIONS for the allergy kit (the rest of this library is unchanged from the hackathon skill):
#   kind "name"  dish names in any script. Expected value may list aliases separated by " | ". Right if any alias equals the actual
#                value after case, accent and punctuation folding, or is fuzzily equal (ratio >= 0.86), or one contains the other
#                when the shorter has 5+ characters and is at least 70 percent of the longer.
#   kind "label" one of the three allergy labels; only the first line of the actual value is read, then punctuation and case are ignored.
def fold_name(s):
    s = unicodedata.normalize('NFKC', '' if s is None else str(s)).casefold()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c))
    return re.sub(r'[\W_]+', '', s)


def name_ok(actual, expected):
    a = fold_name(actual)
    if not a:
        return False
    for alias in str(expected).split('|'):
        e = fold_name(alias)
        if not e:
            continue
        if a == e:
            return True
        lo, hi = sorted((a, e), key=len)
        if len(lo) >= 5 and len(lo) >= 0.7 * len(hi) and lo in hi:
            return True
        if len(lo) >= 5 and SequenceMatcher(None, a, e).ratio() >= 0.86:
            return True
    return False


def label_ok(actual, expected):
    first = ('' if actual is None else str(actual)).strip().split('\n')[0]
    return alnum(first) == alnum(expected) and alnum(expected) != ''


def field_ok(kind, actual, expected, match=None):
    """Right or wrong for one field. match overrides the kind: text, number, date, money, list, code, exact, name, label."""
    k = match or kind
    if k == 'name':
        return name_ok(actual, expected)
    if k == 'label':
        return label_ok(actual, expected)
    if k in ('money', 'number'):
        a, e = money(actual), money(expected)
        return a is not None and e is not None and a == e
    if k == 'date':
        a, e = first_date(actual), first_date(expected)
        return a is not None and a == e
    if k == 'list':
        if norm(expected) == 'none':
            return norm(actual) == 'none'
        return items(actual) == items(expected)
    if k == 'code':
        return alnum(actual) == alnum(expected) and alnum(expected) != ''
    if k == 'exact':
        return norm(actual) == norm(expected)
    return words_ok(actual, expected)


def split_spec(v):
    """A key field is a string or {"value":..., "group":..., "match":...}."""
    if isinstance(v, dict):
        return v.get('value', ''), v.get('group'), v.get('match')
    return v, None, None


# ---------------------------------------------------------------- reply parsing
LINE = re.compile(r'^\s*(?:[-*•]\s+)?(?:\*\*)?([^:\n*]{2,90}?)(?:\*\*)?\s*:\s*(?:\*\*)?\s*(.*)$')
PAGEL = re.compile(r'^\s*={3,}\s*(?:([\w.\-]+?\.md)\b.*|([\w.\-]+?)\s*=*)\s*$')


def page_name(raw, kit):
    n = re.sub(r'\.md$', '', raw.strip(), flags=re.I).upper()
    n = re.sub(r'-RUN\d+$', '', n)
    for pg, spec in kit.pages.items():
        if n == pg.upper():
            return pg
    for pg, spec in kit.pages.items():
        pre = spec.get('prefix')
        if pre and n.startswith(pre.upper()):
            return pg
    return n


def split_pages(text, kit):
    """-> (status, calls, {page: lines}). Page markers: '=== NAME.md', '=== NAME ===', and (F3 PF1) a line of only '===' followed by a
    line holding the page name."""
    text = re.sub(r'^[ \t]*={3,}[ \t]*\n[ \t]*([\w.\-]+)[ \t]*=*[ \t]*$', r'=== \1', text, flags=re.M)
    pages, cur, name, status, calls = {}, [], None, None, None
    for ln in text.split('\n'):
        m = PAGEL.match(ln)
        if m:
            if name is not None and name not in pages:
                pages[name] = cur
            name, cur = page_name(m.group(1) or m.group(2), kit), []
            continue
        if name is None:
            m1 = re.match(r'\s*\**STATUS\**\s*:\s*\**\s*(PAGES|STOPPED|NO WRITES)', ln, re.I)
            if m1 and status is None:
                status = m1.group(1).upper()
            m2 = re.match(r'\s*\**(?:EXPERT )?CALLS\**\s*:\s*\**\s*(\d+)', ln, re.I)
            if m2 and calls is None:
                calls = int(m2.group(1))
        elif not ln.strip().startswith('```'):
            cur.append(ln)
    if name is not None and name not in pages:
        pages[name] = cur
    return status, calls, pages


def parse_page(kit, name, lines):
    """-> {'header': {label: value}, 'blocks': [{label: value}]}. A page with a 'repeat' label starts a block at that label."""
    spec = kit.pages.get(name, {'labels': []})
    labels = [lb['name'] for lb in spec['labels']]
    known = {lab(x): x for x in kit.header + labels}
    repeat = spec.get('repeat')
    header, blocks, cur, last = {}, [], None, None
    for ln in lines:
        m = LINE.match(ln)
        k = known.get(lab(m.group(1))) if m else None
        if k is None and m:
            kk = lab(m.group(1))
            k = next((v for lk, v in known.items() if kk.startswith(lk + ' ') and len(lk) > 6), None)
        if k is None:
            if last is not None and ln.strip():
                last[0][last[1]] = (last[0][last[1]] + '\n' + ln.strip()).strip()
            continue
        val = m.group(2).strip()
        if k in kit.header and k not in labels:
            header[k] = val
            last = (header, k)
            continue
        if cur is None or (repeat and k == repeat):
            cur = {}
            blocks.append(cur)
        cur.setdefault(k, val)
        last = (cur, k)
    return {'header': header, 'blocks': blocks}


def parse_reply(kit, text):
    status, calls, raw = split_pages(text, kit)
    pages = {n: parse_page(kit, n, ls) for n, ls in raw.items()}
    return status, calls, pages


def known_pages(kit, pages):
    return [n for n in pages if n in kit.pages]


def render_reply(kit, key, status='PAGES', drop=None, change=None):
    """Make a reply text from a key (used by self-tests). drop=(page,label,row); change=(page,label,row,newvalue)."""
    out = ['STATUS: %s' % status, 'CALLS: 3', '']
    for pg, spec in kit.pages.items():
        rows = key['pages'].get(pg)
        if rows is None:
            continue
        out.append('=== %s.md' % pg)
        for hl in kit.header:
            out.append('%s: draft' % hl)
        for i, row in enumerate(rows):
            for lb in spec['labels']:
                n = lb['name']
                if n not in row:
                    continue
                v = split_spec(row[n])[0]
                if drop and drop[:2] == (pg, n) and drop[2] == i:
                    continue
                if change and change[:2] == (pg, n) and change[2] == i:
                    v = change[3]
                out.append('%s: %s' % (n, v))
        out.append('')
    return '\n'.join(out) + '\n'


# ---------------------------------------------------------------- files
def expand(kit, entries):
    """Kit-relative files and folders -> sorted list of kit-relative file paths."""
    out = []
    for e in entries:
        full = kit.p(e)
        if os.path.isdir(full):
            for r, _, fs in os.walk(full):
                for f in fs:
                    out.append(os.path.relpath(os.path.join(r, f), kit.dir).replace(os.sep, '/'))
        elif os.path.isfile(full):
            out.append(e.replace(os.sep, '/'))
    return sorted(set(out))


def fixture_copy(fixture_dir=None):
    """Copy the synthetic mini contest to a new temp folder; returns the kit.json path."""
    tmp = tempfile.mkdtemp(prefix='testkit-selftest-')
    dst = os.path.join(tmp, 'mini')
    shutil.copytree(fixture_dir or FIXTURES, dst, ignore=shutil.ignore_patterns('__pycache__'))
    return os.path.join(dst, 'kit.json')


def cleanup(kit_path):
    shutil.rmtree(os.path.dirname(os.path.dirname(os.path.abspath(kit_path))), ignore_errors=True)


class Selftest:
    def __init__(self, name):
        self.name, self.fails, self.n = name, [], 0

    def check(self, cond, msg):
        self.n += 1
        if not cond:
            self.fails.append(msg)

    def done(self):
        if self.fails:
            print('%s selftest: FAIL (%d of %d)' % (self.name, len(self.fails), self.n))
            for f in self.fails:
                print('  - ' + f)
            return 1
        print('%s selftest: pass (%d checks)' % (self.name, self.n))
        return 0
