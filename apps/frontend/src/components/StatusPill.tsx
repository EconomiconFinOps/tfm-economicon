// StatusPill: componente presentacional que normaliza un estado a minusculas
// y lo renderiza como pildora (badge con fondo/borde/texto en verde, mismo
// lenguaje que los indicadores de estado "sano" de los dashboards). Los
// colores proceden de los tokens del tema (styles/theme.css), no de valores
// literales. Un unico estilo neutro-sano basta: la pantalla que lo consume
// (DashboardPage) no distingue estados de error/alerta para este componente,
// solo nombres de servicio/plan/tenant.
interface StatusPillProps {
  status?: string | null;
}

export function StatusPill({ status }: StatusPillProps) {
  const normalized = String(status || "unknown").toLowerCase();
  return (
    <span className="inline-flex items-center rounded-full border border-success-tint/30 bg-success-tint/20 px-2.5 py-0.5 text-xs font-medium text-success-foreground">
      {normalized}
    </span>
  );
}
