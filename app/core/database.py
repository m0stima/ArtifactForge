from __future__ import annotations

import sqlite3
from pathlib import Path


class Database:
    """SQLite wrapper with schema management."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;

                CREATE TABLE IF NOT EXISTS cases (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    analyst TEXT,
                    source_path TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    indexed_files_count INTEGER DEFAULT 0,
                    parser_warnings_count INTEGER DEFAULT 0,
                    findings_count INTEGER DEFAULT 0,
                    timeline_events_count INTEGER DEFAULT 0,
                    artifact_counts TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    support_state TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    source_artifact_type TEXT NOT NULL,
                    parser_name TEXT NOT NULL,
                    timestamp TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_artifacts_case_type ON artifacts(case_id, artifact_type);

                CREATE TABLE IF NOT EXISTS timeline_events (
                    id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    title TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    source_artifact_id TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_timeline_case_ts ON timeline_events(case_id, ts);

                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    artifact_id TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )
