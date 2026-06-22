from django.test import TestCase

from budgets.models import BudgetLineItem, BudgetScenario
from budgets.services.variance import build_analysis_input, deterministic_result


class VarianceEngineTests(TestCase):
    def setUp(self):
        self.scenario = BudgetScenario.objects.create(name="Variance Test", period="FY2026")

    def add_item(self, department, category, budget, actual, notes=""):
        return BudgetLineItem.objects.create(
            scenario=self.scenario,
            department=department,
            category=category,
            budget_amount=budget,
            actual_amount=actual,
            notes=notes,
        )

    def test_over_budget_line_item(self):
        item = self.add_item("Marketing", "Paid Ads", "50000.00", "65000.00")

        snapshot = build_analysis_input(self.scenario)
        row = next(line for line in snapshot["line_items"] if line["id"] == item.id)

        self.assertEqual(row["variance"], "15000.00")
        self.assertEqual(row["variance_percent"], 30.0)
        self.assertEqual(row["severity"], "high")
        self.assertEqual(row["risk_type"], "overspend")

    def test_under_budget_line_item(self):
        item = self.add_item("Engineering", "Tools", "30000.00", "28500.00")

        snapshot = build_analysis_input(self.scenario)
        row = next(line for line in snapshot["line_items"] if line["id"] == item.id)

        self.assertEqual(row["variance"], "-1500.00")
        self.assertEqual(row["variance_percent"], -5.0)
        self.assertEqual(row["status"], "under_budget")
        self.assertEqual(row["risk_type"], "underspend")

    def test_zero_budget_with_actual_spend(self):
        item = self.add_item("Operations", "Emergency", "0.00", "3000.00")

        snapshot = build_analysis_input(self.scenario)
        row = next(line for line in snapshot["line_items"] if line["id"] == item.id)

        self.assertIsNone(row["variance_percent"])
        self.assertEqual(row["severity"], "high")
        self.assertEqual(row["risk_type"], "zero_budget")

    def test_total_variance(self):
        self.add_item("Marketing", "Paid Ads", "50000.00", "65000.00")
        self.add_item("Engineering", "Tools", "30000.00", "28500.00")

        snapshot = build_analysis_input(self.scenario)

        self.assertEqual(snapshot["totals"]["total_budget"], "80000.00")
        self.assertEqual(snapshot["totals"]["total_actual"], "93500.00")
        self.assertEqual(snapshot["totals"]["total_variance"], "13500.00")
        self.assertEqual(snapshot["totals"]["total_variance_percent"], 16.88)

    def test_deterministic_fallback_analysis_structure(self):
        high_item = self.add_item(
            "Marketing",
            "Paid Ads",
            "50000.00",
            "65000.00",
            "Campaign spend increased after an unplanned launch.",
        )
        self.add_item("Engineering", "Tools", "30000.00", "28500.00")

        snapshot = build_analysis_input(self.scenario)
        result = deterministic_result(snapshot)

        self.assertIn("summary", result)
        self.assertIn("findings", result)
        self.assertIn("recommendations", result)
        self.assertEqual(result["generated_by"], "deterministic_fallback")
        self.assertEqual(result["findings"][0]["line_item_id"], high_item.id)
        self.assertEqual(result["findings"][0]["severity"], "high")
        valid_ids = {item["id"] for item in snapshot["line_items"]}
        self.assertTrue(set(result["review_order"]).issubset(valid_ids))
