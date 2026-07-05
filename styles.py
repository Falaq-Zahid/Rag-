import streamlit as st


def apply_styles() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #080a09;
    --panel: rgba(13, 18, 16, .78);
    --panel-strong: rgba(16, 24, 21, .92);
    --ink: #f7fffb;
    --muted: #b8c2bd;
    --line: rgba(113, 255, 196, .16);
    --line-strong: rgba(0, 245, 160, .34);
    --accent: #00f5a0;
    --accent-2: #2fae84;
    --danger: #ff6b6b;
}

html, body, [class*="css"] {
    font-family: "Inter", "Manrope", "Plus Jakarta Sans", system-ui, sans-serif;
}

html, body, #root, .stApp, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
}

.stApp {
    color: var(--ink);
    background:
        radial-gradient(circle at 26% 0%, rgba(0, 245, 160, .20), transparent 31rem),
        radial-gradient(circle at 82% 18%, rgba(47, 174, 132, .12), transparent 28rem),
        linear-gradient(rgba(255, 255, 255, .018) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, .018) 1px, transparent 1px),
        var(--bg);
    background-size: auto, auto, 34px 34px, 34px 34px, auto;
}

.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background-image: radial-gradient(rgba(0, 245, 160, .12) 1px, transparent 1px);
    background-size: 22px 22px;
    opacity: .16;
    mask-image: linear-gradient(to bottom, black, transparent 72%);
}

header[data-testid="stHeader"],
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"],
.stDeployButton {
    background: transparent !important;
}

header[data-testid="stHeader"] {
    background-color: rgba(8, 10, 9, .88) !important;
    backdrop-filter: blur(14px);
}

div[data-testid="stAppViewBlockContainer"] {
    background: transparent !important;
}

section[data-testid="stSidebar"] {
    background: rgba(5, 20, 14, .96);
    border-right: 1px solid var(--line);
}

section[data-testid="stSidebar"] * {
    color: var(--ink);
}

.block-container {
    max-width: 1180px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.app-hero {
    border: 1px solid rgba(0, 245, 160, .22);
    background:
        radial-gradient(circle at 18% 0%, rgba(0, 245, 160, .14), transparent 24rem),
        linear-gradient(135deg, rgba(0, 245, 160, .055), rgba(47, 174, 132, .025)),
        rgba(10, 15, 13, .72);
    box-shadow: 0 24px 80px rgba(0, 245, 160, .08), inset 0 1px 0 rgba(255, 255, 255, .05);
    backdrop-filter: blur(18px);
    padding: 28px;
    border-radius: 8px;
    margin-bottom: 18px;
}

.eyebrow {
    color: var(--accent);
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0;
    text-transform: uppercase;
}

.app-hero h1 {
    margin: 8px 0 8px;
    font-size: 42px;
    line-height: 1.1;
    letter-spacing: 0;
    color: var(--ink);
    font-weight: 800;
}

.app-hero p {
    color: var(--muted);
    font-size: 17px;
    max-width: 760px;
    margin: 0;
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin: 14px 0 22px;
}

.metric-card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 16px;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, .05);
    backdrop-filter: blur(16px);
}

.metric-card span {
    color: var(--muted);
    font-size: 13px;
}

.metric-card strong {
    display: block;
    margin-top: 8px;
    font-size: 24px;
    color: var(--ink);
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--line) !important;
    background: var(--panel) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, .045), 0 20px 60px rgba(0, 0, 0, .20);
    backdrop-filter: blur(16px);
}

div[data-testid="stVerticalBlockBorderWrapper"] > div,
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
    background: transparent !important;
}

.section-panel {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 20px;
    margin: 14px 0;
}

.section-panel h2, .section-panel h3,
h1, h2, h3 {
    color: var(--ink);
    font-weight: 800;
}

p, span, label, div, .stMarkdown, .stCaption {
    color: inherit;
}

label, .stMarkdown, [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"] {
    color: var(--muted) !important;
}

[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    color: var(--ink) !important;
}

.file-row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 16px;
    align-items: center;
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
    background: var(--panel-strong);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, .04);
}

.file-title {
    color: var(--ink);
    font-weight: 800;
    overflow-wrap: anywhere;
}

.file-meta {
    color: var(--muted);
    font-size: 13px;
    margin-top: 4px;
}

.status-ok {
    display: inline-flex;
    align-items: center;
    padding: 4px 8px;
    border-radius: 6px;
    background: rgba(0, 245, 160, .12);
    color: var(--accent);
    border: 1px solid rgba(0, 245, 160, .22);
    font-size: 12px;
    font-weight: 800;
}

