export type Severity = "low" | "medium" | "high";
export type ProviderName = "gemini" | "openai" | "anthropic" | "ollama";
export type RiskType =
  | "overspend"
  | "underspend"
  | "zero_budget"
  | "unusual_variance"
  | "note_based_risk";

export type LineItem = {
  id: number;
  scenario: number;
  department: string;
  category: string;
  description: string;
  budget_amount: string;
  actual_amount: string;
  variance: string;
  variance_percent: number | null;
  status: "over_budget" | "under_budget" | "on_track";
  notes: string;
  created_at: string;
  updated_at: string;
};

export type Scenario = {
  id: number;
  name: string;
  period: string;
  description: string;
  line_item_count: number;
  total_budget: string;
  total_actual: string;
  total_variance: string;
  line_items: LineItem[];
  created_at: string;
  updated_at: string;
};

export type Finding = {
  line_item_id: number;
  department: string;
  category: string;
  variance: string;
  variance_percent: number | null;
  severity: Severity;
  risk_type: RiskType;
  recommendation: string;
  evidence: string;
};

export type AnalysisResult = {
  summary: string;
  health_score: number;
  total_budget: string;
  total_actual: string;
  total_variance: string;
  total_variance_percent: number | null;
  findings: Finding[];
  recommendations: string[];
  review_order: number[];
  generated_by: string;
};

export type FollowUpResponse = {
  answer: string;
  referenced_findings: number[];
  suggested_action: string;
  generated_by: string;
};

export type AnalysisFollowUp = {
  id: number;
  analysis_run: number;
  question: string;
  response: FollowUpResponse;
  created_at: string;
};

export type AnalysisRun = {
  id: number;
  scenario: number;
  provider_config: number | null;
  question: string;
  provider: string;
  model: string;
  input_snapshot: unknown;
  result: AnalysisResult;
  follow_ups: AnalysisFollowUp[];
  created_at: string;
};

export type ProviderModel = {
  id: string;
  label: string;
  metadata: Record<string, unknown>;
};

export type ProviderConfig = {
  id: number;
  name: string;
  provider: ProviderName;
  has_api_key: boolean;
  masked_api_key: string;
  base_url: string;
  selected_model: string;
  model_catalog: ProviderModel[];
  is_active: boolean;
  last_model_sync_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ProviderOption = {
  provider: ProviderName;
  name: string;
  default_model: string;
  default_base_url: string;
  requires_api_key: boolean;
};

export type ScenarioPayload = {
  name: string;
  period: string;
  description?: string;
};

export type LineItemPayload = {
  department: string;
  category: string;
  description?: string;
  budget_amount: string;
  actual_amount: string;
  notes?: string;
};

export type ProviderConfigPayload = {
  name: string;
  provider: ProviderName;
  api_key?: string;
  clear_api_key?: boolean;
  base_url?: string;
  selected_model?: string;
  is_active?: boolean;
};
