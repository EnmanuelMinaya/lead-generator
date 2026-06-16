from typing import Optional, Literal
from pydantic import BaseModel, Field


class SharedFields(BaseModel):
    artifact_type: Literal["history", "search", "download", "bookmark"]
    browser: Literal["chrome", "edge", "firefox", "brave", "safari", "opera"]
    browser_profile: str
    source_db_path: str
    source_db_hash: str
    os_user_account: str
    autopsy_case_id: str


class HistoryArtifact(SharedFields):
    artifact_type: Literal["history"]
    url: str
    page_title: Optional[str] = None
    visit_timestamp: str
    visit_count: int
    transition_type: Optional[Literal["TYPED", "LINK", "AUTO_BOOKMARK", "FORM_SUBMIT", "unspecified"]] = None


class SearchArtifact(SharedFields):
    artifact_type: Literal["search"]
    search_term: str
    search_engine: Optional[str] = None
    search_timestamp: str
    result_url: Optional[str] = None


class DownloadArtifact(SharedFields):
    artifact_type: Literal["download"]
    download_url: str
    referrer_url: Optional[str] = None
    target_path: str
    filename: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    start_timestamp: str
    end_timestamp: Optional[str] = None
    download_state: Literal["complete", "interrupted", "in_progress"]
    danger_type: Optional[str] = None


class BookmarkArtifact(SharedFields):
    artifact_type: Literal["bookmark"]
    url: str
    bookmark_title: Optional[str] = None
    folder_path: Optional[str] = None
    date_added: str
    date_last_used: Optional[str] = None


# Mapping used by the ingest logic to pick the right model
MODEL_BY_TYPE = {
    "history": HistoryArtifact,
    "search": SearchArtifact,
    "download": DownloadArtifact,
    "bookmark": BookmarkArtifact,
}


class QueryRequest(BaseModel):
    question: str
    autopsy_case_id: str
    top_k: int = 10
    artifact_types: Optional[list[Literal["history", "search", "download", "bookmark"]]] = None

    def validate_question(self):
        if not self.question or not self.question.strip():
            raise ValueError("question cannot be empty")

    def validate_top_k(self):
        if not (1 <= self.top_k <= 20):
            raise ValueError("top_k must be between 1 and 20")

    def validate_artifact_types(self):
        if self.artifact_types:
            valid = {"history", "search", "download", "bookmark"}
            for at in self.artifact_types:
                if at not in valid:
                    raise ValueError(f"invalid artifact_type: {at}")

    def __init__(self, **data):
        super().__init__(**data)
        self.validate_question()
        self.validate_top_k()
        self.validate_artifact_types()
