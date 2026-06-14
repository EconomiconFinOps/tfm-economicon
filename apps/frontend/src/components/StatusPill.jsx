export function StatusPill({ status }) {
  const normalized = String(status || "unknown").toLowerCase();
  return <span className={`status-pill ${normalized}`}>{normalized}</span>;
}

