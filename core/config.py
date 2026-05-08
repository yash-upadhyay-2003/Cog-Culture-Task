import os
from dotenv import load_dotenv

# Load .env from project root
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_root, ".env"))


def _get(key: str, default: str = "") -> str:
    # 1. .env / environment variable (primary)
    val = os.getenv(key)
    if val:
        return val
    # 2. Streamlit secrets (Streamlit Cloud fallback)
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return str(val)
    except Exception:
        pass
    return default


def get_groq_api_key() -> str:
    return _get("GROQ_API_KEY")

def get_model_primary() -> str:
    return _get("GROQ_MODEL_PRIMARY", "llama-3.3-70b-versatile")

def get_model_fallback() -> str:
    return _get("GROQ_MODEL_FALLBACK", "llama-3.1-8b-instant")

def get_max_claims() -> int:
    return int(_get("MAX_CLAIMS", "10"))

def get_search_results() -> int:
    return int(_get("SEARCH_RESULTS_PER_CLAIM", "4"))
