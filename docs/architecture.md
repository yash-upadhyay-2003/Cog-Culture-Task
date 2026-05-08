# TruthLayer AI — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    User (Browser)                        │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP (PDF upload)
                          ▼
┌─────────────────────────────────────────────────────────┐
│               Streamlit Frontend (web/)                  │
│  - PDF upload UI                                        │
│  - Progress indicators                                   │
│  - Results table + expandable evidence                   │
└─────────────────────────┬───────────────────────────────┘
                          │ POST /verify (multipart/form-data)
                          ▼
┌─────────────────────────────────────────────────────────┐
│               FastAPI Backend (api/)                     │
│                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────┐  │
│  │ PDF Extractor│──▶│Claim Detector│──▶│Verification│  │
│  │  (PyMuPDF)  │   │  (Groq LLM)  │   │  Service   │  │
│  └──────────────┘   └──────────────┘   └─────┬──────┘  │
│                                               │         │
│                               ┌───────────────┴──────┐  │
│                               │  For each claim:     │  │
│                               │  1. DuckDuckGo Search│  │
│                               │  2. Groq LLM Verdict │  │
│                               └──────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        Groq API    DuckDuckGo    (No DB)
        (LLM)       (Search)    Stateless
```

## Key Design Decisions

1. **Stateless Processing** — No database. Each request is fully self-contained.
2. **Concurrent Verification** — Claims are verified in parallel using asyncio + semaphore.
3. **Model Fallback** — Primary `llama3-70b-8192` falls back to `mixtral-8x7b-32768` on error.
4. **Trusted Source Priority** — Search results from .gov/.edu/research domains are ranked first.
5. **Hybrid Verification** — Rule-based number/date checks supplement LLM semantic reasoning.
