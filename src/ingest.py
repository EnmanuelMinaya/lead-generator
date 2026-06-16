import uuid
import logging
from datetime import datetime
from typing import Any, Dict

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pydantic import ValidationError

from models import MODEL_BY_TYPE

LOGGER = logging.getLogger(__name__)

# Module-level resources to be initialised at app startup
MODEL: SentenceTransformer = None
CHROMA_CLIENT: chromadb.PersistentClient = None
COLLECTION = None


def init_resources(persist_directory: str = "./chroma_db"):
    global MODEL, CHROMA_CLIENT, COLLECTION
    if MODEL is None:
        MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        LOGGER.info("Loaded embedding model all-MiniLM-L6-v2")

    if CHROMA_CLIENT is None:
        CHROMA_CLIENT = chromadb.PersistentClient(path=persist_directory)
        LOGGER.info("Initialised ChromaDB client with %s", persist_directory)

    try:
        COLLECTION = CHROMA_CLIENT.get_collection("browser_artifacts")
    except Exception:
        COLLECTION = CHROMA_CLIENT.create_collection("browser_artifacts")
    LOGGER.info("Using collection 'browser_artifacts'")


def safe_str(val: Any, fallback: str = "unknown") -> str:
    if val is None:
        return fallback
    if isinstance(val, str):
        return val.strip() if val.strip() != "" else fallback
    return str(val)


def safe_int(val: Any, fallback: int = -1) -> int:
    if val is None:
        return fallback
    try:
        return int(val)
    except Exception:
        return fallback


def serialise_artifact(model_obj) -> str:
    t = model_obj.artifact_type
    if t == "history":
        return (
            "Browser history record. User visited {page_title} at URL {url} on {visit_timestamp}. "
            "This page was visited {visit_count} time(s). Navigation type: {transition_type}. "
            "Browser: {browser}. Profile: {browser_profile}. User account: {os_user_account}."
        ).format(
            page_title=safe_str(model_obj.page_title, "untitled page"),
            url=safe_str(model_obj.url),
            visit_timestamp=safe_str(model_obj.visit_timestamp),
            visit_count=safe_int(model_obj.visit_count, 0),
            transition_type=safe_str(model_obj.transition_type, "unspecified"),
            browser=safe_str(model_obj.browser),
            browser_profile=safe_str(model_obj.browser_profile),
            os_user_account=safe_str(model_obj.os_user_account),
        )

    if t == "search":
        return (
            "Web search record. User searched for '{search_term}' using {search_engine} on {search_timestamp}. "
            "Search results page URL: {result_url}. Browser: {browser}. User account: {os_user_account}."
        ).format(
            search_term=safe_str(model_obj.search_term),
            search_engine=safe_str(model_obj.search_engine, "unspecified"),
            search_timestamp=safe_str(model_obj.search_timestamp),
            result_url=safe_str(model_obj.result_url, "unspecified"),
            browser=safe_str(model_obj.browser),
            os_user_account=safe_str(model_obj.os_user_account),
        )

    if t == "download":
        return (
            "File download record. User downloaded file '{filename}' ({mime_type}, {file_size_bytes} bytes) from {download_url} on {start_timestamp}. "
            "File saved to: {target_path}. Download initiated from: {referrer_url}. Download state: {download_state}. "
            "Browser risk classification: {danger_type}. Browser: {browser}. User account: {os_user_account}."
        ).format(
            filename=safe_str(model_obj.filename, "untitled"),
            mime_type=safe_str(model_obj.mime_type, "unknown"),
            file_size_bytes=safe_int(model_obj.file_size_bytes, -1),
            download_url=safe_str(model_obj.download_url),
            start_timestamp=safe_str(model_obj.start_timestamp),
            target_path=safe_str(model_obj.target_path),
            referrer_url=safe_str(model_obj.referrer_url, "unspecified"),
            download_state=safe_str(model_obj.download_state),
            danger_type=safe_str(model_obj.danger_type, "unspecified"),
            browser=safe_str(model_obj.browser),
            os_user_account=safe_str(model_obj.os_user_account),
        )

    if t == "bookmark":
        return (
            "Bookmark record. User bookmarked '{bookmark_title}' at URL {url} on {date_added}. Saved in folder: {folder_path}. "
            "Last used: {date_last_used}. Browser: {browser}. User account: {os_user_account}."
        ).format(
            bookmark_title=safe_str(model_obj.bookmark_title, "untitled bookmark"),
            url=safe_str(model_obj.url),
            date_added=safe_str(model_obj.date_added),
            folder_path=safe_str(model_obj.folder_path, "unspecified"),
            date_last_used=safe_str(model_obj.date_last_used, "unspecified"),
            browser=safe_str(model_obj.browser),
            os_user_account=safe_str(model_obj.os_user_account),
        )

    return ""


def make_metadata_from_model(model_obj) -> Dict[str, Any]:
    data = model_obj.dict()
    # Replace None with safe fallbacks and ensure ints are ints
    out: Dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, int):
            out[k] = v
        else:
            out[k] = safe_str(v)
    return out


def process_and_store(artifact_json: dict) -> dict:
    """Validate, serialise, embed, and store artifact. Returns dict with artifact_id and type."""
    artifact_type = artifact_json.get("artifact_type")
    ModelClass = MODEL_BY_TYPE.get(artifact_type)
    if ModelClass is None:
        raise ValueError(f"unknown artifact_type: {artifact_type}")

    # Validate
    model_obj = ModelClass(**artifact_json)

    artifact_id = str(uuid.uuid4())
    extraction_timestamp = datetime.utcnow().isoformat() + "Z"

    # Serialise
    document = serialise_artifact(model_obj)

    # Embed
    try:
        embedding = MODEL.encode([document])[0]
        # convert numpy to list if needed
        try:
            embedding = embedding.tolist()
        except Exception:
            embedding = list(embedding)
    except Exception as exc:
        LOGGER.exception("Embedding generation failed: %s", exc)
        raise

    # Metadata
    metadata = make_metadata_from_model(model_obj)
    metadata["artifact_id"] = artifact_id
    metadata["extraction_timestamp"] = extraction_timestamp

    # Store in ChromaDB
    try:
        COLLECTION.add(ids=[artifact_id], documents=[document], embeddings=[embedding], metadatas=[metadata])
        # persist to disk
        try:
            CHROMA_CLIENT.persist()
        except Exception:
            # Some chroma builds persist on create; ignore if not available
            pass
    except Exception as exc:
        LOGGER.exception("Failed to write to ChromaDB: %s", exc)
        raise

    return {"artifact_id": artifact_id, "artifact_type": artifact_type}


def get_collection_count() -> int:
    try:
        return COLLECTION.count()
    except Exception:
        try:
            # Fallback: fetch documents and count them
            res = COLLECTION.get(include=["documents"]) or {}
            docs = res.get("documents") or []
            return len(docs)
        except Exception:
            return 0
