import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import bom_costing  # noqa: E402
import incentives  # noqa: E402
import leads_report  # noqa: E402
import payables_plan  # noqa: E402
import receivables_ageing  # noqa: E402
import salary_ot  # noqa: E402
import stock_reorder  # noqa: E402
from tgw_common import inr, parse_date, parse_money  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"
TODAY = date(2026, 11, 18)


class CommonTests(unittest.TestCase):
    def test_parse_date_day_first(self):
        self.assertEqual(parse_date("01/02/2026"), date(2026, 2, 1))
        self.assertEqual(parse_date("1-2-26"), date(2026, 2, 1))
        self.assertEqual(parse_date("2026-02-01"), date(2026, 2, 1))
        self.assertEqual(parse_date("02-Nov-2026"), date(2026, 11, 2))
        self.assertEqual(parse_date("02-Nov-26 12:00 am"), date(2026, 11, 2))
        self.assertIsNone(parse_date("call back"))
        self.assertIsNone(parse_date(""))

    def test_money_and_inr(self):
        self.assertEqual(parse_money("₹1,25,000"), 125000)
        self.assertEqual(parse_money("Rs. 500"), 500)
        self.assertIsNone(parse_money("yes"))
        self.assertEqual(inr(1234567), "₹12,34,567")
        self.assertEqual(inr(999), "₹999")
        self.assertEqual(inr(-100000), "-₹1,00,000")


class LeadsTests(unittest.TestCase):
    def setUp(self):
        files = sorted(str(p) for p in FIX.glob("leads_*.csv"))
        self.leads = leads_report.load_leads(files, TODAY)
        self.by_customer = {x["customer"]: x for x in self.leads}

    def test_all_layouts_loaded_and_blank_rows_skipped(self):
        self.assertEqual(len(self.leads), 11)

    def test_stages(self):
        s = {k: v["stage"] for k, v in self.by_customer.items()}
        self.assertEqual(s["Beta Home"], "Won")
        self.assertEqual(s["Gamma Club"], "Visit")
        self.assertEqual(s["Delta"], "Lost")
        self.assertEqual(s["Epsilon Fitness"], "Quoted")
        self.assertEqual(s["Zeta"], "New")
        self.assertEqual(s["Eta Gym"], "Won")
        self.assertEqual(s["Alpha Gym"], "Contacted")
        self.assertEqual(s["Theta"], "Later")        # latest remark "PLAN IN JULY"
        self.assertEqual(s["Kappa"], "Later")        # "NO REQUIRMENT YET" is not lost
        self.assertEqual(s["Iota"], "Duplicate")     # "ALREADY WITH ..."
        nameless = [x for x in self.leads if not x["customer"]][0]
        self.assertEqual(nameless["stage"], "Lost")  # misspelt "NOT INTRESTED"

    def test_data_quality(self):
        self.assertEqual(leads_report.norm_phone("+91 90000 00001"), "9000000001")
        self.assertEqual(leads_report.norm_phone("90000000099"), "")
        out = leads_report.report(self.leads, TODAY, 3, show_phone=False, limit=25)
        self.assertIn("Invalid phone numbers: **1**", out)
        self.assertIn("Same number appearing more than once: **1**", out)

    def test_source_from_filename_and_name_titlecase(self):
        self.assertEqual(self.by_customer["Alpha Gym"]["source"], "IndiaMART")
        self.assertEqual(self.by_customer["Zeta"]["source"], "Direct/Other")
        self.assertEqual(self.by_customer["Zeta"]["salesperson"], "Test Seller Two")

    def test_sale_amount_and_last_touch(self):
        self.assertEqual(self.by_customer["Eta Gym"]["_sale_amount"], 185000)
        self.assertEqual(self.by_customer["Epsilon Fitness"]["last_touch"], "16/11/2026")

    def test_report_masks_phone(self):
        out = leads_report.report(self.leads, TODAY, 3, show_phone=False, limit=25)
        self.assertNotIn("9000000003", out)
        self.assertIn("xxxxxx0003", out)
        self.assertIn("Overdue follow-ups", out)


class WorkbookLeadsTests(unittest.TestCase):
    """TGW Sales Master Workbook layout: help rows above the header on row 6."""

    def setUp(self):
        self.leads = leads_report.load_leads([str(FIX / "workbook" / "person_page.csv")], TODAY)
        self.by_id = {x["lead_id"]: x for x in self.leads}

    def test_header_found_below_title_rows(self):
        self.assertEqual(sorted(self.by_id), ["L-01", "L-02", "L-03", "L-04", "L-05"])
        self.assertEqual(self.by_id["L-01"]["salesperson"], "Seller X")
        self.assertEqual(self.by_id["L-01"]["source"], "Meta lead form")
        self.assertEqual(self.by_id["L-01"]["page"], "The Gym Wala")
        self.assertEqual(self.by_id["L-01"]["budget"], "10L - 20L")

    def test_workbook_stages(self):
        s = {k: v["stage"] for k, v in self.by_id.items()}
        self.assertEqual(s, {"L-01": "Contacted", "L-02": "Quoted", "L-03": "Won", "L-04": "Lost", "L-05": "New"})

    def test_followups_due_and_overdue(self):
        out = leads_report.report(self.leads, TODAY, 3, show_phone=False, limit=25)
        self.assertIn("Follow-ups due (next follow-up date today or earlier): 2 (1 overdue)", out)
        self.assertIn("L-01 Wb Alpha", out)
        self.assertNotIn("9100000001", out)


