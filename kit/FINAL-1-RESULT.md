# Final exam 1 (held-out set 1, run once) — 2026-11-15T00:12Z
Model app-final1 (build after round 3), Chrome 157 on the builder's computer, cloud on.
- Safety recall 81.9% (77 of 94), false-safe 9, hazard dishes missing 8, label accuracy 71.0%, Ask rate 18.3% (key 11.4%), over-caution 20.0%, privacy 6 of 8 (both flags are translated dish names in the request: M04 'almond','egg','shrimp'; M14 'กง' — checker defect logged in KIT-NOTES).
- Dev set at the same build: recall 97.5%, false-safe 1. The gap shows the round 2-3 fixes overfit the development menus.
- M21 hung once (device call never returned, > 4 min); rerun with M24 completed (31.5 s). Both runs recorded; the scored M21 is the completed rerun.
- M24 key rows were partly seen by a helper earlier (KIT-NOTES); excluding M24 changes the result as listed in scores/.
- False-safe: M02 Zuppa del Giorno (A,B,C,D); M12 Beef Chili (A), Classic Cheeseburger (B), Pulled Pork Plate (D); M18 Beef Rendang (B), Ayam Goreng (C).
This set is now spent. A new sealed set (held-out-2) measures the next build.
