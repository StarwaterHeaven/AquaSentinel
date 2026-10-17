# Tasks for today

Each task has a brief you can paste into your own AI assistant, together with this repo. Open a pull request when a piece is done; small and often is better than one big one at the end.

| Time | Milestone |
|---|---|
| 13:00 | Flood inject released to teams: run it through the pipeline |
| 14:30 | Check-in: console runs end to end |
| 16:00 | Freeze: no new features |
| 16:00–17:00 | Two full rehearsals; deck final |

## Vladyslav: prove the score works

**1. Backtest (most important: it gives the deck its headline number).**
Brief: *"In this repo, `scoring/score.py` scores Kijana water points as of 30 Sep 2026. Make `scoring/backtest.py` that scores every point using only records dated before 1 Jan 2024 (register status dates, inspections, job cards, messages, water tests, rainfall), then compares against what the August 2025 verification survey (`data/kijana_verification_survey_2025.csv`) and the 2024 inspection round actually observed. Report: of the points we flagged Not working or Critical, what share were found non-functional; of the points found non-functional, what share we had flagged; and the same for points we called Silent. Print a short table and write `out/backtest.md`."*

**2. Message reading.**
Brief: *"`data/kijana_community_messages_labelled_sample.csv` has 450 hand-labelled messages (`category`, `wp_id_resolved`). Measure how well the `cat()` and `resolve()` functions in `scoring/score.py` match those labels (category accuracy, water-point match rate). Then improve them: better Swahili/English keywords, and village-name matching that handles spelling variants. Keep the same function names and return values."*

**3. 13:00 flood inject.** When it is released, run it through the message reader and post the list of affected water points as a pull request (`out/` stays local; put the list in the PR description).

## Ruth: field and community side

**1. Test the SMS flow.** Open the published console, switch to "Committee phone", and try every reply from each demo phone, including the shared phone and the unregistered number. Note anything a committee member would find unclear and open an issue or a PR against the text in `app/app.template.html` (search for `WATER ALERT` and `Thank you`).

**2. Water-point plate.** Design the plate fixed to each pump: the water point's 4-digit number and the line to text (e.g. "Water point 0631 · Text 0631 BROKEN to the Kijana Water Line"). One image, PNG or SVG, in `docs/plate.png` or `docs/plate.svg`.

**3. Silence list review.** Our fairness point: points with no fresh evidence are flagged for inspection, and 127 settlements have no phone signal at all. Brief for your AI: *"Using `out/water_point_scores.csv` and `data/kijana_settlements.csv`, list which sub-counties and settlement types dominate the Silent list, how many people live in no-signal settlements, and which of the case pack's personas (Bibi Amina, Halima, Mama Rehema) this list protects. Write it as five bullet points for a slide."*

**4. On stage.** You play the committee member who texts BROKEN during the demo.

## Wizard Kepler: build

Console (officer view, committee phone, receipt), Agentic Commerce Infra layer (sponsor funding into district or village escrows, proof views, one live Qatom step), deck and architecture doc. Merges everyone's pull requests.

## Hassan

Decisions on weights, wording and scope; the Qatom wallet and approval link for the live step; the pitch, demo script and judges' Q&A.
