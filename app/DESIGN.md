# Design: what runs where

## The privacy rule
- The allergy list stays on the device (browser `localStorage`). It is never sent.
- The menu photo is read on the device. It is never sent.
- The only data that leaves the device is the dish names on the menu (printed name and English name), in ONE request per menu, plus a fixed instruction text. The fixed text is the same for every user and names all 19 allergen categories, so the request cannot reveal which ones one user picked.
- The "What left this device" panel shows the exact request text.
- No analytics, no accounts, no server of our own.

## On device versus cloud
| Step | Where | Firebase AI Logic mode | Sees |
|---|---|---|---|
| Read the photo: dish names, English names, printed ingredients | Device (Chrome built-in model) | `ONLY_ON_DEVICE` | Photo |
| Match printed text against the saved list and the hidden-sources tables (11 languages) | Device (plain code, no model) | none | Printed text, saved list |
| Rate every dish for all 19 allergen categories (`usually`, `often`, `rarely`, `unknown`) and list a typical recipe | Cloud (Gemini) | `ONLY_IN_CLOUD` | Fixed instruction and dish names only |
| Read only the saved list's allergens from the cloud answer; merge the marks | Device (plain code) | none | Cloud answer, saved list |
| Waiter question | Device, fixed reviewed templates, no model | none | Final marks |

`PREFER_*` modes are not used: they could send the photo to the cloud without the app deciding. The on-device step shows an error on failure and never falls back to the cloud. Each reply is checked through `inferenceSource`, so the "decided on this device / by the cloud" chip comes from the SDK.

## The three labels
There are exactly three, and none says "safe":
- **No listed allergen found**
- **Ask the kitchen**
- **Avoid**

How a dish gets its label:
- An allergen printed on the menu gives **Avoid**.
- A hidden-sources table hit (dishes, sauces and the named foods on FARE's "may contain" lists), a cloud rating of `unknown` or no rating, or a rating of `often` for peanut or tree nuts, gives **Ask the kitchen**. For other allergens a rating of `often` counts only through an ingredient in the cloud's recipe list.
- A line that looks like a menu section heading ("Snacks and Desserts", "Salades et soupes") is at least **Ask the kitchen**: the photo read may have merged several dishes under it.
- A cloud rating of `usually` gives **Avoid**. If the menu prints ingredients and neither the printed words nor the table point to that allergen, it gives **Ask the kitchen**.
- Dishes whose name says they vary ("of the day", "del giorno", "du jour", "special", "chef's", "seasonal", "house" and the same ideas in other languages) are at least **Ask the kitchen**.
- The stricter mark wins across printed text, tables, recipe and rating. A cloud answer never lowers a mark set from the menu text.
- Cloud step off or failed: every dish that is not already **Avoid** is **Ask the kitchen** when the cloud failed, and a dish with no printed ingredients is **Ask the kitchen** when the cloud is off.

## Timeouts and retries
- Device read of the photo: 90 s, one retry (2 attempts). A reply that is not valid JSON is retried too.
- Cloud request: 45 s, one retry (2 attempts).
- A photo read that returns fewer than 3 dishes is read once more with a fresh call; the longer list is kept, and a warning shows if it is still short.
- Final cloud failure: every dish not already **Avoid** becomes **Ask the kitchen**, and the screen says the cloud recipe step failed.
- Final device failure: dishes already seen while the model was writing become **Ask the kitchen** with a message. If none were seen, the screen shows the error.
- Limit: a hung on-device call cannot be cancelled from JavaScript, so an abandoned call may keep running in Chrome while the retry starts.

## Files
- `src/core/`: pure functions (allergen tables, matching, merge, cloud payload, waiter question). Fully unit-tested.
- `src/pipeline.ts`: the step order. It talks to two small engine interfaces, so tests use fakes.
- `src/ai.ts`: the Firebase AI Logic wrapper.
- `src/runner/run.ts`, `run.html`, `scripts/kit-dev.ts`: a dev-only batch runner that runs the test kit's menus. It serves only the menus and the allergy lists from `../kit`, never the answer keys.
