from app.agents.schemas import FinOpsResponse
from app.clients.litellm import LiteLLMClient, ProviderError
from app.core.config import Settings


class MockLLMProvider:
    def invoke(self, prompt: str, *, response_format: dict) -> str:
        del prompt, response_format
        return FinOpsResponse.model_validate(
            {
                "schema_version": "1.0",
                "status": "insufficient_data",
                "answer": (
                    "No hay evidencia de costes suficiente para generar un "
                    "analisis FinOps verificable."
                ),
                "scope": {
                    "cloud": "azure",
                    "data_environment": "simulated",
                    "subscription_ids": [],
                    "period": None,
                },
                "evidence": [],
                "metrics": [],
                "recommendations": [],
                "assumptions": [
                    "La ejecucion usa el proveedor mock de desarrollo."
                ],
                "limitations": [
                    "El proveedor mock no consulta costes ni documentos."
                ],
                "next_actions": [
                    "Aportar evidencia de costes o contexto recuperado antes de analizar."
                ],
            }
        ).model_dump_json(by_alias=True)


class LiteLLMProvider:
    def __init__(self, settings: Settings):
        self.client = LiteLLMClient(settings)
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_output_tokens

    def invoke(self, prompt: str, *, response_format: dict) -> str:
        payload = self.client.post("chat/completions", {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": response_format,
            "max_tokens": self.max_tokens,
        })
        try:
            content = payload["choices"][0]["message"]["content"]
            if isinstance(content, str) and content.strip():
                return content
        except (KeyError, IndexError, TypeError):
            pass
        raise ProviderError("invalid_response")


def get_provider(provider_name: str, settings: Settings | None = None):
    if provider_name == "mock":
        return MockLLMProvider()
    if provider_name == "litellm":
        if settings is None:
            raise ValueError("LiteLLM requires explicit settings")
        return LiteLLMProvider(settings)
    raise ValueError(f"Unsupported LLM provider: {provider_name}")
