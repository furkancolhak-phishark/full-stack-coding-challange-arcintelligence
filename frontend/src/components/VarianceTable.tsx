import { Finding } from "../api/types";
import { formatPercent, formatSignedMoney, varianceClass } from "../utils/money";

const severityRank = { high: 3, medium: 2, low: 1 };

export function VarianceTable({ findings }: { findings: Finding[] }) {
  const sorted = [...findings].sort((a, b) => {
    const severityDelta = severityRank[b.severity] - severityRank[a.severity];
    if (severityDelta !== 0) return severityDelta;
    return Math.abs(Number(b.variance)) - Math.abs(Number(a.variance));
  });

  return (
    <div className="tableWrap compactTable">
      <table className="dataTable">
        <thead>
          <tr>
            <th>Area</th>
            <th>Severity</th>
            <th>Variance</th>
            <th>Variance %</th>
            <th>Risk</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((finding) => (
            <tr key={finding.line_item_id}>
              <td>
                {finding.department} / {finding.category}
              </td>
              <td>
                <span className={`severityBadge ${finding.severity}`}>
                  {finding.severity}
                </span>
              </td>
              <td className={varianceClass(finding.variance)}>
                {formatSignedMoney(finding.variance)}
              </td>
              <td className={varianceClass(finding.variance)}>
                {formatPercent(finding.variance_percent)}
              </td>
              <td>{finding.risk_type.replaceAll("_", " ")}</td>
            </tr>
          ))}
          {!sorted.length && (
            <tr>
              <td colSpan={5} className="emptyCell">
                No variance findings yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
