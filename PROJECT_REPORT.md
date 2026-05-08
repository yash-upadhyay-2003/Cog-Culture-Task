# TruthLayer AI — Project Report

---

## Table of Contents

1. Problem Statement
2. Solution
3. Project Overview
4. Tech Stack
5. Architecture
6. Workflow
7. Features
8. API Reference
9. Project Structure
10. Screenshots Guide
11. Future Scope

---

## 1. Problem Statement

Misinformation spreads faster than it can be corrected. Research papers, financial reports, news articles, and marketing documents contain hundreds of specific factual claims — statistics, dates, percentages, named figures — that are impossible for any human team to verify at scale and speed.

Current fact-checking is:
- **Manual and slow** — a single analyst can verify ~10–20 claims per hour
- **Inconsistent** — different reviewers reach different conclusions on the same claim
- **Not scalable** — a 50-page report may contain 200+ verifiable claims
- **Reactive** — fact-checking happens after misinformation has already spread

There is no production-grade, automated tool that can take an arbitrary PDF document, extract every verifiable factual claim, cross-reference each one against live web sources, and return a structured, confidence-scored verdict — in under 60 seconds.

---

## 2. Solution

**TruthLayer AI** is an AI-powered fact-checking SaaS that automates the entire verification pipeline end-to-end:

1. User uploads any PDF document
2. An LLM extracts only measurable, verifiable factual claims
3. Each claim is searched against live web sources via DuckDuckGo
4. A second LLM pass reasons over the evidence and assigns a verdict
5. Results are returned as a structured dashboard with confidence scores, source links, reasoning, and a document-level trust score

The entire pipeline runs in under 60 seconds for a typical 10-page document, replacing hours of manual work.

---

## 3. Project Overview

| Field | Detail |
|---|---|
| Project Name | TruthLayer AI |
| Type | AI-powered SaaS Web Application |
| Category | NLP / Information Verification / LLM Application |
| Primary Users | Journalists, researchers, analysts, compliance teams |
| Deployment | Streamlit frontend + FastAPI backend |
| AI Provider | Groq API (llama-3.3-70b-versatile / llama-3.1-8b-instant) |
| Data Persistence | None — fully stateless, zero user data stored |
| Input | PDF documents (up to 200MB) |
| Output | Structured JSON — verdicts, confidence, reasoning, sources, trust score |

---

## 4. Tech Stack

### Backend
| Layer | Technology | Purpose |
|---|---|---|
| API Framework | FastAPI (Python) | REST API, async request handling |
| LLM Provider | Groq API | Ultra-fast LLM inference |
| Primary Model | llama-3.3-70b-versatile | Claim extraction + verdict generation |
| Fallback Model | llama-3.1-8b-instant | Automatic fallback on rate limit |
| PDF Parsing | PyMuPDF (fitz) | Text extraction from PDF |
| Web Search | ddgs (DuckDuckGo) | Live evidence retrieval |
| Data Validation | Pydantic v2 | Request/response schema validation |
| HTTP Client | httpx | Async HTTP for Groq + search |

### Frontend
| Layer | Technology | Purpose |
|---|---|---|
| UI Framework | Streamlit 1.57 | Web app rendering |
| Styling | Custom CSS (Inter font, light theme) | SaaS-grade UI |
| State Management | st.session_state + queue.Queue | Thread-safe processing |
| API Communication | httpx (TruthLayerClient) | Calls FastAPI backend |

### Infrastructure
| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Environment | python-dotenv |
| Version Control | Git / GitHub |
| Deployment Target | Streamlit Cloud (frontend) + any Python host (backend) |

---

## 5. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
└─────────────────────────┬───────────────────────────────────┘
                          │  HTTP (multipart/form-data PDF)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Streamlit Frontend  (web/app.py)                │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  upload.py  │  │   status.py  │  │    results.py     │  │
