"""Backend verifier for the authoritative processor-packaged prompt bundle.

The bundle is copied during image construction; no processor package is imported.
Its version must match the authenticated private descriptor before admission.
"""
import hashlib
import json
from dataclasses import dataclass, field
from app.core.context_budget import budget
from pathlib import Path

from app.schemas.chat import canonical, response_schema, provider_response_schema

TOKENIZER_SHA = '19e773648cb4e65de8660ea6365e10acca112d42a854923df93db4a6f333a82d'
TOKENIZER_REVISION = 'a66456a59f21345d1e5e586345c448a9106d29d7'
BASE_SHA = 'ad44df5f061f4f128b66df1e7720b270b594846adc206fa5d7b85ed2c0ced93b'
INPUT_SHA = 'a69db50801cfc42eb5b633fc724bbc7e4b3b590326f6713cd6b8616bf0ccfb42'
ASSEMBLER_SHA = 'f06d8ab1e440686e4080c6db332915e9b9e70becf25cceed14c2f08fd37dd27a'
from app.core.chat_calculations import PLAN_SCHEMA, validate_plan, calculate

DECISION_SCHEMA = {'type':'object','properties':{
    'action':{'type':'string','enum':['none','search']},'calculations':PLAN_SCHEMA,
    'query':{'anyOf':[{'type':'string','minLength':1,'maxLength':2048},{'type':'null'}]}},
    'required':['action','query','calculations'],'additionalProperties':False,
    'anyOf':[{'type':'object','properties':{'calculations':PLAN_SCHEMA,'action':{'type':'string','const':'none'},'query':{'type':'null'}},
              'required':['action','query','calculations'],'additionalProperties':False},
             {'type':'object','properties':{'calculations':PLAN_SCHEMA,'action':{'type':'string','const':'search'},'query':{'type':'string','minLength':1,'maxLength':2048}},
              'required':['action','query','calculations'],'additionalProperties':False}]}


def validate_decision(value):
    if not isinstance(value,dict) or set(value)!={'action','query','calculations'}:
        raise ValueError('Invalid decision fields.')
    validate_plan(value['calculations'])
    if value['action']=='none' and value['query'] is None:
        return value
    if (value['action']=='search' and isinstance(value['query'],str)
            and value['query'].strip() and len(value['query'])<=2048):
        return value
    raise ValueError('Invalid decision branch.')


