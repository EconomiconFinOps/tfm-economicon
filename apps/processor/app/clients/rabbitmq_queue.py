import json
import time
from dataclasses import dataclass

import pika


@dataclass
class QueueMessage:
    payload: dict
    delivery_tag: int
    # Marca `redelivered` de RabbitMQ: falsa solo en la primera entrega y verdadera tras un
    # `nack(requeue=True)` o tras perder la conexion sin responder. El worker la usa para
    # acotar a una reentrega los fallos no clasificados (JUP-113). Por defecto es `False`
    # ("primera entrega"), la rama segura (se reencola, nunca se descarta por error), de
    # modo que las construcciones existentes `QueueMessage(job, 42)` siguen valiendo. El
    # dataclass se mantiene mutable (sin `frozen` ni `__slots__`) como hasta ahora.
    redelivered: bool = False


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
                try:
                    payload = json.loads(body)
                except (ValueError, UnicodeError, RecursionError):
                    self.nack(method_frame.delivery_tag, requeue=False)
                    continue
                return QueueMessage(
                    payload=payload,
                    delivery_tag=method_frame.delivery_tag,
                    # `getattr` con valor por defecto a proposito: un frame sin el atributo
                    # (dobles de prueba existentes o una respuesta atipica) se trata como
                    # primera entrega. Ante la duda se reencola, jamas se descarta por error;
                    # `bool()` mantiene el campo estrictamente booleano.
                    redelivered=bool(getattr(method_frame, "redelivered", False)),
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
