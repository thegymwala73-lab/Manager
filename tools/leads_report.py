#!/usr/bin/env python3
"""Lead pipeline report from The Gym Wala's Drive lead sheets (exported as CSV).

Accepts any of the known sheet layouts (see knowledge/data-sources.md) and
normalises them into one pipeline.

Usage:
  python3 tools/leads_report.py data/live/leads/*.csv --today 18/11/2026
  python3 tools/leads_report.py a.csv --source IndiaMART --stale-days 3 --out data/live/leads_normalised.csv
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import OrderedDict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tgw_common import fmt_date, inr, md_table, parse_date, parse_money, today_or  # noqa: E402

# Header (lowercase, letters and digits only) -> normalised field.
HEADER_ALIASES = {
    # TGW Sales Master Workbook (person pages and the combined Leads tab)
    "id": "lead_id",
    "leadid": "lead_id",
    "assignedondatetime": "date",
    "channel": "source",
    "lookingfor": "requirement",
    "budgetassubmitted": "budget",
    "budget": "budget",
    "assignedto": "salesperson",
    "originalowner": "original_owner",
    "callstatus": "call_status",
    "firstcontactdate": "first_contact",
    "lastupdatedate": "last_call",
    "stage": "status",
    "nextfollowupdate": "next_followup",
    "quotationvalue": "quotation_amount",
    "expectedclosingdate": "expected_close",
    "bookingdate": "booking_date",
    "lostreason": "lost_reason",
    "updatenotesnewlinewithdate": "notes",
    "priority": "priority",
    "alert": "alert",
    "creditto": "credit_to",
    # Older monthly lead sheets
    "date": "date",
    "leaddate": "date",
    "employeename": "salesperson",
    "employee": "salesperson",
    "salesperson": "salesperson",
    "customername": "customer",
    "customer": "customer",
    "name": "customer",
    "number": "phone",
    "phoneno": "phone",
    "phone": "phone",
    "mobile": "phone",
    "mobileno": "phone",
    "contactno": "phone",
    "location": "location",
    "city": "location",
    "requirements": "requirement",
    "requirement": "requirement",
    "status": "status",
    "source": "source",
    "leadsource": "source",
    "lastcall": "last_call",
    "nextfollowup": "next_followup",
    "quetationdate": "quotation_date",
    "quotationdate": "quotation_date",
    "quotationyesno": "quotation_flag",
    "quotation": "quotation_flag",
    "quotationamount": "quotation_amount",
    "customervistingdate": "visit_date",
    "customervisitingdate": "visit_date",
    "vistingdate": "visit_date",
    "visitingdate": "visit_date",
    "visitdate": "visit_date",
    "sale": "sale",
    "saleamount": "sale",
}
NOTE_HEADER = re.compile(r"^(followup\d*|remarks\d*|remarksnotes|remarksandnotes|notes)$")

YES = {"yes", "y", "haan", "ha", "done", "sent", "send", "ok", "1", "true"}
NO = {"no", "n", "nahi", "na", "0", "-", "false", "nil", "none", "pending"}
WON_WORDS = ("booked", "sold", "won", "converted", "order confirmed", "order done", "deal done", "closed won", "sale done")
# Matched against the status column and the LATEST remark (letters only, lowercase),
# so common spellings used in the sheets ("NOT INTRESTED", "NO REQUIRMENT") are covered.
LATER_WORDS = ("notplanyet", "planin", "planafter", "aftermonth", "nextmonth", "requirmentyet",
               "requirementyet", "planned", "plandelayed", "justinquiry", "justenquiry")
LOST_WORDS = ("notinterested", "notintrested", "notintersted", "nointerest", "lost", "norequirement",
              "norequirment", "noreqirment", "norequriment", "notrequired", "notrequirment", "cancel",
              "wrongnumber", "closedlost", "notinservice", "noteligible", "noeligible", "budgetissue",
              "purchasedfromother", "boughtfromother", "languageissue")
DUPLICATE_WORDS = ("alreadywith", "alreadytalk", "alredytalk", "alredywith", "alreadyin")

FIELDS = [
    "lead_id", "date", "salesperson", "original_owner", "customer", "phone", "location",
    "requirement", "budget", "source", "page", "call_status", "first_contact", "status",
    "last_call", "next_followup", "quotation_date", "quotation_flag", "quotation_amount",
    "expected_close", "visit_date", "booking_date", "sale", "lost_reason", "priority",
    "alert", "credit_to", "notes", "stage", "last_touch", "file",
]


def _letters(text: str) -> str:
    return re.sub(r"[^a-z]", "", (text or "").lower())


def norm_phone(phone: str) -> str:
    """Last 10 digits of an Indian mobile number, or '' if it doesn't look valid."""
    d = re.sub(r"\D", "", phone or "")
    if len(d) == 12 and d.startswith("91"):
        d = d[2:]
    elif len(d) == 11 and d.startswith("0"):
        d = d[1:]
    return d if len(d) == 10 and d[0] in "6789" else ""


