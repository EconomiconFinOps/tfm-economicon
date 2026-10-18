import copy
import json
import math
import pytest
from app.clients.litellm import ProviderError
from app.embeddings.providers import LiteLLMEmbeddingProvider


class Counter:
    def count(self, value):
        return len(value)


class Client:
    def __init__(self):
        self.calls = []
        self.change = lambda value: value
        self.gateway = {'model_id': 'deployment-1', 'model_name': 'openrouter/openai/text-embedding-3-small'}

    def post(self, endpoint, payload, *, with_usage):
        assert endpoint == 'embeddings' and with_usage
        self.calls.append(copy.deepcopy(payload))
        response = {'model': 'text-embedding-3-small', 'data': [
            {'index': index, 'embedding': [float(ord(value[0]))] + [0.] * 1535}
            for index, value in reversed(list(enumerate(payload['input'])))]}
        return self.change(response), {'cost_usd': None, 'attempts': 1, 'gateway': copy.deepcopy(self.gateway)}


@pytest.fixture
def provider():
    value = object.__new__(LiteLLMEmbeddingProvider)
    value.dimension, value.name, value.model = 1536, 'litellm', 'economicon-embedding'
    value.client, value.usage_records = Client(), []
    value.deployment_id, value.mapping_sha256 = 'deployment-1', 'a' * 64
    return value


def test_batch_order_partition_limits_and_unknown_usage(provider):
    values = ['a' * 6, 'b' * 6, 'c' * 3, 'd' * 2, 'e']
    result = provider.embed_batch(values, expected_model='openai/text-embedding-3-small', counter=Counter(), max_items=2, max_tokens=10)
    assert [vector[0] for vector in result] == [97., 98., 99., 100., 101.]
    assert [item['input'] for item in provider.client.calls] == [[values[0]], values[1:3], values[3:]]
    assert all(sum(map(len, item['input'])) <= 10 for item in provider.client.calls)
    assert len(provider.usage_records) == 3 and all(item['cost_usd'] is None for item in provider.usage_records)


def test_wire_bytes_unicode_partition_and_single_input_rejection(provider):
    values = ['á' * 100] * 3
    provider.embed_batch(values, expected_model='openai/text-embedding-3-small', counter=Counter(), max_bytes=1400)
    assert len(provider.client.calls) == 2
    assert all(len(json.dumps(item, allow_nan=False).encode()) <= 1400 for item in provider.client.calls)
    with pytest.raises(ValueError):
        provider.embed_batch(['á' * 500], expected_model='openai/text-embedding-3-small', counter=Counter(), max_bytes=1024)
    assert len(provider.client.calls) == 2


@pytest.mark.parametrize('defect', ['missing_index', 'duplicate_index', 'bool_index', 'negative_index', 'missing_item',
                                  'wrong_model', 'alias_model', 'dimension', 'nan', 'infinity', 'bool_value', 'zero', 'missing_data'])
def test_invalid_complete_response_is_terminal_without_partial_result(provider, defect):
    def corrupt(response):
        if defect == 'missing_index': response['data'][0].pop('index')
        elif defect == 'duplicate_index': response['data'][0]['index'] = response['data'][1]['index']
        elif defect == 'bool_index': response['data'][0]['index'] = True
        elif defect == 'negative_index': response['data'][0]['index'] = -1
        elif defect == 'missing_item': response['data'].pop()
        elif defect == 'wrong_model': response['model'] = 'another-1536-model'
        elif defect == 'alias_model': response['model'] = 'economicon-embedding'
        elif defect == 'dimension': response['data'][0]['embedding'].pop()
        elif defect == 'nan': response['data'][0]['embedding'][0] = math.nan
        elif defect == 'infinity': response['data'][0]['embedding'][0] = math.inf
        elif defect == 'bool_value': response['data'][0]['embedding'][0] = True
        elif defect == 'zero': response['data'][0]['embedding'] = [0.] * 1536
        elif defect == 'missing_data': response.pop('data')
        return response
    provider.client.change = corrupt
    if defect == 'alias_model': provider.client.gateway = {}  # Alias without deployment proof remains invalid.
    with pytest.raises(ProviderError) as failure:
        provider.embed_batch(['a', 'b'], expected_model='openai/text-embedding-3-small', counter=Counter())
    assert failure.value.category == 'invalid_response' and len(provider.client.calls) == 1
    assert len(provider.usage_records) == 1  # A malformed response can still have a charge.


def test_transport_failure_retains_unknown_cost_and_does_not_retry_at_batch_layer(provider):
    def fail(*args, **kwargs):
        raise ProviderError('timeout')
    provider.client.post = fail
    with pytest.raises(ProviderError):
        provider.embed_batch(['a'], expected_model='openai/text-embedding-3-small', counter=Counter())
    assert provider.usage_records == [{'cost_usd': None, 'status': 'unknown'}]


@pytest.mark.parametrize('model', ['economicon-embedding', 'openai/text-embedding-3-small', 'text-embedding-3-small'])
def test_bound_deployment_accepts_alias_or_compatible_resolved_model(provider, model):
    provider.client.change = lambda response: dict(response, model=model)
    assert provider.embed_batch(['a'], expected_model='openai/text-embedding-3-small', counter=Counter())[0][0] == 97.