│  │ File upload │  │ Anim. steps  │  │ Metrics + Claims  │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
│                                                              │
│  queue.Queue ──► background thread ──► TruthLayerClient     │
└─────────────────────────┬───────────────────────────────────┘
                          │  POST /verify
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend  (api/app/main.py)              │
│                                                              │
│  POST /verify                                                │
│       │                                                      │
│       ▼                                                      │
│  pdf_extractor.py  ──►  Raw text from PDF pages             │
│       │                                                      │
│       ▼                                                      │
│  claim_detector.py ──►  Groq LLM → JSON array of claims     │
│                         Fallback: regex heuristics           │
│       │                                                      │
│       ▼  (concurrent, one task per claim)                    │
│  verification_service.py                                     │
│       ├── search_service.py  ──►  DuckDuckGo (4 results)    │
│       │                          Source tier ranking         │
│       └── groq_service.py   ──►  LLM verdict generation     │
│                                  Model fallback logic        │
│       │                                                      │
│       ▼                                                      │
│  Trust score calculation + AI summary generation            │
│       │                                                      │
│       ▼                                                      │
│  JSON Response: claims[], trust_score, summary, timing      │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | File | Responsibility |
|---|---|---|
| PDF Extractor | `api/app/utils/pdf_extractor.py` | PyMuPDF text extraction, page concatenation |
| Claim Detector | `api/app/utils/claim_detector.py` | LLM prompt → JSON claims, regex fallback |
| Search Service | `api/app/services/search_service.py` | DuckDuckGo queries, source deduplication, tier ranking |
| Groq Service | `api/app/services/groq_service.py` | Groq API client, primary/fallback model switching |
| Verification Service | `api/app/services/verification_service.py` | Async orchestration, trust score, summary |
| Verifier | `api/app/utils/verifier.py` | Per-claim verdict logic, confidence calibration |
| Verdict Engine | `api/app/utils/verdict_engine.py` | Rule-based numeric checks + LLM semantic reasoning |
| Prompts | `api/app/utils/prompts.py` | All LLM prompt templates |
| Helpers | `api/app/utils/helpers.py` | JSON parsing, claim validation, sanitization |

---

## 6. Workflow

### Step-by-Step Pipeline

```
STEP 1 — PDF UPLOAD
  User drags and drops a PDF into the Streamlit UI
  Frontend sends multipart POST /verify to FastAPI
  File size validated (max 200MB), MIME type checked

STEP 2 — TEXT EXTRACTION
  PyMuPDF reads all pages
  Text is cleaned, whitespace normalized
  Returns raw document text string

STEP 3 — CLAIM EXTRACTION
  Groq LLM (llama-3.3-70b-versatile) receives document text
  Prompt instructs: extract only measurable, verifiable claims
  Returns JSON array of claim strings (max 10 by default)
  If LLM returns nothing → regex fallback (numbers, %, dates)
  Claims filtered: reject fragments, isolated years, headings

STEP 4 — EVIDENCE GATHERING (concurrent per claim)
  Each claim → DuckDuckGo search query
  4 results fetched per claim, deduplicated by URL
  Sources ranked by tier:
    Tier 1: .gov, .edu, reuters.com, who.int, bbc.com
    Tier 2: established news outlets
    Tier 3: everything else

STEP 5 — VERDICT GENERATION (per claim)
  Evidence snippets + claim → Groq LLM
  LLM returns: verdict, confidence (0–97), reasoning, correct_fact
  Verdicts: Verified / Inaccurate / Misleading / False / Unverifiable
  Confidence capped at 97% (never 100%)
  Source quality bonus applied to confidence score

STEP 6 — TRUST SCORE + SUMMARY
  Weighted score across all verdicts:
    Verified     → full weight positive
    Inaccurate   → partial negative
    Misleading   → partial negative
    False        → full negative
    Unverifiable → neutral
  Score normalized to 0–100
  Groq LLM generates 2–3 sentence document summary

STEP 7 — RESPONSE + UI RENDER
  FastAPI returns structured JSON
  Streamlit renders: metrics row, AI summary, trust bar, claim cards
  Each claim card: verdict badge, confidence bar, reasoning, sources
  CSV export available
```

