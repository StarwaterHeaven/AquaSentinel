"""Turn out/water_point_scores.csv into out/points.json, the compact data the console app embeds."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
o = pd.read_csv(ROOT / "out" / "water_point_scores.csv")
reg = pd.read_csv(ROOT / "data" / "kijana_water_point_register.csv").set_index("wp_id")

def f(x, n=1):
    return None if pd.isna(x) else round(float(x), n)

def s(x):
    return None if pd.isna(x) else x

recs = []
for r in o.itertuples():
    la, lo = reg.at[r.wp_id, "lat"], reg.at[r.wp_id, "lon"]
    ok = pd.notna(la) and pd.notna(lo) and -4.2 < la < -3.0 and 32.0 < lo < 33.2  # bad register coordinates are left off the map
    recs.append(dict(
        id=r.wp_id, n=r.wp_name, sc=r.sub_county, la=round(float(la), 4) if ok else None, lo=round(float(lo), 4) if ok else None,
        ty=str(r.source_type_recorded), st=r.status_now, ss=r.status_src, sd=str(r.status_date)[:10], age=int(r.status_age_days),
        A=f(r.A_status), B=f(r.B_reliability), C=f(r.C_management), D=f(r.D_quality), E=f(r.E_source),
        bk=int(r.breakdowns), mr=f(r.med_repair_days, 0), oj=int(r.open_jobs), tm=s(r.tariff_model),
        sav=f(r.savings_balance_usd, 0), sa=s(r.service_agreement), ec=f(r.ecoli_cfu_per_100ml, 0), fl=f(r.fluoride_mg_l, 2),
        qd=None if pd.isna(r.sample_date) else str(r.sample_date)[:10], ra=f(r.rain_anom_6m, 0),
        gi=1 if r.rising_main_material == "GI" else 0, m12=int(r.msgs_12m),
        pop=None if pd.isna(r.population_2026) else int(r.population_2026), net=s(r.network_coverage),
        mech=s(r.nearest_active_mechanic_id), tw=None if pd.isna(r.travel_min_to_mechanic_wet) else int(r.travel_min_to_mechanic_wet)))
(ROOT / "out" / "points.json").write_text(json.dumps(recs, separators=(",", ":")))
print(f"wrote {len(recs)} water points to out/points.json")
