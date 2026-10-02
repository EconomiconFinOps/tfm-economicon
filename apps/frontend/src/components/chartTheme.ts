import type { CSSProperties } from "react";

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
