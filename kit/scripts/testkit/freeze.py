#!/usr/bin/env python3
"""Freeze the files a score depends on, then prove they did not change.

  freeze.py freeze KIT   write the hash file named in kit.json "freeze" (UTC time on line 1, then 'sha256  path' per file).
                         Refuses if a run exists in the runs folder or if the hash file exists.
  freeze.py verify KIT   list every file that changed, vanished or was added since the freeze; exit 1 if any
  freeze.py check KIT    verify, plus the key hashes (keys.py verify); one line; exit 1 if either fails
  freeze.py --selftest
kit.json: "freeze": {"files": [kit-relative files or folders], "hashfile": "FROZEN-HASHES.txt"}
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import keys as K


def hashfile(kit):
    return kit.p(kit.cfg['freeze'].get('hashfile', 'FROZEN-HASHES.txt'))


def runs_exist(kit):
    d = kit.d('runs')
    return os.path.isdir(d) and any(fs for _, _, fs in os.walk(d))


def do_freeze(kit):
    if runs_exist(kit):
        raise SystemExit('freeze: refusing, a run already exists in %s' % kit.dirs['runs'])
    if os.path.exists(hashfile(kit)):
        raise SystemExit('freeze: refusing, %s already exists' % os.path.basename(hashfile(kit)))
    files = C.expand(kit, kit.cfg['freeze']['files'])
    if not files:
        raise SystemExit('freeze: no files to freeze')
    lines = ['Frozen %s. sha256  path (relative to the kit folder)' % C.utcnow()]
    lines += ['%s  %s' % (C.sha_file(kit.p(f)), f) for f in files]
    C.write(hashfile(kit), '\n'.join(lines) + '\n')
    return len(files)


def verify(kit):
    if not os.path.isfile(hashfile(kit)):
        return ['not frozen: %s missing' % os.path.basename(hashfile(kit))]
    saved = {}
    for ln in C.read(hashfile(kit)).splitlines()[1:]:
        if ln.strip():
            h, p = ln.split(None, 1)
            saved[p.strip()] = h
    bad = []
    for p, h in saved.items():
        if not os.path.isfile(kit.p(p)):
            bad.append('vanished: ' + p)
        elif C.sha_file(kit.p(p)) != h:
            bad.append('changed: ' + p)
    for p in C.expand(kit, kit.cfg['freeze']['files']):
        if p not in saved:
            bad.append('added after freeze: ' + p)
    return bad


def selftest():
    t = C.Selftest('freeze')
    kp = C.fixture_copy()
    try:
        kit = C.load_kit(kp)
        K.write_keys(kit)
        t.check(verify(kit)[0].startswith('not frozen'), 'verify before freeze says not frozen')
        n = do_freeze(kit)
        t.check(n >= 5, 'froze %d files' % n)
        t.check(C.read(hashfile(kit)).splitlines()[0].startswith('Frozen ') and 'UTC' in C.read(hashfile(kit)).splitlines()[0], 'UTC time line')
        t.check(verify(kit) == [], 'verify clean')
        try:
            do_freeze(kit)
            t.check(False, 'second freeze must refuse')
        except SystemExit as e:
            t.check('refusing' in str(e), 'second freeze refuses')
        C.write(kit.p('entry/SKILL.md'), 'changed\n')
        t.check(verify(kit) == ['changed: entry/SKILL.md'], 'change detected: %s' % verify(kit))
        C.write(kit.p('entry/new.md'), 'x\n')
        t.check('added after freeze: entry/new.md' in verify(kit), 'added file detected')
        os.remove(hashfile(kit))
        C.write(os.path.join(kit.d('runs'), 'm', 'M1.reply.txt'), 'x\n')
        try:
            do_freeze(kit)
            t.check(False, 'freeze with a run must refuse')
        except SystemExit as e:
            t.check('a run already exists' in str(e), 'freeze refuses when a run exists')
    finally:
        C.cleanup(kp)
    return t.done()


def main(argv):
    if '--selftest' in argv:
        return selftest()
    if len(argv) < 3 or argv[1] not in ('freeze', 'verify', 'check'):
        print(__doc__)
        return 2
    kit = C.load_kit(argv[2])
    if argv[1] == 'freeze':
        print('froze %d files: %s' % (do_freeze(kit), os.path.basename(hashfile(kit))))
        return 0
    bad = verify(kit)
    if argv[1] == 'check':
        bad += K.verify(kit)
        print('freeze check %s' % ('ok: every frozen file and key matches its hash' if not bad else 'FAIL'))
    else:
        print('freeze verify: %s' % ('ok' if not bad else '%d differences' % len(bad)))
    for b in bad:
        print('  ' + b)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
