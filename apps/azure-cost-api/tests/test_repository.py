from decimal import Decimal

import pytest

from app.repository import CostRepository, DatasetError, parse_tags


def test_repository_loads_public_fixture(settings):
    repository = CostRepository(
        settings.azure_cost_dataset_path,
        settings.azure_cost_mapping_path,
    )

    assert len(repository.records) == 50
    assert len(repository.subscription_ids) == 4
    assert repository.max_usage_date.isoformat() == "2024-06-19"


def test_repository_preserves_negative_and_zero_costs(settings):
    repository = CostRepository(
        settings.azure_cost_dataset_path,
        settings.azure_cost_mapping_path,
    )
    costs = [record.cost for record in repository.records]

    assert any(cost < Decimal("0") for cost in costs)
    assert any(cost == Decimal("0") for cost in costs)


def test_legacy_tags_are_parsed_without_modifying_values():
    tags = parse_tags('"CostCenter": "1234","env": "prod","Project": "Foo"')

    assert tags == {"CostCenter": "1234", "env": "prod", "Project": "Foo"}


def test_json_tags_are_parsed_without_modifying_values():
    tags = parse_tags('{"CostCenter":"1234","env":"prod","Project":"Foo"}')

    assert tags == {"CostCenter": "1234", "env": "prod", "Project": "Foo"}


def test_repository_rejects_fixture_with_missing_contract_columns(settings, tmp_path):
    invalid_fixture = tmp_path / "invalid.csv"
    invalid_fixture.write_text("SubscriptionId\nsubscription-1\n", encoding="utf-8")

    with pytest.raises(DatasetError, match="missing required columns"):
        CostRepository(invalid_fixture, settings.azure_cost_mapping_path)
