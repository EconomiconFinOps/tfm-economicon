"""Verify the processor-packaged summary contract and prepare bounded QA lots.

This module does not import processor, dispatch inference, install artifacts or
select canonical SQL sources. Its caller supplies an authorized ordered snapshot.
"""

from dataclasses import dataclass, field
from app.core.context_budget import budget, SUMMARY_BYTES
import hashlib, json, re
from pathlib import Path
from app.schemas.chat import canonical, _validate
from app.core.chat_resources import TOKENIZER_SHA, TOKENIZER_REVISION

SCHEMA_SHA = "72404e66533f03268bf53727e7ed01cad00a71c31ad483f823ee4c3c8e06783e"
INPUT_SHA = "46afc2e372abbf117956a709047a7dc036f17a0836bc9acfeffc21553611f1d3"
ASSEMBLER_SHA = "77dee48efa01bc0ca1c09685a3b23cfedc2f0f9d2dbfa9bf3200bee2e9d5fd1f"
POLICY_SHA = "e8c326b37b86bbdb30dcb2202d739e33de6d8d1169567449b62d8a977dd1c9e8"
BUDGETS = {
    "input_total_tokens": 4096,
    "output_tokens": 800,
    "payload_tokens": 768,
    "content_tokens": 512,
}
V3_BUDGETS = {
    "input_total_tokens": 1048576,
    "output_tokens": 10000,
    "payload_tokens": 8192,
    "content_tokens": 6144,
}
V3_MANIFEST_SHA = "0284aef330cf790e3b2035b155a502c48b1c997ec322fefc57dce1608c10ccc9"
LEGACY_MANIFEST_SHA = "f724d3fc8379d7926c667c9f5f3c43ed9074d34080a11fb5a1c76b2cd43b8b94"
PAIR_KEYS = {"question_ref", "question", "answer_ref", "answer"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate summary resource field.")
        result[key] = value
    return result


@dataclass(frozen=True)
class BackendSummaryResources:
    summary_version: str
    system: str
    input_template: str
    manifest_bytes: bytes
    schema_bytes: bytes
    tokenizer_sha256: str
    response_schema_sha256: str
    _tokenizer: object
    context_budget: dict = field(default_factory=lambda: budget("summary"))
    legacy_resources: tuple = field(default=(), repr=False)

    @property
    def contract(self):
        manifest = json.loads(self.manifest_bytes)
        return {
            "prompt_version": self.summary_version,
            "schema_sha256": self.response_schema_sha256,
            "tokenizer_sha256": self.tokenizer_sha256,
            "policy_version": manifest["kind"] + ":" + manifest["policy_sha256"],
        }

    def resources_for_contract(self, contract):
        for resources in (self,) + self.legacy_resources:
            if contract == resources.contract:
                return resources
        raise ValueError("Unsupported summary origin contract.")

    @property
    def response_schema(self):
        return json.loads(self.schema_bytes)

    def count(self, value):
        return len(self._tokenizer.encode(value, add_special_tokens=False).ids)

    def validate_payload(self, value):
        schema = self.response_schema
        _validate(value, schema, schema)
        if not value["topics"] and not value["facts"]:
            raise ValueError("Summary has no retained dialogue.")
        text = "\n".join(
            [x["text"] for x in value["topics"]]
            + [x["quote"] for x in value["facts"]]
            + value["limitations"]
        )
        limits = json.loads(self.manifest_bytes)["budgets"]
        if (
            self.count(text) > limits["content_tokens"]
            or self.count(canonical(value)) > limits["payload_tokens"]
        ):
            raise ValueError("Summary payload token limit.")
        return json.loads(canonical(value))

    def prepare_lot(self, previous_summary, pairs, envelope=None):
        if not isinstance(pairs, list):
            raise ValueError("Invalid QA snapshot.")
        refs = set()
        for pair in pairs:
            if not isinstance(pair, dict) or set(pair) != PAIR_KEYS:
                raise ValueError("Only QA fields are allowed.")
            for role in ["question", "answer"]:
                ref = pair[role + "_ref"]
                text = pair[role]
                if (
                    not isinstance(ref, str)
                    or re.fullmatch(
                        ("q" if role == "question" else "a") + "-[0-9a-f]{64}", ref
                    )
                    is None
                    or ref in refs
                    or not isinstance(text, str)
                    or not text
                ):
                    raise ValueError("Invalid QA source.")
                refs.add(ref)
        previous = (
            None
            if previous_summary is None
            else self.validate_payload(previous_summary)
        )
        eligible = pairs[:-4] if len(pairs) > 4 else []
        selected = []
        reason = None
        tokens = 0
        messages = []
        payload = None
        if not eligible:
            reason = "recent_pairs_only"
        for pair in eligible:
            candidate = {"previous_summary": previous, "pairs": selected + [pair]}
            candidate_messages = [
                {"role": "system", "content": self.system + "\n" + self.input_template},
                {
                    "role": "user",
                    "content": "UNTRUSTED_SUMMARY_INPUT\n" + canonical(candidate),
                },
            ]
            measured = (
                self.count(canonical(candidate_messages))
                + self.count(self.schema_bytes.decode("utf-8"))
                + 1024
            )
            wire = (
                envelope(candidate, len(selected) + 1)
                if envelope
                else {"messages": candidate_messages, "schema": self.response_schema}
            )
            if (
                measured + self.context_budget["output_tokens"]
                > self.context_budget["context_tokens"]
                or len(canonical(wire).encode()) > SUMMARY_BYTES
            ):
                reason = "pending_pair_too_large"
                break
            selected.append(pair)
            payload = candidate
            messages = candidate_messages
            tokens = measured
        if payload is not None:
            payload = json.loads(canonical(payload))
        return {
            "payload": payload,
            "messages": messages,
            "input_total_tokens": tokens,
            "input_hash": (
                sha(canonical(payload).encode()) if payload is not None else None
            ),
            "selected_pairs": len(selected),
            "pending_pairs": len(eligible) - len(selected),
            "recent_reserved": min(4, len(pairs)),
            "reason": reason,
            "wrapper_margin_tokens": 1024,
        }

    def verify_descriptor(self, value):
        expected = {
            "v": 2,
            "summary_version": self.summary_version,
            "manifest_sha256": sha(self.manifest_bytes),
            "tokenizer_sha256": self.tokenizer_sha256,
            "response_schema_sha256": self.response_schema_sha256,
            "context_budget": self.context_budget,
        }
        if not isinstance(value, dict) or any(
            type(value.get(k)) is not type(v) or value.get(k) != v
            for k, v in expected.items()
        ):
            raise ValueError("Summary contract mismatch.")


def load_resources(directory=None, tokenizer_file=None):
    import tokenizers

    root = Path(directory or "/opt/economicon/summary/v3")
    names = {"system.md", "input.md", "schema.json", "manifest.json"}
    if (
        root.is_symlink()
        or not root.is_dir()
        or {p.name for p in root.iterdir()} != names
    ):
        raise ValueError("Invalid summary bundle.")
    data = {}
    for name in names:
        p = root / name
        limit = 16384 if name == "manifest.json" else 65536
        if p.is_symlink() or not p.is_file() or not 0 < p.stat().st_size <= limit:
            raise ValueError("Invalid summary resource.")
        data[name] = p.read_bytes()
        if not 0 < len(data[name]) <= limit:
            raise ValueError("Summary resource limit.")
    manifest = json.loads(data["manifest.json"], object_pairs_hook=unique)
    version = manifest.get("v")
    if type(version) is not int or version not in (2, 3):
        raise ValueError("Unsupported summary bundle.")
    if version == 3 and sha(data["manifest.json"]) != V3_MANIFEST_SHA:
        raise ValueError("Summary bundle pin mismatch.")
    schema = json.loads(data["schema.json"], object_pairs_hook=unique)
    if (
        sha(data["schema.json"]) != SCHEMA_SHA
        or data["schema.json"] != canonical(schema).encode()
    ):
        raise ValueError("Summary schema differs from authority.")
    expected = {
        "v": version,
        "kind": f"jup-035.summary.v{version}",
        "system_sha256": sha(data["system.md"]),
        "input_sha256": sha(data["input.md"]),
        "response_schema_sha256": SCHEMA_SHA,
        "input_contract": manifest.get("input_contract"),
        "input_contract_sha256": INPUT_SHA,
        "assembler_contract": manifest.get("assembler_contract"),
        "assembler_sha256": ASSEMBLER_SHA,
        "policy": manifest.get("policy"),
        "policy_sha256": POLICY_SHA,
        "tokenizer": {
            "library_version": "0.22.1",
            "revision": TOKENIZER_REVISION,
            "sha256": TOKENIZER_SHA,
            "bytes": 20217442,
        },
        "budgets": V3_BUDGETS if version == 3 else BUDGETS,
    }
    if canonical(manifest) != canonical(expected) or tokenizers.__version__ != "0.22.1":
        raise ValueError("Summary contract mismatch.")
    for key, pin in [
        ("input_contract", INPUT_SHA),
        ("assembler_contract", ASSEMBLER_SHA),
        ("policy", POLICY_SHA),
    ]:
        if sha(canonical(manifest[key]).encode()) != pin:
            raise ValueError("Summary policy mismatch.")
    asset = Path(tokenizer_file or "/opt/economicon/chat/v3/tokenizer.json")
    if (
        asset.is_symlink()
        or not asset.is_file()
        or asset.stat().st_size != 20217442
        or sha(asset.read_bytes()) != TOKENIZER_SHA
    ):
        raise ValueError("Summary tokenizer mismatch.")
    counter = tokenizers.Tokenizer.from_file(str(asset))
    if sha(asset.read_bytes()) != TOKENIZER_SHA or any(
        (root / n).is_symlink() or (root / n).read_bytes() != raw
        for n, raw in data.items()
    ):
        raise ValueError("Summary resource changed during load.")
    counter.no_truncation()
    counter.no_padding()
    counter.encode("Control € 漢字", add_special_tokens=False)
    frozen = canonical(manifest).encode()
    legacy = ()
    if version == 3:
        previous = load_resources(root.parent / "v2", asset)
        if sha(previous.manifest_bytes) != LEGACY_MANIFEST_SHA:
            raise ValueError("Legacy summary pin mismatch.")
        legacy = (previous,)
    return BackendSummaryResources(
        f"jup-035.summary.v{version}:" + sha(frozen),
        data["system.md"].decode("utf-8"),
        data["input.md"].decode("utf-8"),
        frozen,
        data["schema.json"],
        TOKENIZER_SHA,
        SCHEMA_SHA,
        counter,
        legacy_resources=legacy,
    )
