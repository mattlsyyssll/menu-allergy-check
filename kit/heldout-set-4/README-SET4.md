# Held-out set 4 (M41 to M48)

Status: built 2026-11-14, sealed. 8 menus, 96 dishes, 384 dish-and-list answers (127 hazard: 63 Avoid, 64 Ask the kitchen; 257 No listed allergen found). Measures the next app build. Sets 1 (M02 M03 M04 M12 M14 M18 M21 M24), 2 (M25 to M32) and 3 (M33 to M40) are spent.

Why a subfolder: same reason as sets 2 and 3. This folder is a fourth kit with its own `kit.json`, keys, menus, prompts and freeze file. It uses the frozen scorer, library and allergen plug-in of the parent folder unchanged (in this kit's freeze list as `../scripts` and `../allergy_plugin.py`). Same four allergy lists (`profiles.json` and `labels.json` are byte copies of the parent files).

| Case | Menu | Cuisine | Language | Image | Dishes |
|---|---|---|---|---|---|
| M41 | 麺屋 いろは | Japanese ramen and izakaya | ja | photo | 12 |
| M42 | 蜀味轩 | Sichuan | zh (Simplified Chinese) | glare | 12 |
| M43 | Lalibela Table | Ethiopian | en | clean | 12 |
| M44 | Ocakbasi Karadeniz | Turkish grill | en | blur | 12 |
| M45 | Zum Goldenen Hirsch | German beer hall | de | scan | 12 |
| M46 | Churrascaria Estrela do Sul | Brazilian churrascaria and bakery | pt | photo | 12 |
| M47 | Lola Remy Kainan | Filipino | en | clean | 12 |
| M48 | Sal's Slice House | Italian-American pizzeria | en | scan | 12 |

Each menu has one "of the day / special / chef's choice" dish (all nine allergens Ask) and 1 to 4 dishes that are clean for all four lists.

## Answer-key rules (set 1 and set 2 policy; set 4 does NOT apply FARE's broad category lines per dish)

- Per dish and allergy list, the strictest fact wins.
- "Avoid": the menu prints the allergen, or it is a basic ingredient of the named dish.
- "Ask the kitchen": (a) a public source names THIS dish, or a named food that is part of it (a sauce, dip, paste, bread, batter, dressing by name), as a possible source of the allergen. Examples of named foods: barbecue sauce, Worcestershire sauce, chili sauce, pesto, mayonnaise, hoisin, fish sauce, shrimp paste, bread, buns, rolls, bagels, breadsticks, satay sauce, marzipan. Each such named-food rule is applied to EVERY dish that contains that food. Or (b) the menu does not say what is in the dish ("of the day", "special", "chef's choice").
- NOT counted: broad category, cuisine or cross-contact lines that name no specific food. Examples: "baked goods" in general, "sauces, dressings, gravies and marinades" in general, "soups", "stews", "stir-fries", "Asian / African / Mexican cuisine or restaurant food", "shellfish is sometimes dipped in milk", "fried foods may share oil". A named item inside such a line still counts (FARE's sesame list "baked goods (bagels, bread, breadsticks, hamburger buns and rolls)" -> bread, buns, rolls, bagels and breadsticks count; "baked goods" alone does not).
- Otherwise "No listed allergen found".
- Every fact has a source id (see the Sources section of `ANSWER-KEYS.md`). General cooking knowledge without a fetched page = source GEN, marked UNVERIFIED.

How it is enforced: `tools/menus_data4.py` holds the named-food rules (RULES_A for printed or basic ingredients, RULES_Q for named foods), applies them by code to every dish whose printed text, English gloss or English translation (`kw`) contains the food, and `check_rules()` fails the build if any matching dish lacks the fact.

Judgement calls made in set 4 (so the key can be audited):
- FARE soy line "grains prepared with soy (cereals, breads, chips, crackers, pasta, rice, tortillas)" is treated as a qualifier line and not applied; the plain named list (cookies, crackers, cereals, ice cream, yogurt, sausages, vegetable broth) is applied.
- "Sausages" and "ice cream" are treated as named foods (FARE names them for several allergens). "Steak" is applied for milk ("butter on grilled steaks").
- "Batter" and "breaded" give wheat Ask; flour, bread crumbs, dough, pasta, dumplings, wontons and ramen noodles give wheat Avoid (basic ingredient).
- Fish sauce gives shellfish Ask (FARE: sometimes made from krill). Dashi gives fish Ask (Wikipedia, Dashi). Tare gives soy and wheat Ask. Doubanjiang gives soy and wheat Ask (Wikipedia, Doubanjiang). Tartar sauce gives egg Ask (mayonnaise based).
- Mollusc rule (GEN, UNVERIFIED) exists in the tables but no set 4 dish contains a mollusc.
- Dish-specific facts from pages fetched for this set are in `ANSWER-KEYS.md` Sources (WP_*, fetched 2026-11-14 summaries).

Rules for the app build: read `menus/` and `../profiles.json` allergen lists only. Do not open `keys/`, `cases/`, `case-data.json`, `ANSWER-KEYS.md`, `prompts/` or `tools/` here.

Commands (run from `heldout-set-4/`, the library is in the parent):
```
python3 -I ../scripts/testkit/keys.py verify kit.json
python3 -I ../scripts/testkit/freeze.py check kit.json
python3 -I ../scripts/testkit/cases.py check kit.json
python3 -I ../scripts/testkit/trace.py kit.json
python3 -I ../scripts/testkit/runs.py save kit.json CASE app-<build-id> CASE.reply.txt --transcript CASE.cloudlog.jsonl
python3 -I ../scripts/metrics.py kit.json
```
Keys are hashed in `KEYS-HASHES.txt` (and the copy `../KEYS-HASHES-4.txt`), written before any run. Rebuild input: `tools/make_set4.py` (Pillow; pixels may differ on a rebuild, the committed PNGs are the test input).

Limits: same as sets 1 to 3 (rendered menus, keys from public pages, no allergist review). Dish names were checked by the generator against M01 to M40 (no reuse, no near match); it read the NAMES of those dishes for that check, not any key.
