# AquaSentinel

Team Ocean's build for the **Water Care AI Hackathon 2026**, Track B, challenge B1 (Kijana District rural water security).

AquaSentinel gives every water point in Kijana District a score out of 100, puts the broken ones at the top of the water officer's list, and lets the officer approve, edit or reject each action before anything goes out. Water committees get plain SMS and reply OK, BROKEN, DRY or DIRTY, and the score updates straight away. Every action is metered and receipted on the Agentic Commerce Infra, so sponsors, the officer and each committee can see where the money went.

> **Synthetic data.** Kijana District is fictional. All outputs are scenario results. No score shows that water is safe to drink; only a lab test can.

**Live demo:** https://starwaterheaven.github.io/AquaSentinel/ (officer view; add `#phone` for the committee phone in a second window, `#funding` for funding and proof). Republish with `scripts/publish_pages.sh`.

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

## Run it

```bash
pip install pandas numpy
# 1. Put the Kijana data pack CSVs in data/ (see data/README.md)
python scoring/score.py          # -> out/water_point_scores.csv
python scoring/export_points.py  # -> out/points.json
python app/build.py              # -> out/aquasentinel-console.html (open in a browser)
```

The built page works offline in one browser tab. The published demo shares live state between viewers, so the officer screen and the committee phone can run on two devices.

## Repo layout

| Path | What |
|---|---|
| `scoring/` | Score engine and export |
| `app/` | Console app: officer view, committee phone, receipt |
| `docs/CONTRACT.md` | The fields every part agrees on. Read this before changing anything shared. |
| `docs/TASKS.md` | Who does what today, with a brief you can paste into your own AI |
| `data/` | Local only. The data pack is never committed. |

## Team

Hassan (product, pitch, Qatom), Vladyslav (data and validation), Ruth (field and community side), Wizard Kepler (build).

## Working together

- Work on a branch and open a pull request into `main`. Keep pull requests small.
- Never commit the data pack or anything in `out/`.
- If you change a field in `docs/CONTRACT.md`, say so in the pull request title.
