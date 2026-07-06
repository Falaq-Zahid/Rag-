import json
import os
import re
import time
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHROMA_MODEL_CACHE,
    COLLECTION_NAME,
    DB_FOLDER,
    FASTEMBED_CACHE,
    FASTEMBED_MODEL,
    GROQ_GENERATION_MODEL,
    JINA_EMBEDDING_DIMENSIONS,
    JINA_EMBEDDING_MODEL,
    JINA_EMBEDDING_URL,
    MAX_CHUNK_CONTEXT_CHARS,
    MAX_TOTAL_CONTEXT_CHARS,
    RETRIEVAL_K,
    SYSTEM_PROMPT,
)

load_dotenv()
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

BATCH_SIZE = 100


class RetrievedDoc:
    def __init__(self, page_content: str, metadata: dict):
        self.page_content = page_content
        self.metadata = metadata or {}


def log(message: str) -> None:
    print(message, flush=True)


def total_seconds(timings: dict) -> float:
    return round(
        sum(value for value in timings.values() if isinstance(value, (int, float))),
        2,
    )


def clean_indexing_error(exc: Exception) -> str:
    message = str(exc).lower()
    if "jina" in message and ("api key" in message or "401" in message or "403" in message):
        return "Jina API key is missing, invalid, or not allowed. Please check JINA_API_KEY."
    if "jina" in message and ("rate" in message or "429" in message or "tokens" in message):
        return "Jina embedding limit reached. Please wait or top up your Jina API key."
    if "jina" in message and ("timeout" in message or "connection" in message or "network" in message):
        return "Jina embeddings API is not reachable right now. Please check your internet connection."
    if "fastembed model is not downloaded yet" in message:
        return "FastEmbed model is not downloaded yet, and download failed. Connect internet once so FastEmbed can cache the model locally."
    if (
        "getaddrinfo failed" in message
        or "connecterror" in message
        or "connection" in message
        or "network" in message
        or "huggingface" in message
    ):
        return "FastEmbed model is not downloaded yet, and download failed. Connect internet once so FastEmbed can cache the model locally."
    if "no space" in message or "disk" in message:
        return "FastEmbed could not cache the model because disk space is low."
    return "FastEmbed could not create embeddings for this PDF. Please try again."


def get_api_key() -> str | None:
    return os.getenv("GROQ_API_KEY")


def embedding_provider() -> str:
    provider = os.getenv("EMBEDDING_PROVIDER", "local").strip().lower()
    if provider not in {"local", "jina"}:
        return "local"
    return provider


def get_jina_api_key() -> str | None:
    return os.getenv("JINA_API_KEY") or os.getenv("JINA_TOKEN")


@lru_cache(maxsize=1)
def get_fastembed_model():
    from fastembed import TextEmbedding

    FASTEMBED_CACHE.mkdir(exist_ok=True)
    return TextEmbedding(
        model_name=FASTEMBED_MODEL,
        cache_dir=str(FASTEMBED_CACHE),
        lazy_load=True,
    )


@lru_cache(maxsize=1)
def get_cached_onnx_model():
    from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

    ONNXMiniLM_L6_V2.DOWNLOAD_PATH = str(
        CHROMA_MODEL_CACHE / "onnx_models" / "all-MiniLM-L6-v2"
    )
    return ONNXMiniLM_L6_V2()


def embed_with_jina(texts: list[str], task: str) -> list[list[float]]:
    api_key = get_jina_api_key()
    if not api_key:
        raise RuntimeError("Jina API key is missing. Add JINA_API_KEY to your environment.")

    payload = {
        "model": JINA_EMBEDDING_MODEL,
        "task": task,
        "normalized": True,
        "dimensions": JINA_EMBEDDING_DIMENSIONS,
        "input": texts,
    }
    request = urllib.request.Request(
        JINA_EMBEDDING_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "rag-knowledge-assistant/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Jina embeddings API error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Jina embeddings network error: {exc}") from exc

    rows = sorted(body.get("data", []), key=lambda item: item.get("index", 0))
    embeddings = [row.get("embedding") for row in rows]
    if len(embeddings) != len(texts) or any(not embedding for embedding in embeddings):
        raise RuntimeError("Jina embeddings API returned an unexpected response.")
    return embeddings


