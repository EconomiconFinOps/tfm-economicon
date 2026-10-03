JUP: JUP-023
Trello: https://trello.com/c/O8elKkm9

## Why

El processor valida la configuracion LiteLLM pero sus factorias solo crean mocks.
JUP-023 conectara chat y embeddings reales conservando contratos y guardrails.
Fuente: tarjeta del export de Trello `CawMVPoy - economicon (7).json` y alcance
acotado por el usuario el 2026-10-02; el export no acredita estado remoto actual.

## What Changes

- Adaptadores HTTP stdlib para chat y embeddings, sin SDK ni nuevas dependencias
  Python; reutilizacion de settings, factorias y patron seguro del benchmark.
- Limites reales de 30 s, dos reintentos y 800 tokens; errores tipados y saneados
  que terminan el job sin reencolar indefinidamente.
- Compose adicional opt-in con gateway aislado y PostgreSQL propio para claves
  virtuales; smoke con pgvector desechable de 1536 dimensiones.
- Corregir la privacidad de SpendLogs mediante callback publico soportado en
  la misma imagen 1.103.2: sanear errores antes de persistir, conservando filas
  de fallo y metadatos/costes disponibles; primero Docker simulado sin gasto.
- Pruebas focalizadas offline, despues Docker con upstream falso y finalmente
  smoke OpenRouter obligatorio antes de cualquier PR o cierre, con techo total
  de 0,50 EUR.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `llm-provider-routing`: ampliar la capability del cambio activo JUP-078 con
  ejecucion del processor, errores y validacion de integracion. Este delta solo
  agrega requisitos propios; no duplica ni sustituye los de JUP-078, aun sin
  consolidar en `openspec/specs`. Coordinar su integracion antes del archivo.

## Out of Scope

JUP-022 semantic retrieval, JUP-036 cost tools, JUP-035 web chat, SageMaker,
migraciones, DockerServer compartido, API publica, cambios a FinOpsResponse 1.0,
benchmark y entradas privadas. La peticion documental del 2026-10-02 autoriza
solo proposal/design/tasks, `docs/adr/ADR-0016-litellm-version-pin.md` y su indice;
no amplia alcance de producto. No modifica codigo, tests, dependencias,
ADR-0002, CI, evidencias ni GitHub o Trello; no hace commits, push, merge ni archivo.

## Impact And Gates

Los archivos previstos, riesgos y fases se delimitan en `design.md`. ADR-0002
permanece `Proposed`, con sus aprobaciones existentes intactas. La preparacion
del plan no sustituye la aprobacion humana pre-code posterior a validacion.
La decision operativa de Paris del 2026-10-02 autoriza LiteLLM 1.103.2 con el
digest de [ADR-0016](../../../docs/adr/ADR-0016-litellm-version-pin.md) y Docker
local aislado con upstream simulado sin gasto. El ADR sigue `Proposed` durante
review; no acepta ni sustituye ADR-0002. Compatibilidad Docker y los gates de
privacidad/claves/coste para uso real siguen pendientes; 1.82.6 no se ejecutara.
Las pruebas offline no dan por resueltos esos gates independientes.

Proceso: CONTRIBUTING vigente mas adopcion local `2026-09-30 (JUP-100)` de PR #56
abierta, no politica fusionada ni protecciones remotas verificadas. Roles del
export: Paris liderazgo, Victor pairing, Alejandro revision y Lucia validacion;
pendientes de confirmar/publicar y de acreditar participacion real.

La aprobacion historica siguiente se conserva literalmente; la decision de
imagen posterior tiene el alcance limitado documentado en ADR-0016.

## Human Pre-Code Approval

Decision: APROBADO por Paris el 2026-10-02 para el alcance offline y con las
condiciones siguientes. Este registro no aprueba enmiendas posteriores pendientes.

