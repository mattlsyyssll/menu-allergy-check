# Held-out set 2 (M25 to M32)

Status: built 2026-11-14, sealed. 8 menus, 91 dishes, 364 dish-and-list answers (140 hazard: 76 Avoid, 64 Ask the kitchen; 224 No listed allergen found). Measures the next app build. Set 1 (M02 M03 M04 M12 M14 M18 M21 M24) is spent (`../FINAL-1-RESULT.md`).

Why a subfolder: the set-1 kit is frozen (`../FROZEN-HASHES.txt`, 37 tests check `../heldout.json`). Changing set-1 files would break both. This folder is a second kit with its own `kit.json`, keys, menus, prompts and freeze file. It uses the frozen scorer, library and allergen plug-in of the parent folder unchanged (they are in this kit's freeze list as `../scripts` and `../allergy_plugin.py`, so any change to them fails `freeze.py check`). Same four allergy lists (`profiles.json` and `labels.json` are byte copies of the parent files).

| Case | Menu | Cuisine | Language | Image | Dishes |
|---|---|---|---|---|---|
| M25 | Osteria Lunetta | Italian | en | clean | 11 |
| M26 | Smokestack Pit & Grill | American diner and BBQ | en | photo | 12 |
| M27 | Kedai Makan Pelangi | Indonesian and Malaysian | en (Malay dish words) | glare | 11 |
| M28 | 한옥정 식당 | Korean | ko | clean | 11 |
| M29 | Cocina Azul Marina | Mexican | en | blur | 11 |
| M30 | Taverna Meltemi | Greek | en | clean | 12 |
| M31 | 居酒屋 酔月 | Japanese izakaya | ja | photo | 11 |
| M32 | Boulangerie Petit Matin | French bakery | en | scan | 12 |

Rules for the app build: read `menus/` and `../profiles.json` allergen lists only. Do not open `keys/`, `cases/`, `case-data.json`, `ANSWER-KEYS.md`, `prompts/` or `tools/` here.

Commands (run from `heldout-set-2/`, the library is in the parent):
```
python3 -I ../scripts/testkit/keys.py verify kit.json
python3 -I ../scripts/testkit/freeze.py check kit.json
python3 -I ../scripts/testkit/cases.py check kit.json
python3 -I ../scripts/testkit/trace.py kit.json
python3 -I ../scripts/testkit/runs.py save kit.json CASE app-<build-id> CASE.reply.txt --transcript CASE.cloudlog.jsonl
python3 -I ../scripts/metrics.py kit.json
```
Keys are hashed in `KEYS-HASHES.txt` (and the copy `../KEYS-HASHES-2.txt`), written before any run. Rebuild input: `tools/make_set2.py` (Pillow; pixels may differ on a rebuild, the committed PNGs are the test input).

Limits: same as set 1 (rendered menus, keys from public pages, no allergist review). Facts with source id GEN are general knowledge and marked UNVERIFIED in `ANSWER-KEYS.md`. New Wikipedia source ids (WP_*) were read through a page-fetch summary on 2026-11-14. Dish names were checked against M01 to M24 by the generator (no reuse, no near match). The generator also read the NAMES of M01 to M24 dishes for that check; it did not read any set-1 key.