def embed_locally(texts: list[str]) -> list[list[float]]:
    try:
        return [embedding.tolist() for embedding in get_fastembed_model().embed(texts)]
    except Exception as fastembed_exc:
        try:
            embeddings = get_cached_onnx_model()(texts)
            return [
                embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
                for embedding in embeddings
            ]
        except Exception as fallback_exc:
            raise RuntimeError(clean_indexing_error(fastembed_exc)) from fallback_exc


def embed_texts(texts: list[str], task: str = "retrieval.passage") -> list[list[float]]:
    if embedding_provider() == "jina":
        try:
            log(f"[embed] provider=jina task={task} texts={len(texts)}")
            return embed_with_jina(texts, task)
        except Exception as exc:
            raise RuntimeError(clean_indexing_error(exc)) from exc
    log(f"[embed] provider=local task={task} texts={len(texts)}")
    return embed_locally(texts)


@lru_cache(maxsize=1)
def get_collection():
    import chromadb

    DB_FOLDER.mkdir(exist_ok=True)

    client = chromadb.PersistentClient(path=str(DB_FOLDER))
    collection_name = COLLECTION_NAME
    if embedding_provider() == "jina":
        collection_name = f"{COLLECTION_NAME}_jina"
    log(f"[chroma] provider={embedding_provider()} collection={collection_name}")
    return client.get_or_create_collection(name=collection_name)


@lru_cache(maxsize=1)
def get_groq_client():
    from groq import Groq

    api_key = get_api_key()
    if not api_key:
        return None
    return Groq(api_key=api_key)


def warm_up_resources() -> dict:
    started = time.perf_counter()
    get_collection()
    return {"warm_up": round(time.perf_counter() - started, 2)}


def _load_pdf(path: Path, file_id: str, source_name: str):
    from langchain_community.document_loaders import PyMuPDFLoader

    started = time.perf_counter()
    log(f"[index] loading PDF source={source_name}")
    loader = PyMuPDFLoader(str(path))
    documents = []
    for doc in loader.load():
        if not getattr(doc, "page_content", "").strip():
            continue
        doc.metadata.update(
            {
                "file_id": file_id,
                "source": source_name,
                "path": str(path),
            }
        )
        documents.append(doc)
    log(f"[index] loaded pages={len(documents)} source={source_name} seconds={round(time.perf_counter() - started, 2)}")
    return documents


