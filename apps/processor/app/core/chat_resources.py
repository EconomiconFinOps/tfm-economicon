"""Offline, fixed-resource loading and the contractual GLM tokenizer.

Only server configuration supplies paths. No URL, inference or download occurs.
The manifest hashes a versioned serialization contract, not mutable source paths.
"""
import hashlib
import json
from dataclasses import dataclass, field
from app.core.context_budget import budget
from pathlib import Path

INPUT_CONTRACT = {
    'version': 2,
    'public_fields': ['request_id','content','screen_context','retry_operation_id','retry_question_id'],
    'capture_fields': ['schema_version','screen_version','route','tab_id','source','identity','captured_at','selection','datasets'],
    'scope': 'tenant+user+conversation',
    'capture_limit_bytes': 1048576, 'body_limit_bytes': 2097152, 'depth_limit': 32,
}
ASSEMBLER_CONTRACT = {
    'version': 2, 'roles': ['system','user-summary-optional','user-current'],
    'summary_label': 'UNTRUSTED_DIALOGUE_SUMMARY', 'current_label': 'UNTRUSTED_CURRENT_CONTEXT',
    'serialization': 'utf8-sorted-keys-significant-arrays', 'escape': 'json-controls-angle-brackets',
}
TOKENIZER = {
    'library_version': '0.22.1', 'revision': 'a66456a59f21345d1e5e586345c448a9106d29d7',
    'sha256': '19e773648cb4e65de8660ea6365e10acca112d42a854923df93db4a6f333a82d',
    'bytes': 20217442,
}
BUDGETS = {'variable_tokens':8192, 'wrapper_margin_tokens':1024,
           'output_tokens':800, 'model_context_tokens':1048576}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('Duplicate resource field.')
        value[key] = item
    return value


class TokenBudgetExceeded(ValueError):
    pass


@dataclass(frozen=True)
class ChatResources:
    prompt_version: str
    system: str
    input_template: str
    tokenizer_sha256: str
    response_schema_sha256: str
    manifest_bytes: bytes
    _tokenizer: object
    context_budget: dict = field(default_factory=lambda: budget('chat'))

    def count(self, text):
        return len(self._tokenizer.encode(text, add_special_tokens=False).ids)

    def check_messages(self, messages, schema):
        if not messages or messages[0] != {'role':'system','content':self.system}:
            raise ValueError('System prefix mismatch.')
        if any(message.get('role') != 'user' or set(message) != {'role','content'}
               for message in messages[1:]):
            raise ValueError('Invalid variable roles.')
        variable = self.count(canonical(messages[1:]).decode('utf-8'))
        total = self.count(canonical(messages).decode('utf-8')) + self.count(canonical(schema).decode('utf-8'))
        if total + 1024 + 800 > self.context_budget['context_tokens']:
            raise TokenBudgetExceeded('Token budget exceeded.')
        return variable

    def validate_context(self, context):
        from app.agents.schemas import chat_provider_schema
        if not isinstance(context, dict) or context.get('prompt_version') != self.prompt_version:
            raise ValueError('Context version mismatch.')
        if len(canonical(context)) > self.context_budget['body_limit_bytes']:
            raise ValueError('Context body limit.')
        messages = context.get('messages')
        if not isinstance(messages, list) or len(messages) not in (2, 3):
            raise ValueError('Invalid message count.')
        counted = self.check_messages(messages, chat_provider_schema())
        if not messages[-1]['content'].startswith('UNTRUSTED_CURRENT_CONTEXT\n'):
            raise ValueError('Current block mismatch.')
        if len(messages) == 3:
            summary = messages[1]['content']
            if not summary.startswith('UNTRUSTED_DIALOGUE_SUMMARY\n'):
                raise ValueError('Summary block mismatch.')
            from app.agents.summary_schemas import SummaryResponse
            from app.clients.chat_stream_parser import complete_json
            from app.core.summary_resources import V3_BUDGETS
            payload = SummaryResponse.model_validate(complete_json(summary.split('\n', 1)[1])).model_dump(mode='json')
            content = '\n'.join([item['text'] for item in payload['topics']]
                                + [item['quote'] for item in payload['facts']] + payload['limitations'])
            if (self.count(canonical(payload).decode('utf-8')) > V3_BUDGETS['payload_tokens']
                    or self.count(content) > V3_BUDGETS['content_tokens']):
                raise ValueError('Summary output token limit.')
            # check_messages counts the full escaped block, label, schema and
            # chat reserves; the summary JSON ceiling is not a prefix ceiling.
        declared = context.get('manifest')
        manifest = json.loads(self.manifest_bytes)
        expected = {'prompt_version':self.prompt_version,
                    'tokenizer_sha256':self.tokenizer_sha256,
                    'response_schema_sha256':self.response_schema_sha256,
                    'input_contract_sha256':manifest['input_contract_sha256'],
                    'assembler_sha256':manifest['assembler_sha256'],
                    'variable_tokens':counted, 'context_budget':self.context_budget}
        if not isinstance(declared, dict) or any(type(declared.get(key)) is not type(value)
                                                or declared.get(key) != value for key, value in expected.items()):
            raise ValueError('Context manifest mismatch.')
        return counted


