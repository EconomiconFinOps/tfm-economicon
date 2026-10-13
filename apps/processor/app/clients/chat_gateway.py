"""Private bounded plan and reviewed stream under one chat attempt deadline.

No ingestion setting is changed. Backend alone decides whether another attempt
may run. This adapter never retries, redirects, repairs JSON or falls back.
"""
import asyncio
import codecs
import errno
import json
import hashlib
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import UUID
from pydantic import ValidationError
from functools import partial
from http.client import HTTPConnection,HTTPSConnection
import socket
import select
import ssl
import threading
import time
from urllib import error,request

from app.agents.schemas import chat_provider_schema, assemble_chat_response
from app.clients.chat_dns import resolve
from app.core.context_budget import budget
from app.clients.chat_stream_parser import SegmentAnswerJSON,SSEFrames,complete_json
from app.clients.litellm import LiteLLMClient,_AttemptDeadline,_DeadlineHTTPConnection,_DeadlineHTTPSConnection,_RejectRedirectHandler,_transport_failure,_usage_metadata


_diagnostic_context = ContextVar('chat_diagnostic_context', default=None)
_diagnostic_logger = logging.getLogger(__name__)
_NATIVE_RULES = frozenset({
    'native_tool_index', 'native_metadata_type', 'native_metadata_conflict',
    'native_function_shape', 'native_fragment_type', 'native_tool_limit',
    'native_tool_count', 'native_final_invalid', 'native_multiple_calls',
})


class _NativeEnvelopeError(ValueError):
    def __init__(self, rule_code):
        self.rule_code = rule_code if rule_code in _NATIVE_RULES else 'native_final_invalid'
        super().__init__('Invalid native envelope.')


_MODEL_RULES = {
    'Value error, period.from must be before period.to': 'period_order',
    'Value error, estimated_savings and currency must either both be set or both be null': 'savings_currency_pair',
    'Value error, evidence ids must be unique': 'evidence_id_duplicates',
    'Value error, non-actionable responses cannot contain metrics or recommendations': 'non_actionable_with_metrics_or_recommendations',
    'Value error, metrics and recommendations must reference known evidence': 'unknown_evidence_reference',
    'Value error, ok and partial responses require evidence': 'actionable_requires_evidence',
}
_ERROR_TYPES = frozenset({
    'value_error', 'missing', 'extra_forbidden', 'literal_error', 'enum',
    'string_type', 'string_too_long', 'string_too_short', 'string_pattern_mismatch',
    'list_type', 'too_long', 'too_short', 'dict_type', 'model_type',
    'date_type', 'date_parsing', 'date_from_datetime_parsing', 'date_from_datetime_inexact',
    'bool_type', 'int_type', 'float_type', 'finite_number', 'json_invalid',
})
_ERROR_FIELDS = frozenset({
    'schema_version', 'status', 'answer', 'scope', 'cloud', 'data_environment',
    'subscription_ids', 'period', 'from', 'to', 'from_date', 'to_date', 'evidence',
    'id', 'kind', 'title', 'source', 'metrics', 'name', 'value', 'unit',
    'evidence_ids', 'recommendations', 'category', 'action', 'rationale',
    'estimated_savings', 'currency', 'confidence', 'risk', 'requires_human_approval',
    'assumptions', 'limitations', 'next_actions',
})


def _diagnostic_uuid(value):
    if type(value) is not str:
        return None
    try:
        return value if str(UUID(value)) == value else None
    except (ValueError, AttributeError):
        return None


@contextmanager
def diagnostic_scope(operation_id, attempt_id):
    """Keep authenticated correlation local to the consuming stream/task."""
    token = _diagnostic_context.set((_diagnostic_uuid(operation_id), _diagnostic_uuid(attempt_id)))
    try:
        yield
    finally:
        _diagnostic_context.reset(token)


