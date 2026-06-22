import json

import httpx
from django.conf import settings


SYSTEM_INSTRUCTION = (
    "You are a finance budget review assistant. Analyze only the provided "
    "budget scenario data. Return valid JSON matching the requested schema. "
    "Do not include Markdown. Do not invent departments, categories, or "
    "line item ids. Recommendations must be specific and based on the "
    "provided variance evidence."
)


def list_models(config):
    provider = config.provider
    if provider == "openai":
        data = _openai_request(config, "GET", "/models").json()["data"]
        return sorted(
            [
                {"id": item["id"], "label": item["id"], "metadata": item}
                for item in data
            ],
            key=lambda item: item["id"],
        )
    if provider == "gemini":
        response = httpx.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            headers={"x-goog-api-key": config.api_key},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json().get("models", [])
        models = []
        for item in data:
            model_id = item["name"].replace("models/", "")
            models.append(
                {
                    "id": model_id,
                    "label": item.get("displayName") or model_id,
                    "metadata": item,
                }
            )
        return sorted(models, key=lambda item: item["id"])
    if provider == "anthropic":
        response = httpx.get(
            _join_url(config.base_url or "https://api.anthropic.com", "/v1/models"),
            headers={
                "x-api-key": config.api_key,
                "anthropic-version": "2023-06-01",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json().get("data", [])
        return sorted(
            [
                {
                    "id": item["id"],
                    "label": item.get("display_name") or item["id"],
                    "metadata": item,
                }
                for item in data
            ],
            key=lambda item: item["id"],
        )
    if provider == "ollama":
        response = httpx.get(_join_url(config.base_url, "/api/tags"), timeout=30.0)
        response.raise_for_status()
        data = response.json().get("models", [])
        return sorted(
            [
                {
                    "id": item["name"],
                    "label": item["name"],
                    "metadata": item,
                }
                for item in data
            ],
            key=lambda item: item["id"],
        )
    raise ValueError(f"Unsupported provider: {provider}")


def generate_analysis(config, payload, schema_hint):
    provider = config.provider
    if provider == "openai":
        return _generate_openai(config, payload)
    if provider == "gemini":
        return _generate_gemini(config, payload)
    if provider == "anthropic":
        return _generate_anthropic(config, payload)
    if provider == "ollama":
        return _generate_ollama(config, payload, schema_hint)
    raise ValueError(f"Unsupported provider: {provider}")


def _generate_openai(config, payload):
    from openai import OpenAI

    client = OpenAI(
        api_key=config.api_key,
        base_url=(config.base_url or "https://api.openai.com/v1").rstrip("/"),
    )
    response = client.chat.completions.create(
        model=config.selected_model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": json.dumps(payload)},
        ],
    )
    return json.loads(response.choices[0].message.content)


def _generate_gemini(config, payload):
    response = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{config.selected_model}:generateContent",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": config.api_key,
        },
        json={
            "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "contents": [{"parts": [{"text": json.dumps(payload)}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        },
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()
    return json.loads(data["candidates"][0]["content"]["parts"][0]["text"])


def _generate_anthropic(config, payload):
    response = httpx.post(
        _join_url(config.base_url or "https://api.anthropic.com", "/v1/messages"),
        headers={
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": config.selected_model,
            "max_tokens": 2000,
            "temperature": 0.2,
            "system": SYSTEM_INSTRUCTION,
            "messages": [
                {
                    "role": "user",
                    "content": json.dumps(payload),
                }
            ],
        },
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()
    content_blocks = data.get("content", [])
    text = "".join(
        block.get("text", "") for block in content_blocks if block.get("type") == "text"
    )
    return json.loads(text)


def _generate_ollama(config, payload, schema_hint):
    response = httpx.post(
        _join_url(config.base_url, "/api/chat"),
        json={
            "model": config.selected_model,
            "messages": [
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {
                    "role": "user",
                    "content": (
                        f"Return JSON matching this schema hint: {json.dumps(schema_hint)}\n"
                        f"Payload: {json.dumps(payload)}"
                    ),
                },
            ],
            "format": "json",
            "stream": False,
        },
        timeout=60.0,
    )
    response.raise_for_status()
    data = response.json()
    return json.loads(data["message"]["content"])


def _openai_request(config, method, path):
    with httpx.Client(
        base_url=(config.base_url or "https://api.openai.com/v1").rstrip("/"),
        headers={"Authorization": f"Bearer {config.api_key}"},
        timeout=30.0,
    ) as client:
        response = client.request(method, path)
        response.raise_for_status()
        return response


def _join_url(base_url, path):
    return f"{(base_url or '').rstrip('/')}{path}"
