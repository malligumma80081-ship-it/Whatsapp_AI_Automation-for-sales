import json
import logging

import httpx

from fastapi import APIRouter, HTTPException

from app.schemas.rag import (
    RAGRequest,
    RAGResponse
)

from app.services.rag_service import (
    generate_rag_answer
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/ask",
    response_model=RAGResponse
)
async def ask_rag_question(
    request: RAGRequest
):

    try:
        result = await generate_rag_answer(
            question=request.question,
            top_k=request.top_k
        )

        return RAGResponse(**result)

    except httpx.TimeoutException:
        logger.exception("Ollama request timed out")

        raise HTTPException(
            status_code=504,
            detail="AI service timed out"
        )

    except httpx.HTTPStatusError:
        logger.exception("Ollama HTTP error")

        raise HTTPException(
            status_code=502,
            detail="AI generation failed"
        )

    except httpx.RequestError:
        logger.exception("Ollama connection error")

        raise HTTPException(
            status_code=503,
            detail="Ollama is unavailable"
        )

    except (ValueError, json.JSONDecodeError):
        logger.exception("Invalid RAG output")

        raise HTTPException(
            status_code=502,
            detail="Unable to generate a valid RAG response"
        )

    except Exception:
        logger.exception("Unexpected RAG error")

        raise HTTPException(
            status_code=500,
            detail="RAG processing failed"
        )