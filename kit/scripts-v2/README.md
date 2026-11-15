# scripts-v2: privacy rule v2 (a documented rescore; every frozen file is untouched)

Date: 2026-11-14. Frozen files (`scripts/`, `allergy_plugin.py`, `scores/METRICS.md`, `FROZEN-HASHES.txt`) are not edited. `scripts-v2/` only imports them. `python3 -I scripts/testkit/freeze.py check kit.json` still passes.

## Why
The frozen rule fails any cloud request that holds an allergy word. From round 4 on, the app sends one FIXED instruction that names all 19 allergen categories (peanut, sesame, egg ...), the same text for every user, plus the dish names. The frozen rule flags every request (app-build5: 0 of 16 pass) although the request does not depend on the user's list. The same rule also flagged English names of dishes that the app sent (app-build3 and app-build4: 15 of 16).

## What changed (rule v2, in `privacy_v2.py`)
1. A request must be: fixed instruction + `"\n\nDishes:\n"` + a JSON list of `{"name", "english"?}` (strings). Any other shape fails.
2. The fixed instruction must be byte-identical in every request of the run. For app-build5 it must also equal `cloud-instruction-app-build5.txt`, dumped from `CLOUD_INSTRUCTION` in `app/src/core/core.ts` (written by a one-off vitest that imports the constant; 2363 bytes). For other builds with no such file, the text before `Dishes:` of the first request of the run is the reference (their instructions hold no allergen word).
3. The fixed text and the dish names and English names the app sent are removed. Then the frozen term lists (profiles.json terms, allergens, generic words) and the frozen image checks run on the rest. Any remaining allergy term or image data fails.
4. All requests of one case must be byte-identical (a retry sends the same text again).

## How identity across allergy lists is proven
The runner logs ONE request per menu and shares it across the 4 lists (the log cannot hold 4 requests to compare). Evidence:
- `run.json` `cloudRequests[].profile` is PROFILE-A for all 16 cases of builds 3, 4 and 5 (one request each, made under list A, reused for B to D).
- The request is built from the dish names only (`buildCloudPayload` takes no list); `tests/pipeline.test.ts` checks that two different lists give a byte-identical request.
- v2 check 1 and 2: the fixed text equals the source text and the rest is only names the menu supplied; a list-dependent word would be a leftover term and fail.
Limit: the log alone does not prove it. The proof is the log shape plus the app test. A build whose request varied by list would need one logged request per list.

## How to run
```
cd kit
python3 -I scripts-v2/metrics_v2.py kit.json            # writes scripts-v2/METRICS-v2.md (all models under runs/)
python3 -I scripts-v2/test_privacy_v2.py                # 9 self-tests of the rule
```
To score a new build whose instruction contains category words, dump its instruction to `scripts-v2/cloud-instruction-<run folder name>.txt` (from `CLOUD_INSTRUCTION`).
Models whose log bodies are not strings of this shape (for example the baselines) fail v2 by design.

## v1 stays
v1 numbers stay as scored (`scores/METRICS.md`, FINAL-1-RESULT.md). v2 results are reported beside them, never in place of them. Label and recall columns in `METRICS-v2.md` are the frozen computation (same numbers as v1).

## Result (development runs, 16 menus)
| Build | v1 privacy | v2 privacy |
|---|---|---|
| app-build3 | 15 of 16 | 16 of 16 |
| app-build4 | 15 of 16 | 16 of 16 |
| app-build5 | 0 of 16 | 16 of 16 |
