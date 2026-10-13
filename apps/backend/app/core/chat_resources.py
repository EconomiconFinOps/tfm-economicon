"""Backend verifier for the authoritative processor-packaged prompt bundle.

The bundle is copied during image construction; no processor package is imported.
Its version must match the authenticated private descriptor before admission.
"""

import hashlib
import json
from dataclasses import dataclass, field
from app.core.context_budget import budget
from pathlib import Path

from app.schemas.chat import canonical, response_schema, provider_response_schema

TOKENIZER_SHA = "19e773648cb4e65de8660ea6365e10acca112d42a854923df93db4a6f333a82d"
TOKENIZER_REVISION = "a66456a59f21345d1e5e586345c448a9106d29d7"
BASE_SHA = "8e3197acc5cc50b4368d547fbde9ea198cad3364414cec489cd9050f922e6edf"
INPUT_SHA = "a69db50801cfc42eb5b633fc724bbc7e4b3b590326f6713cd6b8616bf0ccfb42"
ASSEMBLER_SHA = "f8a6d36420ebacc4d2c356730c5b4dd8762652f0c05ce44c718af7fe9910d703"
from app.core.chat_expressions import context_question, context_quantities
from app.core.chat_rules import context_rules

# This control is generated locally, never by an LLM. The entire current
# question (bounded to the retrieval input contract) is deterministically used.
DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"const": "search"},
        "query": {"type": "string", "minLength": 1, "maxLength": 2048},
    },
    "required": ["action", "query"],
    "additionalProperties": False,
}


def decision_schema(context):
    return DECISION_SCHEMA


def retrieval_control(context):
    return {"action": "search", "query": context_question(context)[:2048]}


def validate_search_call(value, context=None):
    if (
        not isinstance(value, dict)
        or set(value) != {"action", "query"}
        or value["action"] != "search"
        or not isinstance(value["query"], str)
        or not value["query"].strip()
        or len(value["query"]) > 2048
    ):
        raise ValueError("Invalid retrieval control.")
    if context is not None and value != retrieval_control(context):
        raise ValueError("Retrieval query mismatch.")
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(raw.encode()).hexdigest(), value["query"]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class BackendChatResources:
    system: str
    prompt_version: str
    manifest_bytes: bytes
    schema_text: str
    schema_sha256: str
    _tokenizer: object
    context_budget: dict = field(default_factory=lambda: budget("chat"))

    def count(self, value):
        return len(self._tokenizer.encode(value, add_special_tokens=False).ids)

    def count_messages(
        self,
        messages,
        *,
        financial_metrics_allowed=False,
        authorized_evidence=None,
        calculations=None
    ):
        variable = self.count(canonical(messages[1:]))
        effective = provider_response_schema(
            financial_metrics_allowed=financial_metrics_allowed,
            authorized_evidence=authorized_evidence,
            quantities=context_quantities(
                {"messages": messages, "authorized_evidence": authorized_evidence or []}
            ),
            rules=context_rules(
                {"messages": messages, "authorized_evidence": authorized_evidence or []}
            ),
        )
        total = self.count(canonical(messages)) + self.count(canonical(effective))
        if (
            total + 1024 + self.context_budget["output_tokens"]
            > self.context_budget["context_tokens"]
        ):
            from app.db.chat_repository import ChatError

            raise ChatError(413, "context_token_limit")
        return variable

    def metadata(self, counted, messages):
        manifest = json.loads(self.manifest_bytes)
        return {
            "prompt_version": self.prompt_version,
            "tokenizer_sha256": TOKENIZER_SHA,
            "response_schema_sha256": manifest["response_schema_sha256"],
            "input_contract_sha256": INPUT_SHA,
            "assembler_sha256": ASSEMBLER_SHA,
            "decision_schema_sha256": sha(
                canonical(decision_schema({"messages": messages})).encode()
            ),
            "variable_tokens": counted,
            "context_budget": dict(self.context_budget),
        }

    def verify_descriptor(self, descriptor):
        if any(
            descriptor.get(key) != value
            for key, value in {
                "prompt_version": self.prompt_version,
                "tokenizer_sha256": TOKENIZER_SHA,
                "response_schema_sha256": self.schema_sha256,
                "context_budget": self.context_budget,
            }.items()
        ):
            from app.db.chat_repository import ChatError

            raise ChatError(503, "chat_contract_mismatch")


