"""Derived lifecycle through existing finals only; all summary/call fixtures synthetic.

No fixture is an installed production LLM result. SQLite proves local behavior,
not Cockroach acceptance. No future product module is imported for Red.
"""
import copy
import hashlib
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import event,text

from app.db import chat_history
from app.db.chat_repository import ChatError
from test_chat_history_final_jup035 import repo,create,complete
from test_chat_history_document_jup035 import legacy_db,SCOPE
from test_chat_operations_jup035 import ANSWER


def digest(value):
    return hashlib.sha256(chat_history.dumps(value).encode()).hexdigest()


def columns(db):
    with db.engine.connect() as connection:
        row=connection.execute(text("SELECT CAST(dialogue_history AS TEXT),CAST(dialogue_summary AS TEXT) FROM conversations WHERE id='c'")).first()
    return row[0],row[1]


def summary(db):
    raw=columns(db)[1]
    return None if raw is None else chat_history.loads(raw)


def save(db,value):
    with db.engine.begin() as connection:
        connection.execute(text("UPDATE conversations SET dialogue_summary=:value WHERE id='c'"),{'value':chat_history.dumps(value)})


def seeded(repository):
    operations=[]
    for index in range(6):
        operation=create(repository,'Pregunta '+str(index))
        _,answer=complete(repository,operation,'Respuesta completa '+str(index)+' € 😀')
        operations.append((operation,answer))
    return operations


def synthetic_artifact(db,covered=2):
    document=chat_history.loads(columns(db)[0])
    pairs,_=chat_history.latest_pairs(document)
    by_id={record['id']:record for record in document['messages']}
    ledger=[]
    for pair in pairs[:covered]:
        question,answer=by_id[pair['question_id']],by_id[pair['answer_id']]
        ledger.append({'question_id':question['id'],'answer_id':answer['id'],
            'question_ordinal':question['ordinal'],'answer_ordinal':answer['ordinal'],
            'question_sha256':digest(question),'answer_sha256':digest(answer)})
    epoch=str(uuid4())
    payload={'v':2,'topics':[],'facts':[],'limitations':['SYNTHETIC: no LLM call performed.']}
    artifact={'artifact_id':str(uuid4()),'artifact_revision':1,'lineage_epoch':epoch,
        'parent_artifact_id':None,'parent_artifact_sha256':None,'previous_payload_used':None,
        'source_refs':ledger,'frontier_processed':copy.deepcopy(ledger[-1]),
        'source_selection_hash':digest({'scope':SCOPE,'pairs':ledger}),
        'exact_output':payload,'text_sha256':digest(payload),
        'contract':{'prompt_version':'jup-035.summary.v2:synthetic','schema_sha256':'a'*64,
            'tokenizer_sha256':'b'*64,'policy_version':'synthetic-lifecycle-43'},
        'observations':{'synthetic':True,'call_id':'synthetic-not-dispatched',
            'usage':None,'cost':None,'opaque_precision':Decimal('-0.12345678901234567890123456789')}}
    return {'v':2,'scope':dict(SCOPE),'state_revision':3,'lineage_epoch':epoch,
        'validity':{'valid':True,'reason':None},'artifact':artifact,'invalidation':None}


def retry(repository,operation,answer='Nueva alternativa'):
    current=create(repository,operation['question_content'],operation['operation_id'])
    finished,answer_id=complete(repository,current,answer)
    return current,finished,answer_id


