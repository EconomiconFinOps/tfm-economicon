# Identidad de marca del frontend — JUP-112

Última actualización documental: 2026-10-22 (texto del conmutador de tema, JUP-134). Esta nota no repite el alcance de la tarjeta, que vive en [Trello](https://trello.com/c/XTZU3vj3).

## Estado

- Rama `feat/JUP-112-brand-identity`, creada desde `develop` en `d057537`. Implementación nueva; no reutiliza el borrador paralelo de otra rama (PR #102) sobre la misma tarjeta, por decisión de Lucia.
- OpenSpec: `openspec/changes/archive/2026-10-10-jup-112-brand-identity/` (capacidad nueva `frontend-brand-identity` y delta de `frontend-navigation-shell`). ADR: [ADR-0012](../adr/ADR-0012-frontend-color-tokens.md), enmendado.
- Evidencia: [JUP-112-validation.md](../evidence/JUP-112-validation.md) con capturas, validación de paletas y comportamiento del conmutador. PR [#112](https://github.com/EconomiconFinOps/tfm-economicon/pull/112) abierto contra `develop`, con una revisión que pidió cambios (pestañas a 1280 px, conflicto con `develop`, tests de la spec, enlaces del cambio archivado y menores), atendidos en una sola tanda. Los responsables de revisión y validación viven en Trello y en la descripción del PR, y esta nota no los repite; `JUP reviews` sigue en rojo hasta que existan las dos reviews humanas y la descripción y la tarjeta coincidan.

## Decisiones que no se deducen del código

- **Dos temas, no uno.** La tarjeta declara el modo oscuro fuera de alcance; Lucia decidió incluirlo tras comparar dos maquetas. Es una ampliación de alcance que debe confirmar el liderazgo de la tarjeta; si se rechaza, el bloque `[data-theme="dark"]` de `theme.css` se retira sin tocar pantallas.
- **Los colores de estado y de gráficas son criterio de diseño**, porque la guía de marca no los define. Se validaron con el validador de dataviz y con contraste WCAG; los valores y por qué se eligieron están en el `design.md` del cambio. El verde es azulado y el peligro un rojo frío a propósito: con verde puro, rojo y verde se confundían para daltonismo, y el naranja es del coral (ahorro e insights), no de las alarmas.
- **Violeta y coral tienen un solo uso cada uno.** El violeta `#5B4FE8` es de botones y llamadas a la acción; la navegación, la selección y el foco usan `highlight`. El coral `#FF8A5B` solo marca ahorro e insights y su texto es siempre casi negro, porque con texto claro no llega a 4,5:1.
- **Fuentes y logotipo** se empaquetan con la aplicación (Inter y Space Grotesk, OFL; monograma E original del dossier, sin editar). Orígenes y hashes en `apps/frontend/ATTRIBUTIONS.md`.

## Qué tocar si cambia algo

- Un color: `apps/frontend/src/styles/theme.css`, siempre en las dos paletas, y ejecutar `theme-contrast.test.ts` y `theme-palette.test.ts`.
- Un color de estado nuevo: debe llevar icono o texto y cumplir el contraste del test (relleno suave como máximo al 30 % de opacidad).
- El orden de arranque del tema vive en dos sitios que deben coincidir: el script de `index.html` y `src/hooks/useTheme.ts`.
- El texto del conmutador de tema (`src/components/ThemeToggle.tsx`) nombra el tema activo: «Tema claro» con el claro y «Tema oscuro» con el oscuro, con el icono del sol o de la luna (JUP-134, delta de `frontend-brand-identity`). Ya no es un botón de alternancia con `aria-pressed`: su nombre accesible es su texto visible y el `title` describe la acción al pulsar («Cambiar a tema oscuro» o «Cambiar a tema claro»). Si cambia el texto hay que actualizar `ThemeToggle.test.tsx`, `useTheme.test.tsx` y `brand-spec.guard.test.tsx`.

## Pendiente

- Revisión de código y validación funcional por las personas con esos roles en Trello; ninguna se da por hecha aquí.
- Confirmar con el liderazgo la ampliación del alcance al tema oscuro.
- Capturar con datos reales la pantalla "Coste Global", que con la API simulada de esta sesión mostró su estado de error.
