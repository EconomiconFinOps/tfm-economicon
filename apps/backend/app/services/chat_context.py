"""Frozen, scoped model context with explicit omissions and exact billing values."""
import asyncio
import copy
import hashlib
import json
import logging
import threading
import time
import socket
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from app.db.chat_repository import ChatError
from app.db import chat_history
from app.schemas.billing import BillingSummary
from app.schemas.chat import canonical
from app.services.citations import resolve_citations, validate_context


_retrieval_correlation=ContextVar('chat_retrieval_correlation',default=(None,None))
_retrieval_logger=logging.getLogger(__name__)


def _retrieval_uuid(value):
    if type(value) is not str: return None
    try: return value if str(UUID(value))==value else None
    except ValueError: return None


@contextmanager
def retrieval_diagnostic_scope(operation_id, attempt_id):
    token=_retrieval_correlation.set((_retrieval_uuid(operation_id),_retrieval_uuid(attempt_id)))
    try: yield
    finally: _retrieval_correlation.reset(token)


def _retrieval_diagnostic(stage, failure=None):
    """Closed stage/cause only; never serialize an exception or retrieved data."""
    try:
        from app.services.embedding_provider import ProviderError, PROVIDER_ERROR_CATEGORIES
        stages={'configuration','embedding','vector_query','candidate_validation','citations'}
        stage=stage if stage in stages else 'configuration'
        code=stage+'_failed' if stage!='configuration' else 'retrieval_components_unavailable'
        if isinstance(failure,TimeoutError): code='retrieval_timeout'
        elif stage=='embedding' and isinstance(failure,ProviderError) and failure.category in PROVIDER_ERROR_CATEGORIES:
            code='embedding_'+failure.category
        elif stage=='vector_query':
            original=getattr(failure,'orig',failure)
            args=getattr(original,'args',())
            message=args[0] if args and type(args[0]) is str else None
            if message is not None and message.strip()=='invalid connection option "context"': code='driver_context_option'
            elif message=='Retrieval address unavailable.': code='trusted_peer_unavailable'
        operation,attempt=_retrieval_correlation.get()
        classes={'ProviderError','ProgrammingError','OperationalError','InterfaceError','TimeoutError','TypeError','AttributeError'}
        name=None if failure is None else 'ValueError' if isinstance(failure,ValueError) else type(failure).__name__ if type(failure).__name__ in classes else 'OtherException'
        _retrieval_logger.warning(json.dumps({'event':'chat_retrieval_diagnostic',
            'operation_id':_retrieval_uuid(operation),'attempt_id':_retrieval_uuid(attempt),
            'stage':stage,'rule_code':code,'exception_class':name},separators=(',',':'),ensure_ascii=True))
    except Exception:
        pass


def escaped(value):
    return canonical(value).replace('<','\\u003c').replace('>','\\u003e')


def verified_response_period(records):
    periods = set()
    for item in records:
        period = item['record']['period']
        start = date.fromisoformat(period['start_date'])
        end = date.fromisoformat(period['end_date'])
        if start >= end or period.get('timezone') != 'UTC':
            raise ValueError('Invalid verified period.')
        periods.add((start.isoformat(), end.isoformat()))
    if len(periods) != 1:
        return None
    start, end = next(iter(periods))
    return {'from': start, 'to': end}


def response_subscriptions(screen):
    """Scope labels come from the admitted selection, never model or tenant IDs."""
    selection = screen.get('selection') or {}
    filters = selection.get('filters') or {}
    selected = filters.get('subscriptions') or []
    if not isinstance(selected, list) or any(type(item) is not str or not item.strip() or len(item) > 256 for item in selected):
        raise ChatError(422, 'invalid_subscription_selection')
    identifiers = sorted({item.strip() for item in selected})
    if len(identifiers) > 20:
        raise ChatError(422, 'subscription_scope_limit')
    return identifiers


