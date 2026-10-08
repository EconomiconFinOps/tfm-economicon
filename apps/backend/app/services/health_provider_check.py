"""Single-instance admission and conservative accounting for provider diagnostics.

Real transport/configuration is assembled separately. This class never discovers
prices, infers available credit or releases a possibly charged reservation.
"""
from collections import OrderedDict, deque
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, localcontext
import re
import threading
import time
from uuid import uuid4


GUARANTEES = (
    "price_verified", "routing_verified", "effective_cap_verified",
    "exclusive_accounting_verified", "enforceable_cost_ceiling_verified",
)
ZERO = Decimal("0")


def amount(value):
    if isinstance(value, bool) or isinstance(value, float) or value is None:
        raise ValueError("Uncertified amount")
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Uncertified amount") from None
    if (not result.is_finite() or result < ZERO or len(result.as_tuple().digits) > 40
            or result.as_tuple().exponent < -18 or result.adjusted() > 12):
        raise ValueError("Uncertified amount")
    return result


def reported_model(value):
    # Bounded information, never a remote identity gate.
    return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,255}", value) else None


def reported_cost(value):
    if value is None:
        return None, "unavailable"
    try:
        return format(amount(value), "f"), "gateway_reported"
    except ValueError:
        return None, "invalid"


class ProviderDiagnosticFailure(Exception):
    """Only a closed failure reason crosses the isolated transport boundary."""
    def __init__(self, reason):
        self.reason = reason if reason in {"authentication", "connection", "upstream_error"} else "upstream_error"
        super().__init__(self.reason)


def utc_now():
    return datetime.now(timezone.utc)


