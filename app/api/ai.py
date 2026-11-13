import logging
import json

import httpx

from fastapi import APIRouter, HTTPException

from app.database.connection import SessionLocal
from app.schemas.ai import AIRequest, AIResponse
from app.services.llm_service import generate_ai_reply


logger = logging.getLogger(__name__)

router = APIRouter()


# @router.post(
#     "/reply",
#     response_model=AIResponse
# )
from fastapi import Depends
from app.core.rate_limiter import rate_limit

@router.post(
    "/reply",
    dependencies=[
        Depends(rate_limit(10, 60))
    ],
)
async def ai_reply(request: AIRequest):
    return await create_ai_reply(request)
async def create_ai_reply(request: AIRequest):

    db = SessionLocal()

    try:
        result = await generate_ai_reply(
            message=request.message,
            db=db
        )

        return result

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="AI service timed out"
        )

    except httpx.HTTPStatusError:
        logger.exception("Ollama returned an HTTP error")

        raise HTTPException(
            status_code=502,
            detail="AI service returned an error"
        )

    except (ValueError, json.JSONDecodeError):
        raise HTTPException(
            status_code=502,
            detail="AI returned an invalid response"
        )

    except httpx.RequestError:
        logger.exception("Cannot connect to Ollama")

        raise HTTPException(
            status_code=503,
            detail="Ollama is unavailable"
        )

    except Exception:
        logger.exception("Unexpected AI service error")

        raise HTTPException(
            status_code=500,
            detail="Unable to generate AI response"
        )

    finally:
        db.close()    