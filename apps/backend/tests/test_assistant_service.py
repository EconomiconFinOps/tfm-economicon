from app.services.assistant import AssistantService


def test_assistant_service_handles_empty_context():
    service = AssistantService()

    result = service.answer("How are my costs doing?", [])

    assert "No he encontrado contexto relevante" in result["content"]
    assert result["citations"] == []


def test_assistant_service_returns_citations_when_context_exists():
    service = AssistantService()

    result = service.answer(
        "What changed in AWS?",
        [
            {
                "chunk_id": "chunk-1",
                "source": "aws-cur",
                "content": "Reserved instances are underutilized.",
                "distance": 0.12,
            }
        ],
    )

    assert "aws-cur" in result["content"]
    assert result["citations"] == ["chunk-1"]
