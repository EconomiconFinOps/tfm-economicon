import { createElement } from "react";
import type { CSSProperties, ReactNode } from "react";

// Estilo unico del tooltip de Recharts. Antes se repetia literal en las 9
// graficas de los dashboards; centralizarlo evita que las copias diverjan.
// Usa variables del tema (`var(--...)`) y no hexadecimales porque Recharts
// aplica este objeto como `style` en linea: una utilidad de Tailwind no
// serviria aqui, pero `var()` si se resuelve en el navegador, asi que un
// cambio de token en `theme.css` llega tambien a las graficas.
export const chartTooltipStyle: CSSProperties = {
  backgroundColor: "var(--card)",
  border: "1px solid var(--border)",
  borderRadius: "8px",
  color: "var(--foreground)"
};

// Recharts pinta el texto de la leyenda con el color de la serie; el texto usa tokens de texto.
export const chartLegendFormatter = (value: ReactNode) =>
  createElement("span", { style: { color: "var(--muted-foreground)" } }, value);
