# Data templates

Column formats for the `tools/` scripts. **The rows here are fake samples.**

To use real data:
1. Copy a template to `data/live/` (git-ignored, never pushed), or export the
   matching Google Sheet tab as CSV into `data/live/`.
2. Run the tool, e.g. `python3 tools/payables_plan.py data/live/payables.csv --cash 300000`.

Dates are DD/MM/YYYY. Money is plain numbers (₹ and commas are tolerated).

| File | Tool |
|---|---|
| `leads_layout_a.csv` (or raw lead sheet tabs) | `tools/leads_report.py` |
| `targets.csv` + `incentive_slabs.csv` | `tools/incentives.py` |
| `payables.csv` | `tools/payables_plan.py` (`category`: statutory / salary / supplier / other; `priority`: A / B / C) |
| `receivables.csv` | `tools/receivables_ageing.py` |
| `inventory.csv` | `tools/stock_reorder.py` |
| `attendance.csv` | `tools/salary_ot.py` (`present_days` should include paid weekly offs) |
| `bom.csv` | `tools/bom_costing.py` |
| `orders.csv` | read directly by Operations and Finance |
