from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from models.artifact import ArtifactRecord
from parsers.base import BaseParser


class PrefetchParser(BaseParser):
    parser_name = "prefetch_xml"
    artifact_type = "Prefetch"

    def parse(self, case_id: str, source_file: Path, source_artifact_type: str, support_state: str) -> list[ArtifactRecord]:
        tree = ET.parse(source_file)
        root = tree.getroot()
        records: list[ArtifactRecord] = []
        for entry in root.findall('.//prefetch') + root.findall('.//item'):
            exe_name = entry.findtext('executable') or entry.findtext('name') or "unknown.exe"
            run_count = entry.findtext('run_count') or "0"
            last_run = entry.findtext('last_run') or entry.findtext('timestamp')
            path = entry.findtext('path') or ""
            row = {
                "executable": exe_name,
                "run_count": int(run_count) if str(run_count).isdigit() else run_count,
                "last_run": last_run,
                "path": path,
            }
            records.append(
                ArtifactRecord(
                    case_id=case_id,
                    artifact_type="Prefetch",
                    support_state="supported",
                    data_json=row,
                    source_file=str(source_file),
                    source_artifact_type=source_artifact_type,
                    parser_name=self.parser_name,
                    timestamp=last_run,
                )
            )
        return records
