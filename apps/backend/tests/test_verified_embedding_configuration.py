import pytest
from app.core.config import Settings
from app.services.embedding_provider import LiteLLMEmbeddingProvider
from app.services.vector_store import PgVectorQueryStore


def test_strategies_are_independent_off_by_default_and_require_verified_space():
    settings = Settings()
    assert not any([settings.rag_verified_enabled, settings.rag_contextual_enabled, settings.rag_hybrid_enabled])
    assert Settings(embedding_mapping_sha256='').embedding_mapping_sha256 is None
    for options in [{'rag_hybrid_enabled': True}, {'rag_contextual_enabled': True}, {'rag_verified_enabled': True}]:
        with pytest.raises(ValueError): Settings(**options)
    assert Settings(embedding_dimension=1536, rag_verified_enabled=True, rag_hybrid_enabled=True).rag_hybrid_enabled
    with pytest.raises(ValueError): Settings(embedding_mapping_sha256='unverified')


@pytest.mark.parametrize('defect', ['model', 'alias', 'index', 'bool', 'missing_index', 'zero_after_storage'])
def test_verified_question_reply_requires_model_index_and_nonzero_canonical_vector(defect):
    provider = object.__new__(LiteLLMEmbeddingProvider)
    provider.dimension, provider.expected_model = 1536, 'openai/text-embedding-3-small'
    provider.alias, provider.deployment_id, provider.mapping_sha256 = 'economicon-embedding', 'deployment-1', 'a' * 64
    gateway = {'model_id': 'deployment-1', 'model_name': 'openrouter/openai/text-embedding-3-small'}
    response = {'model': 'text-embedding-3-small', 'data': [{'index': 0, 'embedding': [1.] + [0.] * 1535}]}
    assert provider._vector(response, gateway) == [1.] + [0.] * 1535
    if defect == 'model': response['model'] = 'different-1536-model'
    elif defect == 'alias': response['model'] = 'economicon-embedding'
    elif defect == 'index': response['data'][0]['index'] = 1
    elif defect == 'bool': response['data'][0]['index'] = False
    elif defect == 'missing_index': response['data'][0].pop('index')
    elif defect == 'zero_after_storage':
        with pytest.raises(ValueError): PgVectorQueryStore._verified_vector([.00000049] * 1536)
        return
    assert provider._vector(response, None if defect == 'alias' else gateway) == 'invalid_response'


def test_verified_litellm_requires_mapping_and_deployment_configuration():
    options = dict(embedding_provider='litellm', embedding_dimension=1536,
        litellm_api_key='synthetic-binding-key', embedding_mapping_sha256='a' * 64,
        rag_verified_enabled=True)
    with pytest.raises(ValueError): Settings(**options)
    assert Settings(**options, embedding_deployment_id='deployment-1').embedding_deployment_id == 'deployment-1'
    for identifier in ['', 'bad/id', 'x' * 129, 123, True]:
        with pytest.raises(ValueError): Settings(**options, embedding_deployment_id=identifier)
    assert Settings(embedding_deployment_id='').embedding_deployment_id is None
