from decimal import Decimal, InvalidOperation

VALID_SEVERITIES = {"low", "medium", "high"}
VALID_RISK_TYPES = {
    "overspend",
    "underspend",
    "zero_budget",
    "unusual_variance",
    "note_based_risk",
}
REQUIRED_RESULT_KEYS = {
    "summary",
    "health_score",
    "total_budget",
    "total_actual",
    "total_variance",
    "total_variance_percent",
    "findings",
    "recommendations",
    "review_order",
    "generated_by",
}
REQUIRED_FINDING_KEYS = {
    "line_item_id",
    "department",
    "category",
    "variance",
    "variance_percent",
    "severity",
    "risk_type",
    "recommendation",
    "evidence",
}


class AnalysisValidationError(ValueError):
    pass


def validate_analysis_result(result, snapshot):
    if not isinstance(result, dict):
        raise AnalysisValidationError("Analysis result must be an object.")
    missing = REQUIRED_RESULT_KEYS - result.keys()
    if missing:
        raise AnalysisValidationError(f"Missing analysis keys: {sorted(missing)}")

    valid_ids = {item["id"] for item in snapshot["line_items"]}
    if not isinstance(result["findings"], list):
        raise AnalysisValidationError("findings must be a list.")
    if not isinstance(result["recommendations"], list) or not all(
        isinstance(item, str) for item in result["recommendations"]
    ):
        raise AnalysisValidationError("recommendations must be a list of strings.")
    if not isinstance(result["review_order"], list):
        raise AnalysisValidationError("review_order must be a list.")

    for item_id in result["review_order"]:
        if item_id not in valid_ids:
            raise AnalysisValidationError("review_order references an unknown line item.")

    for finding in result["findings"]:
        _validate_finding(finding, valid_ids)

    health_score = result["health_score"]
    if not isinstance(health_score, int) or health_score < 0 or health_score > 100:
        raise AnalysisValidationError("health_score must be an integer from 0 to 100.")

    _validate_money_string(result["total_budget"], "total_budget")
    _validate_money_string(result["total_actual"], "total_actual")
    _validate_money_string(result["total_variance"], "total_variance")
    if result["total_variance_percent"] is not None and not isinstance(
        result["total_variance_percent"], (int, float)
    ):
        raise AnalysisValidationError("total_variance_percent must be numeric or null.")

    return _with_deterministic_totals(result, snapshot)


def _validate_finding(finding, valid_ids):
    if not isinstance(finding, dict):
        raise AnalysisValidationError("Each finding must be an object.")
    missing = REQUIRED_FINDING_KEYS - finding.keys()
    if missing:
        raise AnalysisValidationError(f"Missing finding keys: {sorted(missing)}")
    if finding["line_item_id"] not in valid_ids:
        raise AnalysisValidationError("finding references an unknown line item.")
    if finding["severity"] not in VALID_SEVERITIES:
        raise AnalysisValidationError("Invalid severity.")
    if finding["risk_type"] not in VALID_RISK_TYPES:
        raise AnalysisValidationError("Invalid risk type.")
    _validate_money_string(finding["variance"], "finding.variance")
    if finding["variance_percent"] is not None and not isinstance(
        finding["variance_percent"], (int, float)
    ):
        raise AnalysisValidationError("finding.variance_percent must be numeric or null.")


def _validate_money_string(value, name):
    if not isinstance(value, str):
        raise AnalysisValidationError(f"{name} must be a string.")
    try:
        Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise AnalysisValidationError(f"{name} must be a decimal string.") from exc


def _with_deterministic_totals(result, snapshot):
    clean = dict(result)
    clean.update(snapshot["totals"])
    return clean
