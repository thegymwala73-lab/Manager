---
description: Daily morning brief for the owner (aaj ka plan)
---
Prepare today's **Morning Brief** for The Gym Wala owner, as the AI Chief of Staff (see CLAUDE.md).

Today: use the current date in Asia/Kolkata. Extra focus from the owner: $ARGUMENTS

Collect (read only; send or change nothing):
1. **Calendar**: today's and tomorrow-morning's events (Google Calendar).
2. **Gmail**: important unread mail from the last 24 hours: customers, vendors,
   IndiaMART/Justdial enquiries, transporters, bank, GST/accountant. One line each.
3. **Sales** (`sales-crm`): from the TGW Sales Master Workbook, today's and overdue
   follow-ups per person (`Aaj ke Follow-ups`), new leads since yesterday, leads not
   contacted within 24 hours, this month's dispatch sales (`Dashboard`), and any pending
   dispatches in `Dispatch_Master`.
4. **Finance** (`finance-accounts`): payments due this week, collections due this week.
5. **Operations** (`operations-inventory`): dispatches and installations today or
   tomorrow, and critical low stock.

Run steps 3–5 as subagents in parallel. Skip a department quickly if its data source
isn't set up yet, and say so in one line.

Output in Hinglish, phone-friendly:
- **Top 3 priorities aaj ke** (each with why)
- 🔴 Decisions, ✅ Ready for approval, 📋 Department-wise, ⚠️ Risks, ➡️ Next actions
  (the CEO Brief format, `templates/ceo-brief.md`)

Keep it under about 25 lines. No Aarambh Events & Production items.
