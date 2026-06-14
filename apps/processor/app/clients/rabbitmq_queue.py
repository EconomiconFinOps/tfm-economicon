import json
import time
from dataclasses import dataclass

import pika


@dataclass
class QueueMessage:
    payload: dict
    delivery_tag: int


class RabbitMQQueue:
    def __init__(self, rabbitmq_url: str, queue_name: str):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.connection = None
        self.channel = None

    def _connect(self) -> None:
        if (
            self.connection
            and not self.connection.is_closed
            and self.channel
            and not self.channel.is_closed
        ):
            return

        parameters = pika.URLParameters(self.rabbitmq_url)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        self.channel.basic_qos(prefetch_count=1)

    def ping(self) -> bool:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            channel = connection.channel()
            channel.queue_declare(queue=self.queue_name, durable=True)
            connection.close()
            return True
        except Exception:
            return False

    def blocking_pop(self, timeout: int = 5) -> QueueMessage | None:
        self._connect()
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            method_frame, _, body = self.channel.basic_get(queue=self.queue_name, auto_ack=False)
            if method_frame is not None:
                return QueueMessage(
                    payload=json.loads(body),
                    delivery_tag=method_frame.delivery_tag,
                )
            time.sleep(0.5)

        return None

    def ack(self, delivery_tag: int) -> None:
        self._connect()
        self.channel.basic_ack(delivery_tag=delivery_tag)

    def nack(self, delivery_tag: int, requeue: bool = True) -> None:
        self._connect()
        self.channel.basic_nack(delivery_tag=delivery_tag, requeue=requeue)

    def close(self) -> None:
        if self.channel and not self.channel.is_closed:
            self.channel.close()
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        self.channel = None
        self.connection = None
