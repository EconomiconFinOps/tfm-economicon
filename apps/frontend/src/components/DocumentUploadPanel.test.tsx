import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { DocumentUploadPanel } from "./DocumentUploadPanel";
import type { DocumentTransport, UploadStatus, UploadTicket } from "../services/document-contracts";

const id = "10000000-0000-4000-8000-000000000001";
const ticket: UploadTicket = { upload_id: id, upload_url: "http://localhost:9000/private/staging",
  headers: { "Content-Type": "application/octet-stream" }, expires_at: "2030-01-01T00:00:00Z", max_file_bytes: 20_000_000 };
const accepted: UploadStatus = { upload_id: id, filename: "budget.txt", file_size: 8, status: "confirmed", job_id: id,
  job_status: "queued", duplicate: false, cleanup_done: false, retry_pending: false };
function transport(): DocumentTransport {
  return { begin: vi.fn().mockResolvedValue(ticket), transfer: vi.fn().mockResolvedValue(undefined),
    confirm: vi.fn().mockResolvedValue(accepted), status: vi.fn().mockResolvedValue({ ...accepted, job_status: "completed" }),
    cancel: vi.fn().mockResolvedValue(accepted) };
}
function file(name = "budget.txt", size?: number) {
  const value = new File(["Budget42"], name);
  Object.defineProperty(value, "arrayBuffer", { value: async () => new TextEncoder().encode("Budget42").buffer });
  if (size !== undefined) Object.defineProperty(value, "size", { value: size });
  return value;
}
function choose(files: File[]) { fireEvent.change(screen.getByLabelText("Selecciona o arrastra un archivo aquí"), { target: { files } }); }
afterEach(() => { vi.unstubAllGlobals(); });

describe("Document upload", () => {
  it("accepts one file and rejects a multi-file drop without reserving a transfer", () => {
    const api = transport(); render(<DocumentUploadPanel transport={api} />);
    const input = screen.getByLabelText("Selecciona o arrastra un archivo aquí");
    expect(input).not.toHaveAttribute("multiple");
    expect(screen.queryByRole("checkbox")).toBeNull();
    fireEvent.drop(input.parentElement!, { dataTransfer: { files: [file(), file("second.txt")] } });
    expect(screen.getByRole("alert")).toHaveTextContent("un solo archivo");
    expect(api.begin).not.toHaveBeenCalled();
    choose([file()]); expect(screen.getByText("budget.txt")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Quitar budget.txt" }));
    expect(screen.queryByText("budget.txt")).toBeNull();
  });
  it.each([["budget.txt", 0, "vacío"], ["budget.txt", 20_000_001, "supera"], ["budget.exe", 8, "Formato no admitido"]])(
    "prevents invalid selection %s/%s", (name, size, message) => {
      const api = transport(); render(<DocumentUploadPanel transport={api} />);
      choose([file(String(name), Number(size))]);
      expect(screen.getByText(new RegExp(String(message)))).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Subir archivo" })).toBeDisabled();
      expect(api.begin).not.toHaveBeenCalled();
    });
  it("hashes and transfers before confirming; queued is not completion and duplicate is visible", async () => {
    vi.stubGlobal("crypto", { subtle: { digest: vi.fn().mockResolvedValue(new Uint8Array(32).buffer) } });
    const api = transport(); vi.mocked(api.confirm).mockResolvedValue({ ...accepted, duplicate: true });
    render(<DocumentUploadPanel transport={api} />); choose([file()]);
    fireEvent.click(screen.getByRole("button", { name: "Subir archivo" }));
    await waitFor(() => expect(api.confirm).toHaveBeenCalledTimes(1));
    expect(api.begin).toHaveBeenCalledWith(expect.objectContaining({ content_hash: "0".repeat(64), force_reprocess: false }), expect.any(AbortSignal));
    expect(vi.mocked(api.transfer).mock.invocationCallOrder[0]).toBeLessThan(vi.mocked(api.confirm).mock.invocationCallOrder[0]);
    expect(screen.getByRole("status")).toHaveTextContent("Encolado · Documento ya existente");
    expect(screen.getByRole("status")).not.toHaveTextContent("Completado");
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Completado"), { timeout: 4000 });
  });
  it("removes a temporary polling error after status queries recover", async () => {
    vi.stubGlobal("crypto", { subtle: { digest: vi.fn().mockResolvedValue(new Uint8Array(32).buffer) } });
    const api = transport();
    vi.mocked(api.status).mockRejectedValueOnce(new Error("temporary connection failure"))
      .mockResolvedValue({ ...accepted, job_status: "completed" });
    render(<DocumentUploadPanel transport={api} />); choose([file()]);
    fireEvent.click(screen.getByRole("button", { name: "Subir archivo" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Se volverá a consultar"), { timeout: 3500 });
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Completado"), { timeout: 3500 });
    expect(screen.queryByRole("alert")).toBeNull();
  }, 8000);
  it("cancels an unfinished transfer on leaving the session scope", async () => {
    vi.stubGlobal("crypto", { subtle: { digest: vi.fn().mockResolvedValue(new Uint8Array(32).buffer) } });
    const api = transport(); let signal: AbortSignal | undefined;
    vi.mocked(api.transfer).mockImplementation((_ticket, _file, _progress, current) => { signal = current; return new Promise(() => {}); });
    const view = render(<DocumentUploadPanel transport={api} />); choose([file()]);
    fireEvent.click(screen.getByRole("button", { name: "Subir archivo" }));
    await waitFor(() => expect(api.transfer).toHaveBeenCalled()); view.unmount();
    expect(signal?.aborted).toBe(true); expect(api.cancel).toHaveBeenCalledWith(id);
    expect(api.confirm).not.toHaveBeenCalled();
  });
  it("keeps polling a recoverable failed attempt and only deliberately retries a final failed job", async () => {
    vi.stubGlobal("crypto", { subtle: { digest: vi.fn().mockResolvedValue(new Uint8Array(32).buffer) } });
    const api = transport();
    vi.mocked(api.confirm).mockResolvedValueOnce({ ...accepted, job_status: "failed", retry_pending: true });
    vi.mocked(api.status).mockResolvedValue({ ...accepted, job_status: "failed", retry_pending: false });
    render(<DocumentUploadPanel transport={api} />); choose([file()]);
    fireEvent.click(screen.getByRole("button", { name: "Subir archivo" }));
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Pendiente de reintento"));
    expect(screen.queryByRole("button", { name: /Reintentar procesamiento/ })).toBeNull();
    await waitFor(() => expect(screen.getByRole("button", { name: /Reintentar procesamiento/ })).toBeInTheDocument(), { timeout: 4000 });
    fireEvent.click(screen.getByRole("button", { name: /Reintentar procesamiento/ }));
    fireEvent.click(screen.getByRole("button", { name: "Subir archivo" }));
    await waitFor(() => expect(api.begin).toHaveBeenCalledTimes(2));
    expect(vi.mocked(api.begin).mock.calls[1][0].force_reprocess).toBe(true);
  });
});
