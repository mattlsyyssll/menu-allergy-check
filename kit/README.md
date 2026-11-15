# Menu allergy check for a parent: test kit

This folder lets anyone re-check the published test results with no model and no network. It needs Python 3 (standard library only). Run every command from this folder (`kit/`). GitHub runs the same commands on every change (`.github/workflows/check.yml`).

## What the kit holds
- 32 invented menu photos (`menus/` for M01 to M24, `heldout-set-2/menus/` for M25 to M32), 331 dishes, 4 allergy lists, an answer key per dish and per list.
- Held-out set 1 (M02 M03 M04 M12 M14 M18 M21 M24) and held-out set 2 (M25 to M32) are both spent: each was scored once. Their keys are published here.
- Saved app runs: development builds `app-build2` to `app-build5` (16 menus each), `app-final1` (set 1) and `app-final2` (set 2, in `heldout-set-2/runs/`), with the saved scores.

| Folder or file | What it is |
|---|---|
| `menus/`, `cases/`, `case-data.json` | The 24 set-1 inputs: menu photos (PNG, rendered from text; English, Thai, Chinese, Spanish, Italian, French; nine with noise, tilt, blur or glare), and the menu text. All restaurants, dishes and prices are invented. |
| `keys/`, `KEYS-HASHES.txt`, `ANSWER-KEYS.md` | The answer keys, written before any run, their SHA-256 hashes (UTC time on line 1), and the readable form with a source for each hidden-source fact. |
| `profiles.json`, `labels.json`, `heldout.json` | The four allergy lists, the three labels, and which cases are held out. |
| `prompts/`, `baseline/ARM.md` | The plain-chat comparison arm (defined, not run). |
| `entry/` | The output form the app must write its results and cloud log in. |
| `allergy_plugin.py`, `scripts/metrics.py` | The safety, accuracy, Ask-rate, over-caution and privacy measures. |
| `scripts/testkit/`, `tests/`, `tools/` | The checking library, its tests, and the generator of the menus and keys. |
| `runs/` | Saved app replies and cloud-request logs (`app-build2` to `app-build5`, `app-final1`) and the synthetic `replay-sample` that tests the scorer. |
| `scores/` | Saved scores, `RESULTS.md`, `METRICS.md`, `KEY-TRACE.md`. |
| `scripts-v2/` | The privacy rule v2 (documented rescore), its tests and saved results (`METRICS-v2-set1.md`, `METRICS-v2.md` for set 2). |
| `heldout-set-2/` | Held-out set 2: its own menus, keys, hashes, runs and scores. |
| `FINAL-1-RESULT.md`, `FINAL-2-RESULT.md` | The two final exams. |
| `FROZEN-HASHES.txt`, `KEYS-HASHES-2.txt` | Hashes of every frozen file, and of the set-2 keys. |
| `KIT-NOTES.md` | Numbers, the four lists, how labels are decided, what is unverified, and the held-out exposure log. |

## Commands and the first line each prints
```
python3 -I tests/run_tests.py                         # last line: KIT TESTS PASS (37 run, 0 failed, 0 errors, 0 skipped)
python3 -I scripts/testkit/score.py --selftest        # first line: score selftest: pass (18 checks)
python3 -I scripts/testkit/replay.py --selftest       # first line: replay selftest: pass (11 checks)
python3 -I scripts/testkit/keys.py verify kit.json    # first line: keys verify: ok
python3 -I scripts/testkit/freeze.py check kit.json   # first line: freeze check ok: every frozen file and key matches its hash
python3 -I scripts/testkit/cases.py check kit.json    # first line: cases check: ok
python3 -I scripts/testkit/trace.py kit.json          # last line: TRACE done: 8 field types; supported 8; under-specified 0; no support 0; conflict 0
python3 -I scripts/metrics.py kit.json --out /tmp/m.md && diff /tmp/m.md scores/METRICS.md   # no output: the re-score equals the saved scores
python3 -I scripts-v2/test_privacy_v2.py              # the 9 self-tests of privacy rule v2
cd heldout-set-2 && python3 -I ../scripts/testkit/freeze.py check kit.json && python3 -I ../scripts/metrics.py kit.json --out /tmp/m2.md && diff /tmp/m2.md scores/METRICS.md
```
The saved scores are not edited by a re-run. A re-run writes to the path after `--out`.

## Results
See `FINAL-1-RESULT.md`, `FINAL-2-RESULT.md` and the root `README.md` for the table, including every false-safe label. Do not read the `replay-sample` rows as results: those replies are hand-made to test the scorer.

## What is simulated and what is not yet run
Simulated:
- The menu photos are rendered from text, then distorted (tilt, glare, blur, grain). They are not photos of real menus.
- The answer keys are written from the menu text and public allergen pages (FDA, FARE, Allergy and Anaphylaxis Australia). Each fact carries its source; facts with no fetched page are marked UNVERIFIED in `ANSWER-KEYS.md`.

Not run:
- Any real restaurant photo, and any allergist review of the keys.
- The plain-chat baseline (defined in `baseline/ARM.md`).

## License
MIT, see `LICENSE`.
