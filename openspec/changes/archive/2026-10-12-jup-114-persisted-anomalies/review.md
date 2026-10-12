# Review JUP-114 (change 1) — Episodios de anomalía guardados

JUP: JUP-114 · Trello: https://trello.com/c/F492abeY · Rama: `feat/JUP-114-anomaly-circuit` · ADR: [ADR-0019](../../../../docs/adr/ADR-0019-cost-anomaly-episodes.md)

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
- ADR aplicable: [ADR-0019](../../../../docs/adr/ADR-0019-cost-anomaly-episodes.md), `Proposed`.

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
| Revalidación tras la pasada 2 (`53b5af9`, volúmenes nuevos) | columna `first_reviewed_by` creada; 18/18 comprobaciones HTTP, cifras idénticas; `down -v` |
| Pruebas de anomalías tras las correcciones (CockroachDB real) | 121 pasan; antes, 281 de anomalías, billing, presupuesto y aislamiento |

Incidencias de entorno, no del cambio: el fixture de billing da 60 s a las migraciones del processor y en esta máquina tardan más; se subió solo en la copia local y se revirtió antes de cada commit. pgvector arrancó `unhealthy` la primera vez y se resolvió repitiendo `up -d --wait`, como en JUP-030.

## Adversarial Review (pass 1)

Agente `adversarial-reviewer`, independiente, sobre `8035a3d..76952eb` con solo la spec, el diseño, el ADR y el contrato. Veredicto: **changes-requested** (un HIGH).

| ID | Severidad | Hallazgo | Reproducción del revisor | Resolución |
| --- | --- | --- | --- | --- |
| ADV-1 | HIGH | Tras `investigating` (alice) y `resolved` (bob) se pierde quién hizo el primer cambio; la spec («stores both actors and times») y el diseño se contradecían | Sonda con CockroachDB real: ninguna columna contiene `alice` | Columna `first_reviewed_by` en la misma migración `002` (no publicada), expuesta en la API; pruebas de acceso a datos y de API (`a499515`) |
| ADV-2 | MEDIUM | `POST /detect` con cuerpo rechazaba con 422 antes de 401/400/403 (contrato de orden de JUP-086) | Prueba temporal: sin token y con cuerpo, 422 | La comprobación del cuerpo depende de `get_active_tenant`; prueba parametrizada 401/400/403 sin llamadas al almacén |
| ADV-3 | MEDIUM | El motivo aceptaba controles C1, override bidi, separadores de línea, guion blando y un motivo de solo U+200B | `EpisodeStatusChange(status='resolved', reason='ok\x85x')` aceptado | Rechazo de categorías Unicode `C*`, `Zl`, `Zp` como `ownership_questions.py`; seis casos 422 y casos válidos aceptados |
| ADV-4 | LOW | Impacto exacto 499,996 se muestra `500.00` con `P3` | Sonda con 899.996 sobre 400 | Comportamiento correcto (criticidad sobre el valor exacto); escrito en la spec, la API y una prueba |
| ADV-5 | LOW (plausible) | Un PATCH que pierde por `40001` recibía `invalid_status_transition` | No reproducido de forma determinista | Excepción y código propios `status_change_conflict`; prueba con `OperationalError` 40001 simulado y prueba de API |
| ADV-6 | LOW | La detección y la lista abierta cargaban todo el histórico del tenant | Lectura del código | Lista filtrada en SQL; la detección lee solo episodios en seguimiento y el último de cada grupo; prueba con CockroachDB real del enlace al episodio anterior (el mutante que quita el último por grupo la hace fallar) |
| ADV-7 | LOW | El diseño citaba `SELECT … FOR UPDATE` que no se usa; el ADR decía evidencia «por crear»; `review.md` citaba la rama nueva | Lectura | Diseño y ADR corregidos; la rama `feat/JUP-114-anomaly-circuit` es la real tras el renombrado pedido por Lucia |

Ataques que resistieron (resumen del revisor): concurrencia de detecciones en el mismo tenant (3 a la vez, 5 rondas: una `completed`, dos `DetectionConflict`, un episodio); entre tenants sin falsos 409; PATCH simultáneos (un éxito); PATCH frente a detección sin escrituras parciales; igualdades estrictas y equivalencia exacta de la fórmula ×7; `service` nulo frente al literal `"null"`; aislamiento en todas las lecturas y escrituras y 404 idéntico; id de 200 000 caracteres; huecos y días perdidos; `test_schema_migration_ownership.py` del processor 6/6 con la nueva `002`; limitaciones documentadas.

Barrido de patrón: ADV-1 sin otras trazas de autores; ADV-2 es la única dependencia de ruta con lectura del cuerpo; ADV-3 se repite en `billing.py` (`tag_key`), `dependencies.py` (`X-Tenant-Id`) y dos tareas del processor, registrado como `RF-114-009`; ADV-4 y ADV-5 solo en este código.

Tras las correcciones: 281 pruebas de anomalías, billing, presupuesto y aislamiento con CockroachDB real en verde.