def test_covered_retry_keeps_entire_diagnostic_and_changes_epoch_with_final_in_one_update(repo):
    repository,db=repo;operations=seeded(repository)
    original=synthetic_artifact(db);save(db,original)
    before=chat_history.loads(columns(db)[0]);writes=[]
    def observe(connection,cursor,statement,parameters,context,many):
        if statement.lstrip().startswith('UPDATE conversations SET'):
            writes.append(statement)
    event.listen(db.engine,'before_cursor_execute',observe)
    _,finished,answer_id=retry(repository,operations[0][0])
    actual=summary(db)
    assert actual is not None,'Covered retry discarded the derived diagnostic'
    assert actual['scope']==SCOPE and actual['validity']=={'valid':False,'reason':'retry_covered'}
    assert actual['state_revision']==original['state_revision']+1
    assert actual['lineage_epoch']!=original['lineage_epoch']
    assert actual['artifact']==original['artifact'],'Invalidation must not rewrite original payload/ledger'
    after=chat_history.loads(columns(db)[0])
    assert after['revision']==before['revision']+1 and len(after['messages'])==len(before['messages'])+1
    assert after['messages'][:-1]==before['messages'] and after['messages'][-1]['id']==answer_id
    assert actual['invalidation']['history_revision']==after['revision']
    assert actual['invalidation']['result_message_id']==answer_id and actual['invalidation']['question_id']==operations[0][0]['question_message_id']
    assert finished['state']=='completed' and repository.result(SCOPE,finished)['id']==answer_id
    assert len(writes)==1 and 'dialogue_history=' in writes[0] and 'dialogue_summary=' in writes[0]
    assert len(db.fetch_messages(**SCOPE))==13


def test_retry_pending_preserves_prefix_epoch_and_exact_summary_bytes(repo):
    repository,db=repo;operations=seeded(repository)
    original=synthetic_artifact(db);save(db,original);raw=columns(db)[1]
    retry(repository,operations[5][0])
    assert columns(db)[1]==raw and summary(db)==original


def test_new_completed_after_frontier_preserves_valid_prefix(repo):
    repository,db=repo;seeded(repository)
    original=synthetic_artifact(db);save(db,original);raw=columns(db)[1]
    complete(repository,create(repository,'Nueva pregunta'),'Nueva completa')
    assert columns(db)[1]==raw and summary(db)==original


def test_null_reads_and_final_remain_absent_without_any_summary_write_or_llm(repo):
    repository,db=repo
    statements=[]
    event.listen(db.engine,'before_cursor_execute',lambda c,cu,s,p,co,m:statements.append(s))
    assert columns(db)[1] is None
    db.fetch_messages(**SCOPE);db.fetch_dialogue_history(**SCOPE)
    assert not any(s.lstrip().startswith(('INSERT','UPDATE','DELETE')) for s in statements)
    operation=create(repository);complete(repository,operation)
    assert columns(db)[1] is None
    statements.clear()
    retry(repository,operation)
    assert columns(db)[1] is None
    assert not any('dialogue_summary=' in s for s in statements),'Absent derived state needs no rewrite'


def test_latest_a_b_retry_a_keeps_original_order_and_all_alternatives(repo):
    repository,db=repo;operations=seeded(repository)
    original=synthetic_artifact(db);save(db,original)
    _,_,new_answer=retry(repository,operations[0][0],'A revisada')
    document=db.fetch_dialogue_history(**SCOPE)
    pairs,_=chat_history.latest_pairs(document)
    assert [p['question_id'] for p in pairs]==[op['question_message_id'] for op,_ in operations]
    assert pairs[0]['answer_id']==new_answer and pairs[1]['answer_id']==operations[1][1]
    assert document['messages'][1]['id']==operations[0][1] and document['messages'][-1]['ordinal']==12
    assert summary(db) is not None and summary(db)['validity']['valid'] is False


def test_rollback_after_history_update_keeps_summary_history_and_active_operation(repo):
    repository,db=repo;operations=seeded(repository)
    save(db,synthetic_artifact(db))
    current=create(repository,operations[0][0]['question_content'],operations[0][0]['operation_id'])
    before=columns(db)
    with db.engine.begin() as connection:
        connection.execute(text("CREATE TRIGGER reject_summary_final BEFORE UPDATE ON chat_operations WHEN NEW.state='completed' BEGIN SELECT RAISE(ABORT,'synthetic rejection'); END"))
    with pytest.raises(ChatError):complete(repository,current)
    assert columns(db)==before and repository.get(SCOPE,current['operation_id'])['state']=='active'


