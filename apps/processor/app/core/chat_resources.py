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
           'output_tokens':3200, 'model_context_tokens':1048576}
from app.core.chat_expressions import context_question, context_quantities

# This control is generated locally, never by an LLM. The entire current
# question (bounded to the retrieval input contract) is deterministically used.
DECISION_SCHEMA = {'type':'object','properties':{'action':{'const':'search'},
    'query':{'type':'string','minLength':1,'maxLength':2048}},
    'required':['action','query'],'additionalProperties':False}

def decision_schema(context):
    return DECISION_SCHEMA

def retrieval_control(context):
    return {'action':'search','query':context_question(context)[:2048]}

def validate_search_call(value, context=None):
    if (not isinstance(value,dict) or set(value)!={'action','query'}
            or value['action']!='search' or not isinstance(value['query'],str)
            or not value['query'].strip() or len(value['query'])>2048):
        raise ValueError('Invalid retrieval control.')
    if context is not None and value!=retrieval_control(context):
        raise ValueError('Retrieval query mismatch.')
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest(),value['query']


ASSEMBLER_CONTRACT.update(tool_protocol='server-documentation-v4', decision_schema=DECISION_SCHEMA,
    continuation_roles=['user-untrusted-retrieval'], max_searches=1,
    max_generations=2, decision_format='server-current-question', final_format='strict-finops',
    no_search_policy='authorized-context-or-abstention',
    evidence_selection='used-visible-excerpts-and-server-terminals-v4',
    grounding='visible-exact-passage220-labelled-inference-v3',
    arithmetic='provenance-user-document-depth4-unique-numeric12-v10',
    response_modes='unified-visible-support-labelled-inference-v5',
    recommendation_citations='visible-excerpts-derived-source-union-v2',
    undefined_guidance='evaluated-zero-domain-absolute-and-next-step-v2',
    missing_spend='explicit-empty-query-incomplete-ingestion-unknown-total-v1',
    reporting_basis='complete-reporting-policy-closed-scenario-unknown-quality-v1',
    zero_change='explicit-user-zero-baseline-relative-terminal-v1',
    zero_percentage='documented-eligible-zero-denominator-terminal-v1',
    quantity_display='observed-value-unit-provenance-no-operation-v1',
    boolean_rules='grounded-named-delta-pair-three-valued-premises-v2',
    retrieval_neighbors='same-snapshot-tenant-provider-immediate-bounded20-contiguous-priority-v2',
    evidence_order='local-visible-support-no-root-decoration-v2',
    excerpt_repetition='deduplicate-source-and-literal-passage-in-main-answer-v1',
    answer_generation_blocks=24,
    policy_sections={'version':'complete-positional-list-table-policy-v1',
        'module_sha256':hashlib.sha256(Path(__file__).with_name('chat_policy_sections.py').read_text(encoding='utf-8').encode()).hexdigest()},
    policy_retrieval={'version':'same-tenant-provider-snapshot-exact-heading-v1',
        'document_candidates':2,'document_bytes':65536,'max_chunks':6,
        'incomplete_policy':'no-priority','distance':'observed-not-replaced'},
    budget_comparison={'version':'adjacent-labelled-hypothetical-forecast-budget-v1',
        'module_sha256':hashlib.sha256(Path(__file__).with_name('chat_budget_comparison.py').read_text(encoding='utf-8').encode()).hexdigest()},
    documentary_sections='original-markdown-positional-contiguous-ranges-v1',
    interval_rules='explicit-percentage-partition-eligible-total-or-allocation-role-explanation-v4',
    decision_values='server-query-no-model-decision-v1',
    reasoning={'effort':'high','exclude':True,'shared_output_tokens':3200})
from app.core.chat_review import DRAFT_INSTRUCTION,REVIEW_INSTRUCTION,DRAFT_MAX_BYTES,draft_schema
ASSEMBLER_CONTRACT.update(review={'version':2,'draft_tokens':1000,'final_tokens':2200,
    'draft_schema':draft_schema([]),'draft_instruction':DRAFT_INSTRUCTION,
    'review_instruction':REVIEW_INSTRUCTION,'draft_public':False,
    'usage':'observed-partial-explicit-legs-v1','deadline':'shared-120s',
    'draft_max_bytes':DRAFT_MAX_BYTES,'serialized_plan_input_reserve':2*DRAFT_MAX_BYTES,
    'module_sha256':hashlib.sha256(Path(__file__).with_name('chat_review.py').read_text(encoding='utf-8').encode()).hexdigest()})


