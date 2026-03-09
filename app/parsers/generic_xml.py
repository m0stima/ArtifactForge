from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from app.models.artifact import ArtifactRecord
from app.parsers.base import BaseParser


class GenericXMLParser(BaseParser):
    parser_name = "generic_xml"
    artifact_type = "generic"

    def parse(self, case_id: str, source_file: Path, source_artifact_type: str, support_state: str) -> list[ArtifactRecord]:
        tree = ET.parse(source_file)
        root = tree.getroot()
        records: list[ArtifactRecord] = []
        for item in root.findall('.//item'):
            row = {child.tag: (child.text or "") for child in item}
            timestamp = row.get("timestamp") or row.get("time")
            records.append(
                ArtifactRecord(
                    case_id=case_id,
                    artifact_type=source_artifact_type,
                    support_state=support_state,
                    data_json=row,
                    source_file=str(source_file),
                    source_artifact_type=source_artifact_type,
                    parser_name=self.parser_name,
                    timestamp=timestamp,
                )
            )
        return records
