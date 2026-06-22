from django.test import TestCase
from rest_framework.test import APIClient

from budgets.models import LLMProviderConfig


class ProviderConfigApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_provider_config_encrypts_api_key(self):
        response = self.client.post(
            "/api/provider-configs/",
            {
                "name": "Gemini Primary",
                "provider": "gemini",
                "api_key": "secret-key-value",
                "selected_model": "gemini-3.1-flash-lite",
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        config = LLMProviderConfig.objects.get()
        self.assertNotEqual(config.api_key_encrypted, "secret-key-value")
        self.assertTrue(response.data["has_api_key"])
        self.assertEqual(response.data["masked_api_key"][:4], "secr")

    def test_set_active_provider_deactivates_others(self):
        first = LLMProviderConfig.objects.create(
            name="Gemini",
            provider="gemini",
            selected_model="gemini-3.1-flash-lite",
            is_active=True,
        )
        second = LLMProviderConfig.objects.create(
            name="OpenAI",
            provider="openai",
            selected_model="gpt-4o-mini",
            is_active=False,
        )

        response = self.client.post(
            f"/api/provider-configs/{second.id}/set-active/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.is_active)
        self.assertTrue(second.is_active)