@pytest.mark.parametrize('defect', ['missing_id', 'wrong_id', 'wrong_header_model', 'wrong_body_model'])
def test_deployment_contradictions_are_terminal_and_retain_reported_charge(provider, defect):
    provider.client.change = lambda response: dict(response, model='economicon-embedding')
    if defect == 'missing_id': provider.client.gateway.pop('model_id')
    elif defect == 'wrong_id': provider.client.gateway['model_id'] = 'different-deployment'
    elif defect == 'wrong_header_model': provider.client.gateway['model_name'] = 'openrouter/another-1536-model'
    elif defect == 'wrong_body_model': provider.client.change = lambda response: dict(response, model='another-1536-model')
    with pytest.raises(ProviderError, match='invalid_response'):
        provider.embed_batch(['a'], expected_model='openai/text-embedding-3-small', counter=Counter())
    assert len(provider.client.calls) == len(provider.usage_records) == 1


@pytest.mark.parametrize('field', ['mapping_sha256', 'deployment_id'])
def test_missing_accredited_binding_fails_before_paid_batch(provider, field):
    setattr(provider, field, None)
    with pytest.raises(ValueError, match='binding'):
        provider.embed_batch(['a'], expected_model='openai/text-embedding-3-small', counter=Counter())
    assert provider.client.calls == provider.usage_records == []


def test_native_transport_keeps_model_body_and_deployment_headers_separate(provider):
    import io
    from types import SimpleNamespace
    from pydantic import SecretStr
    from app.clients.litellm import LiteLLMClient
    body = {'model': 'economicon-embedding', 'usage': {'prompt_tokens': 1, 'total_tokens': 1},
            'data': [{'index': 0, 'embedding': [1.] + [0.] * 1535}]}
    response = io.BytesIO(json.dumps(body).encode())
    response.status = 200
    response.headers = {'x-litellm-model-id': 'deployment-1',
                        'x-litellm-model-name': 'openrouter/openai/text-embedding-3-small',
                        'x-litellm-call-id': 'call-1', 'x-litellm-response-cost': '0.01'}
    client = LiteLLMClient(SimpleNamespace(litellm_base_url='http://127.0.0.1:9/v1',
        litellm_api_key=SecretStr('synthetic-unit-key'), llm_max_retries=0, llm_timeout_seconds=1))
    class Opener:
        def open(self, request, **kwargs):
            assert json.loads(request.data)['model'] == 'economicon-embedding'
            return response
    client.transport = Opener()
    provider.client = client
    assert provider.embed_batch(['a'], expected_model='openai/text-embedding-3-small', counter=Counter()) == [[1.] + [0.] * 1535]
    assert body['model'] == 'economicon-embedding'
    assert provider.usage_records[0]['gateway']['model_id'] == 'deployment-1'
    assert provider.usage_records[0]['cost_usd'] == .01


@pytest.mark.parametrize('identifier', [' whitespace', 'bad/id', 'x' * 129, 12, True])
def test_processor_deployment_id_is_bounded_explicit_configuration(identifier):
    from app.core.config import Settings
    with pytest.raises(ValueError): Settings(embedding_deployment_id=identifier)


def test_invalid_deployment_cannot_reach_actual_cache_writer(provider, monkeypatch):
    import hashlib
    from contextlib import contextmanager
    from types import SimpleNamespace
    from app.embeddings.space import EmbeddingSpace
    from app.vector_store.generations import GenerationStore
    class Engine:
        writes = 0
        @contextmanager
        def connect(self): yield self
        def execute(self, *args): return []
        def begin(self):
            self.writes += 1
            raise AssertionError('Rejected identity reached cache writer')
    engine = Engine()
    store = GenerationStore(engine, counter=Counter())
    monkeypatch.setattr(store, 'register_space', lambda value: None)
    provider.client.gateway['model_id'] = 'wrong-deployment'
    space = EmbeddingSpace('litellm', 'openai/text-embedding-3-small', 'a' * 64, 'synthetic-tokenizer')
    prepared = SimpleNamespace(text='a', text_hash=hashlib.sha256(b'a').hexdigest(), token_count=1)
    with pytest.raises(ProviderError, match='invalid_response'):
        store.cache_embeddings('tenant-a', space, [prepared], provider)
    assert engine.writes == 0 and len(provider.client.calls) == 1


def test_mapping_mismatch_rejected_before_batch_or_cache_access(provider, monkeypatch):
    from app.embeddings.space import EmbeddingSpace
    from app.vector_store.generations import GenerationStore
    store = GenerationStore(None)
    monkeypatch.setattr(store, 'register_space', lambda value: None)
    space = EmbeddingSpace('litellm', 'openai/text-embedding-3-small', 'b' * 64, 'synthetic-tokenizer')
    with pytest.raises(ValueError, match='incompatible'):
        store.cache_embeddings('tenant-a', space, [], provider)
    assert provider.client.calls == []


def test_legacy_batch_remains_unknown_without_binding_while_verified_call_is_strict(provider):
    provider.mapping_sha256 = provider.deployment_id = None
    provider.client.gateway = {}
    provider.client.change = lambda response: dict(response, model='economicon-embedding')
    assert provider.embed_batch(['a'], counter=Counter())[0][0] == 97.
    assert len(provider.client.calls) == 1
    with pytest.raises(ValueError, match='binding'):
        provider.embed_batch(['a'], expected_model='openai/text-embedding-3-small', counter=Counter())
    assert len(provider.client.calls) == 1
