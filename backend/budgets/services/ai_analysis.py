import json

import httpx
from django.conf import settings

from budgets.models import AnalysisRun, LLMProviderConfig

from .provider_clients import generate_analysis
from .schemas import AnalysisValidationError, validate_analysis_result
from .secrets import decrypt_secret
from .variance import build_analysis_input, deterministic_result


SCHEMA_HINT = {
    "summary": "string",
    "health_score": "integer 0-100",
    "total_budget": "decimal string",
    "total_actual": "decimal string",
    "total_variance": "decimal string",
    "total_variance_percent": "number or null",
    "findings": [
        {
            "line_item_id": "existing id only",
            "department": "string",
            "category": "string",
            "variance": "decimal string",
            "variance_percent": "number or null",
            "severity": "low | medium | high",
            "risk_type": "overspend | underspend | zero_budget | unusual_variance | note_based_risk",
            "recommendation": "string",
            "evidence": "string",
        }
    ],
    "recommendations": ["string"],
    "review_order": ["existing line_item_id values"],
    "generated_by": "llm_with_deterministic_metrics",
}


def analyze_scenario(scenario, question=None, provider_config=None):
    selected_question = question or AnalysisRun.DEFAULT_QUESTION
    scenario = scenario.__class__.objects.prefetch_related("line_items").get(pk=scenario.pk)
    snapshot = build_analysis_input(scenario)

    provider = "deterministic-fallback"
    model = ""
    result = deterministic_result(snapshot)
    selected_config = provider_config or _active_provider_config()
    if selected_config:
        if getattr(selected_config, "pk", None):
            selected_config.api_key = decrypt_secret(selected_config.api_key_encrypted)
        try:
            model = selected_config.selected_model
            llm_result = generate_analysis(
                selected_config,
                _analysis_payload(snapshot, selected_question),
                SCHEMA_HINT,
            )
            provider = selected_config.provider
            llm_result["generated_by"] = "llm_with_deterministic_metrics"
            result = validate_analysis_result(llm_result, snapshot)
        except (
            AnalysisValidationError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
            httpx.HTTPError,
            Exception,
        ):
            result = deterministic_result(snapshot)
            provider = "deterministic-fallback"
            model = ""
            selected_config = None

    stored_provider_config = selected_config if getattr(selected_config, "pk", None) else None

    return AnalysisRun.objects.create(
        scenario=scenario,
        provider_config=stored_provider_config,
        question=selected_question,
        provider=provider,
        model=model,
        input_snapshot=snapshot,
        result=result,
    )


def _active_provider_config():
    active_config = LLMProviderConfig.objects.filter(is_active=True).first()
    if active_config and active_config.selected_model and (
        active_config.api_key or active_config.provider == "ollama"
    ):
        return active_config

    env_provider = _env_provider_config()
    if env_provider and env_provider.selected_model and (
        env_provider.api_key or env_provider.provider == "ollama"
    ):
        return env_provider
    return None


def _analysis_payload(snapshot, question):
    return {
        "question": question,
        "scenario": snapshot["scenario"],
        "totals": snapshot["totals"],
        "line_items": snapshot["line_items"],
        "candidate_findings": snapshot["candidate_findings"],
        "schema": SCHEMA_HINT,
    }

def _env_provider_config():
    provider_name = _preferred_provider_name()
    if not provider_name:
        return None
    config = LLMProviderConfig(
        name=f"Environment {provider_name}",
        provider=provider_name,
        selected_model=_env_model(provider_name),
        base_url=_env_base_url(provider_name),
    )
    config.api_key_encrypted = ""
    config.api_key = _env_api_key(provider_name)
    return config


def _preferred_provider_name():
    if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        return "gemini"
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        return "openai"
    if settings.LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
        return "anthropic"
    if settings.LLM_PROVIDER == "ollama":
        return "ollama"
    if settings.GEMINI_API_KEY:
        return "gemini"
    if settings.OPENAI_API_KEY:
        return "openai"
    if settings.ANTHROPIC_API_KEY:
        return "anthropic"
    if settings.OLLAMA_MODEL:
        return "ollama"
    return None


def _env_api_key(provider_name):
    if provider_name == "gemini":
        return settings.GEMINI_API_KEY
    if provider_name == "openai":
        return settings.OPENAI_API_KEY
    if provider_name == "anthropic":
        return settings.ANTHROPIC_API_KEY
    return ""


def _env_model(provider_name):
    if provider_name == "gemini":
        return settings.GEMINI_MODEL
    if provider_name == "openai":
        return settings.OPENAI_MODEL
    if provider_name == "anthropic":
        return settings.ANTHROPIC_MODEL
    return settings.OLLAMA_MODEL


def _env_base_url(provider_name):
    if provider_name == "anthropic":
        return "https://api.anthropic.com"
    if provider_name == "openai":
        return "https://api.openai.com/v1"
    if provider_name == "ollama":
        return settings.OLLAMA_BASE_URL
    return ""