def index_pdf_file(path: Path, file_id: str, source_name: str) -> int:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    total_started = time.perf_counter()
    log(f"[index] start source={source_name} provider={embedding_provider()}")
    documents = _load_pdf(path, file_id=file_id, source_name=source_name)
    if not documents:
        raise ValueError("No readable text found in this PDF.")

    started = time.perf_counter()
    log(f"[index] chunking source={source_name} chunk_size={CHUNK_SIZE} overlap={CHUNK_OVERLAP}")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)
    if not chunks:
        raise ValueError("No readable chunks found in this PDF.")
    log(f"[index] chunks={len(chunks)} source={source_name} seconds={round(time.perf_counter() - started, 2)}")

    ids = []
    texts = []
    metadatas = []
    for index, chunk in enumerate(chunks):
        metadata = dict(chunk.metadata)
        metadata["chunk_index"] = index
        ids.append(f"{file_id}:{index}")
        texts.append(chunk.page_content)
        metadatas.append(metadata)

    collection = get_collection()
    delete_file_from_database(file_id)
    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    for start in range(0, len(texts), BATCH_SIZE):
        end = start + BATCH_SIZE
        batch_texts = texts[start:end]
        batch_number = (start // BATCH_SIZE) + 1
        batch_started = time.perf_counter()
        log(f"[index] batch {batch_number}/{total_batches} embedding source={source_name} size={len(batch_texts)}")
        embeddings = embed_texts(batch_texts, task="retrieval.passage")
        log(f"[index] batch {batch_number}/{total_batches} upserting source={source_name}")
        collection.upsert(
            ids=ids[start:end],
            embeddings=embeddings,
            documents=batch_texts,
            metadatas=metadatas[start:end],
        )
        log(f"[index] batch {batch_number}/{total_batches} done source={source_name} seconds={round(time.perf_counter() - batch_started, 2)}")

    log(f"[index] done source={source_name} chunks={len(chunks)} total_seconds={round(time.perf_counter() - total_started, 2)}")
    return len(chunks)


def delete_file_from_database(file_id: str) -> None:
    collection = get_collection()
    existing = collection.get(where={"file_id": file_id})
    ids = existing.get("ids", [])
    if ids:
        collection.delete(ids=ids)


def has_file_in_database(file_id: str) -> bool:
    collection = get_collection()
    existing = collection.get(where={"file_id": file_id}, limit=1)
    return bool(existing.get("ids"))


def clean_llm_error(exc: Exception) -> str:
    message = str(exc).lower()
    if "quota" in message or "rate limit" in message or "429" in message:
        return "Groq API rate limit reached. Please wait a while or use another API key."
    if "api key" in message or "permission" in message or "403" in message or "401" in message:
        return "Groq API key is missing, invalid, or not allowed. Please check your .env file."
    if "timeout" in message or "connection" in message or "network" in message:
        return "Groq API is not reachable right now. Please check your internet connection and try again."
    if "model" in message and ("not found" in message or "decommissioned" in message):
        return "The selected Groq model is not available. Please update GROQ_GENERATION_MODEL in config.py."
    return "Groq could not generate an answer right now. Please try again."


def build_context(docs) -> str:
    parts = []
    total = 0
    for doc in docs:
        text = doc.page_content.strip()
        if not text:
            continue
        text = text[:MAX_CHUNK_CONTEXT_CHARS]
        remaining = MAX_TOTAL_CONTEXT_CHARS - total
        if remaining <= 0:
            break
        if len(text) > remaining:
            text = text[:remaining]
        source = doc.metadata.get("source", "Unknown")
        page = int(doc.metadata.get("page", 0)) + 1
        parts.append(f"Source: {source}, page {page}\n{text}")
        total += len(text)
    return "\n\n".join(parts)


def should_skip_retrieval(question: str) -> bool:
    text = " ".join(question.lower().strip().split())
    if not text:
        return True

    casual_phrases = {
        "hi",
        "hello",
        "hey",
        "hy",
        "salam",
        "assalamualaikum",
        "assalamu alaikum",
        "how are you",
        "how r u",
        "what is your name",
        "who are you",
        "what are you",
        "how can you help me",
        "i want some info",
        "thanks",
        "thank you",
        "ok",
        "okay",
    }
    if text in casual_phrases:
        return True

    meta_starts = (
        "your name",
        "tell me your name",
        "introduce yourself",
        "what can you do",
        "can you help",
    )
    return text.startswith(meta_starts)


def query_terms(question: str) -> list[str]:
    stop_words = {
        "who",
        "what",
        "where",
        "when",
        "why",
        "how",
        "is",
        "are",
        "was",
        "were",
        "the",
        "a",
        "an",
        "about",
        "tell",
        "me",
        "give",
        "info",
        "information",
        "details",
        "of",
        "on",
        "in",
    }
    terms = re.findall(r"[a-zA-Z0-9_]+", question.lower())
    return [term for term in terms if len(term) >= 3 and term not in stop_words]


def keyword_search_documents(question: str):
    terms = query_terms(question)
    if not terms:
        return []

    collection = get_collection()
    seen = set()
    docs = []
    for term in terms[:4]:
        result = collection.get(
            where_document={"$contains": term},
            limit=RETRIEVAL_K,
        )
        ids = result.get("ids", [])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])
        for doc_id, text, metadata in zip(ids, documents, metadatas):
            if doc_id in seen:
                continue
            seen.add(doc_id)
            docs.append(RetrievedDoc(text, metadata))
            if len(docs) >= RETRIEVAL_K:
                return docs
    return docs


