# RAG Knowledge Assistant

A private, locally indexed Retrieval-Augmented Generation (RAG) assistant for uploading PDF documents, indexing them into a persistent local vector database, and asking questions with document-backed answers.

Upload PDFs once, keep them indexed across refreshes and app restarts, then ask questions from your private knowledge base with page-level sources and in-session chat history.

## Features

- PDF upload and indexing: Upload one or more PDF files from the Streamlit UI.
- Persistent document storage: Uploaded PDFs and metadata are tracked locally.
- Duplicate detection: Files are hashed on upload so the same PDF is not indexed repeatedly.
- Local embeddings: The app tries FastEmbed first and can fall back to a cached local Chroma ONNX embedding model.
- Persistent vector database: ChromaDB stores document chunks locally.
- Groq-powered answers: Uses Groq for LLM response generation.
- Streaming responses: Answers stream into the UI token by token.
- Source citations: Retrieved source files and page numbers are shown with answers.
- Chat history: Questions and answers stay visible during the current Streamlit session.
- Custom dark UI: Streamlit interface styled with a dark neon-green theme.

## Architecture Overview

```text
PDF Upload
   |
   v
PyMuPDF PDF Loading
   |
   v
LangChain RecursiveCharacterTextSplitter
   |
   v
FastEmbed / Cached Local ONNX Embeddings
   |
   v
ChromaDB Persistent Vector Store
   |
   v
User Question
   |
   v
Keyword Search or Vector Retrieval
   |
   v
Groq LLM Generation
   |
   v
Streamed Answer + Sources
```

## Tech Stack

| Component | Technology |
| --- | --- |
| UI Framework | Streamlit |
| PDF Parsing | PyMuPDF via LangChain community loader |
| Text Splitting | LangChain Text Splitters |
| Embeddings | FastEmbed with cached local ONNX fallback |
| Vector Database | ChromaDB |
| LLM Provider | Groq SDK |
| Environment Config | python-dotenv |
| Language | Python |

## Project Structure

```text
rag_project/
├── app.py              # Main Streamlit app
├── config.py           # Paths, model names, chunk settings, prompt
├── document_store.py   # Upload persistence, manifest, deduplication, delete flow
├── rag_engine.py       # Embeddings, indexing, retrieval, Groq generation
├── upload_section.py   # Streamlit upload/indexed-files UI
├── styles.py           # Custom CSS theme
├── requirements.txt    # Python dependencies
├── .gitignore          # Local data/cache/secrets exclusions
├── data/               # Uploaded PDFs and manifest, excluded from Git
├── chroma_db/          # ChromaDB storage, excluded from Git
├── chroma_model_cache/ # Cached local embedding model, excluded from Git
└── fastembed_cache/    # FastEmbed model cache, excluded from Git
```

## Getting Started

### Prerequisites

- Python 3.10+
- A Groq API key

### Installation

1. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

4. Run the app:

```bash
streamlit run app.py
```

5. Open the app:

```text
http://localhost:8501
```

Upload a PDF, click `Process PDFs`, then ask questions from the indexed documents.

## Configuration

Main settings live in `config.py`.

| Setting | Description |
| --- | --- |
| `APP_TITLE` | Streamlit page title |
| `DATA_FOLDER` | Local folder for uploaded files and manifest |
| `DB_FOLDER` | Local ChromaDB folder |
| `CHROMA_MODEL_CACHE` | Cache folder for Chroma ONNX fallback model |
| `FASTEMBED_CACHE` | Cache folder for FastEmbed model files |
| `MANIFEST_PATH` | JSON manifest path for indexed files |
| `COLLECTION_NAME` | Active ChromaDB collection name |
| `FASTEMBED_MODEL` | FastEmbed model name |
| `GROQ_GENERATION_MODEL` | Groq model used for answer generation |
| `CHUNK_SIZE` | Character length of each text chunk |
| `CHUNK_OVERLAP` | Overlap between chunks |
| `RETRIEVAL_K` | Number of chunks retrieved per question |
| `MAX_CHUNK_CONTEXT_CHARS` | Max characters used per retrieved chunk |
| `MAX_TOTAL_CONTEXT_CHARS` | Max total context sent to the LLM |
| `SYSTEM_PROMPT` | Assistant behavior and grounding instructions |

## Notes About Embeddings

FastEmbed must download its model files once before it can run fully from cache. If FastEmbed cannot download because of internet or DNS issues, the app can use the existing cached local Chroma ONNX embedding model as a fallback.

After a model is cached, embedding generation runs locally.

## Privacy

- Uploaded PDFs are stored locally in `data/`.
- Vector data is stored locally in `chroma_db/`.
- Embedding model files are cached locally.
- Retrieved document context is sent to Groq when generating answers.
- `.env`, uploaded files, vector database files, and model caches are excluded from Git by `.gitignore`.

## License

This project is for personal and educational use.

## Author

Built by Falaq Zahid.
