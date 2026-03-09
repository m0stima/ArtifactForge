from pathlib import Path

from parsers.prefetch_parser import PrefetchParser


def test_prefetch_parser_reads_rows():
    parser = PrefetchParser()
    rows = parser.parse("case-1", Path("sample_data/prefetch_sample.xml"), "Prefetch", "supported")
    assert len(rows) == 2
    assert rows[0].artifact_type == "Prefetch"
