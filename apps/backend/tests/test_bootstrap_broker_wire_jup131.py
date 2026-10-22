"""Opt-in against an isolated, unpublished, disposable RabbitMQ container.

Run tests in a container sharing only that broker's network namespace. The
management transport is loopback HTTP; production HTTPS remains tested separately.
"""
import base64
import http.client
import json
import os
import time

import pytest

from test_bootstrap_broker_jup131 import context


@pytest.mark.skipif(os.getenv('JUP131_BROKER_TEST') != 'disposable-container', reason='Dedicated broker opt-in absent')
def test_real_vhost_permissions_publish_consume_and_idempotence(monkeypatch):
    import pika
    from app import aws_bootstrap_broker as module

    def request(method, path, payload=None, username='economicon_admin', password='Synthetic-broker-test-pass-131!'):
        connection = http.client.HTTPConnection('127.0.0.1', 15672, timeout=3)
        try:
            body = None if payload is None else json.dumps(payload)
            authorization = 'Basic ' + base64.b64encode((username + ':' + password).encode()).decode()
            connection.request(method, '/api/' + path, body=body,
                               headers={'Authorization': authorization, 'Content-Type': 'application/json'})
            response = connection.getresponse()
            raw = response.read(65537)
            assert len(raw) <= 65536
            return response.status, json.loads(raw) if raw else None
        finally:
            connection.close()

    for attempt in range(30):
        try:
            status, users = request('GET', 'users')
            if status == 200:
                break
        except (ConnectionError, OSError):
            pass
        time.sleep(1)
    else:
        pytest.fail('Dedicated broker did not become ready')
    assert [user['name'] for user in users] == ['economicon_admin'], 'Refusing a broker with existing application users'
    assert [vhost['name'] for vhost in request('GET', 'vhosts')[1]] == ['/'], 'Refusing an existing application broker'

    class LocalBroker(module.BrokerAPI):
        def request(self, method, path, body=None):
            status, value = request(method, path.removeprefix('/api/'), body)
            if status == 404 and method == 'GET':
                return None
            assert status in {200, 201, 204}, (method, path, status)
            return value or {}

    monkeypatch.setattr(module, 'BrokerAPI', LocalBroker)
    ctx = context()
    module.configure_broker(ctx)
    module.configure_broker(ctx)
    connections = []
    try:
        channels = []
        for name in ('backend', 'processor'):
            password = ctx.secret('bundle')['mq_passwords'][name]
            connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1', 5672,
                virtual_host='economicon-ensayo1', credentials=pika.PlainCredentials('economicon_' + name, password),
                socket_timeout=3, blocked_connection_timeout=3))
            connections.append(connection)
            channels.append(connection.channel())
        channels[0].queue_declare(queue='processor:jobs', durable=True)
        channels[1].queue_declare(queue='processor:jobs', durable=True)
        channels[0].confirm_delivery()
        channels[0].basic_publish(exchange='', routing_key='processor:jobs', body=b'synthetic-jup131', mandatory=True)
        method, _, body = channels[1].basic_get('processor:jobs', auto_ack=False)
        assert method is not None and body == b'synthetic-jup131'
        channels[1].basic_ack(method.delivery_tag)
        with pytest.raises(pika.exceptions.ChannelClosedByBroker) as caught:
            connections[0].channel().queue_declare(queue='forbidden-other-queue')
        assert caught.value.reply_code == 403
        assert request('GET', 'users', username='economicon_backend', password=ctx.secret('bundle')['mq_passwords']['backend'])[0] in {401, 403}
    finally:
        for connection in connections:
            if connection.is_open:
                connection.close()
