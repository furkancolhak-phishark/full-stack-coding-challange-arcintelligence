import {
  AnalysisFollowUp,
  AnalysisRun,
  LineItem,
  LineItemPayload,
  ProviderConfig,
  ProviderConfigPayload,
  ProviderOption,
  Scenario,
  ScenarioPayload
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000/api";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  analysisExportUrl: (id: number, format: "md" | "pdf") =>
    `${API_BASE_URL}/analysis-runs/${id}/export/?file_format=${format}`,
  listScenarios: () => request<Scenario[]>("/scenarios/"),
  getScenario: (id: number) => request<Scenario>(`/scenarios/${id}/`),
  createScenario: (payload: ScenarioPayload) =>
    request<Scenario>("/scenarios/", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  updateScenario: (id: number, payload: Partial<ScenarioPayload>) =>
    request<Scenario>(`/scenarios/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),
  deleteScenario: (id: number) =>
    request<void>(`/scenarios/${id}/`, { method: "DELETE" }),
  createLineItem: (scenarioId: number, payload: LineItemPayload) =>
    request<LineItem>(`/scenarios/${scenarioId}/line-items/`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  updateLineItem: (id: number, payload: Partial<LineItemPayload>) =>
    request<LineItem>(`/line-items/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),
  deleteLineItem: (id: number) =>
    request<void>(`/line-items/${id}/`, { method: "DELETE" }),
  analyzeScenario: (id: number, question?: string) =>
    request<AnalysisRun>(`/scenarios/${id}/analyze/`, {
      method: "POST",
      body: JSON.stringify({ question })
    }),
  listAnalysisRuns: (scenarioId: number) =>
    request<AnalysisRun[]>(`/scenarios/${scenarioId}/analysis-runs/`),
  listProviderConfigs: () => request<ProviderConfig[]>("/provider-configs/"),
  listProviderOptions: () =>
    request<ProviderOption[]>("/provider-configs/options/"),
  createProviderConfig: (payload: ProviderConfigPayload) =>
    request<ProviderConfig>("/provider-configs/", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  updateProviderConfig: (id: number, payload: Partial<ProviderConfigPayload>) =>
    request<ProviderConfig>(`/provider-configs/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),
  deleteProviderConfig: (id: number) =>
    request<void>(`/provider-configs/${id}/`, { method: "DELETE" }),
  refreshProviderModels: (id: number) =>
    request<ProviderConfig>(`/provider-configs/${id}/refresh-models/`, {
      method: "POST"
    }),
  setActiveProvider: (id: number) =>
    request<ProviderConfig>(`/provider-configs/${id}/set-active/`, {
      method: "POST"
    }),
  analyzeScenarioWithProvider: (
    id: number,
    payload: { question?: string; provider_config_id?: number | null }
  ) =>
    request<AnalysisRun>(`/scenarios/${id}/analyze/`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  followUpAnalysis: (id: number, question: string) =>
    request<AnalysisFollowUp>(`/analysis-runs/${id}/follow-up/`, {
      method: "POST",
      body: JSON.stringify({ question })
    })
};