class HealthProviderCheck:
    """Global per-credential gate; one object per admitted backend instance.

    transport is a trusted server-side callable with a hard deadline. Injected
    deterministic transports exercise admission without network access. Runtime
    transport MUST verify the dated policy again immediately before sending.
    """
    def __init__(self, *, policy, transport, clock=utc_now):
        self.policy = deepcopy(policy)
        self.transport = transport
        self.clock = clock
        self._lock = threading.Lock()
        self._active = False
        self._history = deque()
        self._actions = OrderedDict()
        self._execution_calls = policy.get("known_execution_calls", 0)
        self._spent = ZERO
        self._pending = ZERO
        self._uncertain = ZERO
        self._last = None
        self._verified = None
        self._verified_id = None
        self._accounting_valid = True
        try:
            self._spent = amount(policy.get("known_spend_usd"))
            self._uncertain = amount(policy.get("uncertain_usd"))
            self._pending = amount(policy.get("pending_usd"))
        except ValueError:
            self._accounting_valid = False

    def _reserve_bound(self):
        policy = self.policy
        if (not self._accounting_valid or self._pending != ZERO
                or not policy.get("credential_id")
                or not all(policy.get(name) is True for name in GUARANTEES)):
            raise ValueError("Uncertified policy")
        nin, nout = policy.get("input_tokens_upper"), policy.get("output_tokens_upper")
        if type(nin) is not int or not 0 < nin <= 1024 or type(nout) is not int or not 800 <= nout <= 1_000_000:
            raise ValueError("Uncertified tokens")
        pin = amount(policy.get("input_price_per_million_usd"))
        pout = amount(policy.get("output_price_per_million_usd"))
        fees = amount(policy.get("fees_upper_usd"))
        if pin <= ZERO or pout <= ZERO:
            raise ValueError("Uncertified price")
        budget = amount(policy.get("budget_usd"))
        limits = policy.get("additional_limits_usd", [])
        if not isinstance(limits, list):
            raise ValueError("Uncertified budget")
        for limit in limits:
            budget = min(budget, amount(limit))
        if budget <= ZERO:
            raise ValueError("Uncertified budget")
        # Bounded operands above fit exactly within this precision; never round
        # a financial upper bound down under the ambient Decimal context.
        with localcontext() as context:
            context.prec = 80
            reserve = (Decimal(nin) * pin + Decimal(nout) * pout) / Decimal(1_000_000) + fees
        return reserve, budget

    def _observation(self, now):
        last = self._last or {}
        verified = self._verified
        expired = verified is not None and now >= verified + timedelta(seconds=60)
        status = last.get("status", "unknown")
        reason = last.get("reason_code", "not_verified")
        if expired and status == "ok":
            status, reason = "unknown", "stale"
        return {
            "id": "openrouter", "status": status, "reason_code": reason,
            "source_kind": "live" if verified is not None else "unverified",
            "checked_at": now, "latency_ms": last.get("latency_ms"),
            "verified_at": verified, "last_attempt_at": last.get("last_attempt_at"),
            "expires_at": verified + timedelta(seconds=60) if verified else None,
            "check_id": self._verified_id,
            "reported_model": last.get("reported_model"),
            "model_identity": "unconfirmed",
            "reported_cost_usd": last.get("reported_cost_usd"),
            "cost_status": last.get("cost_status", "unavailable"),
            "cost_confirmation": "unconfirmed",
        }

    def observation(self):
        with self._lock:
            return deepcopy(self._observation(self.clock()))

    def accounting(self):
        with self._lock:
            return {"spent_usd": self._spent, "pending_usd": self._pending, "uncertain_usd": self._uncertain}

    def _refuse(self, now, status, reason, retry_after=None):
        observation = self._observation(now)
        observation.update(http_status=status, status="unknown", reason_code=reason)
        if retry_after is not None:
            observation["retry_after"] = max(1, int(retry_after))
        # A refusal is not an attempt and must not advance any verified date.
        return observation

    def check(self, *, session_id, tenant_id, idempotency_key):
        now = self.clock()
        action = (session_id, tenant_id, idempotency_key)
        with self._lock, localcontext() as context:
            context.prec = 80
            while self._history and self._history[0] <= now - timedelta(days=1):
                self._history.popleft()
            while self._actions and next(iter(self._actions.values()))[0] <= now - timedelta(days=1):
                self._actions.popitem(last=False)
            if action in self._actions:
                previous = self._actions[action][1]
                if previous is not None:
                    result = deepcopy(previous)
                    if result.get("status") == "ok" and result["verified_at"] + timedelta(seconds=60) <= now:
                        result.update(status="unknown", reason_code="stale")
                    return result
            if self._active:
                return self._refuse(now, 409, "busy")
            try:
                preflight = getattr(self.transport, "preflight", None)
                if callable(preflight):
                    preflight()
                reserve, budget = self._reserve_bound()
                limit = self.policy.get("execution_calls_limit")
                if limit is not None and (type(limit) is not int or limit <= 0
                        or type(self._execution_calls) is not int or self._execution_calls < 0
                        or self._execution_calls >= limit):
                    raise ValueError("Execution allowance unavailable")
            except (ValueError, TypeError, KeyError, OSError):
                return self._refuse(now, 429, "budget_unavailable")
            if self._spent + self._uncertain + self._pending + reserve > budget:
                return self._refuse(now, 429, "budget_unavailable")
            if self._history:
                cooldown = 60 - (now - self._history[-1]).total_seconds()
                if cooldown > 0:
                    return self._refuse(now, 429, "cooldown", cooldown)
            hourly = [stamp for stamp in self._history if stamp > now - timedelta(hours=1)]
            if len(hourly) >= 6:
                return self._refuse(now, 429, "cooldown", (hourly[0] + timedelta(hours=1) - now).total_seconds())
            if len(self._history) >= 24:
                return self._refuse(now, 429, "cooldown", (self._history[0] + timedelta(days=1) - now).total_seconds())
            if len(self._actions) >= 2048:
                return self._refuse(now, 429, "busy", 60)
            self._active = True
            self._execution_calls += 1
            self._pending += reserve
            self._history.append(now)
            self._actions[action] = (now, None)

        payload = {
            "model": "economicon-chat", "messages": [{"role": "user", "content": "Return exactly the two uppercase letters OK. Do not include punctuation, quotes, whitespace, or any other text."}],
            "max_tokens": 32, "stream": False, "reasoning": {"enabled": False},
            "provider": {"order": ["deepinfra/fp4"], "allow_fallbacks": False,
                         "require_parameters": True, "zdr": True, "data_collection": "deny",
                         "max_price": {"prompt": str(self.policy["input_price_per_million_usd"]),
                                       "completion": str(self.policy["output_price_per_million_usd"])}},
        }
        started = time.monotonic()
        charged = None
        check_id = uuid4().hex
        reason, state = "invalid_response", "unknown"
        information = {"reported_model": None, "reported_cost_usd": None, "cost_status": "unavailable"}
        try:
            receipt = self.transport(payload, timeout_seconds=30)
            if not isinstance(receipt, dict):
                raise ValueError("Invalid diagnostic receipt")
            cost, cost_status = reported_cost(receipt.get("cost_usd"))
            information = {"reported_model": reported_model(receipt.get("model")),
                           "reported_cost_usd": cost, "cost_status": cost_status}
            route_valid = (receipt.get("provider") == "deepinfra/fp4"
                           and receipt.get("route_verified") is True
                           and receipt.get("result_valid") is True)
            if not route_valid:
                raise ValueError("Invalid functional result or configured route")
            receipt_id = receipt.get("check_id")
            if isinstance(receipt_id, str) and len(receipt_id) == 32 and all(c in "0123456789abcdef" for c in receipt_id):
                check_id = receipt_id
            state, reason = "ok", "none"
            # Settlement cannot change functional availability; unusable cost
            # or usage retains the entire reservation independently.
            try:
                usage = receipt.get("usage", {})
                input_tokens, output_tokens = usage.get("prompt_tokens"), usage.get("completion_tokens")
                usage_valid = (type(input_tokens) is int and type(output_tokens) is int
                               and 0 <= input_tokens <= self.policy["input_tokens_upper"]
                               and 0 <= output_tokens <= self.policy["output_tokens_upper"])
                observed_cost = amount(receipt.get("cost_usd"))
                if usage_valid and input_tokens + output_tokens > 0 and ZERO < observed_cost <= reserve:
                    charged = observed_cost
            except (ValueError, TypeError, AttributeError):
                pass
        except ProviderDiagnosticFailure as failure:
            state, reason = "failed", failure.reason
        except TimeoutError:
            reason = "timeout"
        except (ValueError, TypeError, AttributeError):
            reason = "invalid_response"
        except Exception:
            reason = "upstream_error"
        finally:
            finished = self.clock()
            with self._lock, localcontext() as context:
                context.prec = 80
                self._pending -= reserve
                if charged is None:
                    self._uncertain += reserve
                else:
                    self._spent += charged
                if state == "ok":
                    self._verified, self._verified_id = finished, check_id
                self._last = {"status": state, "reason_code": reason, "last_attempt_at": now,
                              "latency_ms": round((time.monotonic() - started) * 1000, 2),
                              **information}
                self._active = False
                result = self._observation(finished)
                result["http_status"] = 200
                self._actions[action] = (now, deepcopy(result))
        return result
