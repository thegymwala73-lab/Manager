---
description: Weekly review across all 7 departments, consolidated into one CEO Brief
---
Run The Gym Wala **Weekly Review** as the AI Chief of Staff (see CLAUDE.md).

Period: the last 7 days, ending today (Asia/Kolkata), unless specified: $ARGUMENTS

Spawn **all 7 department subagents in parallel**, each with a brief asking for their
weekly report in the format in `templates/dept-report.md`:
- `sales-crm`: leads in, quotations, visits, sales, conversion per salesperson,
  overdue follow-ups, and target pacing.
- `marketing-branding`: content posted against plan, listing and review status,
  lead-source mix (from Sales), next week's plan.
- `operations-inventory`: orders dispatched and installed, pending orders, delays,
  reorder list.
- `finance-accounts`: collections received and due, payables due, cash snapshot for
  the next 4 weeks, statutory dues.
- `hr-admin`: attendance issues, OT, hiring status, staff issues, admin renewals.
- `product-manufacturing`: production status, QC issues, costing updates, project status.
- `research-expansion`: notable competitor moves, open tenders, expansion pipeline,
  one opportunity worth a decision.

Then consolidate:
1. Resolve conflicts between departments (CLAUDE.md section 7).
2. Produce one **CEO Brief** (`templates/ceo-brief.md`), with at most 3 decisions,
   each with a recommendation.
3. Save it to `reports/YYYY-MM-DD-weekly-review.md`.

Draft only; nothing is sent. No invented numbers. No Aarambh Events & Production content.
