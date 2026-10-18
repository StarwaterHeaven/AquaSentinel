"""Record the AquaSentinel demo walkthrough (docs/demo/aquasentinel-demo.mp4).

Plays the docs/DEMO-SCRIPT.md click path on the published console build and adds
captions. The report store (Cloudflare Worker) is answered locally with the two
records in torque_replay.json, which were produced by the Worker's own assess()
code: a re-enactment of the 17 Oct live WhatsApp test through Torque.

Usage (Python 3 with playwright; ffmpeg for the mp4):
  git archive origin/gh-pages | tar -x -C /tmp/site     # or out/site after app/build.py
  (cd /tmp/site && python3 -m http.server 8765 &)
  python3 scripts/demo/record_demo.py /tmp/rec            # writes /tmp/rec/vid/*.webm
  ffmpeg -ss 2.9 -i /tmp/rec/vid/*.webm -c:v libx264 -crf 26 -pix_fmt yuv420p \
         -movflags +faststart -an docs/demo/aquasentinel-demo.mp4
"""
import asyncio, json, os, sys, time
from playwright.async_api import async_playwright

SP = sys.argv[1]
os.makedirs(SP, exist_ok=True)
RECS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "torque_replay.json")))
W, H = 1440, 900

INIT = r"""
(() => {
  const css = `
  #__cap{position:fixed;left:50%;bottom:28px;transform:translateX(-50%);max-width:1100px;z-index:99999;
    background:rgba(16,32,36,.92);color:#fff;font:500 21px/1.4 Inter,system-ui,sans-serif;padding:14px 24px;border-radius:12px;
    box-shadow:0 8px 30px rgba(0,0,0,.25);transition:opacity .35s;opacity:0;text-align:center}
  #__cap small{display:block;font-size:14px;opacity:.75;font-weight:400;margin-top:4px}
  #__card{position:fixed;inset:0;z-index:100000;background:#0f2a2e;color:#fff;display:flex;flex-direction:column;
    align-items:center;justify-content:center;text-align:center;font-family:Inter,system-ui,sans-serif;transition:opacity .5s;opacity:0;pointer-events:none}
  #__card h1{font-size:56px;margin:0 0 10px;font-weight:700;letter-spacing:-1px}
  #__card p{font-size:22px;margin:6px 0;opacity:.88;max-width:1050px;line-height:1.45}
  #__card .k{font-size:15px;opacity:.6;margin-top:26px}
  #__cur{position:fixed;width:26px;height:26px;margin:-13px 0 0 -13px;border-radius:50%;z-index:99998;pointer-events:none;
    background:rgba(214,64,52,.35);border:2px solid rgba(214,64,52,.95);transition:left .6s ease,top .6s ease,transform .15s;left:720px;top:450px}
  #__cur.c{transform:scale(.6)}
  #__wa{position:fixed;right:26px;top:120px;width:330px;z-index:99997;background:#e9e2d7;border-radius:22px;
    box-shadow:0 12px 40px rgba(0,0,0,.3);overflow:hidden;font:15px/1.35 system-ui,sans-serif;transition:opacity .4s;opacity:0}
  #__wa .hd{background:#075e54;color:#fff;padding:12px 16px;font-weight:600}
  #__wa .hd span{display:block;font-weight:400;font-size:12px;opacity:.8}
  #__wa .bd{padding:12px;min-height:330px;display:flex;flex-direction:column;gap:8px}
  #__wa .m{max-width:85%;padding:8px 11px;border-radius:9px;box-shadow:0 1px 1px rgba(0,0,0,.12);animation:pop .3s}
  #__wa .o{align-self:flex-end;background:#d9fdd3}
  #__wa .i{align-self:flex-start;background:#fff}
  @keyframes pop{from{transform:scale(.9);opacity:0}to{transform:none;opacity:1}}`;
  const add = () => {
    if (document.getElementById('__cap')) return;
    const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s);
    for (const id of ['__cap','__card','__cur']) { const d = document.createElement('div'); d.id = id; document.body.appendChild(d); }
    const wa = document.createElement('div'); wa.id='__wa';
    wa.innerHTML = '<div class="hd">Torque<span>WhatsApp · AquaSentinel contact</span></div><div class="bd"></div>';
    document.body.appendChild(wa);
  };
  window.__cap = (t, sub) => { add(); const c = document.getElementById('__cap'); if (!t) { c.style.opacity=0; return; }
    c.innerHTML = t + (sub ? '<small>'+sub+'</small>' : ''); c.style.opacity = 1; };
  window.__card = (html) => { add(); const c = document.getElementById('__card'); if (!html) { c.style.opacity=0; return; }
    c.innerHTML = html; c.style.opacity = 1; };
  window.__cur = (x, y, click) => { add(); const c = document.getElementById('__cur'); c.style.left = x+'px'; c.style.top = y+'px';
    if (click) { c.classList.add('c'); setTimeout(()=>c.classList.remove('c'), 220); } };
  window.__wa = (show) => { add(); document.getElementById('__wa').style.opacity = show ? 1 : 0; };
  window.__wamsg = (txt, out) => { add(); const b = document.querySelector('#__wa .bd'); const m = document.createElement('div');
    m.className = 'm ' + (out ? 'o' : 'i'); m.textContent = txt; b.appendChild(m); };
  if (document.readyState !== 'loading') add(); else document.addEventListener('DOMContentLoaded', add);
})();
"""

