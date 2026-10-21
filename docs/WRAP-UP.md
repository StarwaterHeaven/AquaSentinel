# Wrap-up: after the 17 Oct 2026 pitch

Team Ocean presented AquaSentinel at the Water Care AI Hackathon 2026 (Track B, challenge B1) at 18:00 on 17 October 2026. This page records the final state of the build, what is still running, and what we learned. Kijana District is fictional and all data is synthetic.

## Demo video

[![AquaSentinel demo walkthrough](demo/aquasentinel-demo-poster.jpg)](demo/aquasentinel-demo.mp4)

[`demo/aquasentinel-demo.mp4`](demo/aquasentinel-demo.mp4) (2 minutes, no sound, captions on screen) follows the pitch click path in [`DEMO-SCRIPT.md`](DEMO-SCRIPT.md) on the published console:

1. The officer view: 1,078 water points scored out of 100, with the not-working ones first.
2. Olagoni Shallow Well (KJ-WP-0631): the five 20-point parts and the reasons.
3. The officer approves the alert. Nothing goes out without approval.
4. The committee phone receives the alert and replies BROKEN.
5. A red bar on the officer view, then the to-do list.
6. A WhatsApp report through Torque: the store asks which of the four Olagoni pumps, the committee answers 0631, and the report lands in the console.
7. Funding and proof: a sponsor funds 0631; the sponsor, officer and committee views show the same money trail, including the live Qatom sponsorship from 17 Oct.
8. The running receipt of every metered action.

How it was made: [`scripts/demo/record_demo.py`](../scripts/demo/record_demo.py) drives the gh-pages build in Chromium. Payments in the video are the public build's simulated payments. The WhatsApp segment is a **re-enactment** of the live test run with Hassan and Torque on 17 Oct: the report-store replies come from the Worker's own `assess()` code ([`scripts/demo/torque_replay.json`](../scripts/demo/torque_replay.json)), and the chat panel is drawn by the recording script. The two Qatom transactions named in the video are real (below).

## What was live on 17 Oct

| Piece | Where | State after the event |
|---|---|---|
| Public console | https://starwaterheaven.github.io/AquaSentinel/ (gh-pages, built from `main` at 76d9e16) | Live. Payments simulated and labelled. |
| Report store | Cloudflare Worker `aquasentinel-reports` (Durable Object `ReportLog`), source in [`torque/worker/`](../torque/worker/) | Live. Public read `/reports`, free `/check`; writes need the secret path. |
| Qatom item 212 | AquaSentinel: sponsor a Kijana water point, $1 | Live, demo item. Live transaction `91ca3e13-86db-49fd-a584-ee507eb9f8de` ($1 sponsorship of KJ-WP-0631). |
| Qatom item 213 | AquaSentinel: send an approved water alert, $0.02 | Live, demo item. Live transaction `9d919d86-a347-4e0b-8d26-7fb395bbca91`. |
| Qatom item 214 | AquaSentinel: submit a water report, $0.001 | Live, demo item. Endpoint is the report store's secret write path. |
| Torque | The team's Muse agent on WhatsApp, and iMessage/SMS through Inkbox | Briefed with the webhook and item 214 ([`TORQUE.md`](TORQUE.md)). |

### Decisions still open (owner: Hassan)

- **Items 212 to 214.** They were kept live "until judging ends". Items 212 and 213 point at a test echo endpoint and deliver nothing beyond a receipt. Either archive all three, or keep them as a labelled demo and let the catalog Scorecard score them as they stand.
- **Report store write path.** The secret path was shared with Torque by email for the demo. If the store stays up, rotate it (`bash torque/deploy.sh` makes a new one when the secret file is removed) and re-brief Torque; if not, delete the Worker.
- **Public demo.** Keep the gh-pages site up as the team's showcase, or archive the repo read-only.

## Known issues

- A WhatsApp report that can't be placed yet (the store asked back for the pump number) is metered to the district escrow. If the district escrow is empty, the escrows table shows −$0.001 there (seen in the video). Fix: don't meter an ask-back to an escrow, or charge it to the reporting channel's own line.
- The console polls the report store every 4 seconds from every open window. That is fine for a demo, but at district scale it should poll less often or receive pushed updates.
- The committee phone in the console is an SMS-style simulation, not a cellular connection. Committees reach Torque on real WhatsApp, iMessage or SMS.

## What we learned (carried into the Qatom guides)

1. **An agent can be the front door.** Committees message Torque in their own words. Torque submits whatever it has, and the store returns `accepted`, a `need` list, `candidates` and the exact `reply` to send back. The store decides; the messaging agent only relays. Wrong pump numbers are never guessed.
2. **An incomplete report is an answer, not an error.** Asking back is a 200 with `accepted: false`, so it works the same over the free webhook and over a paid Qatom call (Qatom shows non-2xx replies to the buyer as a paywall error).
3. **One handler, two doors.** The free webhook and Qatom item 214 run the same code with the same body. The paid door adds a per-report receipt, not a different behaviour.
4. **A free preview that stores nothing.** `/check` shows what a submit would do, so an agent can test without writing or paying.
5. **Ask for structured fields, but read loose ones too.** Torque first put the channel inside the reporter label. We added an explicit `channel` field with a default, and the console still reads the old form, so nothing broke mid-demo.
6. **Public feeds are masked by design.** Only the last 3 digits of a phone number are kept.
7. **Rehearsals need a reset.** `/reset/<secret>` and the console's Reset demo cleared test reports before the pitch.
8. **The live payment step needs its approval planned in advance.** Each live purchase waited for Hassan's approval in the TODAQ app. We ran the two live transactions in the morning and replayed them in the public build, so the pitch never depended on an approval arriving on stage.
9. **Polling stays off Qatom.** The console reads the free public feed directly, so it spends none of the seller plan's monthly transactions.
