# Review JUP-116 — Ocultar del MVP las pantallas de maqueta

## Resumen

Coste Detallado (`/operational`), Corte Global (`/cuts`) y Recomendaciones (`/recommendations`) ya no tienen ruta ni entrada de menú; sus pantallas, datos de demostración y pruebas se conservan sin ninguna ruta que las monte. La entrada «Overview» sale del menú y `/overview-legacy` se mantiene como ruta puente. Una dirección no publicada lleva a la pantalla inicial (ruta comodín con `replace`). El menú pasa a una sola lista de cinco entradas y se retira el token `--muted`, cuyo único consumidor era el separador. Rama `feat/JUP-116-hide-mockup-screens` desde `develop` en `3c6517b`; Trello https://trello.com/c/IPB2nGxa.

## Decisiones

- **Ocultar sin borrar, quitando rutas y menú** (Lucia, 2026-10-12), frente a un interruptor de configuración que habría reactivado sin editar código pero añadía un mecanismo y dos modos que probar.
- **`/overview-legacy` conserva su ruta**: 34 líneas de 9 archivos de pruebas y de soporte la usan de vehículo y la spec exige dirección propia para el resumen de facturación. Difiere de lo anunciado en Discord («retirarlo a la vez»); queda anotado como pendiente de confirmar con el equipo.
- **Anomalías sigue publicada** porque declara visiblemente que sus datos son de demostración. La primera versión de la spec decía que el menú solo enlazaba pantallas con backend, lo que era falso en esta base (la conexión es JUP-114); lo detectó la revisión y se corrigió la regla a «no se publican pantallas de demostración salvo que declaren su origen».
- **Ruta comodín hacia `/` con `replace`** en lugar de una pantalla «no encontrada» propia.
- **Se mergea antes que JUP-114** (decisión de Lucia): los conflictos de documentación (README de rutas, guion y esperados de la demo, mapa de JUP-097, findings) los resuelve quien mergee JUP-114 después.
- **Sin ADR**: reversible con dos líneas, sin arquitectura ni contrato nuevos.

## Validación

| Comando | Resultado |
| --- | --- |
| `corepack pnpm test` en `apps/frontend` con `--maxWorkers=2` | 64 archivos y 801 pruebas pasan |
| `corepack pnpm test` en `apps/frontend` sin limitar (equipo al 100 % de CPU por el stack Docker) | primera ejecución: 2 fallos de `ownership-conversations`; segunda: 7 fallos en 4 archivos (`conversations`, `ingestion`, `tenant-switching`, `ownership-conversations`), todos por tiempo (5 s); esos 4 archivos aislados pasan 26 de 26 |
| `corepack pnpm lint`, `typecheck` y `build` en `apps/frontend` | sin errores |
| `corepack pnpm openspec:validate` | 66 de 66 |
| `corepack pnpm jup:check -- --change jup-116-hide-mockup-screens` | correcto |
| `corepack pnpm jup:cleanup:check` | correcto |
| `corepack pnpm synthetic-demo:test` | 40 pruebas pasan |
| `git diff --check origin/develop..HEAD` | sin salida |
| Navegador real (Edge, Playwright, stack Docker, Growth Ops) | 16 comprobaciones PASS; ver la evidencia |

Pruebas en rojo primero (8 de 12 fallaron por la razón esperada antes de implementar) y cuatro mutantes sobre el código (restaurar `/cuts`, quitar el comodín, comodín sin `replace`, Overview en el menú), todos detectados; dos mutantes más sobre el guardián de pantallas de demostración (pantalla con datos de demostración sin aviso, Anomalías sin aviso), detectados.

## Adversarial Review (pass 1)

Revisor `adversarial-reviewer`, base `3c6517b`, head `5a33312`. Veredicto: **changes-requested**.

| ID | Sev. | Hallazgo | Resolución |
| --- | --- | --- | --- |
| ADV-1 | HIGH | El menú publica Anomalías, que no consulta el backend (datos de demostración), contra la spec delta y el diseño. | Corregido: la spec exige ahora aviso visible de demostración; spec, diseño y propuesta enmendados; guardián nuevo (ver pass 2). |
| ADV-2 | MEDIUM | La nota fechada del spike conservaba el recuento viejo (9 rutas, 4 de demostración). | Corregido: la nota indica que JUP-116 ocultó tres. |
| ADV-3 | LOW | Las pruebas «sin sesión + dirección oculta» no discriminan el comodín (pasarían sin él). | Aceptado y declarado en el diseño: son escenario de la spec y control de que el comodín no se salta `SessionGate`. |
| ADV-4 | LOW | `/overview-legacy` queda sin menú pero montada; el mensaje de Discord decía otra cosa. | Riesgo de proceso, anotado como pendiente de confirmar con el equipo en `docs/continuidad/pantallas-ocultas-mvp.md`. |

