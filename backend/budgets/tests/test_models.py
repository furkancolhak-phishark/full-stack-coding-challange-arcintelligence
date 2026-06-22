from decimal import Decimal

from django.test import TestCase

from budgets.models import BudgetLineItem, BudgetScenario


class BudgetLineItemModelTests(TestCase):
    def test_line_item_computed_fields(self):
        scenario = BudgetScenario.objects.create(name="Test", period="2026 Q2")
        item = BudgetLineItem.objects.create(
            scenario=scenario,
            department="Marketing",
            category="Paid Ads",
            budget_amount="100.00",
            actual_amount="125.00",
        )

        self.assertEqual(item.variance, Decimal("25.00"))
        self.assertEqual(item.variance_percent, Decimal("25.00"))
        self.assertEqual(item.status, "over_budget")
