from app.api.evaluation import get_evaluation_summary
from app.evaluation.metrics import (
    fact_coverage,
    tool_accuracy,
    precision_at_k,
    hit_rate_at_k,
    calculate_metrics,
)


def test_correct_answer():
    score = fact_coverage(
        "500 ml Ragi Milk costs Rs. 45.",
        ["500 ml", "45"],
    )

    assert score == 1.0


def test_incorrect_price():
    score = fact_coverage(
        "500 ml Ragi Milk costs Rs. 50.",
        ["500 ml", "45"],
    )

    assert score == 0.5


def test_tool_accuracy():
    assert tool_accuracy(
        "calculate_order",
        "calculate_order",
    ) == 1.0


def test_wrong_tool():
    assert tool_accuracy(
        "calculate_order",
        "get_products",
    ) == 0.0


def test_precision_at_k():
    retrieved = ["products.md", "faq.md", "old.md"]
    relevant = ["products.md", "faq.md"]

    assert precision_at_k(retrieved, relevant) == 2 / 3


def test_hit_rate_at_k():
    retrieved = ["products.md", "old.md"]
    relevant = ["products.md"]

    assert hit_rate_at_k(retrieved, relevant) == 1.0


def test_empty_metrics():
    result = calculate_metrics([])

    assert result["total"] == 0
    assert result["accuracy"] == 0


def test_evaluation_summary_default_values():
    summary = get_evaluation_summary()

    assert summary["total"] == 0
    assert summary["accuracy"] == 0
    assert summary["tool_accuracy"] == 0
    assert summary["average_latency_ms"] == 0