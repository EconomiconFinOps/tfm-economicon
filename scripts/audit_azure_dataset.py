#!/usr/bin/env python3
"""Audit the public Azure FinOps sample archive without extracting it.

The command reads CSV entries as streams, produces a deterministic JSON report,
and can generate small reproducible fixtures for local development.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import io
import json
import zipfile
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


DATE_FORMATS = (
    "%m/%d/%Y",
    "%m/%d/%Y %H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M%z",
    "%Y%m%d",
)
DATE_COLUMN_MARKERS = ("date", "periodstart", "periodend")
CURRENCY_COLUMNS = {"BillingCurrency", "BillingCurrencyCode", "Currency", "CurrencyCode"}
NUMERIC_COLUMNS = {
    "Amount",
    "BilledCost",
    "ConsumedQuantity",
    "CostInBillingCurrency",
    "EffectiveCost",
    "ListCost",
    "Quantity",
    "UsageQuantity",
}
CARDINALITY_COLUMNS = {
    "MeterCategory",
    "ResourceGroup",
    "ServiceCategory",
    "SubAccountId",
    "SubscriptionId",
    "x_ResourceGroupName",
}
IDENTIFIER_COLUMN_MARKERS = (
    "accountowner",
    "email",
    "resourceid",
    "subscriptionid",
    "billingaccountid",
    "billingprofileid",
    "invoicesectionid",
    "reservationid",
    "reservationorderid",
    "customerid",
    "resellerid",
    "tags",
)
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_date(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    if "T" in value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if len(value) == 10 and value[2:3] == "/" and value[5:6] == "/":
        try:
            return datetime.strptime(value, "%m/%d/%Y")
        except ValueError:
            return None
    if len(value) == 8 and value.isdigit():
        try:
            return datetime.strptime(value, "%Y%m%d")
        except ValueError:
            return None
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue
    return None


def is_safe_entry(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and "\\" not in name


def identifier_columns(columns: Iterable[str]) -> list[str]:
    return [
        column
        for column in columns
        if any(marker in column.casefold() for marker in IDENTIFIER_COLUMN_MARKERS)
    ]


def stable_score(seed: str, row_number: int, row: list[str]) -> int:
    payload = f"{seed}:{row_number}:".encode() + "\x1f".join(row).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def profile_entry(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    *,
    sample_size: int,
    sample_seed: str,
) -> tuple[dict[str, Any], list[str], list[list[str]]]:
    with archive.open(info) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        reader = csv.reader(text)
        header = next(reader, [])
        nulls = [0] * len(header)
        malformed_rows = 0
        blank_rows = 0
        row_count = 0
        date_ranges: dict[str, list[str | None]] = {
            column: [None, None]
            for column in header
            if any(marker in column.casefold() for marker in DATE_COLUMN_MARKERS)
        }
        currencies: dict[str, Counter[str]] = {
            column: Counter() for column in header if column in CURRENCY_COLUMNS
        }
        date_indexes = {column: header.index(column) for column in date_ranges}
        currency_indexes = {column: header.index(column) for column in currencies}
        numeric_indexes = {column: header.index(column) for column in header if column in NUMERIC_COLUMNS}
        numeric_stats: dict[str, dict[str, Any]] = {
            column: {"non_null": 0, "invalid": 0, "negative": 0, "zero": 0, "min": None, "max": None}
            for column in numeric_indexes
        }
        cardinality_indexes = {
            column: header.index(column) for column in header if column in CARDINALITY_COLUMNS
        }
        cardinalities: dict[str, set[str]] = {column: set() for column in cardinality_indexes}
        sample_heap: list[tuple[int, int, list[str]]] = []

        for row_number, row in enumerate(reader, start=2):
            if not row or all(not value.strip() for value in row):
                blank_rows += 1
                continue
            row_count += 1
            if len(row) != len(header):
                malformed_rows += 1
                continue

            for index, value in enumerate(row):
                if not value.strip():
                    nulls[index] += 1

            for column, bounds in date_ranges.items():
                parsed = parse_date(row[date_indexes[column]])
                if parsed is None:
                    continue
                normalized = parsed.date().isoformat()
                bounds[0] = normalized if bounds[0] is None or normalized < bounds[0] else bounds[0]
                bounds[1] = normalized if bounds[1] is None or normalized > bounds[1] else bounds[1]

            for column, values in currencies.items():
                value = row[currency_indexes[column]].strip()
                if value:
                    values[value] += 1

            for column, index in numeric_indexes.items():
                value = row[index].strip()
                if not value:
                    continue
                stats = numeric_stats[column]
                stats["non_null"] += 1
                try:
                    number = Decimal(value)
                except InvalidOperation:
                    stats["invalid"] += 1
                    continue
                stats["negative"] += number < 0
                stats["zero"] += number == 0
                stats["min"] = number if stats["min"] is None or number < stats["min"] else stats["min"]
                stats["max"] = number if stats["max"] is None or number > stats["max"] else stats["max"]

            for column, index in cardinality_indexes.items():
                value = row[index].strip()
                if value:
                    cardinalities[column].add(value)

            if sample_size:
                score = stable_score(sample_seed, row_number, row)
                candidate = (-score, row_number, row)
                if len(sample_heap) < sample_size:
                    heapq.heappush(sample_heap, candidate)
                elif candidate > sample_heap[0]:
                    heapq.heapreplace(sample_heap, candidate)

    samples = [item[2] for item in sorted(sample_heap, key=lambda item: item[1])]
    report = {
        "name": info.filename,
        "compressed_bytes": info.compress_size,
        "uncompressed_bytes": info.file_size,
        "row_count": row_count,
        "column_count": len(header),
        "columns": header,
        "duplicate_columns": sorted(
            column for column, count in Counter(header).items() if count > 1
        ),
        "malformed_rows": malformed_rows,
        "blank_rows": blank_rows,
        "null_counts": dict(zip(header, nulls)),
        "date_ranges": {
            column: {"min": bounds[0], "max": bounds[1]}
            for column, bounds in date_ranges.items()
        },
        "currencies": {
            column: dict(sorted(values.items())) for column, values in currencies.items()
        },
        "numeric_stats": {
            column: {
                **{key: value for key, value in stats.items() if key not in {"min", "max"}},
                "min": str(stats["min"]) if stats["min"] is not None else None,
                "max": str(stats["max"]) if stats["max"] is not None else None,
            }
            for column, stats in numeric_stats.items()
        },
        "cardinalities": {column: len(values) for column, values in cardinalities.items()},
        "identifier_columns": identifier_columns(header),
    }
    return report, header, samples


def audit_archive(path: Path, *, sample_size: int = 0) -> tuple[dict[str, Any], dict[str, Any]]:
    archive_sha256 = sha256_file(path)
    fixtures: dict[str, Any] = {}
    entries: list[dict[str, Any]] = []
    archive_issues: list[str] = []
    csv.field_size_limit(16 * 1024 * 1024)

    with zipfile.ZipFile(path) as archive:
        names = [info.filename for info in archive.infolist() if not info.is_dir()]
        if len(names) != len(set(names)):
            archive_issues.append("duplicate entry names")
        for name in names:
            if not is_safe_entry(name):
                archive_issues.append(f"unsafe entry path: {name}")

        for info in archive.infolist():
            if info.is_dir():
                continue
            if not info.filename.casefold().endswith(".csv"):
                archive_issues.append(f"non-CSV entry: {info.filename}")
                continue
            entry, header, samples = profile_entry(
                archive,
                info,
                sample_size=sample_size,
                sample_seed=f"{archive_sha256}:{info.filename}",
            )
            entries.append(entry)
            fixtures[info.filename] = {
                "header": header,
                "rows": samples,
            }

    report = {
        "schema_version": 1,
        "source": {
            "repository": "https://github.com/microsoft/finops-toolkit",
            "release": "v14",
            "release_url": "https://github.com/microsoft/finops-toolkit/releases/tag/v14",
            "asset": "dataset-examples.zip",
            "download_url": "https://github.com/microsoft/finops-toolkit/releases/download/v14/dataset-examples.zip",
            "license": "MIT",
            "license_url": "https://github.com/microsoft/finops-toolkit/blob/v14/LICENSE",
        },
        "archive": {
            "filename": path.name,
            "bytes": path.stat().st_size,
            "sha256": archive_sha256,
            "entry_count": len(entries),
            "issues": archive_issues,
        },
        "totals": {
            "rows": sum(entry["row_count"] for entry in entries),
            "compressed_bytes": sum(entry["compressed_bytes"] for entry in entries),
            "uncompressed_bytes": sum(entry["uncompressed_bytes"] for entry in entries),
            "malformed_rows": sum(entry["malformed_rows"] for entry in entries),
            "blank_rows": sum(entry["blank_rows"] for entry in entries),
        },
        "entries": entries,
    }
    return report, fixtures


def write_fixtures(fixtures: dict[str, Any], destination: Path, manifest: dict[str, Any]) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    generated_files: list[dict[str, Any]] = []
    for source_name, fixture in fixtures.items():
        output_name = f"{Path(source_name).stem}.sample.csv"
        output_path = destination / output_name
        with output_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.writer(target, lineterminator="\n")
            writer.writerow(fixture["header"])
            writer.writerows(fixture["rows"])
        generated_files.append(
            {"path": output_name, "source_entry": source_name, "rows": len(fixture["rows"])}
        )

    fixture_manifest = {
        "schema_version": 1,
        "source_archive_sha256": manifest["archive"]["sha256"],
        "source_release": manifest["source"]["release"],
        "transformation": "None; sampled rows retain the public values published by Microsoft.",
        "files": generated_files,
    }
    (destination / "manifest.json").write_text(
        json.dumps(fixture_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Path to dataset-examples.zip")
    parser.add_argument("--output", type=Path, help="Write the JSON audit report here")
    parser.add_argument("--fixture-dir", type=Path, help="Generate deterministic sample CSV fixtures")
    parser.add_argument("--sample-size", type=int, default=0, help="Rows per fixture (default: 0)")
    args = parser.parse_args()
    if args.sample_size < 0:
        parser.error("--sample-size cannot be negative")
    if args.fixture_dir and args.sample_size == 0:
        parser.error("--fixture-dir requires --sample-size greater than zero")
    return args


def main() -> int:
    args = parse_args()
    if not args.archive.is_file():
        raise SystemExit(f"Archive not found: {args.archive}")
    report, fixtures = audit_archive(args.archive, sample_size=args.sample_size)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    if args.fixture_dir:
        write_fixtures(fixtures, args.fixture_dir, report)
    return 1 if report["archive"]["issues"] or report["totals"]["malformed_rows"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
