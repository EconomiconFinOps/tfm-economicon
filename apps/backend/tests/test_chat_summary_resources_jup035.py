"""Backend verifies the processor schema through existing generic interfaces.

Red uses the existing validator and image contract, without future imports.
Direct loader/batch tests are added after the helper exists in mutation.
"""
import asyncio,copy,hashlib,json,shutil
from pathlib import Path
import pytest
from app.schemas.chat import _validate
from test_chat_operations_jup035 import api

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=ROOT/'apps/processor/app/agents/prompt_resources/jup035/summary/v2'
SCHEMA=json.loads((BUNDLE/'schema.json').read_bytes())
VALUE={'v':2,'topics':[{'text':'Intención sintética','question_refs':['q-'+'1'*64],'answer_refs':['a-'+'2'*64]}],
       'facts':[{'quote':'Texto literal','source_ref':'a-'+'2'*64}],'limitations':['Sin llamada real']}

def test_processor_schema_accepts_valid_closed_backend_payload():
    _validate(copy.deepcopy(VALUE),SCHEMA,SCHEMA)

@pytest.mark.parametrize('field',['question_refs','answer_refs'])
def test_generic_validator_rejects_duplicate_source_refs(field):
    value=copy.deepcopy(VALUE);value['topics'][0][field]*=2
    with pytest.raises(ValueError):_validate(value,SCHEMA,SCHEMA)

@pytest.mark.parametrize('defect',['float_version','bool_version','extra','topics9','facts9','limitations5','wrong_question_role','bad_ref','text513','text_number','missing','array_string'])
def test_processor_schema_is_strict_in_existing_backend_validator(defect):
    value=copy.deepcopy(VALUE)
    if defect=='float_version':value['v']=2.0
    elif defect=='bool_version':value['v']=True
    elif defect=='extra':value['private']='unapproved'
    elif defect=='topics9':value['topics']*=9
    elif defect=='facts9':value['facts']*=9
    elif defect=='limitations5':value['limitations']*=5
    elif defect=='wrong_question_role':value['topics'][0]['question_refs']=['a-'+'1'*64]
    elif defect=='bad_ref':value['facts'][0]['source_ref']='raw-owner-id'
    elif defect=='text513':value['topics'][0]['text']='x'*513
    elif defect=='text_number':value['topics'][0]['text']=42
    elif defect=='missing':del value['facts']
    else:value['topics']='not-array'
    with pytest.raises(ValueError):_validate(value,SCHEMA,SCHEMA)

def test_backend_image_copies_authoritative_summary_bundle_and_validates_it_at_build():
    docker=(ROOT/'apps/backend/Dockerfile').read_text(encoding='utf-8')
    assert 'COPY apps/processor/app/agents/prompt_resources/jup035/summary /opt/economicon/summary' in docker
    assert 'from app.core.summary_resources import load_resources as summary' in docker
    assert 'summary()' in docker

def test_processor_image_validates_summary_bundle_at_build_without_new_dependency():
    docker=(ROOT/'apps/processor/Dockerfile').read_text(encoding='utf-8')
    assert 'from app.core.summary_resources import load_resources as summary' in docker
    assert 'summary()' in docker

@pytest.fixture
def summary_bundle(api,tmp_path,monkeypatch):
    root=tmp_path/'trusted-summary-v2';root.mkdir()
    for name in ['system.md','input.md','schema.json','manifest.json']:shutil.copyfile(BUNDLE/name,root/name)
    asset=ROOT/'apps/processor/app/agents/prompt_resources/jup035/chat/v2/tokenizer.json'
    monkeypatch.setenv('CHAT_ENABLED','true')
    monkeypatch.setenv('CHAT_RESOURCE_DIRECTORY',str(asset.parent))
    monkeypatch.setenv('CHAT_TOKENIZER_FILE',str(asset))
    monkeypatch.setenv('SUMMARY_RESOURCE_DIRECTORY',str(root))
    monkeypatch.setattr(api[0].state,'chat_resources',None,raising=False)
    monkeypatch.setattr(api[0].state,'summary_resources',None,raising=False)
    return api,root,asset

def initialized(bundle,callback):
    async def exercise():
        from app.main import initialize_chat_resources
        application=bundle[0][0]
        await initialize_chat_resources(application)
        try:return callback(application)
        finally:
            service=getattr(application.state,'chat_service',None)
            if service is not None:await service.close()
            assert bundle[0][2].claims==[],'Loading/preparing resources must not call a model'
    return asyncio.run(exercise())

def loaded(application):
    value=getattr(application.state,'summary_resources',None)
    assert value is not None,'Existing initializer did not load the optional authoritative summary resources'
    assert application.state.chat_resources is not None
    return value

