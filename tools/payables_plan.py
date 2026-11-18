#!/usr/bin/env python3
"""Weekly vendor payment plan within available cash ("kisko payment karun?").

Usage:
  python3 tools/payables_plan.py data/live/payables.csv --cash 300000 [--min-balance 50000] [--horizon 7] [--today DD/MM/YYYY]

payables.csv: vendor,bill_no,bill_date,due_date,amount,paid,priority,category,notes
  category: statutory | salary | supplier | other    priority: A | B | C

Order of payment: statutory → salary → by priority (A, B, C) → most overdue → earliest due.
Only bills that are overdue or due within the horizon are considered for this week.
Bills are paid in full or held (no automatic part-payments). This is a recommendation only.
"""
from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tgw_common import fmt_date, inr, md_table, money, parse_date, read_csv, require_columns, today_or  # noqa: E402

CATEGORY_RANK = {"statutory": 0, "salary": 1, "supplier": 2, "other": 3}
PRIORITY_RANK = {"A": 0, "B": 1, "C": 2}


def plan(rows, cash, min_balance, today, horizon):
    bills = []
    for r in rows:
        outstanding = money(r.get("amount")) - money(r.get("paid"))
        if outstanding <= 0:
            continue
        due = parse_date(r.get("due_date")) or parse_date(r.get("bill_date"))
        overdue = (today - due).days if due else 0
        bills.append({**r, "outstanding": outstanding, "due": due, "overdue": overdue,
                      "cat": r.get("category", "other").strip().lower() or "other",
                      "prio": (r.get("priority", "C").strip().upper() or "C")})
    cutoff = today + timedelta(days=horizon)
    in_window = [b for b in bills if b["due"] is None or b["due"] <= cutoff]
    later = [b for b in bills if b not in in_window]
    in_window.sort(key=lambda b: (CATEGORY_RANK.get(b["cat"], 3), PRIORITY_RANK.get(b["prio"], 2), -b["overdue"], b["due"] or today))

    budget = cash - min_balance
    pay, hold = [], []
    for b in in_window:
        if b["outstanding"] <= budget:
            budget -= b["outstanding"]
            pay.append(b)
        else:
            hold.append(b)
    return pay, hold, later, budget + min_balance


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("payables")
    ap.add_argument("--cash", type=float, required=True, help="Cash available to pay (₹)")
    ap.add_argument("--min-balance", type=float, default=0.0, help="Cash to keep untouched (₹); see knowledge/policies/finance.md")
    ap.add_argument("--horizon", type=int, default=7, help="Days ahead to include (default 7)")
    ap.add_argument("--today")
    a = ap.parse_args(argv)
    today = today_or(a.today)
    rows = read_csv(a.payables)
    require_columns(rows, ["vendor", "due_date", "amount"], a.payables)
    pay, hold, later, remaining = plan(rows, a.cash, a.min_balance, today, a.horizon)

    def row(b, why):
        od = f"{b['overdue']} days overdue" if b["overdue"] > 0 else (f"due in {-b['overdue']} days" if b["due"] else "no date")
        return [b.get("vendor"), b.get("bill_no", ""), fmt_date(b["due"]), inr(b["outstanding"]), b["cat"], b["prio"], od, why]

    hdr = ["Vendor", "Bill", "Due", "Outstanding", "Category", "Priority", "Timing", "Note"]
    print(f"# Payment plan: week from {fmt_date(today)}")
    print(f"Cash available {inr(a.cash)} · keep minimum {inr(a.min_balance)} · horizon {a.horizon} days\n")
    print(f"## ✅ Recommended to pay: {inr(sum(b['outstanding'] for b in pay))}")
    print(md_table(hdr, [row(b, "statutory" if b["cat"] == "statutory" else "") for b in pay]))
    print(f"\n## ⏸ Hold (insufficient cash): {inr(sum(b['outstanding'] for b in hold))}")
    print(md_table(hdr, [row(b, "needs more cash or a part-payment decision") for b in hold]))
    stat_hold = [b for b in hold if b["cat"] in ("statutory", "salary")]
    if stat_hold:
        print("\n⚠️ **Statutory or salary dues are on hold. Arrange cash urgently.**")
    print(f"\n## Upcoming (after {a.horizon} days): {inr(sum(b['outstanding'] for b in later))}, {len(later)} bills")
    print(f"\n**Cash left after recommended payments: {inr(remaining)}**")
    print("\n_Recommendation only. Nothing is paid without the owner's approval._")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
