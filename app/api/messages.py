from fastapi import APIRouter, HTTPException

from app.database.connection import SessionLocal
from app.schemas.message import (
    MessageRequest,
    MessageResponse
)
from app.services.message_service import generate_reply

router = APIRouter()


@router.post(
    "/reply",
    response_model=MessageResponse
)
def create_message_reply(
    request: MessageRequest
):
    db = SessionLocal()

    try:
        result = generate_reply(
            message=request.message,
            db=db
        )

        return MessageResponse(**result)

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to generate customer reply"
        ) from exc

    finally:
        db.close()