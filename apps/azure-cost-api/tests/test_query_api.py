import json
from copy import deepcopy
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CASES = json.loads(
    (REPOSITORY_ROOT / "docs/api/azure-cost-query-contract-cases.json").read_text(
        encoding="utf-8"
    )
)
CASES_BY_ID = {case["id"]: case for case in CASES["cases"]}
SUBSCRIPTION_ID = CASES["knownSubscriptionId"]
QUERY_PATH = f"/subscriptions/{SUBSCRIPTION_ID}/providers/Microsoft.CostManagement/query"


def post_query(client, body, *, subscription_id=SUBSCRIPTION_ID, api_version="2025-03-01"):
    path = f"/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query"
    return client.post(path, params={"api-version": api_version}, json=body)


def test_health_reports_loaded_fixture(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "dataset": "EA-Cost-Actual.sample.csv",
        "rows": 50,
        "subscriptions": 4,
    }


def test_contractual_openapi_is_served_verbatim(client):
    expected = json.loads(
        (REPOSITORY_ROOT / "docs/api/azure-cost-query.openapi.json").read_text(
            encoding="utf-8"
        )
    )

    assert client.get("/openapi.json").json() == expected


def test_daily_cost_grouped_by_resource_group(client):
    case = CASES_BY_ID["daily-cost-by-resource-group"]
    response = post_query(client, case["request"])

    assert response.status_code == 200
    payload = response.json()
    properties = payload["properties"]
    assert [column["name"] for column in properties["columns"]] == case["expectedColumns"]
    assert properties["rows"]
    assert all(len(row) == len(properties["columns"]) for row in properties["rows"])
    assert all(isinstance(row[2], int) and row[3] == "USD" for row in properties["rows"])
    assert properties["nextLink"] is None


def test_dimension_filter_uses_service_mapping(client):
    case = CASES_BY_ID["storage-only"]
    response = post_query(client, case["request"])

    assert response.status_code == 200
    properties = response.json()["properties"]
    assert [column["name"] for column in properties["columns"]] == case["expectedColumns"]
    assert len(properties["rows"]) == 1
    assert properties["rows"][0][-1] == "USD"


def test_tag_filter_reads_legacy_tags(client):
    case = CASES_BY_ID["production-tag"]
    response = post_query(client, case["request"])

    assert response.status_code == 200
    assert response.json()["properties"]["rows"]


def test_valid_query_without_data_has_stable_empty_response(client):
    case = CASES_BY_ID["no-data"]
    response = post_query(client, case["request"])

    assert response.status_code == 200
    assert response.json()["properties"]["rows"] == []
    assert response.json()["properties"]["nextLink"] is None


def test_unknown_subscription_uses_azure_error_shape(client):
    case = CASES_BY_ID["unknown-subscription"]
    request = CASES_BY_ID[case["requestRef"]]["request"]
    response = post_query(client, request, subscription_id=case["subscriptionId"])

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SubscriptionNotFound"


def test_unsupported_dimension_is_a_bad_request(client):
    case = CASES_BY_ID["unsupported-dimension"]
    response = post_query(client, case["request"])

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BadRequest"
    assert "UnsupportedDimension" in response.json()["error"]["message"]


def test_unsupported_api_version_is_a_bad_request(client):
    case = CASES_BY_ID["unsupported-api-version"]
    request = CASES_BY_ID[case["requestRef"]]["request"]
    response = post_query(client, request, api_version=case["apiVersion"])

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BadRequest"


def test_invalid_body_uses_contract_error_shape(client):
    response = post_query(
        client,
        {
            "type": "ActualCost",
            "timeframe": "Custom",
            "dataset": {
                "granularity": "None",
                "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BadRequest"


def test_query_resource_id_is_deterministic(client):
    body = CASES_BY_ID["daily-cost-by-resource-group"]["request"]

    first = post_query(client, body).json()
    second = post_query(client, body).json()

    assert first["id"] == second["id"]
    assert first["name"] == second["name"]


def test_nested_filters_are_case_insensitive(client):
    body = deepcopy(CASES_BY_ID["daily-cost-by-resource-group"]["request"])
    body["dataset"]["filter"] = {
        "and": [
            {
                "dimensions": {
                    "name": "ServiceName",
                    "operator": "In",
                    "values": ["storage"],
                }
            },
            {
                "or": [
                    {
                        "tags": {
                            "name": "env",
                            "operator": "In",
                            "values": ["PROD"],
                        }
                    },
                    {
                        "tags": {
                            "name": "Project",
                            "operator": "In",
                            "values": ["foo"],
                        }
                    },
                ]
            },
        ]
    }

    response = post_query(client, body)

    assert response.status_code == 200
    assert response.json()["properties"]["rows"]


def test_two_groupings_follow_contractual_column_order(client):
    body = deepcopy(CASES_BY_ID["daily-cost-by-resource-group"]["request"])
    body["dataset"]["grouping"] = [
        {"type": "Dimension", "name": "ResourceGroup"},
        {"type": "Tag", "name": "Project"},
    ]

    response = post_query(client, body)

    assert response.status_code == 200
    columns = response.json()["properties"]["columns"]
    assert [column["name"] for column in columns] == [
        "PreTaxCost",
        "ResourceGroup",
        "Project",
        "UsageDate",
        "Currency",
    ]


def test_custom_time_period_respects_time_of_day(client):
    body = deepcopy(CASES_BY_ID["daily-cost-by-resource-group"]["request"])
    body["timePeriod"] = {
        "from": "2024-06-12T12:00:00Z",
        "to": "2024-06-13T00:00:00Z",
    }

    response = post_query(client, body)

    assert response.status_code == 200
    assert response.json()["properties"]["rows"] == []


def test_invalid_skip_token_uses_contract_error(client):
    body = CASES_BY_ID["daily-cost-by-resource-group"]["request"]
    response = client.post(
        f"{QUERY_PATH}?api-version=2025-03-01&$skiptoken=opaque",
        json=body,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "InvalidSkipToken"
