"""JUP-113 (tarea 4.1): `QueueMessage.redelivered` y su lectura desde `basic_get`.

RabbitMQ marca `redelivered` en la respuesta de `basic_get`: falso solo en la primera
entrega y verdadero tras un `nack(requeue=True)` o tras perder la conexion sin responder.
El worker usa esa marca para acotar a UN reintento los fallos no clasificados, asi que la
cola tiene que transportarla fielmente al `QueueMessage`.

Contrato que fijan estas pruebas (lo implementa el coder):
- `QueueMessage` gana un tercer campo `redelivered: bool = False`; las construcciones
  existentes (`QueueMessage(job, 42)`, `QueueMessage(job, delivery_tag=7)`) siguen valiendo.
- `RabbitMQQueue.blocking_pop` lo rellena con `bool(method_frame.redelivered)`; si el frame
  no tiene el atributo vale `False`: ante la duda se trata como primera entrega, es decir,
  se reencola y NUNCA se descarta por error.

Solo se dobla el canal de pika (la frontera de red); `RabbitMQQueue` es el real.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.clients.rabbitmq_queue import QueueMessage, RabbitMQQueue


JOB = {"id": "job-redelivered", "created_by": "alice"}


def queue_with_deliveries(*deliveries):
    """Cola real con el canal doblado: cada `basic_get` devuelve la siguiente entrega."""
    queue = RabbitMQQueue("amqp://127.0.0.1:9/%2F", "jup113.redelivered-unit")
    queue._connect = MagicMock()
    queue.channel = MagicMock()
    queue.channel.basic_get.side_effect = deliveries
    return queue


def delivery(frame, payload=JOB):
    """Tupla `(method_frame, properties, body)` como la devuelve `basic_get`."""
    return frame, None, json.dumps(payload).encode()


# ----------------------------------------------------------------- dataclass

def test_queue_message_defaults_to_first_delivery():
    # Compatibilidad hacia atras: quien construye el mensaje sin la marca (todos los tests
    # y el codigo previo) obtiene "primera entrega", que es la rama segura (se reencola).
    assert QueueMessage(JOB, 42).redelivered is False
    assert QueueMessage(JOB, delivery_tag=7).redelivered is False
    assert QueueMessage(payload=JOB, delivery_tag=7).redelivered is False


def test_queue_message_accepts_redelivered_by_keyword():
    # La marca se puede fijar por palabra clave (es lo que usan los tests del worker).
    message = QueueMessage(JOB, delivery_tag=7, redelivered=True)

    assert message.redelivered is True
    assert message.delivery_tag == 7
    assert message.payload == JOB


def test_queue_message_redelivered_does_not_alter_equality_of_other_fields():
    # Es un campo de pleno derecho del dataclass: dos entregas del mismo trabajo y mismo tag
    # que difieren solo en la marca no son iguales (la marca viaja con el mensaje).
    assert QueueMessage(JOB, 7, redelivered=True) != QueueMessage(JOB, 7)
    assert QueueMessage(JOB, 7, redelivered=False) == QueueMessage(JOB, 7)


# ----------------------------------------------------------------- blocking_pop

@pytest.mark.parametrize("flag", [True, False])
def test_blocking_pop_copies_redelivered_flag_from_frame(flag):
    # Caso central: la marca del frame de `basic_get` llega tal cual al mensaje, en ambos
    # sentidos (si solo se propagase el verdadero, o se fijase siempre, uno de los dos falla).
    queue = queue_with_deliveries(delivery(SimpleNamespace(delivery_tag=21, redelivered=flag)))

    message = queue.blocking_pop(timeout=2)

    assert message is not None
    assert message.redelivered is flag
    assert message.delivery_tag == 21
    assert message.payload == JOB


def test_blocking_pop_treats_frame_without_redelivered_as_first_delivery():
    # Edge case: un frame sin el atributo (dobles existentes como `SimpleNamespace(delivery_tag=18)`)
    # se trata como primera entrega. Ante la duda se reencola; jamas se descarta por error.
    queue = queue_with_deliveries(delivery(SimpleNamespace(delivery_tag=18)))

    message = queue.blocking_pop(timeout=2)

    assert message is not None
    assert message.redelivered is False
    assert message.delivery_tag == 18


@pytest.mark.parametrize("raw,expected", [(1, True), (0, False), ("si", True), ("", False), (None, False)])
def test_blocking_pop_coerces_non_boolean_redelivered_with_bool(raw, expected):
    # El campo es siempre un `bool` estricto (el worker lo compara por veracidad, pero el
    # contrato del dataclass es booleano): valores truthy/falsy se convierten con `bool()`.
    queue = queue_with_deliveries(delivery(SimpleNamespace(delivery_tag=22, redelivered=raw)))

    message = queue.blocking_pop(timeout=2)

    assert message is not None
    assert message.redelivered is expected


def test_unreadable_message_is_discarded_and_does_not_affect_next_redelivered_flag():
    # Un mensaje ilegible (JSON invalido) se descarta con `nack(requeue=False)` como hoy,
    # aunque venga marcado como reentrega, y el siguiente conserva SU PROPIA marca: la del
    # envenenado no se "arrastra" ni se pierde la del valido.
    queue = queue_with_deliveries(
        (SimpleNamespace(delivery_tag=30, redelivered=True), None, b"{esto no es json"),
        delivery(SimpleNamespace(delivery_tag=31, redelivered=False)),
    )

    message = queue.blocking_pop(timeout=2)

    queue.channel.basic_nack.assert_called_once_with(delivery_tag=30, requeue=False)
    queue.channel.basic_ack.assert_not_called()
    assert message is not None
    assert message.delivery_tag == 31
    assert message.redelivered is False
    assert queue.channel.basic_get.call_count == 2


def test_valid_redelivered_message_follows_unreadable_first_delivery():
    # Simetrico al anterior: el ilegible es primera entrega y el siguiente es una reentrega
    # valida; la marca verdadera del segundo se conserva.
    queue = queue_with_deliveries(
        (SimpleNamespace(delivery_tag=40, redelivered=False), None, b"\xff\xfe no utf-8"),
        delivery(SimpleNamespace(delivery_tag=41, redelivered=True)),
    )

    message = queue.blocking_pop(timeout=2)

    queue.channel.basic_nack.assert_called_once_with(delivery_tag=40, requeue=False)
    assert message is not None
    assert message.delivery_tag == 41
    assert message.redelivered is True
