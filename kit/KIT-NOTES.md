# Kit notes: menu allergy check for a parent

Status: kit built and frozen 2026-11-14, before any run. The sections below describe the kit as frozen. Results of later runs are in `FINAL-1-RESULT.md`, `FINAL-2-RESULT.md`, `scores/` and `heldout-set-2/scores/`; held-out sets 1 and 2 are both spent and their keys are published.

## Numbers

| Item | Value |
|---|---|
| Cases | 24 menu photos (`menus/M01.png` to `M24.png`), 240 dishes, 4 allergy lists, 960 dish-and-list answers |
| Held out | 8: M02 M03 M04 M12 M14 M18 M21 M24 (`heldout.json`) |
| Development | 16: M01 M05 M06 M07 M08 M09 M10 M11 M13 M15 M16 M17 M19 M20 M22 M23 |
| Key labels | 296 hazard answers (199 Avoid, 97 Ask the kitchen) and 664 No listed allergen found |
| Keys frozen | yes. Keys written 2026-11-14 21:53:53 UTC (`KEYS-HASHES.txt`, 24 SHA-256 lines); kit frozen 2026-11-14 21:54:07 UTC (`FROZEN-HASHES.txt`, 130 files). No run existed at either time. |
| Hash of `KEYS-HASHES.txt` | 42686587146f7c56a5e809255ff5d270c6276f5081d9e89b1e5776e30212bcf8 |
| Hash of `FROZEN-HASHES.txt` | 1eb28c5f6d9778cd4ba50edd3387d10cc2162fc45e03750f9d454ae94fb480e5 |
| Tests | `python3 -I tests/run_tests.py`: 37 pass; the 7 library self-tests pass; `trace.py` exits 0 (8 field types, all supported) |

Held-out rule: tune the app on development cases only. The held-out keys are in `keys/` and `ANSWER-KEYS.md` like the others, so the rule is a promise, not a lock. Show the held-out result separately.

## The four allergy lists

| Id | Allergens | Why this list |
|---|---|---|
| PROFILE-A | peanut | A parent and child; satay, papaya salad, mole, pesto traps |
| PROFILE-B | tree nut, sesame | Pesto, marzipan, tahini, halva |
| PROFILE-C | milk, egg, wheat, soy | Four allergens in one list; ghee, pasta, soy sauce |
| PROFILE-D | fish, shellfish | Fish sauce, Worcestershire, dried shrimp |

All nine US major allergens appear (26 to 95 dishes hold a fact for each allergen).

## The cases

| Case | Menu | Language | Image | Split | Dishes | Hazard answers | Hidden-source traps |
|---|---|---|---|---|---|---|---|
| M01 | Bangkok Garden | en | clean | dev | 10 | 13 | papaya salad, satay |
| M02 | Trattoria Da Marco | it | clean | held out | 11 | 15 | pesto |
| M03 | La Casa de Mole | es | photo | held out | 10 | 11 | mole |
| M04 | 港式小廚 | zh | clean | held out | 10 | 15 | none (printed ingredients, Chinese only) |
| M05 | Bistrot du Coin | fr | clean | dev | 10 | 11 | none |
| M06 | Casa Pepe Tapas | es | clean | dev | 10 | 10 | none (octopus and alioli are Ask) |
| M07 | Sakura Kitchen | en | clean | dev | 10 | 12 | none (miso dashi, gyoza sesame oil are Ask) |
| M08 | Spice Route | en | glare | dev | 10 | 11 | ghee (printed and in dal tadka) |
| M09 | Phở Saigon | en | clean | dev | 10 | 16 | none (fish sauce and hoisin in Ask) |
| M10 | Cedar Table | en | clean | dev | 10 | 11 | tahini (hummus, baba ghanoush), halva |
| M11 | Sunday Table Café | en | photo | dev | 10 | 12 | marzipan |
| M12 | Rosie's Diner | en | clean | held out | 10 | 11 | Worcestershire, Caesar dressing, BBQ sauce, chili |
| M13 | Seoul Table | en | clean | dev | 10 | 15 | none (kimchi fish sauce in Ask) |
| M14 | ครัวไทยบ้านสวน | th | glare | held out | 10 | 13 | satay, papaya salad, fish sauce (Thai script) |
| M15 | Luigi's Kitchen | en | scan | dev | 10 | 14 | pesto |
| M16 | Harbor House Seafood | en | clean | dev | 10 | 13 | none |
| M17 | 龍門茶樓 Dragon Gate Dim Sum | zh | photo | dev | 10 | 14 | none (dried shrimp in turnip cake is Ask) |
| M18 | Warung Nusantara | en | clean | held out | 10 | 14 | satay, peanut sauce |
| M19 | Flour & Chalk Bakery | en | clean | dev | 9 | 10 | hummus |
| M20 | El Camino Tex-Mex | en | blur | dev | 10 | 9 | mole |
| M21 | Olive & Thyme Greek Kitchen | en | clean | held out | 10 | 11 | hummus, halva |
| M22 | Wok & Fire Fusion | en | scan | dev | 10 | 18 | Worcestershire, fish sauce, tahini |
| M23 | Sweet Ending Dessert Bar | en | photo | dev | 10 | 13 | marzipan, ghee, halva |
| M24 | Garden Grill | en | clean | held out | 10 | 4 | none; mostly clean dishes plus one unknown dish ("Chef's Bowl of the Day") |

