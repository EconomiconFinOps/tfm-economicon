from langchain_core.prompts import ChatPromptTemplate

from app.agents.providers import get_provider
from app.core.config import Settings


class AgentRuntime:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = get_provider(settings.llm_provider)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a FinOps analyst focused on actionable operational advice."),
                (
                    "human",
                    "Tenant: {tenant_id}\nSource: {source}\nCurrent status: {status}\n"
                    "Metadata: {metadata}\nProduce a short FinOps insight."
                ),
            ]
        )

    def invoke(self, job_payload: dict, status: str) -> dict:
        messages = self.prompt.format_messages(
            tenant_id=job_payload["tenant_id"],
            source=job_payload["source"],
            status=status,
            metadata=job_payload.get("metadata", {}),
        )
        rendered_prompt = "\n".join(message.content for message in messages)
        insight = self.provider.invoke(rendered_prompt)
        return {
            "provider": self.settings.llm_provider,
            "insight": insight,
        }

