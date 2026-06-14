from app.agents.service import AgentRuntime
from app.core.config import Settings


def test_agent_runtime_returns_mock_insight():
    runtime = AgentRuntime(Settings(llm_provider="mock"))
    result = runtime.invoke(
        {
            "tenant_id": "tenant-core",
            "source": "aws-cur",
            "metadata": {"region": "eu-west-1"},
        },
        status="running",
    )

    assert result["provider"] == "mock"
    assert "FinOps insight" in result["insight"]
