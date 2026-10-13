"""Private grounding constraints: no semantic keyword classifier."""

import pytest

from app.agents.schemas import chat_provider_schema
from app.core.chat_segments import render_response


SOURCE = {"id": "doc-1", "kind": "corpus", "title": "Policy",
          "source": "policy.md", "content": "Recommendations require evidence."}


def response(segment, evidence=None):
    return {"answer": [segment], "evidence": evidence or [], "metrics": [],
            "recommendations": [], "assumptions": [], "limitations": [],
            "next_actions": []}


def test_nonactionable_schema_matches_final_validator():
    schema = chat_provider_schema(financial_metrics_allowed=True,
                                  authorized_evidence=[SOURCE])
    branch = schema["anyOf"][1]["properties"]
    assert branch["metrics"]["maxItems"] == 0
    assert branch["recommendations"]["maxItems"] == 0
    assert branch["evidence"].get("maxItems", 20) > 0


def test_documentary_text_requires_selected_literal_support():
    evidence = {k: SOURCE[k] for k in ("id", "kind", "title", "source")}
    evidence["support_quote"] = SOURCE["content"]
    value = response({"text": "Evidence is required.", "basis": "documentary",
                      "evidence_ids": ["doc-1"]}, [evidence])
    assert render_response(value, [SOURCE], require_grounding=True)["answer"] == "Evidence is required."
    value["evidence"] = []
    with pytest.raises(ValueError, match="Documentary support missing"):
        render_response(value, [SOURCE], require_grounding=True)


def test_user_only_answer_cannot_select_unused_corpus():
    segment = {"text": "There is no coverage in your example.",
               "basis": "non_documentary", "evidence_ids": []}
    assert render_response(response(segment), [SOURCE], require_grounding=True)["evidence"] == []
    with pytest.raises(ValueError, match="Unused documentary evidence"):
        render_response(response(segment, [{**SOURCE, "support_quote": SOURCE["content"]}]),
                        [SOURCE], require_grounding=True)


@pytest.mark.parametrize("ids,quote", [
    (["foreign"], SOURCE["content"]), (["doc-1", "doc-1"], SOURCE["content"]),
    (["doc-1"], "Invented passage"),
])
def test_invalid_provenance_is_not_repaired(ids, quote):
    value = response({"text": "Policy.", "basis": "documentary", "evidence_ids": ids},
                     [{**SOURCE, "support_quote": quote}])
    with pytest.raises(ValueError):
        render_response(value, [SOURCE], require_grounding=True)


def test_corrective_generation_reuses_sources_without_retrieval(monkeypatch):
    import asyncio
    import json
    import time
    from test_chat_auto_jup035 import provider, wire, retrieval_context, empty_result
    from test_chat_gateway_jup035 import _provider, ANSWER

    gateway, requests = provider(monkeypatch, [wire({"content": json.dumps(_provider(ANSWER))})])
    async def run():
        records = [r async for r in gateway(
            retrieval_context(), time.time() + 100,
            correction={"code": "unused_documentary_evidence", "cache": {"result": empty_result()}},
        )]
        assert not any(r["type"] == "tool_call" for r in records)
        assert records[-1]["type"] == "candidate"
    asyncio.run(run())
    assert len(requests) == 1
    assert requests[0]["messages"][-1]["content"].startswith("SERVER_RESPONSE_CORRECTION_V1:")
    assert requests[0]["num_retries"] == 0


@pytest.mark.parametrize("change", ["signature", "tenant", "attempt", "code", "missing"])
def test_private_correction_must_match_durable_grant(private, change):
    import copy
    import json
    from sqlalchemy import text
    from test_chat_private_jup035 import claim, signed, run, KEY
    from app.core.chat_correction import seal_cache

    value = claim()
    cache = seal_cache(value, {}, {}, KEY)
    grant = {"code": "unused_documentary_evidence", "claimed": True,
             "attempt_id": value["attempt_id"], "number": value["number"],
             "deadline": value["deadline"], "source_attempt": "old"}
    with private[2].begin() as connection:
        connection.execute(text("UPDATE chat_operations SET private_control=:value"),
                           {"value": json.dumps({"boot_id": value["boot_id"],
                            "capability": value["capability"], "correction": grant, "recovery": cache})})
    value["correction"] = {**grant, "cache": copy.deepcopy(cache)}
    if change == "signature":
        value["correction"]["cache"]["signature"] = "0" * 64
    elif change == "tenant":
        value["correction"]["cache"]["identity"]["tenant_id"] = "other"
    elif change == "attempt":
        value["correction"]["attempt_id"] = "other"
    elif change == "code":
        value["correction"]["code"] = "arbitrary"
    else:
        value.pop("correction")
    async def scenario(client):
        raw = json.dumps(value).encode()
        result = await client.post("/internal/chat/v2/attempts", content=raw,
                                   headers=signed("POST", "/internal/chat/v2/attempts", raw))
        assert result.status_code in (404, 409)
        assert private[3] == []
    run(private[0], scenario)


from test_chat_private_jup035 import private


def test_correction_instruction_is_counted_against_remaining_context():
    from app.core.chat_resources import ChatResources, TokenBudgetExceeded, canonical
    from app.core.chat_correction import correction_message
    from app.agents.schemas import chat_provider_schema

    messages = [{"role": "system", "content": "System"},
                {"role": "user", "content": 'UNTRUSTED_CURRENT_CONTEXT\n{"question":"Question"}'}]
    schema = chat_provider_schema(financial_metrics_allowed=False,
                                  authorized_evidence=[], quantities=[], rules=[])
    total = len(canonical(messages).decode()) + len(canonical(schema).decode())

    class Resource:
        system = "System"
        context_budget = {"output_tokens": 6400, "context_tokens": total + 1024 + 6400}
        count = staticmethod(len)
        check_messages = ChatResources.check_messages

        def validate_tool_result(self, context, assistant, result):
            return copy.deepcopy(messages)

    import copy
    resource = Resource()
    resource.check_messages(messages, schema)
    correction = {"code": "unused_documentary_evidence",
                  "cache": {"result": {}, "effective": {"authorized_evidence": []}}}
    with pytest.raises(TokenBudgetExceeded):
        ChatResources.validate_correction(
            resource, {"financial_metrics_allowed": False, "messages": messages}, correction)
    assert correction_message(correction["code"])["content"].startswith(
        "SERVER_RESPONSE_CORRECTION_V1:")
