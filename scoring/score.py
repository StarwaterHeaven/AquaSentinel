"""AquaSentinel water-point score (v0.4). Five dimensions x 20 points; any point not working is flagged and listed first.

Run: python scoring/score.py   (needs the Kijana data pack CSVs in data/)

v0.3 -> v0.4 (validation branch; scoring math unchanged):
- Module refactored into load_pack()/prepare()/compute() so scoring/backtest.py
  can score every point as of any cutoff date using the same code path.
- cat() and resolve() improved (same names, same arguments, same return values):
  resolve() now also accepts the bare 4-digit SMS code ('0631 BROKEN'), matches
  misspelt settlement names (difflib), and uses a technology hint to pick the
  right point when a settlement has several. cat() uses a wider, weighted
  Swahili/English keyword table instead of a first-match cascade.
- Originals kept as cat_v0()/resolve_v0() so scoring/eval_messages.py can
  measure the improvement.
"""
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "out"
T_NOW = pd.Timestamp("2026-09-30")

PACK_FILES = {
    "reg": "kijana_water_point_register.csv",
    "jc": "kijana_repair_job_cards.csv",
    "ins": "kijana_inspection_visits.csv",
    "sv": "kijana_verification_survey_2025.csv",
    "wc": "kijana_water_committees.csv",
    "wq": "kijana_water_quality_results.csv",
    "st": "kijana_settlements.csv",
    "msg": "kijana_community_messages.csv",
    "rain": "kijana_rainfall_by_subcounty_monthly.csv",
}


def load_pack(data_dir=DATA):
    """Read the nine data-pack CSVs (schemas per data/README.md)."""
    d = Path(data_dir)
    return {
        "reg": pd.read_csv(d / PACK_FILES["reg"]),
        "jc": pd.read_csv(d / PACK_FILES["jc"],
                          parse_dates=["date_reported", "date_repaired", "breakdown_date_est"]),
        "ins": pd.read_csv(d / PACK_FILES["ins"], parse_dates=["visit_date"]),
        "sv": pd.read_csv(d / PACK_FILES["sv"], parse_dates=["visit_date"]),
        "wc": pd.read_csv(d / PACK_FILES["wc"], parse_dates=["last_meeting"]),
        "wq": pd.read_csv(d / PACK_FILES["wq"], parse_dates=["sample_date"]),
        "st": pd.read_csv(d / PACK_FILES["st"]),
        "msg": pd.read_csv(d / PACK_FILES["msg"], parse_dates=["received_at"]),
        "rain": pd.read_csv(d / PACK_FILES["rain"]),
    }


def norm_wp(x):
    m = re.search(r"(\d{1,4})", str(x))
    return f"KJ-WP-{int(m.group(1)):04d}" if m else None


# ---------------------------------------------------------------------------
# Message reader. v0 = as shipped in v0.3; improved versions keep the same
# names/signatures:  cat(text) -> category str,  resolve(text) -> (wp_id, how)
# ---------------------------------------------------------------------------
def cat_v0(t):
    t = t.lower()
    if re.search(r"chafu|dirty|smell|harufu|kutu|rangi|colou?r|taste|ladha|tumbo|diarr|kuhara", t): return "quality"
    if re.search(r"kidogo|slow|many strokes|long to|takes long|polepole", t): return "slow_flow"
    if re.search(r"\bdry\b|imekauka|kavu", t): return "dry"
    if re.search(r"fixed|imetengenezwa|inafanya kazi|working now|repaired|imerekebishwa", t): return "fixed"
    if re.search(r"still waiting|bado|when will|reported \d+ weeks", t): return "follow_up"
    if re.search(r"not working|broke|imeharibika|imekufa|mbovu|hakuna maji|no water|haitoi|spoilt|loose|imevunjika", t): return "breakdown"
    if re.search(r"flood|mafuriko", t): return "flood"
    return "other"


