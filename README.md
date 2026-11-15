# Menu allergy check for a parent

[![checks](https://github.com/mattlsyyssll/menu-allergy-check/actions/workflows/check.yml/badge.svg)](https://github.com/mattlsyyssll/menu-allergy-check/actions/workflows/check.yml)

Live app: https://menu-allergy-check.vercel.app

A parent photographs a restaurant menu, often in a language they do not read. The app marks every dish against the child's allergy list and writes the question to ask the waiter, in the menu's language and the parent's language.

The allergy list and the photo never leave the device. Only the dish names on the menu go to a cloud model, in one request per menu, to look up typical recipes.

## Numbers first

Held-out set 2 (8 new menus, 91 dishes, 4 allergy lists, 364 answers, run once, keys published):

| Measure | Result |
|---|---|
| Hazard answers marked "Ask the kitchen" or "Avoid" (safety recall) | 90.7% (127 of 140) |
| Label accuracy against the key | 81.6% |
| Over-caution (clean answers marked Ask or Avoid) | 16.1% |
| Menus with no allergy list or image data in the cloud request (privacy rule v2) | 8 of 8 |
| Cloud requests that timed out | 0 |
| Run time, 8 menus | 6 min 29 s |

Development menus (16 menus used while building; the app was tuned on these):

| Build | Safety recall | False-safe | Label accuracy |
|---|---|---|---|
| app-build2 | 82.2% | 34 | 87.7% |
| app-build3 | 95.5% | 6 | 84.9% |
| app-build4 | 97.5% | 1 | 82.1% |
| app-build5 | 92.6% | 0 | 75.0% |

## The honest table

Three labels exist and none says "safe": **No listed allergen found**, **Ask the kitchen**, **Avoid**. A false-safe is a dish that holds a listed allergen and is marked "No listed allergen found". The goal is 0. The app does not reach it on new menus.

| Measure | Final 1 (held-out set 1, build after round 3) | Final 2 (held-out set 2, build 6) |
|---|---|---|
| Safety recall | 81.9% (77/94) | 90.7% (127/140) |
| False-safe | 9 | 9 |
| Hazard dishes missing | 8 | 4 |
| Label accuracy | 71.0% | 81.6% |
| Over-caution | 20.0% | 16.1% |
| Privacy v1 (frozen rule) | 6/8 | 0/8 (fixed 19-allergen instruction) |
| Privacy v2 (documented copy) | n/a | 8/8 |

The 9 false-safe labels of final 2 (letters are the allergy lists A to D):
- M26 Brisket Plate (B), Baby Back Ribs (C, D), Bacon BBQ Burger (D)
- M27 Ayam Penyet (A), Tempe Mendoan (A), Soto Ayam (D)
- M30 Taramosalata (B)
- M32 Baguette Tradition (B)

Facts that limit these numbers:
- Held-out set 1 was spent and M24 was partly exposed. A person building the app printed the header and first rows of M24's key before the run. No change was made from it. Without M24 the set-1 result is recall 81.1% (73 of 90), 9 false-safe, label accuracy 70.1%.
- Both held-out sets are spent. The keys of both are published, so they can no longer test an app that has seen them.
- The development result overfitted: build 4 scored 97.5% recall with 1 false-safe on the development menus, then 81.9% with 9 false-safe on set 1. Round 4 then changed the cloud step to rate every dish for all 19 allergen categories; set 2 scored 90.7%.
- Privacy v1 fails the final 2 run because the fixed cloud instruction names all 19 allergen categories for every user. Privacy v2 is a documented copy of the checker that removes that fixed text, then runs the same checks. Both numbers are published (`kit/scripts-v2/README.md`). The request is identical for every allergy list; that is tested in `app/tests/pipeline.test.ts`.
- The final 1 privacy result (6 of 8) holds two flags caused by translated dish names in the request, a defect of the v1 checker (`kit/KIT-NOTES.md`).
- One run of final 1 (M21) hung once; a rerun completed in 31.5 s. Both are recorded.
- Menus are rendered from text, not photographed. Answer keys are one person's reading of public allergen pages (FDA, FARE, Allergy and Anaphylaxis Australia); no allergist reviewed them. Facts marked UNVERIFIED in `kit/ANSWER-KEYS.md` use general cooking knowledge.
- The marks are not a guarantee. Always ask the kitchen, and carry prescribed medicine.

## Privacy rule
- The allergy list stays in this browser (`localStorage`). It is never uploaded.
- The menu photo is read on the device. It is never uploaded.
- The only data sent to the cloud is the dish names on the menu (printed and English) and one fixed instruction, the same for every user, in one request per menu. The "What left this device" panel shows the exact text.
- No analytics, no accounts, no server of our own.
- How the work is split between device and cloud: `app/DESIGN.md`.

## Run the app
Needs Node 22.12 or newer, and desktop Chrome with the built-in model (Prompt API with image input).
```
cd app
npm ci
cp .env.example .env.local   # optional: add Firebase config to turn the cloud step on
npm run dev                  # http://localhost:5173
npm test
npm run build
```
With no Firebase config the app runs the on-device part only and shows "Cloud step: off". Firebase setup is in `app/README.md`. No Firebase config is stored in this repository.

## Re-score the kit with no model
Needs Python 3 only. It runs offline.
```
cd kit
python3 -I tests/run_tests.py                       # last line: KIT TESTS PASS (37 run, 0 failed, 0 errors, 0 skipped)
python3 -I scripts/testkit/keys.py verify kit.json  # first line: keys verify: ok
python3 -I scripts/testkit/freeze.py check kit.json # first line: freeze check ok: every frozen file and key matches its hash
python3 -I scripts/metrics.py kit.json --out /tmp/m.md && diff /tmp/m.md scores/METRICS.md
```
No output from `diff` means the re-score equals the saved scores. All commands are in `kit/README.md`. GitHub runs them on every change.

## Folders
| Folder | What it holds |
|---|---|
| `app/` | The web app: source, tests, build files. |
| `kit/` | Menus, answer keys and hashes, saved runs and scores, scorer, both held-out sets. |

## License
MIT, see `LICENSE`.
