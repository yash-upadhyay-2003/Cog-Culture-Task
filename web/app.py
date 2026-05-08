import streamlit as st
import threading
from web.services.api_client import TruthLayerClient
from web.components.upload import render_upload_section
from web.components.results import render_summary_metrics, render_results_table
from web.components.status import show_processing_animation

st.set_page_config(
    page_title="TruthLayer AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Dark theme overrides */
    .stApp {
        background-color: #0a0a0a;
        color: #f5f5f5;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1100px;
    }
    /* Header */
    .tl-header {
        border-bottom: 1px solid #1e1e1e;
        padding-bottom: 1.5rem;
        margin-bottom: 2rem;
    }
    .tl-title {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        color: #ffffff;
        margin: 0;
    }
    .tl-subtitle {
        font-size: 1rem;
        color: #888888;
        margin-top: 0.25rem;
    }
    .tl-badge {
        display: inline-block;
        background: #1a1a1a;
        border: 1px solid #2e2e2e;
        color: #aaaaaa;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: monospace;
        margin-left: 8px;
        vertical-align: middle;
    }
    /* Metric card overrides */
    [data-testid="metric-container"] {
        background: #111111;
        border: 1px solid #1e1e1e;
        border-radius: 8px;
        padding: 1rem;
    }
    /* Dataframe */
    .stDataFrame {
        border: 1px solid #1e1e1e;
        border-radius: 8px;
    }
    /* Expander */
    .streamlit-expanderHeader {
        background: #111111 !important;
        border: 1px solid #1e1e1e !important;
        border-radius: 6px !important;
        color: #f5f5f5 !important;
    }
    /* Buttons */
    .stButton > button[kind="primary"] {
        background: #ffffff;
        color: #000000;
        border: none;
        font-weight: 600;
        border-radius: 6px;
    }
    .stButton > button[kind="primary"]:hover {
        background: #e5e5e5;
        color: #000000;
    }
    /* Upload zone */
    [data-testid="stFileUploadDropzone"] {
        background: #0f0f0f;
        border: 2px dashed #2e2e2e;
        border-radius: 8px;
        color: #888888;
    }
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="tl-header">
    <p class="tl-title">TruthLayer AI <span class="tl-badge">v1.0</span></p>
    <p class="tl-subtitle">AI-powered fact-checking — upload a PDF, verify its claims against live web data.</p>
</div>
""", unsafe_allow_html=True)

if "results" not in st.session_state:
    st.session_state.results = None
if "error" not in st.session_state:
    st.session_state.error = None
if "processing" not in st.session_state:
    st.session_state.processing = False

client = TruthLayerClient()

with st.container():
    uploaded_file, verify_clicked = render_upload_section()

if verify_clicked and uploaded_file and not st.session_state.processing:
    st.session_state.results = None
    st.session_state.error = None
    st.session_state.processing = True

    status_placeholder = st.empty()

    anim_stop = threading.Event()

    def run_animation():
        show_processing_animation(status_placeholder)

    anim_thread = threading.Thread(target=run_animation, daemon=True)
    anim_thread.start()

    try:
        file_bytes = uploaded_file.getvalue()
        data = client.verify_pdf(file_bytes, uploaded_file.name)
        st.session_state.results = data
        st.session_state.error = None
    except ConnectionError as e:
        st.session_state.error = str(e)
    except TimeoutError as e:
        st.session_state.error = str(e)
    except ValueError as e:
        st.session_state.error = str(e)
    except Exception as e:
        st.session_state.error = f"Unexpected error: {str(e)}"
    finally:
        anim_stop.set()
        st.session_state.processing = False
        status_placeholder.empty()

    st.rerun()

if st.session_state.error:
    st.error(f"**Error:** {st.session_state.error}")

if st.session_state.results:
    data = st.session_state.results
    render_summary_metrics(data)
    render_results_table(data)

    st.markdown("---")
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Clear Results", type="secondary"):
            st.session_state.results = None
            st.session_state.error = None
            st.rerun()

elif not verify_clicked:
    st.markdown("---")
    st.markdown(
        "<p style='color:#555555; font-size:0.85rem;'>Upload a PDF and click <strong>Verify Claims</strong> to begin.</p>",
        unsafe_allow_html=True
    )