.status-missing {
    display: inline-flex;
    align-items: center;
    padding: 4px 8px;
    border-radius: 6px;
    background: rgba(255, 180, 85, .12);
    color: #ffd08a;
    border: 1px solid rgba(255, 180, 85, .20);
    font-size: 12px;
    font-weight: 800;
}

.answer-box {
    background: var(--panel);
    border: 1px solid var(--line);
    border-left: 4px solid var(--accent);
    border-radius: 8px;
    padding: 18px;
}

.source-box {
    background: var(--panel-strong);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 12px;
    margin-top: 8px;
    color: var(--muted);
}

.source-box strong {
    color: var(--ink);
}

.stFileUploader {
    color: var(--muted) !important;
}

.stFileUploader section,
.stFileUploader [data-testid="stFileUploaderDropzone"] {
    background: rgba(16, 22, 20, .92) !important;
    border: 1px solid rgba(0, 245, 160, .18) !important;
    border-radius: 8px !important;
    color: var(--muted) !important;
}

.stFileUploader section:hover,
.stFileUploader [data-testid="stFileUploaderDropzone"]:hover {
    border-color: rgba(0, 245, 160, .68) !important;
    box-shadow: 0 0 24px rgba(0, 245, 160, .12) !important;
}

.stFileUploader section *,
.stFileUploader [data-testid="stFileUploaderDropzone"] * {
    color: var(--muted) !important;
}

.stFileUploader button,
.stFileUploader [data-testid="stBaseButton-secondary"] {
    background: rgba(8, 13, 11, .95) !important;
    border: 1px solid rgba(0, 245, 160, .48) !important;
    color: var(--accent) !important;
    border-radius: 8px !important;
    font-weight: 800 !important;
}

.stFileUploader button:hover,
.stFileUploader [data-testid="stBaseButton-secondary"]:hover {
    border-color: var(--accent) !important;
    box-shadow: 0 0 22px rgba(0, 245, 160, .18) !important;
}

.stButton > button {
    border-radius: 8px !important;
    font-weight: 800 !important;
    border: 1px solid rgba(0, 245, 160, .22) !important;
    background: rgba(12, 18, 16, .88) !important;
    color: var(--ink) !important;
}

.stButton > button p,
.stButton > button span {
    color: inherit !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent), #54ffc2) !important;
    border-color: rgba(0, 245, 160, .72) !important;
    color: #03110b !important;
    box-shadow: 0 0 24px rgba(0, 245, 160, .22) !important;
}
.stButton > button {
    font-size: 17px !important;
    padding: 0.65rem 1.2rem !important;
}

.stButton > button[kind="primary"] {
    color: #021208 !important;
    text-shadow: 0 1px 0 rgba(255, 255, 255, 0.15);
}

.stButton > button:disabled,
.stButton > button[disabled] {
    opacity: 0.85 !important;
    color: #021208 !important;
}

.stButton > button:disabled p,
.stButton > button[disabled] p {
    color: #021208 !important;
    opacity: 1 !important;
}

.stButton > button:hover {
    border-color: rgba(0, 245, 160, .70) !important;
    box-shadow: 0 0 28px rgba(0, 245, 160, .18) !important;
}

.stTextInput input, .stTextArea textarea {
    border-radius: 8px !important;
    background: rgba(12, 18, 16, .86) !important;
    border: 1px solid var(--line) !important;
    color: var(--ink) !important;
}

.stTextArea textarea::placeholder,
.stTextInput input::placeholder {
    color: rgba(184, 194, 189, .72) !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--line-strong) !important;
    box-shadow: 0 0 0 1px rgba(0, 245, 160, .22) !important;
}

.stAlert, div[data-testid="stNotification"] {
    color: var(--ink) !important;
}

.stAlert {
    background: rgba(13, 18, 16, .88) !important;
    border: 1px solid var(--line) !important;
    color: var(--ink) !important;
}

.stAlert * {
    color: var(--ink) !important;
}

div[data-baseweb="textarea"],
div[data-baseweb="input"] {
    background: transparent !important;
}

small, .stCaption, div[data-testid="stCaptionContainer"] {
    color: var(--muted) !important;
}

@media (max-width: 760px) {
    .app-hero h1 { font-size: 32px; }
    .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .file-row { grid-template-columns: 1fr; }
}
.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span,
.stButton > button[kind="primary"] div {
    color: #021208 !important;
    opacity: 1 !important;
    font-weight: 800 !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )
