#!/usr/bin/env python3
"""BOM costing and margin for an own-manufactured product.

Usage:
  python3 tools/bom_costing.py data/live/bom.csv [--overhead-pct 10] [--price 45000] [--units 1]

bom.csv: part,spec,qty,unit_cost,category  (cost for ONE finished unit)
--price is the selling price per unit EXCLUDING GST.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tgw_common import inr, md_table, money, read_csv, require_columns  # noqa: E402


def cost(rows, overhead_pct=0.0):
    lines = [{**r, "total": money(r.get("qty")) * money(r.get("unit_cost"))} for r in rows]
    direct = sum(line["total"] for line in lines)
    overhead = direct * overhead_pct / 100
    by_cat: dict[str, float] = {}
    for line in lines:
        cat = line.get("category") or "other"
        by_cat[cat] = by_cat.get(cat, 0) + line["total"]
    return lines, direct, overhead, direct + overhead, by_cat


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bom")
    ap.add_argument("--overhead-pct", type=float, default=0.0)
    ap.add_argument("--price", type=float, help="Selling price per unit, excl. GST")
    ap.add_argument("--units", type=int, default=1)
    a = ap.parse_args(argv)
    rows = read_csv(a.bom)
    require_columns(rows, ["part", "qty", "unit_cost"], a.bom)
    lines, direct, overhead, unit_cost, by_cat = cost(rows, a.overhead_pct)
    print("# BOM costing (per unit)")
    print(md_table(["Part", "Spec", "Qty", "Unit cost", "Total", "Category"],
                   [[x["part"], x.get("spec", ""), x["qty"], inr(money(x["unit_cost"])), inr(x["total"]), x.get("category", "")] for x in lines]))
    print("\n## Cost by category")
    print(md_table(["Category", "Cost", "Share"], [[c, inr(v), f"{(v / direct * 100 if direct else 0):.1f}%"] for c, v in sorted(by_cat.items(), key=lambda kv: -kv[1])]))
    print(f"\nDirect cost: {inr(direct)} · Overhead ({a.overhead_pct:g}%): {inr(overhead)} · **Unit cost: {inr(unit_cost)}**")
    if a.price:
        margin = a.price - unit_cost
        pct = margin / a.price * 100
        print(f"Price {inr(a.price)} → margin **{inr(margin)} ({pct:.1f}%)** per unit; {a.units} units → {inr(margin * a.units)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
