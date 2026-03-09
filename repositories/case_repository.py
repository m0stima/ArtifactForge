from __future__ import annotations

import json
from dataclasses import dataclass

from core.database import Database
from models.case import CaseModel


@dataclass(slots=True)
class CaseRepository:
    db: Database

    def create(self, case: CaseModel) -> None:
        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT INTO cases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case.id,
                    case.name,
                    case.description,
                    case.analyst,
                    case.source_path,
                    case.storage_path,
                    case.created_at,
                    case.updated_at,
                    case.indexed_files_count,
                    case.parser_warnings_count,
                    case.findings_count,
                    case.timeline_events_count,
                    json.dumps(case.artifact_counts),
                ),
            )

    def list_all(self) -> list[CaseModel]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
        return [self._row_to_model(row) for row in rows]

    def get(self, case_id: str) -> CaseModel | None:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        return self._row_to_model(row) if row else None

    def update_metrics(self, case: CaseModel) -> None:
        with self.db.connect() as conn:
            conn.execute(
                """
                UPDATE cases
                SET updated_at = ?, indexed_files_count = ?, parser_warnings_count = ?,
                    findings_count = ?, timeline_events_count = ?, artifact_counts = ?
                WHERE id = ?
                """,
                (
                    case.updated_at,
                    case.indexed_files_count,
                    case.parser_warnings_count,
                    case.findings_count,
                    case.timeline_events_count,
                    json.dumps(case.artifact_counts),
                    case.id,
                ),
            )

    @staticmethod
    def _row_to_model(row) -> CaseModel:
        data = dict(row)
        data["artifact_counts"] = json.loads(data["artifact_counts"])
        return CaseModel(**data)