# weighted stems: specific phrases outweigh generic ones; ties break toward the
# category that drives action (quality > breakdown > dry > flood > slow_flow
# > follow_up > fixed > other)
KW = {
    "quality": [("chafu", 2), ("dirty", 2), ("smell", 2), ("harufu", 2), ("kutu", 2),
                ("rangi", 2), ("colour", 2), ("color", 2), ("taste", 1), ("ladha", 2),
                ("tumbo", 2), ("diarr", 2), ("kuhara", 2), ("turbid", 2), ("muddy", 2),
                ("brown", 1), ("green", 1)],
    "breakdown": [("not working", 3), ("broke", 2), ("imeharibika", 3), ("imekufa", 3),
                  ("mbovu", 2), ("hakuna maji", 2), ("haitoi", 3), ("spoilt", 2),
                  ("imevunjika", 3), ("imekataa", 3), ("yapasuka", 2), ("limepasuka", 2),
                  ("haijawasha", 2), ("yamemwagika", 2), ("fundi", 1), ("bila maji", 1),
                  ("no water", 1)],
    "dry": [("imekauka", 3), ("kimekauka", 3), ("kavu", 3), ("source dry", 3),
            ("well dry", 3), ("water table", 2), ("no water at all", 2), ("dry", 2)],
    "flood": [("mafuriko", 3), ("flood", 3), ("submerged", 2), ("mvua kubwa", 2),
              ("washed away", 2), ("heavy rain", 2), ("intake damaged", 2),
              ("imeharibu", 2)],
    "slow_flow": [("kidogo", 2), ("slow", 1), ("many strokes", 2), ("long to", 2),
                  ("takes long", 2), ("polepole", 2), ("inatonea", 3), ("drip", 1),
                  ("pressure low", 2), ("fills slowly", 2)],
    "follow_up": [("still waiting", 3), ("bado", 2), ("when will", 2),
                  ("reported", 1), ("weeks ago", 2), ("hajafika", 2), ("haijafanyiwa", 3)],
    "fixed": [("fixed", 3), ("imetengenezwa", 3), ("inafanya kazi", 3), ("working now", 3),
              ("repaired", 3), ("imerekebishwa", 3), ("sawa", 1), ("back to normal", 3)],
}
_PRIORITY = ["quality", "breakdown", "dry", "flood", "slow_flow", "follow_up", "fixed"]


def cat(t):
    t = t.lower()
    scores = {c: sum(w for kw, w in kws if kw in t) for c, kws in KW.items()}
    best = max(_PRIORITY, key=lambda c: scores[c])
    return best if scores[best] > 0 else "other"


class _Gazetteer:
    """Settlement-name -> water-point(s) lookup, with aliases + fuzzy match."""

    def __init__(self, reg, st):
        reg_set = reg.merge(st[["settlement_id", "name"]], on="settlement_id", how="left")
        self.name2wp = reg_set.groupby(reg_set.name.str.lower())["wp_id"].apply(list).to_dict()
        self.wp2tech = reg.set_index("wp_id")["technology_recorded"].to_dict()
        self.wp2src = reg.set_index("wp_id")["source_type_recorded"].to_dict()
        self.ids = set(reg.wp_id)
        self.names = sorted([n for n in self.name2wp if isinstance(n, str) and len(n) > 3],
                            key=len, reverse=True)
        self.pat = re.compile(r"\b(" + "|".join(map(re.escape, self.names)) + r")\b")

    TECH_HINT = {"hand pump": "Hand pump", "handle": "Hand pump",
                 "motor": "Motorised pump", "solar": "Solar pump",
                 "tank": "Rainwater tank", "spring": "Spring protection",
                 "kiosk": "Kiosk tap", "tap": "Kiosk tap"}

    def _pick(self, wps, t, how):
        if len(wps) == 1:
            return wps[0], "village"
        for hint, tech in self.TECH_HINT.items():
            if re.search(r"\b" + hint + r"\b", t):
                cand = [w for w in wps if self.wp2tech.get(w) == tech]
                if len(cand) == 1:
                    return cand[0], "village-type"
        return wps[0], "village-ambiguous"

    def resolve_v0(self, t):
        t = str(t)
        m = re.search(r"KJ-WP-\d{4}", t)
        if m:
            return m.group(0), "id"
        m = self.pat.search(t.lower())
        if m:
            l = self.name2wp[m.group(1)]
            return l[0], ("village" if len(l) == 1 else "village-ambiguous")
        return None, None

    def resolve(self, t):
        t = str(t)
        m = re.search(r"KJ-WP-\d{4}", t)
        if m:
            return m.group(0), "id"
        tl = t.lower()
        m = re.search(r"\b(\d{4})\b", tl)  # bare SMS code always wins next
        if m and f"KJ-WP-{m.group(1)}" in self.ids:
            return f"KJ-WP-{m.group(1)}", "code"
        m = self.pat.search(tl)
        if m:
            return self._pick(self.name2wp[m.group(1)], tl, "village")
        # fuzzy: settlement names tolerate misspellings; compare token unigrams
        # and bigrams ('Kyulo ew' -> 'Kyulo West', not plain 'Kyulo')
        best, best_name = 0.0, None
        toks = tl.split()
        grams = toks + [f"{toks[i]} {toks[i + 1]}" for i in range(len(toks) - 1)]
        for gram in grams:
            if len(gram) < 5:
                continue
            for name in self.names:
                s = SequenceMatcher(None, gram, name).ratio()
                if s > best:
                    best, best_name = s, name
        if best_name is not None and best >= 0.80:
            wps = self.name2wp[best_name]
            picked, how = self._pick(wps, tl, "village")
            return picked, "village-fuzzy" if how == "village" else "village-ambiguous-fuzzy"
        return None, None


