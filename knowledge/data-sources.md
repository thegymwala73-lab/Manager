# Data sources

Where each department's data lives, and how agents read it. **Read-only** unless
the owner approves a write. File IDs are not stored here because this repo is
public. Agents locate files by title search.

## 0. Sales & leads: "TGW Sales Master Workbook" (PRIMARY, live)

The main sales system. It's one Google Sheet in the owner's Drive.

- **Find**: Google Drive `search_files` with
  `title contains 'TGW Sales Master Workbook' and mimeType = 'application/vnd.google-apps.spreadsheet'`.
  If the owner pastes the link, take the ID from the URL (`/spreadsheets/d/<ID>/`).
  Don't write the ID into any committed file.
- **Tabs**

  | Tab | What it is | How agents use it |
  |---|---|---|
  | `Dashboard` | Formula-driven: sales this month (pre-GST dispatch value per person), lead funnel, open pipeline (quotation value), monthly dispatch trend | **First stop** for sales numbers. Read `A1:Z60`. Only the yellow month cell is meant to change. |
  | `Aaj ke Follow-ups` | Automatic list of today's and overdue follow-ups per person (row 2 has today's counts) | Morning brief, daily follow-up list. Read `A1:N500`. |
  | `<Name> Leads` (one per salesperson) | Where leads are entered and updated. The Team Manager adds them in the morning; the assignee updates them by 7 PM. Row 1 may hold a written daily review. Header on **row 6**, data from row 7. | Detailed lead work, per-person reviews |
  | `Leads` | Automatic join of all person pages (view only). Row 4 shows the next free lead ID and the total. Header on row 6. | Whole-team pipeline. Export to CSV → `tools/leads_report.py` |
  | `Dispatch_Master` | One row per dispatch (pre-GST), the credited employee (60-day rule), co-sales, payment received. Header on **row 5**. | Sales achieved, Finance cross-check, Operations dispatch list |
  | `Settings` | Policy year start, 24-hour first-contact limit, 60-day ownership | Rules (read only) |
  | `Guide` | How the workbook works | Read once for context |

- **Lead columns** (person pages and Leads): ID · Assigned on · Channel (lead source,
  e.g. Meta lead form / IndiaMART / Justdial) · Source (our page or brand) · Name · Phone ·
  Email · City · State · Zip · Looking for · Area · Budget · Phone verified? · Assigned to ·
  Original owner · Call status · First contact date · Last update date · **Stage** ·
  **Next follow-up date** · Quotation value (₹) · Expected closing date · **Booking date** ·
  Lost reason · Update notes · *automatic:* Score · Priority · Value (₹) · Contacted within
  24h? · Days since received · Ownership till (60 days) · Ownership status · Credit to · Alert.
- **Business rules** (from the Guide and Settings tabs):
  - first contact within **24 hours** of the lead arriving; if missed, the Team Manager may reassign;
  - **60-day ownership**: the original owner gets credit for a booking within 60 days of
    the lead's arrival; no activity for 60 days → "Reassign";
  - flow: lead → person page → evening updates → Stage "Booked" with a booking date →
    a Dispatch_Master row with the Lead ID → Dashboard;
  - **Sales achieved = pre-GST dispatch value** in Dispatch_Master (not bookings);
  - targets and incentive slabs are deliberately kept **outside** this shared file
    (use `data/live/targets.csv` and `data/live/incentive_slabs.csv`, owner only).
