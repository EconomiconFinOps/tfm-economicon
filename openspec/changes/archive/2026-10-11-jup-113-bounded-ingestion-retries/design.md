JUP-113 — Acotar los reintentos de la cola de ingesta. Carril `standard`.

## Context

Motivación y alcance en `proposal.md`; requisitos en `specs/document-ingestion-handoff/spec.md` y
`specs/llm-provider-routing/spec.md`. Aquí solo el estado que condiciona el enfoque, leído en el
repositorio el 2026-10-11 sobre `develop` en `8511fb1f`. Nada de esta sección se ha ejecutado contra
un broker todavía; la tarea 1 lo reproduce antes de tocar producto.

**Cómo trata hoy el worker cada resultado** (`apps/processor/app/workers/runner.py`, líneas 80 a 91):

| Resultado de `IngestTask.execute` | Estado del trabajo | Mensaje |
| --- | --- | --- |
| Termina bien | `completed` | `ack` |
| `InvalidJobMessage` | sin cambios | `nack(requeue=False)` |
| `ProviderError` | `failed` | `nack(requeue=False)` |
| Cualquier otra excepción | `failed` si falló el pipeline; sin cambios si falló antes | `nack(requeue=True)` y se relanza |

La última fila no tiene tope. Al relanzar, `run_forever` registra `worker_loop_failed` y espera 2 s;
esa espera es el único intervalo entre intentos. El worker consume con `basic_get` y `prefetch=1`
(`apps/processor/app/clients/rabbitmq_queue.py`).

**Por dónde entra `RF-086-004`.** `IngestJobRequest.validate_source`
(`apps/backend/app/schemas/jobs.py`) solo rechaza el `source` vacío. El pipeline ejecuta `normalize`,
`chunk` y `analyze`; en `analyze`, `prepare_agent_input` llama a `normalize_source`
(`apps/processor/app/agents/guardrails.py`), que lanza `AgentGuardrailError` si el valor no cumple
`SAFE_SOURCE`. `IngestTask` lo captura en su `except Exception`, marca `failed` y lanza
`RuntimeError("ingestion_failed") from None`. El fallo ocurre antes de llamar al proveedor y antes de
`embed_and_store`, así que no gasta inferencia ni escribe vectores. En la reentrega el trabajo está
`failed`, no `completed`, y se repite todo.

**Por dónde entra `RF-054-001`.** `apps/processor/app/tasks/ingest.py`, línea 74, decodifica el
`result` de un trabajo `completed` fuera del `try`. Un `JSONDecodeError` no es `InvalidJobMessage` y
cae en la última fila de la tabla sin cambiar el estado.

**Restricciones.**

- `IngestTask` aplana a propósito la causa (`from None`) para no filtrar secretos ni contenido
  (JUP-053). Las pruebas `test_rf053_003_*` y `test_worker_loop_sanitizes_dependency_exception_and_cause`
  lo fijan.
- `update_job_status` (`apps/processor/app/db/database.py`) reescribe `result` en cada transición,
  también al pasar a `running`. Guardar un contador de intentos en `result` obligaría a cambiar ese
  SQL.
- Backend y processor son dos aplicaciones Python con un paquete `app` cada una; no comparten código
  (`packages/` solo contiene `shared-config`).
- No existe lectura del estado de un trabajo en la API (`RF-104-003`): un trabajo descartado solo se
  ve en la base, en los registros y en la alerta de fallos de ingesta.
- Las pruebas con RabbitMQ, CockroachDB y pgvector reales son opt-in y CI las omite (`RF-096-004`).
- ADR-0008, decisión 2, y el change `jup-086-tenant-isolation-contract` (sin archivar) dicen que los
  fallos transitorios siguen reintentables y que no se define límite. Este cambio define uno.

## Goals / Non-Goals

**Goals:**

- Que ningún fallo atribuible a un trabajo retenga la cola: un trabajo con la entrada inválida sale
  en una entrega y un fallo no clasificado en dos como máximo.
- Que un `source` que el processor no admite no llegue a crear un trabajo.
- Que el worker no descarte nunca el mensaje de un trabajo que sigue en `queued` o `running`, salvo
  los mensajes inválidos que ya se descartan hoy.
- Que la regla del `source` no pueda divergir entre los dos servicios sin que falle una prueba.
- Conservar el saneado de errores y registros de JUP-053 y el aislamiento de JUP-086.

**Non-Goals:**

