from django.conf import settings


def provider_defaults():
    return {
        "gemini": {
            "name": "Gemini",
            "default_model": settings.GEMINI_MODEL,
            "default_base_url": "",
            "requires_api_key": True,
        },
        "openai": {
            "name": "OpenAI",
            "default_model": settings.OPENAI_MODEL,
            "default_base_url": "https://api.openai.com/v1",
            "requires_api_key": True,
        },
        "anthropic": {
            "name": "Anthropic",
            "default_model": settings.ANTHROPIC_MODEL,
            "default_base_url": "https://api.anthropic.com",
            "requires_api_key": True,
        },
        "ollama": {
            "name": "Ollama",
            "default_model": settings.OLLAMA_MODEL,
            "default_base_url": settings.OLLAMA_BASE_URL,
            "requires_api_key": False,
        },
    }


def provider_choices():
    defaults = provider_defaults()
    return [
        {
            "provider": provider,
            "name": details["name"],
            "default_model": details["default_model"],
            "default_base_url": details["default_base_url"],
            "requires_api_key": details["requires_api_key"],
        }
        for provider, details in defaults.items()
    ]
