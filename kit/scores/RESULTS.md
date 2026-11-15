# Results

Strict count: 4 of 7 runs right (a run is right only if every checked field is right).

| Model | Runs | Right (strict) | Fields right | Fields wrong | Fields unread | No-model check passed |
|---|---|---|---|---|---|---|
| replay-sample | 7 | 4 of 7 | 613 | 33 | 3 | 6 of 7 |

Partial measures (key-declared groups, fields right of fields checked):

| Group | replay-sample |
|---|---|
| accuracy | 247 of 280 |
| safety | 87 of 89 |

## Runs

| Model | Case | Class | Right | Wrong | Unread | No-model check |
|---|---|---|---|---|---|---|
| replay-sample | M01 | right | 93 | 0 | 0 | pass |
| replay-sample | M05 | right | 91 | 0 | 0 | pass |
| replay-sample | M07 | wrong | 61 | 31 | 0 | pass |
| replay-sample | M10 | wrong | 89 | 2 | 0 | pass |
| replay-sample | M13 | wrong | 92 | 0 | 3 | pass |
| replay-sample | M16 | right | 93 | 0 | 0 | fail |
| replay-sample | M17 | right | 94 | 0 | 0 | pass |

## Misses (every field not right)

- replay-sample M07: PROFILE-A row 1 Label: wrong
- replay-sample M07: PROFILE-A row 2 Label: wrong
- replay-sample M07: PROFILE-A row 3 Label: wrong
- replay-sample M07: PROFILE-A row 4 Label: wrong
- replay-sample M07: PROFILE-A row 5 Label: wrong
- replay-sample M07: PROFILE-A row 6 Label: wrong
- replay-sample M07: PROFILE-A row 7 Label: wrong
- replay-sample M07: PROFILE-A row 8 Label: wrong
- replay-sample M07: PROFILE-A row 9 Label: wrong
- replay-sample M07: PROFILE-A row 10 Label: wrong
- replay-sample M07: PROFILE-B row 1 Label: wrong
- replay-sample M07: PROFILE-B row 2 Label: wrong
- replay-sample M07: PROFILE-B row 3 Label: wrong
- replay-sample M07: PROFILE-B row 5 Label: wrong
- replay-sample M07: PROFILE-B row 6 Label: wrong
- replay-sample M07: PROFILE-B row 7 Label: wrong
- replay-sample M07: PROFILE-B row 8 Label: wrong
- replay-sample M07: PROFILE-B row 9 Label: wrong
- replay-sample M07: PROFILE-B row 10 Label: wrong
- replay-sample M07: PROFILE-C row 4 Label: wrong
- replay-sample M07: PROFILE-C row 5 Label: wrong
- replay-sample M07: PROFILE-C row 6 Label: wrong
- replay-sample M07: PROFILE-C row 9 Label: wrong
- replay-sample M07: PROFILE-D row 1 Label: wrong
- replay-sample M07: PROFILE-D row 2 Label: wrong
- replay-sample M07: PROFILE-D row 3 Label: wrong
- replay-sample M07: PROFILE-D row 4 Label: wrong
- replay-sample M07: PROFILE-D row 5 Label: wrong
- replay-sample M07: PROFILE-D row 7 Label: wrong
- replay-sample M07: PROFILE-D row 9 Label: wrong
- replay-sample M07: PROFILE-D row 10 Label: wrong
- replay-sample M10: PROFILE-B row 1 Label: wrong
- replay-sample M10: plugin row 1 safety:PROFILE-B:Hummus: wrong
- replay-sample M13: PROFILE-A row 9 Dish: unread
- replay-sample M13: PROFILE-A row 9 Label: unread
- replay-sample M13: plugin row 1 safety:PROFILE-A:Hotteok: unread
