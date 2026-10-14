"""The one place that decides which day is "today" for costs, anomaly detection and the assistant."""
from datetime import date, datetime, timedelta, timezone

_fixed: date | None = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def configure(value: date | None) -> None:
    global _fixed
    _fixed = value


def today() -> date:
    return _fixed if _fixed is not None else _utc_now().date()


def simulated() -> bool:
    return _fixed is not None


def visible_end(end: date) -> date:
    """Exclusive end of a period, cut so that the reference day is the last visible one."""
    return min(end, today() + timedelta(days=1))
