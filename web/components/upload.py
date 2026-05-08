import streamlit as st


def render_upload_section() -> tuple:
    """
    Render the PDF upload section.

    Returns:
        Tuple of (uploaded_file, verify_clicked)
    """
    st.markdown("### Upload Document")
    st.markdown(
        "Upload a PDF containing factual claims. "
        "TruthLayer will extract, search, and verify each claim against live web sources.",
        unsafe_allow_html=False
    )

    uploaded_file = st.file_uploader(
        label="Choose a PDF file",
        type=["pdf"],
        help="Maximum file size: 20MB. Text-based PDFs only (not scanned images).",
        label_visibility="collapsed"
    )

    if uploaded_file:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**Selected:** `{uploaded_file.name}`")
            size_kb = len(uploaded_file.getvalue()) / 1024
            if size_kb > 1024:
                st.caption(f"Size: {size_kb / 1024:.1f} MB")
            else:
                st.caption(f"Size: {size_kb:.1f} KB")
        with col2:
            verify_clicked = st.button(
                "Verify Claims",
                type="primary",
                use_container_width=True
            )
    else:
        st.info("No file selected. Drop a PDF above to get started.")
        verify_clicked = False

    return uploaded_file, verify_clicked
