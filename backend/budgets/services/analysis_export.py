from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


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
    title = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#163b35"),
    )

    story = [
        Paragraph(f"Budget Analysis Export: {scenario.name}", title),
        Spacer(1, 4),
        Paragraph(
            f"Period: {scenario.period}<br/>Generated: {run.created_at.isoformat()}<br/>"
            f"Provider: {run.provider} / {run.model or 'deterministic-fallback'}",
            body,
        ),
        Spacer(1, 6),
        Paragraph("Summary", heading),
        Paragraph(result.get("summary", ""), body),
        Paragraph("Totals", heading),
    ]

    totals_table = Table(
        [
            ["Budget", "Actual", "Variance", "Variance %", "Health score"],
            [
                result.get("total_budget", ""),
                result.get("total_actual", ""),
                result.get("total_variance", ""),
                str(result.get("total_variance_percent", "n/a")),
                str(result.get("health_score", "")),
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
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([totals_table, Spacer(1, 10), Paragraph("Findings", heading)])

    if findings:
        findings_table = Table(
            [["Area", "Severity", "Variance", "Variance %", "Recommendation"]]
            + [
                [
                    f"{finding['department']} / {finding['category']}",
                    finding["severity"],
                    finding["variance"],
                    str(finding["variance_percent"]),
                    finding["recommendation"],
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
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
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
            story.append(Paragraph(f"{index}. {recommendation}", body))
    else:
        story.append(Paragraph("No recommendations.", body))

    story.append(Spacer(1, 6))
    story.append(Paragraph("Evidence", heading))
    for finding in findings:
        story.append(
            Paragraph(
                f"<b>{finding['department']} / {finding['category']}</b><br/>"
                f"{finding['evidence']}",
                body,
            )
        )

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def export_filename(run, extension):
    safe_name = "".join(
        character.lower() if character.isalnum() else "-"
        for character in run.scenario.name
    ).strip("-")
    return f"{safe_name or 'analysis'}-{run.id}.{extension}"