Ataques que resistieron: toda variante de dirección no publicada (barra final, mayúsculas, rutas anidadas, `//cuts`) cae en el comodín; `/login` y las rutas existentes (también las anidadas bajo `TenantScopedOutlet`) no quedan tapadas; sin sesión se presenta el acceso; el ámbito de cliente se conserva; `replace` evita volver a la dirección oculta; `--muted` no tiene consumidores.

## Adversarial Review (pass 2)

Revisor nuevo, head `11b4d7e`. Veredicto: **accept** (sin hallazgos BLOCKING ni HIGH).

| ID | Sev. | Hallazgo | Resolución |
| --- | --- | --- | --- |
| ADV-1 | MEDIUM | El título del escenario del menú contradecía su propio `AND`. | Corregido: «El menú no enlaza pantallas ocultas ni de demostración sin aviso». |
| ADV-2 | MEDIUM | `RF-104-004` pasaba a `Fixed` sin la cualificación de integración pendiente ni el Scope actualizado, y conservaba la frase «sigue `Open`» de JUP-105. | Corregido: `Fixed (JUP-116; integración y validación humana pendientes)`, Scope y frases históricas marcadas. |
| ADV-3 | MEDIUM | Ninguna prueba ligaba el menú con la presencia del aviso de demostración. | Corregido: prueba que, para cada pantalla enrutada que importa datos de demostración, exige el aviso; verificada con 2 mutantes. |
| ADV-4 | LOW | Cifras incoherentes para las referencias a `/overview-legacy`. | Corregido: una sola cifra (34 líneas, 9 archivos de pruebas y soporte). |
| ADV-5 | LOW | El spike conservaba una fila de decisiones con «Rotular las 3 pantallas». | Corregido: nota de que JUP-116 las ocultó. |
| ADV-6 | LOW | `FIXED_DATA_ROUTES` en `test_synthetic_cost_demo.py` lista rutas inexistentes. | Registrado como `RF-116-001`; no se toca para no chocar con JUP-114, que también edita ese archivo. |
| ADV-7 | LOW | Las pruebas «sin sesión» no discriminan el comodín. | Aceptado, ver pass 1 ADV-3. |
| ADV-8 | LOW | No se sondeó una URI mal formada ni direcciones largas. | Probado: `/%E0%A4%A`, `/cuts?x=1#h` y 5000 caracteres redirigen a la inicial (prueba nueva); React Router solo escribe un aviso en la consola. |

Ataques que resistieron: aserciones negativas con dónde fallar, prueba de Atrás por la razón correcta, ámbito de cliente conservado, guion y esperados de la demo coherentes con la interfaz, CI y herramientas sin recuentos de pantallas.

## Barrido de patrón

- Referencias a las pantallas ocultas en documentos **vigentes**: README del frontend, `docs/architecture.md`, `docs/demo/JUP-107/*`, mapa de JUP-097, spike y continuidad, actualizadas.
- Se dejan sin tocar, por ser registros fechados de lo ocurrido: `docs/evidence/JUP-0xx-validation.md` y `JUP-104-browser-recipe.md` (la receta recorre las tres pantallas y ya no es reproducible tal cual), `docs/planning/JUP-091-economicon-source-inventory.md`, ADR-0003 y los changes archivados.
- Referencias en código: las pruebas de las pantallas ocultas se conservan (montan el componente); el README lo explica.
- Patrón «un token de color queda sin consumidor al quitar su único uso»: el guardián de tokens lo detectó; no hay otro token en esa situación.

## Riesgos

- **Pruebas lentas bajo carga:** con el stack Docker en marcha y el equipo al 100 % de CPU, algunas pruebas de formularios superan los 5 s y fallan; con menos paralelismo o aisladas pasan. No se ha comprobado en `develop` sin estos cambios, así que la causa es una hipótesis. Registrado como `RF-116-002`.
- **Conflictos de documentación con JUP-114:** previsibles y asumidos por decisión de Lucia (se mergea antes).
- **Código sin ruta que se pudre:** mitigado porque sus pruebas siguen montándolo; reactivarlo puede requerir ajustes.
- **No comprobado:** envío de mensajes del asistente (el stack de IA no está levantado) y tema oscuro.

## Hallazgos registrados

- `RF-116-001`: `FIXED_DATA_ROUTES` en `scripts/tests/test_synthetic_cost_demo.py` lista rutas que ya no existen.
- `RF-116-002`: pruebas de formularios del frontend fallan por tiempo (5 s) con el equipo saturado.
