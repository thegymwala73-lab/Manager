#!/usr/bin/env python3
"""Monthly salary and overtime sheet.

Usage:
  python3 tools/salary_ot.py data/live/attendance.csv --days-in-month 30
      [--salary-basis 30] [--hours-per-day 8] [--ot-multiplier 1] [--lates-per-half-day 3]

attendance.csv: employee,monthly_salary,present_days,paid_leave_days,absent_days,late_count,ot_hours,advance_deduction,other_deduction
  present_days should include paid weekly offs/holidays as per policy.

per-day rate = monthly_salary / salary_basis (default: days in month)
gross        = per-day × (present_days + paid_leave_days)
OT           = ot_hours × (per-day / hours_per_day) × ot_multiplier
late cut     = floor(late_count / lates_per_half_day) × 0.5 day (0 = no late cut)
net          = gross + OT − late cut − advance − other deductions
Set the options to match knowledge/policies/hr.md.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tgw_common import inr, md_table, money, read_csv, require_columns  # noqa: E402


def compute(r, days_in_month, salary_basis=None, hours_per_day=8.0, ot_multiplier=1.0, lates_per_half_day=0):
    basis = salary_basis or days_in_month
    per_day = money(r.get("monthly_salary")) / basis
    payable_days = min(money(r.get("present_days")) + money(r.get("paid_leave_days")), days_in_month)
    gross = per_day * payable_days
    ot = money(r.get("ot_hours")) * per_day / hours_per_day * ot_multiplier
    late_days = (int(money(r.get("late_count"))) // lates_per_half_day) * 0.5 if lates_per_half_day else 0.0
    late_cut = late_days * per_day
    deductions = late_cut + money(r.get("advance_deduction")) + money(r.get("other_deduction"))
    net = gross + ot - deductions
    return {"employee": r.get("employee", ""), "salary": money(r.get("monthly_salary")), "payable_days": payable_days,
            "gross": round(gross), "ot": round(ot), "late_days": late_days, "deductions": round(deductions), "net": round(net)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("attendance")
    ap.add_argument("--days-in-month", type=int, required=True)
    ap.add_argument("--salary-basis", type=float, help="Divide monthly salary by this (default: days in month; some firms use 26)")
    ap.add_argument("--hours-per-day", type=float, default=8.0)
    ap.add_argument("--ot-multiplier", type=float, default=1.0)
    ap.add_argument("--lates-per-half-day", type=int, default=0)
    a = ap.parse_args(argv)
    rows = read_csv(a.attendance)
    require_columns(rows, ["employee", "monthly_salary", "present_days"], a.attendance)
    res = [compute(r, a.days_in_month, a.salary_basis, a.hours_per_day, a.ot_multiplier, a.lates_per_half_day) for r in rows]
    print("# Salary sheet")
    print(md_table(["Employee", "Monthly salary", "Payable days", "Gross", "OT", "Late cut (days)", "Deductions", "Net payable"],
                   [[x["employee"], inr(x["salary"]), f"{x['payable_days']:g}", inr(x["gross"]), inr(x["ot"]), f"{x['late_days']:g}", inr(x["deductions"]), inr(x["net"])] for x in res]))
    print(f"\n**Total net payable: {inr(sum(x['net'] for x in res))}** (release only after the owner's approval)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
