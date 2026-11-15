#!/usr/bin/env python3
"""No-model checks of a finished reply, driven by kit.json "replay" rules.

  replay.py check KIT CASE REPLY.txt [--transcript T.txt] [--json OUT]    first line: PASS|FAIL pages_parsed: N pages parsed
  replay.py --selftest

Built in: pages_parsed (parsed pages above 0 unless STATUS is STOPPED or NO WRITES; never a vacuous pass), required_pages (every page
of the key is present when STATUS is PAGES).
kit.json "replay": {"rules": [...], "allowed_reads": [prefixes]} with rules
  {"rule": "same_fact", "name": n, "refs": [[PAGE, LABEL], ...], "kind": "money|date|text|code|list|number"}   the same fact on every page that holds it (at least two)
  {"rule": "copy_hashes", "page": PAGE}   every line of the page with a 64-hex SHA-256 holds exactly two equal ones (a listed copy)
allowed_reads (needs --transcript): no read of a path outside these folders. A transcript line reads 'READ path', 'cat path', 'ls path',
'head path', 'tail path' or 'open path'.
A contest plug-in may define replay_extra(case, key, status, pages, text, transcript) -> [(name, ok, detail)].
"""
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C

HEX = re.compile(r'(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])')
READ = re.compile(r'^\s*(?:READ|read|cat|ls|head|tail|open)\s+(\S+)', re.M)


def check_same_fact(kit, rule, pages):
    vals = []
    for pg, lb in rule['refs']:
        p = pages.get(pg)
        if p and p['blocks'] and lb in p['blocks'][0]:
            vals.append((pg, p['blocks'][0][lb]))
    name = rule.get('name', 'same_fact')
    if len(vals) < 2:
        return (name, False, 'fewer than two places state the fact (%d found)' % len(vals))
    kind = rule.get('kind', 'text')
    base = vals[0][1]
    bad = [pg for pg, v in vals[1:] if not C.field_ok(kind, v, base, 'exact' if kind == 'text' else None)]
    return (name, not bad, 'equal on %s' % ', '.join(p for p, _ in vals) if not bad else 'differs from %s on %s' % (vals[0][0], ', '.join(bad)))


def check_copy_hashes(kit, rule, raw_pages):
    pg = rule['page']
    name = 'copy_hashes:' + pg
    lines = [ln for ln in raw_pages.get(pg, []) if HEX.search(ln)]
    bad = [ln.strip()[:60] for ln in lines if len(HEX.findall(ln)) != 2 or HEX.findall(ln)[0].lower() != HEX.findall(ln)[1].lower()]
    return (name, not bad, '%d listed copies, all with two equal hashes' % len(lines) if not bad else 'unequal or missing hash: ' + '; '.join(bad))


def check_reads(kit, transcript, allowed):
    out = []
    for p in READ.findall(transcript):
        q = os.path.normpath(p)
        rel = os.path.relpath(q, kit.dir) if os.path.isabs(q) else q
        if rel.startswith('..') or not any(rel.startswith(os.path.normpath(a)) for a in allowed):
            out.append(p)
    return ('allowed_reads', not out, 'all reads inside the allowed folders' if not out else 'read outside: ' + ', '.join(out[:5]))


def replay_text(kit, case, text, transcript=None, key=None):
    key = key or kit.key(case)
    status, calls, pages = C.parse_reply(kit, text)
    _, _, raw = C.split_pages(text, kit)
    known = C.known_pages(kit, pages)
    res = []
    stopped = status in ('STOPPED', 'NO WRITES')
    res.append(('pages_parsed', len(known) > 0 or stopped, '%d pages parsed' % len(known)))
    if not stopped:
        miss = [pg for pg in key['pages'] if pg not in pages]
        res.append(('required_pages', not miss, 'all key pages present' if not miss else 'missing: ' + ', '.join(miss)))
    rc = kit.cfg.get('replay', {})
    for rule in rc.get('rules', []):
        if rule['rule'] == 'same_fact':
            res.append(check_same_fact(kit, rule, pages))
        elif rule['rule'] == 'copy_hashes':
            res.append(check_copy_hashes(kit, rule, raw))
        else:
            res.append((rule.get('name', rule['rule']), False, 'unknown rule ' + rule['rule']))
    if transcript is not None and rc.get('allowed_reads'):
        res.append(check_reads(kit, transcript, rc['allowed_reads']))
    plug = kit.plugin()
    if plug and hasattr(plug, 'replay_extra'):
        res.extend(plug.replay_extra(case, key, status, pages, text, transcript))
    return res


