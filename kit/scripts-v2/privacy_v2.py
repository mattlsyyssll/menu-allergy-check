"""Privacy rule v2 for the menu allergy kit (copy-and-change of allergy_plugin.privacy_findings; the frozen file is imported, not edited).

Round-4 app design: ONE cloud request per menu = a FIXED instruction (names all 19 allergen categories, identical for every user)
+ "\\n\\nDishes:\\n" + JSON list of {"name", "english"?}. The frozen rule flags the category words in the fixed instruction.

Rule v2, per case:
  1. every request body must be a string = FIXED + "\\n\\nDishes:\\n" + JSON array of objects whose only keys are name / english (strings).
     Any other shape fails (a field we cannot classify could carry anything).
  2. FIXED must be byte-identical in every request of every case of the run, and, when a source file is given
     (cloud-instruction-<model>.txt, dumped from the app's CLOUD_INSTRUCTION), byte-identical to it.
  3. the fixed text and the dish names / English names the app sent are removed; the rest must hold no allergy term (frozen term lists,
     profiles.json) and the whole body no image data (frozen image_hits).
  4. all requests of one case must be byte-identical (retries and the 4 lists share one payload). A case with 2 requests that differ fails.
"""
import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
KITDIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(KITDIR, 'scripts', 'testkit'))
sys.path.insert(0, KITDIR)
import allergy_plugin as P  # noqa: E402  (frozen, read only)

SEP = '\n\nDishes:\n'


def split_request(body):
    """-> (fixed, dishes list, problems). fixed is everything before the first SEP."""
    if not isinstance(body, str):
        return None, [], ['body is not a string (%s)' % type(body).__name__]
    i = body.find(SEP)
    if i < 0:
        return None, [], ['no "Dishes:" section']
    fixed, rest = body[:i], body[i + len(SEP):]
    try:
        dishes = json.loads(rest)
    except ValueError:
        return fixed, [], ['dish section is not JSON']
    if not isinstance(dishes, list):
        return fixed, [], ['dish section is not a list']
    probs = []
    for d in dishes:
        if not isinstance(d, dict) or not set(d) <= {'name', 'english'} or 'name' not in d or not all(isinstance(v, str) for v in d.values()):
            probs.append('dish entry with unexpected shape: %s' % json.dumps(d, ensure_ascii=False)[:80])
    return fixed, dishes, probs


def derive_instruction(texts):
    """First request of the run (texts: transcript texts in case order) -> fixed text, or None."""
    for t in texts:
        reqs, _ = P.parse_log(t)
        for r in reqs:
            fixed, _, _ = split_request(r['body'])
            if fixed is not None:
                return fixed
    return None


def privacy_findings_v2(log_text, fixed, run_fixed_seen=None):
    """-> (term_hits, image_hits, problems, n_requests). `fixed` = the accepted fixed instruction (str)."""
    reqs, bad = P.parse_log(log_text)
    words, subs = P.term_regexes()
    terms, img, probs = [], [], list(bad)
    bodies = []
    for i, rq in enumerate(reqs, 1):
        body = rq['body']
        bodies.append(json.dumps(body, sort_keys=True))
        img += ['request %d: %s' % (i, h) for h in P.image_hits(body)]
        f, dishes, pr = split_request(body)
        probs += ['request %d: %s' % (i, x) for x in pr]
        if f is None:
            continue
        if f != fixed:
            probs.append('request %d: fixed instruction differs from the run\'s fixed text' % i)
        if run_fixed_seen is not None:
            run_fixed_seen.add(f)
        names = set()
        for d in dishes if not pr else []:
            for k in ('name', 'english'):
                if d.get(k):
                    names.add(P.fold(d[k]))
        text = ' \n '.join(P.fold(s) for s in [body[len(f):]])  # fixed text removed (its identity was checked above)
        for n in sorted(names, key=len, reverse=True):
            text = text.replace(n, ' ')
        for rg in words:
            m = rg.search(text)
            if m:
                terms.append('request %d: %r' % (i, m.group(0)))
        for t in subs:
            if t in text:
                terms.append('request %d: %r' % (i, t))
    if len(set(bodies)) > 1:
        probs.append('requests of this case differ from each other (%d distinct)' % len(set(bodies)))
    return sorted(set(terms)), sorted(set(img)), probs, len(reqs)
