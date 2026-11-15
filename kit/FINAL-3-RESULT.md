# Final exam 3 (held-out set 3, M33-M40, run once) — 2026-11-15T01:54Z
Model app-final3 = app build 7 (round 6 rules), Chrome 157 on the builder's computer, cloud on (gemini-3.5-flash-lite), 6 min 17 s, 0 timeouts. Run file: runs/saved/app-final3.json.

| Measure | Final 2 (build 6, set 2) | Final 3 official (build 7, set 3 key) | Final 3 re-score (set 1-2 key rules) |
|---|---|---|---|
| Hazard answers in key | 140 | 206 | 137 |
| Safety recall | 90.7% | 74.8% (154 of 206) | 91.2% (125 of 137) |
| False-safe | 9 | 38 | 0 |
| Hazard dishes missing (name read differently or not read) | 4 | 14 | 12 |
| Label accuracy | 81.6% | 70.8% | 74.2% |
| Over-caution | 16.1% | 20.2% | 26.3% |
| Privacy v2 | 8/8 | 8/8 | 8/8 |

All 38 official false-safe answers rest only on FARE's broad cross-contact lines (baked goods -> peanut/sesame; sauces, marinades, soups -> sesame/soy/wheat; shellfish dipped in milk -> milk), which the set-3 key applied to every dish and sets 1-2 did not. The app does not apply them by design: they would mark almost every dish "Ask the kitchen". Re-score method: rescore-set3/README.md.
Missing dishes: misread names (沙爹 for 沙嗲, 乾炒河粉 for 乾炒牛河, "Susupiro" for "Suspiro"), a variable dish not read (Sugerencia del Chef), and 鴛鴦 not read.
Set 3 is now spent.