def search_documents(question: str):
    timings = {}
    started = time.perf_counter()
    collection = get_collection()
    timings["load"] = round(time.perf_counter() - started, 2)

    started = time.perf_counter()
    docs = keyword_search_documents(question)
    if docs:
        timings["search"] = round(time.perf_counter() - started, 2)
        timings["search_mode"] = "keyword"
        return docs, timings

    result = collection.query(
        query_embeddings=embed_texts([question], task="retrieval.query"),
        n_results=RETRIEVAL_K,
    )
    timings["search"] = round(time.perf_counter() - started, 2)
    timings["search_mode"] = "vector"

    docs = []
    documents = result.get("documents", [[]])[0] if result.get("documents") else []
    metadatas = result.get("metadatas", [[]])[0] if result.get("metadatas") else []
    for text, metadata in zip(documents, metadatas):
        docs.append(RetrievedDoc(text, metadata))
    return docs, timings


def build_messages(question: str, docs: list[RetrievedDoc]) -> list[dict]:
    context = build_context(docs)
    user_prompt = f"Context:\n{context or 'No document context was used for this message.'}\n\nQuestion:\n{question}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def ask_rag(question: str):
    if not question.strip():
        return "Please enter a question.", [], {}

    api_key = get_api_key()
    if not api_key:
        return "Missing Groq API key. Add GROQ_API_KEY to your .env file.", [], {}

    if should_skip_retrieval(question):
        docs = []
        timings = {"load": 0.0, "search": 0.0}
    else:
        docs, timings = search_documents(question)
    if not docs:
        if not should_skip_retrieval(question):
            return "No indexed documents found. Upload and process a PDF first.", [], timings

    try:
        started = time.perf_counter()
        response = get_groq_client().chat.completions.create(
            model=GROQ_GENERATION_MODEL,
            messages=build_messages(question, docs),
            temperature=0.1,
            max_completion_tokens=512,
        )
        answer = response.choices[0].message.content or "Groq did not return any answer text."
        timings["answer"] = round(time.perf_counter() - started, 2)
    except Exception as exc:
        timings["answer"] = round(time.perf_counter() - started, 2)
        return clean_llm_error(exc), docs, timings

    timings["total"] = total_seconds(timings)
    return answer, docs, timings


def stream_rag_answer(question: str):
    if not question.strip():
        yield {"type": "error", "answer": "Please enter a question.", "docs": [], "timings": {}}
        return

    api_key = get_api_key()
    if not api_key:
        yield {
            "type": "error",
            "answer": "Missing Groq API key. Add GROQ_API_KEY to your .env file.",
            "docs": [],
            "timings": {},
        }
        return

    if should_skip_retrieval(question):
        docs = []
        timings = {"load": 0.0, "search": 0.0}
    else:
        docs, timings = search_documents(question)
    if not docs:
        if not should_skip_retrieval(question):
            yield {
                "type": "error",
                "answer": "No indexed documents found. Upload and process a PDF first.",
                "docs": [],
                "timings": timings,
            }
            return

    started = time.perf_counter()
    full_answer = ""
    try:
        stream = get_groq_client().chat.completions.create(
            model=GROQ_GENERATION_MODEL,
            messages=build_messages(question, docs),
            temperature=0.1,
            max_completion_tokens=512,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if not delta:
                continue
            full_answer += delta
            yield {"type": "token", "token": delta, "answer": full_answer, "docs": docs, "timings": timings}
    except Exception as exc:
        timings["answer"] = round(time.perf_counter() - started, 2)
        yield {"type": "error", "answer": clean_llm_error(exc), "docs": docs, "timings": timings}
        return

    timings["answer"] = round(time.perf_counter() - started, 2)
    timings["total"] = total_seconds(timings)
    yield {"type": "done", "answer": full_answer, "docs": docs, "timings": timings}
