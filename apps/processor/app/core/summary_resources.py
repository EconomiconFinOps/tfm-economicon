"""Closed processor-authoritative summary resources, shared pinned tokenizer."""
from dataclasses import dataclass,field
from app.core.context_budget import budget
import json,os
from pathlib import Path
from app.agents.summary_schemas import SummaryResponse
from app.core.chat_resources import TOKENIZER,FLASH_TOKENIZER,canonical,sha,unique

INPUT_CONTRACT={'v':2,'fields':['previous_summary','pairs'],
    'pair_fields':['question_ref','question','answer_ref','answer'],
    'ref_format':'role-sha256-scope-message','serialization':'utf8-sorted-keys-significant-arrays'}
ASSEMBLER_CONTRACT={'v':2,'roles':['system','user'],'input_label':'UNTRUSTED_SUMMARY_INPUT',
    'serialization':'utf8-sorted-keys-significant-arrays'}
POLICY={'v':2,'max_topics':8,'max_facts':8,'max_limitations':4,
    'literal_quotes':True,'opaque_refs':True,'recent_pairs_excluded':4}
BUDGETS={'input_total_tokens':4096,'output_tokens':800,'payload_tokens':768,'content_tokens':512}
V3_BUDGETS={'input_total_tokens':1048576,'output_tokens':10000,'payload_tokens':8192,'content_tokens':6144}
V3_MANIFEST_SHA='b77cb54456152e08db25c57fef510b5864b0f2679db76e743cfe7a5b8a9c8634'
V4_MANIFEST_SHA='ba51412f3ab4cf752cf67aff4a12844acaf66c4a193d7befdf2082a439997052'
LEGACY_MANIFEST_SHA='f724d3fc8379d7926c667c9f5f3c43ed9074d34080a11fb5a1c76b2cd43b8b94'

@dataclass(frozen=True)
class SummaryResources:
    summary_version:str
    system:str
    input_template:str
    manifest_bytes:bytes
    schema_bytes:bytes
    tokenizer_sha256:str
    response_schema_sha256:str
    _tokenizer:object
    response_model:type=SummaryResponse
    context_budget:dict=field(default_factory=lambda: budget('summary'))
    legacy_resources:tuple=field(default=(),repr=False)

    def check_generation(self):
        if json.loads(self.manifest_bytes)['v']!=4 or self.tokenizer_sha256!=FLASH_TOKENIZER['sha256']:
            raise ValueError('Historical summary resources are read-only.')

    @property
    def contract(self):
        manifest=json.loads(self.manifest_bytes)
        return {'prompt_version':self.summary_version,'schema_sha256':self.response_schema_sha256,
            'tokenizer_sha256':self.tokenizer_sha256,'policy_version':manifest['kind']+':'+manifest['policy_sha256']}

    def resources_for_contract(self,contract):
        for resources in (self,)+self.legacy_resources:
            if contract==resources.contract:return resources
        raise ValueError('Unsupported summary origin contract.')

    @property
    def response_schema(self):
        return json.loads(self.schema_bytes)

    @property
    def provider_response_schema(self):
        # Provider compatibility is separate from the authoritative local schema.
        schema=self.response_schema
        properties=schema['$defs']['SummaryTopic']['properties']
        for field in ('question_refs','answer_refs'):
            del properties[field]['uniqueItems']
        return schema

    def count(self,text):
        return len(self._tokenizer.encode(text,add_special_tokens=False).ids)

    def validate_payload(self,value):
        normalized=SummaryResponse.model_validate(value).model_dump(mode='json')
        content='\n'.join([x['text'] for x in normalized['topics']]+[x['quote'] for x in normalized['facts']]+normalized['limitations'])
        limits=json.loads(self.manifest_bytes)['budgets']
        if self.count(content)>limits['content_tokens'] or self.count(canonical(normalized).decode())>limits['payload_tokens']:
            raise ValueError('Summary output token limit.')
        return normalized

    def prepare_input(self,payload):
        import re
        if not isinstance(payload,dict) or set(payload)!={'previous_summary','pairs'}:
            raise ValueError('Summary input fields.')
        previous=payload['previous_summary']
        if previous is not None:self.validate_payload(previous)
        pairs=payload['pairs']
        if not isinstance(pairs,list) or not pairs:raise ValueError('Summary pairs.')
        seen=set()
        for pair in pairs:
            if not isinstance(pair,dict) or set(pair)!={'question_ref','question','answer_ref','answer'}:
                raise ValueError('Summary pair fields.')
            for role,prefix in [('question','q'),('answer','a')]:
                ref=pair[role+'_ref']
                if not isinstance(ref,str) or not re.fullmatch(prefix+r'-[0-9a-f]{64}',ref) or ref in seen:
                    raise ValueError('Summary opaque reference.')
                seen.add(ref)
                if not isinstance(pair[role],str) or not pair[role]:raise ValueError('Summary QA text.')
        messages=[{'role':'system','content':self.system+'\n'+self.input_template},
            {'role':'user','content':'UNTRUSTED_SUMMARY_INPUT\n'+canonical(payload).decode()}]
        total=self.count(canonical(messages).decode())+self.count(self.schema_bytes.decode())+1024
        if total+self.context_budget['output_tokens']>self.context_budget['context_tokens']:raise ValueError('Summary input token limit.')
        return messages,total

