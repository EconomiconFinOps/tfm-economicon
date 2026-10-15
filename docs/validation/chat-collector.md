# Colector reutilizable del chat — JUP-123 / JUP-071

[JUP-123](https://trello.com/c/TqtcumIN) · [JUP-071](https://trello.com/c/H0woDubz)

Python3.12+, biblioteca estándar. Esta entrega extrae la recogida de evidencia
de B; no cambia backend, processor, frontend, prompts, modelos ni corpus.
No depende de que se integre B. El servidor debe ofrecer el contrato de operaciones
de A: `GET /assistant/conversations/{id}` y
`GET /assistant/conversations/{id}/generations/{operation_id}` con sus recursos
`context`, `evidence` y `result`. Un servidor anterior que sólo exponga mensajes
no cumple ese contrato. El chat no tiene que activarse para leer operaciones
persistidas, si el despliegue permite esas lecturas autenticadas.

## Qué hace y qué queda fuera

`tools/chat-eval-collect.py` observa una operación **ya existente y terminal**.
Compara el estado antes/después, pregunta exacta, resultado e historial, e IDs de
citas. Conserva errores y recursos con SHA256. No crea conversaciones, hace POST,
reanuda operaciones ni llama al proveedor. `VERIFIED_PUBLIC_SNAPSHOT` acredita
esas comprobaciones; no la corrección semántica, el modelo, el commit desplegado,
la latencia ni el coste. Las credenciales llegan por `CHAT_EVAL_TOKEN` y
`CHAT_EVAL_TENANT`, nunca por argumentos, planes o recibos.

Cada muestra necesita una conversación nueva con una pregunta y una respuesta.
Los casos con conversación previa necesitan otro adaptador. Para generar las
operaciones se utiliza el flujo autorizado del chat o un ejecutor con contabilidad;
esta PR **no entrega un ejecutor de campañas de pago** ni adapta el POST antiguo
de JUP-071. Leer respuestas existentes no aumenta gasto ni modifica reservas.

## Usarlo con los 29 casos de JUP-071

Conservar otra copia de JUP-071 que contenga `tools/assistant-robustness.py` y su
banco. El adaptador importa **código local de confianza** de esa copia; no la
descarga ni ejecuta el modo `offline` de la antigua plantilla. Corte comprobado:
`test/JUP-071-robustness`, commit `81ceafc67ba400414040b1468d795a41d9d5468d`.
Una vez integrada JUP-071 puede usarse la misma copia mediante `--suite-root .`.
Los ejemplos parten de la raíz de esta PR y de una copia hermana `../jup071`.

Crear previamente `../evaluacion-jup071` fuera de ambos repositorios. Preparar N3
(también se admiten1 y5):

```sh
python tools/chat-eval-jup071.py --suite-root ../jup071 prepare --repetitions 3 --output ../evaluacion-jup071/plan.json
```

El plan contiene29casos×3repeticiones, con los13originales y16perturbaciones;
usa **el prompt exacto de JUP-071** (`contexto + salto de línea + pregunta`), sin
rúbricas ni respuestas esperadas. Congela commit y hashes del banco, evaluador,
metodología y fuentes. Si cambia esa copia, el adaptador exige preparar otro plan;
no altera el banco de28casos de JUP-069 ni los juicios de JUP-071.

Tras ejecutar cada pregunta en su conversación nueva por el flujo autorizado,
guardar su identidad durable en `handles.json` (array; se admiten subconjuntos):

```json
[
  {"sample_id":"JUP-069-002:r1","conversation_id":"ID_CONVERSACION","operation_id":"ID_OPERACION"},
  {"sample_id":"JUP-071-001:r1","conversation_id":"OTRA_CONVERSACION","operation_id":"OTRA_OPERACION"}
]
```

Los IDs se obtienen de la operación iniciada por el chat y de su URL pública;
no son el ID del mensaje ni los de una ejecución antigua. La pregunta almacenada
debe coincidir exactamente con `samples[].content`. Repetir una identidad entre
muestras o añadir un caso desconocido aborta antes de consultar el API.

Con token y tenant ya establecidos en el entorno, recoger una sola vez:

```sh
python tools/chat-eval-jup071.py --suite-root ../jup071 collect --plan ../evaluacion-jup071/plan.json --handles ../evaluacion-jup071/handles.json --base-url http://127.0.0.1:8000 --output-dir ../evaluacion-jup071/recibos
```

HTTP sin TLS sólo se admite en loopback; para otro host usar HTTPS o túnel SSH.
Se rechazan redirects y proxies del entorno para no reenviar credenciales.
El directorio de salida debe ser **nuevo**: contiene plan, handles, recibos
originales en `originals/`, vistas derivadas y manifiesto con hashes. Un timeout,
HTTPfallido o estado vivo queda incompleto; no provoca otra generación. Si la
recogida se interrumpe antes del manifiesto, conservar esos archivos e investigar
la causa; no sobrescribir ni eliminar el intento para seleccionar un resultado.

## Evidencia RAG incorporada después del contexto inicial

El API puede devolver sólo la evidencia inicial, mientras las citas finales
usan fragmentos de una recuperación posterior. En ese caso la recogida queda
`INCOMPLETE`. Opcionalmente pasar `--retrieval-snapshots ARCHIVO_JSON`, array de
objetos con esta forma, obtenido del **payload real conservado** de cada operación:

```json
[{"operation_id":"ID_OPERACION","evidence":[],"omissions":[],"content_sha256":"HASH_REAL"}]
```

`tools/chat-eval-retrieval.py` exige operación, lista ordenada de evidencias e
identidad SHA256 exactas frente al manifest del resultado, incluido el escape de
ángulos y UTF8. No ejecuta otra búsqueda, no recupera por similitud y no inventa
fragmentos. El adaptador conserva el original antes de derivar otra vista y
guarda el suplemento aparte. Un suplemento incorrecto no convierte el caso en
éxito; se conserva como recogida incompleta. No incluye un extractor SQL universal:
si el operador no dispone del payload exacto, debe mantener ese bloqueo.

## Exportar al evaluador existente

Crear `run-info.json` con **exactamente** seis cadenas descriptivas, sin secretos:

```json
{"commit":"SHA_DESPLEGADO_DECLARADO","corpus":"VERSION","provider":"PROVEEDOR_DECLARADO","alias":"ALIAS_DECLARADO","retrieval":"CONFIGURACION","generation":"CONFIGURACION"}
```

El adaptador vuelve a comprobar originales, hashes, pregunta, estado y evidencia;
no se fía de una etiqueta `VERIFIED` modificada. Exportar cada repetición por
separado, cambiando1 por2 y3 y usando salidas nuevas:

```sh
python tools/chat-eval-jup071.py --suite-root ../jup071 export --plan ../evaluacion-jup071/plan.json --receipts ../evaluacion-jup071/recibos --repetition 1 --run-info ../evaluacion-jup071/run-info.json --output ../evaluacion-jup071/raw-r1.json
python ../jup071/tools/assistant-robustness.py review-sheet --raw ../evaluacion-jup071/raw-r1.json --output ../evaluacion-jup071/review-r1.md --judgments-template ../evaluacion-jup071/judgments-r1.json
python ../jup071/tools/assistant-robustness.py score --raw ../evaluacion-jup071/raw-r1.json --output ../evaluacion-jup071/report-r1.json --report ../evaluacion-jup071/report-r1.md
```

El formato sigue siendo `raw_version:1`, `live_unverified` y
`model_execution_verified:false`. Falta de respuesta → muestra ausente (`not_run`
en el scorer); fallo técnico/incompleto → `failure_category:invalid_response`
(`blocked`). No se generan juicios humanos ni una aceptación de robustez.
El último comando ilustra puntuación sin juicios: para aceptación se aplican los
juicios y reglas de JUP-071; `review-sheet` no sustituye esa revisión.

`public_evidence` de cada fila conserva los fragmentos completos. La lista antigua
`retrieved` sólo incluye los que traen distancia numérica real; **no se fabrica
distancia0** para satisfacer su esquema. La hoja antigua puede no mostrar esos
fragmentos: revisar también `public_evidence` del JSON y los originales. Toda esa
evidencia privada permanece fuera de Git. `total_ms:null` evita presentar tiempo
de lectura como latencia de generación.

N3 debe recogerse en **un lote** con conversaciones distintas para las87muestras.
Las tres exportaciones de ese lote conservan configuración idéntica y timestamp
inmutable; reexportar la misma repetición no crea una ejecución independiente.
Luego puede usarse `assistant-robustness.py compare report-r1.json report-r2.json
report-r3.json` según sus reglas. Los metadatos del operador siguen siendo
declaraciones, no atestación del despliegue.

## Pruebas sin proveedor

```sh
python -m unittest discover -s tools -p 'test_chat_eval_collect*.py' -v
```

CI ejecuta el mismo conjunto con `pnpm chat-collector:test`. Incluye un servidor
HTTP local y fallos de transporte, preguntas/historial distintos, citas ajenas,
snapshots RAG alterados, archivos modificados, salidas existentes y aislamiento
de repeticiones. No necesita gateway, Docker, claves ni paquetes Python externos.
