import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from config import DATA_FOLDER, MANIFEST_PATH


@dataclass(frozen=True)
class StoredFile:
    file_id: str
    name: str
    path: str
    size: int
    pages: int
    chunks: int
    created_at: float
    updated_at: float


def ensure_storage() -> None:
    DATA_FOLDER.mkdir(exist_ok=True)


def file_id_for_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_filename(name: str) -> str:
    clean = Path(name).name.replace("\\", "_").replace("/", "_")
    return clean or "document.pdf"


def display_name_from_path(path: Path) -> str:
    return re.sub(r"^[a-f0-9]{12}_", "", path.name)


def recover_manifest_from_saved_pdfs() -> dict:
    files = {}
    now = time.time()
    for path in DATA_FOLDER.glob("*.pdf"):
        try:
            data = path.read_bytes()
        except OSError:
            continue

        file_id = file_id_for_bytes(data)
        files[file_id] = {
            "name": display_name_from_path(path),
            "path": str(path),
            "size": len(data),
            "pages": 0,
            "chunks": 0,
            "created_at": path.stat().st_ctime,
            "updated_at": now,
        }
    return {"files": files}


def load_manifest() -> dict:
    ensure_storage()
    if not MANIFEST_PATH.exists():
        return recover_manifest_from_saved_pdfs()

    try:
        with MANIFEST_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return recover_manifest_from_saved_pdfs()

    if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
        return recover_manifest_from_saved_pdfs()
    if not data["files"]:
        recovered = recover_manifest_from_saved_pdfs()
        if recovered["files"]:
            save_manifest(recovered)
            return recovered
    return data


def save_manifest(manifest: dict) -> None:
    ensure_storage()
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)


def chunk_count(item: dict) -> int:
    if item.get("chunks"):
        return int(item.get("chunks", 0))

    indexes = item.get("indexes")
    if isinstance(indexes, dict) and isinstance(indexes.get("local"), dict):
        return int(indexes["local"].get("chunks", 0))

    return 0


def count_pdf_pages(path: Path) -> int:
    import fitz

    with fitz.open(str(path)) as pdf:
        return len(pdf)


def list_files() -> list[StoredFile]:
    manifest = load_manifest()
    files = []
    for file_id, item in manifest["files"].items():
        path = Path(item.get("path", ""))
        if not path.exists():
            continue
        files.append(
            StoredFile(
                file_id=file_id,
                name=item.get("name", path.name),
                path=str(path),
                size=int(item.get("size", 0)),
                pages=int(item.get("pages", 0)),
                chunks=chunk_count(item),
                created_at=float(item.get("created_at", 0)),
                updated_at=float(item.get("updated_at", 0)),
            )
        )
    return sorted(files, key=lambda item: item.created_at)


def stats() -> dict:
    files = list_files()
    return {
        "files": len(files),
        "pages": sum(item.pages for item in files),
        "chunks": sum(item.chunks for item in files),
        "size": sum(item.size for item in files),
    }


def add_uploaded_files(uploaded_files: Iterable) -> dict:
    ensure_storage()
    manifest = load_manifest()
    added = []
    skipped = []
    errors = []
    started = time.time()

    for uploaded_file in uploaded_files:
        data = uploaded_file.getbuffer().tobytes()
        file_id = file_id_for_bytes(data)
        original_name = safe_filename(uploaded_file.name)

        save_path = Path(manifest["files"].get(file_id, {}).get("path", ""))
        is_new_file = file_id not in manifest["files"] or not save_path.exists()

        try:
            from rag_engine import clean_indexing_error, has_file_in_database, index_pdf_file

            if (
                file_id in manifest["files"]
                and chunk_count(manifest["files"][file_id]) > 0
                and has_file_in_database(file_id)
            ):
                skipped.append(original_name)
                continue

            if is_new_file:
                save_name = f"{file_id[:12]}_{original_name}"
                save_path = DATA_FOLDER / save_name
                with save_path.open("wb") as f:
                    f.write(data)

            page_count = count_pdf_pages(save_path)
            chunks = index_pdf_file(save_path, file_id=file_id, source_name=original_name)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            if is_new_file:
                save_path.unlink(missing_ok=True)
            errors.append(f"{original_name}: {clean_indexing_error(exc)}")
            continue

        now = time.time()
        manifest["files"][file_id] = {
            "name": original_name,
            "path": str(save_path),
            "size": len(data),
            "pages": page_count,
            "chunks": chunks,
            "created_at": manifest["files"].get(file_id, {}).get("created_at", now),
            "updated_at": now,
        }
        added.append(original_name)

    save_manifest(manifest)
    return {
        "added": added,
        "skipped": skipped,
        "errors": errors,
        "seconds": round(time.time() - started, 2),
    }


def delete_file(file_id: str) -> bool:
    manifest = load_manifest()
    item = manifest["files"].pop(file_id, None)
    if not item:
        return False

    from rag_engine import delete_file_from_database

    delete_file_from_database(file_id)
    Path(item.get("path", "")).unlink(missing_ok=True)
    save_manifest(manifest)
    return True
