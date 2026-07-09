import inspect
import json
import logging
import math
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

import ingest

load_dotenv()
LOGGER = logging.getLogger(__name__)

LLM_CLIENT: OpenAI = None

# Configuration from environment variables
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))
LLM_REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", "200"))
ARTIFACT_TYPE_ORDER = ["history", "search", "download", "bookmark"]
DECOMPOSITION_SYSTEM_PROMPT = """You are a query decomposition assistant for a digital forensics retrieval system. Your job is to break down an investigator's question into a set of specific sub-queries that will be used to retrieve browser artifacts from a vector database.

The database contains four artifact types:
- history: browser page visits with URLs, page titles, timestamps, navigation type (TYPED/LINK/FORM_SUBMIT)
- search: web search queries with search terms, search engine, timestamp
- download: downloaded files with filename, URL, file size, danger classification, save path
- bookmark: saved bookmarks with title, URL, folder path, date added

Rules:
- Always generate exactly 4 sub-queries, one targeting each artifact type.
- Each sub-query should be a short natural language phrase (5-10 words) that describes what to look for in that artifact type given the investigator's question.
- If the question is not relevant to a particular artifact type, generate a broad fallback sub-query for that type anyway (e.g. "all bookmark records saved").
- Respond ONLY with a valid JSON object, no preamble, no markdown fences:
{
  "history_query": "string",
  "search_query": "string",
  "download_query": "string",
  "bookmark_query": "string"
}
"""


def init_llm_client():
    global LLM_CLIENT
    if LLM_CLIENT is None:
        LLM_CLIENT = OpenAI(
            base_url=LLM_BASE_URL,
            api_key=LLM_API_KEY,
        )
        LOGGER.info("Initialised LLM client: base_url=%s, model=%s", LLM_BASE_URL, LLM_MODEL)


def _resolve_use_decomposition(use_decomposition: Optional[bool]) -> bool:
    if use_decomposition is not None:
        return use_decomposition

    frame = inspect.currentframe()
    try:
        caller_locals = frame.f_back.f_locals if frame and frame.f_back else {}
        for key in ("req", "request", "payload", "query_request"):
            candidate = caller_locals.get(key)
            if candidate is not None and hasattr(candidate, "use_decomposition"):
                return bool(getattr(candidate, "use_decomposition"))
    finally:
        del frame

    return True


