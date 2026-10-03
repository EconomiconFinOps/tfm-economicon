JUP: JUP-023
ADR: [ADR-0002](../../../docs/adr/ADR-0002-litellm-openrouter.md)
ADR de version: [ADR-0016](../../../docs/adr/ADR-0016-litellm-version-pin.md) (Proposed)

Estado actualizado 2026-10-02: se conserva el diseno y sus gates historicos.
La aprobacion de la correccion de presupuesto esta registrada en proposal.md;
implementacion, simulacion de contador/rechazo y unico embedding real pasan.
Ver [evidencia actual](../../../docs/evidence/JUP-023-validation.md#embedding-budget-correction).
Las referencias a aprobaciones/ensayos pendientes mas abajo documentan el
momento de cada propuesta, no sustituyen el resultado posterior. Revision tecnica
y QA local posteriores pasan; aprobacion final y reviews humanas siguen
pendientes, sin autorizacion de publicacion.

## Context And Boundary

Base local: `origin/develop` y HEAD `5a54ce2ed9001dfb9d4b9d8e06eae84cffe91124`,
rama `feat/JUP-023-litellm-openrouter`. Reutilizar JUP-078, los guardrails JUP-024,
el pipeline de ingestion y las pruebas existentes. La peticion documental del
2026-10-02 incorpora ADR-0016 y su indice, ademas de proposal/design/tasks, sin
ampliar alcance de producto. No se modifica, acepta ni sustituye ADR-0002;
sus decisiones pendientes bloquean uso real.

## Provider Integration

Mantener `invoke(prompt, response_format=...) -> str` y `embed(text) -> list[float]`.
Las factorias reciben los settings existentes sin romper llamadas mock. Un
cliente pequeno compartido en `app/clients/litellm.py` reutiliza el patron
`urllib.request` del benchmark: POST JSON, Bearer virtual y rechazo de todas las
redirecciones, sin importar ni ejecutar el runner de benchmark.
Normalizar URL con o sin `/v1` sin duplicarlo; usar `/v1/chat/completions` y
`/v1/embeddings`, siempre contra el gateway configurado.

Chat envia alias, prompt y `response_format` estricto recibido, sin cambiar el
prompt ni FinOpsResponse 1.0. Extrae contenido textual no vacio y lo entrega a
los guardrails existentes. `parse_and_validate_response` se ejecuta fuera de
`provider.invoke`: en `agents/service.py`, convertir solo su `AgentResponseError`
en `ProviderError` de respuesta invalida cuando la ruta seleccionada es LiteLLM.
No reclasificar errores de preflight, mocks u otros fallos del runtime. No
relajar schema, reparar respuestas ni reintentar ante rechazo de guardrails.

Embeddings envia texto y alias, solicita 1536 dimensiones y exige un vector
numerico de longitud exacta, finito, sin booleanos ni coercion de strings; una
respuesta malformada falla antes de persistir. Conservar `provider.name` para
la trazabilidad del almacen existente.

### Approved Compatible Endpoint Trial

Plan historico de la seleccion DeepInfra. El [smoke posterior](../../../docs/evidence/JUP-023-validation.md#successful-real-smoke-and-accounting)
paso con schema original, vector finito de 1536, pgvector y job completed en
SQLite; total oficial 0,002591308 USD. Las referencias siguientes a pendientes
describen ese plan previo. "Secundario y embeddings no cambian" se limita a
aquella seleccion; la correccion contable F1 se aprobo posteriormente en proposal.md.

La aprobacion de Paris en proposal.md limita la prueba a `economicon-chat`:
mantener `model: openrouter/z-ai/glm-5.2` y agregar en
`litellm_params.extra_body.provider` solo `only: [deepinfra/fp4]` y
`require_parameters: true`. Conservar `zdr: true`, `data_collection: deny`,
`allow_fallbacks: false`, `reasoning.enabled: false`, schema estricto completo,
30 s y 800 tokens; secundario y embeddings no cambian. Si la ruta no satisface
parametros/privacidad o rechaza el schema, fallar sin seleccionar otro endpoint,
modelo ni relajar restricciones. La compatibilidad aun no esta acreditada.

Reutilizar `tools/llm-gateway-config.test.mjs`, el test Docker opt-in y su fixture
para comprobar configuracion y parametros transmitidos, incluyendo schema
completo intacto y aliases ajenos sin cambios. La implementacion prevista se
limita a config/README existentes y esas pruebas; no SDK, dependencias nuevas
ni API directa. No se requiere nuevo ADR: es una prueba de compatibilidad de
endpoint dentro de OpenRouter/JUP-023, conservando las decisiones de JUP-078 y
el contrato de JUP-024; no redefine arquitectura ni acepta ADR-0002.

Tras validar documentos, continuar con tester bajo la aprobacion registrada.
Gate contable pendiente antes de pago: cuatro fallos chat HTTP 400, observado
0 USD, reservas retenidas 0,40 USD y cap upstream 0,40 USD sin reinicio.
Conciliar con registros autoritativos y verificar margen antes de otra llamada;
el cero observado no libera reservas. No elevar caps ni reiniciarlos; mantener
el techo agregado 0,50 EUR. Una prueba simulada no acredita compatibilidad real.

## Limits And Errors

Para cualquier proveedor real, `core/config.py` rechazara explicitamente
timeout > 30 s, retries > 2 o max output tokens > 800. Se admiten valores
inferiores validos, incluido cero reintentos; no hay clamp silencioso. Mantener
defaults 30/2/800, validaciones existentes de secretos/alias/dimension y ajustes
Azure intactos. El timeout limita cada intento; dos reintentos significan como
maximo tres intentos por operacion, no 30 s de plazo total del job.

Solo timeout/transporte transitorio, HTTP 429 y 5xx pueden reintentarse dentro
de ese limite, con espera acotada. Auth, request 4xx distintos de 429,
redirecciones y respuestas invalidas fallan sin retry. No convertir cualquier
excepcion en transitoria. Gateway y router tendran retries efectivos cero
(el ejemplo JUP-078 aun declara dos); comprobarlo con upstream falso para evitar
multiplicar consumo. Nunca fallback a mock, otro alias o proveedor.

`ProviderError` contiene categoria y metadatos seguros, nunca cuerpos HTTP o
secretos. `IngestTask` marca `failed` con razon existente `ingestion_failed` y
preserva este tipo antes de su wrapper generico. El worker captura ese tipo y
ejecuta `nack(requeue=False)`, incluso al agotar errores transitorios. Mantener
`InvalidJobMessage`, ack de exito y tratamiento/requeue de otros errores.
Logs por allowlist: estado/categoria, alias, duracion, correlation ID y uso/coste
disponible y validado; no prompts, respuestas, claves, cabeceras o excepciones
upstream sin sanear. Ausencia de coste nunca equivale a coste cero.

### SpendLogs Privacy Correction

La [validacion simulada](../../../docs/evidence/JUP-023-validation.md) detecto
texto upstream en `LiteLLM_SpendLogs.metadata.error_information.error_message`.
La enmienda aprobada por Paris en proposal.md conserva imagen/digest 1.103.2 y
planea `infra/litellm/safe_logging.py`, montado solo lectura y registrado como
callback publico soportado mediante config/Compose. No se presupone que el
hook disponible ejecute antes de la persistencia: comprobar su contrato y orden
en esa imagen, incluida la ruta asincrona de fallos, antes de darlo por valido.

Sanear texto arbitrario de errores upstream antes de construir/persistir
SpendLogs, sin guardar una copia cruda en campos anidados. Conservar filas de
exito y fallo, estado, modelo, request ID, tiempo, duracion y tokens/coste
disponibles y validados; datos ausentes siguen desconocidos, no cero. No activar
`disable_error_logs` ni eliminar filas, cargos recuperados o contabilidad de
fallos para pasar privacidad. No usar SDK, dependencias productivas nuevas,
parches del proveedor ni monkeypatch.

Verificar inicializacion fail-closed: modulo ausente, import/registro fallido
impiden servir trafico de modelos. Verificar el orden previo a persistencia y
ausencia de fugas en las rutas normales de error del proveedor. Si el hook falla
en pruebas, la validacion falla y el uso real sigue bloqueado; documentar el
comportamiento observado. No se exige circuit breaker, autorrecuperacion ni
callback infalible en runtime. Si un callback publico no
permite ese orden con preservacion de registros, detenerse y devolver evidencia
de ruta/hook/orden y reproduccion simulada; no sustituirlo por mecanismos privados.

Reutilizar `apps/processor/tests/test_litellm_docker.py` y su fixture opt-in,
mas pruebas focalizadas minimas de saneamiento, preservacion e inicializacion.
En Docker sin llamadas reales, inyectar errores con sentinels sinteticos y
tokens/coste conocidos cuando la ruta los entregue; comprobar filas de fallo,
metadatos y contabilidad conservados, ausencia de sentinels en DB y consola, y
orden del hook. Repetir las regresiones afectadas de claves/retries y exito.
Estado historico al redactar el plan: controles pendientes. Estado actual:
1.2/3.2 completadas con los limites de la evidencia y [smoke real satisfactorio](../../../docs/evidence/JUP-023-validation.md#successful-real-smoke-and-accounting).
Esto corrige F2; en aquel momento F1 sobre coste y contador virtual bloqueaba
QA, sin atribuir al smoke cobertura contable que no demostro.

### Pending Embedding Budget Correction

Propuesta historica F1, posteriormente aprobada e implementada; ver estado y
evidencia al inicio. Solo el despliegue
`economicon-embedding` recibiria este bloque, hermano de `litellm_params`:

```yaml
model_info:
  input_cost_per_token: 0.00000002
  output_cost_per_token: 0.0
```

Referencia de precio 2026-10-02: USD/token. Mantener los flags actuales y agregar
`litellm_params.extra_body.provider.max_price.prompt: 0.02` (USD/millon).
[Custom pricing](https://docs.litellm.ai/docs/proxy/custom_pricing) documenta
model_info; [cost tracking](https://docs.litellm.ai/docs/proxy/cost_tracking)
describe el gasto calculado y [OpenRouter max_price](https://openrouter.ai/docs/guides/routing/provider-selection#max-price)
sus unidades. Sintaxis y transmision efectiva en embeddings deben verificarse
primero en la fixture simulada; aplicacion real del filtro no demostrada.
Registrar fecha/fuente de tarifa y revalidarla antes de uso real; precio cambiado
o no verificable, cap o margen desconocidos obligan a parar, no a elevar limites.
El calculo por tokens es atribucion derivada, nunca factura individual. Un cero
o valor ausente con uso positivo no acredita gratuidad ni libera reservas.

Diagnostico offline del 2026-10-02 en LiteLLM 1.103.2, imagen exacta
`ghcr.io/berriai/litellm@sha256:f63fb81b831b170ec16851e23c36ac5bf52ef106b271406429524a2ed730bbfd`:
el mapa incluido tiene `text-embedding-3-small`, pero carece de
`openrouter/openai/text-embedding-3-small` y `openai/text-embedding-3-small`.
La reproduccion con 12 tokens sin coste devuelto calcula 0.0 sin tarifa y
0.000000240 USD con model_info. No demuestra por si sola persistencia o bloqueo.
Fuente dentro de `/app/.venv/lib/python3.13/site-packages/litellm/`:
`router.py:9837` registra precios por deployment;
`litellm_core_utils/litellm_logging.py:5315` detecta model_info automaticamente;
`cost_calculator.py:812` selecciona precio por router_model_id;
`proxy/spend_tracking/spend_tracking_utils.py:787` usa response_cost en SpendLogs;
`proxy/proxy_server.py:2904` omite incremento con cero/None y desde 2921 prepara
el incremento de clave. Ruta reproducida compatible con F1, sin afirmar haber
recuperado el mapa efectivo del anterior contenedor real ya eliminado.

Comprobacion retenida en el transcript del diagnostico; no se creo receipt
permanente. Este comando reproduce el calculo en memoria, sin red, claves o
volumenes; no arranca gateway ni acredita el contador DB:

```powershell
$pricingProbe = @'
import os
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
from litellm import Router, EmbeddingResponse
from litellm.cost_calculator import response_cost_calculator
from litellm.litellm_core_utils.litellm_logging import use_custom_pricing_for_model
response = EmbeddingResponse(model="openai/text-embedding-3-small", data=[], usage={"prompt_tokens":12,"total_tokens":12})
for priced in (False, True):
    deployment = {"model_name":"economicon-embedding","litellm_params":{"model":"openrouter/openai/text-embedding-3-small"}}
    if priced:
        deployment["model_info"] = {"input_cost_per_token":2e-8,"output_cost_per_token":0.0}
    router = Router(model_list=[deployment])
    info = router.model_list[0]["model_info"]
    custom = use_custom_pricing_for_model({"metadata":{"model_info":info}})
    cost = response_cost_calculator(response_object=response, model="openai/text-embedding-3-small", custom_llm_provider="openrouter", call_type="aembedding", custom_pricing=custom, router_model_id=info["id"], optional_params={})
    print(priced, custom, cost)
'@
docker run --rm --pull never --network none --read-only --entrypoint python ghcr.io/berriai/litellm@sha256:f63fb81b831b170ec16851e23c36ac5bf52ef106b271406429524a2ed730bbfd -B -c $pricingProbe
```

Alcance propuesto tras aprobacion: `infra/litellm/config.example.yaml` y README;
reutilizar `tools/llm-gateway-config.test.mjs`, `apps/processor/tests/test_litellm_docker.py`
y `apps/processor/tests/fixtures/litellm_fake_upstream.py`, evitando nuevos casos
o archivos permanentes si basta ampliar los existentes. Sin cambios a
safe_logging, SDK, dependencias, imagen, modelos/schema/dimensiones/privacidad
ni servicio contable; no requiere nuevo ADR al no cambiar arquitectura.

Docker debe devolver usage sin coste: comprobar SpendLogs positivo y contador
virtual antes/despues, esperando propagacion asincrona con plazo acotado.
Agotar cap mediante llamadas simuladas y comprobar rechazo sin acceso upstream;
precargar gasto no prueba esta ruta. Tras aprobar y superar esas pruebas,
realizar exactamente un embedding real acotado sin retries, registrando coste
derivado, avance del contador virtual y delta oficial conciliado. Mantener
0,50 EUR agregados y cap upstream 0,40 USD sin reinicio, incluyendo uso previo
0,002591308 USD. No repetir chat ni suites no afectadas. F1 no se cierra hasta
esa evidencia y revision/QA afectadas; no hay autorizacion de publicacion.

## Isolated Runtime

Compose adicional en `infra/litellm/`, activado expresamente; defaults mock y
Compose raiz sin cambios. Gateway en red Docker propia accesible al processor
del smoke; administracion publicada solo en loopback y healthcheck sin llamada
LLM. PostgreSQL exclusivo del gateway conserva claves virtuales, no es vectorDB
ni la base de jobs. Sin reutilizar contenedores, redes o volumenes del servidor
compartido. No exponer PostgreSQL publicamente.

Secretos solo en entorno o archivo ignorado: OpenRouter solo gateway, master key
solo administracion, virtual key revocable y limitada solo processor. Reutilizar
el mapa de JUP-078: `economicon-chat` -> `z-ai/glm-5.2`,
`economicon-chat-deepseek` -> `deepseek/deepseek-v4-pro` (seleccion explicita de
evaluacion, nunca fallback), `economicon-embedding` ->
`openai/text-embedding-3-small` de 1536 dimensiones. Mantener razonamiento
opcional desactivado, ZDR, `data_collection: deny`, `allow_fallbacks: false` y
fallo cerrado si no existe ruta compatible.

El smoke usa pgvector separado y desechable con fixture de schema de 1536
dimensiones. Preparar esa fixture solo sobre la base aislada antes del recorrido
del processor, teniendo en cuenta que el bootstrap actual crea vectores de 8.
No cambiar migraciones, historial ni schema de 8 dimensiones existente; no
reinterpretar datos de 8 como 1536. Si exige tocar esos limites, escalar.

## Security Precondition

Comprobacion documental contra fuentes oficiales del 2026-10-02; los resultados
aportados por el orquestador se detallan en ADR-0016 y no son auditoria exhaustiva:

- [GHSA-4xpc-pv4p-pm3w](https://github.com/BerriAI/litellm/security/advisories/GHSA-4xpc-pv4p-pm3w),
  publicado 2026-05-28, CVE-2026-49468: bypass por Host Header, afecta < 1.84.0.
  La baseline historica JUP-078 1.82.6, digest
  `sha256:7c311546c25e7bb6e8cafede9fcd3d0d622ac636b5c9418befaa32e85dfb0186`,
  NO se ejecutara ni siquiera para fake upstream.
- [GHSA-r75f-5x8p-qvmc](https://github.com/BerriAI/litellm/security/advisories/GHSA-r75f-5x8p-qvmc):
  SQL injection en verificacion de API keys, >= 1.81.16 y < 1.83.7;
  afecta la baseline y es relevante para PostgreSQL y claves virtuales.
- [GHSA-7hp6-4w63-5g45](https://github.com/BerriAI/litellm/security/advisories/GHSA-7hp6-4w63-5g45),
  critico del 2026-09-30: afecta >= 1.91 y < 1.100.4, y ramas 1.101 < 1.101.3,
  1.102 < 1.102.2 y 1.103 < 1.103.1. No basta seleccionar el minimo 1.84.0.
- El [incidente de marzo](https://docs.litellm.ai/blog/security-update-march-2026)
  refiere PyPI 1.82.7/1.82.8, no la imagen oficial 1.82.6; es distinto del
  riesgo Host Header.

Paris autoriza el 2026-10-02 LiteLLM 1.103.2 y Docker local aislado con upstream
simulado, sin gasto, con este pin:
`ghcr.io/berriai/litellm:v1.103.2@sha256:f63fb81b831b170ec16851e23c36ac5bf52ef106b271406429524a2ed730bbfd`.
Ninguno de los 17 advisories consultados por el orquestador incluye 1.103.2
segun sus rangos; esto no acredita ausencia de vulnerabilidades. Registro/pull
coinciden con el digest e imports sin red identifican LiteLLM 1.103.2 y Prisma
0.11.0. No se verificaron firmas: cosign no estaba disponible.
Compatibilidad de config, auth, claves virtuales, privacidad, retries y API
sigue pendiente en Docker; imports no la demuestran. No usar `latest`.
ADR-0016 permanece `Proposed`; esta decision no acepta ADR-0002 ni autoriza
dependencias compartidas. Rollback solo a imagen corregida aprobada o mocks
development, nunca a una vulnerable. La tarea 1.2 sigue abierta.

Las paginas oficiales de [GLM-5.2](https://openrouter.ai/z-ai/glm-5.2),
[DeepSeek V4 Pro](https://openrouter.ai/deepseek/deepseek-v4-pro) y
[embeddings](https://openrouter.ai/openai/text-embedding-3-small) existen segun
el preflight; no acreditan disponibilidad con la clave, ZDR, structured output
ni consumo. Compatibilidad y disponibilidad efectivas quedan pendientes.

## Validation And Spend

1. Tras gate pre-code, pruebas offline focalizadas de transporte, settings,
   guardrails, vectores y propagacion de errores; CI sin claves externas.
2. Con version/digest autorizados segun ADR-0016, gateway Docker contra upstream falso,
   comprobando configuracion efectiva, privacidad, claves y numero de intentos.
   Esta fase NO es evidencia OpenRouter ni sustituye el smoke real.
3. Tras resolver ADR/privacidad, claves y limites, smoke real secuencial: chat
   principal validado como FinOpsResponse 1.0, embeddings finitos de 1536 y
   recorrido processor con texto sintetico, persistencia pgvector desechable y
   finalizacion del job. Secundario solo seleccionado explicitamente para
   evaluacion, documentando resultado/limite; no se promociona ni oculta un fallo.

Techo agregado de 0,50 EUR para toda la validacion real, incluidos retries y
fallos cobrados. Ni saldo de 10 EUR ni presupuesto mensual del ADR son esta
autorizacion. Antes de gastar verificar limites upstream y virtual, precios
actuales, conversion USD/EUR conservadora y margen para cargos/retardos. Reservar
el peor coste de los intentos antes de cada operacion, ejecutar secuencialmente
y conciliar deltas upstream, incluidos fallos; parar si el coste o margen no se
puede acotar. No gastar con limites solo declarados o precios desconocidos.

Evidencia futura: SHA probado, digest/config saneada, limites efectivos,
comandos/resultados y coste acumulado, sin contenidos ni secretos. Mutation
focalizada sobre limites, retries, rechazo de vectores/salidas y no-requeue;
reutilizar suites y regresiones afectadas, sin cuota artificial de casos.
Validar OpenSpec, trazabilidad e higiene. Por condicion expresa de Paris del
2026-10-02, smoke real pendiente o fallido impide dar nuestra parte por terminada
y abrir cualquier PR, incluido borrador. Registrar evidencia satisfactoria antes
de solicitar autorizacion de publicacion; no sustituye las reviews humanas.

## Expected Files And Handoff

Pre-code debe incluir estos archivos previstos (no editados en esta fase):

- `apps/processor/app/{agents/providers.py,agents/service.py,embeddings/providers.py,clients/litellm.py,core/config.py,tasks/ingest.py,workers/runner.py}`.
- Tests focalizados en `apps/processor/tests/` reutilizando settings, runtime,
  ingestion, worker, embeddings, secretos y tracing; fixtures/smoke aislados.
- `infra/litellm/{safe_logging.py,config.example.yaml,docker-compose.yml,README.md}` y pruebas de
  configuracion existentes en `tools/llm-gateway-config.test.mjs`; instrucciones
  processor solo si necesarias. Sin manifests, lockfiles ni CI.

La enmienda callback solo escribe proposal/design/tasks, el delta de spec para
preservacion y seguimiento en ADR-0016. Los archivos de implementacion anteriores
son previstos, no editados aqui. Reutilizar el test Docker opt-in y su fixture,
`tools/llm-gateway-config.test.mjs` y pruebas focalizadas minimas; no modificar
ADR-0002 ni evidencias en esta fase documental.

Riesgos: imagen vulnerable, API/privacidad incompatibles, retries multiplicados,
coste no conciliable y mezcla de dimensiones. Compatibilidad pendiente,
ADR-0002 o limites sin resolver bloquean su fase; escalar decisiones nuevas
sin ampliar alcance para sortearlos. El gate de imagen ya esta autorizado.

Proceso adoptado localmente `2026-09-30 (JUP-100)`; PR #56 sigue abierta segun
contexto recibido. Paris/Victor/Alejandro/Lucia son roles del export pendientes
de confirmar y publicar, no evidencia de participacion. Publicacion requiere
autorizacion futura. Hacia develop: reviews separadas `Revision JUP-023` y
`Validacion JUP-023`, primera favorable COMMENT y segunda APPROVE cuando ambas
sean satisfactorias; bloqueos REQUEST_CHANGES. Autor/pairing no sustituyen esos
roles. QA tecnica y aprobacion humana final son gates distintos. Merge, archivo
y actualizacion Trello requieren autorizaciones separadas; aclarar el orden de
archivo antes de actuar. La aprobacion pre-code y su condicion de publicacion
se registran en `proposal.md`; no se infieren otras aprobaciones.

## PR 65 Attempt Deadline Correction

Correccion del contrato Limits And Errors, sobre HEAD `9fe836eb8ec1c3805cda9c340a7c6e9bbf247376`.
El timeout de socket actual en `apps/processor/app/clients/litellm.py` no
demuestra un plazo por intento: bytes periodicos pueden mantener bloqueados
`open()` al leer cabeceras o `response.read()` mas alla del limite.

Fijar un unico deadline con reloj monotono al iniciar cada intento de transporte
HTTP. Conexion de socket, cabeceras y cuerpo consumen el mismo presupuesto, maximo 30 s;
recibir bytes o cambiar de fase no reinicia el plazo. Al vencer, interrumpir
la operacion bloqueada y cerrar/liberar su transporte, incluso sin response
disponible aun. Una comprobacion solo despues de read, o devolver dejando
la lectura activa en segundo plano, no satisface el contrato. Clasificar
el vencimiento como timeout aunque el cierre provoque otro error de transporte;
al agotar retries lanzar ProviderError('timeout') saneado, sin datos upstream.
Cada retry permitido tiene un nuevo deadline; conservar backoff acotado y
maximo `llm_max_retries + 1` intentos, sin solapar transportes vencidos.
El plazo sigue siendo por intento, no por job. Mantener redirects rechazados,
sin fallback, contratos chat/embedding y `nack(requeue=False)` existentes.

La resolucion DNS del sistema no es cancelable por este arreglo: no se garantiza
el plazo total incluyendo DNS ni se registra aceptacion humana de esa limitacion.
Sin subprocesos DNS, resolver nuevo, refactor ni cambios en pika.
Implementacion prevista solo en el cliente compartido, con stdlib y sin SDK
ni dependencias nuevas. Conservar los cinco casos actuales de
`apps/processor/tests/test_agent_runtime.py`. La regresion usa HTTP
real sobre loopback con datos sinteticos, sin el transporte mock que impide
sockets: goteo de cuerpo y cabeceras, timeout 0,05 s e intervalos 0,03 s.
Medir con reloj monotono hasta retorno/error, excluyendo teardown del servidor;
comprobar categoria timeout, cierre efectivo y solicitudes recibidas con cero
y dos retries. Declarar tolerancia pequena de planificacion, que rechace los
0,42/4,4 s reportados; el limite total incluye deadlines, backoff y esa tolerancia.
Un control positivo entrega JSON valido dentro del plazo y termina sin retry.
Reutilizar casos existentes de redirects, saneamiento, embeddings y no-requeue;
sin nuevos casos, suite ni repeticion del smoke real.

No requiere nuevo ADR: se hace efectivo el limite ya especificado. Si cumplirlo
exige cambiar arquitectura, dependencias, seguridad o alcance, detenerse y
escalar con la limitacion y decision necesaria; no inventar una alternativa.
CONTRIBUTING vigente: Process version `2026-09-30 (JUP-100)`. Roles recibidos:
Paris liderazgo, Victor pairing, Alejandro revision y Lucia validacion.
Tras pruebas y QA locales, siguen pendientes la revision y validacion humanas
afectadas: cada solicitante debe levantar su Request changes con Approve;
un Comment o un veredicto interno no lo resuelve. Conservar aprobacion final
y autorizaciones externas como gates separados. Sin gasto ni publicacion.
