#!/usr/bin/env python3
"""Save runs and write the results.

  runs.py save KIT CASE MODEL REPLY.txt [--transcript T.txt]
      Checks the frozen hashes first (refuses if not frozen or if anything changed). Copies the reply (and transcript) to
      <runs>/MODEL/CASE.reply.txt, scores it once and runs the no-model check once (<scores>/score and <scores>/replay).
      Refuses if that case and model were already saved.
  runs.py results KIT   write <scores>/RESULTS.md, strict count first
  runs.py --selftest
"""
import glob
import os
import shutil
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import freeze as F
import keys as K
import replay as RP
import score as SC


def save(kit, case, model, reply, transcript=None):
    bad = F.verify(kit)
    if bad:
        raise SystemExit('save: refusing, frozen files do not match: ' + '; '.join(bad[:5]))
    if case not in [c['id'] for c in kit.case_data()['cases']]:
        raise SystemExit('save: unknown case ' + case)
    rd = os.path.join(kit.d('runs'), model)
    dst = os.path.join(rd, case + '.reply.txt')
    if os.path.exists(dst):
        raise SystemExit('save: refusing, %s %s was already saved (one score per run)' % (model, case))
    text = C.read(reply)
    tr = C.read(transcript) if transcript else None
    res = SC.score_text(kit, case, text)
    rep = RP.replay_text(kit, case, text, tr)
    os.makedirs(rd, exist_ok=True)
    shutil.copyfile(reply, dst)
    if transcript:
        shutil.copyfile(transcript, os.path.join(rd, case + '.transcript.txt'))
    res['model'] = model
    C.write(os.path.join(kit.d('scores'), 'score', model, case + '.json'), C.jdump(res))
    C.write(os.path.join(kit.d('scores'), 'replay', model, case + '.json'),
            C.jdump({'case': case, 'model': model, 'pass': all(o for _, o, _ in rep), 'rules': [{'name': n, 'ok': o, 'detail': d} for n, o, d in rep]}))
    return res, rep


def results(kit):
    runs = [C.jload(p) for p in sorted(glob.glob(os.path.join(kit.d('scores'), 'score', '*', '*.json')))]
    rep = {(r['model'], r['case']): r for r in (C.jload(p) for p in sorted(glob.glob(os.path.join(kit.d('scores'), 'replay', '*', '*.json'))))}
    n, right = len(runs), sum(r['class'] == 'right' for r in runs)
    out = ['# Results', '',
           'Strict count: %d of %d runs right (a run is right only if every checked field is right).' % (right, n), '']
    models = sorted({r['model'] for r in runs})
    out += ['| Model | Runs | Right (strict) | Fields right | Fields wrong | Fields unread | No-model check passed |', '|---|---|---|---|---|---|---|']
    for m in models:
        rs = [r for r in runs if r['model'] == m]
        rp = sum(1 for r in rs if rep.get((m, r['case']), {}).get('pass'))
        out.append('| %s | %d | %d of %d | %d | %d | %d | %d of %d |' % (
            m, len(rs), sum(r['class'] == 'right' for r in rs), len(rs), sum(r['right'] for r in rs), sum(r['wrong'] for r in rs),
            sum(r['unread'] for r in rs), rp, len(rs)))
    groups = sorted({g for r in runs for g in r['groups']})
    if groups:
        out += ['', 'Partial measures (key-declared groups, fields right of fields checked):', '', '| Group | ' + ' | '.join(models) + ' |', '|---|' + '---|' * len(models)]
        for g in groups:
            cells = []
            for m in models:
                v = [r['groups'][g] for r in runs if r['model'] == m and g in r['groups']]
                cells.append('%d of %d' % (sum(x['right'] for x in v), sum(sum(x.values()) for x in v)))
            out.append('| %s | %s |' % (g, ' | '.join(cells)))
    out += ['', '## Runs', '', '| Model | Case | Class | Right | Wrong | Unread | No-model check |', '|---|---|---|---|---|---|---|']
    for r in runs:
        rp = rep.get((r['model'], r['case']))
        out.append('| %s | %s | %s | %d | %d | %d | %s |' % (r['model'], r['case'], r['class'], r['right'], r['wrong'], r['unread'],
                                                         'not run' if rp is None else ('pass' if rp['pass'] else 'fail')))
    miss = [(r['model'], r['case'], f) for r in runs for f in r['fields'] if f['verdict'] != 'right']
    out += ['', '## Misses (every field not right)', '']
    out += ['- %s %s: %s row %d %s: %s' % (m, c, f['page'], f['row'] + 1, f['label'], f['verdict']) for m, c, f in miss] or ['none']
    C.write(os.path.join(kit.d('scores'), 'RESULTS.md'), '\n'.join(out) + '\n')
    return right, n


def selftest():
    t = C.Selftest('runs')
    kp = C.fixture_copy()
    try:
        kit = C.load_kit(kp)
        try:
            save(kit, 'M1', 'm', kp)
            t.check(False, 'save before freeze must refuse')
        except SystemExit as e:
            t.check('not frozen' in str(e), 'save refuses before freeze')
        K.write_keys(kit)
        F.do_freeze(kit)
        key = kit.key('M1')
        rp = os.path.join(os.path.dirname(kp), 'm1.reply.txt')
        C.write(rp, C.render_reply(kit, key))
        res, rep = save(kit, 'M1', 'model-a', rp)
        t.check(res['class'] == 'right' and os.path.isfile(os.path.join(kit.d('runs'), 'model-a', 'M1.reply.txt')), 'first save is scored and copied')
        try:
            save(kit, 'M1', 'model-a', rp)
            t.check(False, 'second save must refuse')
        except SystemExit as e:
            t.check('already saved' in str(e), 'second save of the same run refuses')
        C.write(rp, C.render_reply(kit, key, change=('SUMMARY', 'Total', 0, '5.00 CAD')))
        tp = os.path.join(os.path.dirname(kp), 't.txt')
        C.write(tp, 'READ cases/M1/files/IMG_1.png.txt\n')
        res, rep = save(kit, 'M1', 'model-b', rp, tp)
        t.check(res['class'] == 'wrong' and os.path.isfile(os.path.join(kit.d('runs'), 'model-b', 'M1.transcript.txt')), 'wrong run saved with transcript')
        r, n = results(kit)
        text = C.read(os.path.join(kit.d('scores'), 'RESULTS.md'))
        t.check((r, n) == (1, 2) and text.splitlines()[2].startswith('Strict count: 1 of 2'), 'strict count first: %s' % text.splitlines()[2])
        t.check('SUMMARY row 1 Total: wrong' in text and 'money' in text, 'misses and groups listed')
        C.write(kit.p('entry/SKILL.md'), 'changed after the freeze\n')
        try:
            save(kit, 'M2', 'model-a', rp)
            t.check(False, 'save after a frozen-file change must refuse')
        except SystemExit as e:
            t.check('do not match' in str(e), 'save refuses on a frozen-hash change')
    finally:
        C.cleanup(kp)
    return t.done()


def main(argv):
    if '--selftest' in argv:
        return selftest()
    if len(argv) >= 6 and argv[1] == 'save':
        kit = C.load_kit(argv[2])
        tr = argv[argv.index('--transcript') + 1] if '--transcript' in argv else None
        res, rep = save(kit, argv[3], argv[4], argv[5], tr)
        print(SC.line(res))
        print('\n'.join(RP.lines_of(rep)))
        return 0
    if len(argv) >= 3 and argv[1] == 'results':
        right, n = results(C.load_kit(argv[2]))
        print('Strict count: %d of %d runs right (RESULTS.md written)' % (right, n))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
