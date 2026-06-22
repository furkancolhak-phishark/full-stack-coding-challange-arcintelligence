from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from budgets.models import BudgetLineItem, BudgetScenario
from budgets.services.ai_analysis import analyze_scenario


@override_settings(OPENAI_API_KEY="", GEMINI_API_KEY="")
class FollowUpApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.scenario = BudgetScenario.objects.create(
            name="Q2 Operating Budget", period="2026 Q2"
        )
        self.marketing = BudgetLineItem.objects.create(
            scenario=self.scenario,
            department="Marketing",
            category="Paid Ads",
            budget_amount="50000.00",
            actual_amount="65000.00",
            notes="Unplanned launch spend.",
        )
        BudgetLineItem.objects.create(
            scenario=self.scenario,
            department="Engineering",
            category="Tools",
            budget_amount="30000.00",
            actual_amount="28500.00",
            notes="Annual contract came in lower.",
        )
        self.run = analyze_scenario(self.scenario, "Which line items should we review first?")

    def test_follow_up_returns_structured_answer(self):
        response = self.client.post(
            f"/api/analysis-runs/{self.run.id}/follow-up/",
            {"question": "Why is Marketing high risk?"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("answer", response.data)
        self.assertIn("referenced_findings", response.data)
        self.assertIn("suggested_action", response.data)
        self.assertEqual(response.data["referenced_findings"], [self.marketing.id])
