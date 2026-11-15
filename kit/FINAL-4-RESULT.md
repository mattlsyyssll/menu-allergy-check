# Final exam 4 (held-out set 4, M41-M48, run once) — 2026-11-15T02:35Z
Model app-final4 = app build 8 (round 7: "often" alone raises Ask only for peanut and tree nuts; generic curry nut rule removed), Chrome 157 with the built-in model, cloud on (gemini-3.5-flash-lite), 6 min 27 s, 0 timeouts. Run file: runs/saved/app-final4.json.
Key rules (written before the run, heldout-set-4/README-SET4.md): named foods count for every dish that holds them; broad category, cuisine and cross-contact lines do not.

| Measure | Final 4 |
|---|---|
| Hazard answers in key | 127 |
| Safety recall | 76.4% (97 of 127) |
| False-safe | 14 |
| Hazard dishes missing (not read, or name read too differently) | 16 |
| Label accuracy | 73.2% |
| Over-caution | 19.1% |
| Privacy v2 | 8/8 |

False-safe causes:
- 13 of 14: a named food from FARE's full "may contain" lists that the app's table lacks: chocolate (peanut, tree nuts), pudding, pie, hot sauce (peanut), sausage, pretzel, rice cake, cracker (sesame), cracker (tree nuts).
- 1 of 14: Picanha na Brasa, wheat Avoid because "farofa" was read as flour. Farofa is usually toasted cassava (manioc) flour. Unverified here; the official score stands.
Missing dishes: M42 (Sichuan) read 8 of 12 dishes (a section heading was read as a dish and 5 dishes were not returned); M45 misread names (Schweinehase for Schweinshaxe); M41 one variable dish not read.
Set 4 is now spent.
