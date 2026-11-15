#!/usr/bin/env python3
"""Key-to-entry trace: the pre-freeze gate. Finds every key field the entry never asks for or forbids.

  trace.py KIT [--out TRACE.md]    exit 1 if any field is "no support" or "conflict"; last line: TRACE done: ...
  trace.py --selftest

For every key field type (page + label, across all cases) it looks for the label in the page templates file and the rule words in
the entry text, and checks the key values against forbidden values in the rules file.
  supported        the label is in the page templates and has a hint after the colon, or a rule word is in the entry text
  under-specified  the label is in the page templates, no hint, no rule word: the host may write another form than the key
  no support       the label is not in the page templates (the host is never asked for it)
  conflict         a key value is forbidden by an entry rule (rules file)
kit.json: "entry": {"templates": file, "text": [files], "rules": file}. labels.json labels may carry "rule_words": [..]
(default: the words of the label name). rules file: {"forbid": [{"page", "label", "value", "rule"}]}.
Output form follows the Scam Response KEY-TRACE: non-supported rows first (field, verdict, entry quote, key value, one-line fix), then supported.
"""
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C


def template_sections(kit, text):
    names = list(kit.pages)
    secs, cur = {}, None
    for ln in text.splitlines():
        head = re.sub(r'[#*`\s]|\.md$', '', ln.strip(), flags=re.I).upper()
        hit = next((n for n in names if head == n.upper()), None)
        if hit:
            cur = hit
            secs[cur] = []
        elif cur:
            secs[cur].append(ln)
    return secs


def find_label(lines, label):
    pat = re.compile(r'^\s*(?:[-*•]\s+)?(?:\*\*)?' + re.escape(label) + r'(?:\*\*)?\s*:(.*)$', re.I)
    for ln in lines:
        m = pat.match(ln)
        if m:
            return m.group(1).strip()
    return None


def quote(entry, words):
    for sent in re.split(r'(?<=[.!?])\s+|\n+', entry):
        if any(re.search(r'\b' + re.escape(w) + r'\b', sent, re.I) for w in words):
            return ' '.join(sent.split()[:25])
    return ''


def trace(kit):
    ent = kit.cfg['entry']
    tpl = C.read(kit.p(ent['templates']))
    secs = template_sections(kit, tpl)
    text = '\n'.join(C.read(kit.p(f)) for f in ent.get('text', []))
    rules = C.jload(kit.p(ent['rules'])).get('forbid', []) if ent.get('rules') else []
    data = kit.case_data()['cases']
    rows = []
    for pg, spec in kit.pages.items():
        for lb in spec['labels']:
            name = lb['name']
            vals = [(c['id'], C.split_spec(r[name])[0]) for c in data for r in c['key'].get(pg, []) if name in r]
            if not vals:
                continue
            example = '%s: %s' % vals[0]
            hint = find_label(secs.get(pg) or tpl.splitlines(), name)
            words = lb.get('rule_words') or [w for w in re.findall(r'[A-Za-z]{4,}', name)] or re.findall(r'[A-Za-z]{3,}', name)
            q = quote(text, words) if text else ''
            forb = [f for f in rules if f.get('page') == pg and f.get('label') == name
                    and any(C.alnum(f['value']) and C.alnum(f['value']) in C.alnum(v) for _, v in vals)]
            if forb:
                verdict, fix = 'conflict', 'change the key or the entry rule (%s)' % forb[0].get('rule', 'rule')
                q = forb[0].get('rule', q)
            elif hint is None:
                verdict, fix = 'no support', 'add "%s:" with its form to the %s page template, or drop the key field' % (name, pg)
            elif hint or q:
                verdict, fix = 'supported', ''
                q = q or hint
            else:
                verdict, fix = 'under-specified', 'add the value form as a hint after "%s:" in the page template, or widen the scorer for this field' % name
            rows.append({'field': '%s.%s' % (pg, name), 'verdict': verdict, 'quote': q, 'key': example, 'fix': fix})
    return rows


def render(kit, rows):
    cnt = {v: sum(r['verdict'] == v for r in rows) for v in ('supported', 'under-specified', 'no support', 'conflict')}
    out = ['# Key-to-entry trace', '',
           'Kit: %s. %d field types. Supported %d. Under-specified %d. No support %d. Conflict %d.' % (
               kit.cfg.get('name', ''), len(rows), cnt['supported'], cnt['under-specified'], cnt['no support'], cnt['conflict']), '',
           '## Non-supported fields', '', '| # | Field | Verdict | Entry quote | Key value (example) | One-line fix |', '|---|---|---|---|---|---|']
    bad = [r for r in rows if r['verdict'] != 'supported']
    for i, r in enumerate(bad, 1):
        out.append('| %d | %s | %s | %s | %s | %s |' % (i, r['field'], r['verdict'].upper(), r['quote'] or '-', r['key'], r['fix']))
    if not bad:
        out.append('| - | none | | | | |')
    out += ['', '## Supported fields', '', '| Field | Entry quote | Key value (example) |', '|---|---|---|']
    out += ['| %s | %s | %s |' % (r['field'], r['quote'] or '-', r['key']) for r in rows if r['verdict'] == 'supported']
    out += ['', 'TRACE done: %d field types; supported %d; under-specified %d; no support %d; conflict %d' % (
        len(rows), cnt['supported'], cnt['under-specified'], cnt['no support'], cnt['conflict'])]
    return '\n'.join(out) + '\n', cnt


def selftest():
    t = C.Selftest('trace')
    kp = C.fixture_copy()
    try:
        kit = C.load_kit(kp)
        rows = trace(kit)
        text, cnt = render(kit, rows)
        t.check(len(rows) == 10, '10 labels traced: %d' % len(rows))
        t.check(cnt['no support'] == 0 and cnt['conflict'] == 0, 'base fixture has no gate failure: %s' % cnt)
        t.check(cnt['under-specified'] == 2 and cnt['supported'] == 8, 'two under-specified (Items count, Reference): %s' % cnt)
        t.check(text.index('## Non-supported') < text.index('## Supported'), 'non-supported rows come first')
        # conflict
        C.write(kit.p('entry/rules.json'), C.jdump({'forbid': [{'page': 'ITEMS', 'label': 'Code', 'value': 'B1', 'rule': 'B1 is never allowed on a screenshot'}]}))
        rows = trace(kit)
        t.check(any(r['verdict'] == 'conflict' and r['field'] == 'ITEMS.Code' for r in rows), 'forbidden key value is a conflict')
        # no support
        C.write(kit.p('entry/rules.json'), '{"forbid": []}')
        tpl = C.read(kit.p('entry/page-templates.md')).replace('Tags: (list)\n', '')
        C.write(kit.p('entry/page-templates.md'), tpl)
        rows = trace(kit)
        t.check(any(r['verdict'] == 'no support' and r['field'] == 'ITEMS.Tags' for r in rows), 'label missing from the template is no support')
        _, cnt = render(kit, rows)
        t.check(cnt['no support'] == 1, 'exit-code driver: no support counted')
    finally:
        C.cleanup(kp)
    return t.done()


def main(argv):
    if '--selftest' in argv:
        return selftest()
    if len(argv) < 2:
        print(__doc__)
        return 2
    kit = C.load_kit(argv[1])
    text, cnt = render(kit, trace(kit))
    if '--out' in argv:
        C.write(argv[argv.index('--out') + 1], text)
        print(text.strip().splitlines()[-1])
    else:
        print(text)
    return 1 if cnt['no support'] or cnt['conflict'] else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
