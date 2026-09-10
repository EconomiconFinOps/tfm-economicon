JUP: JUP-042

## Context

`backend` y `processor` son dos servicios FastAPI independientes, cada uno con su propio `app/core/logging.py` casi idéntico: `logging.basicConfig` con formato de texto plano (`%(asctime)s %(levelname)s [%(name)s] %(message)s`), sin salida JSON y sin ningún identificador que permita agrupar las líneas de log generadas por una misma petición. Varios módulos ya usan `logging.getLogger(__name__)` directamente (`clients/azure_cost.py`, `tasks/azure_cost_ingest.py`, `workers/runner.py`, entre otros).

No existe en el repo ninguna capability de logging previa (`openspec/specs/` solo tiene `architecture-decisions`, `demo-auth-credentials`, `health-status`), ni ninguna dependencia de logging estructurado en `requirements.txt` de ninguno de los dos servicios.

## Goals / Non-Goals

**Goals:**

- Logs de `backend` y `processor` en JSON estructurado (clave-valor), listos para ser consumidos por un agregador de logs en el futuro sin parseo de texto libre.
- Un `request_id` (UUID) por petición HTTP entrante, presente automáticamente en cada línea de log generada durante el ciclo de vida de esa petición, sin pasarlo a mano en cada llamada a logger.
- Mecanismo homogéneo entre `backend` y `processor` (misma librería, mismo patrón de middleware).

**Non-Goals:**

- Logging de frontend (error tracking de cliente): problema distinto, no cubierto por esta HU.
- Agregación/envío a un sistema centralizado externo (Loki, ELK, etc.): esta HU solo produce el JSON estructurado; el transporte/almacenamiento queda fuera de alcance.
- Métricas técnicas (latencia, throughput) y trazabilidad distribuida entre servicios: son JUP-043 y JUP-044, tarjetas separadas que se apoyarán en el `request_id` introducido aquí.
- Migrar retroactivamente cada línea de log existente a la nueva API: se establece el patrón y se migra el arranque de cada servicio; el resto se migra de forma incremental (detalle en `tasks.md`).

## Decisions

### Usar `structlog` como nueva dependencia, en vez de `logging` estándar a mano

`structlog` resuelve de forma probada las dos piezas necesarias: serialización a JSON vía `processors` encadenables, e integración nativa con `contextvars` (`structlog.contextvars.bind_contextvars`) para propagar el `request_id` sin pasarlo explícitamente en cada llamada. La alternativa (un `logging.Formatter` JSON a mano + un `logging.Filter` que lea `contextvars`) es viable con la librería estándar y evita una dependencia nueva, pero reimplementa algo que `structlog` ya resuelve y prueba. No es una decisión arquitectónica duradera ni cara de revertir (sin coste, sin vendor lock-in, sustituible por stdlib en cualquier momento) — **no requiere ADR**, a diferencia de `ADR-0002` (LiteLLM/OpenRouter), que sí afecta a coste, privacidad y proveedor externo.

### `request_id` generado por middleware FastAPI + `contextvars`, no por parámetro explícito

Un middleware registrado en cada `app/main.py` genera el UUID al entrar la petición y lo vincula al contexto de `structlog` (`bind_contextvars`) antes de pasar la petición a la ruta correspondiente. Así cualquier `logger.info(...)` ejecutado durante esa petición —incluso en capas internas que no reciben el `request_id` como argumento— lo incluye automáticamente. La alternativa (pasar `request_id` como parámetro explícito a través de cada función) ensuciaría firmas de funciones que no deberían conocer detalles de logging.

### Alcance: `backend` y `processor`, mismo patrón, implementaciones independientes

No se extrae a un paquete compartido en `packages/` en esta HU: ambos servicios son procesos independientes con sus propios `requirements.txt`, y una librería compartida de logging sería una abstracción prematura para dos únicos consumidores con el mismo patrón. Si aparece un tercer servicio Python que lo necesite, se revalúa extraer un paquete común.

### Frontend fuera de alcance

Confirmado con el usuario: el frontend es una SPA sin proceso de servidor propio; no genera logs de la misma naturaleza que `backend`/`processor`. Instrumentarlo (captura de errores de cliente) es un problema distinto, candidato a una tarjeta separada.

## Risks / Trade-offs

- **Nueva dependencia en dos servicios** → riesgo bajo: `structlog` es ampliamente usada con FastAPI, sin dependencias transitivas pesadas, sustituible por stdlib si se retira en el futuro.
- **Migración incremental deja logs mezclados (JSON nuevo + texto plano antiguo) durante un tiempo** → se acepta como transición; `tasks.md` prioriza migrar primero los puntos de entrada de cada servicio y los módulos con logging ya existente, dejando claro en `review.md` qué quedó pendiente si no se cubre todo en una sola HU.
- **`contextvars` en código asíncrono puede filtrarse entre tareas si se usa mal** → mitigado usando únicamente la API de `structlog.contextvars` (diseñada para este caso) y limpiando el contexto al finalizar cada request vía el propio middleware.

## Migration Plan

1. Añadir `structlog` a `requirements.txt` de `backend` y `processor`.
2. Reescribir `app/core/logging.py` de cada servicio para configurar `structlog` con salida JSON.
3. Añadir el middleware de `request_id` en `app/main.py` de cada servicio.
4. Migrar los `logger = logging.getLogger(__name__)` existentes a `structlog.get_logger(__name__)` en los módulos ya identificados (`clients/azure_cost.py`, `tasks/azure_cost_ingest.py`, `workers/runner.py`, y equivalentes en `backend`).
5. Verificar manualmente en local (`docker compose up`) que una petición HTTP real produce logs JSON con el mismo `request_id` en todas sus líneas.

Rollback: revertir el commit/PR; no hay migración de datos ni cambio de esquema, solo código de aplicación y una dependencia nueva.

## Open Questions

- Nivel de log por defecto en producción vs. desarrollo local (INFO vs. DEBUG): se deja como constante de configuración simple en esta HU; no bloquea la implementación.
