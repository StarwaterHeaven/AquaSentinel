# Pitch script: 5 minutes, 18:00

Presenter: **Vladyslav**. Committee phone: **Ruth**, if she is there. Otherwise Vladyslav uses the second window himself.

## Set up by 17:40

1. Laptop with two browser windows, side by side:
   - Window A: https://starwaterheaven.github.io/AquaSentinel/ (Water officer)
   - Window B: https://starwaterheaven.github.io/AquaSentinel/#phone (Committee phone, "Olagoni committee chair" selected)
   Both must be in the same browser so they stay in sync.
2. In window A press **Reset demo** (top right), so Olagoni is not yet approved.
3. Have the flood messages CSV on the desktop if the organisers released it.
4. Deck open as PDF: `docs/AquaSentinel-TeamOcean-deck.pdf`. Slides 1–6 are the pitch; 7–21 are the appendix.
5. Fallback if the Wi-Fi fails: the same page opens from a local copy (`out/site/index.html` after `python app/build.py`), or present from the deck alone; slide 4 lists the real Qatom transaction IDs.

## Timing (pitch deck slides 1–6; slides 7–21 are the appendix for questions)

| Time | Slide or screen | What to say (your own words are fine) |
|---|---|---|
| 0:00–0:20 | 1 Cover | "AquaSentinel gives every water point in Kijana District a score out of 100, puts the broken ones first, and makes every action and every dollar traceable." |
| 0:20–0:50 | 2 The problem | "By the newest evidence 71% of water points work; the register says 79%, but its median record is 593 days old. A district-funded repair takes 84 days; a pooled-fund repair takes 0. The delay is about who pays, not who notices." |
| 0:50–1:20 | 3 What we built | One line per box: score, approve, text, prove. "Running now on all 1,078 water points. Let us show you." |
| 1:20–3:20 | 4 Live demo (switch to the browser) | See the click path below. Leave slide 4 up while you switch; it is the backup if the browser fails. |
| 3:20–4:05 | 5 In real life | "The officer owns it and approves everything. People like Bibi Amina, with no phone, are covered: silence puts the pump on the inspection round. About $3.50 to $7.30 per water point per year, inside the district's existing monitoring budget; sponsors fund repairs through escrow." |
| 4:05–4:40 | 6 Before anyone relies on it | The three tests, then: "The data exists. The phones exist. We built the list the officer can defend and the money trail anyone can check." |
| 4:40–5:00 | | "Thank you." Take questions; use the appendix (slide 7 onwards) for detail. |

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
