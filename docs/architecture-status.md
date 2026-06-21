# Estado de cumplimiento arquitectónico

**Backbone:** [`ARCHITECTURE.md`](./ARCHITECTURE.md)

**Política:** bloqueo por alcance con remediación incremental

**Última revisión:** 2026-06-19

## 1. Uso del registro

Este documento contiene desviaciones verificadas entre el código actual y el backbone técnico. No modifica ni relaja ningún invariante.

- `BLOCKING`: impide aprobar nuevas funcionalidades que alcancen o dependan del gap. No impide aprobar una HU de remediación que lo cierre sin introducir ni empeorar otras desviaciones.
- `CLOSED`: existe evidencia verificable de corrección.

Un gap solo puede cerrarse cuando se cumple íntegramente su condición de cierre y el reviewer valida las evidencias. El owner es un rol responsable, no una autorización para aceptar riesgo.

Los cambios exclusivos del harness o de documentación pueden aprobarse mientras no modifiquen el runtime, oculten gaps o relajen invariantes sin una ADR aprobada.

## 2. Resumen

| Estado | Total |
|---|---:|
| `BLOCKING` | 13 |
| `CLOSED` | 0 |

## 3. Gaps bloqueantes

| ID | Invariante | Estado | Evidencia actual | Componente | Owner | Condición verificable de cierre |
|---|---|---|---|---|---|---|
| `GAP-001` | `ARCH-01` | `BLOCKING` | `fetch_messages` y varios updates consultan solo por ID; migrations sin FKs tenant-scoped suficientes | Backend, CockroachDB | Backend owner | Todas las operaciones tenant-scoped filtran tenant; constraints e índices aplicados; suite cross-tenant positiva y negativa aprobada |
| `GAP-002` | `ARCH-01`, `ARCH-04` | `BLOCKING` | `IngestJobRequest` acepta `tenant_id` y el processor confía en el payload completo del mensaje | Backend, Processor | Backend owner | API deriva tenant del contexto; mensaje contiene envelope mínimo; processor recarga y valida el job canónico por job + tenant |
| `GAP-003` | `ARCH-03` | `BLOCKING` | El endpoint inserta el job y después llama directamente a `basic_publish` | Backend, RabbitMQ | Platform owner | Job y outbox se crean en una transacción; publisher separado usa confirms; tests de caída y duplicado aprobados |
| `GAP-004` | `ARCH-05`, `ARCH-06` | `BLOCKING` | Todo error ejecuta `nack(requeue=True)` sin contador, backoff ni DLQ | Processor, RabbitMQ | Processor owner | Retry budget, backoff, clasificación de errores, DLQ y estado `dead_lettered` implementados y probados |
| `GAP-005` | `ARCH-05` | `BLOCKING` | No existe deduplicación persistente; una redelivery repite LLM y embeddings | Processor | Processor owner | Deduplicación por mensaje/job-versión y checkpoints de efectos impiden repetir llamadas confirmadas; tests de redelivery aprobados |
| `GAP-006` | `ARCH-06` | `BLOCKING` | Estados se actualizan sin validar estado previo ni conservar historial de intentos | Processor, CockroachDB | Backend owner | Máquina de estados atómica, historial de intentos y tests de transición válida/inválida implementados |
| `GAP-007` | `ARCH-07`, `ARCH-14` | `BLOCKING` | Backend comparte un `BlockingConnection`/channel Pika global; no hay puerto ni aislamiento por thread | Backend | Backend owner | Publisher detrás de puerto, thread-safe o asíncrono, con lifecycle y concurrencia probados |
| `GAP-008` | `ARCH-14` | `BLOCKING` | `PROCESSOR_CONCURRENCY` está configurado pero `run_all.py` crea un único worker y `prefetch_count=1` | Processor | Processor owner | Configuración crea concurrencia efectiva y acotada; prefetch coherente; tests de carga y shutdown aprobados |
| `GAP-009` | `ARCH-02`, `ARCH-08`, `ARCH-12` | `BLOCKING` | Ownership de pgvector implícito, sin versión de proyección, reconciliación ni contrato formal de lectura | Backend, Processor, pgvector | Data owner | Owner, `VectorSearchPort`, versión de proyección, expand/contract y reconstrucción/reconciliación quedan implementados y probados |
| `GAP-010` | `ARCH-08` | `BLOCKING` | Tablas vectoriales sin índice de búsqueda vectorial ni validación de capacidad representativa | PostgreSQL/pgvector | Data owner | Índice y filtros tenant definidos; explain plan/benchmark con volumen objetivo cumple el TDR aprobado |
| `GAP-011` | `ARCH-09` | `BLOCKING` | Prompt inline en `AgentRuntime`; no hay gateway, redacción, budgets, trazabilidad de modelo/coste ni políticas de proveedor | Processor | AI owner | Gateway y prompt registry versionado, controles de datos, límites, métricas y evaluaciones de regresión aprobados |
| `GAP-012` | `ARCH-10`, `ARCH-11` | `BLOCKING` | Secrets por defecto, Cockroach `--insecure`, logs de texto sin correlation ID y sin métricas operativas | Todos, infraestructura | Platform owner | Perfil local aislado; producción fail-fast ante secrets inseguros; logs estructurados, redacción, IDs, métricas y readiness probados |
| `GAP-013` | `ARCH-13` | `BLOCKING` | Frontend sin tests; cobertura limitada de integración, contratos, fallos y cross-tenant | Todos | QA owner | Suites frontend, integración y contratos cubren los escenarios obligatorios de `ARCH-13` y pasan en CI |

## 4. Orden obligatorio de remediación

1. **Seguridad multitenant:** `GAP-001`, `GAP-002`.
2. **Consistencia DB-cola:** `GAP-003`.
3. **Retries, estados e idempotencia:** `GAP-004`, `GAP-005`, `GAP-006`.
4. **Contratos y ownership de datos:** `GAP-009`, `GAP-010`.
5. **Límites de infraestructura y concurrencia:** `GAP-007`, `GAP-008`.
6. **LLM, privacidad y coste:** `GAP-011`.
7. **Seguridad operativa y observabilidad:** `GAP-012`.
8. **Quality gates completos:** `GAP-013`.

Las tareas de una misma etapa solo pueden paralelizarse cuando no comparten migraciones, contratos ni archivos y disponen de estrategia de integración explícita.

## 5. Historial de cierres

| Gap | Fecha | PR/HU | Evidencias | Reviewer |
|---|---|---|---|---|
| — | — | — | — | — |
