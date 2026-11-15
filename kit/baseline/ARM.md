# Baseline arm: the same menus sent to one cloud model with a plain prompt

Scope: this file defines the comparison arm. It is not run yet. It is frozen with the kit so the baseline cannot be changed after the app is scored.

## What the arm is
A single cloud chat model, no app, no on-device step, no hidden-source list, no safety instructions. It receives, for each case:
1. the menu photo `menus/<CASE>.png`, sent as an attached image;
2. the plain prompt in `prompts/<CASE>.txt`: it states the four allergy lists in the message, asks which dishes are safe for each person, and gives only the output form (so the scorer can read it) and the three label words. It does not define the labels, does not mention hidden sources, and does not say "when unsure, ask".

This is what a parent does with a plain AI chat: type the child's list into the message and attach the photo.

## What it shows
| Measure | Where it comes from | Expected contrast (a hypothesis, not a result) |
|---|---|---|
| Safety recall and false-safe count | `scripts/metrics.py` on the baseline replies | The plain model may label hidden-source dishes "No listed allergen found". Not yet measured. |
| Label accuracy, Ask rate, over-caution | same | Not yet measured. |
| Privacy | `scripts/metrics.py` on the baseline cloud log | Fails by construction: the request carries the allergy lists and the image. This is the point of the comparison, not a defect of the harness. |

## How to run it later (no model is run by this kit)
1. Pick the model and record its exact ID in the run name, for example `plain-<model-id>`.
2. For each case id in `case-data.json` (all 24; report development and held-out separately): send `prompts/<CASE>.txt` with `menus/<CASE>.png`; save the model's text reply as `<CASE>.reply.txt`. One call per case, no retries, no follow-up turns.
3. Write the request log: `/usr/bin/python3 -I scripts/make_baseline_log.py kit.json <CASE> <CASE>.cloudlog.jsonl`. It records the request as sent: the prompt text and the image (the first 400 base64 characters, size and SHA-256; the real request carried the whole image).
4. Save: `/usr/bin/python3 -I scripts/testkit/runs.py save kit.json <CASE> plain-<model-id> <CASE>.reply.txt --transcript <CASE>.cloudlog.jsonl`. The kit must be frozen first and refuses a second save of the same case and model.
5. Score: `/usr/bin/python3 -I scripts/testkit/runs.py results kit.json`, then `/usr/bin/python3 -I scripts/metrics.py kit.json`.

## Known simplifications (Unverified effect on the baseline)
- One message lists all four people. A parent would usually ask once per person. Sending four separate messages is a legitimate variant: save the four pages into one reply file.
- The plain prompt names the three label words. Without them the reply could not be scored by label.
- Model choice, temperature and image resolution are not fixed here: record them in the run name and in KIT-NOTES.md when the arm is run.
