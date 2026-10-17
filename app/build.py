"""Build the single-file console: app/app.template.html + out/points.json -> out/aquasentinel-console.html
Qatom catalog item ids: sponsor 212, alert 213 (Kepler Market Services). Override with AQS_FUND_ITEM / AQS_ALERT_ITEM; "null" = simulated."""
import json
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
t = (ROOT / "app" / "app.template.html").read_text()
d = (ROOT / "out" / "points.json").read_text()
seed = (ROOT / "app" / "seed.json").read_text() if (ROOT / "app" / "seed.json").exists() else "{}"
t = t.replace("__SEED__", seed)
t = t.replace("__REPORTS_URL__", json.dumps(os.environ.get("AQS_REPORTS_URL", "https://aquasentinel-reports.hassan-khan-cd6.workers.dev")))  # Torque report store; "" = off
t = t.replace("__FUND_ITEM__", os.environ.get("AQS_FUND_ITEM", "212")).replace("__ALERT_ITEM__", os.environ.get("AQS_ALERT_ITEM", "213"))
(ROOT / "out" / "aquasentinel-console.html").write_text(t.replace("__DATA__", d))
print("built out/aquasentinel-console.html")

# Standalone site page (GitHub Pages): a full document, since no host wraps it there.
site = ROOT / "out" / "site"
site.mkdir(parents=True, exist_ok=True)
page = (ROOT / "out" / "aquasentinel-console.html").read_text()
head = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}[hidden]{display:none!important}</style>'
        '</head><body>')
(site / "index.html").write_text(head + page + "</body></html>")
(site / ".nojekyll").write_text("")
(site / "llms.txt").write_text((ROOT / "llms.txt").read_text())
print("built out/site/index.html")
