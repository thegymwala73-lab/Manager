---
description: Month-end close pack (HR salary, Finance payables/receivables, Sales targets and incentives)
---
Run The Gym Wala **Month End** as the AI Chief of Staff (see CLAUDE.md).

Month: $ARGUMENTS (default: the month that just ended).

Run in parallel:
- `hr-admin`: attendance/OT sheet and salary sheet via `tools/salary_ot.py`.
- `finance-accounts`: receivables ageing, payables due, the month's collections and
  payments summary, GST/TDS/PF/ESI due dates, cash position.
- `sales-crm`: target vs achieved per salesperson. Achieved = pre-GST dispatch value
  credited in the workbook's `Dispatch_Master` / `Dashboard` section A (60-day rule,
  co-sale shares). Targets come from `data/live/targets.csv`. Incentives via `tools/incentives.py`.

Then consolidate into a CEO Brief. Decisions should include salary release approval
and incentive approval. Save it to `reports/YYYY-MM-month-end.md`.

Every number comes from data or a tool; list any missing inputs and who must provide them.
Nothing is paid or sent without the owner's OK. No Aarambh Events & Production.
