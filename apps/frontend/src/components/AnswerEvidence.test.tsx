import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AnswerEvidence } from "./AnswerEvidence";

const citation = {
  evidence_id: "chunk-1", kind: "corpus", document_id: "doc-1", title: "Guía Azure",
  source: "FinOps", reference: "document:doc-1/chunk:0", section: "Costes", page: 4,
  excerpt: "La evidencia original <script>alert(1)</script>"
};

describe("AnswerEvidence", () => {
  it("opens persisted evidence from a generated claim without interpreting HTML", () => {
    render(<AnswerEvidence content="El presupuesto <b>no</b> es forecast. [1]" metadata={{
      generation: "litellm", citations: ["chunk-1"], source_citations: [citation],
      claims: [{ text: "El presupuesto <b>no</b> es forecast.", evidence_ids: ["chunk-1"] }]
    }} />);
    fireEvent.click(screen.getByRole("link", { name: "Ver fuente 1" }));
    expect(screen.getByText(/Guía Azure/).closest("details")).toHaveAttribute("open");
    expect(screen.getByText(/presupuesto <b>no/).querySelector("b")).toBeNull();
  });

  it("labels mock and insufficient-data results", () => {
    render(<AnswerEvidence content="Sin evidencia" metadata={{ generation: "mock", answer_status: "insufficient_data" }} />);
    expect(screen.getByText(/sin modelo generativo/)).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Evidencia insuficiente");
  });
  it("links each used passage to its persisted source and evidence", () => {
    const { container } = render(<AnswerEvidence content={`Contexto:\n- [1] FinOps: ${citation.excerpt}`} metadata={{ citations: ["chunk-1"], source_citations: [citation] }} />);
    const link = screen.getByRole("link", { name: "Ver fuente 1" });
    expect(document.getElementById(link.getAttribute("href")!.slice(1))).toBeInTheDocument();
    expect(fireEvent.click(link)).toBe(false);
    const evidence = document.getElementById(link.getAttribute("href")!.slice(1));
    expect(evidence).toHaveAttribute("open");
    expect(evidence?.querySelector("summary")).toHaveFocus();
    expect(screen.getByText(/Guía Azure/)).toBeInTheDocument();
    expect(screen.getByText("Página: 4")).toBeInTheDocument();
    expect(screen.getByText("Sección: Costes")).toBeInTheDocument();
    expect(screen.getByText(citation.excerpt)).toBeInTheDocument();
    expect(container.querySelector("script")).toBeNull();
  });

  it.each([
    { citations: ["missing"], source_citations: [citation] },
    { citations: ["chunk-1", "chunk-1"], source_citations: [citation, citation] },
    { citations: ["chunk-1"] },
    { citations: ["chunk-1"], source_citations: [{ ...citation, page: -1 }] }
  ])("does not turn invalid or legacy references into citations", (metadata) => {
    render(<AnswerEvidence content="- [1] Respuesta" metadata={metadata} />);
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.getByText("La evidencia de esta respuesta no está disponible.")).toBeInTheDocument();
  });

  it("does not invent page or section for documents without them", () => {
    render(<AnswerEvidence content="- [1] Respuesta" metadata={{ citations: ["chunk-1"], source_citations: [{ ...citation, page: null, section: null }] }} />);
    expect(screen.queryByText(/Página:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Sección:/)).not.toBeInTheDocument();
  });

  it("does not turn an echoed user citation marker into a supported claim", () => {
    render(<AnswerEvidence content={`Pregunta:\n- [1] Una cifra inventada\n- [1] FinOps: ${citation.excerpt}`} metadata={{ citations: ["chunk-1"], source_citations: [citation] }} />);
    expect(screen.getAllByRole("link")).toHaveLength(1);
    expect(screen.getByText("- [1] Una cifra inventada")).toBeInTheDocument();
  });

  it("shows unavailable cost evidence without a misleading documentary warning", () => {
    render(<AnswerEvidence content="No hay datos suficientes." metadata={{ cost_evidence: { schema_version: "future" } }} />);
    expect(screen.getByText("No hay datos suficientes.")).toBeInTheDocument();
    expect(screen.getByText("La evidencia de costes de esta respuesta no está disponible.")).toBeInTheDocument();
    expect(screen.queryByText("Sin fuentes documentales utilizadas.")).not.toBeInTheDocument();
  });
});
