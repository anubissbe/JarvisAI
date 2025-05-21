import json
from pathlib import Path

from document_processor import DocumentProcessor


class DummySearcher:
    def __init__(self, kb_ids):
        self._kb_ids = kb_ids

    def get_available_knowledge_bases(self):
        return self._kb_ids


def make_processor(searcher=None, default="default-id"):
    proc = DocumentProcessor.__new__(DocumentProcessor)
    proc.default_kb_id = default
    proc.searcher = searcher
    return proc


def test_extract_kb_id_from_upload_path(tmp_path):
    kb_id = "123e4567-e89b-12d3-a456-426614174000"
    path = tmp_path / "uploads" / kb_id / "file.txt"
    path.parent.mkdir(parents=True)
    path.write_text("data")
    proc = make_processor()
    assert proc.extract_kb_id_from_path(str(path)) == kb_id


def test_extract_kb_id_from_config(tmp_path):
    kb_id = "abcdefab-1234-5678-abcd-1234567890ab"
    file_path = tmp_path / "file.txt"
    file_path.write_text("data")
    config = tmp_path / ".kb_config"
    config.write_text(json.dumps({"kb_id": kb_id}))
    proc = make_processor()
    assert proc.extract_kb_id_from_path(str(file_path)) == kb_id


def test_extract_kb_id_from_searcher(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("data")
    searcher = DummySearcher(["deadbeef-dead-beef-dead-beefdeadbeef"])
    proc = make_processor(searcher=searcher, default="fallback")
    assert proc.extract_kb_id_from_path(str(file_path)) == searcher._kb_ids[0]


def test_extract_kb_id_default(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("data")
    searcher = DummySearcher([])
    proc = make_processor(searcher=searcher, default="fallback")
    assert proc.extract_kb_id_from_path(str(file_path)) == "fallback"