El 2026-10-02 Paris aprueba continuar con pruebas y adaptadores offline, sin
credenciales ni gasto, con esta condicion expresa: no dar por finalizada nuestra
parte ni abrir PR (tampoco en borrador) hasta superar las pruebas reales y
registrar sus evidencias. Esto exige chat principal validado por FinOpsResponse,
embeddings de 1536 dimensiones y recorrido del processor con persistencia real
en pgvector desechable. Simulaciones y CI verde no sustituyen esos resultados.
Siguen pendientes los gates de imagen, ADR, privacidad y limites de gasto; esta
aprobacion no autoriza publicar. La revision y validacion humanas de la PR
siguen siendo necesarias despues de las pruebas de implementacion.

## Human Callback Amendment Approval

El 2026-10-02 Paris responde "perfecto adelante" a la propuesta de conservar
registros de fallo y estado, modelo, request ID, tiempo, duracion, tokens y coste
disponibles, saneando texto arbitrario upstream ANTES de SpendLogs mediante un
callback soportado de LiteLLM. Autoriza primero la prueba Docker simulada, sin
llamadas reales. Corrige el criterio de privacidad ya aprobado; no es una
funcionalidad adicional. No autoriza `disable_error_logs`, perdida de registros
de coste, monkeypatch, parche del proveedor, SDK ni dependencias nuevas.

Esta enmienda documental comprende proposal/design/tasks, el delta de spec para
expresar preservacion y ADR-0016; no modifica producto, tests, indice ni evidencia.
La implementacion prevista y sus pruebas se delimitan en design.md. La
viabilidad del callback, su orden previo a persistencia y la inicializacion
fail-closed siguen por demostrar. Si la API publica no permite cumplirlos,
detenerse y presentar prueba del bloqueo, sin improvisar otro mecanismo.
La aprobacion no acepta ADR-0002 ni constituye review o validacion humana;
no autoriza commits, PR, tracker ni amplia ningun otro alcance.

Proceso vigente: CONTRIBUTING local sin `Process version`, mas adopcion local
`2026-09-30 (JUP-100)`. Roles comunicados para esta enmienda: Paris liderazgo,
Victor pairing, Alejandro revision y Lucia validacion; participacion y reviews
humanas siguen pendientes de acreditar.

## Real-Use Agreement Confirmation

El 2026-10-02 Paris confirma "si esta acordado" al preguntarle por el acuerdo
conjunto del equipo sobre presupuesto, privacidad y modelos de ADR-0002.
Se registra como confirmacion comunicada por Paris, no como reviews
individuales inventadas ni cambio automatico del estado de ese ADR.
Se mantiene el techo agregado de 0,50 EUR, incluidos reintentos y fallos
cobrados, y la exigencia de limites verificables antes de consumir.
El preflight solo ha consultado catalogos y metadatos de la clave: uso cero,
limite actual 10 USD/mes. Se ha solicitado ajustarlo a 0,40 USD total sin
reinicio automatico para esta prueba; no iniciar llamadas de modelos mientras
no se verifique el ajuste y la clave virtual limitada. No se autoriza publicar.

## Additional Diagnostic Call Approval

El 2026-10-02, tras verificar el limite upstream de 0,40 USD sin reinicio y
observar HTTP 400 en el primer smoke, Paris responde "si" a una llamada
adicional de diagnostico dentro del mismo presupuesto, capturando unicamente
datos del error sin secretos ni contenido privado. Autoriza un solo intento
adicional de chat, sin retries ni embeddings, manteniendo modelos, schema,
privacidad y limites. Antes de consumir, comprobar offline el clasificador
temporal y preservar solo metadatos permitidos antes de limpiar los recursos.
No ampliar diagnosticos de producto ni desactivar el saneamiento. La reserva
anterior no se considera libre por ausencia de coste en una respuesta fallida.
No se autoriza PR, merge, archivado ni cierre.

## Repair Continuation

