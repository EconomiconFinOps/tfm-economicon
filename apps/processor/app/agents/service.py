from langchain_core.prompts import ChatPromptTemplate

from app.agents.guardrails import (
    parse_and_validate_response,
    prepare_agent_input,
    source_is_supported,
)
from app.agents.prompts import HUMAN_PROMPT, SYSTEM_PROMPT
from app.agents.providers import get_provider
from app.agents.schemas import FinOpsResponse, finops_response_format
from app.core.config import Settings


class AgentRuntime:
    def __init__(self, settings: Settings, provider=None):
        self.settings = settings
        self.provider = provider or get_provider(settings.llm_provider)
        self.response_format = finops_response_format()
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", HUMAN_PROMPT),
            ]
        )

    def invoke(self, job_payload: dict, status: str) -> dict:
        prepared = prepare_agent_input(job_payload, status)
        if not source_is_supported(prepared.source):
            response = self._unsupported_source_response(prepared.source)
            return self._result(response)

        messages = self.prompt.format_messages(
            source=prepared.source,
            status=prepared.status,
            metadata_json=prepared.metadata_json,
        )
        rendered_prompt = "\n".join(message.content for message in messages)
        raw_response = self.provider.invoke(
            rendered_prompt,
            response_format=self.response_format,
        )
        response = parse_and_validate_response(raw_response)
        return self._result(response)

    def _result(self, response: FinOpsResponse) -> dict:
        return {
            "provider": self.settings.llm_provider,
            "model": self.settings.llm_model,
            "response": response.model_dump(mode="json", by_alias=True),
        }

    @staticmethod
    def _unsupported_source_response(source: str) -> FinOpsResponse:
        return FinOpsResponse.model_validate(
            {
                "schema_version": "1.0",
                "status": "unsupported",
                "answer": "La fuente indicada queda fuera del alcance Azure del MVP.",
                "scope": {
                    "cloud": "azure",
                    "data_environment": "simulated",
                    "subscription_ids": [],
                    "period": None,
                },
                "evidence": [],
                "metrics": [],
                "recommendations": [],
                "assumptions": [],
                "limitations": [f"Fuente no soportada: {source}."],
                "next_actions": [
                    "Usar una fuente Azure Cost Management simulada admitida."
                ],
            }
        )

