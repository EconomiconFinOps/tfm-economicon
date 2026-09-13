interface StatusPillProps {
  status?: string | null;
}

export function StatusPill({ status }: StatusPillProps) {
  const normalized = String(status || "unknown").toLowerCase();
  return <span className={`status-pill ${normalized}`}>{normalized}</span>;
}

