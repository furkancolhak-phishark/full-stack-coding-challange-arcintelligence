import { FileDown, FileText } from "lucide-react";

import { api } from "../api/client";
import { AnalysisRun, LineItem } from "../api/types";
import {
  formatMoney,
  formatPercent,
  formatSignedMoney,
  varianceClass
} from "../utils/money";
import { EvidenceDrawer } from "./EvidenceDrawer";
import { RiskCard } from "./RiskCard";
import { VarianceTable } from "./VarianceTable";

export function AnalysisPanel({
  analysis,
  lineItems
}: {
  analysis: AnalysisRun | null;
  lineItems: LineItem[];
}) {
  if (!analysis) {
    return (
      <section className="panel">
        <h2>Latest analysis</h2>
        <p className="emptyState">Run an analysis to see structured findings.</p>
      </section>
    );
  }

  const result = analysis.result;
  const visibleRisks = result.findings.filter((finding) =>
    ["high", "medium"].includes(finding.severity)
  );
  const analysisSource =
    analysis.provider === "deterministic-fallback" ? "Deterministic fallback" : "LLM";

  return (
    <section className="panel analysisPanel">
      <div className="sectionHeader">
        <div>
          <h2>Latest analysis</h2>
          <p className="muted">
            {analysisSource} · {analysis.provider} ·{" "}
            {new Date(analysis.created_at).toLocaleString()}
          </p>
        </div>
        <div className="analysisHeaderActions">
          <div className="buttonRow">
            <a
              className="iconTextButton"
              href={api.analysisExportUrl(analysis.id, "md")}
              download
            >
              <FileText size={16} />
              Markdown
            </a>
            <a
              className="iconTextButton"
              href={api.analysisExportUrl(analysis.id, "pdf")}
              download
            >
              <FileDown size={16} />
              PDF
            </a>
          </div>
          <span className="healthScore">{result.health_score}</span>
        </div>
      </div>

      <p className="summaryText">{result.summary}</p>

      <div className="metricGrid">
        <Metric label="Budget" value={formatMoney(result.total_budget)} />
        <Metric label="Actual" value={formatMoney(result.total_actual)} />
        <Metric
          label="Variance"
          value={formatSignedMoney(result.total_variance)}
          tone={varianceClass(result.total_variance)}
        />
        <Metric
          label="Variance %"
          value={formatPercent(result.total_variance_percent)}
          tone={varianceClass(result.total_variance)}
        />
      </div>

      <div className="riskGrid">
        {visibleRisks.map((finding, index) => (
          <RiskCard
            key={finding.line_item_id}
            finding={finding}
            isFirst={index === 0}
          />
        ))}
        {!visibleRisks.length && (
          <p className="emptyState">No high or medium risk findings.</p>
        )}
      </div>

      <div className="analysisSection">
        <h3>Variance review</h3>
        <VarianceTable findings={result.findings} />
      </div>

      <div className="analysisSection">
        <h3>Recommendations</h3>
        <ol className="recommendationList">
          {result.recommendations.map((recommendation) => (
            <li key={recommendation}>{recommendation}</li>
          ))}
        </ol>
      </div>

      <EvidenceDrawer findings={result.findings} lineItems={lineItems} />
    </section>
  );
}

function Metric({
  label,
  value,
  tone
}: {
  label: string;
  value: string;
  tone?: string;
}) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong className={tone}>{value}</strong>
    </div>
  );
}