@pytest.mark.parametrize('defect',['malformed','foreign_scope','foreign_ref','wrong_hash'])
def test_bad_derived_state_is_quarantined_internally_without_history_failure_or_public_leak(repo,defect):
    repository,db=repo;operations=seeded(repository)
    original=synthetic_artifact(db)
    marker='FOREIGN_OR_MALFORMED_DIAGNOSTIC_ONLY'
    if defect=='malformed':original={'private_marker':marker,'old_extract':True}
    elif defect=='foreign_scope':original['scope']['user_id']='other-owner';original['artifact']['observations']['private_marker']=marker
    elif defect=='foreign_ref':original['artifact']['source_refs'][0]['answer_id']='foreign-answer';original['artifact']['observations']['private_marker']=marker
    else:original['artifact']['source_refs'][0]['answer_sha256']='0'*64;original['artifact']['observations']['private_marker']=marker
    save(db,original)
    _,finished,_=retry(repository,operations[0][0])
    actual=summary(db)
    assert actual is not None and actual['scope']==SCOPE and actual['validity']['valid'] is False
    assert actual['validity']['reason'] in ('invalid_summary','foreign_summary_scope','invalid_summary_sources')
    assert actual['artifact'] is None
    assert actual['invalidation']['diagnostic_raw']==original and actual['invalidation']['diagnostic_sha256']==digest(original)
    public={'conversation':db.fetch_conversation(**SCOPE),'messages':db.fetch_messages(**SCOPE),'result':repository.result(SCOPE,finished)}
    assert marker not in repr(public)
    assert finished['state']=='completed' and len(public['messages'])==13


def test_decimal_unicode_and_metadata_remain_lossless_in_preserved_diagnostic_and_history(repo):
    repository,db=repo;operations=seeded(repository)
    original=synthetic_artifact(db);save(db,original)
    source_before=db.fetch_dialogue_history(**SCOPE)['messages']
    current=create(repository,operations[0][0]['question_content'],operations[0][0]['operation_id'])
    result_id=str(uuid4())
    opaque={'decimal':Decimal('12345678901234567890.000000000000000000001'),'large':9007199254740993,'text':'€ ñ 漢字 😀','nullable':None}
    metadata={'generation':{'question_message_id':current['question_message_id']},'opaque':opaque}
    repository.complete(SCOPE,current['operation_id'],current['current_attempt_id'],{**ANSWER,'answer':'Nueva € 漢字 😀'},metadata,result_id)
    actual=summary(db)
    assert actual is not None and actual['artifact']==original['artifact']
    document=db.fetch_dialogue_history(**SCOPE)
    assert document['messages'][:-1]==source_before and document['messages'][-1]['metadata']['opaque']==opaque


def test_replayed_final_keeps_epoch_and_state_revision_identical(repo):
    repository,db=repo;operations=seeded(repository)
    save(db,synthetic_artifact(db))
    current,finished,result_id=retry(repository,operations[0][0])
    saved=columns(db)
    repository.complete(SCOPE,current['operation_id'],current['current_attempt_id'],ANSWER,{},result_id)
    assert columns(db)==saved and summary(db) is not None


def test_legacy_existing_append_pair_shares_invalid_diagnostic_transition(repo):
    repository,db=repo;operations=seeded(repository)
    original=synthetic_artifact(db);save(db,original)
    first=operations[0][0]
    question={'id':first['question_message_id'],'conversation_id':'c','tenant_id':'t','user_id':'u','requester_id':'u','role':'user','content':first['question_content'],'metadata':{},'created_at':repository.clock()}
    # Existing writer uses a datetime; preserve its instant instead of adapting product.
    from datetime import datetime,timezone
    question['created_at']=datetime.fromtimestamp(repository.clock(),timezone.utc)
    assistant=db.prepare_message(conversation_id='c',tenant_id='t',user_id='u',requester_id='u',role='assistant',content='Alternativa legacy')
    db.append_pair(question=question,assistant=assistant)
    actual=summary(db)
    assert actual is not None and actual['validity']=={'valid':False,'reason':'retry_covered'}
    assert actual['artifact']==original['artifact'] and len(db.fetch_messages(**SCOPE))==13


