#!/usr/bin/env python3
"""Sales incentive calculator (target vs achieved, slab-based).

Usage:
  python3 tools/incentives.py data/live/targets.csv data/live/incentive_slabs.csv [--month 10/2026]

targets.csv:   salesperson,month,target_amount,achieved_amount
slabs.csv:     min_achievement_pct,max_achievement_pct,incentive_pct_of_sales,fixed_bonus
               (blank max = no upper limit; a slab covers min <= achievement < max)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tgw_common import inr, md_table, money, read_csv, require_columns  # noqa: E402


def load_slabs(rows):
    slabs = []
    for r in rows:
        lo = money(r.get("min_achievement_pct"))
        hi_raw = r.get("max_achievement_pct", "")
        hi = float("inf") if hi_raw.strip() == "" else money(hi_raw)
        slabs.append((lo, hi, money(r.get("incentive_pct_of_sales")), money(r.get("fixed_bonus"))))
    slabs.sort()
    return slabs


def find_slab(slabs, pct):
    for lo, hi, rate, bonus in slabs:
        if lo <= pct < hi:
            return lo, hi, rate, bonus
    return None


def calculate(targets, slabs):
    results = []
    for t in targets:
        target = money(t.get("target_amount"))
        achieved = money(t.get("achieved_amount"))
        pct = (achieved / target * 100) if target else 0.0
        slab = find_slab(slabs, pct)
        if slab:
            lo, hi, rate, bonus = slab
            incentive = round(achieved * rate / 100 + bonus)
            slab_txt = f"{lo:g}–{'' if hi == float('inf') else f'{hi:g}'}% → {rate:g}%" + (f" + {inr(bonus)}" if bonus else "")
        else:
            incentive, slab_txt = 0, "no slab"
        results.append({
            "salesperson": t.get("salesperson", ""), "month": t.get("month", ""),
            "target": target, "achieved": achieved, "pct": pct, "slab": slab_txt, "incentive": incentive,
        })
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets")
    ap.add_argument("slabs")
    ap.add_argument("--month", help="Only rows for this month value")
    a = ap.parse_args(argv)
    targets = read_csv(a.targets)
    require_columns(targets, ["salesperson", "target_amount", "achieved_amount"], a.targets)
    if a.month:
        targets = [t for t in targets if t.get("month") == a.month]
    slabs_rows = read_csv(a.slabs)
    require_columns(slabs_rows, ["min_achievement_pct", "max_achievement_pct", "incentive_pct_of_sales"], a.slabs)
    res = calculate(targets, load_slabs(slabs_rows))
    print("# Sales incentives" + (f": {a.month}" if a.month else ""))
    print(md_table(["Salesperson", "Month", "Target", "Achieved", "Achievement", "Slab", "Incentive"],
                   [[r["salesperson"], r["month"], inr(r["target"]), inr(r["achieved"]), f"{r['pct']:.1f}%", r["slab"], inr(r["incentive"])] for r in res]))
    print(f"\n**Total incentive payable: {inr(sum(r['incentive'] for r in res))}** (owner approval needed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
