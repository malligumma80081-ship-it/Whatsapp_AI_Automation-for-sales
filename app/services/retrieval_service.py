import hashlib

from pathlib import Path
from functools import lru_cache
from typing import Any, cast

import chromadb

from app.core.config import settings

from app.services.embedding_service import (
    chunk_text,
    generate_embeddings
)

KNOWLEDGE_DIR = Path("D:\\millet_milk_ai\\knowledge_base")

@lru_cache(maxsize=1)
def get_chroma_collection():

    persist_path = Path(
        settings.CHROMA_PERSIST_DIRECTORY
    )

    persist_path.mkdir(
        parents=True,
        exist_ok=True
    )

    client = chromadb.PersistentClient(
        path=str(persist_path)
    )

    collection = client.get_or_create_collection(
        name=getattr(settings, "CHROMA_COLLECTION_NAME", "knowledge_base"),
        metadata={
            "hnsw:space": "cosine"
        }
    )

    return collection

def generate_chunk_id(
    source: str,
    chunk_index: int,
    content: str
) -> str:

    raw = (
        f"{source}:{chunk_index}:{content}"
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()

def ingest_documents():

    collection = get_chroma_collection()

    files = list(KNOWLEDGE_DIR.glob("*.md"))
    files += list(KNOWLEDGE_DIR.glob("*.txt"))

    if not files:
        raise ValueError(
            "No .md or .txt knowledge documents found"
        )

    all_chunks = []
    all_ids = []
    all_metadata = []

    for file_path in files:

        content = file_path.read_text(
            encoding="utf-8"
        )

        chunks = chunk_text(
            content,
            chunk_size=150,
            overlap=30
        )

        for index, chunk in enumerate(chunks):

            all_chunks.append(chunk)

            all_ids.append(
                generate_chunk_id(
                    file_path.name,
                    index,
                    chunk
                )
            )

            all_metadata.append({
                "source": file_path.name,
                "chunk_index": index,
                "file_type": file_path.suffix
            })

    if not all_chunks:
        raise ValueError(
            "Knowledge documents contain no text"
        )

    embeddings = generate_embeddings(
        all_chunks
    )

    collection.upsert(
        ids=all_ids,
        documents=all_chunks,
        metadatas=all_metadata,
        embeddings=cast(Any, embeddings)
    )

    return {
        "documents_processed": len(files),
        "chunks_created": len(all_chunks),
        "collection_name": collection.name,
        "total_chunks_in_collection": collection.count()
    }

def search_knowledge(
    question: str,
    top_k: int = 3
):

    collection = get_chroma_collection()

    if collection.count() == 0:
        return []

    query_embedding = generate_embeddings(
        [question]
    )[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(
            top_k,
            collection.count()
        ),
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    matches = []

    result_documents = results.get("documents")
    if result_documents is None:
        return []

    result_metadatas = results.get("metadatas")
    if result_metadatas is None:
        return []

    result_distances = results.get("distances")
    if result_distances is None:
        return []

    result_ids = results.get("ids")
    if result_ids is None:
        return []

    documents = result_documents[0]
    metadatas = result_metadatas[0]
    distances = result_distances[0]
    ids = result_ids[0]

    for chunk_id, document, metadata, distance in zip(
        ids,
        documents,
        metadatas,
        distances
    ):

        matches.append({
            "id": chunk_id,
            "content": document,
            "source": metadata["source"],
            "chunk_index": metadata["chunk_index"],
            "distance": float(distance),
            "similarity": float(1 - distance)
        })

    return matches