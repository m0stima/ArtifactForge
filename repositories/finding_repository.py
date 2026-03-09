from __future__ import annotations

from dataclasses import dataclass

from core.database import Database
from models.finding import Finding


@dataclass(slots=True)
class FindingsRepository:
    db: Database

    def insert_many(self, findings: list[Finding]) -> None:
        if not findings:
            return
        with self.db.connect() as conn:
            conn.executemany(
                "INSERT INTO findings VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        f.id,
                        f.case_id,
                        f.severity,
                        f.title,
                        f.description,
                        f.artifact_id,
                        f.created_at,
                    )
                    for f in findings
                ],
            )

    def list_by_case(self, case_id: str) -> list[Finding]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM findings WHERE case_id = ? ORDER BY created_at DESC", (case_id,)).fetchall()
        return [Finding(**dict(r)) for r in rows]
