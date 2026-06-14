import json

import pika


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

    def ping(self) -> bool:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            channel = connection.channel()
            channel.queue_declare(queue=self.queue_name, durable=True)
            connection.close()
            return True
        except Exception:
            return False

    def publish(self, payload: dict) -> bool:
        try:
            self._connect()
            self.channel.basic_publish(
                exchange="",
                routing_key=self.queue_name,
                body=json.dumps(payload),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            return True
        except Exception:
            self.close()
            return False

    def close(self) -> None:
        if self.channel and not self.channel.is_closed:
            self.channel.close()
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        self.channel = None
        self.connection = None
