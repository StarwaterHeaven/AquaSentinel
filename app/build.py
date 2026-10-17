"""Build the single-file console: app/app.template.html + out/points.json -> out/aquasentinel-console.html"""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
t = (ROOT / "app" / "app.template.html").read_text()
d = (ROOT / "out" / "points.json").read_text()
(ROOT / "out" / "aquasentinel-console.html").write_text(t.replace("__DATA__", d))
print("built out/aquasentinel-console.html")
