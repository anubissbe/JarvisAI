import pytest

from document_processor import DocumentProcessor


def make_processor(chunk_size, chunk_overlap):
    proc = DocumentProcessor.__new__(DocumentProcessor)
    proc.chunk_size = chunk_size
    proc.chunk_overlap = chunk_overlap
    return proc


def test_chunk_text_basic():
    proc = make_processor(chunk_size=10, chunk_overlap=2)
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = proc.chunk_text(text)
    assert chunks == [
        "abcdefghij",
        "ijklmnopqr",
        "qrstuvwxyz",
        "yz",
    ]


def test_chunk_text_non_positive_size():
    proc = make_processor(chunk_size=0, chunk_overlap=0)
    assert proc.chunk_text("hello") == ["hello"]


def test_chunk_text_step_adjustment():
    proc = make_processor(chunk_size=5, chunk_overlap=10)
    # overlap >= size -> step becomes size (5)
    text = "abcdefghij"
    assert proc.chunk_text(text) == ["abcde", "fghij"]
