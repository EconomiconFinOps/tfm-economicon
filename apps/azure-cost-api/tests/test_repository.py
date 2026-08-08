from decimal import Decimal

from app.repository import CostRepository, parse_tags


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
