from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.evaluation.evaluator import evaluate_responses
from app.evaluation.metrics import calculate_metrics
from app.evaluation.timing import measure_latency


_last_summary = {
    "total": 0,
    "accuracy": 0,
    "tool_accuracy": 0,
    "average_latency_ms": 0,
}


@measure_latency
async def generate_customer_answer(message, db):
    # Call your existing AI service here.
    ...

router = APIRouter(
    prefix="/evaluation",
    tags=["AI Evaluation"],
)


class Prediction(BaseModel):
    id: str
    answer: str
    actual_tool: str | None = None
    latency_ms: float = Field(default=0, ge=0)


class EvaluationRequest(BaseModel):
    predictions: list[Prediction]


@router.get("/summary")
def get_evaluation_summary():
    return _last_summary


@router.post("/run")
def run_evaluation(request: EvaluationRequest):
    predictions = [
        item.model_dump()
        for item in request.predictions
    ]

    result = evaluate_responses(predictions)
    global _last_summary
    _last_summary = result["metrics"]

    return result