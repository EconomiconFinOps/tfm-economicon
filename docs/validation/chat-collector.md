# Colector reutilizable del chat — JUP-123 / JUP-071

[JUP-123](https://trello.com/c/TqtcumIN) · [JUP-071](https://trello.com/c/H0woDubz)

Python 3.12+, biblioteca estándar. Esta entrega extrae la recogida de evidencia
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

JUP-071 está integrada en `develop/ee4e8031` por #136 y en este árbol reconciliado:
puede usarse la misma copia mediante `--suite-root .`. También se admite otra
copia explícita que contenga `tools/assistant-robustness.py` y su banco. El
adaptador importa **código local de confianza**; no lo descarga ni ejecuta el
modo `offline` de la antigua plantilla. La compatibilidad legada se comprobó en
`81ceafc67ba400414040b1468d795a41d9d5468d`; la integrada anuncia la capacidad para
distancia no medida. Los ejemplos siguientes siguen usando una copia hermana
`../jup071`; si se usa este checkout, sustituir ese destino por `.`.

Crear previamente `../evaluacion-jup071` fuera de ambos repositorios. Preparar N3
(también se admiten 1 y 5):

```sh
python tools/chat-eval-jup071.py --suite-root ../jup071 prepare --repetitions 3 --output ../evaluacion-jup071/plan.json
```

El plan contiene 29 casos × 3 repeticiones, con los 13 originales y 16 perturbaciones;
usa **el prompt exacto de JUP-071** (`contexto + salto de línea + pregunta`), sin
rúbricas ni respuestas esperadas. Los planes nuevos (`version: 2`) congelan los hashes
del banco, evaluador, métricas, calibrador, servicio, reglas, metodología y fuentes.
El commit se conserva como referencia informativa: un commit ajeno a esos ficheros
no invalida el plan ni cambia `harness_commit` al reexportar. Si cambia algún contenido
congelado o prompt, el adaptador exige preparar otro plan. Los planes de versión 1
siguen admitidos con su contrato original, incluido el commit fijo;
no altera el banco de 28 casos de JUP-069 ni los juicios de JUP-071.

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
HTTP fallido o estado vivo queda incompleto; no provoca otra generación. Si la
recogida se interrumpe antes del manifiesto, conservar esos archivos e investigar
la causa; no sobrescribir ni eliminar el intento para seleccionar un resultado.
La salida JSON incluye `summary` con muestras previstas, observadas y ausentes,
y conteos por estado de recogida y de operación. `collect --strict` conserva todos
los recibos y devuelve código 3 si falta alguna muestra, está incompleta o no ha
terminado con `completed`. Sin `--strict` una recogida parcial sigue devolviendo 0.

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
no se fía de una etiqueta `VERIFIED` modificada. Se puede exportar una repetición,
cambiando 1 por 2 y 3 y usando salidas nuevas:

```sh
python tools/chat-eval-jup071.py --suite-root ../jup071 export --plan ../evaluacion-jup071/plan.json --receipts ../evaluacion-jup071/recibos --repetition 1 --run-info ../evaluacion-jup071/run-info.json --output ../evaluacion-jup071/raw-r1.json
python ../jup071/tools/assistant-robustness.py review-sheet --raw ../evaluacion-jup071/raw-r1.json --output ../evaluacion-jup071/review-r1.md --judgments-template ../evaluacion-jup071/judgments-r1.json
python ../jup071/tools/assistant-robustness.py score --raw ../evaluacion-jup071/raw-r1.json --output ../evaluacion-jup071/report-r1.json --report ../evaluacion-jup071/report-r1.md
```

Para exportar todas las repeticiones del plan de una vez (N1, N3 o N5):

```sh
python tools/chat-eval-jup071.py --suite-root ../jup071 export --plan ../evaluacion-jup071/plan.json --receipts ../evaluacion-jup071/recibos --all-repetitions --run-info ../evaluacion-jup071/run-info.json --output-dir ../evaluacion-jup071/exportaciones --strict
```

El directorio debe ser nuevo y recibe `raw-r1.json`, etc. Se validan todas las
exportaciones antes de crearlo. `export --strict` guarda los resultados y devuelve
3 si hay filas bloqueadas o muestras ausentes en las repeticiones elegidas. Su
resumen cuenta filas exportadas, bloqueadas, ausentes y estados estructurados.
Los códigos 0/2/3 significan guardado, error de entrada/validación y guardado
incompleto en modo estricto, respectivamente; no son dictámenes de calidad.

El formato sigue siendo `raw_version:1`, `live_unverified` y
`model_execution_verified:false`. Falta de respuesta → muestra ausente (`not_run`
en el scorer); fallo técnico/incompleto → `failure_category:invalid_response`
(`blocked`). No se generan juicios humanos ni una aceptación de robustez.
El último comando ilustra puntuación sin juicios: para aceptación se aplican los
juicios y reglas de JUP-071; `review-sheet` no sustituye esa revisión.

`public_evidence` de cada fila conserva los fragmentos completos. El formato
antiguo `retrieved` exige una distancia numérica medida: **no se inventa distancia
0**. Si el evaluador no anuncia la capacidad descrita debajo y falta esa distancia
en cualquier fragmento de corpus, la exportación queda
**bloqueada**: `failure_category: invalid_response`, respuesta y citas vacías.
El scorer de JUP-071 devuelve `blocked`; no puntúa esa respuesta como un fallo
semántico por citas colgantes o cifras no trazables. Originales, suplemento y
`public_evidence` permanecen intactos; la recogida puede seguir indicando
`VERIFIED_PUBLIC_SNAPSHOT` porque su verificación y la compatibilidad del formato
de puntuación son comprobaciones distintas.

**La evidencia de corpus que ofrece A no incluye `distance`. Por ello, todas
sus filas con corpus quedan bloqueadas para el evaluador legado**, incluso con
un suplemento RAG exacto. Las respuestas sin corpus no requieren distancia; los
fragmentos con distancia real conservan la exportación anterior. La adaptación
de JUP-071 integrada por #136 admite estas filas usando los IDs y el contenido
de la evidencia sin inventar distancias. El adaptador sólo abre esa exportación
cuando la herramienta importada anuncia la capacidad explícita; las copias
legadas siguen bloqueadas. Esto acredita compatibilidad de transporte y formato,
no calidad semántica ni aceptación de una campaña.

## Contrato con JUP-071 y el dashboard de JUP-121

Propuesta de Lucía del [16/10/2026](https://github.com/EconomiconFinOps/tfm-economicon/pull/131#issuecomment-6209801137),
implementada en el adaptador; la parte del evaluador y el dashboard pertenece a
sus ramas. No cambia `raw_version: 1`, los bancos ni los juicios.

| Campo o capacidad | Contrato |
| --- | --- |
| `ACCEPTS_UNMEASURED_DISTANCE = True` | Sólo el booleano `True` en `tools/assistant-robustness.py` habilita corpus con `distance: null`. Ausencia, `False`, cadenas o números mantienen el bloqueo legado. Las distancias medidas se conservan; valores mal formados, booleanos o no finitos bloquean incluso con la capacidad. JUP-071 debe adaptar validación, citas y trazabilidad de cifras antes de anunciarla. |
| `cases[].structured` | `{status, has_next_actions}`: estado de respuesta conocido y presencia de acciones como booleano, sin texto de acciones. Datos ausentes o instantánea no verificada producen `null`. Una fila bloqueada sólo por distancia puede conservar estos datos verificados; no equivale a aceptación semántica. |
| `execution.collection.accepts_unmeasured_distance` | Registra la capacidad efectiva del evaluador usado en esa exportación. |
| `execution.collection.server_reported[]` | Una entrada por muestra exportada con `sample_id`, `snapshot_verified` y `attested: false`. Copia `prompt_version`, hashes de esquema/ensamblador/tokenizer y `usage` cuando aparecen en los recursos originales revalidados. El manifiesto efectivo tiene prioridad sobre el inicial; `prompt_version` también puede venir de generación u operación. No los toma de `run-info`. |

`prompt_version` conserva íntegro su sufijo hash, que en A identifica el **bundle**,
no el texto del prompt. Sólo se exporta `prompt_sha256` si el servidor lo ofrece
explícitamente; no se calcula ni se renombra el hash del bundle. Tampoco se rellenan
los hashes o `usage` ausentes con valores locales o estimados. Son declaraciones
del servidor, sin atestación de runtime, modelo, facturación o gasto acumulado.

Los errores propios del adaptador indican el motivo seguro (por ejemplo, plan
distinto de las fuentes congeladas o `run-info` con campos incorrectos). Los
errores de validadores importados y transporte no imprimen su texto arbitrario,
que podría incluir secretos; los originales y las clases de error se conservan.

Toda esta evidencia permanece fuera de Git. `total_ms: null` evita presentar
tiempo de lectura como latencia de generación.

N3 debe recogerse en **un lote** con conversaciones distintas para las 87 muestras.
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