def load_resources(directory=None,tokenizer_file=None,legacy_tokenizer_file=None):
    import tokenizers
    root=Path(directory) if directory else Path(__file__).parents[1]/'agents/prompt_resources/jup035/summary/v4'
    names={'system.md','input.md','schema.json','manifest.json'}
    if root.is_symlink() or not root.is_dir() or {p.name for p in root.iterdir()}!=names:
        raise ValueError('Invalid summary bundle.')
    data={}
    for name in names:
        path=root/name
        limit=16384 if name=='manifest.json' else 65536
        if path.is_symlink() or not path.is_file() or not 0<path.stat().st_size<=limit:
            raise ValueError('Invalid summary resource.')
        raw=path.read_bytes()
        if not 0<len(raw)<=limit:
            raise ValueError('Summary resource limit.')
        data[name]=raw
    manifest=json.loads(data['manifest.json'],object_pairs_hook=unique)
    version=manifest.get('v')
    if type(version) is not int or version not in (2,3,4):raise ValueError('Unsupported summary bundle.')
    if version==3 and sha(data['manifest.json'])!=V3_MANIFEST_SHA:raise ValueError('Summary bundle pin mismatch.')
    if version==4 and sha(data['manifest.json'])!=V4_MANIFEST_SHA:raise ValueError('Summary bundle pin mismatch.')
    tokenizer=FLASH_TOKENIZER if version==4 else TOKENIZER
    schema=SummaryResponse.model_json_schema()
    if data['schema.json']!=canonical(schema):
        raise ValueError('Summary schema differs from authority.')
    expected={'v':version,'kind':f'jup-035.summary.v{version}','system_sha256':sha(data['system.md']),
        'input_sha256':sha(data['input.md']),'response_schema_sha256':sha(data['schema.json']),
        'input_contract':INPUT_CONTRACT,'input_contract_sha256':sha(canonical(INPUT_CONTRACT)),
        'assembler_contract':ASSEMBLER_CONTRACT,'assembler_sha256':sha(canonical(ASSEMBLER_CONTRACT)),
        'policy':POLICY,'policy_sha256':sha(canonical(POLICY)),
        'tokenizer':tokenizer,'budgets':V3_BUDGETS if version>=3 else BUDGETS}
    if canonical(manifest)!=canonical(expected) or tokenizers.__version__!='0.22.1':
        raise ValueError('Summary resource contract mismatch.')
    asset=Path(tokenizer_file) if tokenizer_file else root.parents[1]/('chat/v4/tokenizer.json' if version==4 else 'chat/v2/tokenizer.json')
    if asset.is_symlink() or not asset.is_file() or asset.stat().st_size!=tokenizer['bytes']:
        raise ValueError('Summary tokenizer limit.')
    if sha(asset.read_bytes())!=tokenizer['sha256']:
        raise ValueError('Summary tokenizer mismatch.')
    counter=tokenizers.Tokenizer.from_file(str(asset))
    if sha(asset.read_bytes())!=tokenizer['sha256'] or any((root/n).is_symlink() or (root/n).read_bytes()!=raw for n,raw in data.items()):
        raise ValueError('Summary resources changed during load.')
    counter.no_truncation();counter.no_padding()
    counter.encode('Control offline: español, € y 漢字.',add_special_tokens=False)
    frozen=canonical(manifest)
    legacy=()
    if version==3:
        previous=load_resources(root.parent/'v2',asset)
        if sha(previous.manifest_bytes)!=LEGACY_MANIFEST_SHA:raise ValueError('Legacy summary pin mismatch.')
        legacy=(previous,)
    elif version==4:
        historical=legacy_tokenizer_file or os.getenv('CHAT_LEGACY_TOKENIZER_FILE') or root.parents[1]/'chat/v2/tokenizer.json'
        previous=load_resources(root.parent/'v3',historical)
        if sha(previous.manifest_bytes)!=V3_MANIFEST_SHA:raise ValueError('Legacy summary pin mismatch.')
        legacy=(previous,)+previous.legacy_resources
    return SummaryResources(f'jup-035.summary.v{version}:'+sha(frozen),data['system.md'].decode('utf-8'),
        data['input.md'].decode('utf-8'),frozen,data['schema.json'],tokenizer['sha256'],expected['response_schema_sha256'],counter,legacy_resources=legacy)

