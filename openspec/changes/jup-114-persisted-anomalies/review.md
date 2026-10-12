# Review JUP-114 (change 1) — Episodios de anomalía guardados

JUP: JUP-114 · Trello: https://trello.com/c/F492abeY · Rama: `feat/JUP-114-persisted-anomalies` · ADR: [ADR-0019](../../../docs/adr/ADR-0019-cost-anomaly-episodes.md)

## Resumen

Primer change de JUP-114. Guarda episodios de anomalía por tenant, moneda y servicio aplicando la regla diaria de negocio de JUP-019 sobre el coste diario observado, con referencia anclada, tolerancia de 3 días, impacto acumulado, criticidad P1/P2/P3 y estados trazables (`new`, `investigating`, `resolved`, `false_positive`). API bajo `/billing/anomalies/` (`detect`, `episodes`, `episodes/{id}` y `PATCH`), migración `002_anomaly_episodes` del backend y documentación. La consulta de JUP-030 (`/billing/anomalies/evaluate`) no cambia y queda como consulta de prueba sin guardar. Sin cambios en el frontend, el processor, el corpus del asistente ni los conjuntos de evaluación.

## Decisiones

Todas de Lucia, el 2026-10-12, en la exploración y la propuesta; recogidas en ADR-0019 y en `design.md`:

- Una anomalía es un episodio con tolerancia de 3 días; el sistema marca `no_longer_observed` y una persona cierra.
- Regla diaria de JUP-019 tal cual (`> 100` y `> 20 %`, estrictas y juntas). Se eligió primero una regla semanal y se cambió a la diaria al ver que la referencia anclada y el impacto acumulado ya obligaban a leer días, que la semanal dejaba P3 inalcanzable y que obligaba a añadir una regla nueva a las de negocio.
- Lo esperado: media de 7 días; con episodio en seguimiento, la referencia anclada.
- Criticidad sobre el impacto acumulado (pendiente de confirmar con la responsable de las reglas de negocio).
- Umbrales nominales en EUR y USD; otras monedas no se evalúan.
- «Detectar ahora» con marca de agua por tenant y un máximo de 7 días pendientes por pulsación (Lucia mantuvo el límite «de momento» aunque quitarlo costaba poco).
- Estados sin `acknowledged`; motivo obligatorio al cerrar; se guardan primer cambio desde `new` y cierre (MTTA y MTTR).
- El documento de reglas del corpus no se modifica: está fijado por sha256 en las evaluaciones de JUP-022, JUP-069 y JUP-070 (`RF-114-001`).
- ADR aplicable: [ADR-0019](../../../docs/adr/ADR-0019-cost-anomaly-episodes.md), `Proposed`.

## Revisión documental de anomalías (tarea 4.4)

Inventario: `git grep -il anomal` en todo el repositorio (unos 90 ficheros, más 39 en changes archivados). Las evidencias, planes y spikes de otras tarjetas son registros de su momento y no se editan; los changes archivados solo se leen.

Revisados y coherentes sin cambios: `docs/assistant-corpus/glossary/glossary.md` (definición de anomalía y baseline), `docs/assistant-corpus/product-architecture/economicon-product-context.md`, `docs/assistant-corpus/finops/azure-finops-mvp.md` (flujo de investigación), `apps/processor/app/agents/prompts.py` («anomalía confirmada» solo con evidencia), `docs/validation/README.md` y las preguntas JUP-069-016 a 019 (la regla que comprueban es la que aplican los episodios), `openspec/specs/synthetic-anomaly-data/spec.md` y `docs/demo/JUP-107/{README,anomalias,guion,preguntas}.md` (hablan de la consulta de JUP-030 y del panel con datos fijos, que sigue siendo cierto), `apps/frontend/README.md`, `openspec/specs/anomalies-panel/spec.md` y `apps/frontend/src/data/demo/anomaliesPanel.ts` (el panel sigue con su fixture hasta el change 2), `openspec/specs/frontend-brand-identity/spec.md`, `docs/api/azure-cost-ingestion-client.md` y `docs/data/azure-sample-dataset.md` (otro sentido de la palabra).

