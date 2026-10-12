"""JUP-019 daily business rule over observed daily costs, kept as candidate episodes (ADR-0019)."""
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json

RULES_VERSION = "jup019-daily-v1"
REFERENCE_DAYS = 7
TOLERANCE_DAYS = 3
MAX_DAYS_PER_RUN = 7
SUPPORTED_CURRENCIES = ("EUR", "USD")
RULES = {
    "relative_increase_percent": "20",
    "absolute_increase": "100.00",
    "reference_days": REFERENCE_DAYS,
    "tolerance_days": TOLERANCE_DAYS,
    "severity": {"P1": "> 2000.00", "P2": "500.00 to 2000.00", "P3": "< 500.00"},
    "currencies": list(SUPPORTED_CURRENCIES),
}
TRACKING_STATUSES = ("new", "investigating")
# Amounts are kept multiplied by REFERENCE_DAYS so that a mean never needs rounding.
_ABSOLUTE_X7 = Decimal("100.00") * REFERENCE_DAYS
_P1_X7 = Decimal("2000.00") * REFERENCE_DAYS
_P2_X7 = Decimal("500.00") * REFERENCE_DAYS


def money(value: Decimal) -> str:
    with localcontext() as context:
        context.prec = max(80, len(value.as_tuple().digits) + 20)
        rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return "0.00" if rounded == 0 else format(rounded, "f")


def _over_seven(value: Decimal) -> str:
    with localcontext() as context:
        context.prec = max(80, len(value.as_tuple().digits) + 20)
        return money(value / REFERENCE_DAYS)


def severity(impact_numerator: Decimal) -> str:
    if impact_numerator > _P1_X7:
        return "P1"
    return "P2" if impact_numerator >= _P2_X7 else "P3"


def triggers(observed: Decimal, reference_week_cost: Decimal) -> bool:
    excess = observed * REFERENCE_DAYS - reference_week_cost
    # Strict JUP-019 conditions: > 100 per day AND > 20 % over the expected daily cost.
    return reference_week_cost > 0 and excess > _ABSOLUTE_X7 and excess * 5 > reference_week_cost


def service_key(service: str | None) -> str:
    return json.dumps(service, ensure_ascii=True)


@dataclass
class Episode:
    id: str
    currency: str
    service: str | None
    start_date: date
    last_seen_date: date
    observation: str
    no_longer_observed_on: date | None
    reference_week_cost: Decimal
    opening_observed: Decimal
    impact_numerator: Decimal
    impact_day_count: int
    impact_through_date: date
    status: str
    previous_episode_id: str | None
    rules_version: str = RULES_VERSION
    rules: dict = field(default_factory=lambda: json.loads(json.dumps(RULES)))

    @property
    def group(self) -> tuple:
        return self.currency, self.service

    @property
    def tracking(self) -> bool:
        return self.observation == "observed" and self.status in TRACKING_STATUSES

    @property
    def processed_until(self) -> date:
        return max(self.impact_through_date, self.no_longer_observed_on or self.impact_through_date)

    @property
    def severity(self) -> str:
        return severity(self.impact_numerator)

    @property
    def reference_daily_cost(self) -> str:
        return _over_seven(self.reference_week_cost)

    @property
    def opening_observed_cost(self) -> str:
        return money(self.opening_observed)

    @property
    def accumulated_impact(self) -> str:
        return _over_seven(self.impact_numerator)

    def copy(self) -> "Episode":
        return replace(self, rules=json.loads(json.dumps(self.rules)))


@dataclass
class DetectionWindow:
    status: str
    last_complete_day: date | None
    days: list[date]
    unevaluated: tuple[date, date] | None

    @property
    def read_start(self) -> date | None:
        return self.days[0] - timedelta(days=REFERENCE_DAYS) if self.days else None


@dataclass
class DetectionPlan:
    status: str
    evaluated_days: list[date]
    skipped_days: list[tuple[date, str]]
    unsupported_currencies: list[str]
    opened: list[Episode]
    updated: list[Episode]
    continued: int
    no_longer_observed: int
    new_last_evaluated: date | None