def test_serializable_sql_retry_reuses_same_epoch_and_result_without_another_generation(repo):
    from sqlalchemy.exc import DBAPIError
    repository,db=repo;operations=seeded(repository)
    original=synthetic_artifact(db);save(db,original)
    epochs=[]
    def restart_once(connection,cursor,statement,parameters,context,many):
        if statement.lstrip().startswith('UPDATE conversations SET'):
            raw=connection.execute(text("SELECT CAST(dialogue_summary AS TEXT) FROM conversations WHERE id='c'")).scalar_one()
            epochs.append(None if raw is None else chat_history.loads(raw)['lineage_epoch'])
            if len(epochs)==1:
                error=Exception('Synthetic40001');error.sqlstate='40001'
                raise DBAPIError(statement,parameters,error)
    event.listen(db.engine,'after_cursor_execute',restart_once)
    _,finished,result_id=retry(repository,operations[0][0])
    assert summary(db) is not None and len(epochs)==2
    assert epochs[0]==epochs[1] and epochs[0]!=original['lineage_epoch']
    assert repository.result(SCOPE,finished)['id']==result_id and len(db.fetch_messages(**SCOPE))==13


@pytest.mark.parametrize('defect',[
    'question_hash','answer_hash','question_ordinal','answer_ordinal','answer_link',
    'prefix_gap','output_hash','selection_hash','frontier','schema_hash',
    'boolean_revision','numeric_epoch','integer_validity','extra_state_field','parent_without_hash'])
def test_self_consistent_derived_corruption_still_cannot_override_canonical_sources(repo,defect):
    repository,db=repo;operations=seeded(repository)
    original=synthetic_artifact(db)
    if defect in ('answer_link','prefix_gap'):
        save(db,original)
        retry(repository,operations[0][0])
        original=summary(db)  # Actual retained invalid artifact still needs correct source links.
    ledger=original['artifact']['source_refs']
    document=db.fetch_dialogue_history(**SCOPE)
    by_id={message['id']:message for message in document['messages']}
    if defect=='question_hash':ledger[0]['question_sha256']='0'*64
    elif defect=='answer_hash':ledger[0]['answer_sha256']='0'*64
    elif defect=='question_ordinal':ledger[0]['question_ordinal']+=1
    elif defect=='answer_ordinal':ledger[0]['answer_ordinal']+=1
    elif defect=='answer_link':
        other=by_id[ledger[1]['answer_id']]
        ledger[0].update(answer_id=other['id'],answer_ordinal=other['ordinal'],answer_sha256=digest(other))
    elif defect=='prefix_gap':original['artifact']['source_refs']=ledger[1:];ledger=original['artifact']['source_refs']
    # Keep derived checksums self-consistent: they cannot vouch for a wrong
    # canonical source, order, version or relationship within the same owner.
    original['artifact']['source_selection_hash']=digest({'scope':SCOPE,'pairs':ledger})
    original['artifact']['frontier_processed']=copy.deepcopy(ledger[-1])
    if defect=='output_hash':original['artifact']['text_sha256']='0'*64
    elif defect=='selection_hash':original['artifact']['source_selection_hash']='0'*64
    elif defect=='frontier':original['artifact']['frontier_processed']['answer_ordinal']+=1
    elif defect=='schema_hash':original['artifact']['contract']['schema_sha256']='not-a-hash'
    elif defect=='boolean_revision':original['state_revision']=True
    elif defect=='numeric_epoch':original['lineage_epoch']=7
    elif defect=='integer_validity':original['validity']['valid']=1
    elif defect=='extra_state_field':original['unrecognized']='internal-diagnostic-only'
    elif defect=='parent_without_hash':original['artifact']['parent_artifact_id']=str(uuid4())
    save(db,original)
    _,finished,result_id=retry(repository,operations[0][0])
    actual=summary(db)
    assert actual is not None and actual['scope']==SCOPE
    assert actual['validity']['valid'] is False and actual['artifact'] is None
    assert actual['validity']['reason'] in ('invalid_summary','invalid_summary_sources')
    assert actual['invalidation']['diagnostic_raw']==original
    assert actual['invalidation']['diagnostic_sha256']==digest(original)
    assert finished['state']=='completed' and repository.result(SCOPE,finished)['id']==result_id
    assert len(db.fetch_messages(**SCOPE))==(14 if defect in ('answer_link','prefix_gap') else 13)


