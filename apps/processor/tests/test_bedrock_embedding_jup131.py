from io import BytesIO
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.bedrock import TITAN_MODEL, embedding_fingerprint
from app.embeddings.providers import get_embedding_provider
from app.embeddings.space import EmbeddingSpace


def settings(**changes):
    return Settings(embedding_provider='bedrock', embedding_model=TITAN_MODEL,
        embedding_dimension=1024, bedrock_region='eu-south-2', **changes, _env_file=None)


def test_configuration_accepts_native_bedrock_without_gateway_credentials():
    s = settings()
    assert s.litellm_api_key is None
    assert s.embedding_dimension == 1024


def test_native_factory_and_verified_batches_bind_exact_model_and_configuration():
    provider = get_embedding_provider('bedrock', 1024, settings())
    sdk = Mock()
    sdk.invoke_model.side_effect = lambda **kwargs: {'body': BytesIO(json.dumps({
        'embedding': [1.0]+[0.0]*1023, 'inputTextTokenCount': 3}).encode())}
    provider.runtime._client = sdk
    vectors = provider.embed_batch(['evidencia uno', 'evidencia dos'], expected_model=TITAN_MODEL,
        counter=SimpleNamespace(count=lambda text: 3))
    assert len(vectors) == 2 and all(len(vector) == 1024 for vector in vectors)
    assert provider.name == 'bedrock' and provider.dimension == 1024
    assert provider.mapping_sha256 == embedding_fingerprint('eu-south-2',1024)
    assert len(provider.usage_records) == 2
    with pytest.raises(ValueError):
        provider.embed_batch(['texto'], expected_model='openai/text-embedding-3-small',
            counter=SimpleNamespace(count=lambda text: 3))
    assert sdk.invoke_model.call_count == 2


@pytest.mark.parametrize('changes', [dict(bedrock_region=None), dict(embedding_dimension=1536),
    dict(embedding_model='economicon-embedding')])
def test_rejects_unbound_or_incompatible_native_settings(changes):
    values=dict(embedding_provider='bedrock',embedding_model=TITAN_MODEL,
        embedding_dimension=1024,bedrock_region='eu-south-2')
    values.update(changes)
    with pytest.raises(ValidationError):
        Settings(**values, _env_file=None)


def test_native_space_has_a_different_identity_and_rejects_relabelled_dimensions():
    identity = EmbeddingSpace('bedrock', TITAN_MODEL, embedding_fingerprint('eu-south-2',1024),
        'preparation-tokenizer', dimension=1024)
    assert EmbeddingSpace.from_descriptor(identity.descriptor()) == identity
    with pytest.raises(ValueError):
        EmbeddingSpace('bedrock',TITAN_MODEL,identity.mapping_sha256,identity.tokenizer_id,dimension=1536)
    with pytest.raises(ValueError):
        EmbeddingSpace('litellm','openai/text-embedding-3-small',identity.mapping_sha256,identity.tokenizer_id,dimension=1024)


def test_native_model_id_cannot_be_labelled_as_a_gateway_or_mock_model():
    with pytest.raises(ValidationError):
        Settings(embedding_provider='mock',embedding_model=TITAN_MODEL,_env_file=None)
    with pytest.raises(ValidationError):
        Settings(llm_model=TITAN_MODEL,_env_file=None)
