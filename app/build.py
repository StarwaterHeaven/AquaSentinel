"""Build the single-file console: app/app.template.html + out/points.json -> out/aquasentinel-console.html
Qatom catalog item ids: sponsor 212, alert 213 (Kepler Market Services). Override with AQS_FUND_ITEM / AQS_ALERT_ITEM; "null" = simulated."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
t = (ROOT / "app" / "app.template.html").read_text()
d = (ROOT / "out" / "points.json").read_text()
t = t.replace("__FUND_ITEM__", os.environ.get("AQS_FUND_ITEM", "212")).replace("__ALERT_ITEM__", os.environ.get("AQS_ALERT_ITEM", "213"))
(ROOT / "out" / "aquasentinel-console.html").write_text(t.replace("__DATA__", d))
print("built out/aquasentinel-console.html")