def test_stale_answer_cannot_be_restored_as_a_valid_prefix_even_when_original_still_exists(repo):
    repository,db=repo;operations=seeded(repository)
    original=synthetic_artifact(db);save(db,original)
    retry(repository,operations[0][0])
    save(db,original)  # Synthetic stale derived candidate; no production installer.
    retry(repository,operations[5][0])
    actual=summary(db)
    assert actual['validity']=={'valid':False,'reason':'invalid_summary_sources'} and actual['artifact'] is None
    assert actual['invalidation']['diagnostic_raw']==original
    assert len(db.fetch_messages(**SCOPE))==14


def test_quarantined_diagnostic_does_not_nest_or_change_on_a_later_final(repo):
    repository,db=repo;operations=seeded(repository)
    original={'source_question':operations[0][0]['question_message_id'],'epoch':7}
    save(db,original)
    retry(repository,operations[0][0])
    actual=summary(db);saved=columns(db)[1]
    complete(repository,create(repository,'Otra pregunta'),'Otra respuesta')
    assert columns(db)[1]==saved and summary(db)==actual
    assert actual['artifact'] is None and actual['invalidation']['diagnostic_raw']==original
    assert len(db.fetch_messages(**SCOPE))==15

# CAS53 uses the existing ChatRepository constructor; no future module import.
# Every receipt/candidate below is explicitly synthetic and proves no LLM call.
@pytest.fixture(scope='module')
def summary_resources53():
    from pathlib import Path
    from app.core.summary_resources import load_resources
    root=Path(__file__).resolve().parents[3]/'apps/processor/app/agents/prompt_resources/jup035'
    return load_resources(root/'summary/v2', root/'chat/v2/tokenizer.json')

def contract53(resources):
    import json
    manifest=json.loads(resources.manifest_bytes)
    return {'prompt_version':resources.summary_version,'schema_sha256':resources.response_schema_sha256,
        'tokenizer_sha256':resources.tokenizer_sha256,'policy_version':'jup-035.summary.v2:'+manifest['policy_sha256']}

def helper53(repository):
    value=getattr(repository,'summaries',None)
    assert value is not None,'Existing ChatRepository constructor exposes no scoped summary repository'
    return value

def prepare53(repository,resources,processed=2):
    helper=helper53(repository);snapshot=helper.snapshot(SCOPE,contract53(resources),resources)
    chosen=snapshot.new_pairs[:processed]
    assert len(chosen)==processed
    output={'v':2,'topics':[{'text':'Intenciones previas sin autoridad financiera.',
        'question_refs':[pair['question_ref'] for pair in chosen],'answer_refs':[pair['answer_ref'] for pair in chosen]}],
        'facts':[{'quote':chosen[0]['answer'],'source_ref':chosen[0]['answer_ref']}],
        'limitations':['SYNTHETIC QA-only output; no model dispatch performed.']}
    receipt={'synthetic':True,'call_id':str(uuid4()),'dispatch_count':1,
        'input_hash':digest({'previous_summary':snapshot.previous_payload_used,'pairs':chosen}),
        'output_hash':digest(output),'usage':None,'cost':None,'boot_id':'synthetic-boot'}
    candidate=helper.candidate(snapshot,output,receipt,processed)
    return helper,snapshot,candidate,output,receipt

