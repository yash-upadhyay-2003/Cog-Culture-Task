# TruthLayer AI — API Flow

## POST /verify

### Request
```
Content-Type: multipart/form-data
Body: file=<pdf_bytes>
```

### Step-by-Step Pipeline

```
1. PDF Upload
   └── Validate: .pdf extension, non-empty, ≤20MB

2. Text Extraction (PyMuPDF)
   └── Raises 422 if: empty, scanned, or corrupted

3. Claim Detection (Groq LLM)
   └── Prompt: extract only measurable/statistical claims
   └── Returns: JSON array of claim strings (max 10)
   └── Raises 422 if: no claims found

4. Concurrent Verification (asyncio, semaphore=3)
   └── For each claim:
       a. DuckDuckGo search (3-5 results)
       b. Prioritize trusted domains (.gov, .edu, WHO, Reuters...)
       c. Format evidence block
       d. Groq LLM verdict (with fallback model)
       e. Parse: verdict, confidence, correct_fact, reasoning

5. Response Assembly
   └── Returns: VerificationResponse JSON
```

### Response
```json
{
  "claims": [
    {
      "claim": "string",
      "verdict": "Verified | Inaccurate | False | Unverifiable",
      "confidence": 0.0,
      "correct_fact": "string",
      "reasoning": "string",
      "sources": [
        { "title": "", "snippet": "", "url": "" }
      ]
    }
  ],
  "total_claims": 0,
  "processing_time_seconds": 0.0,
  "document_excerpt": "string"
}
```

### Error Codes
| Code | Meaning |
|------|---------|
| 400 | Not a PDF, or file is empty |
| 413 | File exceeds 20MB limit |
| 422 | No text extracted, or no claims detected |
| 503 | AI/Groq service unavailable or key missing |
| 500 | Internal server error |