Paris solicita corregir el fallo de integracion tras el diagnostico anterior.
Se conserva el alcance y presupuesto original, sin cambiar modelos, contrato
FinOpsResponse ni privacidad. El wire completo se comprobo sin gasto; otra
captura estructurada acotada no identifico la causa. Se ha pedido autorizacion
especifica para leer temporalmente el mensaje tecnico del error tras eliminar
secretos, credenciales y contenido de la peticion, sin cambiar los logs del
producto. El 2026-10-02 Paris responde "autorizado" a esa consulta: se permite
utilizar el lector temporal del mensaje tecnico saneado para identificar la
causa real, manteniendo el techo agregado de 0,50 EUR. Antes de otra llamada,
comprobar limites y reservas acumuladas; no liberar reservas por un coste
ausente. Esta autorizacion no cambia modelos, contrato ni logs del producto.
No hay permiso de publicacion, integracion o cierre.

## Contract-Preserving Investigation

Tras preguntar si la decision del schema pertenece a JUP-023, Paris autoriza
buscar primero una solucion compatible con el contrato ("ok adelante entonces").
No aprueba simplificar restricciones ni trasladarlas exclusivamente a validacion
local. El design archivado de JUP-024 exige a JUP-023 un endpoint compatible
con response_format/schema; el contrato y el schema estricto permanecen intactos.

La primera via propuesta es seleccionar explicitamente un endpoint del mismo
GLM-5.2 dentro de OpenRouter, sin fallback, manteniendo ZDR y data_collection deny.
El catalogo publico anuncia structured_outputs para DeepInfra `deepinfra/fp4`;
es candidato, no compatibilidad probada ni seleccion aprobada. Antes de editar,
acordar el endpoint y la configuracion exactos. No se cambia el modelo, el gateway
ni se incorpora una conexion directa a otro servicio. Las reservas acumuladas
deben conciliarse antes de repetir llamadas reales, sin ampliar el presupuesto.

## Human Compatible Endpoint Approval

El 2026-10-02 Paris responde "ok apruebo entonces" a la propuesta concreta de
probar DeepInfra `deepinfra/fp4` A TRAVES de OpenRouter, con el mismo GLM-5.2
y schema estricto completo. Para `economicon-chat`, autoriza
`extra_body.provider.only: [deepinfra/fp4]` y `require_parameters: true`,
conservando ZDR, `data_collection: deny`, `allow_fallbacks: false`,
`reasoning.enabled: false`, timeout de 30 s y maximo de 800 tokens.
Secundario y embeddings permanecen sin cambios. No se autoriza simplificar
schema, cambiar modelo, conexion directa a DeepInfra ni relajar privacidad.

La seleccion queda aprobada; su compatibilidad sigue sin demostrar. Continuar
con tester tras la validacion documental, reutilizando pruebas/fixture existentes,
sin volver a solicitar esta misma aprobacion. Gate de pago pendiente: cuatro
fallos previos de chat HTTP 400, consumo observado 0 USD y reservas conservadoras
de 0,40 USD retenidas contra cap upstream 0,40 USD sin reinicio. Conciliar antes
de otra llamada, sin liberar reservas por el cero observado ni elevar caps;
se conserva el techo agregado 0,50 EUR. Esta fase solo modifica documentos.

CONTRIBUTING local sin `Process version` y adopcion local `2026-09-30 (JUP-100)`;
Paris liderazgo, Victor pairing, Alejandro revision y Lucia validacion. Esta
aprobacion no constituye review humana ni acepta automaticamente ADR-0002.
No autoriza commits, PR, tracker, integracion ni cierre.

## Embedding Accounting Continuation

El 2026-10-02 Paris indica "ok continua" tras el resultado parcial de DeepInfra.
Continuar la correccion del ensayo temporal para conciliar costes ausentes en
la respuesta con informacion oficial verificable y completar la persistencia
real. No modifica producto, schema, modelos, privacidad ni limites. Mantener
techo agregado 0,50 EUR y cap upstream 0,40 USD sin reinicio; contabilizar el
uso previo de 0,001992921 USD y conciliar la reserva, sin asumir coste cero.
Primero comprobar offline la conciliacion, luego repetir el smoke secuencial
con sus controles y diagnostico saneado. Sin autorizacion de publicacion/cierre.

## Pending Embedding Budget Correction Approval

