"""JUP-022: the backend and the processor must agree on the embedding alias, dimension and failure categories."""
import re
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings
from app.services.embedding_provider import PROVIDER_ERROR_CATEGORIES

PROCESSOR = Path(__file__).resolve().parents[2] / "processor" / "app"
CONFIG = PROCESSOR / "core" / "config.py"
CLIENT = PROCESSOR / "clients" / "litellm.py"


def processor_alias(config_source: str) -> str:
    return re.search(r'embedding_model:\s*str\s*=\s*"([^"]+)"', config_source).group(1)


def processor_dimension(config_source: str) -> int:
    return int(re.search(r"embedding_dimension\s*!=\s*(\d+)", config_source).group(1))


def processor_categories(client_source: str) -> set[str]:
    block = re.search(r"self\.category\s*=\s*category if category in \{(.*?)\}\s*else", client_source, re.S)
    return set(re.findall(r'"([a-z_]+)"', block.group(1)))


def backend_alias() -> str:
    return Settings.model_fields["embedding_model"].default


def backend_dimension() -> int:
    for candidate in (1536, 1535, 8):
        try:
            Settings(_env_file=None, embedding_provider="litellm", embedding_dimension=candidate,
                     litellm_api_key=SecretStr("k"), runtime_environment="test")
            return candidate
        except ValidationError:
            continue
    raise AssertionError("no accepted litellm dimension")


def differences(config_source: str, client_source: str) -> list[str]:
    found = []
    if processor_alias(config_source) != backend_alias():
        found.append(f"alias: processor {processor_alias(config_source)!r}, backend {backend_alias()!r}")
    if processor_dimension(config_source) != backend_dimension():
        found.append(f"dimension: processor {processor_dimension(config_source)}, backend {backend_dimension()}")
    if processor_categories(client_source) != set(PROVIDER_ERROR_CATEGORIES):
        found.append(f"categories: processor {sorted(processor_categories(client_source))}, backend {sorted(PROVIDER_ERROR_CATEGORIES)}")
    return found


CATEGORIES_SOURCE = (
    'self.category = category if category in {\n'
    + ", ".join(f'"{name}"' for name in sorted(PROVIDER_ERROR_CATEGORIES))
    + '\n} else "transport"'
)


def test_alias_and_dimension_match_the_processor():
    source = CONFIG.read_text(encoding="utf8")
    assert processor_alias(source) == backend_alias() == "economicon-embedding"
    assert processor_dimension(source) == backend_dimension() == 1536


@pytest.mark.skipif(not CLIENT.exists(), reason="the processor LiteLLM client is not in this branch yet (JUP-023)")
def test_failure_categories_match_the_processor_client():
    assert processor_categories(CLIENT.read_text(encoding="utf8")) == set(PROVIDER_ERROR_CATEGORIES)


def test_no_difference_is_reported_when_both_services_agree():
    assert differences(CONFIG.read_text(encoding="utf8"), CATEGORIES_SOURCE) == []


def test_a_processor_alias_that_changes_alone_is_reported_by_name():
    source = CONFIG.read_text(encoding="utf8").replace('embedding_model: str = "economicon-embedding"', 'embedding_model: str = "otro-alias"')
    assert any(item.startswith("alias:") and "otro-alias" in item for item in differences(source, CATEGORIES_SOURCE))


def test_a_processor_dimension_that_changes_alone_is_reported_by_name():
    source = CONFIG.read_text(encoding="utf8").replace("embedding_dimension != 1536", "embedding_dimension != 3072")
    assert any(item.startswith("dimension:") and "3072" in item for item in differences(source, CATEGORIES_SOURCE))


def test_a_category_that_changes_in_one_service_alone_is_reported_by_name():
    added = CATEGORIES_SOURCE.replace('"timeout"', '"timeout", "quota"')
    removed = CATEGORIES_SOURCE.replace('"timeout", ', "").replace('"timeout"', "")
    assert any(item.startswith("categories:") and "quota" in item for item in differences(CONFIG.read_text(encoding="utf8"), added))
    assert any(item.startswith("categories:") for item in differences(CONFIG.read_text(encoding="utf8"), removed))
