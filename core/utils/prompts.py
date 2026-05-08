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

Classify the verdict:
- Verified: Evidence clearly supports the claim
- Inaccurate: Claim has errors, outdated data, or exaggeration
- Misleading: Technically true but omits critical context
- False: Evidence directly contradicts the claim
- Unverifiable: No relevant evidence found

Confidence guide: strong multi-source=88-97, moderate=70-87, weak/conflicting=45-69
Never return 100%. Reasoning must be 2-3 sentences max.

correct_fact rules:
- If Verified: return empty string ""
- If not Verified: return ONE short sentence with the correct fact (max 15 words)
- Style: "Tesla sold ~1.8M vehicles in 2023." NOT a paragraph
- Never explain, never use CAGR formulas, never write multiple sentences

Respond ONLY with valid JSON:
{{
  "verdict": "Verified" | "Inaccurate" | "Misleading" | "False" | "Unverifiable",
  "confidence": <integer 0-97>,
  "correct_fact": "<one short sentence or empty string>",
  "reasoning": "<2-3 sentence explanation>"
}}"""


SUMMARY_PROMPT = """You are an AI analyst. Generate a concise document trust summary.

VERIFICATION RESULTS:
{results_summary}

Write a 2-3 sentence professional summary covering what the document claims, how many were verified vs false, and overall reliability. Be direct. Output plain text only."""
