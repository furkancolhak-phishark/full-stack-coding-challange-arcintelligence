from decimal import Decimal, ROUND_HALF_UP

NOTE_RISK_WORDS = ("urgent", "unplanned", "vendor", "renewal", "one-time", "unexpected")
SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1}


def money(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money_string(value):
    return str(money(value))


def percent(value):
    if value is None:
        return None
    return float(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_line_item(item):
    budget = money(item.budget_amount)
    actual = money(item.actual_amount)
    variance = actual - budget
    variance_percent = None if budget == 0 else (variance / budget) * Decimal("100")
    lower_notes = (item.notes or "").lower()
    note_risks = [word for word in NOTE_RISK_WORDS if word in lower_notes]

    return {
        "id": item.id,
        "department": item.department,
        "category": item.category,
        "description": item.description,
        "budget_amount": money_string(budget),
        "actual_amount": money_string(actual),
        "variance": money_string(variance),
        "variance_percent": percent(variance_percent),
        "status": _status(variance),
        "notes": item.notes,
        "note_risks": note_risks,
        "severity": _severity(budget, actual, variance, variance_percent),
        "risk_type": _risk_type(budget, actual, variance, note_risks),
    }


def build_analysis_input(scenario):
    items = [calculate_line_item(item) for item in scenario.line_items.all()]
    total_budget = sum((Decimal(item["budget_amount"]) for item in items), Decimal("0.00"))
    total_actual = sum((Decimal(item["actual_amount"]) for item in items), Decimal("0.00"))
    total_variance = total_actual - total_budget
    total_variance_percent = (
        None if total_budget == 0 else (total_variance / total_budget) * Decimal("100")
    )
    candidate_findings = [
        _candidate_from_item(item)
        for item in items
        if Decimal(item["variance"]) != 0 or item["note_risks"]
    ]
    candidate_findings.sort(key=_priority_key, reverse=True)

    return {
        "scenario": {
            "id": scenario.id,
            "name": scenario.name,
            "period": scenario.period,
            "description": scenario.description,
        },
        "totals": {
            "total_budget": money_string(total_budget),
            "total_actual": money_string(total_actual),
            "total_variance": money_string(total_variance),
            "total_variance_percent": percent(total_variance_percent),
        },
        "line_items": items,
        "candidate_findings": candidate_findings,
        "review_order": [finding["line_item_id"] for finding in candidate_findings],
    }


def deterministic_result(snapshot):
    totals = snapshot["totals"]
    findings = [_fallback_finding(finding) for finding in snapshot["candidate_findings"]]
    review_order = [finding["line_item_id"] for finding in findings]
    priority_names = [
        f"{finding['department']} / {finding['category']}" for finding in findings[:3]
    ]
    variance = Decimal(totals["total_variance"])
    direction = "over" if variance > 0 else "under" if variance < 0 else "on"

    if priority_names:
        summary = (
            f"This scenario is {money_string(abs(variance))} {direction} budget. "
            f"The highest-priority review areas are {', '.join(priority_names)}."
        )
    else:
        summary = "This scenario is on track with no material variance findings."

    return {
        "summary": summary,
        "health_score": _health_score(snapshot),
        **totals,
        "findings": findings,
        "recommendations": _fallback_recommendations(findings),
        "review_order": review_order,
        "generated_by": "deterministic_fallback",
    }


def _status(variance):
    if variance > 0:
        return "over_budget"
    if variance < 0:
        return "under_budget"
    return "on_track"


def _severity(budget, actual, variance, variance_percent):
    if budget == 0 and actual > 0:
        return "high"
    if variance > 0 and (variance >= Decimal("10000") or (variance_percent or 0) >= 25):
        return "high"
    if variance > 0 and (variance >= Decimal("5000") or (variance_percent or 0) >= 10):
        return "medium"
    if variance != 0:
        return "low"
    return "low"


def _risk_type(budget, actual, variance, note_risks):
    if budget == 0 and actual > 0:
        return "zero_budget"
    if variance > 0:
        return "overspend"
    if variance < 0:
        return "underspend"
    if note_risks:
        return "note_based_risk"
    return "unusual_variance"


def _candidate_from_item(item):
    return {
        "line_item_id": item["id"],
        "department": item["department"],
        "category": item["category"],
        "budget_amount": item["budget_amount"],
        "actual_amount": item["actual_amount"],
        "variance": item["variance"],
        "variance_percent": item["variance_percent"],
        "severity": item["severity"],
        "risk_type": item["risk_type"],
        "notes": item["notes"],
        "note_risks": item["note_risks"],
        "evidence": _evidence(item),
    }


def _priority_key(finding):
    variance = Decimal(finding["variance"])
    overspend_bias = 1 if variance > 0 else 0
    return (
        SEVERITY_RANK[finding["severity"]],
        overspend_bias,
        abs(variance),
        abs(Decimal(str(finding["variance_percent"] or 0))),
    )


def _fallback_finding(candidate):
    return {
        "line_item_id": candidate["line_item_id"],
        "department": candidate["department"],
        "category": candidate["category"],
        "variance": candidate["variance"],
        "variance_percent": candidate["variance_percent"],
        "severity": candidate["severity"],
        "risk_type": candidate["risk_type"],
        "recommendation": _recommendation(candidate),
        "evidence": candidate["evidence"],
    }


def _evidence(item):
    if item["variance_percent"] is None:
        return (
            f"Actual spend is {item['actual_amount']} against a zero budget, "
            f"creating a {item['variance']} variance."
        )
    return (
        f"Actual spend is {item['actual_amount']} against a {item['budget_amount']} "
        f"budget, creating a {item['variance']} variance "
        f"({item['variance_percent']}%)."
    )


def _recommendation(candidate):
    risk_type = candidate["risk_type"]
    if risk_type == "zero_budget":
        return "Confirm whether this unbudgeted spend should be approved or reforecast."
    if risk_type == "overspend":
        if candidate["note_risks"]:
            return "Review the noted spend driver and decide whether it is temporary or recurring."
        return "Review the drivers of this overspend before approving additional spend."
    if risk_type == "underspend":
        return "Confirm whether this underspend reflects timing, savings, or delayed work."
    return "Review the notes and supporting context for this line item."


def _fallback_recommendations(findings):
    if not findings:
        return ["Continue monitoring actuals against budget as new spend is recorded."]

    recommendations = ["Start with the highest absolute overspend items."]
    if any(finding["severity"] == "medium" for finding in findings):
        recommendations.append(
            "Check whether medium-severity variances are temporary or recurring."
        )
    if any(finding["risk_type"] in {"note_based_risk", "overspend"} for finding in findings):
        recommendations.append("Use notes to identify unplanned or urgent spend drivers.")
    return recommendations


def _health_score(snapshot):
    total_budget = Decimal(snapshot["totals"]["total_budget"])
    total_variance = Decimal(snapshot["totals"]["total_variance"])
    overspend_percent = (
        Decimal("0") if total_budget == 0 else max(total_variance, Decimal("0")) / total_budget * 100
    )
    high_count = sum(1 for finding in snapshot["candidate_findings"] if finding["severity"] == "high")
    medium_count = sum(
        1 for finding in snapshot["candidate_findings"] if finding["severity"] == "medium"
    )
    score = Decimal("100") - (overspend_percent * Decimal("1.1")) - (high_count * 7) - (
        medium_count * 4
    )
    return max(0, min(100, int(score.quantize(Decimal("1"), rounding=ROUND_HALF_UP))))
