#!/usr/bin/env python3
"""Case folders from a case-data JSON.

  cases.py build KIT [--out DIR]   write <cases>/<id>/{experts,person,files}/ and <prompts>/<id>.txt
  cases.py check KIT               validate the case data against labels.json; the folders on disk must equal a fresh build
  cases.py --selftest

Case data (kit.json "case_data"): {"cases": [{"id", "title", "prompt", "steps": [{"step": n, "expert": name, "reply": text}],
"person": {file: text}, "served": {file: text}, "key": {PAGE: [ {label: value | {"value","group","match"}} ]}}]}
Stored expert or tool replies are returned for the step, person answers are what the person says, served files are what a file
read returns. Nothing here is contest specific.
"""
import filecmp
import os
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C


def build(kit, out_cases=None, out_prompts=None):
    out_cases = out_cases or kit.d('cases')
    out_prompts = out_prompts or kit.d('prompts')
    n = 0
    for c in kit.case_data()['cases']:
        base = os.path.join(out_cases, c['id'])
        for s in c.get('steps', []):
            C.write(os.path.join(base, 'experts', 's%02d-%s.txt' % (s['step'], s['expert'])), s['reply'].rstrip('\n') + '\n')
            n += 1
        for name, text in c.get('person', {}).items():
            C.write(os.path.join(base, 'person', name), text.rstrip('\n') + '\n')
            n += 1
        for name, text in c.get('served', {}).items():
            C.write(os.path.join(base, 'files', name), text.rstrip('\n') + '\n')
            n += 1
        C.write(os.path.join(out_prompts, c['id'] + '.txt'), c['prompt'].rstrip('\n') + '\n')
        n += 1
    return n


def problems(kit):
    """Structure problems of the case data (empty list = fine)."""
    out, seen = [], set()
    for c in kit.case_data()['cases']:
        cid = c.get('id')
        if not cid or cid in seen:
            out.append('case id missing or repeated: %r' % cid)
        seen.add(cid)
        if not c.get('prompt'):
            out.append('%s: no prompt' % cid)
        steps = [s['step'] for s in c.get('steps', [])]
        if steps != sorted(steps) or len(steps) != len(set(steps)):
            out.append('%s: steps not in order or repeated' % cid)
        key = c.get('key')
        if not key:
            out.append('%s: no key' % cid)
            continue
        for pg, rows in key.items():
            if pg not in kit.pages:
                out.append('%s: key page %s is not in labels.json' % (cid, pg))
                continue
            for i, row in enumerate(rows):
                for lb in row:
                    if not kit.has_label(pg, lb):
                        out.append('%s: key label %s.%s is not in labels.json' % (cid, pg, lb))
    return out


def check(kit):
    out = problems(kit)
    tmp = tempfile.mkdtemp(prefix='cases-check-')
    try:
        build(kit, os.path.join(tmp, 'cases'), os.path.join(tmp, 'prompts'))
        for name, real in (('cases', kit.d('cases')), ('prompts', kit.d('prompts'))):
            if not os.path.isdir(real):
                out.append('%s folder missing: run build' % name)
                continue
            dc = filecmp.dircmp(os.path.join(tmp, name), real)
            stack = [dc]
            while stack:
                d = stack.pop()
                for x in d.left_only:
                    out.append('%s: not on disk: %s/%s' % (name, os.path.relpath(d.right, kit.dir), x))
                for x in d.right_only:
                    out.append('%s: not in case data: %s/%s' % (name, os.path.relpath(d.right, kit.dir), x))
                for x in d.diff_files:
                    out.append('%s: differs: %s/%s' % (name, os.path.relpath(d.right, kit.dir), x))
                stack.extend(d.subdirs.values())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def selftest():
    t = C.Selftest('cases')
    kp = C.fixture_copy()
    try:
        kit = C.load_kit(kp)
        t.check(problems(kit) == [], 'fixture case data has problems: %s' % problems(kit))
        n = build(kit)
        t.check(n == 8 and os.path.isfile(os.path.join(kit.d('cases'), 'M1', 'experts', 's01-files.txt')), 'build wrote the expert reply')
        t.check(check(kit) == [], 'check after build is not clean: %s' % check(kit))
        C.write(os.path.join(kit.d('cases'), 'M2', 'person', 'step1-answer.txt'), 'changed\n')
        r = check(kit)
        t.check(any('differs' in x for x in r), 'edited case file not detected')
        C.write(os.path.join(kit.d('cases'), 'M2', 'files', 'extra.txt'), 'x\n')
        t.check(any('not in case data' in x for x in check(kit)), 'extra file not detected')
        d = C.jload(kit.p('case-data.json'))
        d['cases'][0]['key']['SUMMARY'][0]['Nope'] = 'x'
        C.write(kit.p('case-data.json'), C.jdump(d))
        t.check(any('Nope' in x for x in problems(kit)), 'key label missing from labels.json not detected')
    finally:
        C.cleanup(kp)
    return t.done()


def main(argv):
    if '--selftest' in argv:
        return selftest()
    if len(argv) < 3 or argv[1] not in ('build', 'check'):
        print(__doc__)
        return 2
    kit = C.load_kit(argv[2])
    if argv[1] == 'build':
        out = argv[argv.index('--out') + 1] if '--out' in argv else None
        n = build(kit, os.path.join(out, 'cases') if out else None, os.path.join(out, 'prompts') if out else None)
        print('cases %d, files written %d' % (len(kit.case_data()['cases']), n))
        return 0
    r = check(kit)
    print('cases check: %s' % ('ok' if not r else '%d problems' % len(r)))
    for x in r:
        print('  ' + x)
    return 1 if r else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
