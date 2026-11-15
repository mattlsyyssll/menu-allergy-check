# Held-out set 5 (M49 to M56)

Status: built 2026-11-14, sealed. 8 menus, 96 dishes, 384 dish-and-list answers (133 hazard: 71 Avoid, 62 Ask the kitchen; 251 No listed allergen found). Measures the next app build. Sets 1 (M02 M03 M04 M12 M14 M18 M21 M24), 2 (M25 to M32), 3 (M33 to M40) and 4 (M41 to M48) are spent.

Why a subfolder: same reason as sets 2 to 4. This folder is a fifth kit with its own `kit.json`, keys, menus, prompts and freeze file. It uses the frozen scorer, library and allergen plug-in of the parent folder unchanged (in this kit's freeze list as `../scripts` and `../allergy_plugin.py`). Same four allergy lists (`profiles.json` and `labels.json` are byte copies of the parent files).

| Case | Menu | Cuisine | Language | Image | Dishes | Layout |
|---|---|---|---|---|---|---|
| M49 | Blue Mountain Cookshop | Jamaican | en | glare | 12 | two columns, 2 headings |
| M50 | Supra Tbilisi | Georgian | en | clean | 12 | one column, 3 headings |
| M51 | Himal Momo House | Nepalese momo house | en | scan | 12 | two columns, 2 headings |
| M52 | Ono Kau Kau Plate House | Hawaiian plate lunch | en | blur | 12 | two columns, 2 headings |
| M53 | Panadería La Concha Dorada | Mexican panadería and café | es | photo | 12 | one column, 3 headings |
| M54 | Crêperie Le Moulin Breton | French crêperie | fr | clean | 12 | two columns, 4 headings |
| M55 | Pasticceria Rossi e Figli | Italian pasticceria and gelateria | it | glare | 12 | two columns, 3 headings |
| M56 | 阿財夜市小吃 | Taiwanese night market | zh (Traditional Chinese) | photo | 12 | two columns, 2 headings |

Every menu has 1 or 2 "of the day / special / chef's choice" dishes (all nine allergens Ask; M55 has two) and several dishes that are clean for all four lists.

## Answer-key rules (set 1 and set 2 policy; set 4 does NOT apply FARE's broad category lines per dish)

- Per dish and allergy list, the strictest fact wins.
- "Avoid": the menu prints the allergen, or it is a basic ingredient of the named dish.
- "Ask the kitchen": (a) a public source names THIS dish, or a named food that is part of it (a sauce, dip, paste, bread, batter, dressing by name), as a possible source of the allergen. Examples of named foods: barbecue sauce, Worcestershire sauce, chili sauce, pesto, mayonnaise, hoisin, fish sauce, shrimp paste, bread, buns, rolls, bagels, breadsticks, satay sauce, marzipan. Each such named-food rule is applied to EVERY dish that contains that food. Or (b) the menu does not say what is in the dish ("of the day", "special", "chef's choice").
- NOT counted: broad category, cuisine or cross-contact lines that name no specific food. Examples: "baked goods" in general, "sauces, dressings, gravies and marinades" in general, "soups", "stews", "stir-fries", "Asian / African / Mexican cuisine or restaurant food", "shellfish is sometimes dipped in milk", "fried foods may share oil". A named item inside such a line still counts (FARE's sesame list "baked goods (bagels, bread, breadsticks, hamburger buns and rolls)" -> bread, buns, rolls, bagels and breadsticks count; "baked goods" alone does not).
- Otherwise "No listed allergen found".
- Every fact has a source id (see the Sources section of `ANSWER-KEYS.md`). General cooking knowledge without a fetched page = source GEN, marked UNVERIFIED.

How it is enforced: `tools/menus_data4.py` holds the named-food rules (RULES_A for printed or basic ingredients, RULES_Q for named foods), applies them by code to every dish whose printed text, English gloss or English translation (`kw`) contains the food, and `check_rules()` fails the build if any matching dish lacks the fact.

Judgement calls (same as set 4, plus):
- Same rule tables as set 4 (RULES_A, RULES_Q), applied by code; `check_rules()` in `tools/menus_data5.py` fails the build if a matching dish lacks the fact.
- New named-food rule from a page fetched 2026-11-14: achar (Wikipedia, Momo) gives peanut, sesame and soy Ask on every dish that names it.
- Dish-specific facts from pages fetched for this set (WP_PATTY, WP_KHACH, WP_MALA, WP_MOMO, WP_LOCO) are in `ANSWER-KEYS.md` Sources.
- Mollusc rule (GEN, UNVERIFIED) exists in the tables; no set 5 dish contains a mollusc.
- Crêpes and the Taiwanese wraps carry "wheat" in the English translation line (`kw`) so the basic-ingredient rule applies; buckwheat galettes do not.
- Dishes of other kinds that would need a rule not in the tables (croissant, doughnut, butterfish) were left off the menus rather than adding rules.

Rules for the app build: read `menus/` and `../profiles.json` allergen lists only. Do not open `keys/`, `cases/`, `case-data.json`, `ANSWER-KEYS.md`, `prompts/` or `tools/` here.

Commands (run from `heldout-set-5/`, the library is in the parent):
```
python3 -I ../scripts/testkit/keys.py verify kit.json
python3 -I ../scripts/testkit/freeze.py check kit.json
python3 -I ../scripts/testkit/cases.py check kit.json
python3 -I ../scripts/testkit/trace.py kit.json
python3 -I ../scripts/testkit/runs.py save kit.json CASE app-<build-id> CASE.reply.txt --transcript CASE.cloudlog.jsonl
python3 -I ../scripts/metrics.py kit.json
```
Keys are hashed in `KEYS-HASHES.txt` (and the copy `../KEYS-HASHES-5.txt`), written before any run. Rebuild input: `tools/make_set5.py` and `tools/make_render5.py` (Pillow; pixels may differ on a rebuild, the committed PNGs are the test input).

Limits: same as sets 1 to 4 (rendered menus, keys from public pages, no allergist review). Dish names were checked by the generator against M01 to M48 (no reuse, no near match); it read the NAMES of those dishes for that check, not any key.