def norm_header(h: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (h or "").lower())


def _norm_source(text: str) -> str:
    t = text.lower()
    if "indiamart" in t or "india mart" in t or "india_mart" in t:
        return "IndiaMART"
    if "justdial" in t or "just-dail" in t or "just dail" in t or "just-dial" in t or "justdail" in t:
        return "Justdial"
    return ""


def map_headers(headers: list[str]) -> list[str | None]:
    out: list[str | None] = []
    keys = {norm_header(h) for h in headers}
    for h in headers:
        key = norm_header(h)
        if key == "source" and "channel" in keys:
            out.append("page")  # workbook: Channel = lead source, Source = our page/brand
        elif key in HEADER_ALIASES:
            out.append(HEADER_ALIASES[key])
        elif NOTE_HEADER.match(key):
            out.append("notes")
        else:
            out.append(None)  # S No. and unknown columns are ignored
    return out


def classify(lead: dict, today: date) -> dict:
    status = lead.get("status", "").lower()
    sale = lead.get("sale", "").strip()
    sale_l = sale.lower()

    won = bool(parse_date(lead.get("booking_date")))
    if sale and sale_l not in NO:
        won = True
    if any(w in status for w in WON_WORDS):
        won = True
    # The latest remark is the current state of the lead.
    remarks = [lead.get("requirement", "")] + [n for n in lead.get("notes", "").split(" | ") if n]
    latest = _letters(remarks[-1]) if remarks else ""
    status_k = _letters(status)
    later = any(w in latest for w in LATER_WORDS) or any(w in status_k for w in LATER_WORDS)
    lost = not won and not later and (
        any(w in status_k for w in LOST_WORDS) or any(w in latest for w in LOST_WORDS) or sale_l == "lost"
        or bool(lead.get("lost_reason", "").strip()))
    duplicate = not won and any(w in _letters(" ".join(remarks) + status) for w in DUPLICATE_WORDS)

    flag = lead.get("quotation_flag", "").strip().lower()
    quoted = bool(lead.get("quotation_date")) or flag in YES or bool(parse_money(lead.get("quotation_amount")))
    visit = parse_date(lead.get("visit_date"))
    visited = visit is not None and visit <= today
    visit_planned = visit is not None and visit > today

    if won:
        stage = "Won"
    elif lost:
        stage = "Lost"
    elif duplicate:
        stage = "Duplicate"
    elif visited or visit_planned:
        stage = "Visit"
    elif quoted:
        stage = "Quoted"
    elif later:
        stage = "Later"
    elif lead.get("last_call") or lead.get("notes"):
        stage = "Contacted"
    else:
        stage = "New"

    touches = [parse_date(lead.get(k)) for k in ("date", "first_contact", "last_call", "quotation_date", "visit_date")]
    touches = [d for d in touches if d and d <= today]
    last_touch = max(touches) if touches else None

    lead["stage"] = stage
    lead["last_touch"] = fmt_date(last_touch)
    lead["_last_touch"] = last_touch
    lead["_quoted"] = quoted or stage in ("Visit", "Won")
    lead["_visited"] = visited
    lead["_visit_planned"] = visit_planned
    lead["_sale_amount"] = parse_money(sale) if won else None
    lead["_next_followup"] = parse_date(lead.get("next_followup"))
    return lead


