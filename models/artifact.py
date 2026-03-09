from __future__ import annotations

from pydantic import BaseModel, Field

from models.base import new_id, utc_now_iso


class ArtifactRecord(BaseModel):
    id: str = Field(default_factory=new_id)
    case_id: str
    artifact_type: str
    support_state: str = "supported"
    data_json: dict
    source_file: str
    source_artifact_type: str
    parser_name: str
    timestamp: str | None = None
    created_at: str = Field(default_factory=utc_now_iso)
