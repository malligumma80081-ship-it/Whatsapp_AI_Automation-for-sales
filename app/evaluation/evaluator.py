import json
import time
from pathlib import Path

from app.evaluation.metrics import (
    fact_coverage,
    tool_accuracy,
    calculate_metrics,
)


DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "knowledge_base"
    / "evaluation"
    / "questions.json"
)

def load_dataset():
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(
            f"Evaluation dataset file not found: {DATASET_PATH}"
        )

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_responses(predictions: list[dict]):
    dataset = load_dataset()

    expected_by_id = {
        item["id"]: item
        for item in dataset
    }

    results = []

    for prediction in predictions:
        expected = expected_by_id.get(prediction["id"])

        if expected is None:
            continue

        coverage = fact_coverage(
            prediction["answer"],
            expected["expected_facts"],
        )

        accuracy = tool_accuracy(
            expected["expected_tool"],
            prediction.get("actual_tool"),
        )

        results.append({
            "id": prediction["id"],
            "category": expected["category"],
            "fact_coverage": coverage,
            "tool_accuracy": accuracy,
            "latency_ms": prediction.get(
                "latency_ms", 0
            ),
        })

    return {
        "metrics": calculate_metrics(results),
        "details": results,
    }