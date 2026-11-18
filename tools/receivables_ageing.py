#!/usr/bin/env python3
"""Receivables ageing: who owes The Gym Wala how much, and for how long.

Usage:
  python3 tools/receivables_ageing.py data/live/receivables.csv [--today DD/MM/YYYY]

receivables.csv: customer,order_id,invoice_date,due_date,amount,received,notes
Age is counted in days past the due date (or the invoice date if there's no due date).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tgw_common import fmt_date, inr, md_table, money, parse_date, read_csv, require_columns, today_or  # noqa: E402

BUCKETS = ["Not due", "0-30", "31-60", "61-90", "90+"]


def bucket(days_past_due: int | None) -> str:
    if days_past_due is None or days_past_due < 0:
        return "Not due"
    if days_past_due <= 30:
        return "0-30"
    if days_past_due <= 60:
        return "31-60"
    if days_past_due <= 90:
        return "61-90"
    return "90+"


def ageing(rows, today):
    items = []
    for r in rows:
        bal = money(r.get("amount")) - money(r.get("received"))
        if bal <= 0:
            continue
        due = parse_date(r.get("due_date")) or parse_date(r.get("invoice_date"))
        days = (today - due).days if due else None
        items.append({**r, "balance": bal, "due": due, "days": days, "bucket": bucket(days)})
    items.sort(key=lambda x: -(x["days"] if x["days"] is not None else -9999))
    return items


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("receivables")
    ap.add_argument("--today")
    a = ap.parse_args(argv)
    today = today_or(a.today)
    rows = read_csv(a.receivables)
    require_columns(rows, ["customer", "amount"], a.receivables)
    items = ageing(rows, today)
    totals = {b: sum(i["balance"] for i in items if i["bucket"] == b) for b in BUCKETS}
    print(f"# Receivables ageing: as of {fmt_date(today)}")
    print(md_table(BUCKETS + ["Total"], [[inr(totals[b]) for b in BUCKETS] + [inr(sum(totals.values()))]]))
    print("\n## Detail (oldest first)")
    print(md_table(["Customer", "Order", "Due", "Balance", "Days past due", "Bucket", "Notes"],
                   [[i["customer"], i.get("order_id", ""), fmt_date(i["due"]), inr(i["balance"]),
                     "" if i["days"] is None else i["days"], i["bucket"], i.get("notes", "")] for i in items]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
