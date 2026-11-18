#!/usr/bin/env python3
"""Stock reorder list and dead-stock check.

Usage:
  python3 tools/stock_reorder.py data/live/inventory.csv [--cover-months 1]

inventory.csv: sku,item,category,on_hand,reorder_point,reorder_qty,avg_monthly_sales,lead_time_days,supplier,unit_cost

Reorder when on_hand <= reorder_point. Suggested quantity = reorder_qty if given, else
enough to cover the lead time plus --cover-months of sales, minus stock on hand.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tgw_common import inr, md_table, money, read_csv, require_columns  # noqa: E402


def suggest(r, cover_months: float) -> int:
    fixed = money(r.get("reorder_qty"))
    if fixed > 0:
        return int(fixed)
    monthly = money(r.get("avg_monthly_sales"))
    lead_months = money(r.get("lead_time_days")) / 30
    need = math.ceil(monthly * (lead_months + cover_months) - money(r.get("on_hand")))
    return max(need, 1)


def analyse(rows, cover_months: float = 1.0):
    reorder, dead = [], []
    for r in rows:
        on_hand = money(r.get("on_hand"))
        if on_hand <= money(r.get("reorder_point")):
            qty = suggest(r, cover_months)
            reorder.append({**r, "qty": qty, "cost": qty * money(r.get("unit_cost"))})
        elif money(r.get("avg_monthly_sales")) == 0 and on_hand > 0:
            dead.append({**r, "value": on_hand * money(r.get("unit_cost"))})
    reorder.sort(key=lambda x: money(x.get("on_hand")) - money(x.get("reorder_point")))
    return reorder, dead


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inventory")
    ap.add_argument("--cover-months", type=float, default=1.0)
    a = ap.parse_args(argv)
    rows = read_csv(a.inventory)
    require_columns(rows, ["item", "on_hand", "reorder_point"], a.inventory)
    reorder, dead = analyse(rows, a.cover_months)
    print("# Stock reorder list")
    print(md_table(["SKU", "Item", "On hand", "Reorder point", "Suggested qty", "Supplier", "Est. cost"],
                   [[r.get("sku", ""), r["item"], r["on_hand"], r["reorder_point"], r["qty"], r.get("supplier", ""), inr(r["cost"])] for r in reorder]))
    print(f"\n**Estimated PO value: {inr(sum(r['cost'] for r in reorder))}** (check with Finance before placing POs)")
    if dead:
        print("\n## Slow or dead stock (no monthly sales)")
        print(md_table(["SKU", "Item", "On hand", "Stock value"], [[d.get("sku", ""), d["item"], d["on_hand"], inr(d["value"])] for d in dead]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
