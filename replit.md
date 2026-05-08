# TruthLayer AI

AI-powered fact-checking SaaS — upload a PDF, verify its claims against live web data in seconds.

## Run & Operate

- `TruthLayer API` workflow — FastAPI backend on port 8000
- `TruthLayer Web` workflow — Streamlit frontend on port 8099
- `pnpm --filter @workspace/api-server run dev` — run the TypeScript API scaffold (port 8080, unused by TruthLayer)

## Stack

- **Frontend**: Streamlit (Python 3.11)
- **Backend**: FastAPI + Uvicorn (Python 3.11)
- **AI**: Groq API — `llama3-70b-8192` (primary), `mixtral-8x7b-32768` (fallback)
- **PDF Parsing**: PyMuPDF (fitz)
- **Web Search**: duckduckgo-search
- **HTTP Client**: httpx
- **Validation**: Pydantic v2

## Where things live

- `api/app/main.py` — FastAPI entrypoint
- `api/app/routes/verify.py` — POST /verify endpoint
- `api/app/services/groq_service.py` — Groq LLM client + model fallback
- `api/app/services/search_service.py` — DuckDuckGo search + source ranking
- `api/app/services/verification_service.py` — async concurrent verification orchestration
- `api/app/utils/prompts.py` — all LLM prompt templates
- `api/app/utils/pdf_extractor.py` — PyMuPDF text extraction
- `api/app/utils/claim_detector.py` — LLM claim extraction
- `api/app/utils/verifier.py` — per-claim verify logic
- `api/app/models/claim_schema.py` — Pydantic response models
- `api/app/config/settings.py` — Pydantic settings (reads from env)
- `web/app.py` — Streamlit main app
- `web/components/` — upload, results, status components
- `web/services/api_client.py` — HTTP client for FastAPI
- `.streamlit/config.toml` — Streamlit dark theme config
- `docs/architecture.md` — system architecture diagram
- `docs/api-flow.md` — API pipeline documentation

## Architecture decisions

- **Stateless** — no database, all processing is ephemeral per request
- **Concurrent verification** — claims processed in parallel with asyncio semaphore (limit 3)
- **Model fallback** — automatic switch from llama3-70b to mixtral on API errors
- **Hybrid verification** — rule-based numeric checks + LLM semantic reasoning
- **Trusted source priority** — .gov/.edu/WHO/Reuters ranked above general web results

## Product

TruthLayer AI accepts a PDF upload, extracts verifiable factual claims (dates, statistics, financial figures, technical assertions), searches the live web for evidence, and returns structured verdicts: Verified, Inaccurate, False, or Unverifiable.

## User preferences

- Python 3.11 stack — no React, no Node.js for this project
- FastAPI on port 8000; Streamlit on port 8099
- Streamlit dark theme: black background (#0a0a0a), white text

## Gotchas

- Python libs live at `.pythonlibs/bin/` — use full paths in workflows
- Port 8501 (Streamlit default) is NOT in Replit's supported port list — use 8099
- Always run from workspace root so `api.app.main` resolves correctly
- `GROQ_API_KEY` must be set as a Replit secret for verification to work
- `.streamlit/config.toml` controls theme and port

## Pointers

- See `docs/architecture.md` for system diagram
- See `docs/api-flow.md` for API pipeline details
- Groq console: https://console.groq.com
