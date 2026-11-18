// AquaSentinel report store for Torque (WhatsApp) and the Qatom report item.
//
// Writes need the secret path (a Worker secret, WRITE_PATH):
//   POST /in/<WRITE_PATH>     Torque's webhook
//   POST /q/<WRITE_PATH>      the Qatom catalog item's endpoint (same body)
//   POST /reset/<WRITE_PATH>  clear the log (rehearsal only)
// Public, read-only:
//   GET  /reports?since=<ms>  recent reports for the console (phone numbers masked)
//   GET  /check?wp_id=&status=&message=   what a submit would do, stores nothing
//   GET  /health
// Live sponsorships (real payments, zero simulation; Hassan 26 Oct 2026):
//   POST /fund/start          {wp_id, sponsor} -> a Qatom checkout for the $1 sponsor item (FUND_ITEM)
//   GET  /fund/<ref>          status of one sponsorship
//   GET  /funds               every paid sponsorship, with its Qatom transaction (public)
//   POST /qatom/fund[/...]    item 212's endpoint (Authorization: Bearer QATOM_FULFILMENT_TOKEN); verifies
//                             the sale with Qatom, then records it once per transaction
// Kijana is fictional; Qatom donates the total collected by this demo to WaterAid Canada.
//
// Body (JSON, form or query): wp_id (KJ-WP-0631, 0631 or a village name), status
// (OK, BROKEN, DRY, DIRTY, or words), message (the text as sent), reporter, phone,
// channel (WhatsApp, iMessage or SMS; default WhatsApp).
// A report needs a water point and a status. If either is missing the answer has
// accepted:false, a `need` list and a `reply` for Torque to send back.
// Synthetic scenario data: nothing here says water is safe to drink.

import { POINTS } from "./points.mjs";

const BY = new Map(POINTS.map(p => [p[0], p]));
const VILLAGES = new Map();
for (const [id, , v] of POINTS) if (v.length > 2) { if (!VILLAGES.has(v)) VILLAGES.set(v, []); VILLAGES.get(v).push(id); }
const VNAMES = [...VILLAGES.keys()].sort((a, b) => b.length - a.length);

const API = "https://pay.m.todaq.net";
const FUND_NOTE = "Kijana District is fictional. Every sponsorship is a real payment; Qatom will donate the total collected by this demo to WaterAid Canada.";
const rand = n => { const a = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789", b = crypto.getRandomValues(new Uint8Array(n)); return [...b].map(x => a[x % a.length]).join(""); };
const clean = (v, n) => String(v ?? "").replace(/[\u0000-\u001f<>]/g, " ").replace(/\s+/g, " ").trim().slice(0, n);
function same(a, b) { if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length || !b) return false; let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i); return d === 0; }
let tok = null;
async function qatomToken(env) {
  if (!env.QATOM_CLIENT_ID || !env.QATOM_CLIENT_SECRET) return null;
  if (tok && tok.expires_at * 1000 > Date.now() + 300000) return tok.access_token;
  const r = await fetch(API + "/v4/account/oauth/token", { method: "POST", headers: { authorization: "Basic " + btoa(env.QATOM_CLIENT_ID + ":" + env.QATOM_CLIENT_SECRET) } });
  if (!r.ok) return null;
  tok = await r.json();
  return tok.access_token;
}
const fundWp = v => { const id = String(v || "").trim().toUpperCase(); if (id === "DISTRICT") return "DISTRICT"; const m = id.match(/(\d{4})$/); return m && BY.has("KJ-WP-" + m[1]) ? "KJ-WP-" + m[1] : null; };
const publicFund = f => ({ ref: f.ref, status: f.status, wp_id: f.wp, sponsor: f.sponsor, amount: f.amount, at: f.paid_at || f.created_at, transaction_id: f.tx || null, checkout_url: f.status === "pending" ? f.checkout_url : null, via: f.via });

const CORS = { "access-control-allow-origin": "*", "access-control-allow-methods": "GET,POST,OPTIONS", "access-control-allow-headers": "content-type" };
const json = (x, status = 200) => new Response(JSON.stringify(x, null, 1), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...CORS } });

