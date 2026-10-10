# Review JUP-112 — Identidad de marca del frontend

Fecha: 2026-10-10. Rama `feat/JUP-112-brand-identity`, desde `origin/develop` en `d057537`. Trello: https://trello.com/c/XTZU3vj3

## Resumen

El frontend adopta la marca de Economicon en dos temas, claro (por defecto) y oscuro, con un conmutador en la cabecera. Cambia el tema (`theme.css`), la cabecera y el acceso (monograma E, nombre y título), la tipografía (Inter y Space Grotesk empaquetadas), los estados y las gráficas, y varias pantallas que asumían fondo oscuro. Se añaden tests de contrato del tema, contraste, marca y conmutador. El tema oscuro amplía el alcance de la tarjeta por decisión de Lucia; la confirmación del liderazgo queda pendiente. No reutiliza el borrador de otra rama (PR #102).

## Decisiones

- Los nombres de token de ADR-0012 se conservan y cambian sus valores; se añaden `brand` y `saving` y se retira `attention-*`.
- Dos paletas con los mismos tokens (`:root` y `[data-theme="dark"]`), con script de arranque en `index.html` y hook `useTheme`.
- Los estados y las gráficas son criterio de diseño validado con el validador de dataviz y con contraste WCAG; ver la tabla del `design.md`.
- ADR: se enmienda ADR-0012 (decisiones 2 y 3); no hace falta un ADR nuevo.

## Validación

Comandos ejecutados en la rama (resultado de la última pasada, tras `148f328`):

| Comando | Resultado |
| --- | --- |
| `corepack pnpm test` (apps/frontend) | 61 archivos y 768 tests pasan (antes del cambio: 55 y 646) |
| `corepack pnpm typecheck`, `lint`, `build` (apps/frontend) | sin errores |
| `corepack pnpm openspec:validate` | 58 de 58 correctos |
| `corepack pnpm jup:check -- --change jup-112-brand-identity` | correcto |
| `corepack pnpm jup:cleanup:check` | correcto |

Capturas en Chromium real (10 pantallas × 2 temas × 1280 y 390 px) y comportamiento del conmutador: [evidencia](../../../docs/evidence/JUP-112-validation.md). Límites de lo no validado, allí.

## Adversarial Review (pass 1)

Veredicto: **changes-required**. Sin BLOCKING; 3 HIGH, 5 MEDIUM y 4 LOW (uno de ellos, ADV-10, confirmó que `design.md` coincidía con el código).

| ID | Sev. | Hallazgo | Resolución |
| --- | --- | --- | --- |
| ADV-1 | HIGH | Una gráfica usaba el violeta de botones (`var(--primary)`) | Usa `--chart-1`; guardián `brand-usage.guard.test.ts` |
| ADV-2 | HIGH | Foco invisible en la cabecera (el anillo era del mismo índigo que ella) | Contorno `brand-foreground` en los controles de la cabecera; tests |
| ADV-3 | HIGH | El ahorro no se destacaba con el coral | Tarjetas de ahorro en coral y test de render (`savings-coral.test.tsx`) |
| ADV-4 | MEDIUM | El contraste del texto neutro y secundario sobre rellenos tintados no estaba cubierto | Tonos ajustados y pares añadidos a `theme-contrast.test.ts` |
| ADV-5 | MEDIUM | El test de contraste usaba solo el 30 % de opacidad | Guardián del máximo del 30 % |
| ADV-6 | MEDIUM | Nombre accesible del conmutador no contenía el texto visible | Texto visible fijo "Tema oscuro", sin `aria-label`; test |
| ADV-7 | MEDIUM | Bordes de campos a 1,4:1 | `--input` propio y `border-input`; test ≥3:1 |
| ADV-8 | MEDIUM | `chart-1` se parecía al violeta de botones | `chart-1` pasa a ciruela y se reordenan las series; test de distancia |
| ADV-9 a ADV-12 | LOW | Primitivo tooltip con el violeta (sin importadores), `design.md` frente al código (sin discrepancias), script de arranque frente al hook, borde del botón primario en oscuro | Excepción declarada en el guardián, test de equivalencia script/hook; ADV-12 sin cambio (el texto del botón llega a 5,63:1) |

## Adversarial Review (pass 2)

Veredicto: **accept**. Sin BLOCKING ni HIGH; 7 MEDIUM y 4 LOW.

| ID | Sev. | Hallazgo | Resolución |
| --- | --- | --- | --- |
| ADV-1 | MEDIUM | Los campos de texto solo cambiaban el borde al enfocarse | Contorno `focus-visible` de `highlight`; guardián de `outline-none` sin foco propio |
| ADV-2 | MEDIUM | Los tooltips de Recharts pintan cada ítem con el color de la serie (3,45:1) | `itemStyle` con el color de texto del tema en todos los tooltips; guardián. Sin captura en navegador real |
| ADV-3 | MEDIUM | La barra de uso de Coste Detallado medía 2,28:1 contra su pista | La pista pasa a tarjeta con borde |
| ADV-4 | MEDIUM | El foco por defecto estaba al 50 % (2,8 a 3,0:1 en claro) | La regla base usa `outline-ring` entero; guardián |
| ADV-5 | MEDIUM | Los guardianes tenían huecos (prefijos y opacidades arbitrarias) | Detectores ampliados con casos en memoria |
| ADV-6 | MEDIUM | Series poco distinguibles con deuteranopía simulada | **Sin corregir**: registrado como RF-112-001 |
| ADV-7 | MEDIUM | Dato demo de ahorro sin coral | Mapeado a `saving` |
| ADV-8 | LOW | `design.md` y `tasks.md` desajustados con el código | Corregidos |
| ADV-9 | LOW | `localStorage` escrito dentro de un actualizador de estado | Movido fuera del actualizador |
| ADV-10 y ADV-11 | LOW | Primitivo `select` sin importadores; `chart-3` igual a `warning-tint` | **Sin corregir**: RF-112-002 |

Ataques que resistieron en las dos pasadas: contraste de estados, de botones y del coral en ambos temas; almacenamiento bloqueado, `matchMedia` ausente o roto y valor guardado inválido; paletas con los mismos tokens; barrido de clases que asumían fondo oscuro; Recharts con `var()`; logotipos; el coral nunca indica alarma.

## Barrido de patrón

Los defectos de uso del violeta, del foco y de los tooltips se barrieron en todo `apps/frontend/src` y quedaron como guardianes estáticos (`brand-usage.guard.test.ts`, `theme-contrast.test.ts`), no como correcciones puntuales.

## Riesgos

- **Probados**: contraste en ambos temas, conmutador (8 casos más equivalencia con el script de `index.html`), uso del violeta, opacidad máxima, foco y tooltips, y ahorro en coral.
- **No probados, pendientes de decisión de Lucia**: separación entre series con deuteranopía (RF-112-001); tooltips y foco no capturados en un navegador real; Firefox y Safari. No se aceptan en nombre de Lucia.
- **Proceso**: el tema se reescribió antes que los tests de contrato, así que la fase "rojo" solo se evidencia en el test de contraste (falló antes de ajustar los tonos de peligro), en los guardianes ampliados tras la revisión y en las mutaciones del conmutador, no en cada cambio visual.

## Hallazgos registrados

[RF-112-001](../../findings/backlog.md#rf-112-001-series-de-grafica-poco-distinguibles-con-deuteranopia-simulada) y [RF-112-002](../../findings/backlog.md#rf-112-002-cabos-sueltos-de-menor-severidad-tras-jup-112) en `openspec/findings/backlog.md`.

## ADR

ADR-0012 enmendado ([enmienda JUP-112](../../../docs/adr/ADR-0012-frontend-color-tokens.md)). Obliga a las tarjetas futuras a definir tokens en las dos paletas y a no usar `primary` fuera de botones.

## Pendiente

- La sección `## Human Approval` se rellena solo con la aprobación explícita de Lucia tras esta revisión.
- Revisión de código y validación funcional por las personas con esos roles en Trello; no se dan por hechas.
- Confirmar con el liderazgo de la tarjeta la ampliación del alcance al tema oscuro.
