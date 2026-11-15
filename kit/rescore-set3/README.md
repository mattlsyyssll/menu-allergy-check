# Documented re-score of held-out set 3 (final exam 3, app-final3)

Not the official score. The official score is `../heldout-set-3/scores/METRICS.md` (frozen scorer, frozen keys, run once).

Why: the set-3 key writer was told to "apply each FARE rule to every dish it covers". It also applied FARE's broad cross-contact lines per dish, which no set-1 or set-2 key did: "baked goods" -> peanut and sesame, "dressings, gravies, marinades and sauces" -> sesame, "soups/sauces/stir-fry/skewers/herbs" -> soy, wheat, sesame, "shellfish is sometimes dipped in milk" -> milk. 69 of the 206 hazard answers rest only on those lines. All 38 official false-safe answers are among those 69.

What this copy changes: each answer is re-labelled from its own key facts with the broad-line facts removed (strictest remaining fact wins: Avoid, else Ask, else No listed allergen found). 69 answers change, all from a hazard label to "No listed allergen found". Nothing else changes: same app replies, same frozen scorer (`../scripts/metrics.py`, run on a copy of the kit with these keys), same name matching.

Broad-line test (regular expression on the fact reason): `baked goods|dressings, gravies, marinades and sauces|lists (soup|sauce|marinated|skewers|stir-fried|herb|stew|broth|fried|curry|noodle|rice)\b|dipped in milk|\(or flavored rice|\(sauces`

Files: `keys/` = the re-labelled key copies; `METRICS-rescore.md` = scorer output on the copy.
