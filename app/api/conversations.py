from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.database.models import ConversationMessage

from app.schemas.conversation import (
    ConversationRequest,
    ConversationResponse
)
from app.database.models import ConversationSession

from app.services.conversation_service import (
    generate_conversation_reply
)

router = APIRouter()


@router.post(
    "/message",
    response_model=ConversationResponse
)
def send_conversation_message(
    request: ConversationRequest
):
    db: Session = SessionLocal()

    try:
        result = generate_conversation_reply(
            db=db,
            customer_id=request.customer_id,
            channel=request.channel,
            message=request.message
        )

        return result

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Conversation processing failed"
        ) from exc

    finally:
        db.close()


@router.get("/{session_id}/history")
def get_conversation_history(session_id: int):
    db = SessionLocal()

    try:
        messages = (
            db.query(ConversationMessage)
            .filter(
                ConversationMessage.session_id == session_id
            )
            .order_by(ConversationMessage.id.asc())
            .all()
        )

        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": item.role,
                    "content": item.content,
                    "created_at": item.created_at
                }
                for item in messages
            ]
        }

    finally:
        db.close()

from app.database.models import ConversationSession


@router.get("/{session_id}/details")
def get_conversation_details(session_id: int):
    db = SessionLocal()

    try:
        session = (
            db.query(ConversationSession)
            .filter(
                ConversationSession.id == session_id
            )
            .first()
        )

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

        return {
            "session_id": session.id,
            "customer_id": session.customer_id,
            "state": session.state,
            "order_id": (session.context or {}).get("order_id"),
            "order_details": session.context or {}
        }

    finally:
        db.close()        