## Adversarial Review (pass 2)

Agente `adversarial-reviewer`, nueva instancia, sobre `8035a3d..9487a7a` centrado en `76952eb..9487a7a`, leyendo la pasada 1 solo al final. Veredicto: **accept** (sin BLOCKING ni HIGH).

| ID | Severidad | Hallazgo | Reproducción del revisor | Resolución |
| --- | --- | --- | --- | --- |
| ADV2-1 | MEDIUM | Ninguna prueba fijaba el orden ni el filtro de tenant de la subconsulta `DISTINCT ON` que elige el último episodio de cada grupo; la frase de la pasada 1 sobre el mutante solo valía para quitar la subconsulta entera | Mutantes `ASC, ASC` y sin `tenant_id` dentro de la subconsulta: 59 pruebas en verde | Prueba con CockroachDB real: dos episodios propios anteriores y uno posterior de otro tenant en el mismo grupo; el nuevo enlaza con el propio más reciente. Los dos mutantes la hacen fallar (`53b5af9`) |
| ADV2-2 | MEDIUM | El motivo aceptaba textos que se ven en blanco fuera de `C*`/`Zl`/`Zp`: rellenos Hangul (U+3164, U+FFA0, U+115F, U+1160), braille en blanco (U+2800) y marcas combinantes sueltas | `EpisodeStatusChange(status="resolved", reason="\u3164")` aceptado | Exigir al menos un carácter visible (letra, número, puntuación o símbolo que no sea relleno); 8 casos 422 y casos válidos aceptados; spec y API actualizadas |
| ADV2-3 | LOW | El filtro `C*` rechaza texto visible legítimo: emojis con ZWJ (U+200D), ZWNJ (U+200C) que necesitan el persa y escrituras índicas, y emojis más nuevos que la tabla Unicode de Python 3.12 (`Cn`) | `reason="ok \U0001F468\u200d\U0001F469"` rechazado | Aceptado por Lucia el 2026-10-12 como limitación registrada: `RF-114-010` |
| ADV2-4 | LOW | `first_reviewed_by` se añadió dentro de la `002` existente; el runner no tiene checksum, así que una base que ya aplicó la `002` anterior no recibe la columna (500 al listar). La evidencia de stack real era anterior | Sonda: quitar la columna y volver a migrar, `NoSuchColumnError` | La rama no está publicada y los volúmenes de la 5.2 se borraron. Revalidación con stack real y volúmenes nuevos sobre `53b5af9`. Una vez publicada, la `002` no se vuelve a editar: los cambios irán en `003` |

Ataques que resistieron (resumen del revisor): prueba de propiedades con 400 semillas y unos 9000 episodios que compara la detección con todo el histórico frente a solo «en seguimiento + último por grupo», con 0 discrepancias; la consulta SQL devuelve exactamente el conjunto esperado con dos tenants, servicio nulo y dos monedas; carrera real de dos PATCH con barrera tras la lectura (`StatusChangeConflict` y un ganador, `first_reviewed_by` coherente); impacto exacto 3499.972 guardado y mostrado `500.00` con P3; ADV-1 y ADV-2 comprobados; rechazo de U+0085, U+202E, U+2028, U+2029, U+00AD, U+200B solo, etiquetas y surrogates; 500 caracteres y 500 emojis astrales aceptados.

Barrido de patrón: `DISTINCT ON` solo en este punto; el criterio Unicode de `ownership_questions.py` escapa en vez de validar y no sufre ADV2-2; filtros débiles ajenos ya en `RF-114-009`; la `002` es la única migración editada en la rama.

## Riesgos

- Criticidad por impacto acumulado pendiente de confirmar con la responsable de las reglas de negocio (anotado en el ADR y la API).
- Pruebas con CockroachDB real fuera de la CI (`RF-107-002`): ejecutadas en local.
- Limitaciones de producto escritas en el ADR, la API y `LIMITATIONS`; trabajo futuro en `RF-114-001` a `RF-114-008`.
- La `002` no se vuelve a editar una vez publicada (ADV2-4).

## Hallazgos registrados

`RF-114-001` a `RF-114-010` en `openspec/findings/backlog.md`; `RF-114-010` aceptado por Lucia el 2026-10-12.

## Human Approval

- Change: jup-114-persisted-anomalies
- Approval type: post-review
- Decision: approved
- Approver: Lucia
- Date: 2026-10-12
- Adversarial review: accept (pass 2) | accepted findings: ADV2-3 (`RF-114-010`, limitación registrada)
- Archive decision: archive
- Notes: change 1 de 3 de JUP-114 (backend de episodios). Se archiva en la rama `feat/JUP-114-anomaly-circuit` sin abrir PR: los tres changes van en un solo PR al terminar el último. Pendiente en Trello: revisión y validación de las personas con esos roles, confirmación de la criticidad por impacto acumulado, y los changes 2 (panel y datos de demo) y 3 (ejecución periódica y avisos).