def _record_diagnostic(stage, failure, request_hash, finish, *, status=None, category=None):
    """A bounded structural event; never serialize exceptions or candidate data."""
    try:
        from app.core.chat_calculations import CalculationError
        correlation = _diagnostic_context.get() or (None, None)
        classes = {ValidationError: 'ValidationError', ValueError: 'ValueError',
                   json.JSONDecodeError: 'JSONDecodeError', UnicodeDecodeError: 'UnicodeDecodeError',
                   TypeError: 'TypeError'}
        errors = []
        if isinstance(failure, ValidationError):
            for item in failure.errors(include_input=False, include_context=False, include_url=False)[:3]:
                kind = item['type'] if item['type'] in _ERROR_TYPES else 'other_error'
                loc = []
                for part in item['loc'][:6]:
                    if type(part) is int and 0 <= part <= 1000000:
                        loc.append(part)
                    elif type(part) is str and part in _ERROR_FIELDS:
                        loc.append(part)
                    else:
                        loc.append('unknown')
                # Only six complete, fixed Pydantic messages are examined in RAM.
                # Unknown text is never retained, hashed, or matched partially.
                rule = _MODEL_RULES.get(item['msg'], 'unclassified_model_rule') if kind == 'value_error' else None
                errors.append({'type': kind, 'loc': loc, 'rule_code': rule})
        observed_finish = finish if type(finish) is str and finish in {
            'stop', 'length', 'content_filter', 'tool_calls', 'function_call'} else None if finish is None else 'other'
        event = {
            'event': 'chat_gateway_diagnostic',
            'operation_id': _diagnostic_uuid(correlation[0]),
            'attempt_id': _diagnostic_uuid(correlation[1]),
            'request_sha256': request_hash,
            'stage': stage if stage in {'request', 'transport', 'envelope', 'provisional_answer',
                                       'finish', 'candidate_json', 'model_validation'} else 'envelope',
            'exception_class': None if failure is None else 'ValueError' if isinstance(failure, _NativeEnvelopeError) else classes.get(type(failure), 'OtherException'),
            'errors': errors,
            'finish_reason': observed_finish,
            'http_status': status if type(status) is int and 100 <= status <= 599 else None,
            'category': category if category in {'timeout', 'eof', 'transport', 'request',
                                                 'incomplete', 'invalid_response'} else None,
        }
        if isinstance(failure, _NativeEnvelopeError):
            event['rule_code'] = failure.rule_code
        if isinstance(failure, CalculationError):
            event['exception_class'] = 'CalculationError'
            event['rule_code'] = failure.rule_code
        assembly_rules = {
            'Citation passage is not grounded.':'citation_passage_not_grounded',
            'Invalid evidence collection.':'invalid_evidence_collection',
            'Invalid evidence record.':'invalid_evidence_record',
            'Invalid recommendation collection.':'invalid_recommendation_collection',
            'Invalid recommendation citations.':'invalid_recommendation_citations',
            'Invalid recommendation citation.':'invalid_recommendation_citation',
            'Recommendation citation shape invalid.':'recommendation_citation_shape',
            'Recommendation citation source unknown.':'recommendation_citation_unknown',
            'Recommendation citation duplicated.':'recommendation_citation_duplicate',
            'Recommendation citation metadata mismatch.':'recommendation_citation_metadata',
            'Recommendation citations must be explicit records.':'recommendation_explicit_citations_required',
            'Invalid response scope.':'invalid_response_scope',
            'Period is server-owned.':'server_owned_period',
            'Subscriptions are server-owned.':'server_owned_subscriptions',
            'Invalid calculation response.':'invalid_calculation_response',
            'Invalid calculation collection.':'invalid_calculation_collection',
            'Invalid short prose item.':'invalid_short_prose_item',
            'Invalid response segment.':'invalid_response_segment',
            'Invalid segment text.':'invalid_segment_text',
            'Invalid segment reference.':'invalid_segment_reference',
            'Invalid segment collection.':'invalid_segment_collection',
            'Rendered text limit.':'rendered_text_limit',
            'Empty rendered text.':'empty_rendered_text',
            'Response segment limit.':'response_segment_limit',
            'Incomplete segmented answer.':'incomplete_segmented_answer',
            'Stream candidate mismatch.':'stream_candidate_mismatch',
            'Expression input unavailable.':'expression_input_unavailable',
            'Expression input type.':'expression_input_type',
            'Expression source magnitude.':'expression_source_magnitude',
            'Expression operation limit.':'expression_operation_limit',
            'Expression catalog changed.':'expression_catalog_changed',
            'Expression shape or depth.':'expression_shape_or_depth',
            'Expression operation shape.':'expression_operation_shape',
            'Rendered expression requires an operation.':'expression_operation_required',
            'Unknown source quantity.':'expression_unknown_source_quantity',
            'Incompatible expression units.':'expression_incompatible_units',
            'Expression magnitude or unit limit.':'expression_magnitude_or_unit_limit',
            'Comparison expression shape.':'expression_comparison_shape',
            'Expression precision limit.':'expression_precision_limit',
            'Classification shape.':'classification_shape',
            'Unknown documentary interval rule.':'classification_unknown_rule',
            'Documentary KPI value mismatch.':'classification_kpi_mismatch',
            'Documentary interval unit mismatch.':'classification_unit_mismatch',
            'Ambiguous documentary interval.':'classification_ambiguous_interval',
            'Unverified documentary classification prose.':'classification_unverified_prose',
            'Invalid classified answer.':'classified_answer_invalid',
            'Classified evidence is server-owned.':'classified_evidence_server_owned',
            'Derived documentary source unavailable.':'derived_documentary_source_unavailable',
            'Derived documentary evidence mismatch.':'derived_documentary_evidence_mismatch',
            'Explicit classification requires typed answer.':'explicit_classification_requires_typed_answer',
            'Explicit boolean rule requires typed answer.':'explicit_boolean_requires_typed_answer',
            'Boolean rule answer shape.':'boolean_answer_shape',
            'Boolean rule not grounded.':'boolean_rule_not_grounded',
            'Boolean rule unit mismatch.':'boolean_rule_unit_mismatch',
            'User rule status requires no financial authority.':'boolean_user_authority_status',
            'Invalid neutral request.':'invalid_neutral_request',
            'Invalid user scenario.':'invalid_user_scenario',
            'User scenario contains documentary operands.':'scenario_documentary_operands',
            'Invalid neutral auxiliary fields.':'invalid_neutral_auxiliary_fields',
            'Neutral request status is server-owned.':'neutral_request_server_owned_status',
            'User scenario status requires no financial authority.':'scenario_status_authority',
            'Narrative requires selected evidence.':'narrative_evidence_required',
            'Invalid response basis.':'invalid_response_basis',
            'Terminal response cannot override basis.':'terminal_basis_override',
            'Response basis status mismatch.':'response_basis_status',
            'Response basis cannot grant authority.':'response_basis_authority',
            'Response basis requires useful next action.':'response_basis_next_action',
            'Response basis contains documentary operands.':'response_basis_documentary_operands',
            'Invalid classified calculation.':'classified_calculation_invalid',
            'Invalid classified auxiliary fields.':'classified_auxiliary_invalid',
            'Classification requires typed answer.':'classification_requires_typed_answer',
            'Documentary calculation citation missing.':'documentary_calculation_citation_missing',
            'Invalid canonical subscriptions.':'invalid_canonical_subscriptions',
            'Invalid authorized evidence.':'invalid_authorized_evidence',
        }
        if type(failure) is ValueError and failure.args and type(failure.args[0]) is str and failure.args[0] in assembly_rules:
            event['rule_code'] = assembly_rules[failure.args[0]]
        encoded = json.dumps(event, ensure_ascii=True, separators=(',', ':'), allow_nan=False)
        if len(encoded.encode()) <= 2048:
            _diagnostic_logger.warning(encoded)
    except Exception:
        # Logging is observational: failures cannot change the original stream.
        pass


