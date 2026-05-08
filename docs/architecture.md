# TruthLayer AI — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    User (Browser)                        │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│           Streamlit App (web/app.py)                     │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              web/services/pipeline.py            │   │
│  │                                                  │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────┐  │   │
│  │  │PDF Extractor│─▶│Claim Detector│─▶│Verify  │  │   │
│  │  │ (PyMuPDF)   │  │ (Groq LLM)   │  │Service │  │   │
│  │  └─────────────┘  └──────────────┘  └───┬────┘  │   │
│  │                                          │       │   │
│  │                          ┌───────────────┘       │   │
│  │                          ▼                       │   │
│  │                  For each claim:                 │   │
│  │                  1. DuckDuckGo Search            │   │
│  │                  2. Groq LLM Verdict             │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                    │               │
                    ▼               ▼
              Groq API         DuckDuckGo
              (LLM)            (Search)
```

## Key Design Decisions

1. **Single Process** — No separate backend server. Streamlit calls core pipeline directly.
2. **Stateless** — No database. Each request is fully self-contained.
3. **Concurrent Verification** — Claims verified in parallel using asyncio + semaphore(3).
4. **Model Fallback** — Primary `llama-3.3-70b-versatile` falls back to `llama-3.1-8b-instant`.
5. **Trusted Source Priority** — .gov/.edu/research domains ranked first in search results.
6. **Hybrid Verification** — Rule-based checks + LLM semantic reasoning.
7. **Streamlit Cloud Ready** — Reads secrets from `st.secrets`, no env file needed.

## Project Structure

```
truthlayer-ai/
├── core/                        # All AI/ML logic
│   ├── config.py                # Reads Streamlit secrets + env vars
│   ├── models/schema.py         # Pydantic data models
│   ├── services/
│   │   ├── groq_service.py      # Groq LLM client + fallback
│   │   ├── search_service.py    # DuckDuckGo + source ranking
│   │   └── verification_service.py  # Orchestration + trust score
│   └── utils/
│       ├── pdf_extractor.py     # PyMuPDF text extraction
│       ├── claim_detector.py    # LLM + heuristic claim extraction
│       ├── verifier.py          # Per-claim verification logic
│       ├── helpers.py           # JSON parsing, text utilities
│       └── prompts.py           # All LLM prompt templates
│
├── web/                         # Streamlit frontend
│   ├── app.py                   # Main Streamlit app
│   ├── components/
│   │   ├── upload.py            # Upload UI component
│   │   ├── results.py           # Results dashboard
│   │   └── status.py            # Processing animation
│   └── services/
│       └── pipeline.py          # Calls core pipeline synchronously
│
├── .streamlit/
│   ├── config.toml              # Theme + server config
│   └── secrets.toml             # Local secrets (gitignored)
│
└── requirements.txt             # Single requirements file
```
