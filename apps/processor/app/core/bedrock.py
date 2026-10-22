"""Native AWS role-authenticated inference. Kept identical in both services.

Construction/import is offline; the SDK and its credential chain are initialized
only for an explicit inference request. There are no alternate providers.
"""
import hashlib
import copy
import json
import math
import re

TITAN_MODEL = 'amazon.titan-embed-text-v2:0'
TITAN_DIMENSIONS = frozenset({256, 512, 1024})
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
CHAT_MODELS = frozenset({'eu.amazon.nova-micro-v1:0', 'eu.amazon.nova-lite-v1:0'})


class BedrockError(RuntimeError):
    def __init__(self, category):
        self.category = category
        super().__init__(category)


def embedding_fingerprint(region, dimension):
    if region != 'eu-west-1' or type(dimension) is not int or dimension not in TITAN_DIMENSIONS:
        raise ValueError('Unsupported regional embedding contract')
    return hashlib.sha256(json.dumps({'provider': 'bedrock', 'region': region,
        'model_id': TITAN_MODEL, 'dimension': dimension, 'normalize': True,
        'recipe': 'titan_v2_native_v1'}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _error(failure):
    from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError, EndpointConnectionError
    if isinstance(failure, (TimeoutError, ConnectTimeoutError, ReadTimeoutError)):
        return BedrockError('timeout')
    if isinstance(failure, EndpointConnectionError):
        return BedrockError('connection')
    if isinstance(failure, ClientError):
        code = failure.response.get('Error', {}).get('Code')
        if code in {'AccessDeniedException', 'UnrecognizedClientException', 'ExpiredTokenException'}:
            return BedrockError('authentication')
        if code in {'ThrottlingException', 'ServiceQuotaExceededException'}:
            return BedrockError('rate_limit')
        if code in {'InternalServerException', 'ServiceUnavailableException', 'ModelNotReadyException', 'ModelTimeoutException'}:
            return BedrockError('upstream')
        return BedrockError('request')
    return BedrockError('invalid_response')


def native_tool_schema(schema):
    """Lossless wrapper for Nova's three-key root restriction, including local refs."""
    def rebase(node):
        if isinstance(node, bool):
            return node
        if not isinstance(node, dict) or any(key in node for key in ('$id', '$anchor', '$dynamicRef', '$recursiveRef')):
            raise ValueError('Unsupported native schema scope')
        result = copy.deepcopy(node)
        if '$ref' in result:
            reference = result['$ref']
            if not isinstance(reference, str) or reference != '#' and not reference.startswith('#/'):
                raise ValueError('Only local native schema references are supported')
            result['$ref'] = '#/properties/response' + reference[1:]
        for key in ('$defs', 'definitions', 'properties', 'patternProperties', 'dependentSchemas'):
            if key in result:
                result[key] = {name: rebase(item) for name, item in result[key].items()}
        for key in ('anyOf', 'oneOf', 'allOf', 'prefixItems'):
            if key in result:
                result[key] = [rebase(item) for item in result[key]]
        for key in ('items', 'additionalProperties', 'contains', 'not', 'if', 'then', 'else', 'propertyNames', 'unevaluatedProperties'):
            if key in result:
                result[key] = rebase(result[key])
        return result
    return {'type': 'object', 'properties': {'response': rebase(schema)}, 'required': ['response']}


def unwrap_tool_response(value, schema):
    try:
        from jsonschema import Draft202012Validator
        if not isinstance(value, dict) or set(value) != {'response'} or not isinstance(value['response'], dict):
            raise ValueError()
        result = value['response']
        Draft202012Validator(schema).validate(result)
        return result
    except Exception:
        raise ValueError('Invalid native structured response') from None


class NativeToolJSON:
    """Expose only the inner JSON as it arrives; validate the complete envelope at finish."""
    def __init__(self, schema):
        self.schema, self.raw = schema, ''
        self.cursor = None
        self.depth, self.quoted, self.escaped, self.complete = 0, False, False, False

    def feed(self, fragment):
        if not isinstance(fragment, str) or len((self.raw + fragment).encode('utf-8')) > MAX_RESPONSE_BYTES:
            raise ValueError('Invalid native tool input')
        self.raw += fragment
        if self.cursor is None:
            prefix = self.raw.lstrip()
            if not prefix.startswith('{'):
                if not prefix:
                    return ''
                raise ValueError('Invalid native envelope')
            start = len(self.raw) - len(prefix) + 1
            while start < len(self.raw) and self.raw[start].isspace(): start += 1
            try:
                key, offset = json.JSONDecoder().raw_decode(self.raw, start)
            except ValueError:
                if len(self.raw) > 256: raise ValueError('Invalid native envelope') from None
                return ''
            if key != 'response': raise ValueError('Invalid native envelope')
            while offset < len(self.raw) and self.raw[offset].isspace(): offset += 1
            if offset == len(self.raw): return ''
            if self.raw[offset] != ':': raise ValueError('Invalid native envelope')
            offset += 1
            while offset < len(self.raw) and self.raw[offset].isspace(): offset += 1
            if offset == len(self.raw): return ''
            if self.raw[offset] != '{': raise ValueError('Invalid native response')
            self.cursor = offset
        start = self.cursor
        while self.cursor < len(self.raw) and not self.complete:
            char = self.raw[self.cursor]
            self.cursor += 1
            if self.quoted:
                if self.escaped: self.escaped = False
                elif char == '\\': self.escaped = True
                elif char == '"': self.quoted = False
            elif char == '"': self.quoted = True
            elif char in '{[': self.depth += 1
            elif char in '}]':
                self.depth -= 1
                if self.depth == 0: self.complete = True
        return self.raw[start:self.cursor]

    def finish(self):
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result: raise ValueError('Duplicate native JSON key')
                result[key] = value
            return result
        try:
            if not self.complete: raise ValueError()
            value = json.loads(self.raw, object_pairs_hook=unique)
            return unwrap_tool_response(value, self.schema)
        except Exception:
            raise ValueError('Invalid native structured response') from None


def conversation_parameters(messages, *, schema, schema_name, model_id, max_tokens):
    if (model_id not in CHAT_MODELS or type(max_tokens) is not int or not 1 <= max_tokens <= 10000
            or not isinstance(schema, dict) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', schema_name)
            or not isinstance(messages, list) or not messages):
        raise ValueError('Invalid explicit EU inference contract')
    system, conversation = [], []
    for message in messages:
        if (not isinstance(message, dict) or message.get('role') not in {'system','user','assistant'}
                or not isinstance(message.get('content'), str) or not message['content'].strip()):
            raise ValueError('Only explicit text messages are supported')
        block = {'text': message['content']}
        if message['role'] == 'system':
            if conversation:
                raise ValueError('System authority must precede conversation data')
            system.append(block)
        elif conversation and conversation[-1]['role'] == message['role']:
            conversation[-1]['content'].append(block)
        else:
            conversation.append({'role': message['role'], 'content': [block]})
    if not conversation or conversation[0]['role'] != 'user':
        raise ValueError('A user message is required')
    result = {'modelId': model_id, 'messages': conversation,
        'inferenceConfig': {'maxTokens': max_tokens, 'temperature': 0},
        'toolConfig': {'tools': [{'toolSpec': {'name': schema_name,
            'description': 'Return the approved structured response using this tool only.',
            'inputSchema': {'json': native_tool_schema(schema)}}}], 'toolChoice': {'tool': {'name': schema_name}}}}
    if system:
        result['system'] = system
    # Conservative UTF-8 admission, not a claim about the model's tokenizer.
    # Reject rather than truncate evidence when the native window may be exceeded.
    if len(json.dumps(result, ensure_ascii=False, allow_nan=False).encode('utf-8')) > 100000:
        raise ValueError('Native model input exceeds the configured window')
    return result


def native_review_usage(legs, attempted):
    """Complete native token receipts do not depend on an unavailable USD price."""
    fields = ('prompt_tokens', 'completion_tokens', 'total_tokens')
    if type(attempted) is not int or attempted not in (1, 2) or len(legs) != attempted:
        return None
    for leg in legs:
        if (not isinstance(leg, dict) or any(type(leg.get(key)) is not int or leg[key] < 0 for key in fields)
                or leg['prompt_tokens'] + leg['completion_tokens'] != leg['total_tokens']):
            return None
    return {key: sum(leg[key] for leg in legs) for key in fields}


def conversation_usage(response, model_id):
    usage = response['usage']
    values = {key: usage[name] for key,name in (('prompt_tokens','inputTokens'),
        ('completion_tokens','outputTokens'),('total_tokens','totalTokens'))}
    if (any(type(v) is not int or v < 0 for v in values.values())
            or values['total_tokens'] != values['prompt_tokens'] + values['completion_tokens']):
        raise ValueError('Invalid native usage counters')
    return {**values, 'model_id': model_id, 'cost_usd': None}


class BedrockRuntime:
    def __init__(self, region, *, timeout=30, client=None):
        if region != 'eu-west-1' or type(timeout) not in {int, float} or not math.isfinite(timeout) or not 0 < timeout <= 30:
            raise ValueError('Explicit Ireland region and bounded inference timeout are required')
        self.region, self.timeout, self._client = region, timeout, client

    def client(self):
        if self._client is None:
            import boto3
            from botocore.config import Config
            self._client = boto3.client('bedrock-runtime', region_name=self.region, config=Config(
                connect_timeout=min(3, self.timeout), read_timeout=self.timeout, signature_version='v4',
                retries={'total_max_attempts': 1}, ignore_configured_endpoint_urls=True,
                proxies={}, user_agent_extra='economicon-aws-rehearsal'))
        return self._client

    def embed(self, text, *, dimension=1024):
        embedding_fingerprint(self.region, dimension)
        if not isinstance(text, str) or not text.strip() or len(text) > 50000 or len(text.encode('utf-8')) > 200000:
            raise ValueError('Embedding input exceeds the native text contract')
        body = None
        try:
            response = self.client().invoke_model(modelId=TITAN_MODEL, accept='application/json',
                contentType='application/json', body=json.dumps({'inputText': text, 'dimensions': dimension, 'normalize': True}))
            body = response['body']
            raw = body.read(MAX_RESPONSE_BYTES + 1)
            if not raw or len(raw) > MAX_RESPONSE_BYTES:
                raise ValueError('Invalid response size')
            data = json.loads(raw)
            vector, count = data['embedding'], data['inputTextTokenCount']
            if (not isinstance(vector, list) or len(vector) != dimension
                    or not all(type(v) in {int, float} and math.isfinite(v) for v in vector)
                    or not any(float(f'{v:.6f}') != 0 for v in vector)
                    or type(count) is not int or not 0 < count <= 8192):
                raise ValueError('Invalid native embedding result')
            return [float(v) for v in vector], {'prompt_tokens': count, 'model_id': TITAN_MODEL, 'cost_usd': None}
        except Exception as failure:
            raise _error(failure) from None
        finally:
            if body is not None:
                body.close()

    def converse(self, messages, *, schema, schema_name, model_id, max_tokens):
        parameters = conversation_parameters(messages, schema=schema, schema_name=schema_name,
            model_id=model_id, max_tokens=max_tokens)
        try:
            response = self.client().converse(**parameters)
            content = response['output']['message']['content']
            if response['stopReason'] != 'tool_use' or not isinstance(content, list) or len(content) != 1:
                raise ValueError('Native completion must contain exactly the requested output tool')
            tool = content[0]['toolUse']
            if tool['name'] != schema_name or not isinstance(tool['input'], dict):
                raise ValueError('Native completion has an unexpected output tool')
            if len(json.dumps(tool['input'],allow_nan=False).encode('utf-8')) > MAX_RESPONSE_BYTES:
                raise ValueError('Native completion exceeds the response limit')
            return unwrap_tool_response(tool['input'], schema), conversation_usage(response, model_id)
        except Exception as failure:
            raise _error(failure) from None


class TitanEmbeddingProvider:
    name = 'bedrock'

    def __init__(self, settings):
        if settings.embedding_model != TITAN_MODEL:
            raise ValueError('An exact native Titan V2 model is required')
        self.dimension, self.model = settings.embedding_dimension, TITAN_MODEL
        self.mapping_sha256 = embedding_fingerprint(settings.bedrock_region, self.dimension)
        self.runtime = BedrockRuntime(settings.bedrock_region, timeout=settings.bedrock_timeout_seconds)
        self.usage_records = []

    def embed(self, text):
        vector, usage = self.runtime.embed(text, dimension=self.dimension)
        self.usage_records.append(usage)
        return vector

    def embed_batch(self, texts, *, expected_model=None, counter=None,
                    max_items=16, max_tokens=16384, max_bytes=262144):
        if (not isinstance(texts, list) or type(max_items) is not int or not 1 <= max_items <= 32
                or type(max_tokens) is not int or not 1 <= max_tokens <= 300000
                or type(max_bytes) is not int or not 1024 <= max_bytes <= 1048576
                or expected_model not in {None, TITAN_MODEL}):
            raise ValueError('Invalid native embedding batch contract')
        for text in texts:
            if not isinstance(text, str) or not text.strip():
                raise ValueError('Embedding inputs must be nonempty text')
            # A native request contains one text, so each is also a bounded
            # batch. The preparation counter is not claimed as Titan usage;
            # inputTextTokenCount from the service is recorded separately.
            count = counter.count(text) if counter is not None else len(text.encode('utf-8'))
            if count > min(8192,max_tokens) or len(text.encode('utf-8')) > max_bytes:
                raise ValueError('Embedding input exceeds batch limits')
        return [self.embed(text) for text in texts]