def load_resources(directory=None, tokenizer_file=None):
    import tokenizers
    from app.agents.prompts import SYSTEM_PROMPT
    from app.agents.schemas import FinOpsResponse, chat_provider_schema
    root = Path(directory) if directory else Path(__file__).parents[1] / 'agents/prompt_resources/jup035/chat/v2'
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Unavailable resources.')
    required = {'system.md','input.md','manifest.json'}
    names = {item.name for item in root.iterdir()}
    if not required.issubset(names) or names - required - {'tokenizer.json'}:
        raise ValueError('Incomplete resources.')
    if any((root/name).is_symlink() for name in required):
        raise ValueError('Invalid resource path.')
    if any((root/name).stat().st_size > (16384 if name == 'manifest.json' else 65536)
           for name in required):
        raise ValueError('Resource limit.')
    system_raw = (root/'system.md').read_bytes()
    input_raw = (root/'input.md').read_bytes()
    manifest_raw = (root/'manifest.json').read_bytes()
    if not 0 < len(system_raw) <= 65536 or not 0 < len(input_raw) <= 65536 or len(manifest_raw) > 16384:
        raise ValueError('Resource limit.')
    manifest = json.loads(manifest_raw, object_pairs_hook=unique)
    expected = {
        'v':2, 'kind':'jup-035.chat.v2',
        'system_sha256':sha(system_raw), 'input_sha256':sha(input_raw),
        'system_base_sha256':sha(SYSTEM_PROMPT.encode('utf-8')),
        'response_schema_sha256':sha(canonical(FinOpsResponse.model_json_schema())),
        'provider_response_schema_sha256':sha(canonical(chat_provider_schema())),
        'response_period_policy':'server-verified-unique-utc-v1',
        'input_contract':INPUT_CONTRACT, 'input_contract_sha256':sha(canonical(INPUT_CONTRACT)),
        'assembler_contract':ASSEMBLER_CONTRACT, 'assembler_sha256':sha(canonical(ASSEMBLER_CONTRACT)),
        'tokenizer':TOKENIZER, 'budgets':BUDGETS,
    }
    if manifest != expected or tokenizers.__version__ != '0.22.1':
        raise ValueError('Resource contract mismatch.')
    asset = Path(tokenizer_file) if tokenizer_file else root/'tokenizer.json'
    if asset.is_symlink() or asset.stat().st_size != TOKENIZER['bytes']:
        raise ValueError('Tokenizer limit.')
    raw = asset.read_bytes()
    if sha(raw) != TOKENIZER['sha256']:
        raise ValueError('Tokenizer mismatch.')
    counter = tokenizers.Tokenizer.from_file(str(asset))
    if sha(asset.read_bytes()) != TOKENIZER['sha256']:
        raise ValueError('Tokenizer changed during load.')
    counter.no_truncation()
    counter.no_padding()
    counter.encode('Control offline: español, € y 漢字.', add_special_tokens=False)
    return ChatResources('jup-035.chat.v2:'+sha(canonical(manifest)), system_raw.decode('utf-8'),
                         input_raw.decode('utf-8'), TOKENIZER['sha256'],
                         expected['response_schema_sha256'], canonical(manifest), counter)
