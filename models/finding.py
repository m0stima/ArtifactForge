from __future__ import annotations

from pydantic import BaseModel, Field

from models.base import new_id, utc_now_iso


class Finding(BaseModel):
    id: str = Field(default_factory=new_id)
    case_id: str
    severity: str
    title: str
    description: str
    artifact_id: str | None = None
    created_at: str = Field(default_factory=utc_now_iso)