def continuation_messages(context, assistant, result):
    identifier,_=validate_search_call(assistant,context)
    if not isinstance(result,dict) or set(result)!={'tool_call_id','content','variable_tokens'} or result['tool_call_id']!=identifier:
        raise ValueError('Tool result correlation.')
    content=result['content']
    if not isinstance(content,str) or len(content.encode('utf-8'))>1024*1024: raise ValueError('Tool result limit.')
    data=json.loads(content,object_pairs_hook=unique)
    if not isinstance(data,dict) or set(data)!={'evidence','omissions'} or not isinstance(data['omissions'],list): raise ValueError('Tool result format.')
    sources=data['evidence']
    if not isinstance(sources,list) or len(sources)+len(context.get('authorized_evidence',[]))>20: raise ValueError('Tool evidence limit.')
    ids=set(item['id'] for item in context.get('authorized_evidence',[]))
    for source in sources:
        if not isinstance(source,dict) or set(source) not in ({'id','kind','title','source','content'},{'id','kind','title','source','content','provenance'}) or source['kind']!='corpus': raise ValueError('Corpus only extension.')
        if any(not isinstance(source[k],str) or not source[k].strip() for k in ('id','title','source','content')) or source['id'] in ids:
            raise ValueError('Invalid corpus source.')
        from app.core.chat_rules import validate_provenance
        validate_provenance(source)
        ids.add(source['id'])
    if type(result['variable_tokens']) is not int or result['variable_tokens']<0: raise ValueError('Tool token count.')
    return context['messages']+[{'role':'user','content':'UNTRUSTED_RETRIEVAL_CONTEXT\n'+content}]


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
        if total + 1024 + self.context_budget['output_tokens'] > self.context_budget['context_tokens']:
            raise TokenBudgetExceeded('Token budget exceeded.')
        return variable

    def validate_tool_result(self, context, assistant, result):
        from app.agents.schemas import chat_provider_schema
        messages=continuation_messages(context,assistant,result)
        sources=context.get('authorized_evidence',[])+json.loads(result['content'])['evidence']
        schema=chat_provider_schema(financial_metrics_allowed=context['financial_metrics_allowed'], authorized_evidence=sources, quantities=context_quantities({'messages':messages,'authorized_evidence':sources}))
        variable=self.count(canonical(messages[1:]).decode('utf-8'))
        total=self.count(canonical(messages).decode('utf-8'))+self.count(canonical(schema).decode('utf-8'))
        if total+1024+self.context_budget['output_tokens']>self.context_budget['context_tokens']:
            raise TokenBudgetExceeded('Tool context token limit.')
        from app.core.chat_review import admission_tokens
        if admission_tokens(self.count,messages,schema,sources)['max_context_tokens']+1024>self.context_budget['context_tokens']:
            raise TokenBudgetExceeded('Review context token limit.')
        if variable!=result['variable_tokens']: raise ValueError('Tool count mismatch.')
        return messages

    def validate_context(self, context):
        from app.agents.schemas import chat_provider_schema
        if not isinstance(context, dict) or context.get('prompt_version') != self.prompt_version:
            raise ValueError('Context version mismatch.')
        if len(canonical(context)) > self.context_budget['body_limit_bytes']:
            raise ValueError('Context body limit.')
        messages = context.get('messages')
        if not isinstance(messages, list) or len(messages) not in (2, 3):
            raise ValueError('Invalid message count.')
        allowed = context.get('financial_metrics_allowed')
        if type(allowed) is not bool:
            raise ValueError('Invalid financial authority control.')
        if context.get('tool_protocol') not in ('server-documentation-v4','mock-direct-v1'):
            raise ValueError('Tool protocol missing.')
        counted = self.check_messages(messages, chat_provider_schema(financial_metrics_allowed=allowed, authorized_evidence=context.get('authorized_evidence', []), quantities=context_quantities(context)))
        from app.core.chat_review import admission_tokens
        if admission_tokens(self.count,messages,chat_provider_schema(financial_metrics_allowed=allowed,authorized_evidence=context.get('authorized_evidence',[]),quantities=context_quantities(context)),context.get('authorized_evidence',[]))['max_context_tokens']+1024>self.context_budget['context_tokens']:
            raise TokenBudgetExceeded('Review context token limit.')
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
                    'decision_schema_sha256':sha(canonical(decision_schema(context))),
                    'variable_tokens':counted, 'context_budget':self.context_budget}
        if not isinstance(declared, dict) or any(type(declared.get(key)) is not type(value)
                                                or declared.get(key) != value for key, value in expected.items()):
            raise ValueError('Context manifest mismatch.')
        return counted


def load_resources(directory=None, tokenizer_file=None):
    import tokenizers
    from app.agents.prompts import CHAT_SYSTEM_PROMPT
    from app.agents.schemas import FinOpsResponse, chat_provider_schema
    root = Path(directory) if directory else Path(__file__).parents[1] / 'agents/prompt_resources/jup035/chat/v3'
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
        'v':3, 'kind':'jup-035.chat.v3',
        'system_sha256':sha(system_raw), 'input_sha256':sha(input_raw),
        'system_base_sha256':sha(CHAT_SYSTEM_PROMPT.encode('utf-8')),
        'response_schema_sha256':sha(canonical(FinOpsResponse.model_json_schema())),
        'provider_response_schema_sha256':sha(canonical(chat_provider_schema(financial_metrics_allowed=True))),
        'financial_metrics_policy':'server-billing-authority-empty-metrics-v1',
        'response_period_policy':'server-verified-unique-utc-v1',
        'response_subscriptions_policy':'server-canonical-selection-v1',
        'input_contract':INPUT_CONTRACT, 'input_contract_sha256':sha(canonical(INPUT_CONTRACT)),
        'assembler_contract':ASSEMBLER_CONTRACT, 'assembler_sha256':sha(canonical(ASSEMBLER_CONTRACT)),
        'tokenizer':TOKENIZER, 'budgets':BUDGETS,
    }
    if manifest != expected or tokenizers.__version__ != '0.22.1':
        raise ValueError('Resource contract mismatch.')
    asset = Path(tokenizer_file) if tokenizer_file else root.parent/'v2/tokenizer.json'
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
    return ChatResources('jup-035.chat.v3:'+sha(canonical(manifest)), system_raw.decode('utf-8'),
                         input_raw.decode('utf-8'), TOKENIZER['sha256'],
                         expected['response_schema_sha256'], canonical(manifest), counter)

ASSEMBLER_CONTRACT['documentary_excerpt_module_sha256']=hashlib.sha256(Path(__file__).with_name('chat_claims.py').read_text(encoding='utf-8').encode()).hexdigest()
