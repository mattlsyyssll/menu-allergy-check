# Menu allergy check for a parent

[![checks](https://github.com/mattlsyyssll/menu-allergy-check/actions/workflows/check.yml/badge.svg)](https://github.com/mattlsyyssll/menu-allergy-check/actions/workflows/check.yml)

Live app: https://menu-allergy-check.vercel.app

A parent photographs a restaurant menu, often in a language they do not read. The app marks every dish against the child's allergy list and writes the question to ask the waiter, in the menu's language and the parent's language.

The allergy list and the photo never leave the device. Only the dish names on the menu go to a cloud model, in one request per menu, to look up typical recipes.

## Numbers first

Newest held-out test: 8 menus the app had never seen, 96 dishes, 4 allergy lists, answer keys written before the run.

| Measure | Result |
|---|---|
| Dishes holding a listed allergen that were marked "Ask the kitchen" or "Avoid" | 91.7% (122 of 133), up from 81.9% on the first held-out test |
| Labels that match the answer key | 82.3% |
| Clean dishes marked "Ask the kitchen" or "Avoid" | 12.4% |
| Menus whose cloud request held no allergy list and no photo data | 8 of 8 |
| Time for all 8 menus | 6 min 31 s |

[All five held-out tests](kit/HELD-OUT-RESULTS.md)

## Three labels
Every dish gets one of three labels, so the parent knows what to ask before ordering: **No listed allergen found**, **Ask the kitchen**, **Avoid**. Each label shows its reason: the word on the menu, the typical recipe, or the hidden source.

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
| `kit/` | Menus, answer keys and hashes, saved runs and scores, scorer, all five held-out sets. |

## License
MIT, see `LICENSE`.
