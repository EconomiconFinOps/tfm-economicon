from app.agents.schemas import FinOpsResponse


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


def get_provider(provider_name: str):
    if provider_name == "mock":
        return MockLLMProvider()
    raise ValueError(f"Unsupported LLM provider: {provider_name}")

