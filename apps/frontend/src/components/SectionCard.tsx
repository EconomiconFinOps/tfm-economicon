// SectionCard: wrapper presentacional trivial (titulo/subtitulo opcional +
// children), usado por IngestPage/ConversationsPage/DashboardPage. Se
// reconstruye sobre Tailwind con el mismo lenguaje visual que las tarjetas de
// los dashboards del origen (degradado, borde, rounded-lg, shadow-xl -- ver
// ExecutiveCostDashboard.tsx) en vez de las clases de main.css que usaba la
// version .jsx (REEMPLAZAR en la linea base de JUP-090), para que las
// pantallas que lo consumen no queden visualmente desentonadas del resto de
// la aplicacion.
import type { ReactNode } from "react";

interface SectionCardProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

export function SectionCard({ title, subtitle, children }: SectionCardProps) {
  return (
    <section className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-6 shadow-xl">
      <div className="mb-4">
        <h2 className="text-lg font-bold text-white">{title}</h2>
        {subtitle ? <p className="mt-1 text-sm text-slate-400">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}
