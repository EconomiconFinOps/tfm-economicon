// SectionCard: componente presentacional (titulo/subtitulo opcional +
// children), usado por IngestPage/ConversationsPage/DashboardPage. Comparte
// lenguaje visual con las tarjetas de los dashboards (degradado, borde,
// rounded-lg, shadow-xl) para que las pantallas que lo consumen no desentonen
// del resto de la aplicacion. Los colores proceden de los tokens del tema
// (styles/theme.css), no de valores literales, de modo que una unica paleta
// gobierna la apariencia de la aplicacion.
import type { ReactNode } from "react";

interface SectionCardProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

export function SectionCard({ title, subtitle, children }: SectionCardProps) {
  return (
    <section className="bg-gradient-to-br from-card to-accent rounded-lg border border-border p-6 shadow-xl">
      <div className="mb-4">
        <h2 className="text-lg font-bold text-foreground">{title}</h2>
        {subtitle ? <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}
