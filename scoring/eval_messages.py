"""Evaluate the message readers on the data pack's 450 hand-labelled committee messages.

Compares, on data/kijana_community_messages_labelled_sample.csv:
  - engine v0.3 (cat_v0/resolve_v0) and v0.4 (cat/resolve) in scoring/score.py
  - the console's reader (parse/resolveText in app/app.template.html), run in node

Category accuracy is on the engine's 8 labels for the engine, and on the 4 statuses
the console acts on (OK, BROKEN, DRY, DIRTY, or no status) for the console.
Point right/wrong is over messages whose label names a water point. The rest are not
placed: the engine guesses the first point in a village with several, while the console
sends those to the officer with the candidate list instead of guessing.

  python scoring/eval_messages.py      # needs data/ and out/points.json; node for the console row
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scoring"))
import score  # noqa: E402

M = pd.read_csv(ROOT / "data" / "kijana_community_messages_labelled_sample.csv")
M["text"] = M["text"].fillna("")
has_wp = M["wp_id_resolved"].notna()

# label -> what the console should do with it
TO_APP = {"breakdown": "broken", "follow_up": "broken", "water_quality_complaint": "dirty", "flood_damage": "dirty",
          "source_dry": "dry", "early_warning_slow_flow": None, "admin_or_payment": None, "noise": None}
# engine categories use slightly different names for some labels
TO_ENGINE = {"breakdown": "breakdown", "follow_up": "follow_up", "water_quality_complaint": "quality", "flood_damage": "flood",
             "source_dry": "dry", "early_warning_slow_flow": "slow_flow", "admin_or_payment": "other", "noise": "other"}


def engine_row(name, cat, resolve):
    got_c = M["text"].map(cat)
    want_c = M["category"].map(TO_ENGINE)
    got_w = M["text"].map(lambda t: resolve(t)[0])
    match = (got_w == M["wp_id_resolved"]) & has_wp
    return {"reader": name, "category accuracy": (got_c == want_c).mean(),
            "point right": match.sum() / has_wp.sum(), "point wrong": ((got_w != M["wp_id_resolved"]) & got_w.notna() & has_wp).sum() / has_wp.sum()}


def app_row():
    if not shutil.which("node"):
        return None
    t = (ROOT / "app" / "app.template.html").read_text()
    reader = t[t.index("// Message reader"):t.index("async function send(text)")]
    resolver = t[t.index("const TYPE_WORDS"):t.index("async function importMessages(file)")]
    js = ("const PTS = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));\n"
          "const BY = Object.fromEntries(PTS.map(p => [p.id, p]));\n" + reader + resolver +
          "\nconst rows = JSON.parse(require('fs').readFileSync(0, 'utf8'));\n"
          "console.log(JSON.stringify(rows.map(x => { const r = resolveText(x); return [parse(x).kind, r.wp || null]; })));")
    tmp = ROOT / "out" / "_eval_reader.js"
    tmp.write_text(js)
    out = subprocess.run(["node", str(tmp), str(ROOT / "out" / "points.json")], input=json.dumps(M["text"].tolist()),
                         capture_output=True, text=True, check=True).stdout
    tmp.unlink(missing_ok=True)
    res = json.loads(out)
    kind = pd.Series([r[0] for r in res]); wp = pd.Series([r[1] for r in res])
    want = M["category"].map(TO_APP)
    ok = (kind.isna() & want.isna()) | (kind == want)
    match = (wp == M["wp_id_resolved"]) & has_wp
    return {"reader": "console (app)", "category accuracy": ok.mean(),
            "point right": match.sum() / has_wp.sum(), "point wrong": ((wp != M["wp_id_resolved"]) & wp.notna() & has_wp).sum() / has_wp.sum()}


rows = [engine_row("engine v0.3", score.cat_v0, score.resolve_v0), engine_row("engine v0.4", score.cat, score.resolve)]
a = app_row()
if a:
    rows.append(a)
df = pd.DataFrame(rows)
print(f"{len(M)} labelled messages, {has_wp.sum()} name a water point\n")
print(df.to_string(index=False, formatters={c: "{:.1%}".format for c in df.columns if c != "reader"}))
