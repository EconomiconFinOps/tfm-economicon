// SectionCard: componente presentacional (titulo/subtitulo opcional +
// children), usado por IngestPage/ConversationsPage/DashboardPage. Comparte
// lenguaje visual con las tarjetas de los dashboards (fondo claro, borde,
// rounded-lg, shadow-sm) para que las pantallas que lo consumen no desentonen
// del resto de la aplicacion. Los colores proceden de los tokens del tema
// (styles/theme.css), no de valores literales, de modo que una unica paleta
// gobierna la apariencia de la aplicacion.
import type { ReactNode } from "react";

interface SectionCardProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  headingLevel?: 1 | 2;
}

export function SectionCard({ title, subtitle, children, headingLevel = 2 }: SectionCardProps) {
  const Heading = headingLevel === 1 ? "h1" : "h2";
  return (
    <section className="min-w-0 bg-card rounded-lg border border-border p-4 sm:p-6 shadow-sm">
      <div className="mb-4">
        <Heading className={headingLevel === 1 ? "page-title" : "font-bold text-brand"}>{title}</Heading>
        {subtitle ? <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}