def detection_window(*, today: date, last_evaluated: date | None, latest_observed: date | None) -> DetectionWindow:
    if latest_observed is None:
        return DetectionWindow("insufficient_data", None, [], None)
    # The latest day with data may still be receiving late records, and today is never closed.
    last_complete = min(latest_observed, today) - timedelta(days=1)
    first_pending = last_complete - timedelta(days=MAX_DAYS_PER_RUN - 1) if last_evaluated is None \
        else last_evaluated + timedelta(days=1)
    if first_pending > last_complete:
        return DetectionWindow("up_to_date", last_complete, [], None)
    first = max(first_pending, last_complete - timedelta(days=MAX_DAYS_PER_RUN - 1))
    unevaluated = (first_pending, first - timedelta(days=1)) if first > first_pending else None
    days = [first + timedelta(days=offset) for offset in range((last_complete - first).days + 1)]
    return DetectionWindow("pending", last_complete, days, unevaluated)


def episode_id(tenant_id: str, currency: str, service: str | None, start: date) -> str:
    identity = json.dumps([1, tenant_id, RULES_VERSION, currency, service, start.isoformat()],
                          ensure_ascii=True, separators=(",", ":"))
    return "anomaly-" + hashlib.sha256(identity.encode()).hexdigest()


def _evaluable(day: date, observed_days: set[date]) -> str | None:
    if day not in observed_days:
        return "not_observed"
    if any(day - timedelta(days=offset) not in observed_days for offset in range(1, REFERENCE_DAYS + 1)):
        return "reference_incomplete"
    return None


def plan_detection(window: DetectionWindow, *, tenant_id: str, observed_days: set[date],
                   daily: dict[tuple, dict[date, Decimal]], episodes: list[Episode]) -> DetectionPlan:
    skipped, evaluable = [], []
    for day in window.days:
        reason = _evaluable(day, observed_days)
        (skipped.append((day, reason)) if reason else evaluable.append(day))
    unsupported = sorted({currency for currency, _ in daily if currency not in SUPPORTED_CURRENCIES
                          and any(day in daily[(currency, _)] for day in window.days)})
    if not evaluable:
        return DetectionPlan("insufficient_data", [], skipped, unsupported, [], [], 0, 0, None)

    by_id = {item.id: item for item in episodes}
    tracking = {item.group: item for item in episodes if item.tracking}
    latest = {}
    for item in sorted(episodes, key=lambda item: (item.start_date, item.id)):
        latest[item.group] = item
    processed = {}
    for item in episodes:
        processed[item.group] = max(processed.get(item.group, item.processed_until), item.processed_until)
    groups = sorted({key for key in daily if key[0] in SUPPORTED_CURRENCIES} | set(tracking),
                    key=lambda key: (key[0], key[1] is not None, key[1] or ""))
    opened, changed, seen = [], set(), set()
    ended = 0
    with localcontext() as context:
        context.prec = 120
        for day in evaluable:
            for group in groups:
                if group in processed and day <= processed[group]:
                    continue
                values = daily.get(group, {})
                observed = values.get(day, Decimal(0))
                current = tracking.get(group)
                reference = current.reference_week_cost if current else sum(
                    (values.get(day - timedelta(days=offset), Decimal(0)) for offset in range(1, REFERENCE_DAYS + 1)),
                    Decimal(0))
                hit = triggers(observed, reference)
                if current is not None:
                    if not hit and (day - current.last_seen_date).days > TOLERANCE_DAYS:
                        current.observation, current.no_longer_observed_on = "no_longer_observed", day
                        del tracking[group]
                        ended += 1
                    else:
                        if hit:
                            current.last_seen_date = day
                            seen.add(current.id)
                        current.impact_numerator += max(Decimal(0), observed * REFERENCE_DAYS - reference)
                        current.impact_day_count += 1
                        current.impact_through_date = day
                    changed.add(current.id)
                elif hit:
                    identifier = episode_id(tenant_id, group[0], group[1], day)
                    if identifier in by_id:
                        continue
                    previous = latest.get(group)
                    item = Episode(
                        id=identifier, currency=group[0], service=group[1], start_date=day, last_seen_date=day,
                        observation="observed", no_longer_observed_on=None, reference_week_cost=reference,
                        opening_observed=observed, impact_numerator=observed * REFERENCE_DAYS - reference,
                        impact_day_count=1, impact_through_date=day, status="new",
                        previous_episode_id=previous.id if previous else None,
                    )
                    opened.append(item)
                    by_id[identifier] = latest[group] = tracking[group] = item
    new_ids = {item.id for item in opened}
    updated = [by_id[identifier] for identifier in sorted(changed - new_ids)]
    return DetectionPlan(
        status="completed", evaluated_days=evaluable, skipped_days=skipped, unsupported_currencies=unsupported,
        opened=opened, updated=updated, continued=len(seen - new_ids), no_longer_observed=ended,
        new_last_evaluated=window.last_complete_day,
    )
