# TruthLayer AI

> AI-powered fact-checking SaaS — upload a PDF, verify its claims against live web data in seconds.

---

## Problem Statement

Misinformation travels faster than fact-checking. Research papers, reports, and news articles contain hundreds of specific claims — dates, statistics, financial figures, technical assertions — that no human team can verify at scale. TruthLayer AI automates this, giving analysts, journalists, and researchers a production-grade fact-checking tool powered by state-of-the-art LLMs and live web search.

---

## Features

- **PDF Upload** — drag-and-drop any text-based PDF (up to 20MB)
- **Claim Extraction** — LLM-powered detection of measurable, verifiable claims only
- **Live Web Search** — DuckDuckGo search with trusted-source prioritization
- **Hybrid Verification** — rule-based numeric checks + LLM semantic reasoning
- **Structured Verdicts** — `Verified`, `Inaccurate`, `False`, or `Unverifiable`
- **Evidence Drill-down** — expandable reasoning, correct facts, and source URLs
- **Model Fallback** — automatic switch from `llama3-70b-8192` to `mixtral-8x7b-32768`
- **Zero Persistence** — fully stateless, no database, no user data stored

---

## Architecture

```
User Browser
    │
    ▼
Streamlit Frontend (web/)
    │ POST /verify (PDF bytes)
    ▼
FastAPI Backend (api/)
    ├── PyMuPDF — text extraction
    ├── Groq LLM — claim detection
    └── For each claim (concurrent):
        ├── DuckDuckGo Search
        └── Groq LLM — verdict + reasoning
    │
    ▼
JSON Response → Streamlit Results Table
```

---

## Monorepo Structure

```
truthlayer-ai/
├── README.md
├── .env.example
├── docker-compose.yml
├── requirements.txt
│
├── api/                          # FastAPI backend
│   ├── app/
│   │   ├── main.py               # App entrypoint, CORS, routers
│   │   ├── routes/verify.py      # POST /verify endpoint
│   │   ├── services/
│   │   │   ├── groq_service.py   # Groq API client + model fallback
│   │   │   ├── search_service.py # DuckDuckGo search + source ranking
│   │   │   └── verification_service.py  # Async orchestration
│   │   ├── utils/
│   │   │   ├── pdf_extractor.py  # PyMuPDF text extraction
│   │   │   ├── claim_detector.py # LLM claim extraction
│   │   │   ├── verifier.py       # Per-claim verify logic
│   │   │   ├── verdict_engine.py # Rule-based numeric checks
│   │   │   ├── prompts.py        # All LLM prompt templates
│   │   │   └── helpers.py        # JSON parsing, text utilities
│   │   ├── models/claim_schema.py # Pydantic models
│   │   └── config/settings.py    # Pydantic settings
│   ├── requirements.txt
│   └── Dockerfile
│
├── web/                          # Streamlit frontend
│   ├── app.py                    # Main Streamlit app
│   ├── components/
│   │   ├── upload.py             # File uploader component
│   │   ├── results.py            # Results table + expanders
│   │   └── status.py             # Processing animations
│   ├── services/api_client.py    # HTTP client for FastAPI
│   ├── requirements.txt
│   └── Dockerfile
│
└── docs/
    ├── architecture.md
    └── api-flow.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit 1.35+ |
| Backend | FastAPI + Uvicorn |
| AI | Groq API (`llama3-70b-8192` / `mixtral-8x7b-32768`) |
| PDF Parsing | PyMuPDF (fitz) |
| Web Search | duckduckgo-search |
| HTTP Client | httpx |
| Validation | Pydantic v2 |
| Containerization | Docker + Docker Compose |

---

## AI Workflow

```
1. CLAIM EXTRACTION
   Prompt → Groq LLM
   Extract only: statistics, dates, percentages, financial figures, technical claims
   Ignore: opinions, vague marketing text, speculation
   Output: JSON array of claim strings (max 10)

