from __future__ import annotations

from pydantic import BaseModel, Field

from models.base import new_id


class TimelineEvent(BaseModel):
    id: str = Field(default_factory=new_id)
    case_id: str
    category: str
    ts: str
    title: str
    details_json: dict
    source_artifact_id: str | None = None
