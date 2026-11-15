# Output contract of the menu allergy check (what the app must emit so the kit can score it)

Scope: this file is read by the scorer's trace step and by the app builder. It defines two files per test case. Nothing here changes how the app looks to a user.

## 1. Results file: `<CASE>.reply.txt`

For each test case (one menu photo, `menus/<CASE>.png`) run the app once per saved allergy list (PROFILE-A to PROFILE-D, listed in `profiles.json`) and write all four results into one text file in this exact form:

```
STATUS: PAGES
=== PROFILE-A
Dish: Pad Thai
Label: Avoid
Reason: peanut named on the menu line
Dish: Spring Rolls
Label: Ask the kitchen
Reason: egg rolls can hold peanut
=== PROFILE-B
...
```

Rules:
- One `=== PROFILE-X` page per saved list, all four present, in any order.
- One `Dish:` / `Label:` / `Reason:` group per dish on the menu, in menu reading order. Every dish of the menu appears on every page.
- `Dish:` is the dish name as printed. An English translation of the printed name is also accepted.
- `Label:` is exactly one of `No listed allergen found`, `Ask the kitchen`, `Avoid` (case and end punctuation are ignored; other text on the line is not).
- `Reason:` is required, one line. Extra lines after `Reason:` (for example the question for the waiter) are allowed and are not scored.
- A dish the app could not read is left out. A left-out dish counts as not found: it is wrong for label accuracy and it counts against safety recall if it holds a listed allergen.

Label meaning (the key uses the same rule):
- `Avoid`: the printed text names a listed allergen, or the dish is by definition made with it.
- `Ask the kitchen`: a hidden or variable source (some recipes hold the allergen and the menu does not say), or the dish contents are unknown.
- `No listed allergen found`: nothing in the printed text or in the usual recipe of the dish holds a listed allergen.

## 2. Cloud-request log: `<CASE>.cloudlog.jsonl`

Every request the app sends to a cloud model, one JSON object per line, written by the app's own network layer for the same run:

```
{"to":"cloud","body":{"dish_names":["Khao Soi","Nam Prik"]}}
```

- `to` is `cloud` for every request that leaves the device. Requests that stay on the device are not logged.
- `body` is exactly what was sent (string or JSON).
- No cloud call at all: an empty file.
- The scorer fails the run if a request holds any allergy term of any profile (peanut, tree nut, sesame, milk, egg, wheat, gluten, soy, fish, shellfish and their translations in `profiles.json`), a generic allergy word (allergy, allergic, profile, anaphylaxis, my child), or any image data (data:image URLs, base64 PNG or JPEG, a field named image/photo/picture/pixels that is not empty, a base64-like run of 200 or more characters). Printed dish names are removed first, so a dish called "Peanut Sauce Noodles" may be sent.
- Pass the log to the kit as the transcript when saving a run: `runs.py save kit.json CASE MODEL reply.txt --transcript cloudlog.jsonl`.