Image types: clean = flat render; photo = tilt, vignette, grain, blur; glare = bright patch plus tilt; scan = scan lines, speckle, tilt; blur = downscale, blur, low contrast. Nine of 24 have noise. Menus have two columns, prices (USD, EUR, HKD, THB style) and a line of ingredients under most dishes. Fonts differ per menu.

## How the answer key decides a label

Per dish and per list, from the facts in `ANSWER-KEYS.md`:
- Avoid: the printed text names a listed allergen, or the dish is by definition made with it (satay, marzipan, tahini, ghee, fish sauce, hummus).
- Ask the kitchen: some recipes hold the allergen and the menu does not say (mole, pesto, papaya salad, Worcestershire, dal tadka), or the dish contents are unknown.
- No listed allergen found: nothing in the printed text or the usual recipe holds a listed allergen.
- Hazard dish = key label Avoid or Ask the kitchen. A false-safe is a hazard dish the app marks "No listed allergen found". The headline number is safety recall with false-safe count 0 required.

Sources fetched 2026-11-14 and checked against the page text: FDA food allergies page (the nine major allergens), FARE pages for peanut, tree nut, fish, sesame, milk, wheat, soy, egg, shellfish, and Allergy and Anaphylaxis Australia "Peanut" page (satay and satay sauce). URLs are in `ANSWER-KEYS.md` (Sources) and `tools/menus_data.py`. No licensed database (for example Open Food Facts) was used, so no licence applies.

## How the app must emit its results (full contract in `entry/OUTPUT-SPEC.md`)

1. Results file per case, `<CASE>.reply.txt`. Run the app once per saved list on `menus/<CASE>.png` and write all four pages in one file:
   `STATUS: PAGES`, then for each of `=== PROFILE-A` to `=== PROFILE-D`, one group per dish: `Dish:` (as printed; an English translation also accepted), `Label:` (exactly `No listed allergen found`, `Ask the kitchen` or `Avoid`), `Reason:` (one line, required). Extra lines after `Reason:` are allowed. A dish the app did not read is left out and counts as not found.
2. Cloud log per case, `<CASE>.cloudlog.jsonl`: one JSON line per request that leaves the device, `{"to":"cloud","body":...}`, exactly what was sent. Empty file if nothing was sent. The app's network layer must write it, not the model.
3. Save one run per case through the kit: `python3 -I scripts/testkit/runs.py save kit.json CASE app-<build-id> CASE.reply.txt --transcript CASE.cloudlog.jsonl`. Refuses if a frozen file changed, and refuses a second save of the same case and model. Then `runs.py results kit.json` and `scripts/metrics.py kit.json` (add `--gate app-<build-id>` to exit 1 on any false-safe or privacy failure).
4. The app does not read `cases/`, `keys/`, `ANSWER-KEYS.md`, `case-data.json` or `prompts/` (they hold the menu text and the answers). It reads `menus/` and `profiles.json` allergen lists only.

## What the scorer measures

| Measure | Definition |
|---|---|
| Safety recall (headline) | Hazard dish-and-list answers marked Ask the kitchen or Avoid, divided by all hazard answers. A missing dish counts as not recalled. |
| False-safe count | Hazard answers marked "No listed allergen found". Must be 0. Every one is listed by case, list and dish in `scores/METRICS.md`. |
| Label accuracy | Answers equal to the key label, divided by all answers. |
| Ask rate | Answers marked Ask the kitchen, divided by answers given; the key's own rate (10.1% of all 960 answers) is printed beside it. |
| Over-caution | Clean answers (key: No listed allergen found) marked Ask or Avoid, divided by clean answers. |
| Privacy | Fails if a cloud request holds an allergy term of any list (with translations), a generic allergy word, or image data (data:image, base64 PNG or JPEG, a non-empty image field, a base64-like run of 200+ characters). Printed dish names and English glosses are removed first, so "Peanut Sauce Noodles" may be sent but "peanut allergy" may not. |
| Strict count | The library's count: a run is right only if every Dish, Label and safety field is right. Harsh by design; the headline is safety recall. |

## Comparison arm

