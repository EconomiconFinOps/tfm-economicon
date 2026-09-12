// MetricCard: wrapper presentacional trivial (label/value/detail + tono
// opcional), usado por DashboardPage. Se reconstruye sobre Tailwind con el
// mismo lenguaje visual que SectionCard y las tarjetas KPI de los
// dashboards del origen (degradado, borde, rounded-lg, shadow-xl -- ver
// ExecutiveCostDashboard.tsx) en vez de las clases `metric-card`/`tone-*` de
// main.css que usaba la version .jsx (REEMPLAZAR en la linea base de
// JUP-090), para que la pantalla que lo consume no quede visualmente
// desentonada del resto de la aplicacion.
interface MetricCardProps {
  label: string;
  value: string | number;
  detail: string;
  tone?: "default" | "warm" | "success";
}

// El tono solo afecta al color del valor destacado: mapa cerrado en vez de
// interpolar la clase de Tailwind con el string (Tailwind no puede purgar
// clases construidas dinamicamente, ver decision de estilos ya aplicada en
// StatusPill/SectionCard de este mismo grupo).
const VALUE_TONE_CLASSES: Record<NonNullable<MetricCardProps["tone"]>, string> = {
  default: "text-white",
  warm: "text-amber-400",
  success: "text-emerald-400"
};

export function MetricCard({ label, value, detail, tone = "default" }: MetricCardProps) {
  return (
    <article className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-5 shadow-xl">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-2 text-2xl font-bold ${VALUE_TONE_CLASSES[tone]}`}>{value}</p>
      <p className="mt-2 text-sm text-slate-400">{detail}</p>
    </article>
  );
}
