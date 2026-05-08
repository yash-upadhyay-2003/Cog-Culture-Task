import streamlit as st
import time


def render_processing_state(step: str, progress: float):
    """Render a processing status block with step description and progress bar."""
    st.markdown(f"**{step}**")
    st.progress(progress)


PROCESSING_STEPS = [
    (0.10, "Uploading document to API..."),
    (0.25, "Extracting text from PDF..."),
    (0.40, "Detecting factual claims with AI..."),
    (0.60, "Searching the web for evidence..."),
    (0.80, "Verifying claims with LLM reasoning..."),
    (0.95, "Generating verdicts..."),
]


def show_processing_animation(placeholder):
    """
    Show animated progress steps in a placeholder.
    Runs until replaced — caller should clear or overwrite the placeholder.
    """
    for progress, message in PROCESSING_STEPS:
        with placeholder.container():
            st.markdown(f"⏳ **{message}**")
            st.progress(progress)
        time.sleep(0.6)
    with placeholder.container():
        st.markdown("⏳ **Finalizing results...**")
        st.progress(0.99)
