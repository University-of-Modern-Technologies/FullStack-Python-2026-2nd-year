import json
from datetime import datetime

import pika

credentials = pika.PlainCredentials("guest", "guest")
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost", port=5672, credentials=credentials)
)
channel = connection.channel()

channel.exchange_declare(exchange="bachelor exchange", exchange_type="direct")
channel.queue_declare(queue="bachelor", durable=True)
channel.queue_bind(
    exchange="bachelor exchange", queue="bachelor", routing_key="bachelor"
)


def create_tasks(nums: int):
    for i in range(nums):
        message = {"id": i, "payload": f"Date: {datetime.now().isoformat()}"}

        channel.basic_publish(
            exchange="bachelor exchange",
            routing_key="bachelor",
            body=json.dumps(message).encode(),
            properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent),
        )

    connection.close()


if __name__ == "__main__":
    create_tasks(100)