- **Write rules**: this workbook is the team's live system. Agents **never** write to
  it without the owner's explicit OK for that exact change. Never type in the `Leads`,
  `Dashboard` or `Aaj ke Follow-ups` tabs or the grey automatic columns (they are formulas).
  Suggested updates (e.g. missing follow-up dates, a stage that's wrong) go to the owner
  or Team Manager as a list.
- **Calculations**: export a tab with `get_values` to `data/live/leads/<tab>.csv` and
  run `python3 tools/leads_report.py data/live/leads/<tab>.csv --today DD/MM/YYYY`. The
  tool finds the header row by itself and understands these columns. Prefer the
  Dashboard's own figures when they answer the question, and cross-check with the tool
  when something looks off.

## 1. Leads: older monthly lead sheets (legacy, before the workbook)

- **Where**: the owner's Google Drive, one spreadsheet per salesperson per month.
  Titles contain `Lead` / `LEADS` plus the person's name and month, e.g.
  "<Name> Jan. Lead Today Calling", "MARCH LEADS <NAME>", "Feb Leads <Name>".
- **Find**: Google Drive `search_files` with
  `(title contains 'Lead' or title contains 'LEADS') and mimeType = 'application/vnd.google-apps.spreadsheet'`,
  `orderBy: modifiedTime desc`. Ignore titles starting with "Copy of".
- **Tabs**: a file can have several tabs (e.g. "Start Lead - <date>",
  "Indiamart & Just-Dail Lead"). Read all non-empty tabs; skip blank "Sheet2"/"Sheet3".
  A tab name containing "Indiamart" or "Just" sets the lead **source**.
- **Read**: Google Sheets `get_spreadsheet` (tab names), then `get_values` on
  `'<tab>'!A1:Z`.
- **Normalise**: save each tab as CSV in `data/live/leads/` (git-ignored) and run
  `python3 tools/leads_report.py data/live/leads/*.csv --today DD/MM/YYYY`.
  The tool recognises all the current header layouts below automatically.

### Known header layouts → normalised fields

| Normalised field | Layout A (e.g. "… Lead Today Calling") | Layout B (e.g. "MARCH LEADS …") | Layout C (e.g. "Feb Leads …", "… LEADS GYM SETUP") |
|---|---|---|---|
| date | Date | DATE | DATE |
| salesperson | Employee Name | EMPLOYEE NAME | EMPLOYEE NAME |
| customer | Customer Name | CUSTOMER NAME | CUSTOMER NAME |
| phone | Number | PHONE NO | PHONE NO |
| location | Location | LOCATION | LOCATION |
| requirement | Requirements | Requirement | Requirement |
| status | Status | — | — |
| notes (joined) | Follow-up 1, Follow-up 2, Remarks & Notes | Remarks 1–4 | Remarks 1–4 |
| last_call | — | LAST CALL | — |
| quotation_date | Quetation Date | QUOTATION DATE | — |
| quotation_sent | (derived: a quotation date is filled) | Quotation YES/NO | Quotation YES/NO |
| visit_date | Customer Visting Date | VISTING DATE | VISTING DATE |
| sale | (derived from Status, e.g. "sold", "done", "converted") | SALE | SALE |

If a new layout appears, add its header aliases to `HEADER_ALIASES` in
`tools/leads_report.py`, with a test.

### Recommended (optional): one standard lead sheet format
Ask all salespeople to use the same columns for new months:
`S No | Date | Employee Name | Customer Name | Phone | Location | Source | Requirement | Status | Last Call | Next Follow-up | Quotation Date | Quotation Amount | Visit Date | Sale Amount | Remarks`.
Status values: `New, Contacted, Quoted, Visit, Negotiation, Won, Lost`.

## 2. Other data (set up as you go)

| Data | Preferred home | Fallback | Template |
|---|---|---|---|
| Dispatches (sales achieved) | **TGW Sales Master Workbook → `Dispatch_Master`** | — | — |
| Orders (open, pre-dispatch) | [[ Google Sheet name ]] | `data/live/orders.csv` | `data/templates/orders.csv` |
| Inventory | [[ Google Sheet name ]] | `data/live/inventory.csv` | `data/templates/inventory.csv` |
| Payables (vendor bills) | [[ ledger / Tally export / Sheet ]] | `data/live/payables.csv` | `data/templates/payables.csv` |
| Receivables | [[ ]] | `data/live/receivables.csv` | `data/templates/receivables.csv` |
| Attendance | [[ ]] | `data/live/attendance.csv` | `data/templates/attendance.csv` |
| BOM / costing | [[ ]] | `data/live/bom.csv` | `data/templates/bom.csv` |
| Incentive slabs | [[ ]] | `data/live/incentive_slabs.csv` | `data/templates/incentive_slabs.csv` |
| Sales targets | [[ ]] | `data/live/targets.csv` | `data/templates/targets.csv` |

## 3. Connected apps
- **Gmail**: customer, vendor, IndiaMART/Justdial, transporter and accountant mail
  (read; drafts allowed; sending needs approval).
- **Google Calendar**: meetings, visits, installations (read; changes need approval).
- **Google Drive / Sheets / Docs**: data and reports.
- **Canva**: marketing designs.

## 4. How the lead stage is decided (`tools/leads_report.py`)
The **latest remark** (the last filled column among Requirement and Remarks/Follow-ups)
is treated as the lead's current state, together with the Status, Quotation, Visit and
Sale columns:

| Stage | Rule (first match wins) |
|---|---|
| Won | SALE is filled (anything except "no") or Status says sold/converted |
| Lost | Latest remark or Status says not interested / no requirement / not eligible / budget issue / not in service… (common misspellings included) |
| Duplicate | A remark says "already with <name>" / "already talk…" |
| Visit | A visit date is filled |
| Quoted | Quotation YES, or a quotation date is filled |
| Later | Latest remark says not planned yet / plan in <month> / next month / just enquiry |
| Contacted | Any remark or last-call date |
| New | Nothing yet |

The report also flags invalid phone numbers and the same number entered more than
once (e.g. two salespeople calling the same customer).
