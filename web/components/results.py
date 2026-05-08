import streamlit as st
import pandas as pd
from typing import Dict, Any

VERDICT_MAP = {
    "Verified":     ("b-v", "✔ Verified",     "#16a34a"),
    "Inaccurate":   ("b-i", "◈ Inaccurate",   "#d97706"),
    "Misleading":   ("b-m", "◉ Misleading",   "#ea580c"),
    "False":        ("b-f", "✘ False",         "#dc2626"),
    "Unverifiable": ("b-u", "? Unverifiable",  "#6b7280"),
}


def render_summary_metrics(data: Dict[str, Any]):
    claims = data.get("claims", [])
    if not claims:
        return

    counts = {"Verified": 0, "Inaccurate": 0, "Misleading": 0, "False": 0, "Unverifiable": 0}
    total_conf = 0.0
    for c in claims:
        v = c.get("verdict", "Unverifiable")
        counts[v] = counts.get(v, 0) + 1
        total_conf += float(c.get("confidence", 0) or 0)

    avg_conf = total_conf / len(claims) if claims else 0
    trust = float(data.get("trust_score", 0) or 0)
    summary = data.get("summary", "")

    trust_color = "#16a34a" if trust >= 75 else ("#d97706" if trust >= 50 else "#dc2626")

    if summary:
        st.markdown(f"""
        <div style="background:#ffffff;border:1px solid #e8e8e8;border-radius:14px;
                    padding:1.2rem 1.4rem;margin-bottom:0.8rem;
                    box-shadow:0 1px 4px rgba(0,0,0,0.04);">
            <div style="font-size:0.62rem;color:#bbb;text-transform:uppercase;
                        letter-spacing:0.1em;font-weight:700;margin-bottom:0.5rem;">
                🧠 AI Document Analysis
            </div>
            <div style="font-size:0.85rem;color:#444;line-height:1.7;">{summary}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="tl-metrics">
        <div class="tl-mc">
            <div class="tl-mc-val">{len(claims)}</div>
            <div class="tl-mc-lbl">Total</div>
        </div>
        <div class="tl-mc v">
            <div class="tl-mc-val">{counts["Verified"]}</div>
            <div class="tl-mc-lbl">Verified</div>
        </div>
        <div class="tl-mc i">
            <div class="tl-mc-val">{counts["Inaccurate"]}</div>
            <div class="tl-mc-lbl">Inaccurate</div>
        </div>
        <div class="tl-mc" style="border-color:#fed7aa">
            <div class="tl-mc-val" style="color:#ea580c">{counts["Misleading"]}</div>
            <div class="tl-mc-lbl">Misleading</div>
        </div>
        <div class="tl-mc f">
            <div class="tl-mc-val">{counts["False"]}</div>
            <div class="tl-mc-lbl">False</div>
        </div>
        <div class="tl-mc">
            <div class="tl-mc-val">{avg_conf:.0f}%</div>
            <div class="tl-mc-lbl">Avg Conf.</div>
        </div>
        <div class="tl-mc">
            <div class="tl-mc-val" style="color:{trust_color}">{trust:.0f}</div>
            <div class="tl-mc-lbl">Trust Score</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-bottom:1rem;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.4rem;">
            <span style="font-size:0.65rem;color:#bbb;text-transform:uppercase;
                         letter-spacing:0.08em;font-weight:700;">Document Trust Score</span>
            <span style="font-size:0.75rem;color:{trust_color};font-weight:700;">{trust:.0f}/100</span>
        </div>
        <div style="height:4px;background:#f0f0f0;border-radius:4px;overflow:hidden;">
            <div style="height:100%;width:{trust}%;background:{trust_color};
                        border-radius:4px;transition:width 0.6s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_results_table(data: Dict[str, Any]):
    claims = data.get("claims", [])
    if not claims:
        st.markdown("""
        <div class="tl-err"><span>🌐</span>
        <div>No verifiable claims were returned. Try a PDF with statistics, dates, or factual assertions.</div>
        </div>""", unsafe_allow_html=True)
        return

    st.markdown(f"""
    <div class="tl-results-hd">
        <div class="tl-results-hd-title">Verification Intelligence</div>
        <div class="tl-results-hd-count">{len(claims)} claim{"s" if len(claims) != 1 else ""} analyzed</div>
    </div>
    """, unsafe_allow_html=True)

    for c in claims:
        verdict = c.get("verdict", "Unverifiable")
        badge_cls, badge_lbl, conf_color = VERDICT_MAP.get(verdict, ("b-u", "? Unverifiable", "#6b7280"))
        confidence = max(0.0, min(100.0, float(c.get("confidence", 0) or 0)))
        reasoning = (c.get("reasoning") or "").strip()
        sources = c.get("sources", []) or []

        raw_fact = (c.get("correct_fact") or "").strip()
        if raw_fact.lower() in ("", "nan", "null", "none", "n/a", "na"):
            raw_fact = ""
        # Never show Corrected Fact for Verified claims
        correct_fact = "" if verdict == "Verified" else raw_fact

        src_html = ""
        for s in sources:
            url = s.get("url", "")
            title = (s.get("title", "") or "Source")[:60]
            snippet = (s.get("snippet", "") or "")[:180]
            if url:
                src_html += f'<a class="tl-src-link" href="{url}" target="_blank">↗ {title}</a>'
            if snippet:
                src_html += f'<div style="font-size:0.7rem;color:#bbb;margin-bottom:4px;line-height:1.5">{snippet}</div>'
        if not src_html:
            src_html = '<span style="color:#ccc;font-size:0.75rem">No sources retrieved</span>'

        fact_block = f"""
        <div class="tl-mb">
            <div class="tl-mb-lbl">Corrected Fact</div>
            <div class="tl-mb-val" style="color:#d97706">{correct_fact}</div>
        </div>""" if correct_fact else ""

        reasoning_block = f"""
        <div class="tl-mb">
            <div class="tl-mb-lbl">AI Reasoning</div>
            <div class="tl-mb-val">{reasoning}</div>
        </div>""" if reasoning else ""

        st.markdown(f"""
        <div class="tl-claim">
            <div class="tl-claim-top">
                <div class="tl-claim-text">{c.get("claim", "")}</div>
                <span class="tl-badge {badge_cls}">{badge_lbl}</span>
            </div>
            <div class="tl-conf-row">
                <div class="tl-conf-lbl">Confidence</div>
                <div class="tl-conf-track">
                    <div class="tl-conf-fill" style="width:{confidence}%;background:{conf_color}"></div>
                </div>
                <div class="tl-conf-pct">{confidence:.0f}%</div>
            </div>
            <div class="tl-claim-meta">
                {fact_block}
                {reasoning_block}
                <div class="tl-mb">
                    <div class="tl-mb-lbl">Sources</div>
                    <div class="tl-mb-val">{src_html}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    _render_export(claims)


def _render_export(claims: list):
    rows = []
    for c in claims:
        rows.append({
            "Claim": c.get("claim", ""),
            "Verdict": c.get("verdict", ""),
            "Confidence (%)": f"{float(c.get('confidence', 0) or 0):.0f}",
            "Correct Fact": c.get("correct_fact", ""),
            "Reasoning": c.get("reasoning", ""),
            "Sources": " | ".join(
                s.get("url", "") for s in (c.get("sources") or []) if s.get("url")
            ),
        })
    df = pd.DataFrame(rows)
    csv = df.to_csv(index=False).encode("utf-8")

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([6, 2])
    with col2:
        st.download_button(
            label="↓ Export CSV",
            data=csv,
            file_name="truthlayer_verification.csv",
            mime="text/csv",
            use_container_width=True,
        )