_GAZ = None


def gazetteer():
    """Lazy default gazetteer so cat()/resolve() keep their v0.3 signatures."""
    global _GAZ
    if _GAZ is None:
        pack = load_pack()
        _GAZ = _Gazetteer(pack["reg"], pack["st"])
    return _GAZ


def resolve_v0(t):
    return gazetteer().resolve_v0(t)


def resolve(t):
    return gazetteer().resolve(t)


# ---------------------------------------------------------------------------
# Prepare: normalise references, read messages, build the status-event stream
# ---------------------------------------------------------------------------
def prepare(pack, reader=(cat, resolve)):
    reg, jc, wq, st, msg = pack["reg"].copy(), pack["jc"].copy(), pack["wq"].copy(), \
        pack["st"], pack["msg"].copy()
    ids = set(reg.wp_id)
    jc["wp"] = jc.wp_id.where(jc.wp_id.isin(ids), jc.wp_id.map(norm_wp))
    wq["wp"] = wq.water_point_ref.map(norm_wp)
    cat_fn, res_fn = reader
    msg[["wp", "res"]] = msg.text.apply(lambda t: pd.Series(res_fn(t)))
    msg["cat"] = msg.text.apply(cat_fn)

    ev = []
    for r in reg.itertuples():
        ev.append((r.wp_id, pd.Timestamp(r.status_date), r.status_recorded, "register"))
    for r in pack["ins"].itertuples():
        ev.append((r.wp_id, r.visit_date, r.status_observed, "inspection"))
    for r in pack["sv"].itertuples():
        ev.append((r.wp_id, r.visit_date, r.status_observed, "survey"))
    b = jc[jc.repair_type != "preventive service"]
    for r in b.itertuples():
        if r.wp in ids:
            ev.append((r.wp, r.date_reported, "Non-functional", "job opened"))
            if pd.notna(r.date_repaired):
                ev.append((r.wp, r.date_repaired, "Functional", "job closed"))
    for r in msg[msg.wp.notna()].itertuples():
        if r.cat in ("breakdown", "follow_up"):
            ev.append((r.wp, r.received_at, "Non-functional", "committee SMS"))
        if r.cat == "fixed":
            ev.append((r.wp, r.received_at, "Functional", "committee SMS"))
        if r.cat == "dry":
            ev.append((r.wp, r.received_at, "Seasonal (dry)", "committee SMS"))
    E = pd.DataFrame(ev, columns=["wp", "date", "status", "src"]).dropna(subset=["date"]) \
        .sort_values("date")
    return {"reg": reg, "jc": jc, "b": b, "wq": wq, "st": st, "msg": msg, "E": E}


