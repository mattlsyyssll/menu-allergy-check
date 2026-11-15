# Held-out set 3 (M33 to M40)

Status: built 2026-11-14, sealed. 8 menus, 96 dishes, 384 dish-and-list answers (206 hazard: 83 Avoid, 123 Ask the kitchen; 178 No listed allergen found). Measures the next app build. Set 1 (M02 M03 M04 M12 M14 M18 M21 M24) and set 2 (M25 to M32) are spent.

Why a subfolder: same reason as set 2. The set-1 kit is frozen (`../FROZEN-HASHES.txt`); set 2 has its own freeze file. This folder is a third kit with its own `kit.json`, keys, menus, prompts and freeze file. It uses the frozen scorer, library and allergen plug-in of the parent folder unchanged (in this kit's freeze list as `../scripts` and `../allergy_plugin.py`). Same four allergy lists (`profiles.json` and `labels.json` are byte copies of the parent files).

| Case | Menu | Cuisine | Language | Image | Dishes |
|---|---|---|---|---|---|
| M33 | 金鳳茶餐廳 | Hong Kong cha chaan teng | zh (Traditional Chinese) | photo | 12 |
| M34 | Bếp Nhà Hạnh | Vietnamese | vi | scan | 12 |
| M35 | Soi 9 Night Market Kitchen | Thai street food | en (Thai dish names) | glare | 12 |
| M36 | Saffron Lane Indian Kitchen | Indian | en | clean | 12 |
| M37 | La Huaca Cocina Peruana | Peruvian | es | blur | 12 |
| M38 | Maple & Main Brunch House | American brunch | en | photo | 12 |
| M39 | Beit Al Mezze | Lebanese | en | clean | 12 |
| M40 | Kedai Kopi Ah Hock | Chinese-Malaysian kopitiam | en | glare | 12 |

Each menu has one "of the day / special / chef's choice" dish (all nine allergens Ask) and 1 to 3 dishes that are clean for all four lists.

## Key-quality rule (new in set 3)

Apply each source rule the same way to EVERY dish it covers. Every item of a fetched FARE "may contain" list is one rule in `tools/menus_data3.py` (tables RULES_A and RULES_Q). Code applies it to every dish whose printed text, English gloss or English translation (`kw`, needed for zh, vi, es menus) matches the rule. `check_rules()` fails the build if a matching dish lacks the fact. Examples:
- FARE_SES3: bread, buns, rolls, bagels, toast, naan, pita, cake, pastry, sandwiches, burgers get "sesame Ask the kitchen"; so do dishes with sauce, dressing, gravy, marinade, dip, soup, stew, stir fry, noodles, fried rice, kebabs, skewers, sausage, herbs.
- Barbecue sauce gives fish and tree nut Ask; Worcestershire gives fish Ask; chili sauce, hot sauce, gravy, dressing, marinade, glaze give peanut Ask; mayonnaise, hollandaise, meringue, pasta, pancakes, waffles, bread give egg Ask; sauces, dressings, soups, sausages, batter-fried or breaded food, soy sauce give wheat Ask; baked goods, pasta, sausages, chocolate, steak, shellfish give milk Ask.
- Avoid: the menu prints the allergen word (or a food that is the allergen, such as cheese, butter, cream, yogurt, tofu, shrimp), or it is a basic ingredient of the named dish (bread, buns, cake, pasta, pizza, dumplings, flour, bulgur, semolina, dough are wheat). The strictest fact wins per list.
- Dish-specific Wikipedia facts (WP_*) are added by hand, as in set 2.
- Not applied as dish rules: cuisine-level lines (FARE "Asian cuisine", "African, Asian and Mexican restaurant food", "certain multicultural cuisines"), because they name no dish; and the vague items chips, candy-type snacks, cereals and "desserts" in general unless a named food matches. Coconut is not treated as a tree nut (FARE says it is typically not restricted) or as milk.
- Mollusc dishes (squid, mussels, oysters, cockles, octopus) get shellfish Ask with source GEN (UNVERIFIED), as in sets 1 and 2.

Rules for the app build: read `menus/` and `../profiles.json` allergen lists only. Do not open `keys/`, `cases/`, `case-data.json`, `ANSWER-KEYS.md`, `prompts/` or `tools/` here.

Commands (run from `heldout-set-3/`, the library is in the parent):
```
python3 -I ../scripts/testkit/keys.py verify kit.json
python3 -I ../scripts/testkit/freeze.py check kit.json
python3 -I ../scripts/testkit/cases.py check kit.json
python3 -I ../scripts/testkit/trace.py kit.json
python3 -I ../scripts/testkit/runs.py save kit.json CASE app-<build-id> CASE.reply.txt --transcript CASE.cloudlog.jsonl
python3 -I ../scripts/metrics.py kit.json
```
Keys are hashed in `KEYS-HASHES.txt` (and the copy `../KEYS-HASHES-3.txt`), written before any run. Rebuild input: `tools/make_set3.py` (Pillow; pixels may differ on a rebuild, the committed PNGs are the test input).

Limits: same as sets 1 and 2 (rendered menus, keys from public pages, no allergist review). Facts with source id GEN are general knowledge, marked UNVERIFIED in `ANSWER-KEYS.md`. Source pages (FARE lists, Wikipedia WP_*) were read through a page-fetch summary on 2026-11-14. Dish names were checked by the generator against M01 to M32 (no reuse, no near match); it read the NAMES of M01 to M32 dishes for that check, not any key.
