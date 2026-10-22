from io import BytesIO
import json
from pathlib import Path
from unittest.mock import Mock

from app.core.config import Settings
from app.services.embedding_provider import BedrockEmbeddingProvider
from app.services.vector_store import PgVectorQueryStore
import pytest


def test_verified_native_embedding_settings_and_backend_provider():
    settings = Settings(embedding_provider='bedrock',embedding_model='amazon.titan-embed-text-v2:0',
        embedding_dimension=1024,bedrock_region='eu-west-1',rag_verified_enabled=True,_env_file=None)
    provider = BedrockEmbeddingProvider(settings)
    sdk = Mock()
    sdk.invoke_model.return_value = {'body': BytesIO(json.dumps({'embedding': [1.0]+[0.0]*1023,
        'inputTextTokenCount': 4}).encode())}
    provider.runtime._client = sdk
    assert len(provider.embed('coste del servicio')) == 1024
    assert provider.name == 'bedrock' and len(provider.mapping_sha256) == 64
    assert settings.litellm_api_key is None


def test_services_share_the_exact_native_protocol_implementation():
    root = Path(__file__).resolve().parents[3]
    assert (root/'apps/backend/app/core/bedrock.py').read_bytes() == (root/'apps/processor/app/core/bedrock.py').read_bytes()


def test_verified_query_vector_requires_the_exact_native_space_dimension():
    assert len(PgVectorQueryStore._verified_vector([1.0]+[0.0]*1023,dimension=1024)) == 1024
    with pytest.raises(ValueError):
        PgVectorQueryStore._verified_vector([1.0]+[0.0]*1535,dimension=1024)


def test_native_model_id_cannot_be_labelled_as_mock():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Settings(embedding_provider='mock',embedding_model='amazon.titan-embed-text-v2:0',_env_file=None)
