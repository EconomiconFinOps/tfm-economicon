from typing import TypedDict

from langgraph.graph import END, StateGraph


class PipelineState(TypedDict, total=False):
    job_id: str
    tenant_id: str
    source: str
    metadata: dict
    artifact_uri: str | None
    normalized_source: str
    cost_focus: list[str]
    insight: dict
    summary: str


class PipelineRunner:
    def __init__(self, agent_runtime):
        self.agent_runtime = agent_runtime
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(PipelineState)
        workflow.add_node("normalize", self._normalize)
        workflow.add_node("analyze", self._analyze)
        workflow.add_node("summarize", self._summarize)
        workflow.set_entry_point("normalize")
        workflow.add_edge("normalize", "analyze")
        workflow.add_edge("analyze", "summarize")
        workflow.add_edge("summarize", END)
        return workflow.compile()

    def _normalize(self, state: PipelineState) -> PipelineState:
        source = state["source"].strip().lower()
        return {
            **state,
            "normalized_source": source,
            "cost_focus": ["rightsizing", "commitments", "idle resources"],
        }

    def _analyze(self, state: PipelineState) -> PipelineState:
        insight = self.agent_runtime.invoke(state, status="running")
        return {
            **state,
            "insight": insight,
        }

    def _summarize(self, state: PipelineState) -> PipelineState:
        summary = (
            f"Ingestion for tenant {state['tenant_id']} from {state['normalized_source']} "
            f"completed with focus areas {', '.join(state['cost_focus'])}."
        )
        return {
            **state,
            "summary": summary,
        }

    def run(self, payload: dict) -> dict:
        return self.graph.invoke(payload)

