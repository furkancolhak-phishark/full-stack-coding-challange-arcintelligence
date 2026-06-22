"use client";

import { FormEvent, ReactNode, useEffect, useRef, useState } from "react";
import {
  BadgeCheck,
  Cloud,
  Database,
  KeyRound,
  RefreshCw,
  Save,
  Server,
  Trash2,
  WandSparkles
} from "lucide-react";

import {
  ProviderConfig,
  ProviderConfigPayload,
  ProviderName,
  ProviderOption
} from "../api/types";

type Draft = {
  name: string;
  provider: ProviderName;
  api_key: string;
  clear_api_key: boolean;
  base_url: string;
  selected_model: string;
  is_active: boolean;
};

type Props = {
  configs: ProviderConfig[];
  options: ProviderOption[];
  saving: boolean;
  syncingId: number | null;
  onCreate: (payload: ProviderConfigPayload) => Promise<void>;
  onUpdate: (id: number, payload: Partial<ProviderConfigPayload>) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
  onRefreshModels: (id: number) => Promise<void>;
  onSetActive: (id: number) => Promise<void>;
};

export function ProviderSettingsPanel({
  configs,
  options,
  saving,
  syncingId,
  onCreate,
  onUpdate,
  onDelete,
  onRefreshModels,
  onSetActive
}: Props) {
  const [selectedId, setSelectedId] = useState<number | "new">("new");
  const [draft, setDraft] = useState<Draft>(() => createDraft(options[0]));
  const formRef = useRef<HTMLFormElement | null>(null);

  useEffect(() => {
    if (!options.length) return;
    if (selectedId === "new") {
      setDraft((current) =>
        current.provider ? current : createDraft(options[0])
      );
      return;
    }

    const selected = configs.find((config) => config.id === selectedId);
    if (!selected) {
      const nextConfig = configs.find((config) => config.is_active) || configs[0];
      if (nextConfig) {
        setSelectedId(nextConfig.id);
        setDraft(createDraftFromConfig(nextConfig));
      } else {
        setSelectedId("new");
        setDraft(createDraft(options[0]));
      }
      return;
    }

    setDraft(createDraftFromConfig(selected));
  }, [configs, options, selectedId]);

  const selectedConfig =
    selectedId === "new"
      ? null
      : configs.find((config) => config.id === selectedId) || null;

  const providerOption =
    options.find((option) => option.provider === draft.provider) || options[0];

  function scrollToForm() {
    window.requestAnimationFrame(() => {
      formRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start"
      });
    });
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    const payload: ProviderConfigPayload = {
      name: draft.name,
      provider: draft.provider,
      base_url: draft.base_url,
      selected_model: draft.selected_model,
      is_active: draft.is_active
    };

    if (draft.api_key) payload.api_key = draft.api_key;
    if (draft.clear_api_key) payload.clear_api_key = true;

    if (selectedConfig) {
      await onUpdate(selectedConfig.id, payload);
      return;
    }

    await onCreate(payload);
  }

  return (
    <section className="panel providerPanel">
      <div className="sectionHeader">
        <div>
          <h2>LLM providers</h2>
          <p className="muted">
            API keys stay on the backend and are stored encrypted at rest.
          </p>
        </div>
        <button
          className="iconTextButton"
          type="button"
          onClick={() => {
            setSelectedId("new");
            setDraft(createDraft(options[0]));
            scrollToForm();
          }}
        >
          <WandSparkles size={16} />
          New config
        </button>
      </div>

      <div className="providerConfigList">
        {configs.map((config) => (
          <button
            key={config.id}
            className={`providerConfigItem ${
              selectedId === config.id ? "providerConfigItemActive" : ""
            }`}
            type="button"
            onClick={() => {
              setSelectedId(config.id);
              setDraft(createDraftFromConfig(config));
              scrollToForm();
            }}
          >
            <div>
              <strong>{config.name}</strong>
              <p className="muted">
                {labelForProvider(config.provider)} ·{" "}
                {config.selected_model || "No model selected"}
              </p>
            </div>
            {config.is_active && <span className="reviewFirst">Active</span>}
          </button>
        ))}
        {!configs.length && (
          <p className="emptyState">
            Add a provider config to browse models and analyze with that provider.
          </p>
        )}
      </div>

      <form
        ref={formRef}
        className="stack form providerForm"
        onSubmit={(event) => void handleSubmit(event)}
      >
        <label>
          <span>Provider</span>
          <select
            value={draft.provider}
            onChange={(event) => {
              const nextProvider = event.target.value as ProviderName;
              const nextOption =
                options.find((option) => option.provider === nextProvider) ||
                options[0];
              setDraft({
                ...draft,
                provider: nextProvider,
                base_url: nextOption.default_base_url,
                selected_model:
                  selectedConfig?.provider === nextProvider
                    ? draft.selected_model
                    : nextOption.default_model
              });
            }}
          >
            {options.map((option) => (
              <option key={option.provider} value={option.provider}>
                {option.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Config name</span>
          <input
            required
            value={draft.name}
            onChange={(event) =>
              setDraft({ ...draft, name: event.target.value })
            }
          />
        </label>

        <label>
          <span>API key</span>
          <input
            type="password"
            placeholder={
              selectedConfig?.has_api_key
                ? "Leave blank to keep the stored key"
                : providerOption?.requires_api_key
                  ? "Paste API key"
                  : "Optional for this provider"
            }
            value={draft.api_key}
            onChange={(event) =>
              setDraft({
                ...draft,
                api_key: event.target.value,
                clear_api_key: false
              })
            }
          />
        </label>

        {selectedConfig?.has_api_key && (
          <div className="providerMetaRow">
            <span className="muted">
              <KeyRound size={14} /> Stored key: {selectedConfig.masked_api_key}
            </span>
            <button
              className="iconTextButton"
              type="button"
              onClick={() =>
                setDraft({ ...draft, api_key: "", clear_api_key: true })
              }
            >
              <Trash2 size={14} />
              Remove key
            </button>
          </div>
        )}

        {(draft.provider === "ollama" || draft.provider === "openai" || draft.provider === "anthropic") && (
          <label>
            <span>Base URL</span>
            <input
              value={draft.base_url}
              onChange={(event) =>
                setDraft({ ...draft, base_url: event.target.value })
              }
              placeholder={providerOption?.default_base_url}
            />
          </label>
        )}

        <label>
          <span>Selected model</span>
          {selectedConfig?.model_catalog?.length ? (
            <select
              value={draft.selected_model}
              onChange={(event) =>
                setDraft({ ...draft, selected_model: event.target.value })
              }
            >
              <option value="">Choose a model</option>
              {selectedConfig.model_catalog.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.label}
                </option>
              ))}
            </select>
          ) : (
            <input
              value={draft.selected_model}
              onChange={(event) =>
                setDraft({ ...draft, selected_model: event.target.value })
              }
              placeholder={providerOption?.default_model || "Model name"}
            />
          )}
        </label>

        <label className="checkboxRow">
          <input
            type="checkbox"
            checked={draft.is_active}
            onChange={(event) =>
              setDraft({ ...draft, is_active: event.target.checked })
            }
          />
          <span>Use this as the active provider for analysis</span>
        </label>

        {selectedConfig && (
          <div className="providerToolbar">
            <button
              className="iconTextButton"
              type="button"
              onClick={() => void onRefreshModels(selectedConfig.id)}
              disabled={syncingId === selectedConfig.id}
            >
              <RefreshCw size={16} />
              {syncingId === selectedConfig.id ? "Syncing..." : "Sync models"}
            </button>
            <button
              className="iconTextButton"
              type="button"
              onClick={() => void onSetActive(selectedConfig.id)}
            >
              <BadgeCheck size={16} />
              Set active
            </button>
            <button
              className="iconTextButton dangerButton"
              type="button"
              onClick={() => void onDelete(selectedConfig.id)}
            >
              <Trash2 size={16} />
              Delete
            </button>
          </div>
        )}

        <button className="primaryButton" type="submit" disabled={saving}>
          <Save size={16} />
          {saving ? "Saving..." : selectedConfig ? "Save config" : "Create config"}
        </button>
      </form>

      <div className="providerFacts">
        <ProviderFact
          icon={<Cloud size={16} />}
          text="Gemini and Anthropic models are listed from their hosted APIs after you provide a key."
        />
        <ProviderFact
          icon={<Server size={16} />}
          text="OpenAI models are listed from the configured base URL, which also works with compatible gateways."
        />
        <ProviderFact
          icon={<Database size={16} />}
          text="Ollama models are discovered from its local tags endpoint, so only installed models appear."
        />
      </div>
    </section>
  );
}

function createDraft(option?: ProviderOption): Draft {
  return {
    name: option ? `${option.name} config` : "Provider config",
    provider: option?.provider || "gemini",
    api_key: "",
    clear_api_key: false,
    base_url: option?.default_base_url || "",
    selected_model: option?.default_model || "",
    is_active: false
  };
}

function createDraftFromConfig(config: ProviderConfig): Draft {
  return {
    name: config.name,
    provider: config.provider,
    api_key: "",
    clear_api_key: false,
    base_url: config.base_url,
    selected_model: config.selected_model,
    is_active: config.is_active
  };
}

function labelForProvider(provider: ProviderName): string {
  if (provider === "openai") return "OpenAI";
  if (provider === "anthropic") return "Anthropic";
  if (provider === "ollama") return "Ollama";
  return "Gemini";
}

function ProviderFact({
  icon,
  text
}: {
  icon: ReactNode;
  text: string;
}) {
  return (
    <div className="providerFact">
      <span>{icon}</span>
      <p>{text}</p>
    </div>
  );
}