def test_summary_constructor_snapshot_is_scoped_immutable_read_only_and_reserves_recent_four(repo,summary_resources53):
    repository,db=repo;seeded(repository);before=columns(db);writes=[]
    event.listen(db.engine,'before_cursor_execute',lambda c,cu,s,p,co,m:writes.append(s))
    helper=helper53(repository);snapshot=helper.snapshot(SCOPE,contract53(summary_resources53),summary_resources53)
    assert snapshot.scope==SCOPE and snapshot.parent_hash is None and snapshot.previous_payload_used is None
    assert len(snapshot.new_pairs)==2 and snapshot.recent_reserved==4
    assert snapshot.new_pairs[0]['question'].startswith('Pregunta 0')
    from dataclasses import FrozenInstanceError
    with pytest.raises(FrozenInstanceError):snapshot.epoch='changed'
    snapshot.scope['user_id']='other';snapshot.new_pairs[0]['answer']='changed'
    assert snapshot.scope==SCOPE and snapshot.new_pairs[0]['answer']!='changed'
    assert columns(db)==before and not any(s.lstrip().startswith(('INSERT','UPDATE','DELETE')) for s in writes)

def test_summary_initial_install_preserves_full_history_and_writes_one_scoped_jsonb(repo,summary_resources53):
    repository,db=repo;seeded(repository);before=columns(db)[0]
    helper,snapshot,candidate,output,receipt=prepare53(repository,summary_resources53)
    result=helper.install(SCOPE,snapshot,candidate);state=summary(db)
    assert result['installed'] is True and result['artifact_id']==candidate.artifact_id
    assert state['scope']==SCOPE and state['validity']=={'valid':True,'reason':None}
    assert state['state_revision']==1 and state['lineage_epoch']==snapshot.epoch
    assert state['artifact']['exact_output']==output and state['artifact']['text_sha256']==digest(output)
    assert state['artifact']['observations']['receipt']==receipt
    assert state['artifact']['frontier_processed']==state['artifact']['source_refs'][-1]
    assert len(state['artifact']['source_refs'])==2 and columns(db)[0]==before
    assert state['artifact']['previous_payload_used'] is None
    assert helper.resolve_install(SCOPE,candidate.artifact_id,digest(output))['installed'] is True
    assert helper.resolve_install(SCOPE,candidate.artifact_id,'0'*64)['installed'] is False

def test_summary_completed_after_snapshot_remains_pending_without_false_stale(repo,summary_resources53):
    repository,db=repo;seeded(repository)
    helper,snapshot,candidate,_,_=prepare53(repository,summary_resources53)
    complete(repository,create(repository,'Posterior al snapshot'),'Posterior completa')
    assert helper.install(SCOPE,snapshot,candidate)['installed'] is True
    view=helper.view(SCOPE,contract53(summary_resources53),summary_resources53)
    assert view['source_valid'] and view['consumable']
    assert view['coverage']['processed_pairs']==2 and view['coverage']['pending_pairs']==1 and view['coverage']['recent_reserved']==4

@pytest.mark.parametrize('change',['selected_retry','parent_install','epoch_invalidation','foreign_scope','contract'])
def test_summary_cas_rejects_stale_latest_parent_epoch_scope_and_contract(repo,summary_resources53,change):
    repository,db=repo;operations=seeded(repository)
    helper,snapshot,candidate,_,_=prepare53(repository,summary_resources53);scope=dict(SCOPE)
    if change=='selected_retry':retry(repository,operations[0][0])
    elif change=='parent_install':helper.install(SCOPE,snapshot,candidate)
    elif change=='epoch_invalidation':
        helper.install(SCOPE,snapshot,candidate);retry(repository,operations[0][0])
    elif change=='foreign_scope':scope['user_id']='foreign-owner'
    else:
        from dataclasses import replace
        candidate=replace(candidate,contract_bytes=chat_history.dumps({**contract53(summary_resources53),'policy_version':'other'}))
    before=columns(db)
    with pytest.raises(ChatError) as captured:helper.install(scope,snapshot,candidate)
    assert captured.value.code in ['summary_stale','summary_candidate_invalid','not_found']
    assert columns(db)==before

