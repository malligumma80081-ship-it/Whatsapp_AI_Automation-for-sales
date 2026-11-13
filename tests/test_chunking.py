import pytest

from app.services.embedding_service import chunk_text

def test_chunk_text_creates_chunks():
    text = " ".join(
        [f"word{i}" for i in range(350)]
    )

    chunks = chunk_text(
        text,
        chunk_size=150,
        overlap=30
    )

    assert len(chunks) == 3

def test_chunk_overlap():
    text = " ".join(
        [f"word{i}" for i in range(200)]
    )

    chunks = chunk_text(
        text,
        chunk_size=150,
        overlap=30
    )

    first_words = chunks[0].split()
    second_words = chunks[1].split()

    assert first_words[-30:] == second_words[:30]

def test_empty_text():
    assert chunk_text("") == []

def test_invalid_chunk_size():
    with pytest.raises(ValueError):
        chunk_text(
            "Hello world",
            chunk_size=0
        )

def test_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text(
            "Hello world",
            chunk_size=100,
            overlap=100
        )