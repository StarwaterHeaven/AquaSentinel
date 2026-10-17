# Torque: AquaSentinel's WhatsApp and text contact

Torque is the team's Muse agent. Committees can reach it on WhatsApp or by text (iMessage/SMS through Inkbox: first send `connect @torque` to +1 (557) 234-1193). In the demo it is the number a water committee messages. Torque reads the report, asks back when something is missing, and submits complete reports to AquaSentinel. The officer console shows each report within a few seconds and rescores the water point.

> Synthetic hackathon scenario. Kijana District is fictional. Torque must never say that water is safe to drink.

## How it fits

```
Committee member --WhatsApp--> Torque --(webhook or Qatom item, $0.001)--> report store --> officer console
        ^                        |
        +---- reply / ask-back --+
```

- **Report store:** Cloudflare Worker `aquasentinel-reports` (`torque/worker/`). It stores reports and answers what to say back.
- **Public read:** `https://aquasentinel-reports.hassan-khan-cd6.workers.dev/reports`. The console polls this every 4 seconds. Phone numbers are masked.
- **Free check:** `GET /check?wp_id=0631&status=broken&message=...` returns what a submit would do and stores nothing.
- **Writes:** these need the secret path. It is never in this repo; Hassan holds it.
  - `POST /in/<secret>`: Torque's webhook.
  - `POST /q/<secret>`: the endpoint of Qatom catalog item 214, "AquaSentinel: submit a water report (hackathon demo)", priced at $0.001 per report. Every report bought this way has a receipt.

## What Torque sends

JSON body, every field optional:

| Field | Example | Notes |
|---|---|---|
| `wp_id` | `0631`, `KJ-WP-0631`, `Olagoni` | 4-digit pump number, full ID or village name |
| `status` | `OK`, `BROKEN`, `DRY`, `DIRTY` | Words work too: "imeharibika", "chafu", "fixed" |
| `message` | `0631 pump imeharibika` | The sender's WhatsApp text, as sent |
| `reporter` | `Olagoni committee chair` | How the console labels the sender |
| `phone` | `+254700000631` | Stored as the last 3 digits only |
| `channel` | `WhatsApp`, `iMessage`, `SMS` | Shown on the officer's screen; default WhatsApp |

## What comes back

- **Complete report:** `accepted: true`, the `wp_id`, `name` and `status`, plus a `reply` to send to the committee.
- **Missing something:** `accepted: false`, a `need` list (`wp_id`, `status`), any `candidates` (for example, the 2 water points in a village), and a `reply` that asks the right question.

Torque sends the `reply` back on WhatsApp in the sender's language (Swahili if they wrote in Swahili). When the person answers, Torque submits again with the earlier message and the answer combined.

## Instructions to paste into Torque

Replace `<WEBHOOK>` with the `TORQUE_WEBHOOK` line from Hassan's secret file before pasting. Do not paste the secret anywhere public.

```
You are Torque, the WhatsApp contact for AquaSentinel, a district water service in Kijana District (a fictional hackathon scenario, synthetic data). Water committee members message you about their water point (hand pump, borehole, well, tap).

Your job:
1. Read each message. Find (a) which water point: the 4-digit number painted on the pump (e.g. 0631), the full ID (KJ-WP-0631), or the village name; and (b) its state: OK (working), BROKEN (not working), DRY (no water at the source), or DIRTY (dirty, smelly or discoloured water, or flood water).
2. Submit it straight away: POST JSON to <WEBHOOK> with fields wp_id, status, message (their exact words), reporter (their name or role if known) and phone. If you only have part of it, submit anyway with what you have.
   (Alternative: buy Qatom catalog item "AquaSentinel: submit a water report" with the same fields as arguments.)
3. The response has "accepted" and a "reply". Send the reply back to the person on WhatsApp, in their language (Swahili if they wrote in Swahili, English otherwise). Keep it short and friendly.
4. If accepted is false, the reply asks for what is missing (the pump number or the state). When they answer, submit again with wp_id and status filled in from the whole conversation.
5. If "candidates" are listed, offer those numbers and names; never guess or invent a pump number.
6. Never say water is safe to drink. For DIRTY reports, always add: boil drinking water until it has been tested.
7. If someone reports an emergency (injury, contamination making people ill), tell them to contact the district water office or health centre directly as well.
```

## Demo script (about 30 seconds)

1. On a phone, WhatsApp Torque, or text it (after `connect @torque` to +1 (557) 234-1193): "Olagoni pump imeharibika tena".
2. Torque asks which of the 4 Olagoni water points (0631, 0681, 0609, 0682).
3. Reply "0631".
4. Torque confirms. In the officer console, Olagoni 0631 shows the WhatsApp report and its new score, and the Committee phone tab's log shows "WhatsApp via Torque".

If Torque or WhatsApp is not available on stage, use the Committee phone tab, which reads the same words.

## Rehearsal reset

`POST /reset/<secret>` clears the stored reports. "Reset demo" in the console also ignores reports received before the reset.
