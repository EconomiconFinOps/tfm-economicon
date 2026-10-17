export interface UploadTicket {
  upload_id: string;
  upload_url: string;
  headers: Record<string, string>;
  expires_at: string;
  max_file_bytes: number;
}
export interface UploadStatus {
  upload_id: string;
  filename: string;
  file_size: number;
  status: string;
  job_id: string | null;
  job_status: string | null;
  duplicate: boolean;
  cleanup_done: boolean;
  retry_pending: boolean;
}
export interface DocumentTransport {
  begin: (request: { filename: string; file_size: number; content_hash: string; force_reprocess: boolean }, signal: AbortSignal) => Promise<UploadTicket>;
  transfer: (ticket: UploadTicket, file: File, progress: (percent: number) => void, signal: AbortSignal) => Promise<void>;
  confirm: (id: string, signal: AbortSignal) => Promise<UploadStatus>;
  status: (id: string, signal: AbortSignal) => Promise<UploadStatus>;
  cancel: (id: string) => Promise<unknown>;
}
const record = (value: unknown): value is Record<string, unknown> => typeof value === "object" && value !== null;
const uuid = (value: unknown): value is string => typeof value === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
export function isUploadTicket(value: unknown): value is UploadTicket {
  if (!record(value) || !uuid(value.upload_id) || typeof value.upload_url !== "string"
    || !record(value.headers) || value.headers["Content-Type"] !== "application/octet-stream"
    || Object.keys(value.headers).length !== 1 || typeof value.expires_at !== "string"
    || !Number.isFinite(Date.parse(value.expires_at)) || !Number.isSafeInteger(value.max_file_bytes)
    || Number(value.max_file_bytes) < 1 || Number(value.max_file_bytes) > 20_000_000) return false;
  try {
    const url = new URL(value.upload_url);
    return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password;
  } catch { return false; }
}
export function isUploadStatus(value: unknown): value is UploadStatus {
  return record(value) && uuid(value.upload_id) && typeof value.filename === "string"
    && Number.isSafeInteger(value.file_size) && Number(value.file_size) > 0 && Number(value.file_size) <= 20_000_000
    && ["uploading", "confirmed", "duplicate", "cancelled", "expired"].includes(String(value.status))
    && (value.job_id === null || uuid(value.job_id))
    && (value.job_status === null || ["publish_pending", "queued", "running", "completed", "failed"].includes(String(value.job_status)))
    && typeof value.duplicate === "boolean" && typeof value.cleanup_done === "boolean" && typeof value.retry_pending === "boolean";
}