def load_resources(directory, tokenizer_file=None):
    import tokenizers

    root = Path(directory or "/opt/economicon/chat/v3")
    names = {item.name for item in root.iterdir()}
    if (
        root.is_symlink()
        or not {"system.md", "input.md", "manifest.json"}.issubset(names)
        or names - {"system.md", "input.md", "manifest.json", "tokenizer.json"}
    ):
        raise ValueError("Invalid bundle.")
    limits = {
        "system.md": 65536,
        "input.md": 65536,
        "manifest.json": 16384,
        "tokenizer.json": 20217442,
    }
    for name, limit in limits.items():
        if name == "tokenizer.json" and name not in names:
            continue
        if (root / name).is_symlink() or not 0 < (root / name).stat().st_size <= limit:
            raise ValueError("Invalid resource.")
    manifest = json.loads((root / "manifest.json").read_bytes())
    schema, schema_sha256 = response_schema()
    system = (root / "system.md").read_bytes()
    input_text = (root / "input.md").read_bytes()
    if (
        manifest.get("v") != 3
        or manifest.get("kind") != "jup-035.chat.v3"
        or tokenizers.__version__ != "0.22.1"
        or manifest.get("system_sha256") != sha(system)
        or manifest.get("input_sha256") != sha(input_text)
        or manifest.get("system_base_sha256") != BASE_SHA
        or manifest.get("response_schema_sha256") != schema_sha256
        or manifest.get("provider_response_schema_sha256")
        != sha(
            canonical(provider_response_schema(financial_metrics_allowed=True)).encode()
        )
        or manifest.get("financial_metrics_policy")
        != "server-billing-authority-empty-metrics-v1"
        or manifest.get("response_period_policy") != "server-verified-unique-utc-v1"
        or manifest.get("response_subscriptions_policy")
        != "server-canonical-selection-v1"
        or manifest.get("input_contract_sha256") != INPUT_SHA
        or manifest.get("assembler_sha256") != ASSEMBLER_SHA
        or sha(canonical(manifest["input_contract"]).encode()) != INPUT_SHA
        or sha(canonical(manifest["assembler_contract"]).encode()) != ASSEMBLER_SHA
        or manifest.get("tokenizer")
        != {
            "library_version": "0.22.1",
            "revision": TOKENIZER_REVISION,
            "sha256": TOKENIZER_SHA,
            "bytes": 20217442,
        }
        or manifest.get("budgets")
        != {
            "variable_tokens": 8192,
            "wrapper_margin_tokens": 1024,
            "output_tokens": 6400,
            "model_context_tokens": 1048576,
        }
    ):
        raise ValueError("Bundle contract mismatch.")
    inherited = system.decode("utf-8").partition("\n\nContrato de chat JUP-035 v3:")[0]
    if sha(inherited.encode("utf-8")) != BASE_SHA:
        raise ValueError("Inherited rules mismatch.")
    asset = (
        Path(tokenizer_file)
        if tokenizer_file
        else (
            root / "tokenizer.json"
            if "tokenizer.json" in names
            else root.parent / "v2/tokenizer.json"
        )
    )
    if (
        asset.is_symlink()
        or asset.stat().st_size != 20217442
        or sha(asset.read_bytes()) != TOKENIZER_SHA
    ):
        raise ValueError("Tokenizer mismatch.")
    counter = tokenizers.Tokenizer.from_file(str(asset))
    if sha(asset.read_bytes()) != TOKENIZER_SHA:
        raise ValueError("Tokenizer changed.")
    counter.no_truncation()
    counter.no_padding()
    raw = canonical(manifest).encode("utf-8")
    return BackendChatResources(
        system.decode("utf-8"),
        "jup-035.chat.v3:" + sha(raw),
        raw,
        canonical(provider_response_schema(financial_metrics_allowed=True)),
        schema_sha256,
        counter,
    )