- Backoff, tope configurable, DLQ, cola de cuarentena o cambio del tipo de cola.
- Contar intentos de forma persistente.
- Distinguir una caída de pgvector o de los embeddings de un fallo determinista del trabajo.
- Proteger frente a un mensaje que mata el proceso antes de que el worker pueda responder al broker.
- Reencolar o recuperar trabajos que quedaron `failed`.
- Cambiar la pantalla de ingesta, el motivo `ingestion_failed` o las métricas.

## Decisions

### 1. La admisión aplica la misma regla que el processor y no normaliza

El backend acepta un `source` si `value.strip().lower()` cumple `^[a-z0-9][a-z0-9._-]{0,63}$` con
coincidencia completa, que es exactamente lo que hace `normalize_source`. Si no, la validación de
`IngestJobRequest` falla y el manejador de validación vigente responde el 422 saneado, antes de
reservar publicación. El valor admitido se guarda y se publica literal.

- **Por qué no normalizar en el backend:** JUP-086 decidió conservar el valor literal, y el processor
  compara el `source` del sobre con el guardado; `test_ingest_padded_source_is_preserved` lo fija con
  ` azure `.
- **Por qué no relajar `SAFE_SOURCE`:** el `source` se interpola en el prompt del agente; la regla es
  un guardrail y no un formato arbitrario.
- **Por qué no exigir la lista de fuentes Azure admitidas:** una fuente no admitida ya tiene salida
  definida (`status: unsupported` y el trabajo se completa), y el valor por defecto de la pantalla,
  `aws-cur`, dejaría de funcionar.

### 2. Una tabla de casos compartida vigila la deriva

`docs/api/ingest-source-contract-cases.json` lista valores aceptados y rechazados, siguiendo el
precedente de `docs/api/azure-cost-query-contract-cases.json`. Una prueba del backend y otra del
processor la recorren; cada una comprueba su mitad. Incluye los valores de los productores conocidos
(`aws-cur`, `local-smoke`, `cd-smoke`, `assistant-corpus`), los límites de longitud (64 y 65), relleno
y mayúsculas, espacios interiores, primer carácter no alfanumérico, y caracteres Unicode que
`lower()` convierte en ASCII.

- **Alternativa descartada, paquete Python compartido:** no existe ninguno y crearlo cambia la
  construcción de las dos imágenes.
- **Alternativa descartada, comparar el texto de la expresión regular:** no cubre `strip` ni `lower` y
  se rompe con un cambio de formato.
- **Límite:** una divergencia fuera de los casos de la tabla no se detecta.

### 3. `IngestTask` dice si registró el fallo y si es permanente

El worker necesita distinguir tres cosas que hoy llegan como la misma excepción genérica. Se
introducen dos tipos, sin cambiar los mensajes:

- En `guardrails.py`, un error de entrada (subclase de `AgentGuardrailError`) que lanzan
  `normalize_source` y `prepare_agent_input`. `AgentResponseError` no cambia. Las pruebas que esperan
  `AgentGuardrailError` siguen pasando porque es la clase base.
- En `ingest.py`, un error de «fallo registrado» (subclase de `RuntimeError`, con el mismo texto
  `ingestion_failed` y lanzado con `from None`) que lleva un indicador de permanente. `IngestTask` lo
  lanza después de `mark_failed`: permanente si la causa es el error de entrada, no permanente para
  cualquier otra excepción. `ProviderError` se sigue relanzando tal cual.

Lo que no sea ninguno de esos tipos significa que el estado no se pudo leer o registrar: fallo de
`fetch_authorized_job`, de `mark_running` o de `mark_failed`.

- **Alternativa descartada, validar el `source` en `IngestTask` antes del pipeline:** duplicaría la
  regla dentro del processor y dejaría fuera las demás comprobaciones de entrada.
- **Alternativa descartada, clasificar por tipo de excepción en el worker:** `IngestTask` aplana la
  causa por seguridad; el worker no debe verla.

### 4. El tope es la marca de reentrega del broker: un reintento

`QueueMessage` gana un campo `redelivered`, con valor por defecto `False`, que `blocking_pop` rellena
con el de la respuesta de `basic_get`. El worker reencola un fallo registrado y no permanente solo si
`redelivered` es `False`.

- **Por qué:** no añade estado, esquema ni infraestructura, y `redelivered=False` garantiza que es la
  primera entrega.
