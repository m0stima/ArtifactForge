from pathlib import Path

from app.services.discovery import XMLDiscovery


def test_discovery_and_classification():
    d = XMLDiscovery()
    files = d.discover(Path("sample_data"))
    assert files
    artifact, state = d.classify(Path("prefetch_sample.xml"))
    assert artifact == "Prefetch"
    assert state == "supported"
