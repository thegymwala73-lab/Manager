---
description: Lead pipeline across all Drive lead sheets (new, hot, overdue, per salesperson)
---
Delegate to the `sales-crm` subagent: build The Gym Wala **lead pipeline report**.

Scope from the owner (salesperson, month or source): $ARGUMENTS. Default: the current
month and the previous month, all salespeople.

Steps:
1. Open the **TGW Sales Master Workbook** (`knowledge/data-sources.md` section 0).
   Read `Dashboard` (sections B and C) and `Aaj ke Follow-ups`.
2. Export the `Leads` tab (or the requested `<Name> Leads` page) to
   `data/live/leads/<tab>.csv` and run
   `python3 tools/leads_report.py data/live/leads/<tab>.csv --today <DD/MM/YYYY>`.
   Use the older monthly sheets only if the owner asks for history.
3. Check the workbook's rules: leads missing 24-hour contact, "Reassign" (60-day) alerts,
   "No update 3+ days" alerts, connected leads with no next follow-up date.
4. Return:
   - a per-salesperson summary (leads, quotations, visits, sales, conversion %);
   - a **hot leads** table (quotation sent or visit planned, no sale yet);
   - an **overdue follow-ups** table (no touch in 3+ days, not closed);
   - a **lead discipline** list for the Team Manager (missing dates, stale stages, alerts);
   - 3 Hinglish WhatsApp follow-up drafts for the hottest leads (drafts only).

Don't paste phone numbers in the chat summary unless the owner asks; show the last
4 digits. Nothing is sent.
