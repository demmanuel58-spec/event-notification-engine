import pika
import json
import os

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

def publish_event(event_type: str, payload: dict):
    """Publishes an asynchronous event to the RabbitMQ exchange."""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()

    # Declare a topic exchange for flexible event routing
    channel.exchange_declare(exchange='events_exchange', exchange_type='topic')

    message = {
        "event_type": event_type,
        "data": payload
    }

    routing_key = f"notification.{event_type}"
    channel.basic_publish(
        exchange='events_exchange',
        routing_key=routing_key,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
        )
    )
    print(f" [x] Sent '{routing_key}': {message}")
    connection.close()