2. EVIDENCE GATHERING (per claim, concurrent)
   Query → DuckDuckGo (3-5 results)
   Prioritize: .gov, .edu, WHO, Reuters, AP, BBC, Nature, NCBI
   Format evidence block for LLM context

3. VERDICT GENERATION (per claim)
   Rule-based: numeric overlap check → confidence adjustment
   LLM-based: semantic comparison, contradiction detection
   Output: verdict + confidence + correct_fact + reasoning
```

---

## API Reference

### `POST /verify`

Upload a PDF and receive structured fact-check results.

**Request:** `multipart/form-data` with `file` field (PDF)

**Response:**
```json
{
  "claims": [
    {
      "claim": "Global temperatures rose by 1.1°C since pre-industrial levels.",
      "verdict": "Verified",
      "confidence": 92.0,
      "correct_fact": "",
      "reasoning": "Multiple IPCC and NASA sources confirm this figure.",
      "sources": [
        { "title": "IPCC Report", "snippet": "...", "url": "https://..." }
      ]
    }
  ],
  "total_claims": 1,
  "processing_time_seconds": 8.4,
  "document_excerpt": "..."
}
```

**Verdicts:**
| Verdict | Meaning |
|---------|---------|
| `Verified` | Evidence supports the claim |
| `Inaccurate` | Claim has minor errors or outdated data |
| `False` | Evidence contradicts the claim |
| `Unverifiable` | No relevant evidence found |

**Other endpoints:**
- `GET /health` — liveness check
- `GET /docs` — Swagger UI
- `GET /redoc` — ReDoc UI

---

## Setup

### Prerequisites
- Python 3.11+
- [Groq API key](https://console.groq.com)

### Local Development

```bash
# 1. Clone and enter project
git clone <repo-url>
cd truthlayer-ai

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Set environment variables
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Start FastAPI backend (terminal 1)
uvicorn api.app.main:app --host 0.0.0.0 --port 8000 --reload

# 6. Start Streamlit frontend (terminal 2)
streamlit run web/app.py --server.port 8501
```

### Docker Deployment

```bash
# Build and start both services
cp .env.example .env  # Edit and add GROQ_API_KEY
docker-compose up --build
```

Access:
- Streamlit UI: `http://localhost:8501`
- FastAPI Docs: `http://localhost:8000/docs`

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | **Yes** | — | Groq API key from console.groq.com |
| `GROQ_MODEL_PRIMARY` | No | `llama3-70b-8192` | Primary LLM model |
| `GROQ_MODEL_FALLBACK` | No | `mixtral-8x7b-32768` | Fallback LLM model |
| `MAX_CLAIMS` | No | `10` | Max claims to extract per document |
| `SEARCH_RESULTS_PER_CLAIM` | No | `4` | Search results fetched per claim |
| `API_BASE_URL` | No | `http://localhost:8000` | FastAPI URL (for Streamlit) |
| `API_TIMEOUT` | No | `120` | Request timeout in seconds |

---

## Deployment

### Streamlit Cloud
1. Push to GitHub
2. Connect repo at [share.streamlit.io](https://share.streamlit.io)
3. Set main file: `web/app.py`
4. Add `GROQ_API_KEY` and `API_BASE_URL` in Secrets
5. Deploy FastAPI separately on Render, Railway, or Fly.io

### Render
1. Create a **Web Service** → connect GitHub repo
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn api.app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables in the Render dashboard

---

## Future Roadmap

- [ ] Scanned PDF support via OCR (pytesseract / AWS Textract)
- [ ] Claim-level source confidence scoring
- [ ] Batch document processing (multiple PDFs)
- [ ] Export results to CSV / PDF report
- [ ] URL input support (scrape + verify web articles)
- [ ] API key dashboard with usage tracking
- [ ] Webhook support for async large-document processing
- [ ] Fine-tuned claim extraction model

---

## Screenshots

> _Add screenshots to `docs/screenshots/` after deployment._

---

## License

MIT License — see [LICENSE](LICENSE) for details.
