from unittest.mock import patch

from app.services.rag_service import (
    retrieve_relevant_context,
    build_rag_context,
    build_rag_prompt
)


def test_retrieve_relevant_context():

    fake_results = [
        {
            "id": "chunk-1",
            "content": "Customer pickup is available.",
            "source": "business_faq.md",
            "chunk_index": 0,
            "distance": 0.15,
            "similarity": 0.85
        },
        {
            "id": "chunk-2",
            "content": "Unrelated information.",
            "source": "products.md",
            "chunk_index": 1,
            "distance": 0.85,
            "similarity": 0.15
        }
    ]

    with patch(
        "app.services.rag_service.search_knowledge",
        return_value=fake_results
    ):
        results = retrieve_relevant_context(
            "Can I collect my order?",
            3
        )

    assert len(results) == 1
    assert results[0]["id"] == "chunk-1"


def test_build_rag_context():

    results = [
        {
            "source": "business_faq.md",
            "chunk_index": 0,
            "content": "Cash on Delivery is available."
        }
    ]

    context = build_rag_context(results)

    assert "Cash on Delivery" in context
    assert "business_faq.md" in context


def test_build_rag_prompt():

    prompt = build_rag_prompt(
        question="Can I pay using UPI?",
        context="UPI payment is available."
    )

    assert "UPI payment is available" in prompt
    assert "Can I pay using UPI?" in prompt
    assert "Do not invent business policies" in prompt
    