def test_summary_second_install_uses_exact_confirmed_previous_and_contiguous_frontier(repo,summary_resources53):
    repository,db=repo;seeded(repository)
    helper,first,one,output,_=prepare53(repository,summary_resources53);helper.install(SCOPE,first,one)
    complete(repository,create(repository,'Séptima'),'Respuesta séptima');complete(repository,create(repository,'Octava'),'Respuesta octava')
    helper,second,two,_,_=prepare53(repository,summary_resources53)
    assert second.previous_payload_used==output and second.parent_hash==digest(summary(db))
    helper.install(SCOPE,second,two);state=summary(db)
    assert state['state_revision']==2 and state['lineage_epoch']==first.epoch
    assert state['artifact']['artifact_revision']==2 and len(state['artifact']['source_refs'])==4
    assert state['artifact']['parent_artifact_id']==one.artifact_id and state['artifact']['previous_payload_used']==output
    assert state['artifact']['frontier_processed']['question_ordinal']==6

def test_summary_retry_of_pending_source_preserves_installed_prefix_but_stales_selected_batch(repo,summary_resources53):
    repository,db=repo;operations=seeded(repository)
    helper,first,one,_,_=prepare53(repository,summary_resources53);helper.install(SCOPE,first,one)
    complete(repository,create(repository,'Séptima'),'Séptima');complete(repository,create(repository,'Octava'),'Octava')
    helper,second,two,_,_=prepare53(repository,summary_resources53);before=columns(db)[1]
    retry(repository,operations[2][0]);assert columns(db)[1]==before
    with pytest.raises(ChatError) as captured:helper.install(SCOPE,second,two)
    assert captured.value.code=='summary_stale' and columns(db)[1]==before

def test_summary_covered_retry_rebuild_keeps_immediate_diagnostic_and_never_uses_invalid_previous(repo,summary_resources53):
    repository,db=repo;operations=seeded(repository)
    helper,first,one,_,_=prepare53(repository,summary_resources53);helper.install(SCOPE,first,one);installed=summary(db)
    retry(repository,operations[0][0]);invalidated=summary(db)
    assert invalidated['artifact']==installed['artifact'] and invalidated['lineage_epoch']!=first.epoch
    helper,rebuild,two,_,_=prepare53(repository,summary_resources53)
    assert rebuild.previous_payload_used is None and rebuild.epoch==invalidated['lineage_epoch']
    helper.install(SCOPE,rebuild,two);state=summary(db)
    assert state['validity']['valid'] and state['artifact']['parent_artifact_id'] is None
    diagnostic=state['artifact']['observations']['superseded_invalidated']
    assert diagnostic['artifact_id']==one.artifact_id and diagnostic['state_sha256']==digest(invalidated) and diagnostic['reason']=='retry_covered'
    assert diagnostic['artifact']['exact_output']==installed['artifact']['exact_output']

def test_summary_sql40001_replays_only_fixed_candidate_and_stable_ids(repo,summary_resources53):
    from sqlalchemy.exc import DBAPIError
    repository,db=repo;seeded(repository);helper,snapshot,candidate,_,_=prepare53(repository,summary_resources53);writes=[]
    def restart(connection,cursor,statement,parameters,context,many):
        if statement.lstrip().startswith('UPDATE conversations SET dialogue_summary='):
            raw=connection.execute(text("SELECT CAST(dialogue_summary AS TEXT) FROM conversations WHERE id='c'")).scalar_one();writes.append(raw)
            if len(writes)==1:
                error=Exception('Synthetic SQL40001');error.sqlstate='40001';raise DBAPIError(statement,parameters,error)
    event.listen(db.engine,'after_cursor_execute',restart)
    assert helper.install(SCOPE,snapshot,candidate)['installed'] is True
    assert len(writes)==2 and writes[0]==writes[1] and summary(db)['artifact']['artifact_id']==candidate.artifact_id

