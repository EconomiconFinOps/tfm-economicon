"""Internal, dormant summary CAS over the canonical conversation row.

SQL retries reuse a fixed candidate; no method dispatches inference. Production
installation is reserved for SummaryService after authenticated validation.
"""

from dataclasses import dataclass, field
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import text
from app.db import chat_history, chat_summary
from app.db.chat_repository import ChatError

digest = chat_summary.digest
dumps = chat_history.dumps
loads = chat_history.loads


def opaque(scope, role, identifier):
    return ("q-" if role == "user" else "a-") + digest(
        {"scope": scope, "role": role, "id": identifier}
    )


def ledger(document):
    pairs, excluded = chat_history.latest_pairs(document, for_model=True)
    by_id = {x["id"]: x for x in document["messages"]}
    refs = []
    qa = []
    for pair in pairs:
        question, answer = by_id[pair["question_id"]], by_id[pair["answer_id"]]
        refs.append(
            {
                "question_id": question["id"],
                "answer_id": answer["id"],
                "question_ordinal": question["ordinal"],
                "answer_ordinal": answer["ordinal"],
                "question_sha256": digest(question),
                "answer_sha256": digest(answer),
            }
        )
        qa.append(
            {
                "question_ref": opaque(document["identity"], "user", question["id"]),
                "question": question["content"],
                "answer_ref": opaque(document["identity"], "assistant", answer["id"]),
                "answer": answer["content"],
            }
        )
    return refs, qa, excluded


@dataclass(frozen=True)
class SummarySnapshot:
    scope_bytes: str
    document_bytes: str
    parent_raw: str | None
    parent_hash: str | None
    epoch: str
    contract_bytes: str
    covered_pairs: int
    previous_bytes: str | None
    recent_reserved: int
    resources: object = field(repr=False, compare=False)

    @property
    def scope(self):
        return loads(self.scope_bytes)

    @property
    def document(self):
        return loads(self.document_bytes)

    @property
    def contract(self):
        return loads(self.contract_bytes)

    @property
    def previous_payload_used(self):
        return None if self.previous_bytes is None else loads(self.previous_bytes)

    @property
    def new_pairs(self):
        _, qa, _ = ledger(self.document)
        return qa[self.covered_pairs : max(self.covered_pairs, len(qa) - 4)]

    @property
    def token(self):
        return digest(
            {
                "scope": self.scope,
                "document": self.document,
                "parent_hash": self.parent_hash,
                "epoch": self.epoch,
                "contract": self.contract,
                "covered_pairs": self.covered_pairs,
                "previous": self.previous_payload_used,
            }
        )


@dataclass(frozen=True)
class SummaryCandidate:
    artifact_id: str
    text_sha256: str
    contract_bytes: str
    artifact_bytes: str
    snapshot_token: str
    processed_pairs: int

    @property
    def artifact(self):
        return loads(self.artifact_bytes)


