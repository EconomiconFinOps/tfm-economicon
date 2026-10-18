import { afterEach, describe, expect, it, vi } from "vitest";
import { transferDocument } from "./api";
import { isUploadStatus, isUploadTicket } from "./document-contracts";

const ticket = { upload_id: "10000000-0000-4000-8000-000000000001", upload_url: "http://localhost:9000/private/staging?signature=synthetic",
  headers: { "Content-Type": "application/octet-stream" }, expires_at: "2030-01-01T00:00:00Z", max_file_bytes: 20_000_000 };
afterEach(() => { vi.unstubAllGlobals(); });
describe("Direct document transfer", () => {
  it("uses only signed storage headers without application credentials and reports progress", async () => {
    const request = { open: vi.fn(), setRequestHeader: vi.fn(), send: vi.fn(), abort: vi.fn(), status: 200,
      withCredentials: true, timeout: 0, upload: { onprogress: null as null | ((event: ProgressEvent) => void) },
      onload: null as null | (() => void), onerror: null as null | (() => void),
      ontimeout: null as null | (() => void), onabort: null as null | (() => void) };
    vi.stubGlobal("XMLHttpRequest", function () { return request; });
    const progress = vi.fn(); const file = new File(["budget42"], "budget.txt");
    const result = transferDocument(ticket, file, progress, new AbortController().signal);
    expect(request.open).toHaveBeenCalledWith("PUT", ticket.upload_url);
    expect(request.withCredentials).toBe(false);
    expect(request.setRequestHeader.mock.calls).toEqual([["Content-Type", "application/octet-stream"]]);
    expect(request.send).toHaveBeenCalledWith(file);
    request.upload.onprogress!({ lengthComputable: true, loaded: 4, total: 8 } as ProgressEvent);
    expect(progress).toHaveBeenCalledWith(50);
    request.onload!(); await expect(result).resolves.toBeUndefined();
  });
  it("does not transfer an already cancelled file", async () => {
    const construct = vi.fn(); vi.stubGlobal("XMLHttpRequest", construct);
    const controller = new AbortController(); controller.abort();
    await expect(transferDocument(ticket, new File(["x"], "budget.txt"), vi.fn(), controller.signal)).rejects.toMatchObject({ name: "AbortError" });
    expect(construct).not.toHaveBeenCalled();
  });
  it("rejects a forged storage response containing application headers or an unsafe URL", () => {
    expect(isUploadTicket(ticket)).toBe(true);
    expect(isUploadTicket({ ...ticket, headers: { ...ticket.headers, Authorization: "Bearer synthetic" } })).toBe(false);
    expect(isUploadTicket({ ...ticket, upload_url: "javascript:alert(1)" })).toBe(false);
    expect(isUploadTicket({ ...ticket, upload_url: "https://user:password@example.com/file" })).toBe(false);
    expect(isUploadTicket({ ...ticket, max_file_bytes: 20_000_001 })).toBe(false);
    expect(isUploadStatus({ ...ticket, status: "completed" })).toBe(false);
  });
});
