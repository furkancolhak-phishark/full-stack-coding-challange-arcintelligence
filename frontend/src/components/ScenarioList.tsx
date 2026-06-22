"use client";

import { Trash2 } from "lucide-react";

import { Scenario } from "../api/types";
import { formatMoney, formatSignedMoney, varianceClass } from "../utils/money";

type Props = {
  scenarios: Scenario[];
  selectedId?: number;
  onSelect: (id: number) => void;
  onDelete: (id: number) => void;
};

export function ScenarioList({
  scenarios,
  selectedId,
  onSelect,
  onDelete
}: Props) {
  if (!scenarios.length) {
    return <p className="emptyState">No scenarios yet.</p>;
  }

  return (
    <div className="scenarioList">
      {scenarios.map((scenario) => (
        <div
          className={`scenarioItem ${
            scenario.id === selectedId ? "scenarioItemActive" : ""
          }`}
          key={scenario.id}
        >
          <button
            className="scenarioSelect"
            type="button"
            onClick={() => onSelect(scenario.id)}
          >
            <span className="scenarioTitle">{scenario.name}</span>
            <span className="scenarioMeta">
              {scenario.period} · {scenario.line_item_count} rows
            </span>
            <span className={varianceClass(scenario.total_variance)}>
              {formatSignedMoney(scenario.total_variance)}
            </span>
            <span className="muted">Budget {formatMoney(scenario.total_budget)}</span>
          </button>
          <button
            className="iconButton dangerButton"
            type="button"
            title="Delete scenario"
            aria-label={`Delete ${scenario.name}`}
            onClick={() => onDelete(scenario.id)}
          >
            <Trash2 size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}
