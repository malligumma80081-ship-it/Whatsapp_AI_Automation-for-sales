from app.services.message_service import (
    detect_intent,
    format_order_confirmation,
)


def test_detect_intent_does_not_match_hi_inside_this():
    assert detect_intent("this is a question") == "unknown"


def test_detect_intent_matches_greeting_word():
    assert detect_intent("Hello there!") == "greeting"


def test_detect_intent_matches_good_evening():
    assert detect_intent("Good evening") == "greeting"


def test_detect_intent_matches_price_phrase():
    assert detect_intent("How much is the milk?") == "price"


def test_detect_intent_matches_pick_up_phrase():
    assert detect_intent("Can I pick up my order?") == "delivery"


def test_detect_intent_matches_human_support():
    assert detect_intent("Can I talk to a person?") == "human_support"


def test_format_order_confirmation():
    assert format_order_confirmation(
        order_id=12,
        customer_name="Asha",
        total_amount=162,
        delivery_mode="home_delivery",
        payment_method="upi",
    ) == (
        "Hello Asha!\n\n"
        "Your Ragi Milk order is received.\n"
        "Order ID: #12\n"
        "Total: ₹162.00\n"
        "Delivery: home_delivery\n"
        "Payment: upi\n\n"
        "Thank you for choosing Millet Milk Sales!"
    )
