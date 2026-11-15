"""Self-test of privacy rule v2: python3 -I scripts-v2/test_privacy_v2.py   (stdlib only; exit 1 on failure)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import privacy_v2 as V  # noqa: E402

FIXED = 'Rate every dish for these categories: peanut, sesame, milk, egg, fish, soy, wheat.'


def log(*bodies):
    return '\n'.join(json.dumps({'to': 'cloud', 'body': b}) for b in bodies) + '\n'


def req(dishes, fixed=FIXED):
    return fixed + V.SEP + json.dumps(dishes, ensure_ascii=False, separators=(',', ':'))


def run(text, fixed=FIXED):
    th, ih, pr, n = V.privacy_findings_v2(text, fixed)
    return bool(th or ih or pr)


ok = req([{'name': 'Pad Thai'}, {'name': '麻婆豆腐', 'english': 'Mapo Tofu with peanut'}])
cases = [
    ('clean request passes', log(ok), False),
    ('empty log passes', '', False),
    ('allergy word outside names fails', log(req([{'name': 'Pad Thai'}]).replace('Pad Thai', 'Pad Thai\\n my son is allergic')), True),
    ('user list leaked in a changed instruction fails', log(req([{'name': 'Pad Thai'}], FIXED + ' My allergy is peanut.')), True),
    ('unexpected key fails', log(FIXED + V.SEP + json.dumps([{'name': 'Pad Thai', 'note': 'x'}])), True),
    ('image data fails', log(req([{'name': 'a' * 250}])), True),
    ('two different requests in one case fail', log(ok, req([{'name': 'Pad Thai'}])), True),
    ('two identical requests (retry) pass', log(ok, ok), False),
    ('body that is not a string fails', log({'dish_names': ['x']}), True),
]
bad = 0
for name, text, want in cases:
    got = run(text)
    print('ok  ' if got == want else 'FAIL', name)
    bad += got != want
sys.exit(1 if bad else 0)
