"""Isolated implementation tests: durable admission and full context budgets."""
import asyncio
import json
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import inspect, text

from app.db.chat_repository import ChatError, ChatRepository
from test_chat_operations_jup035 import api, body, ANSWER
from test_chat_summary_scheduler_jup035 import packet
from test_chat_summary_lifecycle_jup035 import summary_resources53

SCOPE = {'tenant_id': 't', 'user_id': 'alice', 'conversation_id': 'alice-chat'}
ROOT = Path(__file__).resolve().parents[3]/'apps/processor/app/agents/prompt_resources/jup035'


def repository(api):
    # Exercise old admission meaningfully even before the additive migration.
    if 'dialogue_compaction' not in {c['name'] for c in inspect(api[1].engine).get_columns('conversations')}:
        with api[1].engine.begin() as c:
            c.execute(text('ALTER TABLE conversations ADD COLUMN dialogue_compaction JSONB NULL'))
    return ChatRepository(api[1], api[3])


def control(api, state='pending'):
    value = {'v': 1, 'state': state, 'generation': str(uuid4()), 'revision': 0,
             'history_revision': 0, 'parent_hash': None, 'owner': None,
             'lease_until': None, 'job': None, 'reason': 'queued'}
    with api[1].engine.begin() as c:
        c.execute(text("UPDATE conversations SET dialogue_compaction=:value WHERE id='alice-chat'"),
                  {'value': json.dumps(value)})
    return value


def test_migration_adds_nullable_control_without_backfill(api):
    columns = {c['name']: c for c in inspect(api[1].engine).get_columns('conversations')}
    assert 'dialogue_compaction' in columns, 'durable compaction migration is missing'
    assert columns['dialogue_compaction']['nullable']
    with api[1].engine.connect() as c:
        assert c.execute(text('SELECT count(*) FROM conversations WHERE dialogue_compaction IS NOT NULL')).scalar() == 0
        assert c.execute(text("SELECT count(*) FROM schema_migrations WHERE version='004'")).scalar() == 1


@pytest.mark.parametrize('state', ['pending', 'running', 'reconciling', 'failed'])
def test_compaction_blocks_new_reservation_but_not_other_conversation(api, state):
    repo = repository(api)
    control(api, state)
    with pytest.raises(ChatError) as error:
        repo.reserve(SCOPE, body(), {'prompt_version': 'synthetic', 'messages': []})
    assert (error.value.status, error.value.code) == (409, 'conversation_compacting')
    other = {**SCOPE, 'user_id': 'bob', 'conversation_id': 'bob-chat'}
    assert repo.reserve(other, body('bob'), {'prompt_version': 'synthetic', 'messages': []})[1]


def test_existing_idempotent_request_remains_readable_while_compacting(api):
    repo = repository(api)
    payload = body()
    row, _ = repo.reserve(SCOPE, payload, {'prompt_version': 'synthetic', 'messages': []})
    control(api)
    again, created = repo.reserve(SCOPE, payload, {'prompt_version': 'synthetic', 'messages': []})
    assert not created and again['operation_id'] == row['operation_id']


def test_final_and_pending_share_transaction_and_replay_does_not_replace_control(api, monkeypatch):
    monkeypatch.setenv('SUMMARY_ENABLED', 'true')
    repo = repository(api)
    row, _ = repo.reserve(SCOPE, body(), {'prompt_version': 'synthetic', 'messages': []})
    row, won = repo.claim(SCOPE, row['operation_id'], 'boot')
    assert won
    result_id = str(uuid4())
    metadata = {'generation': {'question_message_id': row['question_message_id']}}
    repo.complete(SCOPE, row['operation_id'], row['current_attempt_id'], ANSWER, metadata, result_id)
    with api[1].engine.connect() as c:
        raw = c.execute(text("SELECT dialogue_compaction FROM conversations WHERE id='alice-chat'")).scalar()
    assert raw is not None, 'final must leave a durable barrier before observers can send'
    pending = json.loads(raw)
    assert pending['state'] == 'pending' and pending['history_revision'] == 1
    repo.complete(SCOPE, row['operation_id'], row['current_attempt_id'], ANSWER, metadata, result_id)
    with api[1].engine.connect() as c:
        assert c.execute(text("SELECT dialogue_compaction FROM conversations WHERE id='alice-chat'")).scalar() == raw


