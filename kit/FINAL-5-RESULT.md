# Final exam 5 (held-out set 5, M49-M56, run once) — 2026-11-15T03:29Z
Model app-final5 = app build 9 (round 8: FARE named foods; read prompt lists every section; heading lines split), Chrome 157 with the built-in model, cloud on (gemini-3.5-flash-lite), 6 min 31 s, 0 timeouts. Run file: runs/saved/app-final5.json.
Key rules: same as set 4, written before the run (heldout-set-5/README-SET5.md). All 8 menus have section headings; 5 have two columns.

| Measure | Final 4 (build 8, set 4) | Final 5 (build 9, set 5) |
|---|---|---|
| Hazard answers in key | 127 | 133 |
| Safety recall | 76.4% (97 of 127) | 91.7% (122 of 133) |
| False-safe | 14 | 3 |
| Hazard dishes missing | 16 | 8 |
| Label accuracy | 73.2% | 82.3% |
| Over-caution | 19.1% | 12.4% |
| Privacy v2 | 8/8 | 8/8 |

False-safe (3), all named-food synonyms missing from the table: M53 Torta de Jamón (B: telera is a bread roll), M53 Sope de Chorizo (B: chorizo is a sausage), M55 Cantucci (A: cantucci are cookies).
Missing dishes (8 hazard answers): names read with a one-letter change (Coconut Punch for Peanut Punch, Champutrado, Juju Dhaui, 蒜香雞 for 鹽酥雞), and M54 where the read merged the heading "Salade et soupes" with its first dish; the heading split then turned that dish's ingredients into separate items.
Set 5 is now spent.

## After final exam 5 (build 9b, live) — not measured on a held-out set
Two changes, both from the final-5 findings:
1. The heading split is off. A line that looks like a section heading stays one item, keeps its ingredient warnings, and is at least "Ask the kitchen" (the read-prompt change alone had fixed the final-4 case).
2. Synonyms of named foods: sausages (chorizo, salami, bratwurst, kielbasa, longganisa, linguiça, andouille, merguez), cookies (biscotti, cantucci), rolls (telera, bolillo, kaiser roll).
Replay (true menu text, saved cloud answers) on all 56 spent menus: set-5 missed hazards 3 -> 1 (Polvorones, A), over-caution unchanged on every set. Build 9b has no held-out result of its own.
