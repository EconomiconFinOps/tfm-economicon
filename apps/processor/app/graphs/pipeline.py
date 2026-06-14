from typing import TypedDict

from langgraph.graph import END, StateGraph


class PipelineState(TypedDict, total=False):
    job_id: str
    tenant_id: str
    source: str
    metadata: dict
    artifact_uri: str | None
    text_content: str
    normalized_source: str
    cost_focus: list[str]
    chunks: list[str]
    embedding_result: dict
    insight: dict
    summary: str


class PipelineRunner:
    def __init__(self, agent_runtime, chunker, embedding_provider, vector_store):
        self.agent_runtime = agent_runtime
        self.chunker = chunker
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(PipelineState)
        workflow.add_node("normalize", self._normalize)
        workflow.add_node("chunk", self._chunk)
        workflow.add_node("analyze", self._analyze)
        workflow.add_node("embed_and_store", self._embed_and_store)
        workflow.add_node("summarize", self._summarize)
        workflow.set_entry_point("normalize")
        workflow.add_edge("normalize", "chunk")
        workflow.add_edge("chunk", "analyze")
        workflow.add_edge("analyze", "embed_and_store")
        workflow.add_edge("embed_and_store", "summarize")
        workflow.add_edge("summarize", END)
        return workflow.compile()

    def _normalize(self, state: PipelineState) -> PipelineState:
        source = state["source"].strip().lower()
        return {
            **state,
            "normalized_source": source,
            "cost_focus": ["rightsizing", "commitments", "idle resources"],
        }

    def _chunk(self, state: PipelineState) -> PipelineState:
        chunks = self.chunker.split(state["text_content"])
        return {
            **state,
            "chunks": chunks,
        }

    def _analyze(self, state: PipelineState) -> PipelineState:
        insight = self.agent_runtime.invoke(state, status="running")
        return {
            **state,
            "insight": insight,
        }

    def _embed_and_store(self, state: PipelineState) -> PipelineState:
        embeddings = [self.embedding_provider.embed(chunk) for chunk in state["chunks"]]
        embedding_result = self.vector_store.store_document(
            job_id=state["job_id"],
            tenant_id=state["tenant_id"],
            source=state["normalized_source"],
            artifact_uri=state.get("artifact_uri"),
            text_content=state["text_content"],
            chunks=state["chunks"],
            embeddings=embeddings,
            provider_name=self.embedding_provider.name,
        )
        return {
            **state,
            "embedding_result": embedding_result,
        }

    def _summarize(self, state: PipelineState) -> PipelineState:
        summary = (
            f"Ingestion for tenant {state['tenant_id']} from {state['normalized_source']} "
            f"completed with focus areas {', '.join(state['cost_focus'])} "
            f"and {state['embedding_result']['chunk_count']} stored chunks."
        )
        return {
            **state,
            "summary": summary,
        }

    def run(self, payload: dict) -> dict:
        return self.graph.invoke(payload)
