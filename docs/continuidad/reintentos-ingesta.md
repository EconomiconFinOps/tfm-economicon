# Reintentos de la cola de ingesta — JUP-113

Última actualización documental: 2026-10-11. Esta nota no repite el alcance de la tarjeta, que vive en [Trello](https://trello.com/c/JaHmg0fs).

## Estado

- Rama `fix/JUP-113-bounded-ingestion-retries`, creada desde `develop` en `8511fb1f`. Cierra técnicamente `RF-086-004` (High) y `RF-054-001` (Low) de `openspec/findings/backlog.md`, que pasan a `Fixed` con la salvedad de que integración y validación humana siguen pendientes.
- OpenSpec: `openspec/changes/archive/2026-10-11-jup-113-bounded-ingestion-retries/` (deltas de `document-ingestion-handoff` y `llm-provider-routing`), archivado el 2026-10-11 tras el gate posterior a la revisión de Victor; las specs principales ya incluyen los cinco requisitos añadidos y el modificado. ADR: [ADR-0019](../adr/ADR-0019-ingestion-retry-policy.md), en `Proposed`, pendiente de ratificar en la revisión de la PR.
- Evidencia: [JUP-113-validation.md](../evidence/JUP-113-validation.md), con la reproducción antes de corregir, las pruebas con servicios reales y el recorrido con Compose sobre la rama. La PR aún no está abierta (la abre Victor).
- Producto cambiado: `apps/backend/app/schemas/jobs.py` y, en el processor, `agents/guardrails.py`, `tasks/ingest.py`, `clients/rabbitmq_queue.py` y `workers/runner.py`.

## Decisiones que no se deducen del código

- **Un fallo no clasificado se reintenta una sola vez**, con la marca `redelivered` de RabbitMQ y sin contador, columna ni cola nueva. Es «una reentrega como máximo» y no «dos intentos siempre»: una primera entrega interrumpida ya llega como reentrega.
- **Si no se puede leer el job o registrar su estado, el mensaje se reencola sin tope.** Es deliberado y es el único caso en que el bucle original puede persistir: descartar dejaría el job en `queued` o `running` sin mensaje y sin que nadie lo vea. Se aparta del criterio 5 de la tarjeta, que la aprobación matizó.
- **El coste asumido:** si pgvector o los embeddings fallan lo bastante para los dos intentos (~10 s medidos con pgvector parado), los jobs de ese intervalo quedan `failed` y hay que reenviarlos. Está en el ADR y en `RF-113-003`. La aprobación decía «más de unos 2 s»; era inexacto y está corregido con una adenda.
- **La regla del `source` está duplicada** en backend y processor a propósito (no comparten código). Lo que impide que diverjan es `docs/api/ingest-source-contract-cases.json`, que prueban los dos servicios.
- **Una excepción a «no se adapta ninguna prueba existente»:** `test_secret_boundaries.py` pasó a esperar `IngestionFailed` en el registro `worker_loop_failed`. Decidió Victor y consta como adenda en la aprobación; el cambio de la línea lo hizo a mano porque el hook del harness bloquea editar tests commiteados.

## Qué tocar si cambia algo

- La regla del `source`: `SAFE_SOURCE` del processor y `SAFE_SOURCE` de `apps/backend/app/schemas/jobs.py`, siempre las dos, y la tabla de casos; ejecutar `test_ingest_source_admission.py` en el backend y `test_ingest_source_contract.py` en el processor.
- La política de descarte: `workers/runner.py`, rama `IngestionFailed`, y la tabla del [README del processor](../../apps/processor/README.md#fallos-reintentos-y-descarte-jup-113). Si el broker dejara de poner `redelivered` en `basic_get`, hay que revisar el ADR.
- Un tipo nuevo de fallo permanente: debe heredar de `AgentInputError` si es de entrada; cualquier otra excepción del pipeline se trata como no clasificada.

## Pendiente

- Revisión de código y validación funcional por las personas con esos roles en Trello; ninguna se da por hecha aquí.
- Ratificar o rechazar ADR-0019 y confirmar en Trello el matiz del criterio 5.
- Las pruebas con servicios reales (`test_ingestion_retry_integration.py`) **no corren en CI** (`RF-096-004`); se ejecutaron a mano. La decisión de reencolar sin tope ante una caída real de CockroachDB no se ejercitó con una caída real.
- Findings abiertos: `RF-113-001` (la pantalla de ingesta muestra el cuerpo crudo del 422), `RF-113-002` (el contrato `tenant-isolation` de JUP-086 y ADR-0008 dicen que no hay límite de reintentos) y `RF-113-003` (los jobs descartados por una caída no se reprocesan).
- Limpieza del entorno de pruebas: el proyecto Compose `jup113-repro` y sus volúmenes se borran con `docker compose -p jup113-repro down -v`.