def lines_of(res):
    return ['%s %s: %s' % ('PASS' if ok else 'FAIL', n, d) for n, ok, d in res]


def selftest():
    t = C.Selftest('replay')
    import keys as K
    kp = C.fixture_copy()
    try:
        kit = C.load_kit(kp)
        K.write_keys(kit)
        key = kit.key('M1')
        ok = C.render_reply(kit, key)
        h = 'a' * 64
        good = ok.replace('Item: Voicemail', 'Item: Voicemail\n' + 'copy ' + h + ' ' + h, 1)
        r = replay_text(kit, 'M1', good)
        t.check(all(x[1] for x in r), 'good reply passes: %s' % lines_of(r))
        t.check(r[0][0] == 'pages_parsed' and '3 pages' in r[0][2], 'first line is pages_parsed with the count')
        z = replay_text(kit, 'M1', 'STATUS: PAGES\nnothing\n')
        t.check(not z[0][1], 'zero pages must fail (no vacuous pass)')
        t.check(replay_text(kit, 'M1', 'STATUS: STOPPED\nstopped early\n')[0][1], 'a STOPPED reply may have zero pages')
        r = replay_text(kit, 'M1', C.render_reply(kit, key, change=('LETTER', 'Total', 0, '999.00 CAD')))
        t.check(any(n == 'total_same_everywhere' and not o for n, o, _ in r), 'same fact differing across pages fails')
        r = replay_text(kit, 'M1', ok.replace('=== LETTER.md', '=== OTHER.md'))
        t.check(any(n == 'total_same_everywhere' and not o for n, o, _ in r) and any(n == 'required_pages' and not o for n, o, _ in r), 'missing page fails the same-fact and required-page rules')
        bad = ok.replace('Item: Voicemail', 'Item: Voicemail\ncopy ' + h + ' ' + 'b' * 64, 1)
        r = replay_text(kit, 'M1', bad)
        t.check(any(n.startswith('copy_hashes') and not o for n, o, _ in r), 'unequal copy hashes fail')
        r = replay_text(kit, 'M1', good, transcript='READ cases/M1/files/IMG_1.png.txt\nREAD entry/SKILL.md\n')
        t.check(all(x[1] for x in r), 'reads inside allowed folders pass')
        r = replay_text(kit, 'M1', good, transcript='READ cases/M1/files/IMG_1.png.txt\nREAD keys/M1-key.json\n')
        t.check(any(n == 'allowed_reads' and not o for n, o, _ in r), 'read of the key fails')
        r = replay_text(kit, 'M1', good, transcript='cat ../outside.txt\n')
        t.check(any(n == 'allowed_reads' and not o for n, o, _ in r), 'path above the kit fails')
        t.check(any(n == 'plugin_status_line' for n, _, _ in r), 'plug-in rule ran')
    finally:
        C.cleanup(kp)
    return t.done()


def main(argv):
    if '--selftest' in argv:
        return selftest()
    if len(argv) < 5 or argv[1] != 'check':
        print(__doc__)
        return 2
    kit = C.load_kit(argv[2])
    tr = C.read(argv[argv.index('--transcript') + 1]) if '--transcript' in argv else None
    res = replay_text(kit, argv[3], C.read(argv[4]), tr)
    print('\n'.join(lines_of(res)))
    if '--json' in argv:
        C.write(argv[argv.index('--json') + 1], C.jdump([{'name': n, 'ok': o, 'detail': d} for n, o, d in res]))
    return 0 if all(o for _, o, _ in res) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
