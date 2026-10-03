# ADR-0017: El backend embebe la pregunta con su propia clave virtual y un contrato de recuperacion explicito

- Status: Proposed
- Date: 2026-10-02
- Related JUP/OpenSpec: JUP-022, [jup-022-semantic-retrieval](../../openspec/changes/archive/2026-10-03-jup-022-semantic-retrieval/design.md)
- Trello: https://trello.com/c/DPZpQ09b
- Supersedes: none
- Superseded by: none

## Context

El processor ya indexa los documentos con un modelo real a traves del gateway LiteLLM ([ADR-0002](ADR-0002-litellm-openrouter.md)), con el alias `economicon-embedding` y vectores de 1536 dimensiones. El backend, en cambio, embebe la pregunta del chat con un proveedor simulado (un hash SHA-256 por posicion) y recupera siempre los 4 fragmentos del tenant con menor distancia coseno, sin umbral y sin desempate. Mientras la pregunta y los documentos no usen el mismo modelo, la recuperacion no tiene sentido semantico.

Hay que decidir quien embebe la pregunta, con que credencial y que contrato tiene la recuperacion. Afecta a un limite entre servicios, a un secreto nuevo ([ADR-0006](ADR-0006-runtime-secret-boundaries.md)) y a la forma en que se calibra el sistema, por eso se registra como decision duradera.

## Decision

- El backend llama al gateway con una **clave virtual propia**, distinta de la del processor y restringida al alias `economicon-embedding`. En Compose se lee de `BACKEND_LITELLM_API_KEY`; dentro del backend es `LITELLM_API_KEY`, un `SecretStr` sin valor por defecto, obligatorio solo con el proveedor `litellm`.
- El proveedor `mock` solo es valido con `RUNTIME_ENVIRONMENT=development|test`; con `litellm` la dimension debe ser 1536, la del modelo de la ingesta.
- La recuperacion tiene parametros explicitos: `top_k` (1 a 20, por defecto 4) y distancia coseno maxima opcional (mayor que 0 y como maximo 2; sin valor no se filtra). El orden es distancia ascendente y, a igualdad, identificador del fragmento. Si ningun fragmento cumple, el resultado es una lista vacia y el asistente responde con el estado sin contexto existente. El filtro de tenant se aplica en la misma consulta que el ranking.
- Los valores por defecto de `top_k` y de la distancia maxima los fija una calibracion reproducible con el banco de preguntas JUP-069 y etiquetas por seccion, no una estimacion. Con el modelo real: `top_k` 4 (3 a 6 dan el mismo acierto) y distancia maxima 0.6 con `litellm`; con `mock` no hay umbral. `none` u `off` lo desactivan.
- La duplicacion del cliente HTTP en backend y processor se acepta, protegida por una prueba de paridad de alias, dimension y categorias de error.

## Consequences

- Se puede atribuir y revocar el gasto de embeddings por servicio, y una fuga de la clave del backend no da acceso a otros alias.
- El backend pasa a depender de un servicio externo en cada pregunta: se anade latencia y un modo de fallo (el chat devuelve un 503 con mensaje fijo y el tiempo maximo esta acotado).
- Hay un secreto mas que emitir y rotar por entorno.
- Una base creada con `vector(8)` no sirve con el modelo real: hay que reindexar en una coleccion nueva, nunca en caliente.
- Un cambio de modelo con la misma dimension no se detecta, porque el esquema guarda `provider` y `dimension` pero no el alias; registrarlo exige un cambio de esquema del processor ([ADR-0011](ADR-0011-single-owner-per-table.md)). Queda como finding RF-022-001.
- El umbral calibrado con un corpus pequeño puede sobreajustarse: es configurable y se recalibra al crecer el corpus.

## Alternatives Considered

- Un endpoint interno en el processor que embeba la pregunta: anade un salto y cambia el principio de que el processor solo expone salud operativa.
- Reutilizar la clave del processor en el backend: no permite atribuir ni revocar gasto por servicio.
- Un paquete Python compartido para el cliente: el monorepo no tiene infraestructura para ello; puede reconsiderarse si aparece un tercer consumidor.
- Fijar un umbral por intuicion: se descarta porque el banco y las etiquetas permiten medirlo.

## Evidence And Follow-up

- Calibracion: script `tools/retrieval-calibration.py`, etiquetas en `docs/validation/JUP-022-retrieval-labels.json` e informe con el modelo real en [`docs/spikes/JUP-022-retrieval-calibration.md`](../spikes/JUP-022-retrieval-calibration.md) (80 llamadas al alias `economicon-embedding`, 28 preguntas, 52 fragmentos). Con 0.6 el acierto por seccion de los casos `answer` pasa de 75 % a 70 % y solo el 5 % queda vacio; los casos `clarify` y `abstain` siguen recuperando fragmentos, asi que negarse o aclarar corresponde a las guardas de respuesta. Barrido de troceado en el [anexo](../spikes/JUP-022-retrieval-calibration-chunking.md) y finding RF-022-002.
- Pruebas del contrato de recuperacion sobre pgvector real (opt-in con `JUP086_VECTOR_TEST_URL`) y mutantes registrados en la revision del change.
- Pendiente: decidir si la clave del backend tiene un tope de gasto propio y quien la emite en cada entorno; pasar el estado a Accepted cuando el cambio se integre.
