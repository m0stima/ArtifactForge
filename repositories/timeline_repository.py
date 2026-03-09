from __future__ import annotations

import json
from dataclasses import dataclass

from core.database import Database
from models.timeline import TimelineEvent


@dataclass(slots=True)
class TimelineRepository:
    db: Database

    def insert_many(self, events: list[TimelineEvent]) -> None:
        if not events:
            return
        with self.db.connect() as conn:
            conn.executemany(
                "INSERT INTO timeline_events VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        e.id,
                        e.case_id,
                        e.category,
                        e.ts,
                        e.title,
                        json.dumps(e.details_json),
                        e.source_artifact_id,
                    )
                    for e in events
                ],
            )

    def list_by_case(self, case_id: str, limit: int = 300) -> list[TimelineEvent]:
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM timeline_events WHERE case_id = ? ORDER BY ts DESC LIMIT ?",
                (case_id, limit),
            ).fetchall()
        results: list[TimelineEvent] = []
        for r in rows:
            d = dict(r)
            d["details_json"] = json.loads(d["details_json"])
            results.append(TimelineEvent(**d))
        return results
