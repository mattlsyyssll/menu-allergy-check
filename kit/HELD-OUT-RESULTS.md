<!-- Method page linked from the root README. Menu codes M01 to M56 are the kit's menu ids (case-data.json in each set). -->
# Results of all five held-out tests

Three labels exist and none says "safe": **No listed allergen found**, **Ask the kitchen**, **Avoid**. A false-safe is a dish that holds a listed allergen and is marked "No listed allergen found". The goal is 0.

Each set is 8 new menus, keys hashed before the run, run once, then published.

| Measure | Final 1 (after round 3) | Final 2 (build 6) | Final 3 (build 7) | Final 4 (build 8) | Final 5 (build 9) |
|---|---|---|---|---|---|
| Hazard answers in the key | 94 | 140 | 206 | 127 | 133 |
| Safety recall | 81.9% | 90.7% | 74.8% | 76.4% | 91.7% |
| False-safe | 9 | 9 | 38 | 14 | 3 |
| Hazard dishes not read from the photo | 8 | 4 | 14 | 16 | 8 |
| Label accuracy | 71.0% | 81.6% | 70.8% | 73.2% | 82.3% |
| Over-caution | 20.0% | 16.1% | 20.2% | 19.1% | 12.4% |
| Privacy v2 | n/a | 8/8 | 8/8 | 8/8 | 8/8 |

The 3 false-safe labels of final 5 (letters are the allergy lists A to D): Torta de Jamón (B; telera is a bread roll), Sope de Chorizo (B; chorizo is a sausage), Cantucci (A; cantucci are cookies).

What each round changed, and what the next test showed:
- Round 4 (tested by final 2): the cloud rates every dish for all 19 allergen categories, the same request for every user.
- Round 6 (final 3): hidden sources from the FARE allergen pages (barbecue sauce, chili sauce, bread and rolls). The set-3 key also counted FARE's broad lines (baked goods, sauces, soups) for every dish; all 38 false-safe labels rest only on those lines. A re-score with the set 1 and 2 key rules gives 91.2% and 0 false-safe (`rescore-set3/`, made after the official score; the official score stands).
- Round 7 (final 4): fewer "Ask the kitchen" labels from the cloud's vaguer ratings. 13 of the 14 false-safe labels were foods named on FARE's full lists.
- Round 8 (final 5): those named foods added, and the photo read told to list dishes under every menu heading.

The live app is build 9b: build 9 plus two changes from final 5 (a line that looks like a menu heading is marked "Ask the kitchen"; sausage, cookie and roll names added). Build 9b has no held-out test of its own.

What these numbers rest on:
- All five held-out sets are spent and their keys are published, so they cannot test a later build.
- Menus are rendered from text, not photographed. Keys are one person's reading of public allergen pages (FDA, FARE, Allergy and Anaphylaxis Australia); no allergist reviewed them. Facts marked UNVERIFIED in the `ANSWER-KEYS.md` files use general cooking knowledge.
- Set 4 has one key answer in question: farofa is read as wheat flour; it is usually cassava flour.
- Set 1: the key of menu M24 was partly seen before the run; without M24, recall is 81.1%. One run of menu M21 hung once; the rerun took 31.5 s. Both are in `KIT-NOTES.md`.
- Privacy v1, the frozen checker, fails every run from final 2 on, because the one fixed cloud instruction names all 19 allergen categories for every user. Privacy v2 is a documented copy that removes that fixed text, then runs the same checks (`scripts-v2/README.md`). The request is identical for every allergy list; that is tested in `../app/tests/pipeline.test.ts`.
- The marks are not a guarantee. Always ask the kitchen, and carry prescribed medicine.

Per-test details: `FINAL-1-RESULT.md` to `FINAL-5-RESULT.md`. Re-score commands: `README.md` in this folder.