`baseline/ARM.md` and `prompts/<CASE>.txt`: one cloud chat model, the menu photo, the four lists typed into a plain prompt, no safety scaffolding. Its privacy check fails by construction (the lists and the image are in the request); that is the intended contrast. `scripts/make_baseline_log.py` writes its request log line. Not run.

## Replay sample (SYNTHETIC)

`runs/replay-sample/`: 7 hand-built replies (M01 M05 M17 correct; M07 over-cautious; M10 one false-safe; M13 one hazard dish missing; M16 correct labels but a leaky cloud log), each starting with a SYNTHETIC line, with a `SYNTHETIC.txt` in the folder. Saved through `runs.py save`, so `scores/` holds their scores and `RESULTS.md`, `METRICS.md`. Built by a script from the keys, not by hand typing and not by a model. Before real runs, either keep them (they are a separate model row named `replay-sample`) or delete the folder and its `scores/*/replay-sample` entries.

## Unverified

- Unverified: label correctness against an allergist or a kitchen. The keys are one person's reading of public pages; no clinician reviewed them.
- Unverified: facts marked UNVERIFIED (source id GEN) in `ANSWER-KEYS.md`. They use general culinary knowledge with no fetched page (for example dried shrimp in papaya salad, cheese in pesto, tzatziki on souvlaki, candlenut in rendang). All of them are Ask-level, not Avoid-level. About 60 dish rows in `ANSWER-KEYS.md` carry at least one.
- Unverified: molluscs. Squid, octopus, mussels, clams and oyster sauce are labelled Ask the kitchen for the fish-and-shellfish list because the FDA nine list only names crustacean shellfish and many shellfish plans include molluscs. This is a judgement call, not a sourced fact.
- Unverified: "Avoid" for definitional dishes without a fetched page that names them (basic recipe facts such as pizza dough is wheat, croissants hold butter, tiramisu holds eggs). Source id BASIC.
- Unverified: coconut and cross-contact. Coconut is not treated as a tree nut or milk, and cross-contact in a kitchen is not modelled; a "No listed allergen found" label means only that the printed text and the usual recipe hold nothing listed.
- Unverified: the page "Allergy and Anaphylaxis Australia, Peanut" was read through a page fetch summary; the FARE pages were also read through fetch summaries, not by hand.
- Unverified: whether the on-device model can read the Thai and the glare, blur and scan menus. The images were checked by eye for M03, M14 and M17 only.
- Can't tell from here: whether menu photos made by rendering text resemble real phone photos closely enough. They are cleaner than most real photos (no hands, no curved pages, no handwriting).
- Can't tell from here: whether 16 development cases are enough to tune on without overfitting.
- Baseline simplification: one prompt lists all four people at once; the label words are named in the prompt.
- Pillow, not the standard library, redraws the menus. The committed PNGs are the test input; a rebuild may differ in pixels and would not match `FROZEN-HASHES.txt`.
- Scoring tolerance: dish names match by folded case, accents and punctuation, containment of at least 70% of the longer name, or similarity 0.86 or higher; a dish name the app garbles below that is "not found". The tolerance was tested for the 240 dishes against each other inside a menu (no two dishes of a menu match each other).
- `runs.py save` accepts only one save per case and model, so a re-run needs a new model name (for example `app-build2`).

## Held-out exposure log
- 2026-11-14T23:17Z: a grep by a person building the app, on ANSWER-KEYS.md printed the header and first rows of M24's key (clean Garden Grill menu). No change was made from it. Report held-out results with M24 flagged as exposed, and also the 7-menu result without M24.

## Checker defect found after freeze (2026-11-14T23:43Z)
- Privacy check flags app-build3 M06 for 'almond': the request held the dish name "Turrón de Almendra" and the device's English translation "Almond Turrón". The checker strips printed dish names but not their translations, so menu text was read as list leakage. The allergy list was not sent. Per the freeze rule this stays as scored; a documented rescore with a copied checker that also strips the sent English dish names is allowed and must be reported beside the original.

## Held-out set 2 (built 2026-11-15 00:21 UTC)
- Set 1 is spent (FINAL-1-RESULT.md). Set 2 = M25 to M32, 8 menus, 91 dishes, 364 answers, in `heldout-set-2/` (own kit.json, keys, menus, freeze file `FROZEN-HASHES-2.txt`). Keys hashed in `KEYS-HASHES-2.txt` (timestamp on line 1). Set-1 files, the frozen checker and root `heldout.json` are unchanged; the set-2 `heldout.json` lists set 1 as SPENT and set 2 as SEALED. See `heldout-set-2/README-SET2.md`.
- Check: `cd heldout-set-2; python3 -I ../scripts/testkit/freeze.py check kit.json`. The set-2 freeze list includes `../scripts` and `../allergy_plugin.py`, so a checker change fails it.