def interrupt(response):
    try:
        raw=getattr(getattr(response,'fp',None),'raw',None)
        sock=getattr(raw,'sock',None) or getattr(raw,'_sock',None)
        if sock is not None: sock.shutdown(socket.SHUT_RDWR)
    except (OSError,AttributeError): pass


class _ChatConnect:
    def __init__(self,*args,cancelled=None,**kwargs):
        self.cancelled=cancelled if cancelled is not None else threading.Event()
        self.connect_until=None
        super().__init__(*args,**kwargs)

    def _connect_remaining(self):
        if self.cancelled.is_set(): raise TimeoutError('Gateway connection cancelled')
        remaining=min(self.connect_until-time.monotonic(),self.deadline.remaining())
        if remaining<=0: raise TimeoutError('Gateway connection deadline exceeded')
        return remaining

    def _connect_socket(self,address,timeout,source_address):
        self.connect_until=time.monotonic()+min(5,self.deadline.remaining())
        addresses=resolve(address[0],address[1],self._connect_remaining,self.cancelled)
        last=OSError('No gateway address.')
        for family,kind,protocol,_,location in addresses:
            self._connect_remaining()
            sock=socket.socket(family,kind,protocol)
            try:
                sock.setblocking(False)
                if source_address: sock.bind(source_address)
                status=sock.connect_ex(location)
                pending={errno.EINPROGRESS,errno.EWOULDBLOCK,errno.EALREADY,errno.EINTR,10035}
                if status not in pending and status not in (0,errno.EISCONN):
                    raise OSError(status,'Gateway connection failed')
                while status in pending:
                    budget=self._connect_remaining()
                    _,writable,exceptional=select.select([], [sock], [sock], min(.05,budget))
                    self._connect_remaining()
                    if writable or exceptional:
                        status=sock.getsockopt(socket.SOL_SOCKET,socket.SO_ERROR)
                        if status: raise OSError(status,'Gateway connection failed')
                self._connect_remaining()
                sock.settimeout(self.deadline.remaining())
                return sock
            except TimeoutError:
                sock.close();raise
            except OSError as failure:
                last=failure;sock.close()
            except BaseException:
                sock.close();raise
        self._connect_remaining()
        raise last


