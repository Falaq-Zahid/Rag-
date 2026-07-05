import streamlit as st

from config import APP_TITLE
from document_store import stats
from styles import apply_styles
from upload_section import render_upload_section


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="R",
    layout="wide",
)

apply_styles()

current_stats = stats()

if current_stats["files"] > 0 and not st.session_state.get("search_warmed"):
    with st.spinner("Warming up local search engine..."):
        try:
            from rag_engine import warm_up_resources

            st.session_state.search_timings = warm_up_resources()
            st.session_state.search_warmed = True
        except Exception:
            st.session_state.search_warmed = False

st.markdown(
    """
<div class="app-hero">
  <div class="eyebrow">Local document intelligence</div>
  <h1>RAG Knowledge Assistant</h1>
  <p>Upload PDFs once, keep them indexed across refreshes and app restarts, then ask grounded questions from your private knowledge base.</p>
</div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="metric-grid">
  <div class="metric-card"><span>Files</span><strong>{current_stats["files"]}</strong></div>
  <div class="metric-card"><span>Pages</span><strong>{current_stats["pages"]}</strong></div>
  <div class="metric-card"><span>Chunks</span><strong>{current_stats["chunks"]}</strong></div>
  <div class="metric-card"><span>Storage</span><strong>{current_stats["size"] / 1024 / 1024:.1f} MB</strong></div>
</div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("search_warmed"):
    warm_seconds = st.session_state.get("search_timings", {}).get("warm_up")
    if warm_seconds is not None:
        st.caption(f"Search engine warmed up in {warm_seconds}s. First question should be faster now.")

render_upload_section()

ask_panel = st.container(border=True)
with ask_panel:
    st.subheader("Ask")

    question = st.text_area(
        "Question",
        placeholder="Ask anything from the indexed PDFs...",
        height=95,
        label_visibility="collapsed",
    )

    ask_clicked = st.button(
        "Ask question",
        type="primary",
        use_container_width=True,
        disabled=current_stats["files"] == 0,
    )

    if current_stats["files"] == 0:
        st.caption("Index at least one PDF to enable question answering.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if ask_clicked and question.strip():
    answer_panel = st.container(border=True)
    with answer_panel:
        st.markdown("### Answer")
        answer_placeholder = st.empty()
        timing_placeholder = st.empty()

    docs = []
    timings = {}
    answer = ""
    try:
        from rag_engine import stream_rag_answer

        with st.spinner("Searching your indexed documents..."):
            stream = stream_rag_answer(question)

        for event in stream:
            docs = event.get("docs", docs)
            timings = event.get("timings", timings)
            if event["type"] == "token":
                answer = event["answer"]
                answer_placeholder.write(answer + " |")
            else:
                answer = event["answer"]
                answer_placeholder.write(answer)
    except Exception:
        answer = "Something went wrong while searching your documents. Please try again."
        answer_placeholder.write(answer)

    st.session_state.chat_history.append(
        {
            "question": question,
            "answer": answer,
            "docs": docs,
            "timings": timings,
        }
    )

    st.rerun()

# Render full conversation history, most recent first
for index, exchange in enumerate(reversed(st.session_state.chat_history)):
    is_latest = index == 0
    question_text = exchange["question"].strip()

    if is_latest:
        history_panel = st.container(border=True)
        with history_panel:
            st.markdown(f"**Q: {question_text}**")
            st.markdown("### Answer")
            st.write(exchange["answer"])

            if exchange["timings"]:
                timing_text = " | ".join(
                    f"{name}: {seconds}s" if isinstance(seconds, (int, float)) else f"{name}: {seconds}"
                    for name, seconds in exchange["timings"].items()
                )
                st.caption(f"Timing: {timing_text}")

            if exchange["docs"]:
                st.markdown("### Sources")
                for doc in exchange["docs"]:
                    source = doc.metadata.get("source", "Unknown")
                    page = int(doc.metadata.get("page", 0)) + 1
                    st.markdown(
                        f"""
<div class="source-box">
  <strong>{source}</strong><br>
  Page {page}
</div>
                        """,
                        unsafe_allow_html=True,
                    )
    else:
        history_panel = st.container(border=True)
        with history_panel:
            st.markdown(
                f"""
<div style="opacity:0.75; font-size:0.85rem;">
  <strong>Q:</strong> {question_text}<br><br>
  <strong>A:</strong> {exchange['answer']}
</div>
                """,
                unsafe_allow_html=True,
            )

if st.session_state.chat_history:
    if st.button("Clear chat"):
        st.session_state.chat_history = []
        st.rerun()