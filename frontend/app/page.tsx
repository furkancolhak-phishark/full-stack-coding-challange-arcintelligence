"use client";

import { useEffect, useMemo, useState } from "react";
import { RefreshCw, Sparkles } from "lucide-react";

import { api } from "../src/api/client";
import {
  AnalysisFollowUp,
  AnalysisRun,
  LineItemPayload,
  ProviderConfig,
  ProviderConfigPayload,
  ProviderOption,
  Scenario,
  ScenarioPayload
} from "../src/api/types";
import { AnalysisPanel } from "../src/components/AnalysisPanel";
import { LineItemsTable } from "../src/components/LineItemsTable";
import { ProviderSettingsPanel } from "../src/components/ProviderSettingsPanel";
import { ScenarioForm } from "../src/components/ScenarioForm";
import { ScenarioList } from "../src/components/ScenarioList";

export default function Home() {
  const defaultAnalysisQuestion = "Which line items should we review first?";
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const [analysisRuns, setAnalysisRuns] = useState<AnalysisRun[]>([]);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<number | null>(null);
  const [providerConfigs, setProviderConfigs] = useState<ProviderConfig[]>([]);
  const [providerOptions, setProviderOptions] = useState<ProviderOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [providerLoading, setProviderLoading] = useState(true);
  const [providerSaving, setProviderSaving] = useState(false);
  const [syncingProviderId, setSyncingProviderId] = useState<number | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisQuestion, setAnalysisQuestion] = useState("");
  const [error, setError] = useState<string | null>(null);

  const latestAnalysis = useMemo(() => {
    if (selectedAnalysisId) {
      return analysisRuns.find((run) => run.id === selectedAnalysisId) || null;
    }
    return analysisRuns[0] || null;
  }, [analysisRuns, selectedAnalysisId]);

  useEffect(() => {
    void loadWorkspace();
  }, []);

  useEffect(() => {
    if (selectedId) {
      void loadScenario(selectedId);
    }
  }, [selectedId]);

  const activeProvider =
    providerConfigs.find((config) => config.is_active) || null;

  async function loadWorkspace() {
    await Promise.all([loadScenarios(), loadProviders()]);
  }

  async function loadScenarios(preferredId?: number | null) {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listScenarios();
      setScenarios(data);
      const ids = new Set(data.map((scenario) => scenario.id));
      const preferredExists =
        preferredId !== undefined && preferredId !== null && ids.has(preferredId);
      const selectedExists = selectedId !== null && ids.has(selectedId);
      const nextId = preferredExists
        ? preferredId
        : preferredId === null
          ? null
          : selectedExists
            ? selectedId
            : data[0]?.id || null;
      setSelectedId(nextId);
      if (nextId) {
        await loadScenario(nextId);
      } else {
        setSelectedScenario(null);
        setAnalysisRuns([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load scenarios.");
    } finally {
      setLoading(false);
    }
  }

  async function loadProviders() {
    setProviderLoading(true);
    try {
      const [configs, options] = await Promise.all([
        api.listProviderConfigs(),
        api.listProviderOptions()
      ]);
      setProviderConfigs(configs);
      setProviderOptions(options);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load providers.");
    } finally {
      setProviderLoading(false);
    }
  }

  async function loadScenario(id: number) {
    setError(null);
    try {
      const [scenario, runs] = await Promise.all([
        api.getScenario(id),
        api.listAnalysisRuns(id)
      ]);
      setSelectedScenario(scenario);
      setAnalysisRuns(runs);
      setSelectedAnalysisId(runs[0]?.id || null);
      setAnalysisQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load scenario.");
    }
  }

  async function createScenario(payload: ScenarioPayload) {
    setError(null);
    try {
      const scenario = await api.createScenario(payload);
      await loadScenarios(scenario.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create scenario.");
      throw err;
    }
  }

  async function updateScenario(payload: ScenarioPayload) {
    if (!selectedScenario) return;
    setError(null);
    try {
      await api.updateScenario(selectedScenario.id, payload);
      await loadScenarios(selectedScenario.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update scenario.");
      throw err;
    }
  }

  async function deleteScenario(id: number) {
    const scenario = scenarios.find((item) => item.id === id);
    if (!window.confirm(`Delete ${scenario?.name || "this scenario"}?`)) return;
    setError(null);
    try {
      await api.deleteScenario(id);
      const nextId = scenarios.find((item) => item.id !== id)?.id;
      setSelectedId(nextId || null);
      await loadScenarios(nextId || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete scenario.");
    }
  }

  async function createLineItem(payload: LineItemPayload) {
    if (!selectedScenario) return;
    setError(null);
    try {
      await api.createLineItem(selectedScenario.id, payload);
      await loadScenarios(selectedScenario.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create line item.");
      throw err;
    }
  }

  async function updateLineItem(id: number, payload: LineItemPayload) {
    if (!selectedScenario) return;
    setError(null);
    try {
      await api.updateLineItem(id, payload);
      await loadScenarios(selectedScenario.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update line item.");
      throw err;
    }
  }

  async function deleteLineItem(id: number) {
    if (!selectedScenario) return;
    if (!window.confirm("Delete this line item?")) return;
    setError(null);
    try {
      await api.deleteLineItem(id);
      await loadScenarios(selectedScenario.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete line item.");
    }
  }

  async function analyzeBudget() {
    if (!selectedScenario) return;
    setAnalysisLoading(true);
    setError(null);
    try {
      const run = await api.analyzeScenarioWithProvider(selectedScenario.id, {
        question: analysisQuestion.trim() || defaultAnalysisQuestion,
        provider_config_id: activeProvider?.id || null
      });
      await loadScenario(selectedScenario.id);
      setSelectedAnalysisId(run.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze scenario.");
    } finally {
      setAnalysisLoading(false);
    }
  }

  async function createProviderConfig(payload: ProviderConfigPayload) {
    setProviderSaving(true);
    setError(null);
    try {
      await api.createProviderConfig(payload);
      await loadProviders();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create provider config."
      );
      throw err;
    } finally {
      setProviderSaving(false);
    }
  }

  async function updateProviderConfig(
    id: number,
    payload: Partial<ProviderConfigPayload>
  ) {
    setProviderSaving(true);
    setError(null);
    try {
      await api.updateProviderConfig(id, payload);
      await loadProviders();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update provider config."
      );
      throw err;
    } finally {
      setProviderSaving(false);
    }
  }

  async function deleteProviderConfig(id: number) {
    if (!window.confirm("Delete this provider config?")) return;
    setError(null);
    try {
      await api.deleteProviderConfig(id);
      await loadProviders();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete provider config."
      );
    }
  }

  async function refreshProviderModels(id: number) {
    setSyncingProviderId(id);
    setError(null);
    try {
      await api.refreshProviderModels(id);
      await loadProviders();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to refresh provider models."
      );
    } finally {
      setSyncingProviderId(null);
    }
  }

  async function setActiveProvider(id: number) {
    setError(null);
    try {
      await api.setActiveProvider(id);
      await loadProviders();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to set active provider.");
    }
  }

  function handleFollowUpCreated(analysisId: number, entry: AnalysisFollowUp) {
    setAnalysisRuns((runs) =>
      runs.map((run) =>
        run.id === analysisId
          ? { ...run, follow_ups: [entry, ...(run.follow_ups || [])] }
          : run
      )
    );
  }

  return (
    <main className="workspace">
      <aside className="sidebar">
        <div className="brandBlock">
          <h1>Budget Review Assistant</h1>
          <p>Finance variance workspace</p>
        </div>
        <section className="panel">
          <div className="sectionHeader">
            <h2>Scenarios</h2>
            <button
              className="iconButton"
              type="button"
              title="Refresh"
              aria-label="Refresh scenarios"
              onClick={() => void loadScenarios(selectedId || undefined)}
            >
              <RefreshCw size={16} />
            </button>
          </div>
          {loading ? (
            <p className="emptyState">Loading scenarios...</p>
          ) : (
            <ScenarioList
              scenarios={scenarios}
              selectedId={selectedId || undefined}
              onSelect={setSelectedId}
              onDelete={(id) => void deleteScenario(id)}
            />
          )}
        </section>
        <section className="panel">
          <h2>New scenario</h2>
          <ScenarioForm onSubmit={createScenario} />
        </section>
        {providerLoading ? (
          <section className="panel">
            <h2>LLM providers</h2>
            <p className="emptyState">Loading provider settings...</p>
          </section>
        ) : (
          <ProviderSettingsPanel
            configs={providerConfigs}
            options={providerOptions}
            saving={providerSaving}
            syncingId={syncingProviderId}
            onCreate={createProviderConfig}
            onUpdate={updateProviderConfig}
            onDelete={deleteProviderConfig}
            onRefreshModels={refreshProviderModels}
            onSetActive={setActiveProvider}
          />
        )}
      </aside>

      <section className="mainColumn">
        {error && <div className="errorBanner">{error}</div>}

        {selectedScenario ? (
          <>
            <section className="panel">
              <div className="sectionHeader">
                <div>
                  <h2>{selectedScenario.name}</h2>
                  <p className="muted">{selectedScenario.period}</p>
                  <p className="muted">
                    {activeProvider
                      ? `Active provider: ${activeProvider.name} / ${
                          activeProvider.selected_model || "No model selected"
                        }`
                      : "No active provider config. Analysis will use backend fallback."}
                  </p>
                </div>
                <button
                  className="primaryButton"
                  type="button"
                  onClick={() => void analyzeBudget()}
                  disabled={
                    analysisLoading || selectedScenario.line_items.length === 0
                  }
                >
                  <Sparkles size={16} />
                  {analysisLoading ? "Analyzing..." : "Analyze Budget"}
                </button>
              </div>
              <label className="analysisQuestionField">
                <span>Analysis question</span>
                <textarea
                  rows={3}
                  value={analysisQuestion}
                  onChange={(event) => setAnalysisQuestion(event.target.value)}
                  placeholder="Ask: Which departments are over budget?"
                />
              </label>
              <ScenarioForm
                scenario={selectedScenario}
                onSubmit={updateScenario}
                submitLabel="Save"
              />
            </section>

            <section className="panel">
              <div className="sectionHeader">
                <h2>Line items</h2>
                <p className="muted">{selectedScenario.line_items.length} rows</p>
              </div>
              <LineItemsTable
                lineItems={selectedScenario.line_items}
                onCreate={createLineItem}
                onUpdate={updateLineItem}
                onDelete={deleteLineItem}
              />
            </section>
          </>
        ) : (
          <section className="panel centeredPanel">
            <h2>No scenario selected</h2>
            <p className="emptyState">Create a scenario to begin.</p>
          </section>
        )}
      </section>

      <aside className="analysisColumn">
        {analysisRuns.length > 1 && (
          <label className="historySelect">
            <span>Analysis history</span>
            <select
              value={selectedAnalysisId || ""}
              onChange={(event) => setSelectedAnalysisId(Number(event.target.value))}
            >
              {analysisRuns.map((run) => (
                <option key={run.id} value={run.id}>
                  {new Date(run.created_at).toLocaleString()} · {run.provider}
                </option>
              ))}
            </select>
          </label>
        )}
        <AnalysisPanel
          analysis={latestAnalysis}
          lineItems={selectedScenario?.line_items || []}
          onFollowUpCreated={handleFollowUpCreated}
        />
      </aside>
    </main>
  );
}
