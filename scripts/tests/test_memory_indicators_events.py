"""Los eventos inyectados de las anomalías (JUP-130) coinciden con los saltos reales del generador de datos."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVENTS_PATH = ROOT / "docs" / "validation" / "JUP-130-injected-events.json"
JUMP = Decimal(100)
REFERENCE_DAYS = 7


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


dataset = load("economicon_jup130_demo_dataset", ROOT / "scripts" / "demo_dataset.py")


def generator_series() -> dict[str, dict[date, Decimal]]:
    """Coste diario por servicio tal como lo define el generador; un día sin registro no aparece."""
    days = list(dataset.days(dataset.WINDOW_START, dataset.WINDOW_END))
    return {
        service: {day: Decimal(value) for day, value in zip(days, values) if value is not None}
        for service, values in dataset.anomaly_levels().items()
    }


def generator_jumps(series: dict[str, dict[date, Decimal]]) -> set[tuple[str, date]]:
    """Aumentos de al menos 100 EUR sobre el día anterior; la caída de un servicio no es un aumento."""
    jumps = set()
    for service, values in series.items():
        for day, cost in values.items():
            previous = values.get(day - timedelta(days=1), Decimal(0))
            if day > dataset.WINDOW_START and cost - previous >= JUMP:
                jumps.add((service, day))
    return jumps


def prior_week_cost(series: dict[date, Decimal], day: date) -> Decimal:
    return sum((series.get(day - timedelta(days=offset), Decimal(0)) for offset in range(1, REFERENCE_DAYS + 1)), Decimal(0))


def read_events(document: dict | None = None) -> list[dict]:
    document = document if document is not None else json.loads(EVENTS_PATH.read_text("utf-8"))
    return document["events"]


def event_key(event: dict) -> tuple[str, date]:
    return event["service"], date.fromisoformat(event["start_date"])


class EventsAgainstGenerator(unittest.TestCase):
    def test_every_event_is_a_real_jump_of_the_generator(self):
        jumps = generator_jumps(generator_series())
        for event in read_events():
            self.assertIn(event_key(event), jumps, event["id"])

    def test_every_jump_of_the_generator_has_an_event(self):
        covered = {event_key(event) for event in read_events()}
        self.assertEqual(generator_jumps(generator_series()) - covered, set())

    def test_exactly_the_seven_known_events(self):
        self.assertEqual(
            sorted((e["service"], e["start_date"]) for e in read_events()),
            sorted([
                ("Compute", "2026-09-09"), ("Analytics", "2026-09-10"), ("Backup", "2026-09-10"),
                ("Networking", "2026-09-14"), ("Database", "2026-09-16"), ("Tools", "2026-10-08"),
                ("Storage", "2026-10-20"),
            ]),
        )

    def test_the_fall_of_compute_on_4_october_is_not_an_event(self):
        self.assertNotIn(("Compute", "2026-10-04"), [(e["service"], e["start_date"]) for e in read_events()])

    def test_detectable_by_design_means_a_positive_reference_week(self):
        series = generator_series()
        for event in read_events():
            service, day = event_key(event)
            self.assertEqual(event["detectable_by_design"], prior_week_cost(series[service], day) > 0, event["id"])

    def test_the_zero_reference_events_are_backup_and_networking(self):
        undetectable = sorted(e["service"] for e in read_events() if not e["detectable_by_design"])
        self.assertEqual(undetectable, ["Backup", "Networking"])

    def test_ids_are_unique_and_the_document_declares_its_origin(self):
        document = json.loads(EVENTS_PATH.read_text("utf-8"))
        ids = [event["id"] for event in document["events"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(document["version"], 1)
        self.assertEqual(document["origin"], "scripts/demo_dataset.py")
        self.assertEqual(document["tolerance_days"], 3)


class ConsistencyDetectsDrift(unittest.TestCase):
    """Cada variante de la lista tiene que romper alguna de las comprobaciones de arriba."""

    def variant(self, change) -> list[dict]:
        document = copy.deepcopy(json.loads(EVENTS_PATH.read_text("utf-8")))
        change(document["events"])
        return document["events"]

    def broken(self, events: list[dict]) -> bool:
        series = generator_series()
        jumps = generator_jumps(series)
        keys = {event_key(event) for event in events}
        if keys - jumps or jumps - keys:
            return True
        return any(event["detectable_by_design"] != (prior_week_cost(series[event["service"]], event_key(event)[1]) > 0)
                   for event in events)

    def test_the_real_list_is_not_broken(self):
        self.assertFalse(self.broken(read_events()))

    def test_a_deleted_event_is_detected(self):
        self.assertTrue(self.broken(self.variant(lambda events: events.pop(0))))

    def test_a_false_event_is_detected(self):
        extra = {"id": "EV-99", "service": "Tools", "start_date": "2026-10-09", "nature": "one_day_spike",
                 "detectable_by_design": True}
        self.assertTrue(self.broken(self.variant(lambda events: events.append(extra))))

    def test_a_moved_day_is_detected(self):
        def move(events):
            events[0]["start_date"] = (date.fromisoformat(events[0]["start_date"]) + timedelta(days=1)).isoformat()
        self.assertTrue(self.broken(self.variant(move)))

    def test_a_flipped_detectable_flag_is_detected(self):
        def flip(events):
            events[0]["detectable_by_design"] = not events[0]["detectable_by_design"]
        self.assertTrue(self.broken(self.variant(flip)))


if __name__ == "__main__":
    unittest.main()