def pairs(count=8):
    return [{'question_ref':'q-'+hashlib.sha256(('q'+str(i)).encode()).hexdigest(),
             'answer_ref':'a-'+hashlib.sha256(('a'+str(i)).encode()).hexdigest(),
             'question':'Pregunta '+str(i)+' € ñ 漢字 😀',
             'answer':'Respuesta literal '+str(i)+'; se conserva incertidumbre.'} for i in range(count)]

def test_initializer_loads_same_authoritative_bundle_schema_and_offline_counter(summary_bundle):
    def check(application):
        resources=loaded(application);raw=(summary_bundle[1]/'manifest.json').read_bytes()
        assert resources.summary_version=='jup-035.summary.v2:'+hashlib.sha256(raw).hexdigest()
        assert resources.manifest_bytes==raw
        assert resources.response_schema==SCHEMA and resources.response_schema_sha256==hashlib.sha256((BUNDLE/'schema.json').read_bytes()).hexdigest()
        assert resources.tokenizer_sha256==json.loads(raw)['tokenizer']['sha256']
        assert resources.system==(summary_bundle[1]/'system.md').read_text(encoding='utf-8')
        assert resources.count('Control € 漢字')>0
    initialized(summary_bundle,check)

@pytest.mark.parametrize('defect',['missing_system','missing_input','missing_schema','missing_manifest','tampered_system','self_hashed_schema','extra','duplicate_manifest','float_version','tokenizer_pin','budgets','policy','root_symlink','file_symlink','oversized_input','absent_tokenizer'])
def test_invalid_optional_bundle_keeps_main_operational_without_any_call(summary_bundle,monkeypatch,defect,tmp_path):
    _,root,asset=summary_bundle;manifest=json.loads((root/'manifest.json').read_bytes())
    if defect.startswith('missing_'):(root/(defect.removeprefix('missing_')+('.json' if defect in ['missing_schema','missing_manifest'] else '.md'))).unlink()
    elif defect=='tampered_system':(root/'system.md').write_text('tampered',encoding='utf-8')
    elif defect=='self_hashed_schema':
        schema=copy.deepcopy(SCHEMA);schema['properties']['facts']['maxItems']=99
        raw=json.dumps(schema,sort_keys=True,separators=(',',':')).encode();(root/'schema.json').write_bytes(raw);manifest['response_schema_sha256']=hashlib.sha256(raw).hexdigest()
    elif defect=='extra':(root/'unexpected.md').write_text('unexpected',encoding='utf-8')
    elif defect=='duplicate_manifest':(root/'manifest.json').write_bytes(b'{"v":2,'+(root/'manifest.json').read_bytes()[1:])
    elif defect=='float_version':manifest['v']=2.0
    elif defect=='tokenizer_pin':manifest['tokenizer']['revision']='unapproved'
    elif defect=='budgets':manifest['budgets']['input_total_tokens']=4097
    elif defect=='policy':manifest['policy']['literal_quotes']=False
    elif defect=='root_symlink':
        link=tmp_path/'linked-bundle';link.symlink_to(root,target_is_directory=True);monkeypatch.setenv('SUMMARY_RESOURCE_DIRECTORY',str(link))
    elif defect=='file_symlink':
        actual=tmp_path/'linked-system';actual.write_bytes((root/'system.md').read_bytes());(root/'system.md').unlink();(root/'system.md').symlink_to(actual)
    elif defect=='oversized_input':(root/'input.md').write_bytes(b'x'*65537)
    else:monkeypatch.setenv('CHAT_TOKENIZER_FILE',str(tmp_path/'absent-tokenizer'))
    if defect in ['self_hashed_schema','float_version','tokenizer_pin','budgets','policy']:(root/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,separators=(',',':')),encoding='utf-8')
    def check(application):
        assert getattr(application.state,'summary_resources',None) is None
        if defect!='absent_tokenizer':assert application.state.chat_resources is not None and application.state.chat_context_builder is not None
    initialized(summary_bundle,check)

def test_loaded_resources_and_schema_are_frozen_after_disk_and_caller_changes(summary_bundle):
    def check(application):
        resources=loaded(application);before=resources.summary_version;system=resources.system
        exposed=resources.response_schema;exposed['properties']['facts']['maxItems']=99
        (summary_bundle[1]/'system.md').write_text('later tamper',encoding='utf-8')
        assert resources.summary_version==before and resources.system==system and resources.response_schema==SCHEMA
    initialized(summary_bundle,check)

def test_disabled_initializer_clears_stale_optional_resources(summary_bundle,monkeypatch):
    monkeypatch.setenv('CHAT_ENABLED','false');monkeypatch.setattr(summary_bundle[0][0].state,'summary_resources',object())
    initialized(summary_bundle,lambda application:assert_no_summary(application))

def assert_no_summary(application):assert getattr(application.state,'summary_resources',None) is None

