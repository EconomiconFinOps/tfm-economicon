class MockLLMProvider:
    def invoke(self, prompt: str) -> str:
        return (
            "FinOps insight: prioritize rightsizing on idle workloads, validate "
            "commitment coverage and review tenant-level spend drift."
        )


def get_provider(provider_name: str):
    if provider_name == "mock":
        return MockLLMProvider()
    raise ValueError(f"Unsupported LLM provider: {provider_name}")

