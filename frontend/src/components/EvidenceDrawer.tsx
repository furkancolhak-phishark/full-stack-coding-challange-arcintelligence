import { Finding, LineItem } from "../api/types";
import { formatMoney, formatPercent, formatSignedMoney } from "../utils/money";

export function EvidenceDrawer({
  findings,
  lineItems
}: {
  findings: Finding[];
  lineItems: LineItem[];
}) {
  const itemById = new Map(lineItems.map((item) => [item.id, item]));

  return (
    <details className="evidencePanel" open>
      <summary>Why this answer?</summary>
      <div className="evidenceList">
        {findings.map((finding) => {
          const item = itemById.get(finding.line_item_id);
          return (
            <div className="evidenceItem" key={finding.line_item_id}>
              <h4>
                {finding.department} / {finding.category}
              </h4>
              <p>
                Budget: {formatMoney(item?.budget_amount || "0.00")} · Actual:{" "}
                {formatMoney(item?.actual_amount || "0.00")} · Variance:{" "}
                {formatSignedMoney(finding.variance)}
              </p>
              <p>
                Why flagged: {finding.evidence}{" "}
                {finding.variance_percent !== null &&
                  `Variance is ${formatPercent(finding.variance_percent)}.`}
              </p>
            </div>
          );
        })}
        {!findings.length && <p className="emptyState">No findings to explain.</p>}
      </div>
    </details>
  );
}
