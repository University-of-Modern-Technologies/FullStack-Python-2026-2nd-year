import os
import sys

import pika

from config import (
    RABBITMQ_CONSUMER_NAME,
    RABBITMQ_HOST,
    RABBITMQ_PASSWORD,
    RABBITMQ_PORT,
    RABBITMQ_QUEUE,
    RABBITMQ_USER,
    RABBITMQ_VIRTUAL_HOST,
)
from models import Task


def main():
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
    queue_name = RABBITMQ_QUEUE
    channel.queue_declare(queue=queue_name, durable=True)

    consumer = RABBITMQ_CONSUMER_NAME

    def callback(ch, method, properties, body):
        pk = body.decode()
        task = Task.objects(id=pk, completed=False).first()
        if task:
            task.update(set__completed=True, set__consumer=consumer)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)

    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
