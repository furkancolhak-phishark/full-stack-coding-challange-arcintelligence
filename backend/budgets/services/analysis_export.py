from io import BytesIO

from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _get_follow_ups(run):
    if hasattr(run, "follow_ups") and hasattr(run.follow_ups, "all"):
        return list(run.follow_ups.all().order_by("-created_at"))
    return list(getattr(run, "follow_ups", []) or [])


def _get_follow_up_evidence(run, referenced_findings):
    findings = run.result.get("findings", []) or []
    line_items = {
        item["id"]: item for item in run.input_snapshot.get("line_items", []) or []
    }
    findings_by_id = {f.get("line_item_id"): f for f in findings}
    evidence_rows = []
    for item_id in referenced_findings or []:
        finding = findings_by_id.get(item_id)
        if not finding:
            continue
        item = line_items.get(item_id, {})
        evidence_rows.append(
            {
                "department": finding.get("department", ""),
                "category": finding.get("category", ""),
                "budget": item.get("budget_amount", ""),
                "actual": item.get("actual_amount", ""),
                "variance": item.get("variance", finding.get("variance", "")),
                "evidence": finding.get("evidence", ""),
            }
        )
    return evidence_rows


def build_markdown_export(run):
    scenario = run.scenario
    result = run.result
    findings = result.get("findings", [])
    recommendations = result.get("recommendations", [])

    lines = [
        f"# Budget Analysis Export: {scenario.name}",
        "",
        f"- Scenario: {scenario.name}",
        f"- Period: {scenario.period}",
        f"- Generated at: {run.created_at.isoformat()}",
        f"- Provider: {run.provider}",
        f"- Model: {run.model or 'deterministic-fallback'}",
        "",
        "## Summary",
        "",
        result.get("summary", ""),
        "",
        "## Totals",
        "",
        f"- Total budget: {result.get('total_budget', '')}",
        f"- Total actual: {result.get('total_actual', '')}",
        f"- Total variance: {result.get('total_variance', '')}",
        f"- Total variance percent: {result.get('total_variance_percent', 'n/a')}",
        f"- Health score: {result.get('health_score', '')}",
        "",
        "## Findings",
        "",
    ]

    if findings:
        for index, finding in enumerate(findings, start=1):
            lines.extend(
                [
                    f"### {index}. {finding['department']} / {finding['category']}",
                    "",
                    f"- Severity: {finding['severity']}",
                    f"- Risk type: {finding['risk_type']}",
                    f"- Variance: {finding['variance']}",
                    f"- Variance percent: {finding['variance_percent']}",
                    f"- Evidence: {finding['evidence']}",
                    f"- Recommendation: {finding['recommendation']}",
                    "",
                ]
            )
    else:
        lines.extend(["No findings.", ""])

    lines.extend(["## Recommendations", ""])
    if recommendations:
        lines.extend([f"{index}. {text}" for index, text in enumerate(recommendations, start=1)])
    else:
        lines.append("No recommendations.")

    lines.extend(["", "## Review Order", ""])
    review_order = result.get("review_order", [])
    if review_order:
        lines.extend([f"- Line item ID {item_id}" for item_id in review_order])
    else:
        lines.append("- None")

    lines.extend(["", "## Follow-up Questions", ""])
    follow_ups = _get_follow_ups(run)
    if follow_ups:
        for index, follow_up in enumerate(follow_ups, start=1):
            response = follow_up.response if isinstance(follow_up.response, dict) else {}
            question_text = follow_up.question or ""
            answer_text = response.get("answer", "")
            suggested_action = response.get("suggested_action", "")
            referenced_findings = response.get("referenced_findings", []) or []
            asked_at = (
                follow_up.created_at.isoformat() if follow_up.created_at else ""
            )

            lines.extend(
                [
                    f"### {index}. {question_text}",
                    "",
                    f"- Asked at: {asked_at}",
                    f"- Answer: {answer_text}",
                    f"- Suggested action: {suggested_action}",
                ]
            )
            if referenced_findings:
                lines.append(
                    f"- Referenced findings: {', '.join(str(fid) for fid in referenced_findings)}"
                )
            lines.append("")

            evidence_rows = _get_follow_up_evidence(run, referenced_findings)
            if evidence_rows:
                lines.append("Evidence used:")
                for row in evidence_rows:
                    lines.append(
                        f"- {row['department']} / {row['category']} "
                        f"— Budget: {row['budget']}, Actual: {row['actual']}, "
                        f"Variance: {row['variance']}"
                    )
                    if row["evidence"]:
                        lines.append(f"  {row['evidence']}")
                lines.append("")
    else:
        lines.append("No follow-up questions for this analysis.")
        lines.append("")

    return "\n".join(lines) + "\n"


