from app.run_azure_cost_ingestion import DEFAULT_DEFINITION


def test_default_definition_requests_resource_level_grouping():
    grouping_names = {
        item["name"]
        for item in DEFAULT_DEFINITION["dataset"]["grouping"]
        if item["type"] == "Dimension"
    }

    assert grouping_names == {"ResourceId", "ResourceGroup"}