def test_lot_excludes_four_recent_and_preserves_exact_previous_and_qa_only(summary_bundle):
    source=pairs();previous=copy.deepcopy(VALUE)
    def check(application):
        resources=loaded(application);result=resources.prepare_lot(previous,source)
        assert result['payload']=={'previous_summary':previous,'pairs':source[:4]}
        assert result['selected_pairs']==4 and result['recent_reserved']==4 and result['pending_pairs']==0
        assert result['messages']==[{'role':'system','content':resources.system+'\n'+resources.input_template},
            {'role':'user','content':'UNTRUSTED_SUMMARY_INPUT\n'+json.dumps(result['payload'],ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)}]
        expected=resources.count(json.dumps(result['messages'],ensure_ascii=False,sort_keys=True,separators=(',',':')))+resources.count(json.dumps(SCHEMA,ensure_ascii=False,sort_keys=True,separators=(',',':')))+1024
        assert result['input_total_tokens']==expected<=4096
        assert result['input_hash']==hashlib.sha256(json.dumps(result['payload'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        source[0]['question']='later mutation';previous['topics']=[]
        assert result['payload']['pairs'][0]['question']!='later mutation' and result['payload']['previous_summary']['topics']
    initialized(summary_bundle,check)

def test_first_pair_too_large_is_pending_without_skip_truncation_or_frontier(summary_bundle,monkeypatch):
    monkeypatch.setenv('SUMMARY_CONTEXT_TOKENS','14096')
    source=pairs(9);source[0]['answer']='dato '*5000
    def check(application):
        result=loaded(application).prepare_lot(None,source)
        assert result['selected_pairs']==0 and result['payload'] is None and result['messages']==[]
        assert result['reason']=='pending_pair_too_large' and result['pending_pairs']==5
        assert source[0]['answer']=='dato '*5000
    initialized(summary_bundle,check)

def test_lot_stops_at_first_oversized_pair_and_keeps_oldest_prefix(summary_bundle,monkeypatch):
    monkeypatch.setenv('SUMMARY_CONTEXT_TOKENS','14096')
    source=pairs(10);source[1]['answer']='dato '*5000
    def check(application):
        result=loaded(application).prepare_lot(None,source)
        assert result['payload']['pairs']==source[:1] and result['selected_pairs']==1 and result['pending_pairs']==5
        assert result['reason']=='pending_pair_too_large' and result['input_total_tokens']<=4096
    initialized(summary_bundle,check)

def test_only_recent_pairs_cannot_create_summary_lot(summary_bundle):
    def check(application):
        result=loaded(application).prepare_lot(None,pairs(4))
        assert result['payload'] is None and result['selected_pairs']==0 and result['reason']=='recent_pairs_only'
    initialized(summary_bundle,check)

@pytest.mark.parametrize('field',['screen_context','metadata','scope','cost_evidence','api_key'])
def test_non_qa_fields_never_enter_compaction_payload(summary_bundle,field):
    source=pairs();source[0][field]='synthetic-must-not-reach-model'
    def check(application):
        resources=loaded(application)
        with pytest.raises(ValueError):resources.prepare_lot(None,source)
    initialized(summary_bundle,check)

@pytest.mark.parametrize('defect',['duplicate_ref','bad_ref','wrong_role','number_text','float_previous','large_previous_content','large_previous_payload'])
def test_input_or_previous_summary_is_rejected_without_repairs_or_calls(summary_bundle,defect):
    source=pairs();previous=copy.deepcopy(VALUE)
    if defect=='duplicate_ref':source[1]['question_ref']=source[0]['question_ref']
    elif defect=='bad_ref':source[0]['answer_ref']='real-owner-id'
    elif defect=='wrong_role':source[0]['question_ref']='a-'+'1'*64
    elif defect=='number_text':source[0]['question']=42
    elif defect=='float_previous':previous['v']=2.0
    elif defect=='large_previous_content':previous['topics']=[{**VALUE['topics'][0],'text':'dato '*100} for _ in range(8)]
    else:previous['topics']=[{**VALUE['topics'][0],'question_refs':['q-'+str(i)*64 for i in range(1,9)],'answer_refs':['a-'+str(i)*64 for i in range(1,9)]} for _ in range(8)]
    def check(application):
        resources=loaded(application)
        with pytest.raises(ValueError):resources.prepare_lot(previous,source)
    initialized(summary_bundle,check)


@pytest.mark.parametrize('field',['question_refs','answer_refs'])
def test_loaded_backend_payload_rejects_duplicate_refs_after_provider_projection(summary_bundle,field):
    def check(application):
        resources=loaded(application)
        value=copy.deepcopy(VALUE)
        assert resources.validate_payload(value)==value
        duplicate=copy.deepcopy(value);duplicate['topics'][0][field]*=2
        with pytest.raises(ValueError):resources.validate_payload(duplicate)
        assert resources.response_schema['$defs']['SummaryTopic']['properties'][field]['uniqueItems'] is True
        assert resources.response_schema_sha256=='72404e66533f03268bf53727e7ed01cad00a71c31ad483f823ee4c3c8e06783e'
    initialized(summary_bundle,check)
