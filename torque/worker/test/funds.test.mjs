// Offline test of the report store's sponsorship routes with a mocked Durable Object and Qatom API.
import assert from "node:assert/strict";
const mod = await import("../src/index.mjs");
const W = mod.default, ReportLog = mod.ReportLog;
const mem = new Map(); const ctx = { storage: { get: async k => mem.get(k), put: async (k, v) => mem.set(k, structuredClone(v)) } };
const dobj = new ReportLog(ctx);
const env = { LOG: { idFromName: () => 1, get: () => ({ fetch: r => dobj.fetch(r) }) }, WRITE_PATH: "x".repeat(32), FUND_ITEM: "212", QATOM_CLIENT_ID: "id", QATOM_CLIENT_SECRET: "sec", QATOM_FULFILMENT_TOKEN: "tok123" };
let checkoutBody = null, verified = new Set(["tx-real-1", "tx-agent-2"]);
globalThis.fetch = async (u, o = {}) => {
  u = String(u);
  if (u.endsWith("/v4/account/oauth/token")) return new Response(JSON.stringify({ access_token: "AT", expires_at: Date.now() / 1000 + 3600 }));
  if (u.endsWith("/v4/payment/checkout")) { checkoutBody = JSON.parse(o.body); return new Response(JSON.stringify({ url: "https://checkout.m.todaq.net/x", hash: "h1" })); }
  const m = u.match(/purchases\/(.+)$/); if (m) return new Response("{}", { status: verified.has(decodeURIComponent(m[1])) ? 200 : 404 });
  throw new Error("unexpected fetch " + u);
};
const call = async (path, method = "GET", body, headers = {}) => { const r = await W.fetch(new Request("https://w" + path, { method, headers: { "content-type": "application/json", ...headers }, body: body ? JSON.stringify(body) : undefined }), env); return { s: r.status, j: await r.json() }; };
let n = 0; const ok = m => console.log("ok", ++n, m);
let r = await call("/fund/start", "POST", { wp_id: "0631", sponsor: "Ruth <b>" }); assert.equal(r.j.ok, true); assert.equal(r.j.status, "pending"); assert.equal(checkoutBody.catalog_item_id, 212); assert.equal(checkoutBody.arguments.wp_id, "KJ-WP-0631"); assert.ok(!/<|>/.test(checkoutBody.arguments.sponsor)); ok("start opens a real checkout for item 212 with wp and a clean sponsor");
const ref = r.j.ref;
r = await call("/fund/start", "POST", { wp_id: "9999" }); assert.equal(r.s, 400); ok("unknown water point refused");
r = await call("/funds"); assert.equal(r.j.funds.length, 0); ok("pending is not listed as paid");
r = await call("/qatom/fund", "POST", { arguments: { wp_id: "KJ-WP-0631", sponsor: "Ruth", fund_ref: ref } }, { "x-qatom-transaction-id": "tx-real-1" }); assert.equal(r.s, 404); ok("dispatch without the item header is refused");
r = await call("/qatom/fund", "POST", { wp_id: "KJ-WP-0631", fund_ref: ref }, { authorization: "Bearer tok123", "x-qatom-transaction-id": "tx-fake" }); assert.equal(r.j.status, "unverified"); ok("a sale Qatom can't confirm is not recorded");
r = await call("/qatom/fund", "POST", { arguments: { wp_id: "KJ-WP-0631", sponsor: "Ruth", fund_ref: ref } }, { authorization: "Bearer tok123", "x-qatom-transaction-id": "tx-real-1" }); assert.equal(r.j.status, "recorded"); assert.equal(r.j.fund_ref, ref); ok("verified checkout sale recorded against its ref");
r = await call("/qatom/fund", "POST", { wp_id: "KJ-WP-0631", fund_ref: ref }, { authorization: "Bearer tok123", "x-qatom-transaction-id": "tx-real-1" }); assert.equal(r.j.status, "already_recorded"); ok("same transaction recorded once");
r = await call("/qatom/fund/1", "POST", { wp_id: "district", sponsor: "Hassan" }, { authorization: "Bearer tok123", "x-qatom-transaction-id": "tx-agent-2" }); assert.equal(r.j.status, "recorded"); assert.equal(r.j.wp_id, "DISTRICT"); ok("agent_checkout purchase (no ref, /qatom/fund/1 path) recorded");
r = await call("/fund/" + ref); assert.equal(r.j.status, "paid"); assert.equal(r.j.transaction_id, "tx-real-1"); ok("status shows paid with tx");
r = await call("/funds"); assert.equal(r.j.funds.length, 2); assert.match(r.j.note, /WaterAid Canada/); ok("public feed lists both, with the WaterAid note");
await call("/reset/" + env.WRITE_PATH, "POST"); r = await call("/funds"); assert.equal(r.j.funds.length, 2); ok("report reset never clears real sponsorships");
delete env.QATOM_CLIENT_ID; r = await call("/fund/start", "POST", { wp_id: "0631" }); assert.equal(r.s, 503); ok("no credentials: refuses, no simulated fallback");
console.log(n + " checks passed");
