import json
import re

import httpx

from .ai_analysis import _active_provider_config
from .provider_clients import generate_analysis
from .secrets import decrypt_secret


FOLLOW_UP_SCHEMA = {
    "answer": "string",
    "referenced_findings": ["existing line_item_id values from the saved analysis"],
    "suggested_action": "string",
    "generated_by": "llm_follow_up or deterministic_follow_up",
}
SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1}


class FollowUpValidationError(ValueError):
    pass


def answer_follow_up(run, question):
    response = deterministic_follow_up(run, question)
    selected_config = run.provider_config or _active_provider_config()
    if selected_config:
        if getattr(selected_config, "pk", None):
            selected_config.api_key = decrypt_secret(selected_config.api_key_encrypted)
        try:
            llm_result = generate_analysis(
                selected_config,
                _follow_up_payload(run, question),
                FOLLOW_UP_SCHEMA,
            )
            llm_result["generated_by"] = "llm_follow_up"
            response = validate_follow_up_result(llm_result, run)
        except (
            FollowUpValidationError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
            httpx.HTTPError,
            Exception,
        ):
            response = deterministic_follow_up(run, question)
    return response


def validate_follow_up_result(result, run):
    if not isinstance(result, dict):
        raise FollowUpValidationError("Follow-up result must be an object.")

    required = {"answer", "referenced_findings", "suggested_action", "generated_by"}
    missing = required - result.keys()
    if missing:
        raise FollowUpValidationError(f"Missing follow-up keys: {sorted(missing)}")

    if not isinstance(result["answer"], str) or not result["answer"].strip():
        raise FollowUpValidationError("answer must be a non-empty string.")
    if not isinstance(result["suggested_action"], str) or not result["suggested_action"].strip():
        raise FollowUpValidationError("suggested_action must be a non-empty string.")
    if not isinstance(result["referenced_findings"], list):
        raise FollowUpValidationError("referenced_findings must be a list.")

    valid_ids = {finding["line_item_id"] for finding in run.result.get("findings", [])}
    for item_id in result["referenced_findings"]:
        if item_id not in valid_ids:
            raise FollowUpValidationError(
                "referenced_findings references an unknown saved finding."
            )

    return {
        "answer": result["answer"].strip(),
        "referenced_findings": result["referenced_findings"],
        "suggested_action": result["suggested_action"].strip(),
        "generated_by": result["generated_by"],
    }


def deterministic_follow_up(run, question):
    findings = run.result.get("findings", [])
    line_items = {
        item["id"]: item for item in run.input_snapshot.get("line_items", [])
    }

    if not findings:
        return {
            "answer": (
                "There are no saved findings in this analysis, so there is no specific "
                "risk area to explain yet."
            ),
            "referenced_findings": [],
            "suggested_action": "Run the analysis after adding or updating budget line items.",
            "generated_by": "deterministic_follow_up",
        }

    ranked = sorted(
        findings,
        key=lambda finding: _follow_up_score(
            question,
            finding,
            line_items.get(finding["line_item_id"], {}),
            run,
        ),
        reverse=True,
    )
    primary = ranked[0]
    item = line_items.get(primary["line_item_id"], {})
    variance_percent = primary["variance_percent"]
    variance_percent_text = (
        "no budget baseline"
        if variance_percent is None
        else f"{variance_percent:.2f}%"
    )

    answer = (
        f"{primary['department']} / {primary['category']} stands out because it is "
        f"{primary['severity']} severity with a variance of {primary['variance']} "
        f"({variance_percent_text}). {primary['evidence']}"
    )
    if item.get("notes"):
        answer += f" Notes on the line item also mention: {item['notes']}"

    return {
        "answer": answer,
        "referenced_findings": [primary["line_item_id"]],
        "suggested_action": primary["recommendation"],
        "generated_by": "deterministic_follow_up",
    }


def _follow_up_payload(run, question):
    return {
        "question": question,
        "saved_analysis": {
            "question": run.question,
            "provider": run.provider,
            "model": run.model,
            "result": run.result,
        },
        "line_items": run.input_snapshot.get("line_items", []),
        "schema": FOLLOW_UP_SCHEMA,
    }


def _follow_up_score(question, finding, item, run):
    normalized_question = _normalize(question)
    search_blob = " ".join(
        [
            finding["department"],
            finding["category"],
            finding["severity"],
            finding["risk_type"].replace("_", " "),
            finding["recommendation"],
            finding["evidence"],
            item.get("notes", ""),
            item.get("description", ""),
        ]
    )
    search_tokens = set(_tokens(search_blob))
    question_tokens = set(_tokens(normalized_question))

    score = len(question_tokens & search_tokens)
    if finding["department"].lower() in normalized_question:
        score += 4
    if finding["category"].lower() in normalized_question:
        score += 4
    if finding["severity"] in normalized_question:
        score += 1
    if finding["risk_type"].replace("_", " ") in normalized_question:
        score += 2

    review_order = run.result.get("review_order", [])
    if finding["line_item_id"] in review_order:
        score += max(0, 4 - review_order.index(finding["line_item_id"]))

    score += SEVERITY_RANK.get(finding["severity"], 0)
    return score


def _normalize(text):
    return (text or "").strip().lower()


def _tokens(text):
    return re.findall(r"[a-z0-9]+", (text or "").lower())
