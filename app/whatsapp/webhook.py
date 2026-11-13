import logging

from fastapi import (
    APIRouter,
    Request,
    HTTPException,
)

from fastapi.responses import PlainTextResponse

from app.core.config import settings

from app.whatsapp.security import (
    verify_webhook_signature,
    verify_webhook_token,
)

from app.whatsapp.message_handler import (
    process_incoming_message,
)


logger = logging.getLogger(__name__)

router = APIRouter()


# GET: Meta webhook subscription verification

@router.get("/")
async def verify_whatsapp_webhook(
    request: Request,
):

    mode = request.query_params.get("hub.mode")

    token = request.query_params.get(
        "hub.verify_token"
    )

    challenge = request.query_params.get(
        "hub.challenge"
    )

    if (
        mode == "subscribe"
        and challenge
        and verify_webhook_token(token)
    ):

        return PlainTextResponse(
            content=challenge,
            status_code=200,
        )

    raise HTTPException(
        status_code=403,
        detail="Webhook verification failed",
    )


# POST: Incoming WhatsApp messages

@router.post("/")
async def receive_whatsapp_message(
    request: Request,
):

    body = await request.body()

    signature = request.headers.get(
        "X-Hub-Signature-256"
    )

    if not verify_webhook_signature(
        body,
        signature,
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature",
        )

    try:

        payload = await request.json()

        results = process_incoming_message(
            payload
        )

        logger.info(
            "Processed %s WhatsApp messages",
            len(results),
        )

        return {
            "status": "received",
            "processed_messages": len(results),
        }

    except Exception:

        logger.exception(
            "WhatsApp webhook processing failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Webhook processing failed",
        )