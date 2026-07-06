import streamlit as st

from document_store import add_uploaded_files, delete_file, list_files, process_saved_files


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

        files = list_files()
        has_unindexed_files = any(item.chunks == 0 for item in files)

        left, right = st.columns([1, 3])
        with left:
            process_clicked = st.button(
                "Process PDFs",
                type="primary",
                use_container_width=True,
                disabled=not uploaded_files and not has_unindexed_files,
            )
        with right:
            st.caption("New files and saved files missing the active embedding index are processed.")

        if process_clicked:
            with st.spinner("Indexing PDF files..."):
                result = {
                    "added": [],
                    "skipped": [],
                    "errors": [],
                    "seconds": 0,
                }
                if uploaded_files:
                    upload_result = add_uploaded_files(uploaded_files)
                    result["added"].extend(upload_result["added"])
                    result["skipped"].extend(upload_result["skipped"])
                    result["errors"].extend(upload_result["errors"])
                    result["seconds"] += upload_result["seconds"]

                if has_unindexed_files:
                    saved_result = process_saved_files()
                    result["added"].extend(saved_result["added"])
                    result["skipped"].extend(saved_result["skipped"])
                    result["errors"].extend(saved_result["errors"])
                    result["seconds"] += saved_result["seconds"]

                result["seconds"] = round(result["seconds"], 2)

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
                status_class = "status-ok" if item.chunks > 0 else "status-missing"
                status_label = "Indexed" if item.chunks > 0 else "Needs processing"
                row_left, row_right = st.columns([4, 1])
                with row_left:
                    st.markdown(
                        f"""
<div class="file-row">
  <div>
    <div class="file-title">{item.name}</div>
    <div class="file-meta">{item.pages} pages | {item.chunks} chunks | {item.size / 1024:.1f} KB</div>
  </div>
  <span class="{status_class}">{status_label}</span>
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
