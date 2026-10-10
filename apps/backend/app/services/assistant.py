class AssistantService:
    def __init__(self, provider=None):
        self.provider = provider

    def answer_cost(self, user_prompt: str, tool_output: dict) -> dict:
        # Only a server-side, tenant-scoped adapter may provide this evidence.
        # Keep its complete snapshot and limitations alongside the generated prose.
        if self.provider is None:
            return tool_output
        evidence = tool_output["cost_evidence"]
        output = self.answer(user_prompt, [{"chunk_id": evidence["id"],
            "content": tool_output["content"], "evidence_kind": "cost"}])
        return {**output, "cost_evidence": evidence}

    def answer(self, user_prompt: str, retrieved_chunks: list[dict]) -> dict:
        if self.provider is not None:
            from app.services.chat_guardrails import GeneratedAnswer, SYSTEM_PROMPT, prepare_context, validate_answer
            if not retrieved_chunks:
                return validate_answer('{"status":"insufficient_data","statements":[]}', [])
            raw = self.provider.generate(SYSTEM_PROMPT, prepare_context(user_prompt, retrieved_chunks),
                                         GeneratedAnswer.model_json_schema())
            return validate_answer(raw, retrieved_chunks)
        if not retrieved_chunks:
            content = (
                "No he encontrado contexto relevante para este tenant todavia. "
                "Sube mas documentos o lanza nuevas ingestas para enriquecer la base de conocimiento."
            )
        else:
            snippets = "\n".join(
                f"- [{index}] {chunk['source'].strip()}: {chunk['content'][:140]}"
                for index, chunk in enumerate(retrieved_chunks[:3], start=1)
            )
            content = (
                "He encontrado contexto relacionado para tu consulta.\n"
                f"Pregunta: {user_prompt}\n"
                "Contexto mas relevante:\n"
                f"{snippets}"
            )

        return {
            "content": content,
            "citations": [chunk["chunk_id"] for chunk in retrieved_chunks[:3]],
        }