def test_stale_context_fence_rejected_inside_reserve(api):
    repo = repository(api)
    context = {'prompt_version': 'synthetic', 'messages': [],
               'memory_fence': {'history_revision': 99, 'parent_hash': None}}
    with pytest.raises(ChatError) as error:
        repo.reserve(SCOPE, body(), context)
    assert error.value.code == 'context_stale'


def test_durable_control_excludes_second_owner_and_stale_release(api):
    repo = repository(api)
    control(api)
    assert hasattr(repo, 'compactions'), 'repository lacks durable control transitions'
    first = repo.compactions.claim(SCOPE, 'owner-one')
    assert first is not None
    assert repo.compactions.claim(SCOPE, 'owner-two') is None
    stale = dict(first)
    running = repo.compactions.transition(SCOPE, first, state='running', reason='running',
        job={'job_id': str(uuid4()), 'boot_id': 'processor', 'input_hash': '1'*64, 'summary_version': 'synthetic'})
    with pytest.raises(ChatError):
        repo.compactions.transition(SCOPE, stale, clear=True)
    assert repo.compactions.get(SCOPE)['job'] == running['job']
    from app.core.config import get_settings
    api[3].advance(get_settings().summary_timeout_seconds)
    assert repo.compactions.claim(SCOPE, 'owner-two') is None
    api[3].advance(16)
    recovered = repo.compactions.claim(SCOPE, 'owner-two')
    assert recovered['state'] == 'reconciling' and recovered['job'] == running['job']
    with pytest.raises(ChatError):
        repo.compactions.transition(SCOPE, running, clear=True)


def test_early_admission_does_not_call_descriptor_during_compaction(api):
    from app.services.chat_operations import ChatOperations
    repository(api)
    control(api)
    called = []
    async def descriptor():
        called.append(True)
        return await type(api[2]).descriptor(api[2])
    api[2].descriptor = descriptor
    async def exercise():
        service = ChatOperations(api[0])
        try:
            with pytest.raises(ChatError) as error:
                await service.open(SCOPE, body())
            assert error.value.code == 'conversation_compacting'
            assert called == []
        finally:
            await service.close()
    asyncio.run(exercise())


def test_chat_context_can_exceed_old_limit_with_real_tokenizer():
    from app.core.chat_resources import load_resources
    resources = load_resources(ROOT/'chat/v2')
    messages = [{'role': 'system', 'content': resources.system},
                {'role': 'user', 'content': 'dato '*12000}]
    assert resources.count_messages(messages) > 8192


def test_summary_lot_can_exceed_old_limit_with_real_tokenizer():
    from app.core.summary_resources import load_resources
    from test_chat_summary_resources_jup035 import pairs
    resources = load_resources(ROOT/'summary/v2', ROOT/'chat/v2/tokenizer.json')
    qa = pairs(10)
    for pair in qa:
        pair['answer'] = 'texto literal '*2500
    lot = resources.prepare_lot(None, qa)
    assert lot['payload'] is not None and lot['input_total_tokens'] > 4096


def test_chat_keeps_more_than_four_complete_pairs(api):
    from app.core.chat_resources import load_resources
    from app.services.chat_context import ChatContext
    from test_chat_history_context_jup035 import install
    records = []
    for i in range(9):
        records.extend([(f'q{i}', 'user', f'q{i}', {}), (f'a{i}', 'assistant', f'q{i}', {})])
    install(api[1], records)
    resources = load_resources(ROOT/'chat/v2')
    context = ChatContext(api[0], resources).build(SCOPE, body())
    current = json.loads(context['messages'][-1]['content'].split('\n', 1)[1])
    assert len(current['recent_pairs']) == 9


def test_configured_token_budget_and_descriptor_are_enforced(monkeypatch):
    from app.core.chat_resources import load_resources
    monkeypatch.setenv('CHAT_CONTEXT_TOKENS', '16384')
    resources = load_resources(ROOT/'chat/v2')
    with pytest.raises(ChatError):
        resources.count_messages([{'role': 'system', 'content': resources.system},
                                  {'role': 'user', 'content': 'dato '*20000}])
    manifest = json.loads(resources.manifest_bytes)
    descriptor = {'prompt_version': resources.prompt_version, 'tokenizer_sha256': manifest['tokenizer']['sha256'],
                  'response_schema_sha256': resources.schema_sha256,
                  'context_budget': {'model_context_tokens': 1048576}}
    with pytest.raises(ChatError):
        resources.verify_descriptor(descriptor)


