"""Native Bedrock protocol with an injected SDK boundary; never contacts AWS."""
from io import BytesIO
import json
from unittest.mock import Mock

from botocore.exceptions import ClientError
import pytest

from app.core.bedrock import BedrockError, BedrockRuntime, embedding_fingerprint

MODEL = 'amazon.titan-embed-text-v2:0'


def test_previous_spain_contract_is_rejected_before_sdk_creation():
    with pytest.raises(ValueError):
        BedrockRuntime('eu-south-2', client=Mock())
    with pytest.raises(ValueError):
        embedding_fingerprint('eu-south-2', 1024)


def response(vector, **changes):
    return {'body': BytesIO(json.dumps(dict(embedding=vector, inputTextTokenCount=3, **changes)).encode())}


def test_titan_v2_uses_exact_model_native_dimension_and_normalization():
    sdk = Mock()
    sdk.invoke_model.return_value = response([1.0] + [0.0]*1023)
    runtime = BedrockRuntime('eu-west-1', client=sdk)
    vector, usage = runtime.embed('evidencia de coste', dimension=1024)
    assert len(vector) == 1024 and vector[0] == 1
    call = sdk.invoke_model.call_args.kwargs
    assert call['modelId'] == MODEL
    assert json.loads(call['body']) == {'inputText': 'evidencia de coste', 'dimensions': 1024, 'normalize': True}
    assert call['accept'] == call['contentType'] == 'application/json'
    assert usage == {'prompt_tokens': 3, 'model_id': MODEL, 'cost_usd': None}


@pytest.mark.parametrize('dimension', [8, 1536, True, 1024.0])
def test_rejects_non_native_dimensions_before_calling_sdk(dimension):
    sdk = Mock()
    with pytest.raises(ValueError):
        BedrockRuntime('eu-west-1', client=sdk).embed('texto', dimension=dimension)
    sdk.invoke_model.assert_not_called()


@pytest.mark.parametrize('vector', [[1.0], [0.0]*256, [float('nan')]*256, [True]*256])
def test_rejects_invalid_or_wrong_dimension_vectors(vector):
    sdk = Mock()
    sdk.invoke_model.return_value = response(vector)
    with pytest.raises(BedrockError, match='invalid_response'):
        BedrockRuntime('eu-west-1', client=sdk).embed('texto', dimension=256)


@pytest.mark.parametrize(('code','category'), [('AccessDeniedException','authentication'),
    ('ThrottlingException','rate_limit'), ('ServiceUnavailableException','upstream'),
    ('ValidationException','request')])
def test_sdk_errors_are_sanitized_and_not_retried(code, category):
    sdk = Mock()
    sdk.invoke_model.side_effect = ClientError({'Error': {'Code': code, 'Message': 'private prompt and credentials'}}, 'InvokeModel')
    with pytest.raises(BedrockError) as caught:
        BedrockRuntime('eu-west-1', client=sdk).embed('texto', dimension=256)
    assert str(caught.value) == category
    assert caught.value.category == category
    assert sdk.invoke_model.call_count == 1


def test_embedding_space_binding_changes_with_dimension_and_model_region_contract():
    a = embedding_fingerprint('eu-west-1', 1024)
    assert len(a) == 64 and a == embedding_fingerprint('eu-west-1', 1024)
    assert a != embedding_fingerprint('eu-west-1', 512)
    with pytest.raises(ValueError):
        BedrockRuntime('eu-west-3')


def test_empty_input_never_initializes_or_calls_sdk():
    sdk = Mock()
    with pytest.raises(ValueError):
        BedrockRuntime('eu-west-1', client=sdk).embed('  ', dimension=256)
    sdk.invoke_model.assert_not_called()


def test_sdk_initialization_is_lazy_role_signed_and_ignores_endpoint_overrides(monkeypatch):
    import boto3
    factory=Mock()
    monkeypatch.setattr(boto3,'client',factory)
    monkeypatch.setenv('AWS_ENDPOINT_URL_BEDROCK_RUNTIME','https://attacker.example.invalid')
    runtime=BedrockRuntime('eu-west-1',timeout=7)
    factory.assert_not_called()
    assert runtime.client() is factory.return_value
    kwargs=factory.call_args.kwargs
    assert kwargs['region_name']=='eu-west-1'
    assert kwargs['config'].signature_version=='v4'
    assert kwargs['config'].ignore_configured_endpoint_urls is True
    assert kwargs['config'].proxies == {}
    assert kwargs['config'].read_timeout == 7
    assert not any('access_key' in key or key=='endpoint_url' for key in kwargs)


def test_converse_preserves_messages_forces_schema_and_reports_actual_usage():
    sdk = Mock()
    sdk.converse.return_value = {'output': {'message': {'role':'assistant','content':[
        {'toolUse': {'toolUseId':'return-1','name':'FinOpsResponse','input':{'response':{'answer':'Verificado'}}}}]}},
        'stopReason':'tool_use','usage':{'inputTokens':10,'outputTokens':4,'totalTokens':14}}
    schema = {'type':'object','properties':{'answer':{'type':'string'}},'required':['answer'],'additionalProperties':False}
    value, usage = BedrockRuntime('eu-west-1',client=sdk).converse(
        [{'role':'system','content':'Instrucción aprobada'},{'role':'user','content':'Pregunta'},
         {'role':'user','content':'UNTRUSTED_RETRIEVAL_CONTEXT\nDato'}],schema=schema,
        schema_name='FinOpsResponse',model_id='eu.amazon.nova-micro-v1:0',max_tokens=800)
    assert value == {'answer':'Verificado'}
    assert usage == {'prompt_tokens':10,'completion_tokens':4,'total_tokens':14,
        'cost_usd':None,'model_id':'eu.amazon.nova-micro-v1:0'}
    call = sdk.converse.call_args.kwargs
    assert call['modelId'] == 'eu.amazon.nova-micro-v1:0'
    assert call['system'] == [{'text':'Instrucción aprobada'}]
    assert call['messages'] == [{'role':'user','content':[{'text':'Pregunta'},{'text':'UNTRUSTED_RETRIEVAL_CONTEXT\nDato'}]}]
    assert call['toolConfig']['toolChoice'] == {'tool':{'name':'FinOpsResponse'}}
    assert call['toolConfig']['tools'][0]['toolSpec']['inputSchema']['json'] == {
        'type':'object','properties':{'response':schema},'required':['response']}
    assert call['inferenceConfig']['maxTokens'] == 800


@pytest.mark.parametrize('change', [dict(stopReason='max_tokens'),
    dict(output={'message':{'role':'assistant','content':[{'text':'unstructured'}]}}),
    dict(output={'message':{'role':'assistant','content':[{'toolUse':{'name':'WrongTool','input':{}}}]}})])
def test_converse_rejects_truncated_unstructured_or_wrong_tool_results(change):
    sdk = Mock()
    sdk.converse.return_value = dict(output={'message':{'role':'assistant','content':[
        {'toolUse':{'name':'FinOpsResponse','input':{'answer':'ok'}}}]}},stopReason='tool_use',
        usage={'inputTokens':1,'outputTokens':1,'totalTokens':2})
    sdk.converse.return_value.update(change)
    with pytest.raises(BedrockError):
        BedrockRuntime('eu-west-1',client=sdk).converse([{'role':'user','content':'texto'}],
            schema={'type':'object'},schema_name='FinOpsResponse',model_id='eu.amazon.nova-micro-v1:0',max_tokens=800)
