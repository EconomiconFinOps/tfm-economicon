// StatusPill: wrapper presentacional trivial que normaliza un estado a
// minusculas y lo renderiza como pildora. Se reconstruye sobre Tailwind
// (badge con fondo/borde/texto en verde, mismo lenguaje que los indicadores
// de estado "sano" de los dashboards del origen, p. ej. AnomaliesPanel.tsx)
// en vez de la clase `status-pill` de main.css que usaba la version .jsx
// (REEMPLAZAR en la linea base de JUP-090). Un unico estilo neutro-sano
// basta: la pantalla que lo consume (DashboardPage) no distingue estados de
// error/alerta para este componente, solo nombres de servicio/plan/tenant.
interface StatusPillProps {
  status: string;
}

export function StatusPill({ status }: StatusPillProps) {
  const normalized = String(status || "unknown").toLowerCase();
  return (
    <span className="inline-flex items-center rounded-full border border-green-500/30 bg-green-500/20 px-2.5 py-0.5 text-xs font-medium text-green-300">
      {normalized}
    </span>
  );
}
