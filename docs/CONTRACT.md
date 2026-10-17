# Shared contract

Everything that crosses between the scoring code, the app and the demo. Change it only in a pull request that says so in its title.

## One water point (`out/points.json`, one object per point)

| Field | Meaning |
|---|---|
| `id` | Water-point ID, e.g. `KJ-WP-0631`. The last four digits are the SMS code. |
| `n`, `sc`, `ty` | Name, sub-county, type as recorded |
| `la`, `lo` | Latitude and longitude, or `null` when the register's coordinates are missing or implausible |
| `st`, `ss`, `sd`, `age` | Latest status (`Functional`, `Non-functional`, `Seasonal (dry)`, `Not found`), its source, its date, and its age in days at 30 Sep 2026 |
| `A` `B` `C` `D` `E` | The five dimension scores, 0–20 each: working now, reliability, committee, water quality, water supply |
| `bk`, `mr`, `oj` | Breakdowns since 2021, median repair days, open job cards |
| `tm`, `sav`, `sa` | Tariff model, savings in USD, service agreement (`yes`/`no`) |
| `ec`, `fl`, `qd` | Latest E. coli (cfu/100 ml), fluoride (mg/l), test date |
| `ra` | Sub-county rainfall anomaly, last 6 months, % |
| `gi` | 1 if the rising main is galvanised iron |
| `m12` | Community messages linked to this point in the last 12 months |
| `pop`, `net` | Host settlement population and best phone signal |
| `mech`, `tw` | Nearest active mechanic and wet-season travel minutes |

The app recomputes score, band, flag, confidence and actions from these fields plus live SMS updates (see `view()` in `app/app.template.html`, which mirrors `scoring/score.py`).

## Live state (published demo, shared between viewers)

| Collection | Document id | Body |
|---|---|---|
| `decisions` | water-point ID | `{decision: "approved"|"rejected", actions: [text], sms, score, at}` |
| `status` | water-point ID | `{status, dirty, at, src}`: the latest committee report |
| `inbox` | random | `{phone, text, wp, result, at}`: SMS received |
| `outbox` | random | `{wp | phone, text, kind: "alert"|"reply", at}`: SMS sent |
| `ledger` | random | `{item, wp, units, cost, at}`: every metered action |

## SMS replies (demo is in English; the reader also accepts common Swahili)

| Reply | Meaning | Also accepted |
|---|---|---|
| `OK` | Working | sawa, working, fixed |
| `BROKEN` | Not working | mbovu, imeharibika, no water, hakuna maji |
| `DRY` | Dried up | kimekauka, imekauka |
| `DIRTY` | Water quality complaint | chafu, kutu, rust, smell |

A four-digit code in the text (e.g. `0631 BROKEN`) always wins. Without one, a phone registered to exactly one water point is matched automatically; a phone covering several points, or an unregistered one, is asked for the code.

## Prices used for metering (scenario values)

| Item | Price |
|---|---|
| One scoring or agent call | $0.001 |
| One SMS, sent or reverse-billed | $0.02 (case pack range $0.01–0.03) |
