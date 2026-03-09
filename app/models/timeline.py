from __future__ import annotations

from app.models.pydantic_compat import BaseModel, Field

from app.models.base import new_id


class TimelineEvent(BaseModel):
    id: str = Field(default_factory=new_id)
    case_id: str
    category: str
    ts: str
    title: str
    details_json: dict
    source_artifact_id: str | None = None
