"""Explicit local fixtures, never a fallback or a semantic inference provider."""

import asyncio
import json
import time

from app.agents.providers import MockLLMProvider
from app.agents.schemas import assemble_chat_response


def require_local_mock(settings):
    if (
        settings.llm_provider != "mock"
        or settings.runtime_environment not in {"development", "test"}
        or settings.ai_execution_mode not in {"development", "test"}
    ):
        raise ValueError("Mock chat requires explicit development/test configuration.")


class MockChatGateway:
    async def __call__(self, context, deadline):
        if deadline <= time.time() + 5:
            yield {"type": "error", "category": "timeout"}
            return
        result = json.loads(MockLLMProvider().invoke("", response_format={}))
        del result["scope"]["period"]
        del result["scope"]["subscription_ids"]
        result = assemble_chat_response(
            result,
            context.get("response_period"),
            context.get("response_subscriptions", []),
        )
        yield {"type": "delta", "text": result["answer"]}
        await asyncio.sleep(0)
        if deadline <= time.time() + 5:
            yield {"type": "error", "category": "timeout"}
            return
        yield {
            "type": "candidate",
            "result": result,
            "finish_reason": "stop",
            "usage": None,
        }


class MockSummaryGateway:
    def __init__(self):
        self.jobs = {}

    async def dispatch(self, job_id, messages, resources, deadline):
        from app.clients.summary_gateway import SummaryGatewayError

        if deadline <= time.time():
            raise SummaryGatewayError(504, "summary_deadline")
        if job_id in self.jobs:
            raise SummaryGatewayError(409, "summary_job_replayed")
        cancelled = asyncio.Event()
        self.jobs[job_id] = cancelled
        try:
            await asyncio.sleep(0)
            if cancelled.is_set():
                raise SummaryGatewayError(503, "summary_cancelled")
            content = messages[1]["content"]
            label = "UNTRUSTED_SUMMARY_INPUT\n"
            if not content.startswith(label):
                raise ValueError("Summary input label.")
            payload = json.loads(content[len(label) :])
            resources.prepare_input(payload)
            previous = payload["previous_summary"] or {
                "topics": [],
                "facts": [],
                "limitations": [],
            }
            facts = list(previous["facts"])
            # Keep whole literal statements only: never truncate away a negation.
            for pair in payload["pairs"]:
                for role in ("question", "answer"):
                    if len(pair[role]) <= 512:
                        facts.append(
                            {"quote": pair[role], "source_ref": pair[role + "_ref"]}
                        )
            output = resources.validate_payload(
                {
                    "v": 2,
                    "topics": previous["topics"],
                    "facts": facts[-8:],
                    "limitations": previous["limitations"][-3:]
                    + [
                        "Resumen mock: seleccion literal limitada; puede omitir contenido. "
                        "No sustituye el historial original ni acredita una sintesis semantica."
                    ],
                }
            )
            if deadline <= time.time():
                raise SummaryGatewayError(504, "summary_deadline")
            return {
                "output": output,
                "usage": None,
                "cost": None,
                "observed_model": "mock",
            }
        finally:
            self.jobs.pop(job_id, None)

    def cancel(self, job_id):
        if job_id in self.jobs:
            self.jobs[job_id].set()

    async def close(self):
        for cancelled in self.jobs.values():
            cancelled.set()
        await asyncio.sleep(0)
