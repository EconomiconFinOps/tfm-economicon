import json
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError
from app.core.bedrock import BedrockError

from app.clients.bedrock import BedrockTransport


class Events:
    def __init__(self, values): self.values, self.closed = values, False
    def __iter__(self): return iter(self.values)
    def close(self): self.closed = True


def request(stream=True):
    return SimpleNamespace(data=json.dumps({'model':'economicon-chat','stream':stream,'max_tokens':800,
        'messages':[{'role':'system','content':'Reglas'},{'role':'user','content':'Pregunta'}],
        'response_format':{'type':'json_schema','json_schema':{'name':'FinOpsResponse','schema':{'type':'object'}}}}).encode(),
        _attempt_deadline=SimpleNamespace(remaining=lambda: 10), _chat_cancelled=threading.Event())


def transport():
    value = BedrockTransport(SimpleNamespace(bedrock_region='eu-west-1',bedrock_timeout_seconds=20,
        bedrock_chat_model_id='eu.amazon.nova-micro-v1:0'))
    value.runtime._client = Mock()
    return value


def events():
    return [{'messageStart':{'role':'assistant'}},
        {'contentBlockStart':{'contentBlockIndex':0,'start':{'toolUse':{'name':'FinOpsResponse','toolUseId':'return-1'}}}},
        {'contentBlockDelta':{'contentBlockIndex':0,'delta':{'toolUse':{'input':'{"response":{"answer":"Verificado"}}'}}}},
        {'contentBlockStop':{'contentBlockIndex':0}}, {'messageStop':{'stopReason':'tool_use'}},
        {'metadata':{'usage':{'inputTokens':12,'outputTokens':4,'totalTokens':16}}}]


def test_converse_stream_normalizes_only_the_approved_output_tool_and_usage():
    native = transport()
    stream = Events(events())
    native.runtime._client.converse_stream.return_value = {'stream':stream}
    with native.open(request()) as response:
        data = b''
        while block := response.read1(11): data += block
    assert response.headers['Content-Type'] == 'text/event-stream'
    lines = [line[6:] for line in data.decode().splitlines() if line.startswith('data: ')]
    assert lines[-1] == '[DONE]'
    assert json.loads(lines[0])['choices'][0]['delta']['content'] == '{"answer":"Verificado"}'
    assert json.loads(lines[-2])['usage']['prompt_tokens'] == 12
    assert stream.closed
    assert native.runtime._client.converse_stream.call_args.kwargs['modelId'] == 'eu.amazon.nova-micro-v1:0'


@pytest.mark.parametrize('defect',['wrong_tool','missing_finish','missing_usage','text_instead_of_tool'])
def test_invalid_stream_is_not_reported_as_a_completed_response(defect):
    native = transport()
    values = events()
    if defect == 'wrong_tool': values[1]['contentBlockStart']['start']['toolUse']['name']='OtherTool'
    if defect == 'missing_finish': del values[4]
    if defect == 'missing_usage': values.pop()
    if defect == 'text_instead_of_tool': values[2]['contentBlockDelta']['delta']={'text':'unstructured'}
    stream=Events(values)
    native.runtime._client.converse_stream.return_value={'stream':stream}
    with pytest.raises(ValueError):
        with native.open(request()) as response:
            while response.read1(8192): pass
    assert stream.closed


def test_cancelled_request_never_dispatches_to_bedrock():
    native = transport()
    req = request()
    req._chat_cancelled.set()
    with pytest.raises(TimeoutError): native.open(req)
    native.runtime._client.converse_stream.assert_not_called()


def test_non_streaming_summary_envelope_uses_native_schema_result():
    native = transport()
    native.runtime._client.converse.return_value={'output':{'message':{'content':[
        {'toolUse':{'name':'FinOpsResponse','input':{'response':{'answer':'Respuesta'}}}}]}},
        'stopReason':'tool_use','usage':{'inputTokens':2,'outputTokens':1,'totalTokens':3}}
    with native.open(request(False)) as response:
        value=json.loads(response.read())
    assert value['requested_model_id']=='eu.amazon.nova-micro-v1:0' and value['model'] is None
    assert json.loads(value['choices'][0]['message']['content']) == {'answer':'Respuesta'}
    assert value['choices'][0]['finish_reason']=='stop'


def test_stream_sdk_failure_never_exposes_response_or_prompt():
    native=transport()
    class Failing(Events):
        def __iter__(self):
            raise ClientError({'Error':{'Code':'ServiceUnavailableException','Message':'private prompt data'}},'ConverseStream')
    stream=Failing([])
    native.runtime._client.converse_stream.return_value={'stream':stream}
    with pytest.raises(BedrockError) as caught:
        with native.open(request()) as response: response.read1(8192)
    assert caught.value.category=='upstream' and 'private' not in str(caught.value)
    assert stream.closed
