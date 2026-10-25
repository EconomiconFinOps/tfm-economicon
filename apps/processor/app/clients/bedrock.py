"""Normalize native Converse output for the existing guarded chat/summary parser.

This boundary invokes only the AWS SDK. It opens no OpenAI-compatible HTTP
endpoint and invents no provider identity, price or completed answer.
"""
import io
import json
from botocore.exceptions import ClientError, BotoCoreError

from app.core.bedrock import BedrockRuntime, BedrockError, MAX_RESPONSE_BYTES, NativeToolJSON, _error, conversation_parameters, conversation_usage


class _JSONResponse(io.BytesIO):
    status = 200
    headers = {'Content-Type': 'application/json'}


def _sse(value):
    return ('data: ' + json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n\n').encode('utf-8')


class _NativeStream:
    status = 200
    headers = {'Content-Type': 'text/event-stream'}

    def __init__(self, stream, req, schema_name, model_id, close_client, schema):
        self.stream, self.req, self.schema_name, self.model_id = stream, req, schema_name, model_id
        self.close_client = close_client
        self.closed, self.buffer = False, b''
        self.records = iter(self._records())
        self.decoder = NativeToolJSON(schema)

    def __enter__(self): return self
    def __exit__(self, *args): self.close()

    def close(self):
        if not self.closed:
            self.closed = True
            try: self.stream.close()
            finally: self.close_client()

    def read1(self, size=8192):
        if self.closed: return b''
        if type(size) is not int or size <= 0: raise ValueError('Invalid native read size')
        while not self.buffer:
            try: self.buffer = next(self.records)
            except StopIteration: return b''
            except (ClientError,BotoCoreError) as failure:
                raise _error(failure) from None
        result, self.buffer = self.buffer[:size], self.buffer[size:]
        return result

    def _records(self):
        started, block, stopped, finish, usage, size = False, False, False, None, None, 0
        for event in self.stream:
            self.req._attempt_deadline.remaining()
            if self.closed or self.req._chat_cancelled.is_set(): raise TimeoutError()
            if not isinstance(event, dict) or len(event) != 1: raise ValueError('Invalid native event')
            try:
                if 'messageStart' in event:
                    if started or event['messageStart']['role'] != 'assistant': raise ValueError()
                    started = True
                elif 'contentBlockStart' in event:
                    value = event['contentBlockStart']
                    if not started or block or finish is not None or type(value['contentBlockIndex']) is not int or value['contentBlockIndex'] != 0:
                        raise ValueError()
                    if value['start']['toolUse']['name'] != self.schema_name: raise ValueError()
                    block = True
                elif 'contentBlockDelta' in event:
                    value = event['contentBlockDelta']
                    if not block or stopped or finish is not None or type(value['contentBlockIndex']) is not int or value['contentBlockIndex'] != 0:
                        raise ValueError()
                    fragment = value['delta']['toolUse']['input']
                    if not isinstance(fragment, str): raise ValueError()
                    size += len(fragment.encode('utf-8'))
                    if size > MAX_RESPONSE_BYTES: raise ValueError()
                    inner = self.decoder.feed(fragment)
                    if inner:
                        yield _sse({'choices': [{'index': 0, 'delta': {'content': inner}, 'finish_reason': None}]})
                elif 'contentBlockStop' in event:
                    value = event['contentBlockStop']
                    if not block or stopped or type(value['contentBlockIndex']) is not int or value['contentBlockIndex'] != 0:
                        raise ValueError()
                    stopped = True
                elif 'messageStop' in event:
                    if not stopped or finish is not None: raise ValueError()
                    reason = event['messageStop']['stopReason']
                    if reason not in {'tool_use','max_tokens'}: raise ValueError()
                    if reason == 'tool_use': self.decoder.finish()
                    finish = 'stop' if reason == 'tool_use' else 'length'
                elif 'metadata' in event:
                    if finish is None or usage is not None: raise ValueError()
                    usage = conversation_usage(event['metadata'], self.model_id)
                else:
                    raise ValueError()
            except (KeyError, TypeError, ValueError):
                raise ValueError('Invalid native structured stream') from None
        if finish is None or usage is None or not size:
            raise ValueError('Incomplete native structured stream')
        yield _sse({'choices': [{'index': 0, 'delta': {}, 'finish_reason': finish}], 'usage': usage})
        yield b'data: [DONE]\n\n'


class BedrockTransport:
    def __init__(self, settings):
        self.runtime = BedrockRuntime(settings.bedrock_region, timeout=settings.bedrock_timeout_seconds)
        self.model_id = settings.bedrock_chat_model_id

    def open(self, req, timeout=None):
        remaining = req._attempt_deadline.remaining()
        if req._chat_cancelled.is_set(): raise TimeoutError()
        payload = json.loads(req.data)
        if payload.get('model') != 'economicon-chat' or payload.get('native_model_id',self.model_id) != self.model_id:
            raise ValueError('Unexpected native model binding')
        schema = payload['response_format']['json_schema']
        parameters = conversation_parameters(payload['messages'], schema=schema['schema'], schema_name=schema['name'],
            model_id=self.model_id, max_tokens=payload['max_tokens'])
        native = BedrockRuntime(self.runtime.region, timeout=min(self.runtime.timeout,remaining), client=self.runtime._client)
        def close_client():
            if self.runtime._client is None and native._client is not None: native._client.close()
        try:
            if payload.get('stream') is True:
                response = native.client().converse_stream(**parameters)
                return _NativeStream(response['stream'],req,schema['name'],self.model_id,close_client,schema['schema'])
            value, usage = native.converse(payload['messages'],schema=schema['schema'],schema_name=schema['name'],
                model_id=self.model_id,max_tokens=payload['max_tokens'])
            result = {'model':None,'requested_model_id':self.model_id,'choices':[{'index':0,'finish_reason':'stop',
                'message':{'role':'assistant','content':json.dumps(value,ensure_ascii=False,allow_nan=False)}}], 'usage':usage}
            close_client()
            return _JSONResponse(json.dumps(result,ensure_ascii=False,allow_nan=False).encode('utf-8'))
        except BedrockError:
            close_client()
            raise
        except Exception as failure:
            close_client()
            raise _error(failure) from None
