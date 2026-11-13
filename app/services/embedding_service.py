from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import settings

@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer(
        getattr(settings, "EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    )

def chunk_text(
    text: str,
    chunk_size: int = 150,
    overlap: int = 30
) -> list[str]:

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and "
            "smaller than chunk_size"
        )

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(words[start:end])

        if chunk.strip():
            chunks.append(chunk)

        if end >= len(words):
            break

        start = end - overlap

    return chunks

def generate_embeddings(
    texts: list[str]
) -> list[list[float]]:

    if not texts:
        return []

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    return embeddings.tolist()