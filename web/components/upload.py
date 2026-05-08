import streamlit as st


def render_upload_section() -> tuple:
    st.markdown("""
    <style>
    /* ── Upload card ── */
    .tl-upload-card {
        background: #ffffff;
        border: 1px solid #e8e8e8;
        border-radius: 16px;
        padding: 1.6rem 1.8rem 1.2rem 1.8rem;
        margin-bottom: 0.6rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .tl-upload-head {
        display: flex; align-items: center; gap: 0.55rem;
        margin-bottom: 0.3rem;
    }
    .tl-upload-title {
        font-size: 0.95rem; font-weight: 700;
        color: #111; letter-spacing: -0.02em;
    }
    .tl-upload-desc {
        font-size: 0.82rem; color: #888;
        margin-bottom: 1rem; line-height: 1.5;
    }

    /* ── Native uploader styled as dashed dropzone ── */
    section[data-testid="stFileUploader"] {
        background: #fafafa !important;
        border: 1.5px dashed #d1d5db !important;
        border-radius: 12px !important;
        padding: 0 !important;
        margin: 0 !important;
        transition: border-color 0.2s !important;
    }
    section[data-testid="stFileUploader"]:hover {
        border-color: #9ca3af !important;
    }
    [data-testid="stFileUploadDropzone"] {
        background: transparent !important;
        border: none !important;
        padding: 2.2rem 1rem !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
    }
    [data-testid="stFileUploadDropzone"] svg {
        width: 2rem !important;
        height: 2rem !important;
        color: #9ca3af !important;
        margin-bottom: 0.6rem !important;
    }
    [data-testid="stFileUploadDropzone"] p,
    [data-testid="stFileUploadDropzone"] > div > div > p:first-child {
        color: #6b7280 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.1rem !important;
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stFileUploadDropzone"] small,
    [data-testid="stFileUploadDropzone"] span {
        color: #9ca3af !important;
        font-size: 0.72rem !important;
    }
    [data-testid="stFileUploadDropzone"] button {
        background: #ffffff !important;
        border: 1px solid #e8e8e8 !important;
        color: #555 !important;
        font-size: 0.75rem !important;
        border-radius: 8px !important;
        padding: 0.3rem 0.9rem !important;
        margin-top: 0.6rem !important;
        cursor: pointer !important;
        transition: border-color 0.2s, color 0.2s !important;
    }
    [data-testid="stFileUploadDropzone"] button:hover {
        border-color: #9ca3af !important;
        color: #111 !important;
    }
    [data-testid="stFileUploaderFileName"] {
        color: #555 !important;
        font-size: 0.78rem !important;
    }

    /* ── Footer row ── */
    .tl-upload-footer {
        display: flex; align-items: center;
        justify-content: space-between;
        flex-wrap: wrap; gap: 0.5rem;
        margin-top: 0.9rem;
    }
    .tl-upload-hint {
        display: flex; align-items: center; gap: 6px;
        font-size: 0.75rem; color: #9ca3af;
    }
    .tl-file-ready {
        display: inline-flex; align-items: center; gap: 8px;
        background: #f9fafb; border: 1px solid #e8e8e8;
        border-radius: 8px; padding: 0.4rem 0.9rem;
        font-size: 0.78rem; color: #555;
    }
    .tl-file-sz { color: #9ca3af; font-size: 0.7rem; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="tl-upload-card">
        <div class="tl-upload-head">
            <span style="font-size:1rem">📄</span>
            <span class="tl-upload-title">Upload Your Document</span>
        </div>
        <p class="tl-upload-desc">
            Upload a PDF containing factual claims. We'll extract, verify, and show you the truth.
        </p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        label="Upload PDF",
        type=["pdf"],
        label_visibility="collapsed",
    )

    verify_clicked = False

    if uploaded_file:
        size_kb = len(uploaded_file.getvalue()) / 1024
        size_str = f"{size_kb/1024:.1f} MB" if size_kb > 1024 else f"{size_kb:.1f} KB"
        col1, col2 = st.columns([5, 2])
        with col1:
            st.markdown(f"""
            <div class="tl-upload-footer">
                <div class="tl-file-ready">
                    <span>📄</span>
                    <span>{uploaded_file.name}</span>
                    <span class="tl-file-sz">{size_str}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            verify_clicked = st.button("✦ Verify Claims", type="primary", use_container_width=True)
    else:
        st.markdown("""
        <div class="tl-upload-footer">
            <div class="tl-upload-hint">
                <span>📄</span>
                <span>Supports PDF &nbsp;·&nbsp; Max 200MB</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    return uploaded_file, verify_clicked
