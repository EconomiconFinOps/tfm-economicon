# ADR-0019: Política de reintentos de la cola de ingesta

- Status: Proposed
- Date: 2026-10-11
- Related JUP/OpenSpec: JUP-113, [proposal](../../openspec/changes/jup-113-bounded-ingestion-retries/proposal.md), [design](../../openspec/changes/jup-113-bounded-ingestion-retries/design.md#decisions)
- Trello: https://trello.com/c/JaHmg0fs
- Supersedes: none; complementa la decisión 2 de [ADR-0008](ADR-0008-tenant-isolation-boundaries.md), que permanece Accepted y que dejaba sin definir el límite de reintentos.
- Superseded by: none

## Context

El worker del processor reencola sin límite cualquier excepción que no sea `InvalidJobMessage` o
`ProviderError` (`apps/processor/app/workers/runner.py`). Consume con un solo hilo y la cola
`processor:jobs` la comparten todos los tenants. Un trabajo cuyo fallo no puede resolverse vuelve a
la cabeza de la cola en cada vuelta y retiene a los que van detrás.

Se reprodujo con RabbitMQ 3.13.7 real (`RF-086-004`): un `source` como `Azure Cost Management` se
acepta con 202 porque el backend solo rechaza el vacío, y el processor lo rechaza siempre porque
exige `^[a-z0-9][a-z0-9._-]{0,63}$`. El mensaje se procesó cada ~2 s, el contador de fallos pasó de
0 a 66 y un trabajo válido de otro tenant siguió `queued` durante 60 s. `RF-054-001` es el mismo
bucle con otra causa: un resultado guardado corrupto en la reentrega de un trabajo completado.

ADR-0008 y el contrato de JUP-086 dicen que los fallos transitorios siguen reintentables y que no
se define límite, backoff ni infraestructura de reintentos, y que los permanentes se descartan. El
problema es la clase intermedia: fallos que el worker no sabe clasificar y que pueden ser tanto
transitorios como deterministas.

Restricciones: sin DLQ, sin migración, sin cambiar el tipo ni los argumentos de la cola, sin
configuración nueva; no filtrar el `source`, el contenido ni la causa en registros o excepciones
(JUP-053); `update_job_status` reescribe `result` en cada transición, así que guardar un contador
ahí obligaría a cambiar ese SQL.

## Decision

1. **Evitar la entrada.** `POST /jobs/ingest` rechaza con el 422 saneado vigente un `source` que, tras
   quitar espacios y pasar a minúsculas, no cumple la regla del processor. El valor admitido se guarda
   y publica literal. Una tabla de casos compartida vigila que los dos servicios no diverjan.
2. **Fallo permanente de entrada.** Si el guardrail de entrada rechaza un trabajo ya guardado, este
   queda `failed` y el mensaje se descarta sin reencolar en esa misma entrega.
3. **Tope de un reintento para el fallo no clasificado.** El worker reencola solo si el broker no
   marca la entrega como reentrega (`redelivered` falso). Si es reentrega y vuelve a fallar, el
   trabajo queda `failed` y el mensaje se descarta. El tope es «una reentrega como máximo»: una
   primera entrega interrumpida ya llega como reentrega, y entonces su primer fallo descarta.
4. **Solo se descarta con estado terminal registrado.** Si el worker no puede leer el trabajo o
   registrar su estado (base caída), reencola sin tope, sea o no reentrega. Descartar ahí dejaría el
   trabajo en `queued` o `running` sin mensaje y sin que nadie lo vea.
5. **Resultado guardado.** La reentrega de un trabajo `completed` devuelve el resultado solo si es un
   objeto; si está corrupto o tiene otra forma, el mensaje se rechaza como inválido.

`InvalidJobMessage` y `ProviderError` conservan su tratamiento. El tope es fijo, sin variable de
entorno.

## Consequences

**Más fácil.** Un trabajo mal formado sale de la cola en una entrega y un fallo no clasificado en
dos como máximo, de modo que ya no retiene a otros tenants. Sin esquema, cola ni configuración
nuevos, el cambio se revierte con un commit. Desplegar backend y processor en cualquier orden es
seguro.

**Más difícil o arriesgado.**

- **Coste aceptado:** una caída de pgvector o de los embeddings de más de unos 2 s marca `failed`
  los trabajos en cola, que hoy esperarían, y hay que volver a enviarlos. El fallo queda en la
  base, en los registros y en la alerta de JUP-045; la interfaz no lo muestra porque no existe
  lectura del estado de un trabajo (`RF-104-003`).
- Una reentrega causada por un reinicio del worker deja ese trabajo sin reintento.
- Sin estado legible o registrable, el reencolado sigue sin tope. Es deliberado y es el único caso
  en que el bucle original puede persistir; lo causa el almacén y no el mensaje.
- Un mensaje que mata el proceso antes de que el worker responda al broker se reentrega sin fin y
  queda fuera de esta política.
- La regla del `source` está duplicada en dos servicios; la tabla de casos detecta la deriva solo
  en los casos que contiene.
- Un cliente que enviara un `source` con otro formato pasa de 202 a 422.

## Alternatives Considered

- **Contador de intentos en `result`:** exacto y configurable, pero obliga a cambiar el SQL de
  transiciones y el contenido de `result`, que varias pruebas fijan como `{"error": "ingestion_failed"}`.
- **Columna de intentos en `jobs`:** es una migración; excluida por el alcance de la tarjeta.
- **Cola quorum con `x-delivery-limit`:** ambos servicios declaran la cola como clásica y duradera;
  redeclararla con otros argumentos falla sobre una cola existente y cambia su tipo.
- **DLQ o cola de cuarentena:** excluida por la tarjeta; ADR-0008 y JUP-086 la descartan sin una
  decisión nueva. Sigue siendo posible más adelante y permitiría recuperar los trabajos descartados.
- **Solo clasificar los dos casos conocidos como permanentes:** cierra los findings pero deja el
  reencolado infinito para cualquier otro fallo determinista que aparezca.
- **Tope también cuando no se puede registrar el estado:** una caída de unos segundos de la base
  vaciaría la cola dejando todos los trabajos en `queued` para siempre.
- **Relajar la regla de `source` del processor o normalizar en el backend:** la regla es un
  guardrail porque el valor entra en el prompt del agente, y JUP-086 decidió conservar el valor
  literal.

## Evidence And Follow-up

Medido el 2026-10-11 sobre `develop` en `8511fb1f`, con la evidencia en
[JUP-113-validation.md](../evidence/JUP-113-validation.md):

- La reproducción de `RF-086-004` con Compose aislado y RabbitMQ real (secciones «Reproducción»).
- La marca de reentrega: `redelivered` es falso solo en la primera entrega y verdadero tras
  `nack(requeue=True)` y tras cerrar la conexión sin responder (pika 1.4.4, RabbitMQ 3.13.7). La
  decisión 3 depende de ello; si dejara de cumplirse, hay que revisar este ADR.

Seguimiento: completar esta sección con la evidencia de las pruebas y de la comprobación con
servicios reales (tareas 6 y 7.4 del change); decidir la ratificación del ADR en la revisión de la
PR; valorar más adelante la DLQ y la lectura del estado de un trabajo (`RF-104-003`) si el coste de
la decisión 3 resulta molesto en la práctica.
