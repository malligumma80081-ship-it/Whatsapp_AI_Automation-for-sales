from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.schemas.tools import ToolRequest, ToolResponse
from app.services.tool_registry import execute_tool

router = APIRouter(prefix="/tools", tags=["AI Tools"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/execute", response_model=ToolResponse)
def run_tool(
    request: ToolRequest,
    db: Session = Depends(get_db),
):
    try:
        result = execute_tool(
            db=db,
            tool_name=request.tool_name,
            arguments=request.arguments,
            confirmed=request.confirmed,
        )

        return ToolResponse(
            tool_name=request.tool_name,
            success=True,
            result={"data": result},
            message="Tool executed successfully.",
        )

    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc))

    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))