Estado inicial 2026-10-02: PENDING HUMAN APPROVAL; superado por la aprobacion
explicita registrada al final de esta seccion. Inicialmente solo se autorizo preparar esta
enmienda documental; no implementar, modificar pruebas ni consumir. F1 bloquea
QA: el smoke completo paso, pero SpendLogs registra cero para 12 tokens de
embedding con delta oficial positivo de 0,000000240 USD, sin prueba posterior
del contador virtual. Ver [smoke y limites](../../../docs/evidence/JUP-023-validation.md#successful-real-smoke-and-accounting).

Propuesta concreta: solo en `economicon-embedding`, configurar `model_info`
con `input_cost_per_token: 0.00000002` USD y `output_cost_per_token: 0.0`, mas
`extra_body.provider.max_price.prompt: 0.02` USD por millon. Tarifa contrastada
el 2026-10-02: calculo derivado, no factura individual. Verificar mantenimiento,
sintaxis y transmision de max_price primero con upstream simulado; no se afirma
que ya se hayan probado. Detenerse si precio cambia/no es verificable o no se
conoce cap/margen; no subir caps ni tratar cero/desconocido como consumo gratis.

Tras aprobacion, reutilizar Node y test/fixture Docker existentes para demostrar
SpendLogs positivo, avance real del contador virtual y rechazo tras agotar cap
mediante llamadas simuladas, sin precargar gasto. Despues exigir una sola llamada
real acotada de embedding, sin retries, para comprobar coste, contador virtual
y uso oficial bajo 0,50 EUR agregados y cap upstream 0,40 USD sin reinicio,
incluyendo el total previo 0,002591308 USD. No repetir chat/suites no afectadas.

La frase historica "Secundario y embeddings permanecen sin cambios" pertenece
a la seleccion DeepInfra, no autoriza ni describe esta nueva correccion: la
tarifa de embedding solo cambiara si se aprueba. No cambiar modelos, schema,
dimensiones, privacidad, SDK, dependencias o imagen ni crear servicio contable.
No hay nueva decision de arquitectura que requiera ADR. Se conservan las
aprobaciones previas, los gates de pruebas reales/revision/QA/aprobacion final
y la ausencia de autorizacion de PR/publicacion. Proceso: CONTRIBUTING vigente
sin `Process version`, adopcion local `2026-09-30 (JUP-100)`; Paris liderazgo,
Victor pairing, Alejandro revision, Lucia validacion, sin atribuirles reviews.

### Human Approval: Embedding Budget Correction

Decision: APROBADO por Paris el 2026-10-02 mediante "ok pues apruebo entonces",
tras aclarar que 0,02 USD por millon es la tarifa del modelo, no el limite de
la clave. Se aprueba la correccion exacta descrita arriba, pruebas existentes
primero, verificacion Docker simulada y despues una unica llamada real de
embedding sin retries para verificar coste y contador. No cambiar el cap
upstream de 0,40 USD sin reinicio ni el techo agregado de 0,50 EUR; incluir
el consumo anterior de 0,002591308 USD y verificar precios/margen antes de llamar.
No repetir chat ni introducir otro modelo, schema, imagen o sistema contable.
Esta aprobacion desbloquea implementacion y comprobaciones de F1, no equivale
a QA final ni autoriza commits, push, PR, merge, archivado o cambios en Trello.

## Develop Reconciliation

El 2026-10-02 Paris autoriza actualizar develop y reconciliar esta rama.
Ambas avanzan de `5a54ce2` a `11d63ea` por fast-forward, incorporando JUP-100
(PR #56), sin conflictos ni cambios al producto, configuracion o pruebas locales.
Las menciones anteriores a una adopcion local o PR #56 abierta son historicas:
la fuente actual es CONTRIBUTING y AGENTS en `11d63ea`, Process version
`2026-09-30 (JUP-100)`, ya integrada. No se ha verificado la activacion remota
de sus rulesets. Se mantienen Paris liderazgo, Victor pairing, Alejandro
revision y Lucia validacion; no se atribuye participacion humana a agentes.
No cambia alcance ni criterios de aceptacion. Esta autorizacion solo cubre
la reconciliacion local, no publicacion, archivo, merge de entrega ni Trello.
Evidencia y controles afectados en [validacion](../../../docs/evidence/JUP-023-validation.md#develop-reconciliation).

## PR 65 Attempt Deadline Correction

Enmienda acotada del 2026-10-02 al contrato existente de 30 s maximos por
intento. Segun el feedback leido por el orquestador, Alejandro (`Iber1to`,
review `5396101137`) y Lucia (`lmatsan`, validacion `5396552390`) solicitan
cambios: con timeout 0,05 s y cero retries, HTTP loopback entrega 14/140 bytes
cada 0,03 s y tarda aproximadamente 0,42/4,4 s sin timeout efectivo. Es una
reproduccion comunicada, no ejecutada en esta fase documental.

Corregir el cliente compartido con deadline monotono por intento de transporte
HTTP que cubra conexion de socket, cabeceras y cuerpo, interrumpa lecturas bloqueadas y cierre el
transporte al vencer. Mantener ProviderError('timeout'), como maximo
retries configurados + 1 intentos, stdlib, rechazo de redirects, saneamiento
y rechazo terminal sin requeue. Pruebas locales focalizadas, sin gasto.
Alcance delimitado por la instruccion del usuario: "limitate a lo que se ha pedido en las revisiones de la pr por favor".
La resolucion DNS del sistema no es cancelable por este arreglo; no se garantiza
un plazo total que la incluya ni se atribuye aceptacion humana de esa limitacion.
Sin subprocesos DNS, resolver nuevo, refactor ni cambios en pika.
No ampliar arquitectura, dependencias ni ADR; dejar fuera los hallazgos no
bloqueantes de arranque Docker 45 s y dimension 1536. Esta fase solo modifica
proposal/design/tasks/spec; conserva aprobaciones y evidencias historicas.
Paris aprueba esta correccion local y sus pruebas con su respuesta explicita
"si" del 2026-10-02, tras presentar el defecto y la solucion acotada. Enmienda
validada antes de iniciar pruebas/codigo: OpenSpec estricto 38/38 y trazabilidad
PASS. No es aprobacion final ni autorizacion de publicacion o consumo real.
Sin llamadas OpenRouter, DockerServer, commits, publicacion, push, merge,
archivo ni cambios en trackers; tampoco fusionar la base durante esta fase.

### Human Approval: Real Revalidation After Timeout Correction

El 2026-10-03 Paris responde "si" a repetir una llamada de chat y otra de
embeddings por el gateway real antes de publicar la correccion. Autoriza como
maximo esas dos llamadas secuenciales, sin retries ni fallback, usando el
cliente local corregido y los modelos, ruta y privacidad ya aprobados.
Verificar primero precios, consumo acumulado, cap upstream de 0,40 USD sin
reinicio y limite de la clave virtual; conservar el techo agregado de 0,50 EUR.
Detenerse si no puede comprobarse coste o margen, sin repetir intentos fallidos
ni aumentar limites. Registrar respuestas validadas, tiempos, tokens y coste
sin secretos ni contenido, y retirar los recursos y credenciales temporales.
Esta autorizacion no cambia alcance ni sustituye las reviews humanas; no
autoriza commits, push, merge, archivado, Trello ni DockerServer compartido.

### Human Approval: Single Embedding Recheck

El 2026-10-03 Paris responde "sisi" a corregir el comprobador temporal y repetir
solo una llamada de embedding, tras comunicar el resultado parcial anterior.
Autoriza reparar y probar offline el ensayo temporal, sin modificar producto
ni pruebas permanentes, y una unica llamada real adicional sin retries ni chat.
Validar el vector antes de la conciliacion asincrona y conservar resultados
saneados aunque la contabilidad no se complete; no ocultar errores ni declarar
coste desconocido como cero. Mantener modelo, privacidad, dimension 1536, limites
y preflight previos, con techo agregado de 0,50 EUR y cap upstream de 0,40 USD
sin reinicio. El ultimo uso oficial observado es 0,003342170 USD, no un nuevo
presupuesto; releer el uso efectivo antes de consumir. No autoriza publicacion,
commits, merge, archivo, cambios de tracker ni recursos compartidos.
