---
description: Send a task straight to one department, e.g. /dept sales quotation for 5 treadmills
---
The owner wants this routed straight to one department: $ARGUMENTS

1. Map the first word to a subagent: sales→`sales-crm`, marketing→`marketing-branding`,
   ops/operations/inventory/dispatch→`operations-inventory`, finance/accounts→`finance-accounts`,
   hr/admin→`hr-admin`, product/manufacturing/factory→`product-manufacturing`,
   research/expansion→`research-expansion`.
2. Brief that subagent following CLAUDE.md section 4 (goal, context, sources,
   deliverable, draft-only rule).
3. Check the result against the guardrails, then return it to the owner in Hinglish,
   with any decision needed at the top.
