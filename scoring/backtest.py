#!/usr/bin/env python3
"""scoring/backtest.py — does the score predict what the field later finds?

Scores every water point as of the cutoff (default 2024-01-01) using only
records dated before the cutoff: register status, inspections, job cards,
committee SMS, water tests, rainfall. The committee table is excluded (its
figures are 2025-era). The Aug-2025 verification survey and the 2024
inspection round are then used purely as ground truth — they never feed the
score (the cutoff filter in compute() guarantees it; verifier checks it).

Reports, against both ground truths:
  - of the points we flagged (Not working or Critical): share found
    non-functional (precision)
  - of the points found non-functional: share we had flagged (recall)
  - the same two numbers for points we called Silent (confidence Low)

Prints a short table and writes out/backtest.md.
Run:  python scoring/backtest.py [--cutoff 2024-01-01]
"""
import argparse
from pathlib import Path

import pandas as pd

import score  # scoring/score.py — same engine, same math

CUTOFF = "2024-01-01"


def truth_tables(pack):
    """Ground-truth frames: (name, frame with wp_id + bool non_functional)."""
    sv = pack["sv"].copy()
    sv["nf"] = sv["status_observed"] == "Non-functional"
    ins24 = pack["ins"][pack["ins"].visit_date.dt.year == 2024].copy()
    ins24["nf"] = ins24["status_observed"] == "Non-functional"
    return [("Aug-2025 verification survey", sv[["wp_id", "nf"]]),
            ("2024 inspection round", ins24[["wp_id", "nf"]])]


def evaluate(out, truth):
    m = out.reset_index().merge(truth, on="wp_id", how="inner")
    flagged = (m["flag"] == "Not working") | (m["band"] == "Critical")
    silent = m["confidence"] == "Low"

    def stats(mask):
        n_flag = int(mask.sum())
        n_nf = int(m["nf"].sum())
        prec = float(m.loc[mask, "nf"].mean()) if n_flag else float("nan")
        rec = float(m.loc[mask, "nf"].sum() / n_nf) if n_nf else float("nan")
        return n_flag, n_nf, prec, rec

    return {
        "n_compared": int(len(m)),
        "n_non_functional": int(m["nf"].sum()),
        "flagged": stats(flagged),
        "silent": stats(silent),
    }


def fmt(res, label):
    lines = [f"### vs {label} ({res['n_compared']} points observed, "
             f"{res['n_non_functional']} non-functional)",
             "",
             "| signal | points | share found non-functional | share of non-functional caught |",
             "|---|---|---|---|"]
    for name, key in (("Flagged Not working / Critical", "flagged"),
                      ("Silent (no fresh evidence)", "silent")):
        n_flag, n_nf, prec, rec = res[key]
        lines.append(f"| {name} | {n_flag} | {prec:.0%} | {rec:.0%} |")
    base = res["n_non_functional"] / res["n_compared"]
    lines.append(f"| — base rate (all points) | {res['n_compared']} | {base:.0%} | — |")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff", default=CUTOFF)
    args = ap.parse_args()
    cutoff = pd.Timestamp(args.cutoff)

    pack = score.load_pack()
    pp = score.prepare(pack)
    out = score.compute(pp, pack, T=cutoff, cutoff=cutoff, use_committees=False)

    truths = truth_tables(pack)
    results = [(label, evaluate(out, t)) for label, t in truths]

    head = (f"# Backtest — score as of {cutoff.date()} vs what the field later found\n\n"
            "Every record used is dated before the cutoff (register, inspections,\n"
            "job cards, committee SMS, water tests, rainfall). Committee finances are\n"
            "excluded — they did not exist yet. Ground truth comes from observations\n"
            "after the cutoff only.\n")
    body = []
    for label, res in results:
        body += fmt(res, label) + [""]
    take = (
        "## Reading\n\n"
        "- Precision answers the officer's question: *if I spend a crew day on the\n"
        "  flagged list, how often is the pump really down?*\n"
        "- Recall answers the funder's question: *of the pumps that failed, how many\n"
        "  were already on our list?*\n"
        "- Silent points are the fairness net: no fresh evidence, so they go on the\n"
        "  inspection list instead of being mistaken for healthy.\n"
        "- Ground truth is observational: a pump repaired between cutoff and survey\n"
        "  counts as a false positive even though the flag was right at the time.\n"
        "  That makes these numbers a lower bound on usefulness.\n")
    text = head + "\n" + "\n".join(body) + "\n" + take
    Path(score.OUT).mkdir(exist_ok=True)
    (score.OUT / "backtest.md").write_text(text)
    # the full as-of-cutoff ranking, so anyone can recompute these numbers
    cols = ["wp_name", "sub_county", "score", "band", "flag", "confidence",
            "status_now", "status_src", "status_date", "A_status", "B_reliability",
            "D_quality", "E_source", "breakdowns", "open_jobs"]
    out.reset_index()[["wp_id"] + cols].to_csv(score.OUT / "backtest_scores.csv", index=False)

    print(f"Backtest cutoff {cutoff.date()}")
    for label, res in results:
        nf, prec = res["flagged"][2], res["flagged"][2]
        print(f"\n  {label}: compared {res['n_compared']}, non-functional {res['n_non_functional']}")
        print(f"    Flagged {res['flagged'][0]:>3} pts -> precision {res['flagged'][2]:.0%}, "
              f"recall {res['flagged'][3]:.0%}")
        print(f"    Silent  {res['silent'][0]:>3} pts -> precision {res['silent'][2]:.0%}, "
              f"recall {res['silent'][3]:.0%}")
    print("\nwrote out/backtest.md")


if __name__ == "__main__":
    main()
