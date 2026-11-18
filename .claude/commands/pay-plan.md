---
description: Weekly vendor payment plan within available cash ("kisko payment karun?")
---
Delegate to `finance-accounts`: build this week's **vendor payment plan** for The Gym Wala.

Owner input (available cash, must-pay vendors, anything to hold): $ARGUMENTS

Steps:
1. Load the payables (`data/live/payables.csv` or the sheet in `knowledge/data-sources.md`).
2. Load the minimum cash balance and vendor priorities from `knowledge/policies/finance.md`
   and `knowledge/vendors.md`.
3. Run `python3 tools/payables_plan.py data/live/payables.csv --cash <amount> --today <DD/MM/YYYY>`.
   If the owner gave no cash figure, ask for it. Don't assume one.
4. Return: a pay-this-week table, a hold list with reasons, the remaining cash, and
   any statutory dues.

Recommendation only. No payment is made or promised.
