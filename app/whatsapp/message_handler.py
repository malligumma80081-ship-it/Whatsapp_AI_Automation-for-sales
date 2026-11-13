import logging

from app.database.connection import SessionLocal
from app.database.models import Customer


logger = logging.getLogger(__name__)


def extract_whatsapp_messages(payload: dict):

    messages = []

    for entry in payload.get("entry", []):

        for change in entry.get("changes", []):

            value = change.get("value", {})

            contacts = value.get("contacts", [])

            contact_names = {}

            for contact in contacts:

                wa_id = contact.get("wa_id")

                profile_name = (
                    contact.get("profile", {})
                    .get("name")
                )

                if wa_id:
                    contact_names[wa_id] = profile_name

            for message in value.get("messages", []):

                sender = message.get("from")

                if not sender:
                    continue

                message_type = message.get("type")

                message_text = None

                if message_type == "text":

                    message_text = (
                        message.get("text", {})
                        .get("body")
                    )

                messages.append({
                    "sender": sender,
                    "profile_name": contact_names.get(sender),
                    "message_id": message.get("id"),
                    "message_type": message_type,
                    "message_text": message_text,
                    "timestamp": message.get("timestamp"),
                })

    return messages


def identify_customer(sender: str, profile_name: str | None):

    db = SessionLocal()

    try:

        customer = (
            db.query(Customer)
            .filter(Customer.phone == sender)
            .first()
        )

        if customer is None:

            customer = Customer(
                name=profile_name or "WhatsApp Customer",
                phone=sender,
            )

            db.add(customer)

            db.commit()

            db.refresh(customer)

            logger.info(
                "New WhatsApp customer registered: %s",
                customer.id,
            )

        return {
            "customer_id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
        }

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


def process_incoming_message(payload: dict):

    messages = extract_whatsapp_messages(payload)

    results = []

    for message in messages:

        customer = identify_customer(
            sender=message["sender"],
            profile_name=message["profile_name"],
        )

        results.append({
            "customer": customer,
            "message": message,
            "status": "received",
        })

        logger.info(
            "WhatsApp message received from customer %s",
            customer["customer_id"],
        )

    return results