def load_leads(paths: list[str], today: date, source: str = "") -> list[dict]:
    leads = []
    for p in paths:
        with open(p, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        if not rows:
            continue
        # The header is not always row 1 (the workbook has title/help rows above it).
        header_idx = None
        for i, row in enumerate(rows[:15]):
            m = map_headers(row)
            if ("customer" in m or "phone" in m) and sum(1 for f in m if f) >= 3:
                header_idx = i
                break
        if header_idx is None:
            print(f"warning: {p}: no customer/phone column recognised; skipped", file=sys.stderr)
            continue
        mapping = map_headers(rows[header_idx])
        file_source = source or _norm_source(Path(p).name)
        for raw in rows[header_idx + 1:]:
            lead: dict = {k: "" for k in FIELDS}
            notes = []
            for field, val in zip(mapping, raw):
                val = (val or "").strip()
                if not field or not val:
                    continue
                if field == "notes":
                    notes.append(val)
                elif not lead[field]:
                    lead[field] = val
            lead["notes"] = " | ".join(notes)
            if not (lead["customer"] or lead["phone"] or lead["requirement"]):
                continue
            lead["source"] = _norm_source(lead["source"]) or lead["source"] or file_source or "Direct/Other"
            lead["salesperson"] = lead["salesperson"].title() or "Unassigned"
            lead["file"] = Path(p).name
            leads.append(classify(lead, today))
    return leads


def mask(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    return ("xxxxxx" + digits[-4:]) if len(digits) >= 4 else phone


def report(leads: list[dict], today: date, stale_days: int, show_phone: bool, limit: int) -> str:
    out = [f"# Lead pipeline: as of {fmt_date(today)}", f"Total leads: **{len(leads)}**", ""]

    by_person: "OrderedDict[str, list[dict]]" = OrderedDict()
    for lead in sorted(leads, key=lambda x: x["salesperson"]):
        by_person.setdefault(lead["salesperson"], []).append(lead)

    rows = []
    for person, ls in by_person.items():
        n = len(ls)
        quoted = sum(1 for x in ls if x["_quoted"])
        visits = sum(1 for x in ls if x["_visited"])
        won = [x for x in ls if x["stage"] == "Won"]
        lost = sum(1 for x in ls if x["stage"] == "Lost")
        sale_amt = sum(x["_sale_amount"] or 0 for x in won)
        conv = f"{(len(won) / n * 100):.1f}%" if n else "0%"
        rows.append([person, n, quoted, visits, len(won), lost, conv, inr(sale_amt) if sale_amt else ""])
    out += ["## By salesperson", md_table(
        ["Salesperson", "Leads", "Quoted", "Visits done", "Won", "Lost", "Conversion", "Sale value (where given)"], rows), ""]

    src: dict[str, int] = {}
    for lead in leads:
        src[lead["source"]] = src.get(lead["source"], 0) + 1
    out += ["## By source", md_table(["Source", "Leads"], sorted(src.items(), key=lambda kv: -kv[1])), ""]

    stages = ["New", "Contacted", "Quoted", "Visit", "Later", "Won", "Lost", "Duplicate"]
    out += ["## By stage", md_table(stages, [[sum(1 for x in leads if x["stage"] == s) for s in stages]]), ""]

    def ph(x):
        return x["phone"] if show_phone else mask(x["phone"])

    def who(x):
        return f"{x['lead_id']} {x['customer']}".strip()

    due = [x for x in leads if x["_next_followup"] and x["_next_followup"] <= today
           and x["stage"] not in ("Won", "Lost", "Duplicate")]
    due.sort(key=lambda x: (x["_next_followup"], x["salesperson"]))
    overdue_n = sum(1 for x in due if x["_next_followup"] < today)
    if any(x["next_followup"] for x in leads):
        out += [f"## Follow-ups due (next follow-up date today or earlier): {len(due)} ({overdue_n} overdue)", md_table(
            ["Salesperson", "Lead", "Phone", "Requirement", "Budget", "Stage", "Follow-up date"],
            [[x["salesperson"], who(x), ph(x), x["requirement"], x["budget"], x["stage"], x["next_followup"]] for x in due[:limit]]), ""]

    hot = [x for x in leads if x["stage"] in ("Quoted", "Visit")]
    # Planned visits first, then the most recently touched.
    hot.sort(key=lambda x: (not x["_visit_planned"], -(x["_last_touch"] or date.min).toordinal()))
    out += [f"## Hot leads (quoted or visit, not closed): {len(hot)}", md_table(
        ["Salesperson", "Customer", "Phone", "Location", "Requirement", "Stage", "Last touch", "Visit date"],
        [[x["salesperson"], x["customer"], ph(x), x["location"], x["requirement"], x["stage"], x["last_touch"], x["visit_date"]] for x in hot[:limit]]), ""]

    stale = []
    for x in leads:
        if x["stage"] in ("Won", "Lost", "Duplicate", "Later"):
            continue
        lt = x["_last_touch"]
        days = (today - lt).days if lt else None
        if days is None or days >= stale_days:
            stale.append((days if days is not None else 9999, x))
    stale.sort(key=lambda t: (not t[1]["_quoted"], -t[0]))
    out += [f"## Overdue follow-ups (no touch for {stale_days}+ days): {len(stale)}", md_table(
        ["Salesperson", "Customer", "Phone", "Requirement", "Stage", "Last touch", "Days idle"],
        [[x["salesperson"], x["customer"], ph(x), x["requirement"], x["stage"], x["last_touch"] or "unknown", d if d != 9999 else "?"] for d, x in stale[:limit]]), ""]
    later = [x for x in leads if x["stage"] == "Later"]
    out += [f"## Nurture (plan later): {len(later)}", md_table(
        ["Salesperson", "Customer", "Phone", "Location", "Requirement", "Latest remark", "Lead date"],
        [[x["salesperson"], x["customer"], ph(x), x["location"], x["requirement"], (x["notes"].split(" | ") or [""])[-1], x["date"]] for x in later[:limit]]), ""]

    # Data quality: invalid numbers and the same customer in several rows or sheets.
    invalid = [x for x in leads if x["phone"] and not norm_phone(x["phone"])]
    seen: dict[str, list[dict]] = {}
    for x in leads:
        k = norm_phone(x["phone"])
        if k:
            seen.setdefault(k, []).append(x)
    dups = {k: v for k, v in seen.items() if len(v) > 1}
    out += ["## Data quality",
            f"- Invalid phone numbers: **{len(invalid)}**" + (" (e.g. " + ", ".join(f"{x['salesperson']} row dated {x['date']}" for x in invalid[:3]) + ")" if invalid else ""),
            f"- Same number appearing more than once: **{len(dups)}**",
            f"- Leads without a customer name: **{sum(1 for x in leads if not x['customer'])}**", ""]
    if dups:
        out.append(md_table(["Phone", "Entries (salesperson · date · stage)"],
                            [[(k if show_phone else mask(k)), "; ".join(f"{x['salesperson']} · {x['date']} · {x['stage']}" for x in v)] for k, v in list(dups.items())[:limit]]))
        out.append("")
    if len(hot) > limit or len(stale) > limit:
        out.append(f"_Tables show the top {limit} rows; use --limit to see more._")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="CSV exports of lead sheet tabs")
    ap.add_argument("--today", help="DD/MM/YYYY (default: system date)")
    ap.add_argument("--source", default="", help="Force the lead source for all files (e.g. IndiaMART)")
    ap.add_argument("--stale-days", type=int, default=3)
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--show-phone", action="store_true", help="Show full phone numbers (default: masked)")
    ap.add_argument("--out", help="Write normalised leads CSV here (keep it in data/live/)")
    a = ap.parse_args(argv)

    today = today_or(a.today)
    leads = load_leads(a.files, today, a.source)
    if a.out:
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
            w.writeheader()
            w.writerows(leads)
    print(report(leads, today, a.stale_days, a.show_phone, a.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