def decompose_question(question: str) -> Dict[str, str]:
    """Decompose the investigator question into four targeted sub-queries."""
    fallback_queries = {artifact_type: question for artifact_type in ARTIFACT_TYPE_ORDER}

    messages = [
        {"role": "system", "content": DECOMPOSITION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Decompose this question: {question}"},
    ]

    try:
        llm_response, _ = call_llm(messages, timeout=LLM_REQUEST_TIMEOUT)
    except Exception as exc:
        LOGGER.warning("Question decomposition LLM call failed; falling back to the original question for all artifact types: %s", exc)
        return fallback_queries

    try:
        parsed = json.loads(llm_response)
    except json.JSONDecodeError as exc:
        LOGGER.warning("Question decomposition response was not valid JSON; falling back to the original question for all artifact types: %s", exc)
        # Fallback to the original question for all four artifact types if the decomposition response is malformed.
        return fallback_queries

    if not isinstance(parsed, dict):
        LOGGER.warning("Question decomposition response was not an object; falling back to the original question for all artifact types")
        return fallback_queries

    decomposed = {}
    for artifact_type in ARTIFACT_TYPE_ORDER:
        query_key = f"{artifact_type}_query"
        query_value = parsed.get(query_key)
        if isinstance(query_value, str) and query_value.strip():
            decomposed[artifact_type] = query_value.strip()
        else:
            decomposed[artifact_type] = question

    return decomposed


def get_subquery_allocations(top_k: int) -> Dict[str, int]:
    """Compute per-type subquery sizes while preserving a minimum slot count per type."""
    allocations = {}
    base = top_k / 2
    for artifact_type, ratio in {
        "history": 0.35,
        "search": 0.30,
        "download": 0.20,
        "bookmark": 0.15,
    }.items():
        allocations[artifact_type] = max(2, math.ceil(base * ratio))
    return allocations


def embed_question(question: str) -> List[float]:
    """Embed the investigator's question using the shared embedding model."""
    embedding = ingest.MODEL.encode([question])[0]
    try:
        embedding = embedding.tolist()
    except Exception:
        embedding = list(embedding)
    return embedding


def build_where_filter(autopsy_case_id: str, artifact_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Build a ChromaDB where clause to filter by case and optionally by artifact types.
    Combines multiple conditions with $and if needed.
    """
    filters = [{"autopsy_case_id": autopsy_case_id}]

    if artifact_types:
        filters.append({"artifact_type": {"$in": artifact_types}})

    if len(filters) == 1:
        return filters[0]
    else:
        return {"$and": filters}


def retrieve_artifacts(
    question_embedding: List[float],
    autopsy_case_id: str,
    artifact_types: Optional[List[str]] = None,
    top_k: int = 10,
) -> tuple:
    """
    Query ChromaDB for the most relevant artifacts.
    Returns (artifacts_list, artifact_ids_set).
    """
    where_filter = build_where_filter(autopsy_case_id, artifact_types)

    try:
        result = ingest.COLLECTION.query(
            query_embeddings=[question_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        LOGGER.exception("ChromaDB query failed: %s", exc)
        raise

    artifacts = []
    artifact_ids = set()

    if result and result["ids"] and len(result["ids"]) > 0:
        for i, aid in enumerate(result["ids"][0]):
            artifact_ids.add(aid)
            doc = result["documents"][0][i] if result["documents"] else ""
            meta = result["metadatas"][0][i] if result["metadatas"] else {}

            artifacts.append(
                {
                    "id": aid,
                    "document": doc,
                    "metadata": meta,
                }
            )

    return artifacts, artifact_ids


def retrieve_artifacts_decomposed(
    question: str,
    autopsy_case_id: str,
    artifact_types: Optional[List[str]] = None,
    top_k: int = 10,
) -> tuple:
    """Run four decomposed subqueries against ChromaDB and merge the results."""
    sub_queries = decompose_question(question)
    allocations = get_subquery_allocations(top_k)

    artifacts_by_type = {artifact_type: [] for artifact_type in ARTIFACT_TYPE_ORDER}
    retrieved_per_type = {artifact_type: 0 for artifact_type in ARTIFACT_TYPE_ORDER}
    selected_types = list(artifact_types) if artifact_types else ARTIFACT_TYPE_ORDER

    for artifact_type in ARTIFACT_TYPE_ORDER:
        if artifact_types and artifact_type not in selected_types:
            continue

        sub_query = sub_queries[artifact_type]
        embedding = embed_question(sub_query)
        where_filter = {
            "$and": [
                {"autopsy_case_id": {"$eq": autopsy_case_id}},
                {"artifact_type": {"$eq": artifact_type}},
            ]
        }

        try:
            result = ingest.COLLECTION.query(
                query_embeddings=[embedding],
                n_results=allocations[artifact_type],
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            LOGGER.exception("ChromaDB query failed for %s sub-query: %s", artifact_type, exc)
            continue

        if result and result["ids"] and len(result["ids"]) > 0:
            for i, aid in enumerate(result["ids"][0]):
                doc = result["documents"][0][i] if result["documents"] else ""
                meta = result["metadatas"][0][i] if result["metadatas"] else {}
                artifacts_by_type[artifact_type].append({"id": aid, "document": doc, "metadata": meta})

        retrieved_per_type[artifact_type] = len(artifacts_by_type[artifact_type])

    merged_artifacts = []
    seen_artifact_ids = set()
    for artifact_type in ARTIFACT_TYPE_ORDER:
        for artifact in artifacts_by_type[artifact_type]:
            artifact_id = artifact.get("id")
            if artifact_id in seen_artifact_ids:
                continue
            seen_artifact_ids.add(artifact_id)
            merged_artifacts.append(artifact)

    merged_artifacts.sort(key=lambda artifact: (0, get_timestamp_for_artifact(artifact)) if get_timestamp_for_artifact(artifact) not in {"", "unknown", None} else (1, ""))
    artifact_ids_set = {artifact["id"] for artifact in merged_artifacts}

    return merged_artifacts, artifact_ids_set, retrieved_per_type, sub_queries


def get_timestamp_for_artifact(artifact: Dict[str, Any]) -> str:
    """Extract the most relevant timestamp based on artifact type."""
    meta = artifact.get("metadata", {})
    artifact_type = meta.get("artifact_type", "unknown")

    if artifact_type == "history":
        return meta.get("visit_timestamp", "unknown")
    elif artifact_type == "search":
        return meta.get("search_timestamp", "unknown")
    elif artifact_type == "download":
        return meta.get("start_timestamp", "unknown")
    elif artifact_type == "bookmark":
        return meta.get("date_added", "unknown")
    else:
        return "unknown"


def format_artifact_context(artifacts: List[Dict[str, Any]]) -> str:
    """Build the numbered list of artifacts for LLM context."""
    lines = []
    for idx, artifact in enumerate(artifacts, start=1):
        aid = artifact["id"]
        doc = artifact["document"]
        meta = artifact["metadata"]
        artifact_type = meta.get("artifact_type", "unknown")
        ts = get_timestamp_for_artifact(artifact)

        lines.append(
            f"     artifact_id: {aid}\n"
            f"     type: {artifact_type}\n"
            f"     {doc}\n"
            f"     timestamp: {ts}"
        )

    return "\n\n".join(lines)


def build_llm_prompt(question: str, artifact_context: str) -> List[Dict[str, str]]:
    """Construct the messages array for the LLM."""
    system_msg = """You are a digital forensics assistant specialising in browser artifact analysis.
You will be given a numbered list of browser artifacts recovered from a disk image,
each identified by an artifact_id.

Your task is to analyse these artifacts and produce:
1. A list of investigative leads relevant to the investigator's question.
2. A chronological timeline of the user's activity based on the artifacts.

Rules you must follow without exception:
- Every lead and every timeline entry must cite the artifact_id(s) that support
  it, in square brackets at the end of the statement. Example:
  "User searched for anonymous file transfer tools [a1b2c3d4]"
- Only use information present in the provided artifacts.
  Do not infer, assume, or add facts not explicitly present in the context.
- If a claim cannot be supported by a specific artifact_id from the list,
  do not make that claim.
- If the provided artifacts are insufficient to answer the question,
  state this explicitly and explain what type of evidence would be needed.
- Flag any suspicious patterns, unusual navigation types, or temporal
  anomalies you observe.
- If you detect gaps in the timeline (periods with no activity) that seem
  unusual, flag them as potential use of private browsing or history deletion.
- Never use list position numbers as artifact_ids. Always copy the exact UUID value from the artifact_id field.
Respond in the following JSON structure and nothing else:
{
  "leads": [
    {
      "lead": "description of the lead",
      "severity": "high | medium | low",
      "artifact_ids": ["id1", "id2"],
      "explanation": "why this is investigatively significant"
    }
  ],
  "timeline": [
    {
      "timestamp": "ISO 8601",
      "event": "description of the event",
      "artifact_id": "id"
    }
  ],
  "gaps": [
    {
      "gap_start": "ISO 8601",
      "gap_end": "ISO 8601",
      "note": "description of the gap and why it is suspicious"
    }
  ],
  "summary": "2-3 sentence overall summary of the investigative picture"
}
"""

    user_msg = f"""Investigator question: {question}

Recovered artifacts:
{artifact_context}
"""

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]


def call_llm(messages: List[Dict[str, str]], timeout: int = None) -> tuple:
    """Call the LLM and return the response content and finish_reason."""
    if timeout is None:
        timeout = LLM_REQUEST_TIMEOUT
    try:
        response = LLM_CLIENT.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0,
            max_tokens=LLM_MAX_TOKENS,
            timeout=timeout,
        )
        content = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason
        if finish_reason == "length":
            LOGGER.warning("LLM response truncated due to token limit (finish_reason='length')")
        return content, finish_reason
    except Exception as exc:
        LOGGER.exception("LLM call failed: %s", exc)
        raise


def validate_citations(parsed_response: Dict[str, Any], valid_artifact_ids: set) -> List[str]:
    """
    Check all artifact_id citations in leads and timeline.
    Return list of hallucinated artifact_ids (those not in valid_artifact_ids).
    """
    hallucinations = []

    # Check leads
    for lead in parsed_response.get("leads", []):
        for aid in lead.get("artifact_ids", []):
            if aid not in valid_artifact_ids:
                if aid not in hallucinations:
                    hallucinations.append(aid)

    # Check timeline
    for entry in parsed_response.get("timeline", []):
        aid = entry.get("artifact_id")
        if aid and aid not in valid_artifact_ids:
            if aid not in hallucinations:
                hallucinations.append(aid)

    return hallucinations


def process_query(
    question: str,
    autopsy_case_id: str,
    top_k: int = 10,
    artifact_types: Optional[List[str]] = None,
    use_decomposition: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Orchestrate the full query pipeline:
    1. Decompose question (optional) or embed directly
    2. Retrieve artifacts
    3. Build LLM prompt
    4. Call LLM
    5. Parse and validate response
    6. Return structured result
    """
    use_decomposition = _resolve_use_decomposition(use_decomposition)

    if use_decomposition:
        artifacts, artifact_ids_set, retrieved_per_type, sub_queries = retrieve_artifacts_decomposed(
            question,
            autopsy_case_id,
            artifact_types,
            top_k,
        )
        artifacts_count = len(artifacts)
        LOGGER.info(
            "Retrieved %d artifacts for question='%s', case=%s, types=%s via decomposition",
            artifacts_count,
            question[:100],
            autopsy_case_id,
            artifact_types,
        )
        LOGGER.info("Decomposition sub-queries: history=%s, search=%s, download=%s, bookmark=%s", sub_queries["history"], sub_queries["search"], sub_queries["download"], sub_queries["bookmark"])
        LOGGER.info("Decomposition retrieval counts before deduplication: history=%d, search=%d, download=%d, bookmark=%d", retrieved_per_type["history"], retrieved_per_type["search"], retrieved_per_type["download"], retrieved_per_type["bookmark"])
        LOGGER.info("Decomposition deduplication summary: before=%d, after=%d, unique_types=%d", sum(retrieved_per_type.values()), artifacts_count, len({artifact.get("metadata", {}).get("artifact_type") for artifact in artifacts if artifact.get("metadata", {}).get("artifact_type")}))
    else:
        question_embedding = embed_question(question)
        artifacts, artifact_ids_set = retrieve_artifacts(
            question_embedding,
            autopsy_case_id,
            artifact_types,
            top_k,
        )
        artifacts_count = len(artifacts)
        LOGGER.info(
            "Retrieved %d artifacts for question='%s', case=%s, types=%s",
            artifacts_count,
            question[:100],
            autopsy_case_id,
            artifact_types,
        )

    if artifacts_count == 0:
        LOGGER.warning("No artifacts found for case %s", autopsy_case_id)
        return {
            "leads": [],
            "timeline": [],
            "gaps": [],
            "summary": "No artifacts found for this query and case. Verify ingestion completed successfully.",
            "warning": "No artifacts found for this query and case. Verify ingestion completed successfully.",
            "artifacts_retrieved": 0,
            "artifact_ids_used": [],
            "hallucination_warnings": [],
            "decomposition_metadata": None if not use_decomposition else {
                "sub_queries": {
                    "history": sub_queries["history"],
                    "search": sub_queries["search"],
                    "download": sub_queries["download"],
                    "bookmark": sub_queries["bookmark"],
                },
                "retrieved_per_type": {artifact_type: retrieved_per_type[artifact_type] for artifact_type in ARTIFACT_TYPE_ORDER},
                "deduplicated_total": artifacts_count,
            },
        }

    artifact_context = format_artifact_context(artifacts)

    messages = build_llm_prompt(question, artifact_context)

    try:
        llm_response, finish_reason = call_llm(messages, timeout=LLM_REQUEST_TIMEOUT)
        if finish_reason == "length":
            raise ValueError("LLM response truncated due to token limit. Increase LLM_MAX_TOKENS.")
    except Exception as exc:
        LOGGER.exception("LLM call failed: %s", exc)
        raise

    try:
        output_dir = os.path.join(os.getcwd(), "test_output")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        llm_debug_file = os.path.join(output_dir, f"llm_response_{timestamp}.txt")
        with open(llm_debug_file, "w", encoding="utf-8") as f:
            f.write(llm_response)
        LOGGER.debug("Saved raw LLM response to %s", llm_debug_file)
    except Exception as exc:
        LOGGER.warning("Failed to save LLM response debug file: %s", exc)

    try:
        parsed_response = json.loads(llm_response)
    except json.JSONDecodeError as exc:
        LOGGER.exception("Failed to parse LLM JSON response: %s", exc)
        raise ValueError(f"LLM returned malformed JSON: {str(exc)}")

    hallucinations = validate_citations(parsed_response, artifact_ids_set)
    if hallucinations:
        LOGGER.warning("Detected %d hallucinated artifact citations for case %s", len(hallucinations), autopsy_case_id)

    return {
        "leads": parsed_response.get("leads", []),
        "timeline": parsed_response.get("timeline", []),
        "gaps": parsed_response.get("gaps", []),
        "summary": parsed_response.get("summary", ""),
        "artifacts_retrieved": artifacts_count,
        "artifact_ids_used": list(artifact_ids_set),
        "hallucination_warnings": [
            {"artifact_id": hid, "message": f"Citation to artifact_id {hid} not found in retrieved set"}
            for hid in hallucinations
        ],
        "decomposition_metadata": None if not use_decomposition else {
            "sub_queries": {
                "history": sub_queries["history"],
                "search": sub_queries["search"],
                "download": sub_queries["download"],
                "bookmark": sub_queries["bookmark"],
            },
            "retrieved_per_type": {artifact_type: retrieved_per_type[artifact_type] for artifact_type in ARTIFACT_TYPE_ORDER},
            "deduplicated_total": artifacts_count,
        },
    }
