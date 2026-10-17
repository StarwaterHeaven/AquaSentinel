# Pitch script: 5 minutes, 18:00

Presenter: **Vladyslav**. Committee phone: **Ruth**, if she is there. Otherwise Vladyslav uses the second window himself.

## Set up by 17:40

1. Laptop with two browser windows, side by side:
   - Window A: https://starwaterheaven.github.io/AquaSentinel/ (Water officer)
   - Window B: https://starwaterheaven.github.io/AquaSentinel/#phone (Committee phone, "Olagoni committee chair" selected)
   Both must be in the same browser so they stay in sync.
2. In window A press **Reset demo** (top right), so Olagoni is not yet approved.
3. Have the flood messages CSV on the desktop if the organisers released it.
4. Deck open as PDF: `docs/AquaSentinel-TeamOcean-deck.pdf` (slides are numbered below).
5. Fallback if the Wi-Fi fails: the same page opens from a local copy (`out/site/index.html` after `python app/build.py`), or present from the deck alone; slide 15 lists the real Qatom transaction IDs.

## Timing

| Time | Slide or screen | What to say (your own words are fine) |
|---|---|---|
| 0:00–0:30 | 1 Cover | "AquaSentinel gives every water point in Kijana District a score out of 100, puts the broken ones first, and makes every action and every dollar traceable." |
| 0:30–1:15 | 2 Stakes, 3 Problem | "About a third of the district's 1,042 water points are down. The register says 79% work, but its median record is 593 days old. A district-funded repair takes 84 days; a pooled-fund repair takes 0. The delay is about who pays, not who notices." |
| 1:15–1:40 | 4 Which number we trust | "We trust 71% as a ceiling: 384 of the 'working' points have no fresh evidence. Until they're checked, the truth is between 65 and 71." |
| 1:40–3:30 | **Live demo** (switch to the browser) | See the click path below. |
| 3:30–4:00 | 8 How the score works, 10 People | "Five parts of 20, every reason shown. Not working always goes first. Joseph approves everything. Bibi Amina has no phone, so silence puts her pump on the inspection list instead of being read as 'working'." |
| 4:00–4:30 | 12 Cost | "About $3.50 to $7.30 per water point per year. The whole district fits inside its existing monitoring budget line. Repairs get new money from sponsors through escrow, with a receipt for every dollar." |
| 4:30–5:00 | 15 Build and testing | "Before anyone relies on it: backtest against the next inspection round, test the Swahili SMS with committees, pilot the plates in one sub-county." Close: "The data exists. The phones exist. What was missing is a list the officer can defend and money anyone can trace." |

## Live demo click path (about 2 minutes)

1. **Window A, Water officer.** Point at the top tiles: "311 not working, at the top of the list." Point at the map: "Every dot is a water point, coloured by score."
2. Click **Olagoni Shallow Well, 26**. "Five parts, each out of 20, and the reasons in plain words: reported broken by text a year ago and nobody came, E. coli in its last test, no tariff, no savings."
3. "Nothing goes out without the officer." Press **Approve and send**. (In this public build the payment is labelled Simulated; say: "This morning we ran this exact step live on Qatom. The receipts are in the proof view.")
4. **Window B, Committee phone.** The alert has arrived. Press **OK** or **BROKEN**. "The committee replies with one word."
5. **Window A.** The score changes and the report appears. "The officer sees it straight away."
6. Optional, if the flood CSV is there: **Import messages (CSV)** in window A. "Here are today's flood reports: each matched to a water point and rescored, and the ones we can't place go to the officer."
7. Open **Funding and proof** (tab in window A). Show the escrows table and the **Committee** proof for 0631: "$1 from a sponsor this morning, live on Qatom, transaction 91ca3e13. The sponsor, the officer and the committee each see where it went."

## If a judge asks

- **"Is the payment real?"** Yes: two live Qatom transactions today, 91ca3e13 ($1 sponsorship, item 212) and 9d919d86 ($0.02 officer-approved alert, item 213). The public page replays them; new payments on this page are simulated and labelled.
- **"What if the score is wrong?"** The officer edits or rejects; every decision is recorded. The score advises, people decide.
- **"Is the water safe?"** No score can say so. Only a lab test can, and the alerts carry boil-water advice until one is done.
- **"Why 20 points each?"** Equal weights are easy to defend and change; the backtest tells us where to move them.
- **"Who might it leave out?"** Settlements with no signal and no visit. The silence list and mechanic visits are the answer; that's the first thing to field-test.
