import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AnswerEvidence } from "./AnswerEvidence";

const source = { evidence_id: "chunk-1", kind: "corpus", document_id: "doc-1", title: "FinOps",
  source: "Manual", reference: "document:doc-1/chunk:0", page: 2, section: "Costes",
  excerpt: "Introducción", content: "Introducción\nActual es consumo; amortizado distribuye compromisos. <script>alert(1)</script>" };
const metadata = { citations: ["chunk-1"], source_citations: [source] };

describe("rehearsal panel regressions", () => {
  it("shows the clarification from the persisted structured response after remount", () => {
    const props = { content: "Necesito más datos.", metadata: { response: {
      next_actions: ["Indica período y ámbito.", "Aporta una fuente autorizada."] } } };
    const first = render(<AnswerEvidence {...props} />);
    expect(screen.getByRole("region", { name: "Siguientes pasos" })).toHaveTextContent("Indica período y ámbito.");
    first.unmount();
    render(<AnswerEvidence {...JSON.parse(JSON.stringify(props))} />);
    expect(screen.getByText("Aporta una fuente autorizada.")).toBeVisible();
  });

  it.each([null, {}, ["Dato", 3], [""], [" "]])("ignores malformed actions %j", (next_actions) => {
    render(<AnswerEvidence content="Respuesta" metadata={{ response: { next_actions } }} />);
    expect(screen.queryByRole("region", { name: "Siguientes pasos" })).toBeNull();
  });

  it("opens the frozen passage safely and closes it with Escape", () => {
    const outerEscape = vi.fn();
    const { container } = render(<section onKeyDown={outerEscape}><AnswerEvidence content="Respuesta" metadata={metadata} /></section>);
    fireEvent.click(screen.getByRole("button", { name: "Abrir fuente 1: FinOps" }));
    const dialog = screen.getByRole("dialog", { name: "FinOps" });
    expect(dialog).toHaveTextContent("Actual es consumo; amortizado distribuye compromisos.");
    expect(dialog).toHaveTextContent("Página: 2");
    expect(dialog).toHaveTextContent("Sección: Costes");
    expect(dialog.querySelector("script")).toBeNull();
    expect(container.querySelector("script")).toBeNull();
    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(outerEscape).not.toHaveBeenCalled();
  });

  it("labels legacy excerpts without claiming a complete document", () => {
    const { content: _content, ...legacy } = source;
    void _content;
    render(<AnswerEvidence content="Respuesta" metadata={{ ...metadata, source_citations: [legacy] }} />);
    fireEvent.click(screen.getByRole("button", { name: "Abrir fuente 1: FinOps" }));
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("Introducción")).toBeVisible();
    expect(dialog).toHaveTextContent("Sólo se conserva el extracto de esta respuesta");
  });
});
