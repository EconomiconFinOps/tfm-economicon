import { AlertCircle, CheckCircle2, HelpCircle } from "lucide-react";

interface StatusPillProps {
  status?: string | null;
  tone?: string;
}
const TONES = {
  ok: "border-success-tint/30 bg-success-tint/20 text-success-foreground",
  failed: "border-danger-tint/30 bg-danger-tint/20 text-danger-foreground",
  degraded: "border-warning-tint/30 bg-warning-tint/20 text-warning-foreground",
  unknown: "border-neutral/30 bg-neutral/20 text-muted-foreground"
} as const;

// Existing consumers keep their green default; health explicitly selects tone.
export function StatusPill({ status, tone }: StatusPillProps) {
  const normalized = String(status || "unknown").toLowerCase();
  const selected = tone === undefined ? "ok" : Object.prototype.hasOwnProperty.call(TONES, tone) ? tone as keyof typeof TONES : "unknown";
  const Icon = selected === "ok" ? CheckCircle2 : selected === "failed" || selected === "degraded" ? AlertCircle : HelpCircle;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${TONES[selected]}`}>
      {tone ? <Icon className="size-3 shrink-0" aria-hidden="true" /> : null}
      {normalized}
    </span>
  );
}
