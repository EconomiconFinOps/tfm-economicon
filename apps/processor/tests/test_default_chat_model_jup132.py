"""Versioned tokenizer compatibility, offline and without rewriting history."""
import copy
import json
import os
from pathlib import Path

import pytest
from tokenizers import Tokenizer
from app.core.chat_resources import load_resources as chat_resources
from app.core.summary_resources import load_resources as summary_resources

ROOT = Path(__file__).resolve().parents[1] / "app/agents/prompt_resources/jup035"


def test_flash_active_and_historical_summary_contracts_remain_distinct():
    flash = Path(os.getenv("JUP132_FLASH_TOKENIZER", ROOT / "chat/v4/tokenizer.json"))
    legacy = Path(os.getenv("JUP132_LEGACY_TOKENIZER", ROOT / "chat/v2/tokenizer.json"))
    active = summary_resources(ROOT / "summary/v4", flash, legacy)
    assert active.summary_version.startswith("jup-035.summary.v4:")
    assert active.tokenizer_sha256 == "c90dfa01249db1be4245780a052ede752e1361c612ac6d08e2bdada7d599476b"
    payload = {"v": 2, "topics": [], "facts": [], "limitations": ["Ejemplo sintético"]}
    original = copy.deepcopy(payload)
    for version in (2, 3):
        old = summary_resources(ROOT / f"summary/v{version}", legacy)
        reader = active.resources_for_contract(old.contract)
        assert reader.contract == old.contract
        assert reader.tokenizer_sha256 != active.tokenizer_sha256
        assert reader.validate_payload(payload) == payload
        with pytest.raises(ValueError, match="read-only"):
            reader.check_generation()
    active.check_generation()
    assert active.validate_payload(payload) == payload == original
    text = "Control offline: español, euros y contexto histórico."
    assert active.count(text) == len(Tokenizer.from_file(str(flash)).encode(text, add_special_tokens=False).ids)
    manifest = json.loads(active.manifest_bytes)
    assert manifest["budgets"] == {"input_total_tokens": 1048576, "output_tokens": 10000,
                                  "payload_tokens": 8192, "content_tokens": 6144}
    invalid = dict(active.contract, tokenizer_sha256="0" * 64)
    with pytest.raises(ValueError):
        active.resources_for_contract(invalid)


def test_new_chat_requires_flash_and_rejects_legacy_asset():
    flash = Path(os.getenv("JUP132_FLASH_TOKENIZER", ROOT / "chat/v4/tokenizer.json"))
    legacy = Path(os.getenv("JUP132_LEGACY_TOKENIZER", ROOT / "chat/v2/tokenizer.json"))
    resources = chat_resources(ROOT / "chat/v4", flash)
    assert resources.prompt_version.startswith("jup-035.chat.v4:")
    assert json.loads(resources.manifest_bytes)["budgets"]["output_tokens"] == 11000
    with pytest.raises(ValueError):
        chat_resources(ROOT / "chat/v4", legacy)