class _ChatHTTPConnection(_ChatConnect,_DeadlineHTTPConnection):
    pass


class _ChatHTTPSConnection(_ChatConnect,_DeadlineHTTPSConnection):
    def connect(self):
        plain=None
        try:
            HTTPConnection.connect(self)
            plain=self.sock
            self._connect_remaining()
            plain.setblocking(False)
            self.sock=self._context.wrap_socket(plain,server_hostname=self._tunnel_host or self.host,do_handshake_on_connect=False)
            while True:
                budget=self._connect_remaining()
                try:
                    self.sock.do_handshake()
                    break
                except ssl.SSLWantReadError:
                    select.select([self.sock],[],[],min(.05,budget))
                except ssl.SSLWantWriteError:
                    select.select([],[self.sock],[],min(.05,budget))
            self._connect_remaining()
            self.sock.settimeout(self.deadline.remaining())
        except BaseException:
            if self.sock is not None: self.sock.close()
            if plain is not None and plain is not self.sock: plain.close()
            self.sock=None
            raise


class _ChatHandler:
    def do_open(self,http_class,req,**kwargs):
        connection=_ChatHTTPSConnection if http_class is HTTPSConnection else _ChatHTTPConnection
        return super().do_open(partial(connection,deadline=req._attempt_deadline,cancelled=req._chat_cancelled),req,**kwargs)


class _ChatHTTPHandler(_ChatHandler,request.HTTPHandler):
    pass


class _ChatHTTPSHandler(_ChatHandler,request.HTTPSHandler):
    pass


