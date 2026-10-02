// MetricCard: componente presentacional (label/value/detail + tono opcional),
// usado por DashboardPage. Comparte lenguaje visual con SectionCard y las
// tarjetas KPI de los dashboards (degradado, borde, rounded-lg, shadow-xl)
// para que la pantalla que lo consume no desentone del resto de la
// aplicacion. Todos los colores proceden de los tokens del tema
// (styles/theme.css), no de valores literales: asi una unica paleta gobierna
// la apariencia de la aplicacion.
interface MetricCardProps {
  label: string;
  value: string | number;
  detail: string;
  tone?: "default" | "warm" | "success";
}

// El tono solo afecta al color del valor destacado: mapa cerrado en vez de
// interpolar la clase de Tailwind con el string (Tailwind no puede purgar
// clases construidas dinamicamente, por lo que cada variante debe aparecer
// completa como literal en el codigo fuente).
const VALUE_TONE_CLASSES: Record<NonNullable<MetricCardProps["tone"]>, string> = {
  default: "text-foreground",
  warm: "text-warning",
  success: "text-positive"
};

export function MetricCard({ label, value, detail, tone = "default" }: MetricCardProps) {
  return (
    <article className="bg-gradient-to-br from-card to-accent rounded-lg border border-border p-5 shadow-xl">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className={`mt-2 text-2xl font-bold ${VALUE_TONE_CLASSES[tone]}`}>{value}</p>
      <p className="mt-2 text-sm text-muted-foreground">{detail}</p>
    </article>
  );
}
