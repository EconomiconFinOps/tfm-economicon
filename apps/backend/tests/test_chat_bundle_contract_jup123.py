"""Load the actual packaged chat contract; no mocked manifest or model call."""
import hashlib
import json
from pathlib import Path

from app.core.chat_resources import ASSEMBLER_SHA, load_resources
from app.schemas.chat import canonical


def test_packaged_bundle_loads_and_advertises_its_canonical_assembler():
    root = Path(__file__).resolve().parents[3]
    chat = root / 'apps/processor/app/agents/prompt_resources/jup035/chat'
    bundle = chat / 'v3'
    resources = load_resources(bundle, chat / 'v2/tokenizer.json')
    manifest = json.loads((bundle / 'manifest.json').read_bytes())
    expected = hashlib.sha256(canonical(manifest['assembler_contract']).encode()).hexdigest()
    assert ASSEMBLER_SHA == manifest['assembler_sha256'] == expected
    assert resources.metadata(0, [])['assembler_sha256'] == expected
    assert resources.prompt_version == 'jup-035.chat.v3:' + hashlib.sha256(
        canonical(manifest).encode()).hexdigest()