# ---------------------------------------------------------------------------
# Compute scores as of T, optionally using only records dated before `cutoff`.
# use_committees=False drops the committee table (its figures are 2025-era and
# would leak the future into a backtest).
# ---------------------------------------------------------------------------
def compute(pp, pack, T=T_NOW, cutoff=None, use_committees=True):
    reg, jc, b, wq, st, msg, E = (pp["reg"], pp["jc"], pp["b"], pp["wq"],
                                  pp["st"], pp["msg"], pp["E"])
    if cutoff is not None:
        cutoff = pd.Timestamp(cutoff)
        E = E[E.date < cutoff]
        b = b[b.date_reported < cutoff]
        wq = wq[wq.sample_date < cutoff]
        msg = msg[msg.received_at < cutoff]
    last = E.groupby("wp").tail(1).set_index("wp")

    out = reg[["wp_id", "wp_name", "sub_county", "settlement_id", "source_type_recorded",
               "technology_recorded", "design_population", "rising_main_material",
               "install_year", "committee_id"]].copy().set_index("wp_id")
    out["status_now"] = last.status
    out["status_date"] = last.date
    out["status_src"] = last.src
    out["status_age_days"] = (T - out.status_date).dt.days

    # A. Service status (35 -> 20)
    def A(r):
        s, a = r.status_now, r.status_age_days
        if s == "Functional":
            base = 35
        elif s == "Seasonal (dry)":
            base = 15
        else:
            base = 0
        if s == "Functional" and a > 365:
            base = 25
        if s == "Functional" and a > 730:
            base = 18
        return base
    out["A_status"] = out.apply(A, axis=1)

    # B. Reliability (20): breakdowns/yr since 2021 and median repair days;
    #    at a cutoff, jobs still open then count as open
    ids = set(reg.wp_id)
    bb = b[b.wp.isin(ids)].copy()
    if cutoff is not None:
        open_mask = bb.date_repaired.isna() | (bb.date_repaired >= cutoff)
        bb_done = bb[~open_mask]
    else:
        open_mask = bb.date_repaired.isna()
        bb_done = bb[~open_mask]
    bb_done = bb_done.copy()
    bb_done["days"] = (bb_done.date_repaired - bb_done.date_reported).dt.days
    g = bb.groupby("wp").agg(breakdowns=("job_id", "count")).join(
        bb_done.groupby("wp")["days"].median().rename("med_repair_days"),
        how="left").join(
        bb[open_mask].groupby("wp").size().rename("open_jobs"), how="left")
    out = out.join(g)
    out[["breakdowns", "open_jobs"]] = out[["breakdowns", "open_jobs"]].fillna(0)
    yrs = max((T - pd.Timestamp("2021-01-01")).days / 365.25, 0.5)
    out["B_reliability"] = (12 - np.clip(out.breakdowns / yrs * 4, 0, 12)) + \
        (8 - np.clip(out.med_repair_days.fillna(30) / 15, 0, 8))

    # C. Management & money (15 -> 20)
    if use_committees:
        w = pack["wc"].set_index("wp_id")
        out = out.join(w[["tariff_model", "avg_monthly_collection_usd_2025",
                          "savings_balance_usd", "last_meeting", "service_agreement"]])
        tm = {"Monthly flat fee": 5, "Pay per container": 5, "Collect when broken": 2,
              "No tariff": 0}

        def C(r):
            if pd.isna(r.tariff_model):
                return 10  # piped/solar: operator-run, neutral
            s = tm.get(r.tariff_model, 0)
            s += 3 if (r.savings_balance_usd or 0) >= 50 else (1 if (r.savings_balance_usd or 0) > 0 else 0)
            s += 3 if pd.notna(r.last_meeting) and (T - r.last_meeting).days <= 180 else 0
            s += 4 if r.service_agreement == "yes" else 0
            return s
        out["C_management"] = out.apply(C, axis=1)
    else:
        out["C_management"] = 7.5  # neutral mid-point; committee table excluded

    # D. Water quality (15 -> 20): latest result before cutoff
    q = wq[wq.wp.isin(ids)].sort_values("sample_date").groupby("wp").tail(1).set_index("wp")
    out = out.join(q[["sample_date", "ecoli_cfu_per_100ml", "fluoride_mg_l", "nitrate_mg_l"]])
    qc = msg[msg.cat == "quality"].groupby("wp").received_at.max()
    out["last_quality_complaint"] = qc

    def Dq(r):
        if pd.isna(r.sample_date):
            s = 8
        else:
            s = 15
            if (r.ecoli_cfu_per_100ml or 0) > 0:
                s -= 10
            if (r.fluoride_mg_l or 0) > 1.5:
                s -= 5
            if (r.nitrate_mg_l or 0) > 50:
                s -= 5
            if (T - r.sample_date).days > 730:
                s = min(s, 10)
        if pd.notna(r.last_quality_complaint) and (T - r.last_quality_complaint).days <= 365:
            s = min(s, 5)
        return max(s, 0)
    out["D_quality"] = out.apply(Dq, axis=1)

    # E. Source & climate (15 -> 20): sub-county rainfall anomaly, last 6
    #    months before T; shallow wells more exposed; recent dry reports
    rain = pack["rain"]
    if cutoff is not None:
        rain = rain[rain.month < cutoff.strftime("%Y-%m")]
    win_start = (T - pd.DateOffset(months=6)).strftime("%Y-%m")
    r6 = rain[rain.month >= win_start].groupby("sub_county").anomaly_pct_vs_2014_2020.mean()
    out["rain_anom_6m"] = out.sub_county.map(r6).fillna(0.0)
    shallow = out.source_type_recorded.str.contains("shallow|hand|hdw", case=False, na=False)
    dry = msg[msg.cat == "dry"].groupby("wp").received_at.max()
    out["last_dry_report"] = dry

    def Ec(r, sh):
        s = 15 + min(0, r.rain_anom_6m) / (4 if sh else 8)
        if pd.notna(r.last_dry_report) and (T - r.last_dry_report).days <= 365:
            s -= 6
        return float(np.clip(s, 0, 15))
    out["E_source"] = [Ec(r, sh) for r, sh in zip(out.itertuples(), shallow)]

    # scale each dimension to 20
    out["A_status"] = out.A_status * 20 / 35
    out["C_management"] = out.C_management * 20 / 15
    out["D_quality"] = out.D_quality * 20 / 15
    out["E_source"] = out.E_source * 20 / 15
    for c in ["A_status", "B_reliability", "C_management", "D_quality", "E_source"]:
        out[c] = out[c].round(1)
    out["score"] = (out.A_status + out.B_reliability + out.C_management
                    + out.D_quality + out.E_source).round().astype(int)

    # confidence (separate from score): how fresh/varied the evidence is
    recent_msg = msg[(msg.received_at >= T - pd.Timedelta(days=365))].groupby("wp").size()
    out["msgs_12m"] = recent_msg
    out["msgs_12m"] = out.msgs_12m.fillna(0)
    out = out.join(st.set_index("settlement_id")[["network_coverage", "population_2026",
                                                  "nearest_active_mechanic_id",
                                                  "travel_min_to_mechanic_wet"]],
                   on="settlement_id")

    def conf(r):
        if r.status_age_days <= 180:
            return "High"
        if r.status_age_days <= 540 or r.msgs_12m > 0:
            return "Medium"
        return "Low"
    out["confidence"] = out.apply(conf, axis=1)

    def acts(r):
        a = []
        if r.status_now != "Functional" and r.open_jobs == 0:
            a.append(f"Dispatch mechanic {r.nearest_active_mechanic_id} "
                     f"(~{int(r.travel_min_to_mechanic_wet) if pd.notna(r.travel_min_to_mechanic_wet) else '?'} min wet season)")
        if r.open_jobs > 0:
            a.append("Chase open job card")
        if r.D_quality <= 6.7:
            a.append("Boil-water advice + retest E. coli")
        if r.confidence == "Low":
            a.append("Inspect: no fresh evidence (silent point)")
        if r.C_management <= 5.3 and pd.notna(r.get("tariff_model", None)):
            a.append("Committee support: tariff/savings")
        if r.E_source <= 10.7:
            a.append("Seasonal-dry watch")
        if r.rising_main_material == "GI" and r.breakdowns >= 4:
            a.append("Plan preventive rising-main swap")
        return "; ".join(a) or "No action"
    out["actions"] = out.apply(acts, axis=1)

    out["band"] = pd.cut(out.score, [-1, 39, 59, 79, 100],
                         labels=["Critical", "At risk", "Watch", "Good"]).astype(str)
    # any point not working is flagged and goes to the top of the list
    out["flag"] = np.where(out.status_now != "Functional", "Not working", "")
    out["priority"] = np.where(out.flag == "Not working", 0, 1)
    return out.sort_values(["priority", "score"])


def main():
    OUT.mkdir(exist_ok=True)
    pack = load_pack()
    pp = prepare(pack)
    out = compute(pp, pack, T=T_NOW)
    out.to_csv(OUT / "water_point_scores.csv")
    print(out.band.value_counts().sort_index())
    print(out.confidence.value_counts())
    print(out.status_src.value_counts())
    print("msgs resolved", pp["msg"].res.value_counts(dropna=False).to_dict(),
          pp["msg"].cat.value_counts().to_dict())
    print(out.score.describe())
    print(out.sort_values("score")[["wp_name", "sub_county", "score", "status_now",
                                    "status_src", "confidence", "actions"]].head(8).to_string())
    print(out[["A_status", "B_reliability", "C_management", "D_quality", "E_source"]]
          .mean().round(1))


if __name__ == "__main__":
    sys.exit(main())
