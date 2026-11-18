"""Shared helpers for The Gym Wala tools: dates, money, CSV, tables.

Standard library only, so the tools run anywhere with python3.
"""
from __future__ import annotations

import csv
import re
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Sequence

_DATE_RE = re.compile(r"^\s*(\d{1,4})[/\-.](\d{1,2})[/\-.](\d{1,4})\s*$")
# "02-Nov-2026", "02-Nov-26 12:00 am", "2 Nov 2026"
_MON_RE = re.compile(r"^\s*(\d{1,2})[\s\-/.]+([A-Za-z]{3,9})[\s\-/.,]+(\d{2,4})\b")
_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def parse_date(value: str | None) -> date | None:
    """Parse Indian-style dates (day first). Returns None if blank or unparseable.

    Accepts DD/MM/YYYY, D/M/YY, DD-MM-YYYY, DD.MM.YYYY, YYYY-MM-DD and
    DD-Mon-YYYY / DD-Mon-YY (an optional time after it is ignored).
    """
    if value is None:
        return None
    m = _DATE_RE.match(str(value))
    if not m:
        mm = _MON_RE.match(str(value))
        if not mm or mm.group(2)[:3].lower() not in _MONTHS:
            return None
        year = int(mm.group(3)) + (2000 if len(mm.group(3)) == 2 else 0)
        try:
            return date(year, _MONTHS[mm.group(2)[:3].lower()], int(mm.group(1)))
        except ValueError:
            return None
    a, b, c = m.groups()
    try:
        if len(a) == 4:  # YYYY-MM-DD
            return date(int(a), int(b), int(c))
        year = int(c)
        if len(c) == 2:
            year += 2000
        return date(year, int(b), int(a))
    except ValueError:
        return None


def today_or(value: str | None) -> date:
    if value:
        d = parse_date(value)
        if d is None:
            raise SystemExit(f"Could not parse --today '{value}'. Use DD/MM/YYYY.")
        return d
    return datetime.now().date()


def parse_money(value: str | None) -> float | None:
    """'₹1,25,000' -> 125000.0; blank or non-numeric -> None."""
    if value is None:
        return None
    s = str(value).strip().lower()
    s = s.replace("₹", "").replace("rs.", "").replace("rs", "").replace("inr", "")
    s = s.replace(",", "").replace(" ", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def money(value: str | None, default: float = 0.0) -> float:
    v = parse_money(value)
    return default if v is None else v


def inr(amount: float, symbol: bool = True) -> str:
    """Format in the Indian numbering system: 1234567 -> ₹12,34,567."""
    neg = amount < 0
    n = int(round(abs(amount)))
    s = str(n)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        s = ",".join(groups) + "," + tail
    return ("-" if neg else "") + ("₹" if symbol else "") + s


def fmt_date(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else ""


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [
            {(k or "").strip(): (v or "").strip() for k, v in row.items()}
            for row in csv.DictReader(f)
        ]


def require_columns(rows: list[dict], columns: Iterable[str], path: str) -> None:
    if not rows:
        return
    missing = [c for c in columns if c not in rows[0]]
    if missing:
        raise SystemExit(f"{path}: missing column(s): {', '.join(missing)}")


def md_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    rows = [["" if c is None else str(c) for c in r] for r in rows]
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)