def test_summary_selection_counts_complete_wire_envelope_bytes():
    from app.core.summary_resources import load_resources
    from app.schemas.chat import canonical
    from test_chat_summary_resources_jup035 import pairs
    resources = load_resources(ROOT/'summary/v2', ROOT/'chat/v2/tokenizer.json')
    qa = pairs(8)
    first = {'previous_summary': None, 'pairs': qa[:1]}
    padding = 'x'*(1048576-len(canonical({'payload': first, 'padding': ''}).encode())-1)
    def envelope(payload, count):
        return {'payload': payload, 'padding': padding}
    lot = resources.prepare_lot(None, qa, envelope)
    assert lot['selected_pairs'] == 1
    assert len(canonical(envelope(lot['payload'], 1)).encode()) == 1048575
    assert len(canonical(envelope({'previous_summary': None, 'pairs': qa[:2]}, 2)).encode()) > 1048576


def test_chat_selects_maximal_byte_bounded_complete_suffix(api):
    from app.core.chat_resources import load_resources
    from app.services.chat_context import ChatContext
    from app.schemas.chat import canonical
    from test_chat_history_context_jup035 import install
    records = []
    for i in range(9):
        records.extend([(f'q{i}', 'user', f'q{i}', {}), (f'a{i}', 'assistant', f'q{i}', {})])
    document = install(api[1], records)
    for message in document['messages']:
        message['content'] = message['id']+'a'*120000
    with api[1].engine.begin() as c:
        c.execute(text("UPDATE conversations SET dialogue_history=:doc WHERE id='alice-chat'"), {'doc': json.dumps(document)})
    resources = load_resources(ROOT/'chat/v2')
    context = ChatContext(api[0], resources).build(SCOPE, body())
    selected = json.loads(context['messages'][-1]['content'].split('\n', 1)[1])['recent_pairs']
    assert [p['question_id'] for p in selected] == [f'q{i}' for i in range(1, 9)]
    assert all(p['answer'] == document['messages'][2*(i+1)+1]['content'] for i, p in enumerate(selected))
    assert len(canonical(context).encode()) <= 2097152-8192
    assert api[1].fetch_dialogue_history(**SCOPE) == document


def test_recovery_keeps_same_uncertain_job_without_second_submit(packet):
    from test_chat_summary_scheduler_jup035 import runtime, source, context, idle
    service, child = runtime(packet)
    source(packet, count=5, long=False)
    boundary = packet[3]
    boundary.mode = 'uncertain'
    async def exercise():
        try:
            child.on_completed(SCOPE, context(8192), str(uuid4()))
            await idle(child)
            assert len(boundary.calls) == 1
            original = service.repository.compactions.get(SCOPE)
            assert original['state'] == 'reconciling' and child.reserved
            replacement = type(service)(packet[0])
            try:
                await replacement.summary.recover()
                await idle(replacement.summary)
                recovered = replacement.repository.compactions.get(SCOPE)
                assert recovered['job']['job_id'] == original['job']['job_id']
                assert recovered['state'] == 'reconciling' and len(boundary.calls) == 1
                with pytest.raises(ChatError):
                    await replacement.open(SCOPE, body())
                boundary.confirmed = True
                await replacement.summary.recover()
                await idle(replacement.summary)
                assert replacement.repository.compactions.get(SCOPE)['state'] == 'failed'
                assert len(boundary.calls) == 1
            finally:
                await replacement.close()
        finally:
            await service.close()
    asyncio.run(exercise())


def test_confirmed_invalid_summary_allows_explicit_fresh_attempt_only(packet):
    from test_chat_summary_scheduler_jup035 import runtime, source, context, idle
    service, child = runtime(packet)
    source(packet, count=5, long=False)
    boundary = packet[3]
    boundary.mode = 'invalid'
    async def exercise():
        try:
            child.on_completed(SCOPE, context(8192), str(uuid4()))
            await idle(child)
            failed = service.repository.compactions.get(SCOPE)
            assert failed['state'] == 'failed' and failed['job'] is None
            assert len(boundary.calls) == 1
            await child.recover()
            await idle(child)
            assert len(boundary.calls) == 1
            boundary.mode = 'valid'
            await child.retry(SCOPE)
            await idle(child)
            assert len(boundary.calls) == 2
            assert boundary.calls[0]['job_id'] != boundary.calls[1]['job_id']
            assert service.repository.compactions.get(SCOPE) is None
        finally:
            await service.close()
    asyncio.run(exercise())
