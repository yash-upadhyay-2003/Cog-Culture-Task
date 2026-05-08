CLAIM_EXTRACTION_PROMPT = """You are a fact-checking assistant. Extract verifiable factual statements from the text.

Extract statements containing: dates, years, statistics, percentages, financial figures, company facts, market claims, scientific assertions, named entities with attributed facts, measurable comparisons.

Be inclusive — if a statement has a number, date, or named fact, include it.
Return MAXIMUM {max_claims} of the strongest, most specific claims.
Return ONLY a valid JSON array of strings. No markdown, no explanation.

TEXT:
{text}"""


VERIFICATION_PROMPT = """You are an expert fact-checker. Analyze this claim against the evidence below.

CLAIM: {claim}

EVIDENCE:
{evidence}

Classify the verdict precisely:
- Verified: Evidence clearly supports the claim
- Inaccurate: Claim is partially correct but contains errors, outdated data, or exaggeration
- Misleading: Claim is technically true but omits critical context or is deceptive
- False: Evidence directly contradicts the claim
- Unverifiable: No relevant evidence found

Confidence scoring guide:
- Strong multi-source agreement: 88-97
- Moderate evidence: 70-87
- Weak or conflicting evidence: 45-69
- Minimal evidence: 20-44

Rules:
- Never return 100% confidence
- Calibrate based on source quality and agreement
- Reasoning must be 2-3 sentences max, professional and concise

Respond ONLY with valid JSON:
{{
  "verdict": "Verified" | "Inaccurate" | "Misleading" | "False" | "Unverifiable",
  "confidence": <integer 0-97>,
  "correct_fact": "<corrected fact or empty string if Verified>",
  "reasoning": "<2-3 sentence professional explanation>"
}}"""


SUMMARY_PROMPT = """You are an AI analyst. Generate a concise document trust summary.

VERIFICATION RESULTS:
{results_summary}

Write a 2-3 sentence professional summary covering:
- What the document claims overall
- How many claims were verified vs false/inaccurate
- The overall reliability assessment

Be direct, analytical, and professional. No fluff. Output plain text only."""