"""Local factual guards over QA; these checks do not prove semantic entailment."""
import re
import unicodedata

ENTITY = re.compile(r"https?://[^\s<>\"']+|\b[A-Z]{2,}(?:[-_]\w+)?\b|\b[A-Z]-\d+\b|\b\d+(?:[.,]\d+)*\b|[€$£%]")
NAMES = re.compile(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+\b")
NEGATION = re.compile(r"\b(?:no|sin|nunca|jam[aá]s|not|never|cannot|unknown|inciert\w*|desconocid\w*)\b")
STEMS = ('autor','confirm','elimin','borr','permit','acredit','verific','convert','disminu','aument')
QUALIFIED = re.compile(r"\b(?:contradic\w*|inciert\w*|desconocid\w*|pregunt\w*|solicit\w*|intenci[oó]n|hip[oó]tesis)\b")

def folded(value):
    return ''.join(c for c in unicodedata.normalize('NFD',value.casefold()) if not unicodedata.combining(c))

def factual_text(value, original):
    # Entities must be literal, even when surrounding qualitative prose differs.
    for match in list(ENTITY.finditer(value))+list(NAMES.finditer(value)):
        token=match.group().rstrip('.,;')
        if token not in original:
            raise ValueError('Summary invents an entity.')
    if QUALIFIED.search(value.casefold()):
        return
    output=folded(value)
    for clause in re.split(r'[.;!?\n]',original):
        source=folded(clause)
        if NEGATION.search(source) and any(stem in source and stem in output for stem in STEMS) and not NEGATION.search(output):
            raise ValueError('Summary removes negation or flattens contradictory QA.')

def validate_sources(value,sources):
    if not isinstance(sources,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in sources.items()):
        raise ValueError('Summary sources are invalid.')
    for topic in value['topics']:
        refs=topic['question_refs']+topic['answer_refs']
        if not refs or any(ref not in sources for ref in refs):
            raise ValueError('Summary topic references are invalid.')
        factual_text(topic['text'],'\n'.join(sources[ref] for ref in refs))
    for fact in value['facts']:
        if fact['source_ref'] not in sources or fact['quote'] not in sources[fact['source_ref']]:
            raise ValueError('Summary fact is not literal.')
    original='\n'.join(sources.values())
    for limitation in value['limitations']:
        factual_text(limitation,original)
    return value

def validate_output(value,sources,resources):
    return validate_sources(resources.validate_payload(value),sources)
