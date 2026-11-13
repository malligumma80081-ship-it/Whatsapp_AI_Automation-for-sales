import logging

from fastapi import APIRouter, HTTPException

from app.schemas.llm_gateway import (
    GatewayRequest,
    GatewayResponse,
)

from ..services.llm_gateway.gateway import LLMGateway
from ..services.llm_monitoring import get_metrics

logger = logging.getLogger(__name__)

router = APIRouter()

gateway = LLMGateway()

@router.post(
    "/generate",
    response_model=GatewayResponse
)
async def generate_with_gateway(
    request: GatewayRequest
):

    try:
        result = await gateway.generate(
            messages=[
                {
                    "role": "user",
                    "content": request.message
                }
            ],
            task=request.task
        )

        return GatewayResponse(
            reply=result.content,
            provider=result.provider,
            model=result.model
        )

    except Exception:
        logger.exception("LLM Gateway request failed")

        raise HTTPException(
            status_code=503,
            detail="All configured LLM providers are unavailable"
        )

@router.get("/metrics")
def gateway_metrics():

    return get_metrics()