from __future__ import annotations

import json
from dataclasses import dataclass

from core.database import Database
from models.artifact import ArtifactRecord


@dataclass(slots=True)
class ArtifactRepository:
    db: Database

    def insert_many(self, artifacts: list[ArtifactRecord]) -> None:
        if not artifacts:
            return
        with self.db.connect() as conn:
            conn.executemany(
                """
                INSERT INTO artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        a.id,
                        a.case_id,
                        a.artifact_type,
                        a.support_state,
                        json.dumps(a.data_json),
                        a.source_file,
                        a.source_artifact_type,
                        a.parser_name,
                        a.timestamp,
                        a.created_at,
                    )
                    for a in artifacts
                ],
            )

    def query(self, case_id: str, artifact_type: str | None = None, limit: int = 200, offset: int = 0) -> list[ArtifactRecord]:
        query = "SELECT * FROM artifacts WHERE case_id = ?"
        params: list[object] = [case_id]
        if artifact_type:
            query += " AND artifact_type = ?"
            params.append(artifact_type)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        with self.db.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_model(r) for r in rows]

    def count_by_type(self, case_id: str) -> dict[str, int]:
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT artifact_type, COUNT(*) c FROM artifacts WHERE case_id = ? GROUP BY artifact_type",
                (case_id,),
            ).fetchall()
        return {row["artifact_type"]: row["c"] for row in rows}

    @staticmethod
    def _row_to_model(row) -> ArtifactRecord:
        data = dict(row)
        data["data_json"] = json.loads(data["data_json"])
        return ArtifactRecord(**data)
