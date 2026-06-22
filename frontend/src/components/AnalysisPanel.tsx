import { FileDown, FileText, MessageSquareMore } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { AnalysisFollowUp, AnalysisRun, LineItem } from "../api/types";
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
  lineItems,
  onFollowUpCreated
}: {
  analysis: AnalysisRun | null;
  lineItems: LineItem[];
  onFollowUpCreated?: (analysisId: number, entry: AnalysisFollowUp) => void;
}) {
  const [followUpQuestion, setFollowUpQuestion] = useState("");
  const [followUpEntries, setFollowUpEntries] = useState<AnalysisFollowUp[]>([]);
  const [followUpLoading, setFollowUpLoading] = useState(false);
  const [followUpError, setFollowUpError] = useState<string | null>(null);

  useEffect(() => {
    setFollowUpQuestion("");
    setFollowUpEntries(analysis?.follow_ups || []);
    setFollowUpError(null);
  }, [analysis?.id]);

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
  const findingsById = new Map(
    result.findings.map((finding) => [finding.line_item_id, finding])
  );
  const lineItemsById = new Map(lineItems.map((item) => [item.id, item]));

  async function handleFollowUp() {
    if (!analysis || !followUpQuestion.trim()) return;
    setFollowUpLoading(true);
    setFollowUpError(null);
    try {
      const nextEntry = await api.followUpAnalysis(analysis.id, followUpQuestion.trim());
      setFollowUpEntries((current) => [nextEntry, ...current]);
      onFollowUpCreated?.(analysis.id, nextEntry);
      setFollowUpQuestion("");
    } catch (error) {
      setFollowUpError(
        error instanceof Error ? error.message : "Failed to ask follow-up."
      );
    } finally {
      setFollowUpLoading(false);
    }
  }

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

      <div className="analysisSection followUpPanel">
        <h3>Follow-up</h3>
        <label className="analysisQuestionField">
          <span>Ask a follow-up about this analysis</span>
          <textarea
            rows={3}
            value={followUpQuestion}
            onChange={(event) => setFollowUpQuestion(event.target.value)}
            placeholder="Ask: Why is Marketing high risk?"
          />
        </label>
        <button
          className="iconTextButton followUpButton"
          type="button"
          onClick={() => void handleFollowUp()}
          disabled={followUpLoading || !followUpQuestion.trim()}
        >
          <MessageSquareMore size={16} />
          {followUpLoading ? "Asking..." : "Ask follow-up"}
        </button>
        {followUpError && <p className="emptyState">{followUpError}</p>}
        {!followUpEntries.length && (
          <p className="emptyState">No follow-up questions for this analysis yet.</p>
        )}
        {followUpEntries.map((entry) => (
          <div className="followUpResult" key={entry.id}>
            <p className="muted">
              Follow-up asked {new Date(entry.created_at).toLocaleString()}
            </p>
            <div className="metric">
              <span>Question</span>
              <strong>{entry.question}</strong>
            </div>
            <h4>Follow-up answer</h4>
            <p>{entry.response.answer}</p>
            <div className="metric">
              <span>Suggested action</span>
              <strong>{entry.response.suggested_action}</strong>
            </div>
            <div className="analysisSection">
              <h4>Evidence used</h4>
              {entry.response.referenced_findings.length === 0 ? (
                <p className="emptyState">No matching evidence rows were returned for this follow-up.</p>
              ) : (
                <div className="evidenceList">
                  {entry.response.referenced_findings.map((itemId) => {
                    const finding = findingsById.get(itemId);
                    const lineItem = lineItemsById.get(itemId);
                    if (!finding) return null;
                    return (
                      <div className="evidenceItem" key={itemId}>
                        <p>
                          {finding.department} / {finding.category}
                        </p>
                        {lineItem && (
                          <p>
                            Budget: {formatMoney(lineItem.budget_amount)} · Actual:{" "}
                            {formatMoney(lineItem.actual_amount)} · Variance:{" "}
                            {formatSignedMoney(lineItem.variance)}
                          </p>
                        )}
                        <p>{finding.evidence}</p>
                      </div>
                    );
                  })}
                  {entry.response.referenced_findings.every(
                    (itemId) => !findingsById.get(itemId)
                  ) && (
                    <p className="emptyState">No matching evidence rows were returned for this follow-up.</p>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
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
