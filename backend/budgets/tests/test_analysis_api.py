from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from unittest.mock import patch

from budgets.models import AnalysisRun, BudgetLineItem, BudgetScenario
from budgets.services.ai_analysis import analyze_scenario


@override_settings(OPENAI_API_KEY="", GEMINI_API_KEY="")
class AnalyzeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.scenario = BudgetScenario.objects.create(
            name="Q2 Operating Budget", period="2026 Q2"
        )
        self.line_item = BudgetLineItem.objects.create(
            scenario=self.scenario,
            department="Marketing",
            category="Paid Ads",
            budget_amount="50000.00",
            actual_amount="65000.00",
            notes="Unplanned launch spend.",
        )

    def test_analyze_api_creates_analysis_run(self):
        response = self.client.post(
            f"/api/scenarios/{self.scenario.id}/analyze/",
            {"question": "What should we review first?"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(AnalysisRun.objects.count(), 1)
        result = response.data["result"]
        self.assertIn("summary", result)
        self.assertIn("findings", result)
        self.assertIn("recommendations", result)
        self.assertEqual(response.data["provider"], "deterministic-fallback")
        self.assertEqual(result["findings"][0]["line_item_id"], self.line_item.id)

    @patch("budgets.services.ai_analysis.generate_analysis", side_effect=Exception("boom"))
    @override_settings(LLM_PROVIDER="gemini", GEMINI_API_KEY="test-key")
    def test_env_provider_fallback_does_not_store_unsaved_provider_config(self, _mock_generate):
        run = analyze_scenario(self.scenario, "Fallback from env provider")

        self.assertEqual(run.provider, "deterministic-fallback")
        self.assertIsNone(run.provider_config)
