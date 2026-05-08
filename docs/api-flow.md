# TruthLayer AI — Verification Pipeline Flow

## How It Works

No HTTP API. The Streamlit app calls the pipeline directly.

## Pipeline Steps

```
1. PDF Upload (Streamlit UI)
   └── Validate: .pdf extension, non-empty, ≤20MB

2. Text Extraction  (core/utils/pdf_extractor.py)
   └── PyMuPDF extracts text layer
   └── Raises ValueError if: empty, scanned, or corrupted

3. Claim Detection  (core/utils/claim_detector.py)
   └── Step 1: Groq LLM extracts factual claims (JSON array)
   └── Step 2: Quality filter — rejects fragments, isolated numbers
   └── Step 3: Heuristic fallback if LLM returns nothing
   └── Raises ValueError if: no valid claims found

4. Concurrent Verification  (core/services/verification_service.py)
   └── asyncio.gather() with Semaphore(3)
   └── For each claim:
       a. DuckDuckGo search (4 results, deduplicated)
       b. Source credibility ranking (Tier1 > Tier2 > other)
       c. Groq LLM verdict generation
       d. Confidence calibration + natural variation
       e. Returns: verdict, confidence, correct_fact, reasoning

5. Trust Score + Summary
   └── Weighted trust score (0–100) based on verdict distribution
   └── AI-generated document summary via Groq

6. Results Display  (web/components/results.py)
   └── Metrics row: Total, Verified, Inaccurate, Misleading, False, Avg Conf, Trust
   └── Trust bar
   └── Per-claim cards with verdict badge, confidence bar, sources
   └── CSV export
```

## Verdict Types

| Verdict | Meaning |
|---|---|
| Verified | Evidence clearly supports the claim |
| Inaccurate | Claim has errors, outdated data, or exaggeration |
| Misleading | Technically true but omits critical context |
| False | Evidence directly contradicts the claim |
| Unverifiable | No relevant evidence found |

## Confidence Scoring

| Range | Meaning |
|---|---|
| 88–97% | Strong multi-source agreement |
| 70–87% | Moderate evidence |
| 45–69% | Weak or conflicting evidence |
| 0–44% | Minimal evidence |

Max confidence is capped at 97% — never 100%.

## Deployment

- **Streamlit Cloud**: Set `GROQ_API_KEY` in Secrets dashboard
- **Local**: Set `GROQ_API_KEY` in `.env` file
- **Main file**: `web/app.py`
