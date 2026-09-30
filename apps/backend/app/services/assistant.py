class AssistantService:
    def answer(self, user_prompt: str, retrieved_chunks: list[dict]) -> dict:
        if not retrieved_chunks:
            content = (
                "No he encontrado contexto relevante para este tenant todavia. "
                "Sube mas documentos o lanza nuevas ingestas para enriquecer la base de conocimiento."
            )
        else:
            snippets = "\n".join(
                f"- [{index}] {chunk['source']}: {chunk['content'][:140]}"
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