class SummaryRepository:
    def __init__(self, repository):
        self.repository = repository

    def _read(self, connection, scope):
        row = connection.execute(
            text(
                "SELECT CAST(dialogue_history AS TEXT),CAST(dialogue_summary AS TEXT) FROM conversations "
                "WHERE id=:conversation_id AND tenant_id=:tenant_id AND user_id=:user_id"
            ),
            scope,
        ).first()
        if row is None:
            raise ChatError(404, "not_found")
        document = loads(row[0])
        chat_history.validate(document, scope)
        return document, row[1]

    def _state(self, raw, document, scope):
        if raw is None:
            return None, "summary_absent"
        try:
            state = loads(raw)
            reason = chat_summary._header_reason(state, scope)
            if reason is None:
                reason = chat_summary._artifact_reason(state, document, scope)
            return state, reason
        except (ValueError, TypeError, KeyError, OverflowError):
            return None, "invalid_summary"

    def _view(self, document, raw, scope, contract, resources):
        state, reason = self._state(raw, document, scope)
        refs, _, excluded = ledger(document)
        valid = reason is None and state is not None and state["validity"]["valid"]
        covered = len(state["artifact"]["source_refs"]) if valid else 0
        payload = None
        if valid:
            if resources is None:
                reason = "summary_validator_unavailable"
            elif contract != resources.contract:
                reason = "summary_contract_mismatch"
            else:
                try:
                    origin = resources.resources_for_contract(
                        state["artifact"]["contract"]
                    )
                    payload = origin.validate_payload(state["artifact"]["exact_output"])
                except (ValueError, TypeError, KeyError):
                    reason = "summary_payload_invalid"
        elif state is not None and reason is None:
            reason = state["validity"]["reason"]
        return {
            "source_valid": bool(valid),
            "consumable": payload is not None,
            "payload": payload,
            "reason": reason,
            "coverage": {
                "processed_pairs": covered,
                "pending_pairs": max(0, len(refs) - 4 - covered),
                "recent_reserved": min(4, len(refs)),
                "excluded": excluded,
            },
        }

    def view(self, scope, contract, resources=None):
        def read(connection):
            document, raw = self._read(connection, scope)
            return self._view(document, raw, scope, contract, resources)

        return self.repository._transaction(scope, read)

    def snapshot(self, scope, contract, resources=None):
        if not chat_summary._closed(contract, chat_summary.CONTRACT_KEYS):
            raise ChatError(503, "summary_contract_invalid")
        stable_epoch = str(uuid4())

        def read(connection):
            document, raw = self._read(connection, scope)
            state, reason = self._state(raw, document, scope)
            view = self._view(document, raw, scope, contract, resources)
            previous = view["payload"] if view["consumable"] else None
            covered = view["coverage"]["processed_pairs"] if previous is not None else 0
            epoch = (
                state["lineage_epoch"]
                if state is not None
                and reason is None
                and (previous is not None or not state["validity"]["valid"])
                else stable_epoch
            )
            return SummarySnapshot(
                dumps(scope),
                dumps(document),
                raw,
                None if raw is None else digest(loads(raw)),
                epoch,
                dumps(contract),
                covered,
                None if previous is None else dumps(previous),
                view["coverage"]["recent_reserved"],
                resources,
            )

        return self.repository._transaction(scope, read)

    def candidate(self, snapshot, output, receipt, processed_pairs):
        try:
            if (
                not isinstance(snapshot, SummarySnapshot)
                or snapshot.resources is None
                or type(processed_pairs) is not int
                or not 0 < processed_pairs <= len(snapshot.new_pairs)
            ):
                raise ValueError("Invalid frontier.")
            normalized = snapshot.resources.validate_payload(output)
            chosen = snapshot.new_pairs[:processed_pairs]
            input_payload = {
                "previous_summary": snapshot.previous_payload_used,
                "pairs": chosen,
            }
            if (
                not isinstance(receipt, dict)
                or type(receipt.get("dispatch_count")) is not int
                or receipt["dispatch_count"] != 1
                or not isinstance(receipt.get("call_id"), str)
                or not receipt["call_id"]
                or receipt.get("input_hash") != digest(input_payload)
                or receipt.get("output_hash") != digest(normalized)
            ):
                raise ValueError("Invalid receipt.")
            refs, qa, excluded = ledger(snapshot.document)
            count = snapshot.covered_pairs + processed_pairs
            covered = refs[:count]
            sources = {
                pair[role + "_ref"]: pair[role]
                for pair in qa[:count]
                for role in ["question", "answer"]
            }
            returned = []
            for topic in normalized["topics"]:
                returned.extend(topic["question_refs"] + topic["answer_refs"])
            for fact in normalized["facts"]:
                returned.append(fact["source_ref"])
                if (
                    fact["source_ref"] not in sources
                    or fact["quote"] not in sources[fact["source_ref"]]
                ):
                    raise ValueError("Nonliteral fact.")
            if any(ref not in sources for ref in returned):
                raise ValueError("Unknown reference.")
            # Confirm total input using the SAME serialization as resources52.
            from app.schemas.chat import canonical

            messages = [
                {
                    "role": "system",
                    "content": snapshot.resources.system
                    + "\n"
                    + snapshot.resources.input_template,
                },
                {
                    "role": "user",
                    "content": "UNTRUSTED_SUMMARY_INPUT\n" + canonical(input_payload),
                },
            ]
            input_tokens = (
                snapshot.resources.count(canonical(messages))
                + snapshot.resources.count(snapshot.resources.schema_bytes.decode())
                + 1024
            )
            if (
                input_tokens + snapshot.resources.context_budget["output_tokens"]
                > snapshot.resources.context_budget["context_tokens"]
            ):
                raise ValueError("Input token limit.")
        except (ValueError, TypeError, KeyError, AttributeError):
            raise ChatError(409, "summary_candidate_invalid") from None
        parent = loads(snapshot.parent_raw) if snapshot.parent_raw is not None else None
        reusable = snapshot.previous_payload_used is not None
        observations = {
            "receipt": deepcopy(receipt),
            "synthetic": receipt.get("synthetic") is True,
            "context_budget": deepcopy(snapshot.resources.context_budget),
            "input_payload": input_payload,
            "input_total_tokens": input_tokens,
            "wrapper_margin_tokens": 1024,
            "payload_tokens": snapshot.resources.count(canonical(normalized)),
            "usage": deepcopy(receipt.get("usage")),
            "cost": deepcopy(receipt.get("cost")),
            "retained_refs": list(dict.fromkeys(returned)),
            "excluded": excluded,
            "previous_fact_omissions": [
                fact
                for fact in (snapshot.previous_payload_used or {}).get("facts", [])
                if fact not in normalized["facts"]
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if parent is not None and not reusable:
            artifact = parent.get("artifact") if isinstance(parent, dict) else None
            if isinstance(artifact, dict):
                artifact = deepcopy(artifact)
                if isinstance(artifact.get("observations"), dict):
                    artifact["observations"].pop("superseded_invalidated", None)
            observations["superseded_invalidated"] = {
                "state_sha256": snapshot.parent_hash,
                "reason": (
                    parent.get("validity", {}).get("reason")
                    if isinstance(parent, dict)
                    else "invalid_summary"
                ),
                "artifact_id": (
                    artifact.get("artifact_id") if isinstance(artifact, dict) else None
                ),
                "artifact": artifact,
            }
        artifact = {
            "artifact_id": str(uuid4()),
            "artifact_revision": (
                parent["artifact"]["artifact_revision"] + 1 if reusable else 1
            ),
            "lineage_epoch": snapshot.epoch,
            "parent_artifact_id": (
                parent["artifact"]["artifact_id"] if reusable else None
            ),
            "parent_artifact_sha256": digest(parent["artifact"]) if reusable else None,
            "previous_payload_used": snapshot.previous_payload_used,
            "source_refs": covered,
            "frontier_processed": deepcopy(covered[-1]),
            "source_selection_hash": digest(
                {"scope": snapshot.scope, "pairs": covered}
            ),
            "exact_output": normalized,
            "text_sha256": digest(normalized),
            "contract": snapshot.contract,
            "observations": observations,
        }
        return SummaryCandidate(
            artifact["artifact_id"],
            artifact["text_sha256"],
            snapshot.contract_bytes,
            dumps(artifact),
            snapshot.token,
            processed_pairs,
        )

    def install(self, scope, snapshot, candidate, control=None):
        if (
            not isinstance(snapshot, SummarySnapshot)
            or not isinstance(candidate, SummaryCandidate)
            or scope != snapshot.scope
            or candidate.snapshot_token != snapshot.token
            or candidate.contract_bytes != snapshot.contract_bytes
        ):
            raise ChatError(409, "summary_candidate_invalid")
        artifact = candidate.artifact
        if (
            artifact["artifact_id"] != candidate.artifact_id
            or artifact["text_sha256"] != candidate.text_sha256
            or artifact["contract"] != snapshot.contract
        ):
            raise ChatError(409, "summary_candidate_invalid")

        def persist(connection):
            document, raw = self._read(connection, scope)
            current_hash = None if raw is None else digest(loads(raw))
            if current_hash != snapshot.parent_hash:
                raise ChatError(409, "summary_stale")
            refs, _, _ = ledger(document)
            count = snapshot.covered_pairs + candidate.processed_pairs
            if (
                candidate.processed_pairs <= 0
                or count > max(0, len(refs) - 4)
                or artifact["source_refs"] != refs[:count]
                or artifact["frontier_processed"] != refs[count - 1]
            ):
                raise ChatError(409, "summary_stale")
            parent = loads(raw) if raw is not None else None
            revision = (
                parent["state_revision"] + 1
                if isinstance(parent, dict)
                and type(parent.get("state_revision")) is int
                and parent["state_revision"] >= 0
                else 1
            )
            state = {
                "v": 2,
                "scope": dict(scope),
                "state_revision": revision,
                "lineage_epoch": snapshot.epoch,
                "validity": {"valid": True, "reason": None},
                "artifact": artifact,
                "invalidation": None,
            }
            if (
                chat_summary._header_reason(state, scope) is not None
                or chat_summary._artifact_reason(state, document, scope) is not None
            ):
                raise ChatError(409, "summary_candidate_invalid")
            predicate = (
                "dialogue_summary IS NULL"
                if raw is None
                else "CAST(dialogue_summary AS TEXT)=:previous"
            )
            result = connection.execute(
                text(
                    "UPDATE conversations SET dialogue_summary=:state WHERE id=:conversation_id "
                    "AND tenant_id=:tenant_id AND user_id=:user_id AND " + predicate
                ),
                {**scope, "state": dumps(state), "previous": raw},
            )
            if result.rowcount != 1:
                raise ChatError(409, "summary_stale")
            if control is not None:
                self.repository.compactions.transition_in(
                    connection,
                    scope,
                    control,
                    state="pending",
                    reason="queued",
                    job=None,
                    owner=None,
                    lease_until=None,
                    parent_hash=digest(state),
                    history_revision=document["revision"],
                )
            return {
                "installed": True,
                "artifact_id": candidate.artifact_id,
                "resolved_commit": False,
            }

        try:
            return self.repository._transaction(scope, persist)
        except ChatError as error:
            if error.code != "commit_unknown":
                raise
            resolution = self.resolve_install(
                scope, candidate.artifact_id, candidate.text_sha256
            )
            if resolution["installed"]:
                return {**resolution, "resolved_commit": True}
            raise error

    def resolve_install(self, scope, artifact_id, candidate_sha):
        def resolve(connection):
            document, raw = self._read(connection, scope)
            state, reason = self._state(raw, document, scope)
            found = (
                reason is None
                and state is not None
                and state["validity"]["valid"]
                and state["artifact"] is not None
                and state["artifact"]["artifact_id"] == artifact_id
                and state["artifact"]["text_sha256"] == candidate_sha
            )
            return {
                "installed": bool(found),
                "artifact_id": artifact_id if found else None,
            }

        return self.repository._transaction(scope, resolve)
