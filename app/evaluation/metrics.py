import re
from typing import Any


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def fact_coverage(
    answer: str,
    expected_facts: list[str],
) -> float:
    if not expected_facts:
        return 1.0

    normalized_answer = normalize_text(answer)

    matched = sum(
        1
        for fact in expected_facts
        if normalize_text(fact) in normalized_answer
    )

    return matched / len(expected_facts)


def tool_accuracy(
    expected_tool: str,
    actual_tool: str | None,
) -> float:
    actual_tool = actual_tool or "none"

    return float(expected_tool == actual_tool)


def average_score(scores: list[float]) -> float:
    if not scores:
        return 0.0

    return sum(scores) / len(scores)


def calculate_metrics(results: list[dict[str, Any]]):
    if not results:
        return {
            "total": 0,
            "accuracy": 0,
            "tool_accuracy": 0,
            "average_latency_ms": 0,
        }

    return {
        "total": len(results),
        "accuracy": round(
            average_score(
                [item["fact_coverage"] for item in results]
            ) * 100,
            2,
        ),
        "tool_accuracy": round(
            average_score(
                [item["tool_accuracy"] for item in results]
            ) * 100,
            2,
        ),
        "average_latency_ms": round(
            average_score(
                [item["latency_ms"] for item in results]
            ),
            2,
        ),
    }

def precision_at_k(
    retrieved_sources: list[str],
    relevant_sources: list[str],
) -> float:
    if not retrieved_sources:
        return 0.0

    relevant = set(relevant_sources)

    hits = sum(
        1 for source in retrieved_sources
        if source in relevant
    )

    return hits / len(retrieved_sources)


def hit_rate_at_k(
    retrieved_sources: list[str],
    relevant_sources: list[str],
) -> float:
    if not relevant_sources:
        return 0.0

    relevant = set(relevant_sources)

    return float(
        any(source in relevant for source in retrieved_sources)
    )    