- **Lo que no garantiza:** `redelivered=True` también aparece cuando la entrega anterior se
  interrumpió sin respuesta (reinicio del worker, conexión caída). En ese caso el primer fallo ya
  descarta. El tope es «una reentrega como máximo», no «dos intentos siempre».
- **Alternativa descartada, contador en `result`:** exacto y configurable, pero exige cambiar el SQL
  de transiciones (ver Context) y el contenido de `result`, que varias pruebas fijan como
  `{"error": "ingestion_failed"}`.
- **Alternativa descartada, columna de intentos:** es una migración.
- **Alternativa descartada, cola quorum con `x-delivery-limit`:** los dos servicios declaran la cola
  como clásica y duradera; redeclararla con otros argumentos falla sobre una cola existente y cambia
  el tipo de cola, que la tarjeta excluye.
- **Alternativa descartada, DLQ:** excluida por la tarjeta.

Esta decisión depende de que RabbitMQ marque la reentrega con `basic_get` tras `nack(requeue=True)` y
tras un cierre de conexión. La tarea 1.3 lo comprueba con un broker real antes de implementar; si no
se cumple, se para y se vuelve a este diseño.

### 5. Solo se descarta con estado terminal registrado

Tabla resultante. «Cambia» indica si difiere de hoy.

| Qué ocurre | Estado del trabajo | Mensaje | Cambia |
| --- | --- | --- | --- |
| Termina bien | `completed` | `ack` | No |
| Mensaje inválido | sin cambios | `nack` sin reencolar | No |
| Resultado guardado corrupto o sin forma de objeto | sin cambios | `nack` sin reencolar | Sí |
| `ProviderError` | `failed` | `nack` sin reencolar | No |
| Entrada rechazada por el guardrail | `failed` | `nack` sin reencolar, no se relanza | Sí |
| Fallo no clasificado, primera entrega | `failed` | `nack` con reencolado y se relanza | No |
| Fallo no clasificado, reentrega | `failed` | `nack` sin reencolar, no se relanza | Sí |
| No se pudo leer o registrar el estado | el que tuviera | `nack` con reencolado y se relanza | No |

La última fila conserva el reencolado sin tope a propósito. Descartar ahí dejaría el trabajo en
`queued` o `running` sin mensaje y sin que nadie pueda verlo. Tampoco es el bucle que describe el
finding: lo causa el almacén y no el mensaje, y mientras el almacén no responde ningún trabajo puede
avanzar.

**Diferencia con la tarjeta.** El criterio 5 dice que un error no clasificado se reintenta un número
fijo de veces y después el trabajo queda `failed`. Con esta decisión eso se cumple siempre que el
estado se pueda registrar; si no se puede, el mensaje espera. Hay que reflejarlo en la tarjeta al
aprobar el diseño.

- **Alternativa descartada, tope también para esa fila:** una caída de CockroachDB de unos segundos
  vaciaría la cola y dejaría todos los trabajos en `queued` para siempre.

### 6. El resultado de un trabajo completado se valida al decodificar

En la reentrega de un `completed`: si el resultado es texto, se decodifica dentro de una guarda; un
error de decodificación, o un valor que no es objeto ni nulo, lanza `InvalidJobMessage`. Nulo o
ausente devuelve `{}`, como fija hoy `test_completed_redelivery_returns_stored_result_in_any_representation`.
El texto `null` pasa a devolver `{}` en vez de `None`, para que SQLite (texto) y CockroachDB (JSONB ya
decodificado) den lo mismo.

### 7. Diagnóstico con nombres de evento fijos y sin métricas nuevas

Los dos descartes nuevos registran un evento de nivel `warning` con nombre fijo, uno para la entrada
rechazada y otro para el reintento agotado, con el identificador de correlación que ya aporta el
contexto y sin más campos. No se registra el `source`, el contenido ni la causa. El contador
`processor_ingest_jobs_failed_total` sigue sumando en cada `mark_failed`: una vez para la entrada
rechazada y hasta dos para un fallo no clasificado. La alerta de JUP-045 no cambia.

### 8. Sin configuración nueva

El tope es fijo. Un valor configurable necesitaría contar intentos (decisión 4), y un interruptor
para volver al comportamiento anterior reabriría el finding.

### 9. Pruebas: reproducir primero, y qué se acredita en cada nivel

- **Antes de implementar (tarea 1):** reproducir `RF-086-004` con Compose en un proyecto aislado y
  comprobar la marca de reentrega con RabbitMQ real. El análisis del finding es estático hasta
  entonces.
