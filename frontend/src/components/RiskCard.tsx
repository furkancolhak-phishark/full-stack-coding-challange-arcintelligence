import { Finding } from "../api/types";
import { formatPercent, formatSignedMoney, varianceClass } from "../utils/money";

export function RiskCard({
  finding,
  isFirst
}: {
  finding: Finding;
  isFirst: boolean;
}) {
  return (
    <article className="riskCard">
      <div className="riskCardHeader">
        <div>
          <h4>{finding.department}</h4>
          <p>{finding.category}</p>
        </div>
        <div className="badgeStack">
          {isFirst && <span className="reviewFirst">Review first</span>}
          <span className={`severityBadge ${finding.severity}`}>
            {finding.severity}
          </span>
        </div>
      </div>
      <p className={varianceClass(finding.variance)}>
        {formatSignedMoney(finding.variance)} · {formatPercent(finding.variance_percent)}
      </p>
      <p>{finding.recommendation}</p>
    </article>
  );
}