// Weighted keywords, English and common Swahili (same stems as scoring/score.py v0.4).
const KW = {
  DIRTY: [["chafu", 2], ["dirty", 2], ["smell", 2], ["harufu", 2], ["kutu", 2], ["rangi", 2], ["colour", 2], ["color", 2], ["taste", 1], ["ladha", 2], ["tumbo", 2], ["diarr", 2], ["kuhara", 2], ["turbid", 2], ["muddy", 2], ["matope", 2], ["brown", 1], ["flood", 2], ["mafuriko", 2]],
  BROKEN: [["not working", 3], ["broken", 3], ["broke", 2], ["imeharibika", 3], ["imekufa", 3], ["mbovu", 2], ["hakuna maji", 2], ["haitoi", 3], ["spoilt", 2], ["imevunjika", 3], ["imekataa", 3], ["no water", 1], ["still waiting", 2], ["bado", 1], ["handle", 1], ["leak", 1]],
  DRY: [["imekauka", 3], ["kimekauka", 3], ["kavu", 3], ["source dry", 3], ["well dry", 3], ["dried", 2], ["dry", 2]],
  OK: [["fixed", 3], ["imetengenezwa", 3], ["inafanya kazi", 3], ["working now", 3], ["repaired", 3], ["imerekebishwa", 3], ["back to normal", 3], ["working", 2], ["sawa", 2], ["ok", 2], ["okay", 2], ["good", 1]]
};
const ORDER = ["DIRTY", "BROKEN", "DRY", "OK"]; // ties go to the status that drives action
const LABEL = { OK: "working", BROKEN: "not working", DRY: "dry", DIRTY: "dirty water" };

function statusOf(field, text) {
  const f = String(field || "").trim().toUpperCase();
  if (LABEL[f]) return f;
  const t = " " + (String(field || "") + " " + String(text || "")).toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ") + " ";
  const has = kw => kw.length <= 3 ? t.includes(" " + kw + " ") : t.includes(kw);
  const sc = Object.fromEntries(ORDER.map(k => [k, KW[k].reduce((a, [kw, w]) => a + (has(kw) ? w : 0), 0)]));
  if (sc.OK && /not working|haifanyi kazi/.test(t)) sc.OK = 0;
  const best = ORDER.reduce((a, k) => (sc[k] > sc[a] ? k : a), ORDER[0]);
  return sc[best] > 0 ? best : null;
}