async def main():
    store = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": W, "height": H}, record_video_dir=SP + "/vid",
                                  record_video_size={"width": W, "height": H})
        await ctx.add_init_script(INIT)

        async def reports(route):
            since = 0
            try: since = int(route.request.url.split("since=")[1].split("&")[0])
            except Exception: pass
            await route.fulfill(json={"reports": [r for r in store if r["at"] > since], "now": int(time.time()*1000)},
                                headers={"access-control-allow-origin": "*"})
        await ctx.route("**/*workers.dev/**", reports)
        pg = await ctx.new_page()

        async def sleep(s): await pg.wait_for_timeout(int(s * 1000))
        async def cap(t, sub=None): await pg.evaluate("([t,s]) => __cap(t,s)", [t, sub])
        async def card(h): await pg.evaluate("h => __card(h)", h)
        async def point(sel, click=True, pause=0.7):
            loc = pg.locator(sel).first
            await loc.scroll_into_view_if_needed()
            bb = await loc.bounding_box()
            x, y = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
            await pg.evaluate("([x,y]) => __cur(x,y,false)", [x, y]); await sleep(pause)
            if click:
                await pg.evaluate("([x,y]) => __cur(x,y,true)", [x, y]); await loc.evaluate("e => e.click()"); await sleep(0.4)

        await pg.goto("http://localhost:8765/index.html")
        await sleep(1.5)
        await card("<h1>AquaSentinel</h1><p>Water security and service intelligence for Kijana District</p>"
                   "<p>Team Ocean · Water Care AI Hackathon 2026 · Track B, challenge B1</p>"
                   "<p class='k'>Demo walkthrough of the published console. Kijana District is fictional and all data is synthetic.<br>"
                   "A score is not a water-safety finding: only a lab test can show water is safe to drink.</p>")
        await sleep(6); await card(None); await sleep(0.8)

        # 1. officer view
        await cap("Every one of Kijana's 1,078 water points gets a score out of 100.", "The 323 that are not working go first, whatever their score.")
        await point("#kpis >> text=Not working", click=False, pause=1.2); await sleep(3.5)
        await point("#map", click=False, pause=0.5)
        await cap("Every dot on the map is a water point, coloured by score.", "The close-up follows the selected point: Olagoni Shallow Well, KJ-WP-0631.")
        await sleep(4.5)

        # 2. detail
        await point("#detail", click=False, pause=0.6)
        await cap("Olagoni Shallow Well: 26 out of 100, Critical.", "Five parts worth 20 points each, and the reasons in plain words.")
        await sleep(5)
        await cap("The suggested actions: send the nearest mechanic, boil-water advice and a retest, committee support.",
                  "The SMS to the committee is written for the officer to review and edit.")
        await pg.locator("#smstext").first.scroll_into_view_if_needed(); await sleep(4.5)

        # 3. approve
        await cap("Nothing goes out without the officer.", "Approve and send. In this public build the payment is simulated; the live run was paid on Qatom.")
        await point("#approve", pause=1.0); await sleep(3.5)

        # 4. committee phone
        await cap("The committee's phone receives the alert.", "Plain SMS, works on a basic phone. They reply with one word.")
        await point("header.top >> text=Committee phone", pause=0.6); await sleep(3)
        await point("#v-phone button:has-text('BROKEN')", pause=1.0)
        await cap("The committee replies BROKEN.", "The reply is read in English or Swahili, matched to the pump and logged.")
        await sleep(4)

        # 5. officer red bar + to-do
        await point("header.top >> text=Water officer", pause=0.6)
        await cap("Back with the officer: a red bar says a new report needs a decision.", "The Water officer tab shows the count.")
        await pg.evaluate("window.scrollTo(0,0)"); await sleep(4)
        await point("#gotodo", pause=0.8)
        await cap("The to-do list: urgent reports first, then broken pumps nobody has been sent to,",
                  "then repair job cards to chase, then silent pumps to inspect. Approving clears it.")
        await sleep(5.5)

        # 6. Torque on WhatsApp
        await pg.evaluate("window.scrollTo(0,0)")
        await point("header.top >> text=Committee phone", pause=0.6)
        await cap("Committees can also use WhatsApp or text, through Torque, the team's messaging agent.",
                  "Re-enactment of the 17 Oct live test. Torque submits each report to the AquaSentinel report store.")
        await pg.evaluate("__wa(true)"); await sleep(2.5)
        await pg.evaluate("t => __wamsg(t, true)", RECS[0]["message"]); await sleep(1.5)
        r1 = dict(RECS[0]); r1["at"] = int(time.time() * 1000); store.append(r1)
        await sleep(2.5)
        await pg.evaluate("t => __wamsg(t, false)", "Asante. Kuna pampu 4 Olagoni: 0631, 0681, 0609, 0682. Ni ipi? Tuma namba iliyopakwa kwenye pampu.")
        await cap("Olagoni has four pumps, so the report store asks back instead of guessing.",
                  "Torque replies in Swahili because the committee wrote in Swahili.")
        await sleep(5)
        await pg.evaluate("t => __wamsg(t, true)", "0631"); await sleep(1.5)
        r2 = dict(RECS[1]); r2["at"] = int(time.time() * 1000); store.append(r2)
        await sleep(3)
        await pg.evaluate("t => __wamsg(t, false)", "Asante. 0631 Olagoni Shallow Well imerekodiwa kuwa haifanyi kazi. Afisa wa maji wa wilaya anaiona sasa.")
        await cap("The complete report lands in the console within seconds: \"WhatsApp via Torque\".",
                  "The pump is rescored. Phone numbers in the public feed are masked.")
        await sleep(6.5)
        await pg.evaluate("__wa(false)")

        # 7. funding and proof
        await point("header.top >> text=Funding and proof", pause=0.6)
        await cap("Sponsors fund a water point, or the whole district, into an escrow.",
                  "On Qatom each dollar is a payment with its own record.")
        await sleep(3.5)
        await point("#fundbtn", pause=0.9); await sleep(2.5)
        await point("#proofseg >> text=Committee", pause=0.8)
        await cap("The same money trail, seen by the sponsor, the officer and the committee.",
                  "Live on Qatom on 17 Oct: transaction 91ca3e13, a $1 sponsorship of 0631 (catalog item 212).")
        await sleep(6)

        # 8. receipt
        await point("header.top >> text=Receipt", pause=0.6)
        await cap("The running receipt: every metered action, from scoring calls to each SMS.",
                  "About $3.50 to $7.30 per water point per year, inside the district's monitoring budget (scenario estimate).")
        await sleep(6)
        await cap(None)

        await card("<h1>AquaSentinel</h1>"
                   "<p>Scores every water point, puts the broken ones first, the officer approves every action,<br>committees report by SMS or WhatsApp, and every dollar has a receipt.</p>"
                   "<p>Live on Qatom, 17 Oct 2026: 91ca3e13 ($1 sponsorship, item 212) · 9d919d86 ($0.02 approved alert, item 213)</p>"
                   "<p>github.com/StarwaterHeaven/AquaSentinel · starwaterheaven.github.io/AquaSentinel</p>"
                   "<p class='k'>Team Ocean: Vladyslav, Ruth and Hassan, with Wizard Kepler (build) and Torque (WhatsApp and text).<br>"
                   "Synthetic scenario. Scenario results only; no score shows that water is safe to drink.</p>")
        await sleep(7)
        await ctx.close(); await b.close()

asyncio.run(main())
