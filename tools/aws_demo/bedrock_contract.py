"""Offline contract for the reviewed EU Bedrock system profiles.

Metadata must be checked against this contract before a future deployment.
This module never opens an AWS session or invokes a model.
"""

import re


PROFILES = frozenset(("eu.amazon.nova-micro-v1:0", "eu.amazon.nova-lite-v1:0"))
DESTINATIONS = ("eu-central-1", "eu-north-1", "eu-south-2", "eu-west-1", "eu-west-3")


def expected_profile(account_id: str, profile_id: str) -> dict:
    if not isinstance(account_id, str) or not re.fullmatch(r"[0-9]{12}", account_id):
        raise ValueError("Expected a twelve-digit AWS account ID")
    if profile_id not in PROFILES:
        raise ValueError("Unreviewed Bedrock inference profile")
    return {
        "arn": f"arn:aws:bedrock:eu-south-2:{account_id}:inference-profile/{profile_id}",
        "models": [
            f"arn:aws:bedrock:{region}::foundation-model/{profile_id.removeprefix('eu.')}"
            for region in DESTINATIONS
        ],
    }


def validate_profile(value: dict, account_id: str, profile_id: str) -> dict:
    expected = expected_profile(account_id, profile_id)
    if not isinstance(value, dict) or any(
        value.get(key) != required
        for key, required in {
            "inferenceProfileArn": expected["arn"],
            "inferenceProfileId": profile_id,
            "status": "ACTIVE",
            "type": "SYSTEM_DEFINED",
        }.items()
    ):
        raise ValueError("Bedrock profile identity or status differs from the reviewed contract")
    models = value.get("models")
    if not isinstance(models, list) or not all(
        isinstance(model, dict) and isinstance(model.get("modelArn"), str)
        for model in models
    ):
        raise ValueError("Invalid Bedrock model destinations")
    arns = [model["modelArn"] for model in models]
    if len(arns) != len(expected["models"]) or set(arns) != set(expected["models"]):
        raise ValueError("Bedrock destinations differ from the reviewed contract")
    return expected
