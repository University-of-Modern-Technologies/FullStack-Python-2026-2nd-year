import json
from datetime import datetime

import pika

from config import (
    RABBITMQ_EXCHANGE,
    RABBITMQ_HOST,
    RABBITMQ_PASSWORD,
    RABBITMQ_PORT,
    RABBITMQ_QUEUE,
    RABBITMQ_USER,
    RABBITMQ_VIRTUAL_HOST,
)
from models import Task

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        virtual_host=RABBITMQ_VIRTUAL_HOST,
    )
)
channel = connection.channel()

exchange = RABBITMQ_EXCHANGE
queue_name = RABBITMQ_QUEUE

channel.exchange_declare(exchange=exchange, exchange_type="direct")
channel.queue_declare(queue=queue_name, durable=True)
channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=queue_name)


def create_tasks(nums: int):
    for i in range(nums):
        task = Task(consumer="Noname").save()

        channel.basic_publish(
            exchange=exchange,
            routing_key=queue_name,
            body=str(task.id).encode(),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent
            ),
        )

    connection.close()


if __name__ == "__main__":
    create_tasks(1000)