- **Offline, en CI:** admisión del backend con SQLite y cola doblada; `IngestTask` y el worker con
  repositorio SQLite y cola doblada, pasando `redelivered` a mano; lectura de `redelivered` con un
  canal doblado.
- **Opt-in, fuera de CI:** con el `real_queue` y las bases reales de
  `test_tenant_isolation_integration.py`, un trabajo envenenado seguido de uno válido de otro tenant,
  y un reintento agotado. Se ejecutan en contenedor y se anotan como no cubiertas por CI.
- **Pruebas existentes:** `test_ingest_task.py:225`, `test_secret_boundaries.py:428` y
  `test_tenant_isolation_jobs.py:176` y `:293` afirman `requeue=True` en una primera entrega con un
  error no clasificado. Ese caso no cambia y `redelivered` vale `False` por defecto, así que deben
  seguir pasando sin editarlas. Si alguna falla, no se adapta la prueba: se para y se revisa la
  implementación.
- **Mutación:** sobre la validación del backend, la clasificación en `IngestTask`, la lectura de
  `redelivered` y las ramas del worker. Cada mutante superviviente se cubre con un caso o se
  justifica en `review.md`.

### 10. Dónde van los requisitos

Los requisitos nuevos se añaden a `document-ingestion-handoff`. Su requisito «Preserve failure
handling and request correlation» no se modifica porque sigue siendo cierto: cuando hay reintento,
conserva el sobre y el identificador de correlación. En `llm-provider-routing` se modifica una frase
que deja de ser verdad. `tenant-isolation` no se toca porque no está en `openspec/specs/`.

### 11. ADR

Se añade `docs/adr/ADR-0019-ingestion-retry-policy.md`, estado `Proposed`, enlazado a JUP-113 y a
este change. Recoge las decisiones 4 y 5 y su coste. No sustituye a ADR-0008: complementa su
decisión 2, que dejaba el límite sin definir.

## Risks / Trade-offs

- **Una caída de pgvector o de los embeddings que cubra los dos intentos marca `failed` los trabajos
  en cola**, que hoy esperarían, y hay que volver a enviarlos. Medido en el stack real con pgvector
  parado: unos 10 s hasta el descarte (dos intentos de unos 4 s separados por la espera de 2 s); un
  fallo que se rechace más rápido lo acortaría → el fallo queda registrado y dispara la
  alerta de JUP-045; se documenta en el ADR y en el README del processor. Distinguir esa caída de un
  fallo del trabajo queda como mejora posterior.
- **Nadie ve en la interfaz que un trabajo quedó `failed`** (`RF-104-003`) → fuera de alcance; el
  cambio no lo empeora respecto a `ProviderError`, que ya descarta así.
- **Una reentrega por interrupción deja el trabajo sin reintento** → aceptado y escrito en la spec.
- **Un mensaje que mata el proceso se reentrega sin fin**, porque el worker nunca llega a responder →
  fuera de alcance; se registra como finding si la reproducción lo muestra.
- **Un fallo determinista al leer o registrar el estado seguiría en bucle** → esa rama solo contiene
  lecturas y escrituras del estado; los identificadores ya se validan antes (`RF-086-001`). Se anota
  como límite.
- **El 422 nuevo rompe a un cliente que enviara otro formato de `source`** → los productores del
  repositorio están en la tabla de casos; se documenta en el README del backend.
- **La pantalla de ingesta puede no explicar el 422** → no se cambia; la tarea 6.4 comprueba qué
  muestra y, si no es comprensible, se registra un finding.
- **Los trabajos ya envenenados en una cola viva pasan a `failed` al desplegar** → es el efecto
  buscado; se anota en la evidencia.
- **Las pruebas con broker real no corren en CI** (`RF-096-004`) → se ejecutan a mano y la evidencia
  dice qué no cubre CI.
- **El change `jup-086` sin archivar quedará con una frase desactualizada** → no se edita un change
  ajeno; se anota en la evidencia y se avisa a quien lo lidera.

## Migration Plan

No hay migración de datos ni de cola. Backend y processor se pueden desplegar en cualquier orden: el
backend solo deja de crear trabajos envenenados y el processor solo deja de reencolarlos. Volver
atrás es revertir el commit; ningún formato guardado cambia.

## Open Questions

Ninguna que cambie las specs o las tareas. Queda para después, fuera de esta tarjeta, si la pantalla
de ingesta debe explicar el formato del campo Source.
