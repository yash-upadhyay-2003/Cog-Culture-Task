import streamlit as st
import pandas as pd
from typing import Dict, Any


VERDICT_STYLES = {
    "Verified": ("✅", "#22c55e"),
    "Inaccurate": ("⚠️", "#f59e0b"),
    "False": ("❌", "#ef4444"),
    "Unverifiable": ("❓", "#6b7280"),
}


def _verdict_badge(verdict: str) -> str:
    icon, _ = VERDICT_STYLES.get(verdict, ("❓", "#6b7280"))
    return f"{icon} {verdict}"


def render_summary_metrics(data: Dict[str, Any]):
    """Render top-level summary metric cards."""
    claims = data.get("claims", [])
    total = len(claims)
    if total == 0:
        return

    counts = {"Verified": 0, "Inaccurate": 0, "False": 0, "Unverifiable": 0}
    for c in claims:
        v = c.get("verdict", "Unverifiable")
        counts[v] = counts.get(v, 0) + 1

    elapsed = data.get("processing_time_seconds", 0)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Claims", total)
    col2.metric("✅ Verified", counts["Verified"])
    col3.metric("⚠️ Inaccurate", counts["Inaccurate"])
    col4.metric("❌ False", counts["False"])
    col5.metric("⏱ Time (s)", f"{elapsed:.1f}")


def render_results_table(data: Dict[str, Any]):
    """Render the claims results table and expandable evidence sections."""
    claims = data.get("claims", [])
    if not claims:
        st.warning("No claims were returned from the verification engine.")
        return

    st.markdown("---")
    st.markdown("### Verification Results")

    rows = []
    for c in claims:
        verdict = c.get("verdict", "Unverifiable")
        icon, _ = VERDICT_STYLES.get(verdict, ("❓", "#6b7280"))
        rows.append({
            "Claim": c.get("claim", ""),
            "Verdict": f"{icon} {verdict}",
            "Confidence": f"{c.get('confidence', 0):.0f}%",
            "Correct Fact": c.get("correct_fact", "—") or "—",
        })

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Claim": st.column_config.TextColumn("Claim", width="large"),
            "Verdict": st.column_config.TextColumn("Verdict", width="medium"),
            "Confidence": st.column_config.TextColumn("Confidence", width="small"),
            "Correct Fact": st.column_config.TextColumn("Correct Fact", width="large"),
        }
    )

    st.markdown("---")
    st.markdown("### Evidence & Reasoning")
    st.caption("Expand each claim to see supporting evidence, sources, and AI reasoning.")

    for i, claim in enumerate(claims):
        verdict = claim.get("verdict", "Unverifiable")
        icon, _ = VERDICT_STYLES.get(verdict, ("❓", "#6b7280"))
        label = f"{icon} {verdict} — {claim.get('claim', '')[:80]}"

        with st.expander(label, expanded=False):
            reasoning = claim.get("reasoning", "")
            if reasoning:
                st.markdown("**Reasoning**")
                st.markdown(reasoning)

            correct_fact = claim.get("correct_fact", "")
            if correct_fact:
                st.markdown("**Correct Fact**")
                st.info(correct_fact)

            sources = claim.get("sources", [])
            if sources:
                st.markdown("**Sources**")
                for s in sources:
                    title = s.get("title", "Source")
                    url = s.get("url", "")
                    snippet = s.get("snippet", "")
                    if url:
                        st.markdown(f"- [{title}]({url})")
                    else:
                        st.markdown(f"- {title}")
                    if snippet:
                        st.caption(snippet[:200])
            else:
                st.caption("No sources retrieved for this claim.")