def validate_search_call(decision):
    """Private retrieval request, never an assistant/tool conversation message.

    The digest correlates the exact validated query; the signed transport also
    binds the request and its result to the operation, attempt and tenant scope.
    """
    validate_decision(decision)
    if decision['action']!='search' and not decision['calculations']: raise ValueError('Control action required.')
    raw=json.dumps(decision,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest(),decision['query']

def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class BackendChatResources:
    system: str
    prompt_version: str
    manifest_bytes: bytes
    schema_text: str
    schema_sha256: str
    _tokenizer: object
    context_budget: dict = field(default_factory=lambda: budget('chat'))

    def count(self, value):
        return len(self._tokenizer.encode(value, add_special_tokens=False).ids)

    def count_messages(self, messages, *, financial_metrics_allowed=False, authorized_evidence=None):
        variable = self.count(canonical(messages[1:]))
        effective = provider_response_schema(financial_metrics_allowed=financial_metrics_allowed, authorized_evidence=authorized_evidence)
        total = self.count(canonical(messages)) + self.count(canonical(effective)) + self.count(canonical(DECISION_SCHEMA))
        if total + 1024 + self.context_budget['output_tokens'] > self.context_budget['context_tokens']:
            from app.db.chat_repository import ChatError
            raise ChatError(413, 'context_token_limit')
        return variable

    def metadata(self, counted):
        manifest = json.loads(self.manifest_bytes)
        return {'prompt_version':self.prompt_version, 'tokenizer_sha256':TOKENIZER_SHA,
                'response_schema_sha256':manifest['response_schema_sha256'],
                'input_contract_sha256':INPUT_SHA, 'assembler_sha256':ASSEMBLER_SHA,
                'variable_tokens':counted, 'context_budget':dict(self.context_budget)}

    def verify_descriptor(self, descriptor):
        if any(descriptor.get(key) != value for key, value in {
                'prompt_version':self.prompt_version, 'tokenizer_sha256':TOKENIZER_SHA,
                'response_schema_sha256':self.schema_sha256,
                'context_budget':self.context_budget}.items()):
            from app.db.chat_repository import ChatError
            raise ChatError(503, 'chat_contract_mismatch')


def load_resources(directory, tokenizer_file=None):
    import tokenizers
    root = Path(directory or '/opt/economicon/chat/v3')
    names = {item.name for item in root.iterdir()}
    if (root.is_symlink() or not {'system.md','input.md','manifest.json'}.issubset(names)
            or names - {'system.md','input.md','manifest.json','tokenizer.json'}):
        raise ValueError('Invalid bundle.')
    limits = {'system.md':65536, 'input.md':65536, 'manifest.json':16384, 'tokenizer.json':20217442}
    for name, limit in limits.items():
        if name == 'tokenizer.json' and name not in names:
            continue
        if (root/name).is_symlink() or not 0 < (root/name).stat().st_size <= limit:
            raise ValueError('Invalid resource.')
    manifest = json.loads((root/'manifest.json').read_bytes())
    schema, schema_sha256 = response_schema()
    system = (root/'system.md').read_bytes()
    input_text = (root/'input.md').read_bytes()
    if (manifest.get('v') != 3 or manifest.get('kind') != 'jup-035.chat.v3'
            or tokenizers.__version__ != '0.22.1'
            or manifest.get('system_sha256') != sha(system)
            or manifest.get('input_sha256') != sha(input_text)
            or manifest.get('system_base_sha256') != BASE_SHA
            or manifest.get('response_schema_sha256') != schema_sha256
            or manifest.get('provider_response_schema_sha256') != sha(canonical(provider_response_schema(financial_metrics_allowed=True)).encode())
            or manifest.get('financial_metrics_policy') != 'server-billing-authority-empty-metrics-v1'
            or manifest.get('response_period_policy') != 'server-verified-unique-utc-v1'
            or manifest.get('response_subscriptions_policy') != 'server-canonical-selection-v1'
            or manifest.get('input_contract_sha256') != INPUT_SHA
            or manifest.get('assembler_sha256') != ASSEMBLER_SHA
            or sha(canonical(manifest['input_contract']).encode()) != INPUT_SHA
            or sha(canonical(manifest['assembler_contract']).encode()) != ASSEMBLER_SHA
            or manifest.get('tokenizer') != {'library_version':'0.22.1','revision':TOKENIZER_REVISION,'sha256':TOKENIZER_SHA,'bytes':20217442}
            or manifest.get('budgets') != {'variable_tokens':8192,'wrapper_margin_tokens':1024,'output_tokens':3200,'model_context_tokens':1048576}):
        raise ValueError('Bundle contract mismatch.')
    inherited = system.decode('utf-8').partition('\n\nContrato de chat JUP-035 v3:')[0]
    if sha(inherited.encode('utf-8')) != BASE_SHA:
        raise ValueError('Inherited rules mismatch.')
    asset = Path(tokenizer_file) if tokenizer_file else (root/'tokenizer.json' if 'tokenizer.json' in names else root.parent/'v2/tokenizer.json')
    if asset.is_symlink() or asset.stat().st_size != 20217442 or sha(asset.read_bytes()) != TOKENIZER_SHA:
        raise ValueError('Tokenizer mismatch.')
    counter = tokenizers.Tokenizer.from_file(str(asset))
    if sha(asset.read_bytes()) != TOKENIZER_SHA:
        raise ValueError('Tokenizer changed.')
    counter.no_truncation()
    counter.no_padding()
    raw = canonical(manifest).encode('utf-8')
    return BackendChatResources(system.decode('utf-8'),'jup-035.chat.v3:'+sha(raw),raw,
                                canonical(provider_response_schema(financial_metrics_allowed=True)),schema_sha256,counter)