function lev(a, b) {
  const d = Array.from({ length: a.length + 1 }, (_, i) => [i]);
  for (let j = 1; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
  return d[a.length][b.length];
}

function pointOf(field, text) {
  const all = String(field || "") + " " + String(text || "");
  const m = all.match(/KJ-WP-(\d{4})/i) || all.match(/\b(\d{4})\b/);
  if (m) {
    const id = "KJ-WP-" + m[1];
    if (BY.has(id)) return { wp: id, how: "number" };
    return { wp: null, how: "unknown number", bad: m[1] };
  }
  const t = " " + all.toLowerCase().replace(/[^a-z\s]/g, " ").replace(/\s+/g, " ") + " ";
  for (const v of VNAMES) if (t.includes(" " + v + " ")) return pick(v, t, "village");
  const toks = t.trim().split(" ").filter(x => x.length >= 5);
  let best = null;
  for (const tok of toks) for (const v of VNAMES) {
    if (v.includes(" ") || Math.abs(v.length - tok.length) > 2) continue;
    const r = 1 - lev(tok, v) / Math.max(tok.length, v.length);
    if (r >= 0.8 && (!best || r > best.r)) best = { v, r };
  }
  return best ? pick(best.v, t, "similar village name") : { wp: null, how: "none" };
}
function pick(v, t, how) {
  const ids = VILLAGES.get(v);
  if (ids.length === 1) return { wp: ids[0], how };
  const hints = [["borehole", "borehole"], ["shallow", "shallow well"], ["well", "well"], ["kiosk", "kiosk"], ["tap", "tap"], ["school", "school"], ["solar", "solar"], ["spring", "spring"], ["tank", "tank"], ["piped", "piped"]];
  for (const [w, s] of hints) if (t.includes(" " + w + " ")) {
    const c = ids.filter(id => BY.get(id)[1].toLowerCase().includes(s));
    if (c.length === 1) return { wp: c[0], how: how + " and type" };
  }
  return { wp: null, how: "several water points", ids };
}

function assess(input) {
  const message = String(input.message || input.text || "").slice(0, 500);
  const p = pointOf(input.wp_id || input.code || input.village, message);
  const status = statusOf(input.status, message);
  const out = { accepted: false, wp_id: p.wp, name: p.wp ? BY.get(p.wp)[1] : null, status, label: status ? LABEL[status] : null, matched_by: p.how, need: [], candidates: [] };
  if (!p.wp) out.need.push("wp_id");
  if (!status) out.need.push("status");
  const code = p.wp ? p.wp.slice(-4) : null;
  if (p.ids) out.candidates = p.ids.slice(0, 8).map(id => ({ wp_id: id, code: id.slice(-4), name: BY.get(id)[1] }));
  if (!out.need.length) {
    out.accepted = true;
    out.reply = `Thank you. ${code} ${out.name} is recorded as ${out.label}. The district water officer can see it now.` + (status === "DIRTY" ? " Please boil drinking water until it has been tested." : "");
  } else if (p.ids) {
    out.reply = `Thank you. There are ${p.ids.length} water points there: ` + out.candidates.slice(0, 4).map(c => `${c.code} ${c.name}`).join(", ") + `. Which one? Send the 4-digit number painted on the pump.`;
  } else if (p.bad) {
    out.reply = `Thank you. We could not find water point ${p.bad}. Please check the 4-digit number painted on the pump.`;
  } else if (!p.wp) {
    out.reply = "Thank you. Which water point is this? Please send the 4-digit number painted on the pump, for example 0631.";
  } else {
    out.reply = `Thank you. Is ${code} ${out.name} working (OK), broken (BROKEN), dry (DRY), or is the water dirty (DIRTY)?`;
  }
  return out;
}

async function readInput(req, url) {
  const q = Object.fromEntries(url.searchParams);
  if (req.method !== "POST") return q;
  const ct = req.headers.get("content-type") || "";
  try {
    if (ct.includes("json")) { const b = await req.json(); return { ...q, ...(b && b.arguments ? b.arguments : b) }; }
    if (ct.includes("form")) return { ...q, ...Object.fromEntries(await req.formData()) };
    const t = await req.text();
    try { const b = JSON.parse(t); return { ...q, ...(b && b.arguments ? b.arguments : b) }; } catch { return { ...q, message: t }; }
  } catch { return q; }
}

// Channel from any of the usual field names; falls back to hints in the reporter label.
function chan(input) {
  const f = String(input.channel || input.source || input.medium || input.platform || input.via || "").toLowerCase();
  const h = f || String(input.reporter || "").toLowerCase();
  if (/imessage|apple/.test(h)) return "iMessage";
  if (/\b(sms|text|txt)\b/.test(h)) return "SMS";
  return "WhatsApp";
}

export class ReportLog {
  constructor(ctx) { this.ctx = ctx; }
  async fetch(req) {
    const url = new URL(req.url);
    let ev = (await this.ctx.storage.get("ev")) || [];
    if (url.pathname === "/add") {
      const r = await req.json();
      ev.push(r); if (ev.length > 500) ev = ev.slice(-500);
      await this.ctx.storage.put("ev", ev);
      return json({ ok: true });
    }
    if (url.pathname === "/reset") { await this.ctx.storage.put("ev", []); return json({ ok: true, cleared: ev.length }); }
    // Sponsorships are real money: reset never clears them.
    if (url.pathname.startsWith("/fund")) {
      const funds = (await this.ctx.storage.get("funds")) || {};
      if (url.pathname === "/fund/put") { const f = await req.json(); funds[f.ref] = f; await this.ctx.storage.put("funds", funds); return json({ ok: true }); }
      if (url.pathname === "/fund/get") { const f = funds[url.searchParams.get("ref")]; return f ? json(f) : json({ missing: true }, 404); }
      if (url.pathname === "/fund/tx") { const tx = url.searchParams.get("tx"); return json({ seen: Object.values(funds).some(f => f.tx === tx) }); }
      if (url.pathname === "/funds") return json({ funds: Object.values(funds).filter(f => f.status === "paid").sort((a, b) => a.paid_at.localeCompare(b.paid_at)).map(publicFund), note: FUND_NOTE });
    }
    const since = +url.searchParams.get("since") || 0;
    return json({ reports: ev.filter(r => r.at > since).slice(-200), now: Date.now() });
  }
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
    const log = env.LOG.get(env.LOG.idFromName("kijana"));
    const p = url.pathname.replace(/\/+$/, "");
    if (p === "" || p === "/health") return json({ ok: true, service: "AquaSentinel report store (hackathon demo, synthetic data)", points: POINTS.length });
    if (p === "/reports" && req.method === "GET") return log.fetch(new Request("https://do/list" + url.search));
    if (p === "/check") return json({ preview: true, ...assess(await readInput(req, url)) });
    const dof = (path, body) => log.fetch(new Request("https://do" + path, body === undefined ? {} : { method: "POST", body: JSON.stringify(body) }));
    if (p === "/funds" && req.method === "GET") return dof("/funds");
    if (p === "/fund/start" && req.method === "POST") {
      const b = await readInput(req, url);
      const wp = fundWp(b.wp_id), sponsor = clean(b.sponsor, 40) || "Anonymous sponsor";
      if (!wp) return json({ ok: false, status: "invalid", message: "Choose a Kijana water point or the district escrow." }, 400);
      const t = env.FUND_ITEM ? await qatomToken(env) : null;
      if (!t) return json({ ok: false, status: "payments_unavailable", message: "Payments are not available right now. Nothing was charged." }, 503);
      const ref = "S" + rand(11);
      const r = await fetch(API + "/v4/payment/checkout", { method: "POST", headers: { authorization: "Bearer " + t, "content-type": "application/json" }, body: JSON.stringify({ catalog_item_id: Number(env.FUND_ITEM), arguments: { wp_id: wp, sponsor, fund_ref: ref } }) });
      const c = await r.json().catch(() => ({}));
      if (!r.ok || !c.url) return json({ ok: false, status: "checkout_failed", message: "Qatom could not open the checkout (" + r.status + "). Nothing was charged." }, 502);
      const f = { ref, status: "pending", wp, sponsor, amount: 1, created_at: new Date().toISOString(), checkout_url: c.url, hash: c.hash || null, via: "Qatom checkout" };
      await dof("/fund/put", f);
      return json({ ok: true, ...publicFund(f), note: FUND_NOTE });
    }
    const fm = p.match(/^\/fund\/(S[A-Z0-9]{11})$/);
    if (fm && req.method === "GET") { const r = await dof("/fund/get?ref=" + fm[1]); return r.status === 200 ? json({ ok: true, ...publicFund(await r.json()) }) : json({ ok: false, status: "not_found" }, 404); }
    if (p === "/qatom/fund" || p.startsWith("/qatom/fund/")) {
      if (!same(req.headers.get("authorization") || "", "Bearer " + (env.QATOM_FULFILMENT_TOKEN || ""))) return json({ error: "not found" }, 404);
      const b = await readInput(req, url);
      const tx = req.headers.get("x-qatom-transaction-id") || "";
      if (!tx) return json({ ok: false, status: "no_transaction", summary: "No Qatom transaction id came with the call." });
      if ((await (await dof("/fund/tx?tx=" + encodeURIComponent(tx))).json()).seen) return json({ ok: true, status: "already_recorded", transaction_id: tx, summary: "This sponsorship was already recorded." });
      const t = await qatomToken(env);
      const v = t ? await fetch(API + "/v4/catalog/purchases/" + encodeURIComponent(tx), { headers: { authorization: "Bearer " + t } }) : null;
      if (!v || v.status !== 200) return json({ ok: false, status: "unverified", summary: "Qatom could not confirm this sale, so it was not recorded." });
      const ref0 = clean(b.fund_ref, 12);
      let f = /^S[A-Z0-9]{11}$/.test(ref0) ? await dof("/fund/get?ref=" + ref0).then(r => r.status === 200 ? r.json() : null) : null;
      const wp = fundWp(b.wp_id) || (f && f.wp);
      if (!wp) return json({ ok: false, status: "invalid", summary: "wp_id must be a Kijana water point (e.g. KJ-WP-0631) or DISTRICT." });
      if (!f) f = { ref: "S" + rand(11), created_at: new Date().toISOString(), amount: 1, via: "Qatom agent_checkout" }; // bought from an agent, not from the console's checkout
      Object.assign(f, { status: "paid", wp, sponsor: clean(b.sponsor, 40) || f.sponsor || "Anonymous sponsor", paid_at: new Date().toISOString(), tx });
      await dof("/fund/put", f);
      return json({ ok: true, status: "recorded", fund_ref: f.ref, wp_id: wp, transaction_id: tx, summary: `Thank you. $1 sponsorship of ${wp === "DISTRICT" ? "the Kijana district escrow" : wp} recorded (tx ${tx}). ${FUND_NOTE}` });
    }
    const secret = env.WRITE_PATH;
    if (!secret || secret.length < 16) return json({ error: "not configured" }, 503);
    const m = p.match(/^\/(in|q|reset)\/(.+)$/);
    if (!m || m[2] !== secret) return json({ error: "not found" }, 404);
    if (req.method !== "POST") return json({ error: "use POST" }, 405);
    if (m[1] === "reset") return log.fetch(new Request("https://do/reset", { method: "POST" }));
    const input = await readInput(req, url);
    const a = assess(input);
    const phone = String(input.phone || "").replace(/\D/g, "");
    const rec = {
      id: crypto.randomUUID(), at: Date.now(), accepted: a.accepted, wp_id: a.wp_id, name: a.name, status: a.status, need: a.need,
      message: String(input.message || input.text || "").slice(0, 280), reporter: String(input.reporter || "").slice(0, 80),
      phone: phone ? "…" + phone.slice(-3) : "", channel: chan(input), via: m[1] === "q" ? "Qatom item" : "Torque webhook", reply: a.reply
    };
    await log.fetch(new Request("https://do/add", { method: "POST", body: JSON.stringify(rec) }));
    return json({ ...a, report_id: rec.id, received_at: new Date(rec.at).toISOString(), note: "Synthetic hackathon scenario. A report never shows that water is safe to drink." });
  }
};