### Verdict Reference

| Verdict | Color | Meaning |
|---|---|---|
| Verified | Green | Evidence clearly supports the claim |
| Inaccurate | Amber | Claim has errors, outdated data, or exaggeration |
| Misleading | Orange | Technically true but omits critical context |
| False | Red | Evidence directly contradicts the claim |
| Unverifiable | Gray | No relevant evidence found |

### Trust Score Interpretation

| Score | Meaning |
|---|---|
| 75–100 | High credibility document |
| 50–74 | Mixed — some claims need scrutiny |
| 0–49 | Low credibility — significant inaccuracies found |

---

## 7. Features

### Core Features
- **PDF Upload** — drag-and-drop, up to 200MB, text-based PDFs
- **LLM Claim Extraction** — only measurable, verifiable claims extracted
- **Heuristic Fallback** — regex-based extraction when LLM returns nothing
- **Live Web Search** — DuckDuckGo with trusted-source prioritization
- **Hybrid Verification** — rule-based numeric checks + LLM semantic reasoning
- **5 Nuanced Verdicts** — Verified, Inaccurate, Misleading, False, Unverifiable
- **Calibrated Confidence** — realistic scoring, never 100%, source quality bonus
- **Trust Score** — weighted document-level reliability score (0–100)
- **AI Summary** — auto-generated 2–3 sentence document analysis
- **Evidence Drill-down** — reasoning, corrected facts, and source URLs per claim
- **CSV Export** — download full verification report
- **Model Fallback** — automatic switch from llama-3.3-70b to llama-3.1-8b on rate limit

### UI/UX Features
- Light theme SaaS design (Linear/Vercel/Stripe aesthetic)
- Sticky navbar with live verification badge
- Hero section with real-time stats
- Animated processing pipeline (5-step visual progress)
- Responsive layout — desktop, tablet, mobile
- Verdict badges color-coded per verdict type
- Confidence bars colored by verdict
- NaN/null safe — empty correct_fact fields hidden automatically
- Verified claims never show "Corrected Fact" section

### Engineering Features
- **Zero persistence** — fully stateless, no database, no user data stored
- **Thread-safe animation** — `queue.Queue` for background API thread communication
- **Single process** — no separate worker, deploys directly on Streamlit Cloud
- **Concurrent verification** — all claims verified in parallel via async tasks
- **Structured error handling** — connection errors, timeouts, API errors all surfaced cleanly

---

## 8. API Reference

### POST /verify

Accepts a PDF file and returns full verification results.

**Request**
```
Content-Type: multipart/form-data
Body: file=<pdf_bytes>
```

**Response (200 OK)**
```json
{
  "claims": [
    {
      "claim": "Global temperatures have risen by 1.1°C since pre-industrial times",
      "verdict": "Verified",
      "confidence": 91,
      "reasoning": "Multiple IPCC reports and NASA datasets confirm...",
      "correct_fact": "",
      "sources": [
        {
          "title": "IPCC Sixth Assessment Report",
          "snippet": "Global surface temperature increased by 1.1°C...",
          "url": "https://www.ipcc.ch/report/ar6/"
        }
      ]
    }
  ],
  "total_claims": 8,
  "processing_time_seconds": 34.2,
  "trust_score": 78.5,
  "summary": "This document presents climate data that is largely accurate..."
}
```

### GET /health

```json
{ "status": "ok" }
```

---

## 9. Project Structure

