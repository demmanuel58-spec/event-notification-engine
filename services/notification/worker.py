import pika
import json
import os
import time

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

def process_notification(event_type: str, data: dict):
    """Simulates multi-channel notification dispatch logic."""
    print(f" [->] Processing '{event_type}' for user {data.get('email', 'N/A')}...")
    
    # Simulate processing work
    time.sleep(2)
    
    if event_type == "user.registered":
        print(f" [EMAIL SENT] Welcome email dispatched to {data.get('email')}")
    elif event_type == "security.alert":
        print(f" [SMS SENT] Security alert sent to {data.get('phone', 'N/A')}")
    else:
        print(f" [GENERIC] Notification logged for {event_type}")

def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        event_type = message.get("event_type")
        data = message.get("data", {})
        
        process_notification(event_type, data)
        
        # Acknowledge successful execution
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        print(f" [!] Execution error processing message: {exc}")
        # Reject and drop/route to Dead-Letter Queue (requeue=False)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_worker():
    print(" [*] Connecting to RabbitMQ Broker...")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()

    # 1. Declare Dead-Letter Exchange & Queue
    channel.exchange_declare(exchange='dlx_exchange', exchange_type='direct')
    channel.queue_declare(queue='notification_dlq', durable=True)
    channel.queue_bind(exchange='dlx_exchange', queue='notification_dlq', routing_key='dlq_key')

    # 2. Declare Primary Exchange & Queue bound to DLX
    channel.exchange_declare(exchange='events_exchange', exchange_type='topic')
    channel.queue_declare(
        queue='notification_queue',
        durable=True,
        arguments={
            'x-dead-letter-exchange': 'dlx_exchange',
            'x-dead-letter-routing-key': 'dlq_key'
        }
    )
    
    # Bind queue to listen to all notification routing keys
    channel.queue_bind(exchange='events_exchange', queue='notification_queue', routing_key='notification.#')

    # Fair dispatching: don't give more than 1 unacknowledged message to a worker
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='notification_queue', on_message_callback=callback)

    print(" [*] Notification Consumer Worker initialized. Waiting for events...")
    channel.start_consuming()

if __name__ == "__main__":
    start_worker()
