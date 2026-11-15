#!/usr/bin/env python3
"""Answer keys, written once before any run.

  keys.py write KIT     write <keys>/<id>-key.json from the case data and KEYS-HASHES.txt (SHA-256 per key, UTC time on line 1).
                        Refuses to overwrite any key file or the hash file.
  keys.py verify KIT    check the key files against KEYS-HASHES.txt
  keys.py --selftest
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import cases as CS


def hashfile(kit):
    return kit.p('KEYS-HASHES.txt')


def write_keys(kit):
    bad = CS.problems(kit)
    if bad:
        raise SystemExit('keys: case data has problems, fix first:\n  ' + '\n  '.join(bad))
    data = kit.case_data()['cases']
    existing = [c['id'] for c in data if os.path.exists(os.path.join(kit.d('keys'), c['id'] + '-key.json'))]
    if existing or os.path.exists(hashfile(kit)):
        raise SystemExit('keys: refusing to overwrite (exists: %s)' % (', '.join(existing) or 'KEYS-HASHES.txt'))
    lines = ['Keys written %s. SHA-256 of each key file, written before any model reads a case.' % C.utcnow()]
    for c in data:
        path = os.path.join(kit.d('keys'), c['id'] + '-key.json')
        C.write(path, C.jdump({'case': c['id'], 'pages': c['key']}))
        lines.append('%s  %s' % (C.sha_file(path), os.path.basename(path)))
    C.write(hashfile(kit), '\n'.join(lines) + '\n')
    return len(data)


def verify(kit):
    if not os.path.isfile(hashfile(kit)):
        return ['KEYS-HASHES.txt missing']
    bad = []
    for ln in C.read(hashfile(kit)).splitlines()[1:]:
        if not ln.strip():
            continue
        h, name = ln.split(None, 1)
        p = os.path.join(kit.d('keys'), name.strip())
        if not os.path.isfile(p):
            bad.append('missing key file ' + name)
        elif C.sha_file(p) != h:
            bad.append('key changed: ' + name)
    return bad


def selftest():
    t = C.Selftest('keys')
    kp = C.fixture_copy()
    try:
        kit = C.load_kit(kp)
        t.check(write_keys(kit) == 2, 'two keys written')
        first = C.read(hashfile(kit)).splitlines()[0]
        t.check(first.startswith('Keys written ') and 'UTC' in first, 'first line has the UTC time')
        t.check(verify(kit) == [], 'verify clean after write')
        try:
            write_keys(kit)
            t.check(False, 'second write must refuse')
        except SystemExit as e:
            t.check('refusing' in str(e), 'second write refuses')
        p = os.path.join(kit.d('keys'), 'M1-key.json')
        C.write(p, C.read(p).replace('2026-10-15', '2026-10-16'))
        t.check(verify(kit) == ['key changed: M1-key.json'], 'changed key detected')
    finally:
        C.cleanup(kp)
    return t.done()


def main(argv):
    if '--selftest' in argv:
        return selftest()
    if len(argv) < 3 or argv[1] not in ('write', 'verify'):
        print(__doc__)
        return 2
    kit = C.load_kit(argv[2])
    if argv[1] == 'write':
        print('keys written: %d (KEYS-HASHES.txt)' % write_keys(kit))
        return 0
    bad = verify(kit)
    print('keys verify: %s' % ('ok' if not bad else 'FAIL'))
    for b in bad:
        print('  ' + b)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
