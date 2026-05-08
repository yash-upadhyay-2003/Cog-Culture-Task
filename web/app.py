import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import queue
import threading
import time

import streamlit as st

from components.results import render_results_table, render_summary_metrics
from components.status import STEPS, render_how_it_works
from components.upload import render_upload_section
from services.pipeline import run_verification

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TruthLayer AI",
    page_icon="T",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body { margin: 0 !important; padding: 0 !important; }
.stApp, [data-testid="stAppViewContainer"], .main {
    background: #f8f9fa !important;
    color: #111111 !important;
    font-family: 'Inter', sans-serif !important;
    overflow-x: hidden !important;
}
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stApp > header,
#MainMenu, footer { display: none !important; height: 0 !important; }
[data-testid="stSidebar"] { display: none !important; }

.main .block-container, div.block-container {
    padding-top: 0 !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
}

/* Navbar */
.tl-nav {
    position: sticky; top: 0; z-index: 999;
    background: #fff; border-bottom: 1px solid #e8e8e8;
    height: 60px; display: flex; align-items: center;
    justify-content: space-between;
    padding: 0 2.5rem; margin: 0 -2.5rem;
    width: calc(100% + 5rem);
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.tl-nav-left { display: flex; align-items: center; gap: 0.75rem; }
.tl-nav-logo {
    width: 30px; height: 30px; background: #111;
    border-radius: 8px; display: flex; align-items: center;
    justify-content: center; font-size: 0.85rem; font-weight: 800; color: #fff;
}
.tl-nav-brand { font-size: 0.95rem; font-weight: 700; color: #111; letter-spacing: -0.02em; }
.tl-nav-sep   { width: 1px; height: 18px; background: #e8e8e8; margin: 0 0.25rem; }
.tl-nav-sub   { font-size: 0.72rem; font-weight: 600; color: #999; letter-spacing: 0.08em; text-transform: uppercase; }
.tl-nav-right { display: flex; align-items: center; gap: 0.6rem; }
.tl-live-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: #f0fdf4; border: 1px solid #bbf7d0;
    border-radius: 20px; padding: 5px 12px;
    font-size: 0.72rem; font-weight: 600; color: #16a34a;
}
.tl-live-dot {
    width: 6px; height: 6px; background: #22c55e;
    border-radius: 50%; animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:0.5; transform:scale(0.8); }
}
.tl-github-pill {
    display: inline-flex; align-items: center; gap: 5px;
    background: #fff; border: 1px solid #e8e8e8;
    border-radius: 20px; padding: 5px 12px;
    font-size: 0.72rem; font-weight: 600; color: #555;
    text-decoration: none; transition: border-color 0.2s, color 0.2s;
}
.tl-github-pill:hover { border-color: #ccc; color: #111; }

/* Hero */
.tl-hero {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 3rem; padding: 2.5rem 0 2rem; align-items: center;
}
.tl-hero-title {
    font-size: clamp(2.4rem,4vw,3.4rem); font-weight: 800;
    color: #111; letter-spacing: -0.04em; line-height: 1.1; margin: 0 0 1rem;
}
.tl-hero-title .dim { color: #bbb; }
.tl-hero-sub { font-size: 0.9rem; color: #666; line-height: 1.7; margin-bottom: 1.2rem; max-width: 420px; }
.tl-pills { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.tl-pill {
    background: #fff; border: 1px solid #e8e8e8;
    border-radius: 20px; padding: 5px 12px;
    font-size: 0.72rem; font-weight: 600; color: #555;
}
.tl-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.tl-stat {
    background: #fff; border: 1px solid #e8e8e8; border-radius: 16px;
    padding: 1.2rem 1rem; text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04); transition: box-shadow 0.2s;
}
.tl-stat:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.tl-stat-ico { font-size: 1rem; margin-bottom: 0.5rem; display: block; }
.tl-stat-val { font-size: 1.8rem; font-weight: 800; color: #111; letter-spacing: -0.04em; line-height: 1; margin-bottom: 0.3rem; }
.tl-stat-lbl { font-size: 0.65rem; color: #999; text-transform: uppercase; letter-spacing: 0.07em; font-weight: 600; line-height: 1.4; }

/* Buttons */
.stButton > button {
    background: #111 !important; color: #fff !important; border: none !important;
    font-weight: 700 !important; font-size: 0.85rem !important;
    border-radius: 10px !important; padding: 0.65rem 1.8rem !important;
    letter-spacing: -0.01em !important; transition: all 0.2s !important;
    font-family: 'Inter', sans-serif !important; white-space: nowrap !important;
}
.stButton > button:hover {
    background: #333 !important; transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}
.stButton > button[kind="secondary"] {
    background: #fff !important; color: #555 !important; border: 1px solid #e8e8e8 !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #f8f9fa !important; color: #111 !important;
    transform: none !important; box-shadow: none !important;
}
[data-testid="stDownloadButton"] > button {
    background: #fff !important; color: #111 !important;
    border: 1px solid #e8e8e8 !important; font-weight: 600 !important;
    font-size: 0.82rem !important; border-radius: 10px !important; padding: 0.55rem 1.2rem !important;
}

/* How it works */
.tl-two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; margin-bottom: 0.8rem; }
.tl-info-card {
    background: #fff; border: 1px solid #e8e8e8; border-radius: 14px;
    padding: 1.2rem 1.4rem; box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.tl-info-card-head {
    display: flex; align-items: center; gap: 0.6rem;
    margin-bottom: 1rem; padding-bottom: 0.8rem; border-bottom: 1px solid #f0f0f0;
}
.tl-info-card-icon  { font-size: 0.9rem; color: #999; }
.tl-info-card-title { font-size: 0.88rem; font-weight: 700; color: #111; letter-spacing: -0.02em; }
.tl-step-row { display: flex; align-items: center; gap: 0.8rem; padding: 0.55rem 0; border-bottom: 1px solid #f5f5f5; }
.tl-step-row:last-child { border-bottom: none; }
.tl-step-num {
    width: 22px; height: 22px; background: #f5f5f5; border: 1px solid #e8e8e8;
    border-radius: 6px; display: flex; align-items: center; justify-content: center;
    font-size: 0.62rem; color: #999; font-weight: 700; flex-shrink: 0;
}
.tl-step-label { font-size: 0.82rem; color: #555; }
.tl-proc-row { display: flex; align-items: center; gap: 0.8rem; padding: 0.55rem 0; border-bottom: 1px solid #f5f5f5; }
.tl-proc-row:last-child { border-bottom: none; }
.tl-proc-icon-idle  { color: #ddd; font-size: 0.75rem; width: 16px; text-align: center; }
.tl-proc-label-idle { font-size: 0.82rem; color: #bbb; }

/* Processing card */
.tl-processing-card {
    background: #fff; border: 1px solid #e8e8e8; border-radius: 16px;
    padding: 1.6rem 1.8rem; margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.tl-proc-title { font-size: 0.9rem; font-weight: 700; color: #111; margin-bottom: 0.25rem; }
.tl-proc-sub   { font-size: 0.78rem; color: #999; margin-bottom: 1.2rem; }
.tl-proc-step  { display: flex; align-items: center; gap: 10px; padding: 0.55rem 0; border-bottom: 1px solid #f5f5f5; font-size: 0.82rem; }
.tl-proc-step:last-child { border-bottom: none; }
.tl-proc-step.done   { color: #999; }
.tl-proc-step.active { color: #111; font-weight: 600; }
.tl-proc-step.idle   { color: #ccc; }
.icon-done   { color: #22c55e; }
.icon-active { color: #f59e0b; }
.icon-idle   { color: #ddd; }

/* Progress bar */
.stProgress > div > div     { background: #f0f0f0 !important; height: 3px !important; border-radius: 3px !important; }
.stProgress > div > div > div { background: #111 !important; border-radius: 3px !important; }

/* Error */
.tl-err {
    background: #fff5f5; border: 1px solid #fecaca; border-radius: 12px;
    padding: 1rem 1.4rem; color: #dc2626; font-size: 0.82rem;
    display: flex; gap: 10px; align-items: flex-start; margin-bottom: 1rem;
}
[data-testid="stAlert"] { display: none !important; }

/* Metrics */
.tl-metrics { display: grid; grid-template-columns: repeat(7,1fr); gap: 8px; margin-bottom: 0.8rem; }
.tl-mc {
    background: #fff; border: 1px solid #e8e8e8; border-radius: 12px;
    padding: 0.9rem 0.5rem; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.tl-mc-val { font-size: 1.6rem; font-weight: 800; color: #111; letter-spacing: -0.04em; line-height: 1; margin-bottom: 0.3rem; }
.tl-mc-lbl { font-size: 0.6rem; color: #999; text-transform: uppercase; letter-spacing: 0.07em; font-weight: 600; }
.tl-mc.v .tl-mc-val { color: #16a34a; }
.tl-mc.i .tl-mc-val { color: #d97706; }
.tl-mc.f .tl-mc-val { color: #dc2626; }

/* Results header */
.tl-results-hd { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.8rem; }
.tl-results-hd-title { font-size: 0.95rem; font-weight: 700; color: #111; letter-spacing: -0.02em; }
.tl-results-hd-count { font-size: 0.7rem; color: #999; background: #f5f5f5; border: 1px solid #e8e8e8; padding: 3px 10px; border-radius: 20px; }

/* Claim cards */
.tl-claim {
    background: #fff; border: 1px solid #e8e8e8; border-radius: 12px;
    padding: 1rem 1.2rem; margin-bottom: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: box-shadow 0.2s, transform 0.2s;
}
.tl-claim:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); transform: translateY(-1px); }
.tl-claim-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; margin-bottom: 0.7rem; }
.tl-claim-text { font-size: 0.85rem; color: #333; line-height: 1.6; flex: 1; }
.tl-badge { font-size: 0.65rem; font-weight: 700; padding: 3px 10px; border-radius: 20px; white-space: nowrap; flex-shrink: 0; letter-spacing: 0.04em; }
.b-v { background: #f0fdf4; border: 1px solid #bbf7d0; color: #16a34a; }
.b-i { background: #fffbeb; border: 1px solid #fde68a; color: #d97706; }
.b-m { background: #fff7ed; border: 1px solid #fed7aa; color: #ea580c; }
.b-f { background: #fff5f5; border: 1px solid #fecaca; color: #dc2626; }
.b-u { background: #f9fafb; border: 1px solid #e5e7eb; color: #6b7280; }
.tl-conf-row { display: flex; align-items: center; gap: 10px; margin-bottom: 0.7rem; }
.tl-conf-lbl   { font-size: 0.65rem; color: #999; width: 72px; flex-shrink: 0; }
.tl-conf-track { flex: 1; height: 3px; background: #f0f0f0; border-radius: 3px; overflow: hidden; }
.tl-conf-fill  { height: 100%; border-radius: 3px; }
.tl-conf-pct   { font-size: 0.7rem; color: #999; width: 32px; text-align: right; flex-shrink: 0; }
.tl-claim-meta { display: flex; gap: 1.2rem; flex-wrap: wrap; }
.tl-mb { flex: 1; min-width: 180px; }
.tl-mb-lbl { font-size: 0.6rem; color: #bbb; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; margin-bottom: 0.25rem; }
.tl-mb-val { font-size: 0.78rem; color: #555; line-height: 1.5; }
.tl-src-link {
    color: #555; font-size: 0.75rem; text-decoration: none;
    border-bottom: 1px solid #e8e8e8; padding-bottom: 1px;
    margin-right: 10px; margin-bottom: 3px; display: inline-block; transition: color 0.2s;
}
.tl-src-link:hover { color: #111; border-bottom-color: #999; }

/* Footer */
.tl-footer {
    margin-top: 3rem; padding: 1.2rem 0; border-top: 1px solid #e8e8e8;
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;
}
.tl-footer-l { font-size: 0.72rem; color: #bbb; }
.tl-footer-r { font-size: 0.68rem; color: #ccc; }

/* Responsive */
@media (max-width: 1200px) {
    .main .block-container, div.block-container { padding-top:0 !important; padding-left:1.5rem !important; padding-right:1.5rem !important; }
    .tl-nav { padding:0 1.5rem; margin:0 -1.5rem; width:calc(100% + 3rem); }
}
@media (max-width: 991px) {
    .main .block-container, div.block-container { padding-top:0 !important; padding-left:1.2rem !important; padding-right:1.2rem !important; }
    .tl-nav { height:54px; padding:0 1.2rem; margin:0 -1.2rem; width:calc(100% + 2.4rem); }
    .tl-nav-sep, .tl-nav-sub { display:none; }
    .tl-hero { grid-template-columns:1fr 1fr; gap:1.5rem; padding:1.8rem 0 1.4rem; }
    .tl-hero-title { font-size:clamp(1.8rem,3.5vw,2.4rem); }
    .tl-stats { grid-template-columns:1fr 1fr; gap:8px; }
    .tl-metrics { grid-template-columns:repeat(4,1fr); }
    .tl-two-col { grid-template-columns:1fr 1fr; }
}
@media (max-width: 767px) {
    .main .block-container, div.block-container { padding-top:0 !important; padding-left:1rem !important; padding-right:1rem !important; }
    .tl-nav { height:52px; padding:0 1rem; margin:0 -1rem; width:calc(100% + 2rem); }
    .tl-nav-sep, .tl-nav-sub { display:none; }
    .tl-hero { grid-template-columns:1fr !important; gap:1rem; padding:1.2rem 0 1rem; }
    .tl-hero-title { font-size:clamp(2rem,8vw,2.8rem); }
    .tl-stats { grid-template-columns:1fr 1fr !important; }
    .tl-two-col { grid-template-columns:1fr !important; }
    .tl-metrics { grid-template-columns:repeat(2,1fr) !important; }
    .tl-claim-top { flex-direction:column; gap:0.5rem; }
    .tl-badge { align-self:flex-start; }
    .tl-claim-meta { flex-direction:column; gap:0.8rem; }
    .tl-mb { min-width:100%; }
    .tl-footer { flex-direction:column; gap:0.3rem; align-items:flex-start; }
    .stButton > button { width:100% !important; }
    [data-testid="stHorizontalBlock"] { flex-wrap:wrap !important; }
    [data-testid="stHorizontalBlock"] > div { min-width:100% !important; flex:1 1 100% !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Navbar ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tl-nav">
    <div class="tl-nav-left">
        <div class="tl-nav-logo">T</div>
        <span class="tl-nav-brand">TruthLayer AI</span>
        <div class="tl-nav-sep"></div>
        <span class="tl-nav-sub">Fact Verification Engine</span>
    </div>
    <div class="tl-nav-right">
        <div class="tl-live-pill">
            <div class="tl-live-dot"></div>
            Live Verification
        </div>
        <a class="tl-github-pill" href="https://github.com/yash-upadhyay-2003/Cog-Culture-Task" target="_blank">
            &#9095;&nbsp;GitHub
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tl-hero">
    <div>
        <h1 class="tl-hero-title">
            Verify Facts<br>
            <span class="dim">Before They</span><br>
            Spread.
        </h1>
        <p class="tl-hero-sub">
            AI-powered factual verification for PDFs, research
            documents, reports, and marketing claims.
        </p>
        <div class="tl-pills">
            <span class="tl-pill">&#9889; Powered by AI</span>
            <span class="tl-pill">&#129422; Llama 3</span>
        </div>
    </div>
    <div class="tl-stats">
        <div class="tl-stat">
            <span class="tl-stat-ico">&#9889;</span>
            <div class="tl-stat-val">10x</div>
            <div class="tl-stat-lbl">Faster Than<br>Manual</div>
        </div>
        <div class="tl-stat">
            <span class="tl-stat-ico">&#127760;</span>
            <div class="tl-stat-val">Live</div>
            <div class="tl-stat-lbl">Web<br>Evidence</div>
        </div>
        <div class="tl-stat">
            <span class="tl-stat-ico">&#129504;</span>
            <div class="tl-stat-val">LLM</div>
            <div class="tl-stat-lbl">Hybrid<br>Reasoning</div>
        </div>
        <div class="tl-stat">
            <span class="tl-stat-ico">&#10022;</span>
            <div class="tl-stat-val">4</div>
            <div class="tl-stat-lbl">Verdict<br>Types</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
for k, v in [
    ("results", None),
    ("error", None),
    ("processing", False),
    ("anim_step", 0),
    # q is a real Python queue.Queue object — shared by reference across reruns
    # This is the ONLY thread-safe way to pass data from a bg thread to Streamlit
    ("q", None),
]:
    if k not in st.session_state:
        st.session_state[k] = v

client = None  # no longer needed — using direct pipeline

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded_file, verify_clicked = render_upload_section()

# ── How it works ──────────────────────────────────────────────────────────────
render_how_it_works()

# ── Verify clicked: create queue, start background thread ────────────────────
if verify_clicked and uploaded_file and not st.session_state.processing:
    st.session_state.results    = None
    st.session_state.error      = None
    st.session_state.anim_step  = 0
    st.session_state.processing = True

    # Create a fresh queue and store it in session state
    # The background thread will put() exactly one item: ("ok", data) or ("err", msg)
    q = queue.Queue()
    st.session_state.q = q

    file_bytes = uploaded_file.getvalue()
    file_name  = uploaded_file.name

    def _call_api():
        try:
            result = run_verification(file_bytes, file_name)
            q.put(("ok", result))
        except Exception as e:
            q.put(("err", str(e)))

    threading.Thread(target=_call_api, daemon=True).start()
    st.rerun()

# ── Processing animation loop ─────────────────────────────────────────────────
if st.session_state.processing:
    q = st.session_state.q

    # Poll the queue — non-blocking
    try:
        status, payload = q.get_nowait()
        # Got a result — finalize
        if status == "ok":
            st.session_state.results = payload
            st.session_state.error   = None
        else:
            st.session_state.error   = payload
            st.session_state.results = None
        st.session_state.processing = False
        st.session_state.anim_step  = 0
        st.session_state.q          = None
        st.rerun()

    except queue.Empty:
        # API still running — render animation then rerun after delay
        step = st.session_state.anim_step
        rows = ""
        for j, s in enumerate(STEPS):
            if j < step:
                rows += (
                    f'<div class="tl-proc-step done">'
                    f'<span class="icon-done">&#10004;</span>{s}</div>'
                )
            elif j == step:
                rows += (
                    f'<div class="tl-proc-step active">'
                    f'<span class="icon-active">&#9676;</span>{s}</div>'
                )
            else:
                rows += (
                    f'<div class="tl-proc-step idle">'
                    f'<span class="icon-idle">&#9675;</span>{s}</div>'
                )

        st.markdown(f"""
        <div class="tl-processing-card">
            <div class="tl-proc-title">Analyzing Document</div>
            <div class="tl-proc-sub">Please wait while TruthLayer processes your PDF...</div>
            {rows}
        </div>
        """, unsafe_allow_html=True)
        st.progress(round((step + 1) / len(STEPS), 2))

        # Advance step, cap at last
        st.session_state.anim_step = min(step + 1, len(STEPS) - 1)
        time.sleep(0.9)
        st.rerun()

# ── Error ─────────────────────────────────────────────────────────────────────
if st.session_state.error:
    st.markdown(f"""
    <div class="tl-err">
        <span>&#9888;</span>
        <div>{st.session_state.error}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.results:
    render_summary_metrics(st.session_state.results)
    render_results_table(st.session_state.results)
    col1, _ = st.columns([1, 8])
    with col1:
        if st.button("Clear", type="secondary"):
            st.session_state.results = None
            st.session_state.error   = None
            st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tl-footer">
    <div class="tl-footer-l">TruthLayer AI &middot; v1.0 &middot; Stateless &middot; No data stored</div>
    <div class="tl-footer-r">FastAPI &middot; LLM &middot; Streamlit</div>
</div>
""", unsafe_allow_html=True)
