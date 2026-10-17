"""Export the data pack's own (synthetic) map layers for the console: out/map.json.

Sub-county borders, roads, rivers, the May 2024 flood extent, Kijana Town and the
health facilities. All from the organisers' fictional Kijana geography; no real maps.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"


def rnd(c):
    return [round(c[0], 4), round(c[1], 4)]


def lines(geom):
    t, c = geom["type"], geom["coordinates"]
    if t == "LineString":
        return [[rnd(p) for p in c]]
    if t == "MultiLineString":
        return [[rnd(p) for p in l] for l in c]
    if t == "Polygon":
        return [[rnd(p) for p in c[0]]]
    if t == "MultiPolygon":
        return [[rnd(p) for p in poly[0]] for poly in c]
    return []


def layer(name):
    return json.loads((D / name).read_text())["features"]


out = {
    "subcounties": [{"name": f["properties"]["sub_county"], "rings": lines(f["geometry"])} for f in layer("kijana_subcounties.geojson")],
    "roads": [{"name": f["properties"].get("name", ""), "cls": f["properties"].get("class", ""),
               "wet": f["properties"].get("wet_season_passable", ""), "lines": lines(f["geometry"])} for f in layer("kijana_roads.geojson")],
    "rivers": [{"name": f["properties"].get("name", ""), "lines": lines(f["geometry"])} for f in layer("kijana_rivers.geojson")],
    "flood": [r for f in layer("kijana_flood_extent_2024_05.geojson") if f["properties"].get("flooded", True) for r in lines(f["geometry"])],
}
st = pd.read_csv(D / "kijana_settlements.csv")
town = st[st.settlement_type.str.startswith("town")]
out["towns"] = [{"name": r["name"], "lo": round(r.lon, 4), "la": round(r.lat, 4)} for _, r in town.iterrows()]
hf = pd.read_csv(D / "kijana_health_facilities.csv")
out["health"] = [{"name": r.facility_name, "lo": round(r.lon, 4), "la": round(r.lat, 4)} for _, r in hf.iterrows() if pd.notna(r.lat)]

(ROOT / "out" / "map.json").write_text(json.dumps(out, separators=(",", ":")))
print(f"out/map.json: {len(out['subcounties'])} sub-counties, {len(out['roads'])} roads, {len(out['rivers'])} rivers, "
      f"{len(out['flood'])} flood polygons, {len(out['towns'])} towns, {len(out['health'])} health facilities")