Corregido en este change:

- `docs/api/cost-anomalies.md`: la evaluación es la consulta de prueba sin guardar; JUP-038 usa episodios; la regla diaria ya se aplica en los episodios, con `>` frente a `>=`.
- `docs/architecture.md`: rutas de anomalías en el diagrama de billing (faltaba incluso la de JUP-030), tablas nuevas en el mapa de datos, «seis» a «ocho» tablas del backend y fila del backend.
- `docs/architecture/finops-agent-tools.md`: lo esperado, criticidad por impacto acumulado y fuente persistida para la herramienta futura.
- `apps/backend/README.md`: sección de episodios y nota de que la consulta de JUP-030 es de prueba.
- `docs/adr/README.md`, `docs/continuidad/deteccion-anomalias-coste.md` y su fila en `docs/continuidad/README.md`.

Registrado, no se puede tocar aquí:

- Corpus del asistente sin las aclaraciones de lo esperado, la criticidad y los estados: `RF-114-001` (para JUP-038, con regeneración de huellas en cadena).
- Panel `/anomalies` con fixture (criticidad Alta/Media/Baja y estados Pendiente/Investigando/Resuelto que no coinciden con el modelo): es el alcance del change 2 de esta tarjeta; no se registra como hallazgo aparte.
- La guía de anomalías de JUP-107 enseña la consulta de prueba y sigue siendo correcta. Con la regla diaria sus datos abren 4 episodios P2 (Compute, Analytics, Database y Storage) porque concentran el gasto de cada semana en uno o dos días: el conjunto se diseñó para comparar semanas. Los datos de demo del change 2 deben tener gasto diario; su limpieza es `RF-114-007`, confirmado en el stack real.

Enlaces: los enlaces locales de los Markdown tocados resuelven salvo dos de `docs/continuidad/README.md` (`metricas-funcionales-negocio.md` y `cobertura-etiquetado.md`) que ya estaban rotos en `develop` y no son de anomalías.

## Validación

Commits: implementación hasta `b048e43`; los comandos se ejecutaron sobre ese código.

| Comprobación | Resultado |
| --- | --- |
| Backend completo con CockroachDB real (`JUP086_COCKROACH_TEST_URL`, nodo desechable v24.1.11) | 1126 pasan, 21 omitidas (servicios externos), 145 fallan: todas en `test_*health*_jup047.py`, el fallo conocido de Windows (`socketpair` de asyncio frente a la guarda de red), igual en `develop` sin este cambio |
| Pruebas nuevas | 46 de la regla (`test_anomaly_episode_rules.py`), 6 de esquema, 11 de acceso a datos y 33 de API con CockroachDB real |
| JUP-030 y billing sin tocar sus pruebas | 151 pasan con CockroachDB real |
| Mutantes | 19, todos detectados (13 de la lógica, 6 de SQL con CockroachDB real) |
| `corepack pnpm lint` | 4/4 tareas correctas |
| `corepack pnpm openspec:validate` | 66/66 |
| `corepack pnpm jup:check:all`, `jup:check:test`, `repository:governance:test`, `tools/ci-workflow.test.mjs` | OK; 7, 13 y 12 pruebas en verde |
| `corepack pnpm jup:cleanup:check` | OK, 1236 archivos |
| `git diff --check develop` | sin errores |
| Stack real aislado (`docker compose -p jup114`, volúmenes nuevos) | migraciones `001` y `002` aplicadas; datos de JUP-107 cargados; 15/15 comprobaciones HTTP; cifras verificadas a mano con SQL independiente; `down -v` |

Incidencias de entorno, no del cambio: el fixture de billing da 60 s a las migraciones del processor y en esta máquina tardan más; se subió solo en la copia local y se revirtió antes de cada commit. pgvector arrancó `unhealthy` la primera vez y se resolvió repitiendo `up -d --wait`, como en JUP-030.
