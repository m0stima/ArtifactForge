from __future__ import annotations

from pydantic import BaseModel, Field

from models.base import new_id, utc_now_iso


class CaseModel(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str
    description: str = ""
    analyst: str = ""
    source_path: str
    storage_path: str
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    indexed_files_count: int = 0
    parser_warnings_count: int = 0
    findings_count: int = 0
    timeline_events_count: int = 0
    artifact_counts: dict[str, int] = Field(default_factory=dict)