def build_pdf_export(run):
    result = run.result
    findings = result.get("findings", [])
    recommendations = result.get("recommendations", [])
    scenario = run.scenario

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        spaceAfter=6,
    )
    heading = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        spaceAfter=8,
        textColor=colors.HexColor("#163b35"),
    )
    subheading = ParagraphStyle(
        "Subheading",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11,
        spaceAfter=4,
        textColor=colors.HexColor("#163b35"),
    )
    title = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#163b35"),
    )

    story = [
        Paragraph(f"Budget Analysis Export: {escape(scenario.name)}", title),
        Spacer(1, 4),
        Paragraph(
            f"Period: {escape(scenario.period)}<br/>Generated: {run.created_at.isoformat()}<br/>"
            f"Provider: {escape(run.provider)} / {escape(run.model or 'deterministic-fallback')}",
            body,
        ),
        Spacer(1, 6),
        Paragraph("Summary", heading),
        Paragraph(escape(result.get("summary", "")), body),
        Paragraph("Totals", heading),
    ]

    totals_header_style = ParagraphStyle(
        "TotalsHeader",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
    )
    totals_cell_style = ParagraphStyle(
        "TotalsCell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
    )
    totals_table = Table(
        [
            [
                Paragraph("Budget", totals_header_style),
                Paragraph("Actual", totals_header_style),
                Paragraph("Variance", totals_header_style),
                Paragraph("Variance %", totals_header_style),
                Paragraph("Health score", totals_header_style),
            ],
            [
                Paragraph(escape(str(result.get("total_budget", ""))), totals_cell_style),
                Paragraph(escape(str(result.get("total_actual", ""))), totals_cell_style),
                Paragraph(escape(str(result.get("total_variance", ""))), totals_cell_style),
                Paragraph(escape(str(result.get("total_variance_percent", "n/a"))), totals_cell_style),
                Paragraph(escape(str(result.get("health_score", ""))), totals_cell_style),
            ],
        ],
        colWidths=[32 * mm, 32 * mm, 32 * mm, 32 * mm, 28 * mm],
    )
    totals_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6f0ed")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#163b35")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c6d3cf")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([totals_table, Spacer(1, 10), Paragraph("Findings", heading)])

    if findings:
        cell_style = ParagraphStyle(
            "CellStyle",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
        )
        header_style = ParagraphStyle(
            "HeaderCellStyle",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
        )
        findings_table = Table(
            [
                [
                    Paragraph("Area", header_style),
                    Paragraph("Severity", header_style),
                    Paragraph("Variance", header_style),
                    Paragraph("Variance %", header_style),
                    Paragraph("Recommendation", header_style),
                ]
            ]
            + [
                [
                    Paragraph(escape(f"{finding['department']} / {finding['category']}"), cell_style),
                    Paragraph(escape(str(finding["severity"])), cell_style),
                    Paragraph(escape(str(finding["variance"])), cell_style),
                    Paragraph(escape(str(finding["variance_percent"])), cell_style),
                    Paragraph(escape(str(finding["recommendation"])), cell_style),
                ]
                for finding in findings
            ],
            colWidths=[34 * mm, 20 * mm, 24 * mm, 22 * mm, 72 * mm],
        )
        findings_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6f0ed")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#163b35")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c6d3cf")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.extend([findings_table, Spacer(1, 10)])
    else:
        story.extend([Paragraph("No findings.", body), Spacer(1, 6)])

    story.append(Paragraph("Recommendations", heading))
    if recommendations:
        for index, recommendation in enumerate(recommendations, start=1):
            story.append(Paragraph(f"{index}. {escape(recommendation)}", body))
    else:
        story.append(Paragraph("No recommendations.", body))

    story.append(Spacer(1, 6))
    story.append(Paragraph("Evidence", heading))
    for finding in findings:
        story.append(
            Paragraph(
                f"<b>{escape(finding['department'])} / {escape(finding['category'])}</b><br/>"
                f"{escape(finding['evidence'])}",
                body,
            )
        )

    story.append(Spacer(1, 10))
    story.append(Paragraph("Follow-up Questions", heading))
    follow_ups = _get_follow_ups(run)
    if follow_ups:
        for index, follow_up in enumerate(follow_ups, start=1):
            response = follow_up.response if isinstance(follow_up.response, dict) else {}
            question_text = follow_up.question or ""
            answer_text = response.get("answer", "")
            suggested_action = response.get("suggested_action", "")
            referenced_findings = response.get("referenced_findings", []) or []
            asked_at = (
                follow_up.created_at.isoformat() if follow_up.created_at else ""
            )

            story.append(
                Paragraph(
                    f"{index}. {escape(question_text)}",
                    subheading,
                )
            )
            story.append(Paragraph(f"Asked at: {escape(asked_at)}", body))
            story.append(Paragraph(f"Answer: {escape(answer_text)}", body))
            story.append(
                Paragraph(f"Suggested action: {escape(suggested_action)}", body)
            )
            if referenced_findings:
                story.append(
                    Paragraph(
                        f"Referenced findings: {escape(', '.join(str(fid) for fid in referenced_findings))}",
                        body,
                    )
                )

            evidence_rows = _get_follow_up_evidence(run, referenced_findings)
            if evidence_rows:
                story.append(Paragraph("<b>Evidence used:</b>", body))
                for row in evidence_rows:
                    story.append(
                        Paragraph(
                            f"{escape(row['department'])} / {escape(row['category'])} "
                            f"— Budget: {escape(str(row['budget']))}, "
                            f"Actual: {escape(str(row['actual']))}, "
                            f"Variance: {escape(str(row['variance']))}<br/>"
                            f"{escape(row['evidence'])}",
                            body,
                        )
                    )
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No follow-up questions for this analysis.", body))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def export_filename(run, extension):
    safe_name = "".join(
        character.lower() if character.isalnum() else "-"
        for character in run.scenario.name
    ).strip("-")
    return f"{safe_name or 'analysis'}-{run.id}.{extension}"
