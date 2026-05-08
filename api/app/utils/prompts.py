CLAIM_EXTRACTION_PROMPT = """You are a precise fact-checking assistant. Extract ONLY verifiable factual claims from the text below.

Extract ONLY:
- Measurable statements with specific numbers
- Dates and timelines
- Percentages and statistics
- Financial figures and economic data
- Scientific or technical claims
- Named entities with attributed facts

IGNORE completely:
- Opinions and subjective statements
- Vague marketing language
- Predictions and speculation
- General descriptions without specifics

Return a JSON array of strings. Each string is one factual claim, stated as a complete sentence.
Return MAXIMUM {max_claims} claims, prioritizing the most specific and verifiable ones.

If no verifiable claims are found, return an empty array [].

TEXT:
{text}

Return ONLY valid JSON array. No explanation, no markdown, no extra text."""


VERIFICATION_PROMPT = """You are a rigorous fact-checker. Analyze the following claim against the provided evidence from web searches.

CLAIM: {claim}

SEARCH EVIDENCE:
{evidence}

Your task:
1. Determine if the claim is: Verified, Inaccurate, or False
   - Verified: Evidence supports the claim
   - Inaccurate: Claim has minor errors or outdated info
   - False: Evidence contradicts the claim
   - Unverifiable: No relevant evidence found

2. Provide a confidence score (0-100)
3. If not Verified, provide the correct fact
4. Explain your reasoning concisely

Respond ONLY with valid JSON in this exact format:
{{
  "verdict": "Verified" | "Inaccurate" | "False" | "Unverifiable",
  "confidence": <number 0-100>,
  "correct_fact": "<corrected fact or empty string if verified>",
  "reasoning": "<2-3 sentence explanation>"
}}"""
