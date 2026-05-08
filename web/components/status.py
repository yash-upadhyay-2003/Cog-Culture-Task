import streamlit as st
import time

STEPS = [
    "Extracting PDF text",
    "Detecting factual claims",
    "Searching live web",
    "Verifying evidence",
    "Generating verdicts",
]

HOW_IT_WORKS = [
    ("01", "Upload PDF"),
    ("02", "Extract Claims"),
    ("03", "Search Web"),
    ("04", "Generate Verdict"),
]


def render_how_it_works():
    hiw_rows = "".join([
        f'<div class="tl-step-row">'
        f'<div class="tl-step-num">{n}</div>'
        f'<div class="tl-step-label">{label}</div>'
        f'</div>'
        for n, label in HOW_IT_WORKS
    ])

    proc_rows = "".join([
        f'<div class="tl-proc-row">'
        f'<span class="tl-proc-icon-idle">○</span>'
        f'<span class="tl-proc-label-idle">{s}</span>'
        f'</div>'
        for s in STEPS
    ])

    st.markdown(f"""
    <div class="tl-two-col">
        <div class="tl-info-card">
            <div class="tl-info-card-head">
                <span class="tl-info-card-icon">🌐</span>
                <span class="tl-info-card-title">How It Works</span>
            </div>
            {hiw_rows}
        </div>
        <div class="tl-info-card">
            <div class="tl-info-card-head">
                <span class="tl-info-card-icon">🧠</span>
                <span class="tl-info-card-title">Processing Steps</span>
            </div>
            {proc_rows}
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_processing_animation(placeholder):
    for i in range(len(STEPS)):
        rows = ""
        for j, step in enumerate(STEPS):
            if j < i:
                rows += f'<div class="tl-proc-step done"><span class="icon-done">✔</span>{step}</div>'
            elif j == i:
                rows += f'<div class="tl-proc-step active"><span class="icon-active">◌</span>{step}</div>'
            else:
                rows += f'<div class="tl-proc-step idle"><span class="icon-idle">○</span>{step}</div>'

        with placeholder.container():
            st.markdown(f"""
            <div class="tl-processing-card">
                <div class="tl-proc-title">Analyzing Document</div>
                <div class="tl-proc-sub">Please wait while TruthLayer processes your PDF...</div>
                {rows}
            </div>
            """, unsafe_allow_html=True)
            st.progress(round((i + 1) / len(STEPS), 2))
        time.sleep(0.9)

    all_done = "".join([
        f'<div class="tl-proc-step done"><span class="icon-done">✔</span>{s}</div>'
        for s in STEPS
    ])
    with placeholder.container():
        st.markdown(f"""
        <div class="tl-processing-card">
            <div class="tl-proc-title">Finalizing Results</div>
            <div class="tl-proc-sub">Almost done...</div>
            {all_done}
        </div>
        """, unsafe_allow_html=True)
        st.progress(1.0)