class ChatContext:
    def __init__(self, application, resources):
        self.app, self.resources = application, resources

    async def __call__(self, scope, payload, descriptor):
        self.resources.verify_descriptor(descriptor)
        context=await asyncio.to_thread(self.build, scope, payload)
        protocol=descriptor.get('tool_protocol')
        if protocol not in ('server-documentation-v4','mock-direct-v1'):
            raise ChatError(503,'tool_contract_mismatch')
        context['tool_protocol']=protocol
        return context

    def billing(self, scope, dataset, snapshot_id, index):
        selection = dataset['selection']
        period = selection.get('period') or selection
        if (dataset['source'] != 'billing-summary-v2'
                or dataset['data_environment'] not in ('simulated','unknown')
                or dataset['load_state'] not in ('loaded','partial','refresh_pending')):
            return {'dataset':index,'status':'unverified_screen_data'}, None, None
        filters = selection.get('filters') or {}
        if any(filters.values()) or not period.get('start_date') or not period.get('end_date'):
            return {'dataset':index,'status':'verification_unavailable'}, None, None
        start, end = date.fromisoformat(period['start_date']), date.fromisoformat(period['end_date'])
        grouping = selection.get('group_by') or 'subscription'
        tag = selection.get('tag_key') if grouping == 'tag' else None
        if start >= end or grouping == 'tag' and not tag:
            return {'dataset':index,'status':'verification_unavailable'}, None, None
        try:
            record = self.app.state.database.fetch_billing_summary(
                scope['tenant_id'],start_date=start,end_date=end,group_by=grouping,tag_key=tag)
            record = BillingSummary.model_validate(record).model_dump(mode='json')
            if (record['period'] != {'start_date':start.isoformat(),'end_date':end.isoformat(),'timezone':'UTC'}
                    or record['group_by'] != grouping or record['tag_key'] != tag):
                raise ValueError('Selection mismatch.')
        except Exception:
            return {'dataset':index,'status':'verification_unavailable'}, None, None
        claimed = sorted((item['currency'],Decimal(item['amount'])) for item in dataset['totals'])
        actual = sorted((item['currency'],Decimal(item['cost'])) for item in record['totals'])
        actual_groups = sorted((item['value'] or '',item['currency'],Decimal(item['cost']))
                               for item in record['groups'])
        claimed_groups = sorted((item['label'],item['currency'],Decimal(item['amount']))
                                for item in dataset['groups'])
        matched = (claimed == actual and claimed_groups == actual_groups
                   and dataset['counts']['records'] == sum(item['record_count'] for item in record['totals'])
                   and dataset['counts']['groups'] == len(record['groups'])
                   and dataset['completeness'].get('excluded_undated_count',0) == record['excluded_undated_count']
                   and dataset['completeness']['status'] == {
                       'available':'complete','partial':'partial','empty':'empty'}[record['data_status']])
        status = 'matched_at_verification' if matched else 'different_at_verification'
        evidence = {'id':f'cost:{snapshot_id}:{index}','kind':'cost_query',
                    'title':'Consulta de costes contrastada por el servidor','source':'billing-summary-v2',
                    'metrics':[{'name':'total_cost','value':item['cost'],'unit':item['currency']}
                               for item in record['totals']],
                    'period':record['period'],'group_by':grouping,'data_status':record['data_status']}
        return {'dataset':index,'status':status,'verified_at':datetime.now(timezone.utc).isoformat(),
                'data_status':record['data_status']}, evidence, record

    def retrieve(self, scope, question, evidence_limit=20, *, deadline=None, cancelled=None, holder=None):
        provider = getattr(self.app.state,'embedding_provider',None)
        store = getattr(self.app.state,'vector_store',None)
        if provider is None or store is None:
            _retrieval_diagnostic('configuration')
            return [], [], {'collection':'corpus','reason':'retrieval_unavailable'}
        stage='embedding'
        def current():
            if deadline is not None and (time.time()>=deadline or cancelled.is_set()):
                raise TimeoutError('Retrieval deadline.')
        try:
            from app.core.config import get_settings
            settings = get_settings()
            current()
            if deadline is not None:
                from app.services.embedding_provider import LiteLLMEmbeddingProvider
                if isinstance(provider,LiteLLMEmbeddingProvider):
                    # Clone per call: never modify the shared provider or its policy.
                    provider=copy.copy(provider)
                    original=provider._transport
                    class BoundedTransport:
                        @contextmanager
                        def open(self, req, timeout):
                            current()
                            remaining=deadline-time.time()
                            req._attempt_deadline.expires=min(req._attempt_deadline.expires,time.monotonic()+remaining)
                            with original.open(req,timeout=min(timeout,remaining)) as response:
                                holder['response']=response
                                try:
                                    current()
                                    yield response
                                finally: holder.pop('response',None)
                    provider._transport=BoundedTransport()
            vector = provider.embed(question)
            current()
            stage='vector_query'
            from app.services.vector_store import PgVectorQueryStore
            bounded={'deadline':deadline,'cancelled':cancelled} if deadline is not None and isinstance(store,PgVectorQueryStore) else {}
            candidates = store.search_chunks(scope['tenant_id'],vector,top_k=20,
                                         max_distance=settings.retrieval_max_distance,provider=provider.name,**bounded)
            stage='candidate_validation'
            validate_context(candidates,scope['tenant_id'])
            if len(candidates) > 20:
                raise ValueError('Invalid candidate count.')
            locations = {}
            for item in candidates:
                document, index = item.get('document_id'), item.get('chunk_index')
                if (not isinstance(document, str) or not document or type(index) is not int
                        or index < 0 or (document, index) in locations):
                    raise ValueError('Invalid candidate location.')
                locations[(document, index)] = item
            current()
            chunks = list(candidates[:min(settings.retrieval_top_k,evidence_limit)])
            selected = {item['chunk_id'] for item in chunks}
            omitted = set()
            # Expand only primary hits, never recursively or beyond this scoped pool.
            for seed in list(chunks):
                for index in (seed['chunk_index'] - 1, seed['chunk_index'] + 1):
                    neighbor = locations.get((seed['document_id'], index))
                    if neighbor is None or neighbor['chunk_id'] in selected:
                        continue
                    if len(chunks) >= evidence_limit:
                        omitted.add(neighbor['chunk_id'])
                        continue
                    chunks.append(neighbor)
                    selected.add(neighbor['chunk_id'])
            stage='citations'
            citations = resolve_citations([item['chunk_id'] for item in chunks],chunks,scope['tenant_id'])
            evidence = [{'id':item['chunk_id'],'kind':'corpus','title':item['title'],'source':item['source'],
                         'content':item['content'], 'provenance':{
                             'document_id':item['document_id'], 'chunk_index':item['chunk_index'],
                             'sections':item.get('section_spans',[])}} for item in chunks]
            omission = {'collection':'corpus','reason':'contiguous_context_bounded',
                        'candidate_limit':20,'omitted_neighbors':len(omitted)} if candidates else None
            return evidence, citations, omission
        except TimeoutError as failure:
            _retrieval_diagnostic(stage,failure)
            raise
        except Exception as failure:
            _retrieval_diagnostic(stage,failure)
            current()
            return [], [], {'collection':'corpus','reason':'retrieval_unavailable'}

    async def tool_extension(self, scope, context, assistant, deadline):
        from app.core.chat_resources import validate_search_call
        identifier,query=validate_search_call(assistant,context)
        if context.get('tool_protocol')!='server-documentation-v4': raise ValueError('Tool not admitted.')
        initial=context.get('authorized_evidence',[])
        if any(item['kind']!='cost_query' for item in initial): raise ValueError('Initial corpus not allowed.')
        cancelled=threading.Event();holder={}
        try:
            remaining=deadline-time.time()
            if remaining<=0: raise TimeoutError('Retrieval deadline.')
            corpus,citations,omission=[],[],None
            if assistant['action']=='search':
                corpus,citations,omission=await asyncio.wait_for(asyncio.to_thread(self.retrieve,scope,query,
                    evidence_limit=max(0,20-len(initial)),deadline=deadline,cancelled=cancelled,holder=holder),remaining)
            original=len(corpus)
            while True:
                omissions=[omission] if omission else []
                if len(corpus)<original:
                    omissions.append({'collection':'corpus','reason':'context_budget','omitted':original-len(corpus)})
                content=escaped({'evidence':corpus,'omissions':omissions})
                messages=context['messages']+[{'role':'user','content':'UNTRUSTED_RETRIEVAL_CONTEXT\n'+content}]
                try:
                    counted=self.resources.count_messages(messages,financial_metrics_allowed=context['financial_metrics_allowed'], authorized_evidence=initial+corpus)
                    result={'tool_call_id':identifier,'content':content,'variable_tokens':counted}
                    if len(content.encode())>1024*1024 or len(canonical({'claim_context':context,'tool_result':result}).encode())>2097152-8192:
                        raise ChatError(413,'tool_body_limit')
                    break
                except ChatError:
                    if not corpus: raise
                    corpus=corpus[:-1]
            ids={item['id'] for item in corpus}
            effective=copy.deepcopy(context)
            effective['authorized_evidence']=initial+corpus
            effective['source_citations']=[item for item in citations if item['evidence_id'] in ids]
            effective['manifest'].update(evidence_ids=[item['id'] for item in effective['authorized_evidence']],
                tool_result={'tool_call_id':identifier,'variable_tokens':counted,
                             'content_sha256':hashlib.sha256(content.encode()).hexdigest(),'omissions':omissions})
            if time.time()>=deadline: raise TimeoutError('Retrieval deadline.')
            return result,effective
        finally:
            cancelled.set()
            response=holder.get('response')
            if response is not None:
                raw=getattr(getattr(response,'fp',None),'raw',None)
                sock=getattr(raw,'_sock',None) or getattr(raw,'sock',None)
                if sock is not None:
                    try: sock.shutdown(socket.SHUT_RDWR)
                    except OSError: pass
                response.close()

    def dialogue(self, scope):
        document = self.app.state.database.fetch_dialogue_history(**scope)
        if document is None:
            raise ChatError(404,'not_found')
        return chat_history.latest_pairs(document)

    def memory(self, scope, payload=None):
        """Read one scoped snapshot; derive no evidence and repair no stored state."""
        from app.db.chat_repository import ChatRepository
        from app.db.chat_summary_repository import ledger, digest
        from app.services.summary_validation import validate_output
        import os
        resources = getattr(self.app.state, 'summary_resources', None)
        meta = {'used': False, 'reason': 'summary_disabled'}
        snapshot = None
        if os.getenv('SUMMARY_ENABLED', 'false') == 'true':
            meta['reason'] = 'summary_validator_unavailable'
            if resources is not None:
                contract = resources.contract
                repository = ChatRepository(self.app.state.database)
                try:
                    snapshot = repository.summaries.snapshot(scope, contract, resources)
                    meta['reason'] = 'summary_not_available'
                    if snapshot.previous_payload_used is not None:
                        _, qa, _ = ledger(snapshot.document)
                        sources = {pair[role + '_ref']: pair[role] for pair in qa[:snapshot.covered_pairs]
                            for role in ['question', 'answer']}
                        state = chat_history.loads(snapshot.parent_raw)
                        artifact = state['artifact']
                        origin = resources.resources_for_contract(artifact['contract'])
                        output = validate_output(snapshot.previous_payload_used, sources, origin)
                        meta = {'used': True, 'reason': None, 'payload': output,
                            'payload_sha256': digest(output), 'artifact_id': artifact['artifact_id'],
                            'artifact_sha256': digest(artifact), 'summary_version': artifact['contract']['prompt_version']}
                        retry = (payload or {}).get('retry_of_operation_id')
                        if retry:
                            operation = repository.get(scope, retry)
                            if any(ref['question_id'] == operation['question_message_id'] for ref in artifact['source_refs']):
                                meta = {'used': False, 'reason': 'retry_covered'}
                        # build measures the full escaped prefix with all essentials,
                        # schema, chat output reserve and margin; never truncate it.
                except ChatError as error:
                    if error.status == 404:
                        raise
                    meta = {'used': False, 'reason': 'summary_unavailable'}
                except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
                    meta = {'used': False, 'reason': 'summary_invalid'}
        if snapshot is None:
            pairs, excluded = self.dialogue(scope)
        else:
            pairs, excluded = chat_history.latest_pairs(snapshot.document)
        processed = snapshot.covered_pairs if snapshot is not None and meta['used'] else 0
        public = {'v': 2, 'scope': dict(scope), 'available': meta['used'], 'reason': meta['reason'],
            'coverage': {'processed_pairs': processed, 'pending_pairs': max(0, len(pairs) - 4 - processed),
                'recent_reserved': min(4, len(pairs))},
            'limitations': list(meta['payload']['limitations']) if meta['used'] else [],
            'artifact_id': meta.get('artifact_id')}
        return pairs, excluded, meta, public

    def recent_pairs(self, scope):
        pairs, excluded = self.dialogue(scope)
        return pairs[-4:], max(0,len(pairs)-4)

    def build(self, scope, payload):
        screen = copy.deepcopy(payload['screen_context'])
        subscriptions = response_subscriptions(screen)
        screen_hash = hashlib.sha256(canonical(screen).encode()).hexdigest()
        snapshot_id = screen_hash[:24]
        projection = copy.deepcopy(screen)
        fragments = []
        for index, dataset in enumerate(projection['datasets']):
            for collection in ['groups','series']:
                for item in dataset[collection]:
                    fragments.append((index,collection,item))
                dataset[collection] = []
        verification, authorized, records = [], [], []
        for index, dataset in enumerate(screen['datasets']):
            checked, evidence, record = self.billing(scope,dataset,snapshot_id,index)
            verification.append(checked)
            if evidence is not None:
                authorized.append(evidence)
                records.append({'dataset':index,'record':record})
        # Only billing() can create this authority, after scoped query and parsing.
        financial_metrics_allowed = any(item['metrics'] for item in authorized)
        citations, retrieval_omission = [], None
        if len(authorized) > 20:
            raise ChatError(413,'essential_evidence_limit')
        pairs, excluded, summary, public_memory = self.memory(scope, payload)
        older = public_memory['coverage']['processed_pairs'] if summary['used'] else 0
        recent = pairs[older:]
        base_omissions = []
        if older:
            base_omissions.append({'collection':'dialogue','omitted_pairs':older,'reason':'summary_not_available'})
        if excluded:
            base_omissions.append({'collection':'dialogue_unpaired','omitted_messages':len(excluded),
                'reasons':sorted({entry['reason'] for entry in excluded}),
                'message_ids':[entry['message_id'] for entry in excluded]})
        if retrieval_omission:
            base_omissions.append(retrieval_omission)

        def assemble(retained, pairs, used_summary=None):
            selected = copy.deepcopy(projection)
            for index, collection, item in fragments[:retained]:
                selected['datasets'][index][collection].append(item)
            omissions = copy.deepcopy(base_omissions)
            if used_summary is not None and older:
                omissions = [item for item in omissions if item.get('reason') != 'summary_not_available']
                omissions.append({'collection':'dialogue','reason':'summary_is_lossy','older_pairs':older})
            if len(pairs) < len(recent):
                omissions.append({'collection':'recent_pairs','omitted_pairs':len(recent)-len(pairs)})
            for index, original in enumerate(screen['datasets']):
                for collection in ['groups','series']:
                    missing = len(original[collection])-len(selected['datasets'][index][collection])
                    if missing:
                        omissions.append({'dataset':index,'collection':collection,'omitted':missing})
            current = {'question':payload['content'],'recent_pairs':pairs,'screen_projection':selected,
                       'omissions':omissions,'verification':verification,'evidence':authorized}
            messages = [{'role':'system','content':self.resources.system},
                        {'role':'user','content':'UNTRUSTED_CURRENT_CONTEXT\n'+escaped(current)}]
            if used_summary is not None:
                messages.insert(1, {'role':'user','content':'UNTRUSTED_DIALOGUE_SUMMARY\n'+escaped(used_summary)})
            return messages,current

        # Essentials must fit before considering optional history or details.
        used_payload = summary.get('payload') if summary['used'] else None
        def measure(messages,current):
            counted=self.resources.count_messages(messages, financial_metrics_allowed=financial_metrics_allowed, authorized_evidence=authorized)
            manifest=self.resources.metadata(counted,messages)
            manifest.update(summary=summary,essential_tokens=0,screen_snapshot_sha256=screen_hash,
                omissions=current['omissions'],evidence_ids=[item['id'] for item in authorized])
            probe={'prompt_version':self.resources.prompt_version,'messages':messages,'manifest':manifest,
                'authorized_evidence':authorized,'source_citations':citations,'verification_records':records,
                'response_period':verified_response_period(records), 'response_subscriptions':subscriptions,
                'financial_metrics_allowed':financial_metrics_allowed,'tool_protocol':'server-documentation-v4'}
            # The actual private claim is checked again by ChatTransport. Reserve
            # its bounded controls and the subsequently attached revision fence.
            if len(canonical(probe).encode())>2097152-8192:
                raise ChatError(413,'context_body_limit')
            return counted
        messages, current = assemble(0,[],used_payload)
        essential_tokens = measure(messages,current)
        retained_recent = list(recent)
        while True:
            messages,current = assemble(0,retained_recent,used_payload)
            try:
                measure(messages,current)
                break
            except ChatError:
                if not retained_recent:
                    raise
                retained_recent.pop(0)
        low, high = 0,len(fragments)
        while low < high:
            middle = (low+high+1)//2
            candidate,trial = assemble(middle,retained_recent,used_payload)
            try:
                measure(candidate,trial)
                low = middle
            except ChatError:
                high = middle-1
        messages,current = assemble(low,retained_recent,used_payload)
        counted = self.resources.count_messages(messages, financial_metrics_allowed=financial_metrics_allowed, authorized_evidence=authorized)
        manifest = self.resources.metadata(counted,messages)
        manifest.update(summary=summary,essential_tokens=essential_tokens,screen_snapshot_sha256=screen_hash,omissions=current['omissions'],
                        evidence_ids=[item['id'] for item in authorized])
        context = {'prompt_version':self.resources.prompt_version,'messages':messages,'manifest':manifest,
                   'authorized_evidence':authorized,'source_citations':citations,'verification_records':records,
                   'response_period':verified_response_period(records), 'response_subscriptions':subscriptions,
                   'financial_metrics_allowed':financial_metrics_allowed,'tool_protocol':'server-documentation-v4'}
        # Leave space for authenticated claim controls within the private2MiB body.
        if len(canonical(context).encode()) > 2097152-8192:
            raise ChatError(413,'context_body_limit')
        return context
