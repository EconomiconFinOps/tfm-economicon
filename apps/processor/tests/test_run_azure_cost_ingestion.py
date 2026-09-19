from app.run_azure_cost_ingestion import DEFAULT_DEFINITION


def test_default_definition_requests_resource_level_grouping():
    grouping_names = {
        item["name"]
        for item in DEFAULT_DEFINITION["dataset"]["grouping"]
        if item["type"] == "Dimension"
    }

    assert "ResourceId" in grouping_names
    assert "ResourceGroup" in grouping_names
    assert "ServiceName" in grouping_names