class FinanceTests(unittest.TestCase):
    def test_payables_priority_and_budget(self):
        rows = [
            {"vendor": "Supplier C", "due_date": "15/11/2026", "amount": "30000", "priority": "C", "category": "supplier"},
            {"vendor": "Supplier A", "due_date": "17/11/2026", "amount": "50000", "priority": "A", "category": "supplier"},
            {"vendor": "GST", "due_date": "20/11/2026", "amount": "40000", "priority": "A", "category": "statutory"},
            {"vendor": "Paid", "due_date": "10/11/2026", "amount": "10000", "paid": "10000"},
            {"vendor": "Later", "due_date": "30/12/2026", "amount": "5000"},
        ]
        pay, hold, later, remaining = payables_plan.plan(rows, cash=100000, min_balance=10000, today=TODAY, horizon=7)
        self.assertEqual([b["vendor"] for b in pay], ["GST", "Supplier A"])
        self.assertEqual([b["vendor"] for b in hold], ["Supplier C"])
        self.assertEqual([b["vendor"] for b in later], ["Later"])
        self.assertEqual(remaining, 10000)

    def test_receivables_buckets(self):
        rows = [
            {"customer": "X", "due_date": "01/11/2026", "amount": "1000", "received": "0"},
            {"customer": "Y", "due_date": "01/08/2026", "amount": "1000", "received": "0"},
            {"customer": "Z", "due_date": "01/12/2026", "amount": "1000", "received": "0"},
            {"customer": "Paid", "due_date": "01/08/2026", "amount": "1000", "received": "1000"},
        ]
        items = {i["customer"]: i["bucket"] for i in receivables_ageing.ageing(rows, TODAY)}
        self.assertEqual(items, {"X": "0-30", "Y": "90+", "Z": "Not due"})

    def test_incentive_slabs(self):
        slabs = incentives.load_slabs([
            {"min_achievement_pct": "0", "max_achievement_pct": "80", "incentive_pct_of_sales": "0", "fixed_bonus": ""},
            {"min_achievement_pct": "80", "max_achievement_pct": "100", "incentive_pct_of_sales": "1", "fixed_bonus": ""},
            {"min_achievement_pct": "100", "max_achievement_pct": "", "incentive_pct_of_sales": "2", "fixed_bonus": "1000"},
        ])
        res = incentives.calculate([
            {"salesperson": "A", "target_amount": "100000", "achieved_amount": "79000"},
            {"salesperson": "B", "target_amount": "100000", "achieved_amount": "90000"},
            {"salesperson": "C", "target_amount": "100000", "achieved_amount": "150000"},
        ], slabs)
        self.assertEqual([r["incentive"] for r in res], [0, 900, 4000])


class OpsHrProductTests(unittest.TestCase):
    def test_stock_reorder(self):
        rows = [
            {"item": "Low", "on_hand": "2", "reorder_point": "5", "avg_monthly_sales": "6", "lead_time_days": "30", "unit_cost": "100"},
            {"item": "Fixed", "on_hand": "1", "reorder_point": "1", "reorder_qty": "10", "unit_cost": "50"},
            {"item": "OK", "on_hand": "20", "reorder_point": "5", "avg_monthly_sales": "3"},
            {"item": "Dead", "on_hand": "7", "reorder_point": "1", "avg_monthly_sales": "0", "unit_cost": "10"},
        ]
        reorder, dead = stock_reorder.analyse(rows)
        qty = {r["item"]: r["qty"] for r in reorder}
        self.assertEqual(qty, {"Low": 10, "Fixed": 10})
        self.assertEqual([d["item"] for d in dead], ["Dead"])

    def test_salary(self):
        r = {"employee": "E", "monthly_salary": "30000", "present_days": "25", "paid_leave_days": "1",
             "ot_hours": "8", "late_count": "6", "advance_deduction": "2000"}
        x = salary_ot.compute(r, days_in_month=30, lates_per_half_day=3)
        # per day 1000; gross 26000; OT 8h*125=1000; late 1 day=1000; advance 2000
        self.assertEqual((x["gross"], x["ot"], x["deductions"], x["net"]), (26000, 1000, 3000, 24000))

    def test_bom(self):
        rows = [{"part": "a", "qty": "2", "unit_cost": "100", "category": "material"},
                {"part": "b", "qty": "1", "unit_cost": "300", "category": "labour"}]
        _, direct, overhead, unit, by_cat = bom_costing.cost(rows, overhead_pct=10)
        self.assertEqual((direct, overhead, unit), (500, 50, 550))
        self.assertEqual(by_cat, {"material": 200, "labour": 300})


if __name__ == "__main__":
    unittest.main()
