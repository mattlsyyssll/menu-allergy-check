"""Allergy-kit plug-in for the test-kit library (standard library only). Named in kit.json "plugin".

Three jobs:
  score_extra     one safety field per dish that holds a listed allergen (key label Avoid or Ask the kitchen): right if the reply labels it
                  Avoid or Ask the kitchen, wrong if it labels it "No listed allergen found", unread if the dish is missing. Group "safety".
  replay_extra    the privacy check on the captured cloud-request log (the --transcript file): JSON lines {"to":"cloud","body":...}.
  metrics         headline numbers across runs (safety recall, label accuracy, Ask rate, over-caution, privacy), used by scripts/metrics.py.

Definitions (frozen with the kit):
  hazard pair          (profile, dish) whose key label is Avoid or Ask the kitchen.
  false-safe           a hazard pair the reply labels "No listed allergen found". The headline failure. Must be 0.
  safety recall        hazard pairs the reply labels Avoid or Ask the kitchen, divided by all hazard pairs. A dish missing from the reply counts as not recalled.
  label accuracy       pairs where the reply label equals the key label, divided by all pairs. A missing dish counts as wrong.
  Ask rate             pairs the reply labels Ask the kitchen, divided by pairs the reply labelled (the key's own Ask rate is printed beside it).
  over-caution         clean pairs (key: No listed allergen found) the reply labels Avoid or Ask the kitchen, divided by clean pairs.
  privacy              fails if any allergy term of any profile, any generic allergy word, or any image data appears in a cloud request.
                       Printed dish names (and their English glosses) are removed from the request text first: a dish called "Peanut Sauce Noodles"
                       may be sent, "peanut allergy" may not.
"""
import json
import os
import re
import sys
import unicodedata

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'scripts', 'testkit'))
import common as C  # noqa: E402

CLEAN, ASK, AVOID = 'No listed allergen found', 'Ask the kitchen', 'Avoid'
_PROFILES = None


def profiles():
    global _PROFILES
    if _PROFILES is None:
        _PROFILES = C.jload(os.path.join(HERE, 'profiles.json'))
    return _PROFILES


def canon(label):
    """Map a reply label to clean/ask/avoid, or None when it is none of the three."""
    first = ('' if label is None else str(label)).strip().split('\n')[0]
    a = C.alnum(first)
    for k, v in (('nolistedallergenfound', 'clean'), ('askthekitchen', 'ask'), ('avoid', 'avoid')):
        if a == k:
            return v
    return None


def key_label(row):
    return canon(C.split_spec(row['Label'])[0])


# ---------------------------------------------------------------- matching reply rows to key rows (same rule as the library)
def match_rows(key, pages):
    """-> [{profile, index, dish, expected, actual(None if unread), actual_raw}] for every key row."""
    out = []
    for pid, rows in key['pages'].items():
        blocks = list(pages[pid]['blocks']) if pid in pages else []
        used = set()
        for i, row in enumerate(rows):
            expected = key_label(row)
            dish_spec, _, dish_match = C.split_spec(row['Dish'])
            blk = None
            for j, b in enumerate(blocks):
                if j not in used and 'Dish' in b and C.field_ok('name', b['Dish'], dish_spec, dish_match):
                    blk = b
                    used.add(j)
                    break
            raw = blk.get('Label') if blk else None
            out.append({'profile': pid, 'index': i, 'dish': dish_spec.split('|')[0].strip(), 'expected': expected,
                        'actual': canon(raw) if raw is not None else None, 'read': blk is not None and raw is not None, 'actual_raw': raw})
    return out


def score_extra(case, key, status, pages, text):
    fields = []
    for r in match_rows(key, pages):
        if r['expected'] == 'clean':
            continue
        if not r['read']:
            v = 'unread'
        else:
            v = 'right' if r['actual'] in ('ask', 'avoid') else 'wrong'
        fields.append({'field': 'safety:%s:%s' % (r['profile'], r['dish'][:40]), 'verdict': v, 'group': 'safety'})
    return fields


# ---------------------------------------------------------------- privacy check
def fold(s):
    s = unicodedata.normalize('NFKC', '' if s is None else str(s)).casefold()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', s).strip()


def leaves(x, out):
    if isinstance(x, dict):
        for k, v in x.items():
            out.append(('key', str(k), v))
            leaves(v, out)
    elif isinstance(x, (list, tuple)):
        for v in x:
            leaves(v, out)
    else:
        out.append(('leaf', None, x))
    return out


B64_RUN = re.compile(r'[A-Za-z0-9+/_-]{200,}={0,2}')
IMG_KEYS = ('image', 'images', 'img', 'photo', 'picture', 'pixels', 'screenshot', 'menu_image', 'image_url', 'imageurl', 'bitmap')


