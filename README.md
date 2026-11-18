# The Gym Wala: AI Business Manager

An AI **Chief of Staff** that runs The Gym Wala (fitness equipment manufacturing,
trading, sales and distribution) through 7 specialised department subagents.
It's built on [Claude Code](https://code.claude.com): open this repo in Claude Code
and talk to it in Hinglish or English.

> Scope: **The Gym Wala only.** Aarambh Events & Production is deliberately excluded.
> This replaces the older "TGW CEO Office / Personal Manager" skill.

## How it works

```
                       Owner (one instruction)
                                │
                     ┌──────────▼──────────┐
                     │  AI Chief of Staff  │  CLAUDE.md
                     │ intake → route →    │  guardrails · conflict rules · CEO Brief
                     │ check → consolidate │
                     └──────────┬──────────┘
     ┌──────────┬──────────┬────┴─────┬──────────┬──────────┬──────────┐
     ▼          ▼          ▼          ▼          ▼          ▼          ▼
  Sales &   Marketing  Operations  Finance &   HR &     Product &  Research &
   CRM      & Branding & Inventory  Accounts   Admin  Manufacturing Expansion
     └──────────┴──────────┴────┬─────┴──────────┴──────────┴──────────┘
                                ▼
        knowledge/ (context) · tools/ (calculators) · templates/ (drafts)
        Google Drive lead sheets · Gmail · Calendar · Sheets · Canva
```

1. **Intake**: the Chief of Staff restates the request and tags the departments.
2. **Route**: one department, or several in parallel (or in sequence when one needs another's output).
3. **Execute**: subagents read the data, calculate with `tools/`, and draft outputs.
4. **Check and consolidate**: verify the figures and the guardrails, and resolve conflicts
   (compliance → cash safety → commitments → margin → growth).
5. **Report**: one CEO Brief (🔴 decisions · ✅ ready · 📋 departments · ⚠️ risks · ➡️ next actions).

## Departments

| Subagent | Responsibilities |
|---|---|
| `sales-crm` | TGW Sales Master Workbook (leads, follow-ups, dispatch sales), IndiaMART/Justdial enquiries, quotations, follow-ups, pipeline, targets and incentives |
| `marketing-branding` | Content calendar, captions and reels, Canva, listings, offers, catalogue, showroom |
| `operations-inventory` | Stock and reorder, POs, order tracker, dispatch, installation |
| `finance-accounts` | Receivables, payables plan, cash flow, GST and invoicing, margins |
| `hr-admin` | Attendance, OT, salary, hiring, onboarding, policies, admin |
| `product-manufacturing` | Own products, BOM and costing, fabricators, production, QC, fit-outs |
| `research-expansion` | Competitors, market prices, new products, dealers, new cities, tenders, exports |

## Commands

| Say / type | Result |
|---|---|
| `/morning-brief` ("aaj ka plan") | Calendar, important mail, dues, follow-ups, dispatches, top 3 priorities |
| `/weekly-review` | All 7 departments in parallel → CEO Brief |
| `/month-end` | Salary, payables/receivables, targets and incentives |
| `/leads` | Pipeline from all Drive lead sheets |
| `/orders` | Order tracker with advance and balance |
| `/pay-plan` ("kisko payment karun?") | Vendor payments within available cash |
| `/dept sales …` | Send a task straight to one department |

You can also just ask in plain language: "is mahine ke hot leads dikhao", "row machine ki costing banao",
"Ludhiana mein dealer kaise banayein?"

## Calculators (`tools/`, Python 3, no installs needed)

| Tool | Purpose |
|---|---|
| `leads_report.py` | Normalises all lead-sheet layouts → stages, hot leads, overdue, nurture, duplicates |
| `incentives.py` | Target vs achieved → incentive by slab |
| `payables_plan.py` | Weekly payment plan within cash and minimum balance |
| `receivables_ageing.py` | Customer dues by age bucket |
| `stock_reorder.py` | Reorder list and dead stock |
| `salary_ot.py` | Salary sheet with OT, late cuts and deductions |
| `bom_costing.py` | Product cost and margin |

Run `python3 tools/<tool>.py --help`. Tests: `python3 -m unittest discover -s tests`.

## Guardrails
- **Approval first**: nothing is sent, paid, promised, scheduled or edited without the
  owner's OK (enforced by `.claude/settings.json` permission prompts).
- **No invented numbers**: figures come from data or `tools/`, with their source.
- **Privacy**: this repo is **public**. Real data lives in Google Drive or in the
  git-ignored `data/live/` and `reports/`. Only placeholders are committed.

## Setup checklist
1. ☐ **Make this repository private** (recommended before adding any real business details).
2. ☐ Fill in the `knowledge/` files (placeholders marked `[[ … ]]`).
3. ☐ Connect Google Drive, Sheets, Gmail, Calendar and Canva in Claude.
4. ☐ Add the names of your orders, inventory, payables and attendance sheets to
   `knowledge/data-sources.md` (or use the CSV templates in `data/templates/`).
5. ☐ Disable the old "tgw-ceo-office" skill in Claude settings so the two systems don't overlap.
6. ☐ Try `/leads` and `/morning-brief`.
