# AquaSentinel

Team Ocean's build for the **Water Care AI Hackathon 2026**, Track B, challenge B1 (Kijana District rural water security).

AquaSentinel gives every water point in Kijana District a score out of 100, puts the broken ones at the top of the water officer's list, and lets the officer approve, edit or reject each action before anything goes out. Water committees get plain SMS and reply OK, BROKEN, DRY or DIRTY, and the score updates straight away. Every action is metered and receipted on the Agentic Commerce Infra, so sponsors, the officer and each committee can see where the money went.

> **Synthetic data.** Kijana District is fictional. All outputs are scenario results. No score shows that water is safe to drink; only a lab test can.

**Live demo:** https://starwaterheaven.github.io/AquaSentinel/ (officer view; add `#phone` for the committee phone in a second window, `#funding` for funding and proof). Republish with `scripts/publish_pages.sh`.

**For AI assistants:** [llms.txt](llms.txt) · **Pitch script:** [docs/DEMO-SCRIPT.md](docs/DEMO-SCRIPT.md) · **Architecture (discussion draft):** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · **Backtest:** [docs/BACKTEST.md](docs/BACKTEST.md) · **WhatsApp via Torque:** [docs/TORQUE.md](docs/TORQUE.md) · **Pump plate:** [docs/plate.svg](docs/plate.svg) · **Pitch deck (PDF):** [docs/AquaSentinel-TeamOcean-deck.pdf](docs/AquaSentinel-TeamOcean-deck.pdf)

## How the score works

Five dimensions, 20 points each:

| Dimension | What drives it |
|---|---|
| Working now | The newest report from any source (register, inspection, survey, job card, committee SMS). Old reports count for less. |
| Reliability | Breakdowns since 2021 and median repair time |
| Committee | Tariff, savings, a recent meeting, service agreement |
| Water quality | Latest E. coli, fluoride and nitrate; recent dirty-water reports |
| Water supply | Rainfall against normal (shallow wells weigh more); recent "dry" reports |

Bands: 80+ Good, 60–79 Watch, 40–59 At risk, under 40 Critical. **Any point that is not working is flagged "Not working" and goes to the top of the list, whatever its score.** Each point also gets a confidence label: points with no fresh evidence are "silent" and go on the inspection list. The code is `scoring/score.py`.

Engine v0.4 splits the pipeline into three steps—load the pack, prepare the evidence, and compute the scores—so one codebase serves the live console export, the backtest, and message evaluation. A cutoff date can make the past blind to future data. The console's `view()` mirrors this file; keep them in step.

## Reading committee SMS

Committees can text in plain English or Swahili. The reader scores each message against weighted keywords, including `imeharibika`, `haitoi`, `imevunjika`, `imekauka`, `kavu`, `chafu`, `harufu`, and `mafuriko`, and picks the strongest category. A flood report also counts as a water-safety report.

It matches a message to a water point using, in order:

1. A `KJ-WP-0000` identifier
2. A bare four-digit code
3. An exact village name
4. A fuzzy village name (to tolerate misspellings)
5. A technology hint such as “borehole,” “spring,” or “tank” when one village has multiple points

If the message is still ambiguous, it goes to the officer rather than being guessed onto a point.

## Does it work? The backtest

We scored each point using only data available up to early 2024, then compared the lists with what field teams later found:

| Ground truth | Points observed | Not working (base rate) | Flagged precision | Flagged recall |
|---|---:|---:|---:|---:|
| 2024 inspection round | 624 | 130 (21%) | 47% | 72% |
| Aug-2025 verification survey | 124 | 35 (28%) | 47% | 49% |

The flagged list caught 72% of points later confirmed not working in the 2024 inspection round, at 47% precision—about 2.2× the base failure rate (1.7× against the survey). Of the failures the flagged list missed, 52–57% were already on the silent, low-confidence inspection list. See [docs/BACKTEST.md](docs/BACKTEST.md) for methodology and full tables.

## The district right now (scenario run)

- 1,078 water points: 755 working, 323 not working
- 20 Critical, 377 At risk, and 484 silent points on the inspection list
- The register claims 79% functional; the newest evidence supports at most 70%
- The median register record is 593 days old; district-funded repairs take a median 84 days

## Money and proof

Actions run through the Agentic Commerce Infra (Qatom): catalog item 212 is a $1 water-point sponsorship, item 213 is a $0.02 officer-approved alert SMS, and engine calls are metered at $0.001. Nothing is spent until the officer approves it, and every action carries a receipt. Open the `#funding` view to follow a dollar from sponsor to committee.

## Run it

```bash
pip install pandas numpy
# 1. Put the Kijana data pack CSVs in data/ (see data/README.md)
python scoring/score.py          # -> out/water_point_scores.csv
python scoring/backtest.py       # -> out/backtest.md + out/backtest_scores.csv
python scoring/export_points.py  # -> out/points.json
python app/build.py              # -> out/aquasentinel-console.html (open in a browser)
```

The built page works offline in one browser tab. The published demo shares live state between viewers, so the officer screen and the committee phone can run on two devices.

## Repo layout

| Path | What |
|---|---|
| `scoring/` | Score engine, backtest and console export |
| `app/` | Console app: officer view, committee phone, receipt |
| `torque/` | Report store (Cloudflare Worker) that Torque, our WhatsApp agent, submits committee reports to |
| `docs/CONTRACT.md` | The fields every part agrees on. Read this before changing anything shared. |
| `docs/TASKS.md` | Who does what today, with a brief you can paste into your own AI |
| `data/` | Local only. The data pack is never committed. |

## Team

Hassan (product, pitch, Qatom), Vladyslav (data and validation), Ruth (field and community side), Wizard Kepler (build).

## Working together

- Work on a branch and open a pull request into `main`. Keep pull requests small; Wizard Kepler merges.
- Never commit the data pack or anything in `out/`.
- If you change a field in `docs/CONTRACT.md`, say so in the pull request title.
- Keep the console's `view()` in step with `scoring/score.py`, and keep the SMS reader accepting the Swahili words in `docs/CONTRACT.md`.
- Write money as `$1` / `$0.02` / `$0.001`—no other formats.
