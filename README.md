# Budget Review Assistant

## What I Built

This is a small full-stack app for reviewing budget scenarios.

Users can:

- create, edit, and delete budget scenarios
- add, edit, and delete line items inside a scenario
- run an analysis for the selected scenario
- ask one follow-up question about a saved analysis
- view the result as structured UI instead of plain text
- switch between saved analysis runs
- export a saved analysis as Markdown or PDF

The backend calculates totals, variances, percentages, and review priority first. After that, a model can turn those facts into a structured analysis. If no API key is available, or if the model response fails validation, the app falls back to a deterministic result so the product still works.

I also added a provider settings panel in the UI. It supports Gemini, OpenAI, Anthropic, and Ollama. A user can save a provider config, browse the models available for that provider, choose any model they want, and run `Analyze Budget` with that selection.

## How I Started

I started this task by planning the product slice first instead of jumping straight into code.

I used ChatGPT to help define the scope, limits, and structure of the task. That helped me think through the database shape, the main endpoints I would need, and how to keep the backend, frontend, and model layer separated in a modular way. After that, I turned those notes into a more detailed implementation brief before starting the actual build.

For the implementation itself, I worked mostly with OpenAI tools. Part of that choice was cost efficiency, and part of it was that I really like Codex for both backend and frontend work. In this project especially, I thought Codex was very strong on the backend side. I used a strong prompt and ran Codex with high reasoning to build the main structure of the app.

My rough plan was:

- define the product scope and keep it focused
- design the data model and required API endpoints
- build the backend first, especially deterministic budget calculations and the analysis flow
- build the frontend on top of those APIs
- add provider configuration, history, and export support after the core flow was stable
- test and refine the product until it felt complete enough for submission

For the frontend, my thinking was a bit more flexible. If the UI effort had needed to go much further, I could also have used OpenCode with models like Qwen or DeepSeek for faster iteration on the presentation side. But the challenge did not ask for a perfect frontend, so I chose to keep the UI simple, clear, and functional instead of spending too much time polishing visual details.

Testing was also part of the process from both sides. Codex and I tested things in parallel, and after a few extra passes and fixes, I felt the product reached a solid final state.

## How to Run

```bash
git clone <repo-url>
cd <repo-folder>
cp .env.example .env
docker compose up --build
```

Then open:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Django admin: http://localhost:8000/admin

The backend runs migrations and seeds demo scenarios automatically when the database is empty.

After startup, you can use the app right away with the seeded data.

If you want to use a hosted model, open the provider settings panel and:

- create provider configs for Gemini, OpenAI, Anthropic, or Ollama
- enter API keys in the UI
- sync the provider's available models
- choose a model and mark that config as active for analysis

If your provider does not support the default model, choose a supported model from Provider Settings or set a supported model in `.env`.

## Demo Notes

The app does not require an API key for the core demo.

If no provider key is configured, `Analyze Budget` still works and returns the deterministic fallback analysis. That means a reviewer can still test the full product flow without any external setup.

If someone wants to see a hosted LLM response instead, they can add their own provider key in Provider Settings, sync models, select a supported model, and run the analysis again.

## Environment Variables

The project uses `.env.example` as the template.

- `DJANGO_SECRET_KEY`: Django secret for local development
- `APP_ENCRYPTION_KEY`: key used to encrypt saved provider secrets. If left blank in local development, the app derives one from `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`: set to `true` for local development
- `DJANGO_ALLOWED_HOSTS`: comma-separated backend hostnames
- `CORS_ALLOWED_ORIGINS`: allowed frontend origins
- `LLM_PROVIDER`: optional fallback provider name. Supported values are `gemini`, `openai`, `anthropic`, and `ollama`
- `GEMINI_API_KEY`: optional Gemini API key
- `GEMINI_MODEL`: optional Gemini model name
- `ANTHROPIC_API_KEY`: optional Anthropic API key
- `ANTHROPIC_MODEL`: optional Anthropic model name
- `OLLAMA_BASE_URL`: optional Ollama base URL
- `OLLAMA_MODEL`: optional Ollama model name
- `OPENAI_API_KEY`: optional OpenAI API key
- `OPENAI_MODEL`: optional OpenAI model name
- `NEXT_PUBLIC_API_BASE_URL`: frontend API base URL

## AI Approach and Why

I wanted the budget numbers to be reliable first, and the model output to sit on top of that.

So the backend always calculates totals, variances, percentages, severity, and review order by itself. That part is deterministic and easy to test. Then, if a provider is configured, the app sends those saved rows and calculated facts to the selected model and asks for a structured JSON response. The response is validated before it is shown in the UI.

If the provider is missing, unreachable, or returns invalid output, the backend falls back to a deterministic structured result. That means the app stays usable even without external model access.

Gemini is the default hosted option in this repo, and the default Gemini model is `gemini-3.1-flash-lite`. I picked it because it is new, fast, and I think it is good enough for this task even if it is not trying to be the highest-end model. Gemini also has a free tier, which helps keep the app cheap to run while still producing useful structured recommendations.

At the same time, I did not want the app to be tied to one provider or one model. That is why I added the provider layer in the first place. The user can configure Gemini, OpenAI, Anthropic, or Ollama, browse that provider's model list, pick the model they want, and use that selection when running `Analyze Budget`.

I also added a simple follow-up flow on top of a saved analysis. It is not a full chat interface. Instead, the user can ask one follow-up question about the selected analysis run and get a structured answer with referenced findings and a suggested action.

Provider API keys saved from the UI are encrypted in the backend database. The UI only shows masked values after save.

## Architecture and Trade-Offs

- Django REST Framework handles API and persistence.
- Next.js, React, and TypeScript provide the workspace UI.
- SQLite is used for one-command challenge setup.
- CRUD, budget calculations, model integration, and export logic are kept separate.
- Provider configuration is stored in the database so the reviewer can switch models from the UI instead of editing environment variables.
- The app supports env-based fallback keys, but the normal flow is to manage providers from the frontend.
- Analysis responses are validated before they are saved or rendered.
- Analysis history is persisted so the user can come back to older runs after refresh.

## Backend Tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

Tests cover variance calculations, zero-budget handling, deterministic fallback behavior, provider config behavior, analysis creation, and export output. They do not require external API keys.

## Assumptions / Known Limitations

- No authentication or multi-user permissions.
- SQLite is used for simplicity.
- Finance logic is simplified to variance analysis.
- LLM quality depends on the configured provider and model.
- Provider secrets are encrypted at rest, but this is still a simple challenge app, not a full secrets platform.
- Ollama model discovery only shows models available on the configured Ollama host.
- No streaming analysis progress.

## What I Would Improve With More Time

- CSV import/export for line items.
- Variance trend charts across periods.
- Better audit history for provider and analysis changes.
- Configurable finance thresholds.
- Streaming analysis progress with SSE.
- Frontend component tests and Playwright flow tests.
