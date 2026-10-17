# SMS flow test notes

Written from reading `parse()` and `send()` in `app/app.template.html`. Items marked **to confirm** have not yet been seen on the published console. Fill in the Result column when you run it.

Demo phones: 0631 (Olagoni chair), 0151 (Olango chair), 0143 (shared, covers 0069 and 0143), unregistered (+000 555 9999).

## Test sheet

| # | Phone | Send | Expected | Result |
|---|---|---|---|---|
| 1 | 0631 | `OK` | Recorded as working, matched automatically | |
| 2 | 0631 | `BROKEN` | Not working, flagged to the top of the officer list | |
| 3 | 0631 | `DRY` | Recorded as dry | |
| 4 | 0631 | `DIRTY` | Recorded as dirty water, with boil-water advice | |
| 5 | 0631 | `0631 broken` and `broken 0631` | Code works in either position | |
| 6 | 0631 | `mbovu`, `sawa`, `kimekauka`, `chafu` | Same as the English words | |
| 7 | 0631 | `hello` | Asks for OK, BROKEN, DRY or DIRTY | |
| 8 | 0143 | `BROKEN` | Asks which water point | |
| 9 | 0143 | `0069 BROKEN` | Records 0069 only | |
| 10 | Unregistered | `BROKEN` | Asks for the 4-digit number | |
| 11 | Unregistered | `0151 BROKEN` | Code wins, records against 0151 | |
| 12 | 0631 | `0632 BROKEN` (0632 not a real point) | **Should** reject the number; see issue 1 | |
| 13 | 0631 | `NOT OK` | **Should not** record as working; see issue 2 | |

Also check: the officer screen updates, the receipt gains three lines per report (inbound SMS, reply SMS, rescore), and a second device sees the change.

## Issues

1. **Wrong code is silently accepted (to confirm).** In `send()`, a code that is not a known water point is ignored, and a phone linked to one point then files the report there. Proposed fix: if a 4-digit code is present but unknown, reply "We do not know water point 0632. Please check the number painted on the pump." and record nothing.
2. **Negation flips meaning (to confirm).** `parse()` only treats "not working" as negative, so `NOT OK` and `not fixed` match the OK rule. Proposed fix: check for `not ok`, `not fixed`, `bado` and similar before the OK rule, and ask the sender to reply BROKEN or OK.
3. **OK clears dirty water.** `kind === "ok"` sets `dirty = false` with no test. Hassan to decide: leave the dirty flag until a lab result, or keep it as is. No message should imply the water is safe to drink.
4. **Any number can report on any pump.** This follows `docs/CONTRACT.md` (a code always wins). Worth an answer ready for the judges' Q&A.
5. **Reply wording.** Every reply opens with "Thank you." and says the officer "can see it now". Read each one on a small phone screen and shorten if needed.

## Who decides

Issues 1 and 2 change logic, not just text, so Kepler agrees before any PR. Issue 3 is Hassan's call. Issues 4 and 5 are for Ruth and Hassan.
