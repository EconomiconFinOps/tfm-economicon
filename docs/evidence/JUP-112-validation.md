# Evidencia JUP-112 — Adaptar el frontend a la guía de estilo e imagen de marca

- Fecha: 2026-10-10.
- Trello: https://trello.com/c/XTZU3vj3
- Rama: `feat/JUP-112-brand-identity`, desde `origin/develop` en `d057537`.
- OpenSpec: `openspec/changes/jup-112-brand-identity/` (proposal, design, specs y tasks).
- ADR: [ADR-0012](../adr/ADR-0012-frontend-color-tokens.md), enmendado en este cambio.
- Alcance: implementación nueva sobre `develop`; no reutiliza el borrador paralelo de otra rama (PR #102) sobre la misma tarjeta. El tema oscuro amplía el alcance de la tarjeta (que lo declara fuera de alcance) por decisión de Lucia; la confirmación del liderazgo de la tarjeta queda pendiente.
- Estado: evidencia técnica y visual de esta sesión, tras dos pasadas de revisión adversarial (ver `openspec/changes/jup-112-brand-identity/review.md`). No sustituye la revisión de código ni la validación funcional de las personas con esos roles en Trello.

## Qué se comprobó y cómo

| Comprobación | Resultado |
| --- | --- |
| `corepack pnpm test` en `apps/frontend` | 61 archivos y 768 tests pasan (antes del cambio: 55 archivos y 646 tests) |
| `corepack pnpm typecheck`, `lint`, `build` en `apps/frontend` | sin errores |
| `corepack pnpm openspec:validate` | 58 de 58 correctos |
| `corepack pnpm jup:check -- --change jup-112-brand-identity` | correcto |
| `corepack pnpm jup:cleanup:check` | correcto (sin agentes personales, binarios ni tareas paralelas) |
| Validador de paletas de dataviz (`palette-validation.txt`) | series de gráfica: 5 chequeos correctos en claro y en oscuro; estados, comparados todos contra todos: correctos, con un aviso de separación para daltonismo en oscuro (ΔE 6,6 entre peligro y aviso) |
| Capturas en Chromium real: 10 pantallas × 2 temas × 1280 y 390 px (40) | sin errores de página ni scroll horizontal de la página; Inter y Space Grotesk cargadas |
| Conmutador de tema en Chromium real (`toggle-report.json`) | alterna sin recargar, repinta las gráficas, recuerda la elección y respeta el sistema |

## Evidencia por requisito de la spec

| Requisito (`frontend-brand-identity` y delta del armazón) | Evidencia |
| --- | --- |
| Paleta de marca sobre fondo claro por defecto | `theme-contrast.test.ts` fija fondo `#FAFAFC`, texto `#14121F` y lila `#E4E1FB`; capturas `claro-*` |
| Tema oscuro derivado de la marca, arranque según el sistema, elección que prevalece, almacenamiento no disponible | `useTheme.test.tsx` (8 casos); `toggle-report.json`: con el sistema en claro arranca claro, con el sistema en oscuro arranca oscuro desde el primer pintado, una elección clara con sistema oscuro se conserva tras recargar |
| Control accesible para alternar | `ThemeToggle` con `aria-pressed` y etiqueta fija; `toggle-report.json`: el atributo pasa de `null` a `dark` sin recargar y se guarda `economicon-theme` |
| Violeta exclusivo de botones | revisión de usos de `primary` en `src/` (los botones usan `bg-primary` con `text-primary-foreground`; navegación, selección, foco y bordes pasan a `highlight`); `theme-contrast.test.ts` fija 5,63:1 del texto sobre el violeta. No se midió el porcentaje de superficie (≤10 %): se revisó a ojo en las capturas |
| Coral solo para ahorro e insights, con texto casi negro | `saving` solo se consume en `RecommendationsPanel` (cifras de ahorro e insignia de agentes de IA); `theme-contrast.test.ts` fija 7,96:1 del texto sobre el coral y que ninguna serie de gráfica lo usa |
| Estados distinguibles y legibles en ambos temas | `theme-contrast.test.ts`: texto de estado sobre su relleno (30 % de opacidad, el máximo que usan las pantallas), sobre fondo, tarjeta y lila ≥4,5:1; relleno contra tarjeta ≥3:1. Los indicadores de estado llevan texto o icono |
| Gráficas con paleta propia y legible | series ≥3:1 sobre la tarjeta en ambos temas (test); validador de dataviz sin fallos; texto de leyenda en `muted-foreground` y no en el color de la serie (`chartTheme.test.tsx`) |
| Tipografía empaquetada | `toggle-report.json`: las únicas fuentes cargadas son `Inter Variable` y `Space Grotesk Variable` y los hosts solicitados son el propio servidor y la API; ningún CDN. El host `gc.kis.v2.scr.kaspersky-labs.com` que aparece lo inyecta el antivirus del navegador, no la aplicación |
| Monograma E, título y favicon | `Layout.brand.test.tsx`; `public/favicon.png` reescalado a 64 px y revisado a ojo; logotipos con el SHA-256 original (ver `ATTRIBUTIONS.md`) |
| Armazón sin identidad antigua | `Layout.brand.test.tsx`: sin "FinOps AI Platform" ni "FinOps Control Tower" |
| Pantallas legibles en 1280 y 390 px en ambos temas | `capture-report.json` y capturas; defectos encontrados y corregidos: ver abajo |
| El tema define dos paletas con los mismos tokens, uno por definición y con consumidor | `theme-palette.test.ts` (119 casos) |

## Defectos encontrados durante la verificación (y corregidos)

- El texto de peligro no llegaba a 4,5:1 sobre el lila al 30 % (4,1:1 en claro y 4,4:1 en oscuro). Lo detectó `theme-contrast.test.ts` en su primera ejecución y se oscureció y aclaró el tono de texto (`#8F1B1B` y `#FF9DAC`).
- En móvil (390 px) las tarjetas de recomendaciones se cortaban por la derecha y el botón "Implementar" quedaba fuera de pantalla; la comprobación de scroll horizontal de la página no lo detectó porque la tarjeta recorta su contenido. Se apilan los bloques en móvil y se permite que las insignias y las métricas pasen de línea.
- La leyenda de las gráficas pintaba su texto con el color de la serie; ahora usa el color de texto secundario.
- La etiqueta "Infrastructure" del eje de la gráfica de recomendaciones se cortaba con la fuente nueva; se ensanchó el eje.
- La última pestaña de la navegación ("Salud del sistema") quedaba cortada a 1280 px; se redujo el relleno de las pestañas. La navegación sigue siendo desplazable si la anchura no basta.

## Defectos que encontró la revisión adversarial (y corregidos)

Dos pasadas independientes encontraron, entre otros: una gráfica con el violeta de botones, foco invisible en la cabecera, ahorro sin el coral, bordes de campos a 1,4:1, texto neutro por debajo de 4,5:1 sobre el degradado de tarjeta, tooltips con el texto en el color de la serie y barras de uso poco visibles contra su pista. Cada uno se corrigió con un test o un guardián estático, y las capturas de esta carpeta son posteriores a esas correcciones. Quedan registrados sin corregir `RF-112-001` y `RF-112-002` en `openspec/findings/backlog.md`.

## Pruebas de las propias comprobaciones

- Los tests más críticos del conmutador se sometieron a mutaciones de comprobación, con el código restaurado después: invertir la precedencia de la elección guardada, quitar la protección del almacenamiento al guardar y no persistir. Cada mutación hizo fallar al menos un test (2, 1 y 2 respectivamente).
- Como en el resto del cambio el tema se reescribió antes que los tests de contrato, la fase "rojo" estricta solo se evidencia en el test de contraste, que falló antes del ajuste de los tonos de peligro, y en las mutaciones anteriores. Los tests de `theme-palette.test.ts` se actualizaron junto con el tema.

## No se validó (y por qué)

- Datos reales y backend: las capturas usan una API simulada. La pantalla "Coste Global" mostró su estado de error porque el contrato simulado de `/billing/summary` no cubre el detalle que pide esa pantalla, así que no se capturó su estado con datos. Sí se capturaron con datos las pantallas de demostración (costes, corte, anomalías, recomendaciones y salud).
- Estados de carga, vacío y error: solo los que produjo la API simulada. No se forzó cada uno por pantalla.
- Las tablas anchas (anomalías, acciones de optimización) siguen desplazándose horizontalmente dentro de su contenedor en 390 px; se considera comportamiento aceptado de la tabla, no un recorte de la página.
- Navegadores: solo Chromium 1243 en Windows. No se probó Firefox ni Safari, ni lectores de pantalla, ni daltonismo simulado a ojo (solo el validador numérico).
- El documento de impresión de `ExportButton` solo se comprobó por código y test (valores de marca); no se abrió el diálogo de impresión.
- El favicon solo se comprobó como archivo, no en la pestaña del navegador.
- La aprobación estética y funcional de las personas con los roles de revisión y validación queda pendiente en Trello.

## Archivos de esta carpeta

`palette-validation.txt` (salida del validador con las paletas finales), `capture-report.json` (40 capturas: scroll horizontal, tema, fuentes y errores), `toggle-report.json` (comportamiento del conmutador) y 13 capturas representativas de las 40, con el prefijo `claro-` u `oscuro-` y la anchura. El guion de captura vive fuera del repositorio.
