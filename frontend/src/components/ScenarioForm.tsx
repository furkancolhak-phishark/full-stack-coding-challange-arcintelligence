"use client";

import { FormEvent, useEffect, useState } from "react";
import { Check, Plus, X } from "lucide-react";

import { Scenario, ScenarioPayload } from "../api/types";

type Props = {
  scenario?: Scenario | null;
  onSubmit: (payload: ScenarioPayload) => Promise<void>;
  onCancel?: () => void;
  submitLabel?: string;
};

const emptyForm: ScenarioPayload = {
  name: "",
  period: "",
  description: ""
};

export function ScenarioForm({
  scenario,
  onSubmit,
  onCancel,
  submitLabel = "Create"
}: Props) {
  const [form, setForm] = useState<ScenarioPayload>(emptyForm);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (scenario) {
      setForm({
        name: scenario.name,
        period: scenario.period,
        description: scenario.description
      });
    } else {
      setForm(emptyForm);
    }
  }, [scenario]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      await onSubmit(form);
      if (!scenario) setForm(emptyForm);
    } catch {
      // Parent component renders the API error banner.
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="stack form" onSubmit={handleSubmit}>
      <label>
        <span>Name</span>
        <input
          required
          value={form.name}
          onChange={(event) => setForm({ ...form, name: event.target.value })}
        />
      </label>
      <label>
        <span>Period</span>
        <input
          required
          value={form.period}
          onChange={(event) => setForm({ ...form, period: event.target.value })}
          placeholder="2026 Q2"
        />
      </label>
      <label>
        <span>Description</span>
        <textarea
          value={form.description}
          onChange={(event) =>
            setForm({ ...form, description: event.target.value })
          }
          rows={3}
        />
      </label>
      <div className="buttonRow">
        <button className="primaryButton" type="submit" disabled={saving}>
          {scenario ? <Check size={16} /> : <Plus size={16} />}
          {saving ? "Saving..." : submitLabel}
        </button>
        {onCancel && (
          <button className="iconTextButton" type="button" onClick={onCancel}>
            <X size={16} />
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
