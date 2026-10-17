"""Build the single-file console: app/app.template.html + out/points.json -> out/aquasentinel-console.html
Qatom catalog item ids come from the environment (AQS_FUND_ITEM, AQS_ALERT_ITEM); unset = simulated."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
t = (ROOT / "app" / "app.template.html").read_text()
d = (ROOT / "out" / "points.json").read_text()
t = t.replace("__FUND_ITEM__", os.environ.get("AQS_FUND_ITEM", "null")).replace("__ALERT_ITEM__", os.environ.get("AQS_ALERT_ITEM", "null"))
(ROOT / "out" / "aquasentinel-console.html").write_text(t.replace("__DATA__", d))
print("built out/aquasentinel-console.html")