```
truthlayer-ai/
│
├── api/                              # FastAPI backend
│   ├── app/
│   │   ├── main.py                   # FastAPI app entry point
│   │   ├── config/
│   │   │   └── settings.py           # Env vars, model config
│   │   ├── models/
│   │   │   └── claim_schema.py       # Pydantic request/response models
│   │   ├── routes/
│   │   │   └── verify.py             # POST /verify endpoint
│   │   ├── services/
│   │   │   ├── groq_service.py       # Groq LLM client + model fallback
│   │   │   ├── search_service.py     # DuckDuckGo + source tier ranking
│   │   │   └── verification_service.py  # Async orchestration + trust score
│   │   └── utils/
│   │       ├── pdf_extractor.py      # PyMuPDF text extraction
│   │       ├── claim_detector.py     # LLM + heuristic claim extraction
│   │       ├── verifier.py           # Per-claim verify logic
│   │       ├── verdict_engine.py     # Rule-based + LLM verdict logic
│   │       ├── helpers.py            # JSON parsing, claim validation
│   │       └── prompts.py            # All LLM prompt templates
│   └── requirements.txt
│
├── web/                              # Streamlit frontend
│   ├── app.py                        # Main app — CSS, layout, state, logic
│   ├── components/
│   │   ├── upload.py                 # PDF upload card component
│   │   ├── results.py                # Metrics, claim cards, CSV export
│   │   └── status.py                 # How it works + processing animation
│   ├── services/
│   │   └── api_client.py             # TruthLayerClient — httpx wrapper
│   └── requirements.txt
│
├── docs/
│   ├── architecture.md
│   └── api-flow.md
│
├── .streamlit/
│   ├── config.toml                   # Light theme + server config
│   └── secrets.toml                  # Local secrets (gitignored)
│
├── .env.example                      # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 10. Screenshots Guide

> Add the following screenshots to your submission:

| Screenshot | What to Capture |
|---|---|
| **1. Landing Page** | Full page — navbar, hero section with stats cards, upload card |
| **2. File Uploaded** | Upload card with file name pill + "Verify Claims" button visible |
| **3. Processing Animation** | The 5-step animated pipeline card mid-verification |
| **4. Results — Metrics Row** | The 7 metric cards + AI summary block + trust bar |
| **5. Claim Card — Verified** | A green "Verified" claim with confidence bar and sources |
| **6. Claim Card — False/Inaccurate** | A red/amber claim showing corrected fact + reasoning |
| **7. CSV Export** | Bottom of results with the Export CSV button |
| **8. Mobile View** | Responsive single-column layout on narrow screen |

---

## 11. Future Scope

### Short Term (Next Sprint)
| Feature | Description |
|---|---|
| Scanned PDF support | OCR via pytesseract or AWS Textract for image-based PDFs |
| URL input | Scrape and verify web articles directly by URL |
| Claim-level source confidence | Per-source reliability score, not just tier ranking |
| PDF export | Download verification report as formatted PDF |

### Medium Term
| Feature | Description |
|---|---|
| Batch processing | Upload multiple PDFs, process queue asynchronously |
| Fine-tuned claim extractor | Domain-specific model trained on verified claim datasets |
| User accounts + history | Optional auth layer, save past verification runs |
| Browser extension | Highlight and verify claims on any webpage in real time |
| Webhook support | POST results to external systems when large docs finish |

### Long Term
| Feature | Description |
|---|---|
| Multi-language support | Verify claims in Spanish, French, Hindi, etc. |
| Real-time document monitoring | Watch a URL, alert when new claims appear |
| Enterprise API | Rate-limited API keys, usage dashboard, SLA |
| Claim graph | Visual network of related claims across multiple documents |
| Custom source lists | Let organizations define their own trusted source tiers |

---

## Summary

TruthLayer AI demonstrates a complete, production-grade AI application built on a modern Python stack. It solves a real problem — scalable fact-checking — using a well-designed pipeline that combines PDF parsing, concurrent web search, and dual-pass LLM reasoning. The system is stateless, deployable with zero infrastructure, and produces nuanced, explainable verdicts rather than simple true/false outputs.

The project showcases:
- **LLM orchestration** — prompt engineering, model fallback, structured output parsing
- **Async architecture** — concurrent claim verification, background thread safety
- **Production UI patterns** — thread-safe state management with queue.Queue, rerun-driven animation
- **Clean API design** — typed Pydantic schemas, structured error responses
- **Deployment readiness** — single-process Streamlit Cloud deploy, environment-based config

---

*TruthLayer AI — Built with FastAPI, Groq, Streamlit · v1.0*
