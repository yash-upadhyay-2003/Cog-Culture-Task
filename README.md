# TruthLayer AI

> AI-powered fact-checking SaaS — upload a PDF, verify its claims against live web data in seconds.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

---

## Problem Statement

Misinformation travels faster than fact-checking. Research papers, reports, and news articles contain hundreds of specific claims — dates, statistics, financial figures, technical assertions — that no human team can verify at scale. TruthLayer AI automates this, giving analysts, journalists, and researchers a production-grade fact-checking tool powered by state-of-the-art LLMs and live web search.

---

## Features

- **PDF Upload** — drag-and-drop any text-based PDF (up to 20MB)
- **Claim Extraction** — LLM-powered detection of measurable, verifiable claims only
- **Heuristic Fallback** — regex-based extraction when LLM returns nothing
- **Live Web Search** — DuckDuckGo search with trusted-source prioritization
- **Hybrid Verification** — rule-based numeric checks + LLM semantic reasoning
- **Nuanced Verdicts** — `Verified`, `Inaccurate`, `Misleading`, `False`, or `Unverifiable`
- **Calibrated Confidence** — realistic scoring with source quality bonuses (never 100%)
- **Trust Score** — weighted document-level reliability score (0–100)
- **AI Summary** — auto-generated document analysis after verification
- **Evidence Drill-down** — reasoning, corrected facts, and source URLs per claim
- **CSV Export** — download full verification report
- **Model Fallback** — automatic switch from `llama-3.3-70b-versatile` to `llama-3.1-8b-instant`
- **Zero Persistence** — fully stateless, no database, no user data stored
- **Single Process** — no separate backend server, deploys directly on Streamlit Cloud

---

## Architecture

```
User Browser
    │
    ▼
Streamlit App (web/app.py)
    │
    ▼
web/services/pipeline.py
    │
    ├── core/utils/pdf_extractor.py     — PyMuPDF text extraction
    ├── core/utils/claim_detector.py    — LLM + heuristic claim extraction
    └── core/services/verification_service.py
        ├── core/services/search_service.py   — DuckDuckGo + source ranking
        └── core/services/groq_service.py     — Groq LLM + model fallback
    │
    ▼
Results → Streamlit UI
```

---

## Project Structure

```
truthlayer-ai/
│
├── core/                          # All AI/ML logic (no web framework)
│   ├── config.py                  # Reads Streamlit secrets + env vars
│   ├── models/
│   │   └── schema.py              # Pydantic data models
│   ├── services/
│   │   ├── groq_service.py        # Groq LLM client + model fallback
│   │   ├── search_service.py      # DuckDuckGo search + source ranking
│   │   └── verification_service.py  # Async orchestration + trust score
│   └── utils/
│       ├── pdf_extractor.py       # PyMuPDF text extraction
│       ├── claim_detector.py      # LLM + heuristic claim extraction
│       ├── verifier.py            # Per-claim verify logic
│       ├── helpers.py             # JSON parsing, claim validation
│       └── prompts.py             # All LLM prompt templates
│
├── web/                           # Streamlit frontend
│   ├── app.py                     # Main Streamlit app
│   ├── components/
│   │   ├── upload.py              # PDF upload component
│   │   ├── results.py             # Results dashboard + export
│   │   └── status.py              # Processing animation
│   └── services/
│       └── pipeline.py            # Calls core pipeline synchronously
│
├── docs/
│   ├── architecture.md
│   └── api-flow.md
│
├── .streamlit/
│   ├── config.toml                # Theme + server config
│   └── secrets.toml               # Local secrets (gitignored)
│
├── .env.example
├── .gitignore
├── requirements.txt               # Single requirements file
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit 1.35+ |
| AI | Groq API (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`) |
| PDF Parsing | PyMuPDF (fitz) |
| Web Search | ddgs (DuckDuckGo) |
| Validation | Pydantic v2 |
| Deployment | Streamlit Cloud |

---

## AI Workflow

```
1. CLAIM EXTRACTION
   PDF Text → Groq LLM → JSON array of claims
   Fallback: regex heuristics for numbers, dates, percentages
   Filter: reject fragments, isolated years, headings

2. EVIDENCE GATHERING (per claim, concurrent)
   Query → DuckDuckGo (4 results, deduplicated)
   Rank: Tier1 (.gov, .edu, Reuters, WHO) > Tier2 > other

3. VERDICT GENERATION (per claim)
   Evidence → Groq LLM → verdict + confidence + reasoning
   Verdicts: Verified / Inaccurate / Misleading / False / Unverifiable
   Confidence: capped at 97%, source quality bonus applied

4. TRUST SCORE + SUMMARY
   Weighted score across all verdicts (0–100)
   AI-generated 2-3 sentence document summary
```

---

## Verdict Reference

| Verdict | Meaning |
|---------|---------|
| `Verified` | Evidence clearly supports the claim |
| `Inaccurate` | Claim has errors, outdated data, or exaggeration |
| `Misleading` | Technically true but omits critical context |
| `False` | Evidence directly contradicts the claim |
| `Unverifiable` | No relevant evidence found |

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

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
cp .env.example .env
# Edit .env and add: GROQ_API_KEY=your_key_here

# 5. Run
streamlit run web/app.py
```

App opens at: [http://localhost:8501](http://localhost:8501)

---

## Deployment on Streamlit Cloud

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your repository and branch
4. Set **Main file path**: `web/app.py`
5. Click **Advanced settings → Secrets** and add:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

6. Click **Deploy**

No separate backend needed — the entire app runs as a single Streamlit process.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | **Yes** | — | Groq API key from console.groq.com |
| `GROQ_MODEL_PRIMARY` | No | `llama-3.3-70b-versatile` | Primary LLM model |
| `GROQ_MODEL_FALLBACK` | No | `llama-3.1-8b-instant` | Fallback LLM model |
| `MAX_CLAIMS` | No | `10` | Max claims to extract per document |
| `SEARCH_RESULTS_PER_CLAIM` | No | `4` | Search results fetched per claim |

---

## Future Roadmap

- [ ] Scanned PDF support via OCR (pytesseract / AWS Textract)
- [ ] URL input support (scrape + verify web articles)
- [ ] Batch document processing (multiple PDFs)
- [ ] PDF export of verification report
- [ ] Claim-level source confidence scoring
- [ ] Fine-tuned claim extraction model
- [ ] Webhook support for async large-document processing

---

## License

MIT License — see [LICENSE](LICENSE) for details.