class ChatGateway:
    requires_tool_result=True
    def __init__(self,settings):
        if settings.llm_model!='economicon-chat' or settings.litellm_api_key is None:
            raise ValueError('Chat gateway configuration.')
        self.settings=settings
        self.resources=None
        self.client=LiteLLMClient(settings)
        self.client.transport=request.build_opener(request.ProxyHandler({}),_RejectRedirectHandler(),_ChatHTTPHandler(),_ChatHTTPSHandler())

    def _records(self,context,deadline,holder,cancelled,tool_choice=None):
        from app.core.chat_review import DRAFT_TOKENS,FINAL_TOKENS,draft_schema,validate_draft
        phase=context.get('_review_phase','final')
        holder['usage']=None
        finish=None;request_hash=None;emitted=False;stage='request'
        def diagnostic(at,failure=None,**metadata):
            nonlocal emitted
            if emitted or cancelled.is_set(): return
            emitted=True
            _record_diagnostic(at,failure,request_hash,finish,**metadata)
        remaining=deadline-time.time()-5
        if remaining<=0:
            diagnostic('transport',category='timeout')
            yield {'type':'error','category':'timeout'};return
        try:
            payload={'model':'economicon-chat','messages':context['messages'],'stream':True,
                'stream_options':{'include_usage':True},'max_tokens':DRAFT_TOKENS if phase=='draft' else FINAL_TOKENS,'num_retries':0,
                'timeout':remaining,'stream_timeout':remaining,'reasoning':{'effort':'high','exclude':True},
                'provider':{'order':['deepinfra/fp4'],'allow_fallbacks':False,'require_parameters':True}}
            from app.core.chat_expressions import context_quantities
            source_quantities=context_quantities(context)
            payload['response_format']={'type':'json_schema','json_schema':{
                'name':'FinOpsResponse','strict':True,
                'schema':chat_provider_schema(
                    financial_metrics_allowed=context.get('financial_metrics_allowed'),
                    authorized_evidence=context.get('authorized_evidence', []), quantities=source_quantities)}}
            if phase=='draft':
                payload['response_format']['json_schema']={'name':'PrivateAnswerPlan','strict':True,
                    'schema':draft_schema(context.get('authorized_evidence',[]))}
            if self.resources is not None:
                self.resources.check_messages(payload['messages'],payload['response_format']['json_schema']['schema'])
            req=request.Request(self.client.base_url+'/chat/completions',data=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode(),
                headers={'Authorization':'Bearer '+self.settings.litellm_api_key.get_secret_value(),'Content-Type':'application/json'},method='POST')
            request_hash=hashlib.sha256(req.data).hexdigest()
        except Exception as failure:
            diagnostic('request',failure)
            raise
        req._attempt_deadline=_AttemptDeadline(max(.001,deadline-time.time()-5))
        req._chat_cancelled=cancelled
        request_metadata={'phase':phase,'request_sha256':request_hash,'output_token_limit':payload['max_tokens']}
        if self.resources is not None:
            from app.core.chat_resources import canonical
            request_metadata['input_tokens']=self.resources.count(canonical(payload['messages']).decode())+self.resources.count(canonical(payload['response_format']['json_schema']['schema']).decode())
        frames,answer=SSEFrames(),SegmentAnswerJSON([], quantities=source_quantities)
        decoder=codecs.getincrementaldecoder('utf-8-sig')('strict')
        candidate=[];candidate_bytes=0;usage=None
        try:
            stage='transport'
            holder['attempted_legs']=holder.get('attempted_legs',0)+1
            holder.setdefault('requests',[]).append(request_metadata)
            with self.client.transport.open(req,timeout=min(5,remaining)) as response:
                holder['response']=response
                if cancelled.is_set(): return
                stage='envelope'
                if not response.headers.get('Content-Type','').startswith('text/event-stream'): raise ValueError('Gateway stream format.')
                while not cancelled.is_set():
                    req._attempt_deadline.remaining()
                    chunk=response.read1(8192)
                    req._attempt_deadline.remaining()
                    stage='envelope'
                    if not chunk:
                        decoder.decode(b'',final=True)
                        diagnostic('envelope',category='eof')
                        yield {'type':'error','category':'eof'};return
                    for data in frames.feed(decoder.decode(chunk)):
                        stage='envelope'
                        if data=='[DONE]':
                            stage='finish'
                            if finish not in ('stop','length'): raise ValueError('Gateway finish reason.')
                            raw=''.join(candidate)
                            try:
                                stage='candidate_json'
                                parsed=complete_json(raw)
                                if phase=='draft':
                                    if finish!='stop':raise ValueError('Private draft truncated.')
                                    validate_draft(parsed,context.get('authorized_evidence',[]))
                                    yield {'type':'draft','plan':parsed,'usage':usage}
                                    return
                                stage='model_validation'
                                from app.core.chat_segments import render_response
                                parsed=render_response(parsed,[],quantities=source_quantities)
                                result=assemble_chat_response(parsed,context.get('response_period'), context.get('response_subscriptions', []), authorized_evidence=context.get('authorized_evidence', []))
                            except Exception as failure:
                                diagnostic(stage,failure,category='incomplete' if finish=='length' else 'invalid_response')
                                if finish=='length':
                                    yield {'type':'error','status':502,'category':'incomplete'}
                                    return
                                raise
                            if answer.finish()!=result['answer']:raise ValueError('Stream candidate mismatch.')
                            yield {'type':'candidate','result':result,'finish_reason':finish,'usage':usage}
                            return
                        event=complete_json(data)
                        if not isinstance(event,dict): raise ValueError('Gateway event.')
                        if isinstance(event.get('usage'),dict):
                            usage=_usage_metadata(event,response.headers.get('x-litellm-response-cost'))
                            holder['usage']=usage
                        choices=event.get('choices',[])
                        if not isinstance(choices,list) or len(choices)>1: raise ValueError('Gateway choices.')
                        for choice in choices:
                            if not isinstance(choice,dict) or choice.get('index',0)!=0: raise ValueError('Gateway choice.')
                            if choice.get('finish_reason') is not None: finish=choice['finish_reason']
                            delta=choice.get('delta',{})
                            if not isinstance(delta,dict): raise ValueError('Gateway delta.')
                            if delta.get('tool_calls') is not None or delta.get('function_call') is not None:
                                raise _NativeEnvelopeError('native_final_invalid')
                            fragment=delta.get('content')
                            if fragment is None: continue
                            if not isinstance(fragment,str): raise ValueError('Gateway content.')
                            candidate_bytes+=len(fragment.encode())
                            if candidate_bytes>1024*1024: raise ValueError('Candidate limit.')
                            candidate.append(fragment)
                            stage='provisional_answer'
                            provisional=answer.feed(fragment) if phase!='draft' else ''
                            # Escape-aware decoding completes surrogate pairs;
                            # chunking preserves codepoints and the8KiB wire bound.
                            yield from text_deltas(provisional)
        except error.HTTPError as failure:
            status=failure.code
            retry_after=failure.headers.get('Retry-After')
            if retry_after is not None and (len(retry_after)>128 or any(ord(ch)<32 for ch in retry_after)): retry_after=None
            failure.close()
            diagnostic('transport',failure,status=status)
            yield {'type':'error','status':status,'retry_after':retry_after}
        except error.URLError as failure:
            category,retryable=_transport_failure(failure.reason)
            diagnostic('transport',failure,category='transport' if retryable else 'request')
            yield {'type':'error','category':'transport' if retryable else 'request','status':None}
        except (TimeoutError,OSError) as failure:
            diagnostic('transport',failure,category='transport')
            yield {'type':'error','category':'transport'}
        except Exception as failure:
            diagnostic(stage,failure,category='invalid_response')
            yield {'type':'error','category':'invalid_response','status':422}
        finally:
            holder.pop('response',None)

    async def __call__(self,context,deadline,*,tool_result=None):
        holder={};cancelled=threading.Event()
        from app.core.chat_review import phase_messages,review_usage
        usages=[];attempted=0
        try:
            protocol=context.get('tool_protocol')
            if protocol not in (None,'server-documentation-v4'):
                yield {'type':'error','status':422,'category':'invalid_response'};return
            if protocol=='server-documentation-v4':
                if tool_result is None:
                    yield {'type':'error','status':422,'category':'invalid_response'};return
                from app.core.chat_resources import retrieval_control,continuation_messages
                control=retrieval_control(context)
                yield {'type':'tool_call','assistant':control}
                remaining=deadline-time.time()-5
                if remaining<=0:raise TimeoutError()
                result=await asyncio.wait_for(tool_result(control),remaining)
                messages=continuation_messages(context,control,result)
                context={**context,'messages':messages,'authorized_evidence':
                    context.get('authorized_evidence',[])+json.loads(result['content'])['evidence']}
            if cancelled.is_set() or time.time()>=deadline-5:raise TimeoutError()
            if self.resources is None:raise ValueError('Review token resources unavailable.')
            draft_context={**context,'_review_phase':'draft','messages':phase_messages(context['messages'],'draft')}
            iterator=self._records(draft_context,deadline,holder,cancelled)
            draft=None
            while True:
                record=await asyncio.to_thread(next,iterator,None)
                attempted=holder.get('attempted_legs',0)
                if record is None:break
                if record.get('type')=='draft':
                    draft=record['plan'];usages.append(record.get('usage'));break
                if record.get('type')=='error':
                    if attempted>len(usages):usages.append(holder.get('usage'))
                    await asyncio.to_thread(iterator.close)
                    yield {**record,'usage_report':review_usage(usages,attempted) if attempted else None};return
                raise ValueError('Unexpected draft record.')
            await asyncio.to_thread(iterator.close)
            if draft is None:raise ValueError('Missing private draft.')
            if cancelled.is_set() or time.time()>=deadline-5:raise TimeoutError()
            final_context={**context,'_review_phase':'final','messages':phase_messages(context['messages'],'final',draft)}
            iterator=self._records(final_context,deadline,holder,cancelled)
            while True:
                record=await asyncio.to_thread(next,iterator,None)
                attempted=holder.get('attempted_legs',0)
                if record is None:return
                if record.get('type') in ('candidate','error'):
                    if attempted>len(usages):usages.append(record.get('usage',holder.get('usage')))
                    report=review_usage(usages,attempted) if attempted else None
                    record={**record,'usage_report':report,'usage':report['observed'] if report and report['complete'] else None}
                    await asyncio.to_thread(iterator.close)
                    yield record
                    return
                yield record
        except TimeoutError:
            attempted=holder.get('attempted_legs',0)
            yield {'type':'error','category':'timeout','usage_report':review_usage(usages+[holder.get('usage')] if len(usages)<attempted else usages,attempted) if attempted else None}
        finally:
            cancelled.set()
            response=holder.get('response')
            if response is not None:interrupt(response)
            try:
                attempted=holder.get('attempted_legs',0)
                if attempted:
                    report=review_usage(usages+[holder.get('usage')] if len(usages)<attempted else usages,attempted)
                    operation_id,attempt_id=_diagnostic_context.get() or (None,None)
                    _diagnostic_logger.info('chat_review_usage %s',json.dumps({'event':'chat_review_usage','operation_id':operation_id,'attempt_id':attempt_id,'requests':holder.get('requests',[]),**report}))
            except Exception:
                pass


def text_deltas(text):
    piece=[];size=0
    for char in text:
        width=len(char.encode())
        if size+width>8192:
            yield {'type':'delta','text':''.join(piece)};piece=[];size=0
        piece.append(char);size+=width
    if piece: yield {'type':'delta','text':''.join(piece)}


def combined_usage(first,second):
    """Sum reported legs only; missing counters/costs are never estimated."""
    from decimal import Decimal
    if not isinstance(first,dict) or not isinstance(second,dict): return None
    result={}
    for key in ('prompt_tokens','completion_tokens','total_tokens'):
        if type(first.get(key)) is int and type(second.get(key)) is int:
            result[key]=first[key]+second[key]
    if all(item.get('cost_usd') is not None for item in (first,second)):
        values=[Decimal(str(item['cost_usd'])) for item in (first,second)]
        if all(value.is_finite() and value>=0 for value in values):
            result['cost_usd']=format(sum(values),'f')
    return result or None


def configured_gateway():
    from app.core.config import get_settings
    settings=get_settings()
    if settings.llm_provider=='mock':
        from app.clients.mock_chat import MockChatGateway,require_local_mock
        require_local_mock(settings)
        return MockChatGateway()
    if settings.llm_provider!='litellm': return None
    return ChatGateway(settings)