def test_summary_commit_unknown_resolves_only_same_id_and_hash_without_redispatch(repo,summary_resources53,monkeypatch):
    repository,db=repo;seeded(repository);helper,snapshot,candidate,_,_=prepare53(repository,summary_resources53)
    original=repository._transaction;calls=[]
    def uncertain(scope,action,on_unique=None):
        result=original(scope,action,on_unique);calls.append(result)
        if len(calls)==1:raise ChatError(503,'commit_unknown')
        return result
    monkeypatch.setattr(repository,'_transaction',uncertain)
    result=helper.install(SCOPE,snapshot,candidate)
    assert result['installed'] is True and result['resolved_commit'] is True and len(calls)==2
    assert summary(db)['artifact']['artifact_id']==candidate.artifact_id

def test_summary_unconfirmed40003_remains_unknown_without_install_or_retry(repo,summary_resources53,monkeypatch):
    repository,db=repo;seeded(repository);helper,snapshot,candidate,_,_=prepare53(repository,summary_resources53);original=repository._transaction;calls=[]
    def uncertain(scope,action,on_unique=None):
        calls.append(action)
        if len(calls)==1:raise ChatError(503,'commit_unknown')
        return original(scope,action,on_unique)
    monkeypatch.setattr(repository,'_transaction',uncertain)
    with pytest.raises(ChatError) as captured:helper.install(SCOPE,snapshot,candidate)
    assert captured.value.code=='commit_unknown' and len(calls)==2 and summary(db) is None

@pytest.mark.parametrize('defect',['wrong_quote','foreign_ref','duplicate_receipt','wrong_output_hash','wrong_input_hash','bad_schema','zero_pairs','recent_pairs'])
def test_summary_candidate_rejects_invalid_shape_refs_receipt_and_selected_frontier_before_sql(repo,summary_resources53,defect):
    repository,db=repo;seeded(repository);helper,snapshot,_,output,receipt=prepare53(repository,summary_resources53);count=2
    if defect=='wrong_quote':output['facts'][0]['quote']='Invented absent literal'
    elif defect=='foreign_ref':output['facts'][0]['source_ref']='a-'+'f'*64
    elif defect=='duplicate_receipt':receipt['dispatch_count']=2
    elif defect=='wrong_output_hash':receipt['output_hash']='0'*64
    elif defect=='wrong_input_hash':receipt['input_hash']='0'*64
    elif defect=='bad_schema':output['v']=2.0
    elif defect=='zero_pairs':count=0
    else:count=3
    if defect in ['wrong_quote','foreign_ref','bad_schema']:receipt['output_hash']=digest(output)
    before=columns(db)
    with pytest.raises(ChatError) as captured:helper.candidate(snapshot,output,receipt,count)
    assert captured.value.code=='summary_candidate_invalid' and columns(db)==before

@pytest.mark.parametrize('defect',['malformed','foreign_scope','wrong_hash'])
def test_summary_view_quarantines_derived_only_and_never_leaks_diagnostic(repo,summary_resources53,defect):
    repository,db=repo;seeded(repository);original=synthetic_artifact(db);marker='SYNTHETIC_PRIVATE_DIAGNOSTIC'
    if defect=='malformed':original={'private_marker':marker}
    elif defect=='foreign_scope':original['scope']['user_id']='foreign-owner';original['artifact']['observations']['private_marker']=marker
    else:original['artifact']['source_refs'][0]['answer_sha256']='0'*64
    save(db,original);before=columns(db)
    view=helper53(repository).view(SCOPE,contract53(summary_resources53),summary_resources53)
    assert view['consumable'] is False and view['payload'] is None and marker not in repr(view)
    assert columns(db)==before and len(db.fetch_messages(**SCOPE))==12

def test_summary_without_authoritative_validator_is_not_consumable_even_when_ledger_valid(repo,summary_resources53):
    repository,db=repo;seeded(repository);helper,snapshot,candidate,_,_=prepare53(repository,summary_resources53);helper.install(SCOPE,snapshot,candidate)
    view=helper.view(SCOPE,contract53(summary_resources53),None)
    assert view['source_valid'] and view['consumable'] is False and view['payload'] is None and view['reason']=='summary_validator_unavailable'