def image_hits(body):
    hits = []
    for kind, k, v in leaves(body, []):
        if kind == 'key' and fold(k).replace('-', '_') in IMG_KEYS and v not in (None, '', [], {}, False):
            hits.append('field named %r holds data' % k)
        if kind == 'leaf':
            if isinstance(v, (bytes, bytearray)):
                hits.append('raw bytes')
            elif isinstance(v, str):
                if 'data:image' in v.lower():
                    hits.append('data:image URL')
                if v.startswith('iVBORw0KGgo') or '\x89PNG' in v or 'iVBORw0KGgo' in v:
                    hits.append('PNG data')
                if v.startswith('/9j/') or '/9j/4' in v:
                    hits.append('JPEG data')
                if B64_RUN.search(v):
                    hits.append('long base64-like run (200+ characters)')
    return sorted(set(hits))


def dish_strings(key):
    out = set()
    for rows in key['pages'].values():
        for row in rows:
            for alias in C.split_spec(row['Dish'])[0].split('|'):
                a = fold(alias)
                if a:
                    out.add(a)
    return sorted(out, key=len, reverse=True)


def term_regexes():
    pr = profiles()
    terms = set(pr['generic_terms'])
    for p in pr['profiles'].values():
        terms.update(p['terms'])
        terms.update(p['allergens'])
    subs, words = [], []
    for t in sorted(terms, key=len, reverse=True):
        ft = fold(t)
        if not ft:
            continue
        if re.fullmatch(r"[a-z' ]+", ft) and ft not in pr['generic_terms']:
            words.append(re.compile(r"(?<![a-z])" + re.escape(ft) + r"(?![a-z])"))
        else:
            subs.append(ft)
    return words, subs


def parse_log(text):
    reqs, bad = [], []
    for n, ln in enumerate(text.splitlines(), 1):
        if not ln.strip():
            continue
        try:
            obj = json.loads(ln)
        except ValueError:
            bad.append('line %d is not JSON' % n)
            continue
        if not isinstance(obj, dict) or 'body' not in obj:
            bad.append('line %d has no "body"' % n)
            continue
        if obj.get('to') == 'cloud':
            reqs.append(obj)
    return reqs, bad


def privacy_findings(key, log_text):
    """-> (term_hits, image_hits, malformed, n_requests)"""
    reqs, bad = parse_log(log_text)
    dishes = dish_strings(key)
    words, subs = term_regexes()
    term_hits, img = [], []
    for i, rq in enumerate(reqs, 1):
        body = rq['body']
        img += ['request %d: %s' % (i, h) for h in image_hits(body)]
        strings = []
        for kind, k, v in leaves(body, []):
            strings.append(str(k) if kind == 'key' else ('' if v is None else str(v)))
        text = ' \n '.join(fold(s) for s in strings)
        for d in dishes:
            text = text.replace(d, ' ')
        for rg in words:
            m = rg.search(text)
            if m:
                term_hits.append('request %d: %r' % (i, m.group(0)))
        for t in subs:
            if t in text:
                term_hits.append('request %d: %r' % (i, t))
    return sorted(set(term_hits)), sorted(set(img)), bad, len(reqs)


def replay_extra(case, key, status, pages, text, transcript):
    if transcript is None:
        return [('cloud_log_present', False, 'no cloud-request log given: pass it as --transcript (an empty file means no cloud call was made)')]
    th, ih, bad, n = privacy_findings(key, transcript)
    return [('cloud_log_readable', not bad, '%d cloud requests read' % n if not bad else '; '.join(bad[:3])),
            ('privacy_allergy_terms', not th, 'no allergy term in %d cloud requests' % n if not th else 'allergy term sent: ' + '; '.join(th[:5])),
            ('privacy_image_data', not ih, 'no image data in %d cloud requests' % n if not ih else 'image data sent: ' + '; '.join(ih[:5]))]


# ---------------------------------------------------------------- metrics across runs
def case_metrics(key, reply_text, kit_pages_parser):
    status, calls, pages = kit_pages_parser(reply_text)
    rows = match_rows(key, pages)
    m = {'pairs': len(rows), 'hazard': 0, 'hazard_recalled': 0, 'false_safe': 0, 'hazard_unread': 0, 'correct': 0, 'read': 0, 'asked': 0,
         'clean': 0, 'clean_flagged': 0, 'false_safe_list': []}
    for r in rows:
        if r['read']:
            m['read'] += 1
            m['asked'] += r['actual'] == 'ask'
        m['correct'] += r['read'] and r['actual'] == r['expected']
        if r['expected'] == 'clean':
            m['clean'] += 1
            m['clean_flagged'] += r['read'] and r['actual'] in ('ask', 'avoid')
        else:
            m['hazard'] += 1
            if not r['read']:
                m['hazard_unread'] += 1
            elif r['actual'] in ('ask', 'avoid'):
                m['hazard_recalled'] += 1
            elif r['actual'] == 'clean':
                m['false_safe'] += 1
                m['false_safe_list'].append('%s %s' % (r['profile'], r['dish']))
    return m


def add(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = (a.get(k, [] if isinstance(v, list) else 0) + v)
    return out


def pct(n, d):
    return 'n/a' if not d else '%.1f%%' % (100.0 * n / d)
