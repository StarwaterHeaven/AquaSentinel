# Notes for AI assistants working in this repo

- Read `docs/CONTRACT.md` before changing anything that crosses between scoring and the app. Keep field names stable.
- The Kijana data pack lives in `data/` locally and must never be committed. Nothing in `out/` is committed either.
- All data is synthetic. Never write text that presents a score or prediction as showing water is safe to drink.
- Five scoring dimensions at 20 points each; any non-working point is flagged and listed first. Keep `view()` in `app/app.template.html` in step with `scoring/score.py`.
- The demo is in English. Keep the SMS reader accepting the common Swahili words listed in the contract.
- Do not use the mentor Staff Pack or the 1pm inject before it is released to teams.
- Small pull requests into `main`; describe what changed and how you checked it.
