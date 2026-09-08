interface MetricCardProps {
  label: string;
  value: string | number;
  detail: string;
  tone?: "default" | "warm" | "success";
}

export function MetricCard({ label, value, detail, tone = "default" }: MetricCardProps) {
  return (
    <article className={`metric-card tone-${tone}`}>
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value}</p>
      <p className="metric-detail">{detail}</p>
    </article>
  );
}

