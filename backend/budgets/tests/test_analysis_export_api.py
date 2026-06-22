from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from budgets.models import BudgetLineItem, BudgetScenario
from budgets.services.ai_analysis import analyze_scenario


@override_settings(OPENAI_API_KEY="", GEMINI_API_KEY="")
class AnalysisExportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.scenario = BudgetScenario.objects.create(
            name="Q2 Operating Budget", period="2026 Q2"
        )
        BudgetLineItem.objects.create(
            scenario=self.scenario,
            department="Marketing",
            category="Paid Ads",
            budget_amount="50000.00",
            actual_amount="65000.00",
            notes="Unplanned launch spend.",
        )
        self.run = analyze_scenario(self.scenario, "Export test")

    def test_markdown_export_returns_attachment(self):
        response = self.client.get(
            f"/api/analysis-runs/{self.run.id}/export/?file_format=md"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/markdown; charset=utf-8")
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertIn("Budget Analysis Export", response.content.decode("utf-8"))

    def test_pdf_export_returns_pdf(self):
        response = self.client.get(
            f"/api/analysis-runs/{self.run.id}/export/?file_format=pdf"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
