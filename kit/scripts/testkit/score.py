#!/usr/bin/env python3
"""Label-driven scorer.

  score.py score KIT CASE REPLY.txt [--json OUT]   one line: CASE: right|wrong (r right, w wrong, u unread); groups on the next lines
  score.py --selftest

For each field of the answer key the verdict is right, wrong or unread (page or label not found). The class is right only if every
field is right (strict). Tolerances: spaces, case, thousands commas, date forms, list order, bold marks, page-split forms
('=== NAME.md', '=== NAME ===', a line '===' then the page name). Partial measures come from key-declared "group" names.
A contest plug-in module named in kit.json ("plugin") may define score_extra(case, key, status, pages, text) -> [{field, verdict, group}].
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C


def score_text(kit, case, text, key=None):
    key = key or kit.key(case)
    status, calls, pages = C.parse_reply(kit, text)
    fields = []

    def add(page, row, label, verdict, group=None):
        fields.append({'page': page, 'row': row, 'label': label, 'verdict': verdict, 'group': group})

    for pg, rows in key['pages'].items():
        parsed = pages.get(pg)
        blocks = list(parsed['blocks']) if parsed else []
        used = set()
        repeat = kit.pages[pg].get('repeat')
        for i, row in enumerate(rows):
            blk = None
            if repeat and repeat in row:
                ev = C.split_spec(row[repeat])[0]
                for j, b in enumerate(blocks):
                    if j not in used and repeat in b and C.field_ok(kit.kind(pg, repeat), b[repeat], ev, C.split_spec(row[repeat])[2]):
                        blk = b
                        used.add(j)
                        break
            elif i < len(blocks):
                blk = blocks[i]
            for label, spec in row.items():
                ev, group, match = C.split_spec(spec)
                if blk is None or label not in blk:
                    add(pg, i, label, 'unread', group)
                else:
                    add(pg, i, label, 'right' if C.field_ok(kit.kind(pg, label), blk[label], ev, match) else 'wrong', group)
    plug = kit.plugin()
    if plug and hasattr(plug, 'score_extra'):
        for x in plug.score_extra(case, key, status, pages, text):
            add('plugin', 0, x['field'], x['verdict'], x.get('group'))
    r = sum(f['verdict'] == 'right' for f in fields)
    w = sum(f['verdict'] == 'wrong' for f in fields)
    u = sum(f['verdict'] == 'unread' for f in fields)
    groups = {}
    for f in fields:
        if f['group']:
            g = groups.setdefault(f['group'], {'right': 0, 'wrong': 0, 'unread': 0})
            g[f['verdict']] += 1
    return {'case': case, 'class': 'right' if fields and w == 0 and u == 0 else 'wrong', 'right': r, 'wrong': w, 'unread': u,
            'pages_parsed': len(C.known_pages(kit, pages)), 'groups': groups, 'fields': fields}


def line(res):
    s = '%s: %s (%d right, %d wrong, %d unread)' % (res['case'], res['class'], res['right'], res['wrong'], res['unread'])
    for g, v in sorted(res['groups'].items()):
        s += '\n  group %s: %d of %d right' % (g, v['right'], sum(v.values()))
    return s


def selftest():
    t = C.Selftest('score')
    import keys as K
    kp = C.fixture_copy()
    try:
        kit = C.load_kit(kp)
        K.write_keys(kit)
        key = kit.key('M1')
        ok = C.render_reply(kit, key)
        res = score_text(kit, 'M1', ok)
        t.check(res['class'] == 'right' and res['wrong'] == 0 and res['unread'] == 0, 'correct reply is right: %s' % line(res))
        t.check(res['right'] == 14, 'M1 has 13 key fields plus 1 plugin field (14): got %d' % res['right'])
        t.check(res['groups'].get('money', {}).get('right') == 2, 'group money counted')
        # one wrong of each kind
        cases = [('SUMMARY', 'What happened', 0, 'Nothing here'), ('SUMMARY', 'Date of event', 0, '2026-10-16'),
                 ('SUMMARY', 'Total', 0, '1250.00 CAD'), ('SUMMARY', 'Items count', 0, '3'), ('ITEMS', 'Tags', 0, 'fraud'),
                 ('ITEMS', 'Code', 1, 'B2'), ('LETTER', 'Reference', 0, 'REF-78')]
        for pg, lb, row, new in cases:
            r = score_text(kit, 'M1', C.render_reply(kit, key, change=(pg, lb, row, new)))
            t.check(r['wrong'] == 1 and r['unread'] == 0 and r['class'] == 'wrong', 'wrong %s.%s detected: %s' % (pg, lb, line(r)))
        # tolerances
        tol = C.render_reply(kit, key, change=('SUMMARY', 'Total', 0, '**1,200.00  cad**'))
        tol = tol.replace('fraud; urgent', 'URGENT, Fraud').replace('Date of event: 2026-10-15', 'Date of event: 15 October 2026')
        tol = tol.replace('Reference: REF-77', 'Reference: ref 77')
        r = score_text(kit, 'M1', tol)
        t.check(r['class'] == 'right', 'tolerances (commas, case, list order, date form, code spacing): %s' % line(r))
        # unread
        r = score_text(kit, 'M1', C.render_reply(kit, key, drop=('SUMMARY', 'Total', 0)))
        t.check(r['unread'] == 1 and r['wrong'] == 0 and r['class'] == 'wrong', 'dropped label is unread: %s' % line(r))
        # row order and repeat blocks
        sw = ok.replace('Item: Voicemail', 'Item: TMP').replace('Item: Screenshot', 'Item: Voicemail').replace('Item: TMP', 'Item: Screenshot')
        r = score_text(kit, 'M1', sw)
        t.check(r['wrong'] + r['unread'] > 0, 'swapped rows are not scored right')
        # zero pages
        r = score_text(kit, 'M1', 'STATUS: PAGES\nno pages here\n')
        t.check(r['pages_parsed'] == 0 and r['unread'] == 13 and r['class'] == 'wrong', 'zero-page reply: all unread, class wrong')
        # page-split forms
        for form in ('=== SUMMARY.md ===', '===\nSUMMARY.md', '=== SUMMARY'):
            variant = ok.replace('=== SUMMARY.md', form, 1)
            r = score_text(kit, 'M1', variant)
            t.check(r['class'] == 'right', 'page split form %r parsed' % form)
        # plugin
        r = score_text(kit, 'M1', ok + '\npassword\n')
        t.check(any(f['page'] == 'plugin' and f['verdict'] == 'wrong' for f in r['fields']), 'plugin check can fail the class')
    finally:
        C.cleanup(kp)
    return t.done()


def main(argv):
    if '--selftest' in argv:
        return selftest()
    if len(argv) < 5 or argv[1] != 'score':
        print(__doc__)
        return 2
    kit = C.load_kit(argv[2])
    res = score_text(kit, argv[3], C.read(argv[4]))
    print(line(res))
    if '--json' in argv:
        C.write(argv[argv.index('--json') + 1], C.jdump(res))
    return 0 if res['class'] == 'right' else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
