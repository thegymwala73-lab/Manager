---
description: Order tracker (advance, balance, dispatch, installation, next step)
---
Build The Gym Wala **order tracker** as the AI Chief of Staff. Filter: $ARGUMENTS

Run in parallel:
- `operations-inventory`: all open orders, with items, dispatch and installation
  dates, status and blockers.
- `finance-accounts`: advance received and balance due per order.

Merge into one table:
`Order | Customer | City | Advance | Balance | Dispatch | Install | Status | Next step (who · when)`

Then flag: orders delayed past the promised date, orders ready to dispatch but with
balance pending, and installations without a confirmed technician. Draft customer
update messages only if asked. Nothing is sent.
