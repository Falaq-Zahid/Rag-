import streamlit as st

from document_store import add_uploaded_files, delete_file, list_files


def render_upload_section() -> None:
    panel = st.container(border=True)
    with panel:
        st.subheader("Documents")

        uploaded_files = st.file_uploader(
            "Add PDF files",
            type=["pdf"],
            accept_multiple_files=True,
            key="pdf_upload",
        )

        left, right = st.columns([1, 3])
        with left:
            process_clicked = st.button(
                "Process PDFs",
                type="primary",
                use_container_width=True,
                disabled=not uploaded_files,
            )
        with right:
            st.caption("Only new files are embedded. Existing PDFs stay indexed until you delete them here.")

        if process_clicked and uploaded_files:
            with st.spinner("Indexing only the new PDF files..."):
                result = add_uploaded_files(uploaded_files)

            if result["added"]:
                st.success(
                    f"Indexed {len(result['added'])} file(s) in {result['seconds']} seconds."
                )
            if result["skipped"]:
                st.info(f"Already indexed: {', '.join(result['skipped'])}")
            if result["errors"]:
                st.error("Some files could not be processed.")
                for error in result["errors"]:
                    st.warning(error)

        files = list_files()
        if not files:
            st.info("No documents indexed yet.")
        else:
            st.markdown("#### Indexed files")
            for item in files:
                row_left, row_right = st.columns([4, 1])
                with row_left:
                    st.markdown(
                        f"""
<div class="file-row">
  <div>
    <div class="file-title">{item.name}</div>
    <div class="file-meta">{item.pages} pages | {item.chunks} chunks | {item.size / 1024:.1f} KB</div>
  </div>
  <span class="status-ok">Indexed</span>
</div>
                    """,
                        unsafe_allow_html=True,
                    )
                with row_right:
                    if st.button(
                        "Delete", key=f"delete_{item.file_id}", use_container_width=True
                    ):
                        delete_file(item.file_id)
                        st.rerun()
