from app.main import app

def complete_order(client, customer_id):
    messages = [
        "I want to order Ragi Milk",
        "2 bottles",
        "500 ml",
        "Home delivery",
        "House 12, Main Road, Hyderabad",
        "Cash on Delivery",
        "YES",
    ]

    response = None
    for message in messages:
        response = client.post(
            "/api/v1/conversations/message",
            json={
                "customer_id": customer_id,
                "channel": "internal",
                "message": message,
            },
        )
        assert response.status_code == 200, response.text

    assert response is not None
    return response


def test_order_confirmation_creates_order(client, customer_id):
    response = complete_order(client, customer_id)
    assert response.json()["state"] == "completed"


def test_repeat_confirmation_does_not_create_new_order(client, customer_id):
    complete_order(client, customer_id)

    response = client.post(
        "/api/v1/conversations/message",
        json={
            "customer_id": customer_id,
            "channel": "internal",
            "message": "YES",
        },
    )

    assert response.status_code == 200, response.text
    assert "already" in response.json()["reply"].lower()