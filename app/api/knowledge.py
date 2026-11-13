import logging

from fastapi import APIRouter, HTTPException

from app.schemas.knowledge import (
    KnowledgeSearchRequest,
    KnowledgeSearchResponse
)

from app.services.retrieval_service import (
    ingest_documents,
    search_knowledge
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/ingest")
def ingest_knowledge_base():

    try:
        return ingest_documents()

    except Exception as exc:
        logger.exception("Knowledge ingestion failed")

        raise HTTPException(
            status_code=500,
            detail="Unable to ingest knowledge documents"
        ) from exc

@router.post(
    "/search",
    response_model=KnowledgeSearchResponse
)
def search_knowledge_base(
    request: KnowledgeSearchRequest
):

    try:
        results = search_knowledge(
            question=request.question,
            top_k=request.top_k
        )

        return {
            "question": request.question,
            "results": results
        }

    except Exception as exc:
        logger.exception("Knowledge retrieval failed")

        raise HTTPException(
            status_code=500,
            detail="Unable to search knowledge base"
        ) from exc

@router.get("/stats")
def knowledge_statistics():

    try:
        from app.services.retrieval_service import (
            get_chroma_collection
        )

        collection = get_chroma_collection()

        return {
            "collection_name": collection.name,
            "total_chunks": collection.count()
        }

    except Exception as exc:
        logger.exception("Knowledge statistics failed")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve knowledge statistics"
        ) from exc