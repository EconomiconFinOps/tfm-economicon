# Robustez ante datos incompletos o ambiguos — JUP-071

[Tarjeta](https://trello.com/c/H0woDubz) · [Casos](JUP-071-robustness-cases.json) · [Herramienta](../../tools/assistant-robustness.py) · [Evidencia](../evidence/JUP-071-validation.md)

La campaña ejecuta 16 perturbaciones y sus 13 referencias originales de [JUP-069](JUP-069-questions.json). Reutiliza el transporte, los prompts y la comprobación numérica de [JUP-070](JUP-070-evaluation.md). No cambia la batería original ni los umbrales de aceptación generales. Todos los importes y tenants son sintéticos. Las rúbricas no se envían al chat ni se indexan.

| Variantes | Riesgo comprobado |
| --- | --- |
| 001–005 | Tag ausente con asignación suficiente, null, vacío, desconocido y conflicto owner/costcenter |
| 006–007 | Coste compartido sin reparto aprobado o con pesos contradictorios |
| 008–010 | Denominador omitido, cero o volumen de negocio ausente |
| 011–012 | Periodos no comparables o no identificados |
| 013–014 | Moneda omitida y unidades temporales incompatibles |
| 015–016 | Ingesta parcial y ausencia de acceso al tenant real |

Los casos 001–003 requieren `answer`: la información disponible basta para una respuesta limitada. Rechazar todo no constituye robustez. Doce variantes requieren `clarify` y una `abstain`; aclarar puede incluir un cálculo parcial fundado. Todos los casos de esta campaña se tratan como críticos para exigir dos juicios humanos distintos, incluso cuando no tienen cifras esperadas. Esto amplía el criterio de criticidad numérica de JUP-070 a decisiones de asignación con datos inciertos.

## Reproducir la evidencia local

Python 3.12 o posterior, desde la raíz de la copia. Crear previamente una carpeta `../evaluacion-jup071` fuera del repositorio. Los comandos usan rutas relativas válidas tanto en PowerShell como en shells POSIX.

```sh
python tools/assistant-robustness.py validate
python -m unittest discover -s scripts/tests -p test_assistant_robustness.py -v
python tools/assistant-robustness.py prepare --output ../evaluacion-jup071/inputs.json
python tools/assistant-robustness.py offline --retrieval fixed --output ../evaluacion-jup071/fixed-raw.json
python tools/assistant-robustness.py score --raw ../evaluacion-jup071/fixed-raw.json --output ../evaluacion-jup071/fixed-report.json --report ../evaluacion-jup071/fixed-report.md
python tools/assistant-robustness.py offline --retrieval empty --output ../evaluacion-jup071/empty-raw.json
python tools/assistant-robustness.py score --raw ../evaluacion-jup071/empty-raw.json --output ../evaluacion-jup071/empty-report.json --report ../evaluacion-jup071/empty-report.md
```

`offline` llama al `AssistantService.answer` real del checkout, con recuperación vacía o un fragmento fijo: los primeros 500 caracteres de la primera fuente que declara el caso, sin elegirlo por relevancia con la pregunta. El fragmento fijo lleva distancia artificial cero: **no se ejecutan embeddings, búsqueda vectorial, HTTP, SQL, gateway ni modelo**. Se importa el servicio de la versión de plantilla actual, que no requiere dependencias externas. Si JUP-035 cambia su constructor o lo hace asíncrono, adaptar explícitamente este runner y volver a medir. El hash fijado del servicio impide que `offline` ejecute silenciosamente otro código; nunca reemplazar silenciosamente el servicio por respuestas esperadas.

Los dos modos son condiciones de prueba diferentes, no repeticiones equivalentes. Su latencia no se mide: no se interpreta como rendimiento del servicio desplegado.

## Recoger desde un chat desplegado

El adaptador reutiliza `collect_cases` de JUP-070: login, conversación nueva por caso, prompt exacto y petición de mensaje. No hay reintentos. Conserva un error de transporte como `blocked`; un login fallido aborta la campaña, sin inventar 29 respuestas. `DEMO_PASSWORD` se establece mediante el entorno, nunca en la línea de comandos ni en evidencia versionada.

Crear fuera de Git una ficha sin secretos con `commit`, `corpus`, `provider`, `alias`, `retrieval` y `generation`, siguiendo JUP-070. Incluir en ella versión del dataset, prompt del sistema, alias/temperatura reales y evidencia de configuración del despliegue. Son datos declarados por quien opera, no mediciones del cliente.

```sh
python tools/assistant-robustness.py collect --tenant tenant-core --run-info ../evaluacion-jup071/run-info.json --output ../evaluacion-jup071/live-raw.json
python tools/assistant-robustness.py review-sheet --raw ../evaluacion-jup071/live-raw.json --output ../evaluacion-jup071/review.md --judgments-template ../evaluacion-jup071/judgments.json
```

La recogida se etiqueta siempre `live_unverified`. El contrato HTTP actual no atestigua qué modelo generó la respuesta. Un alias en la ficha, un HTTP 200, embeddings reales o una prueba del gateway por separado **no acreditan generación**. El hash del servicio local identifica el código inspeccionado, no el desplegado; el commit de la ficha debe contrastarse con el despliegue por separado.

## Puntuar sin inventar juicios

La hoja muestra pregunta, contexto, rúbrica, respuesta completa, citas y fragmentos. Mantener hoja, crudos, fichas y juicios fuera de Git. La herramienta rechaza sus salidas dentro de este checkout, salvo los informes generados `JUP-071-*-report.json`, `JUP-071-*-report.md` y `JUP-071-*-rows.json` de `docs/evidence/`. No registrar credenciales en la ficha.

En la plantilla de juicios, cada lista vacía se completa por las personas que realmente juzgaron el punto. `raw_sha256` vincula los juicios al crudo completo: no trasladarlos a otra respuesta ni cambiar ese hash para reutilizarlos.

```json
{"reviewer": "identificador de quien revisó", "result": "fail", "note": "motivo concreto"}
```

Cada punto `behavior`, `required-N` y `forbidden-N` necesita dos personas distintas. `forbidden-N` pasa cuando **no** ocurre la conducta prohibida. No se usan regex para declarar una prohibición semántica satisfecha. Los nombres se normalizan sin tildes ni mayúsculas; duplicar una identidad es error. Desacuerdo conserva `fail`. La herramienta valida la estructura de los juicios, no autentica identidades.

```sh
python tools/assistant-robustness.py score --raw ../evaluacion-jup071/live-raw.json --judgments ../evaluacion-jup071/judgments.json --output ../evaluacion-jup071/report.json --report ../evaluacion-jup071/report.md
```

`--provisional` permite un juicio por punto y marca el informe. Sin juicios se comprueban sólo cifras; no se genera ningún juicio ficticio. `check_number` conserva las limitaciones conocidas de JUP-070 (por ejemplo cifras escritas con palabras). El eco del prompt se informa como diagnóstico, no como prueba semántica autónoma.

| Estado | Significado |
| --- | --- |
| `pass` | Todas las cifras y todos los juicios requeridos pasan |
| `fail` | Existe un fallo conocido, incluso si quedan otros juicios pendientes |
| `blocked` | Error de infraestructura al recoger ese caso |
| `not_run` | Falta respuesta o faltan juicios, sin otro fallo ya comprobado |

`assessment_complete=false` conserva cualquier falta de juicio aunque el estado sea `fail`. Se publican cuatro conteos y `pass/total`, con todos los casos en el denominador. También se publica `pass/(pass+fail)`, con denominador explícito y `null` si está vacío: incluye fallos conocidos con juicios pendientes y no mide cobertura de revisión humana. No convertir `0/29` de una campaña sin juicios en tasa de error semántico del modelo. Las parejas muestran resultados original/perturbado; no se afirma regresión causal si el original ya falla o está pendiente.

Los informes sólo contienen IDs, hashes, estados, resultados por punto y versiones, sin textos de respuestas ni nombres. No son el formato del calculador JUP-067: los subgrupos propios no equivalen a su batería completa, sus métricas de relevancia ni sus umbrales globales. Para aquellas métricas ejecutar JUP-070 con los 28 casos.

## Repeticiones y aceptación pendiente

Hacer al menos tres recogidas separadas con los mismos casos y configuración; puntuar cada una conservando todas, incluidas las malas:

```sh
python tools/assistant-robustness.py compare ../evaluacion-jup071/report-1.json ../evaluacion-jup071/report-2.json ../evaluacion-jup071/report-3.json
```

`compare` rechaza distintos corpus/configuración, suite, versión del runner, servicio local, Python, tipo de ejecución o provisionalidad y crudos duplicados. Los hashes facilitan auditoría, pero no prueban independencia de una captura manipulada: quien valida debe comprobar crudos y trazas.

`generative_robustness_accepted` permanece falso en todos los informes de esta versión. Para una conclusión generativa faltan contraste de JUP-035 integrado, evidencia del commit/modelo/prompt desplegado, tres recogidas reales iguales y los juicios independientes. Entonces el equipo debe revisar explícitamente el contrato de procedencia y la interpretación de resultados; no editar el booleano a mano. La presente entrega completa el instrumento y su evaluación local acotada. No declara la tarjeta aceptada, las revisiones humanas hechas ni robustez generativa.

## Re-fijar la batería cuando cambia un fichero que referencia

La batería (`JUP-071-robustness-cases.json`) fija el hash del banco de JUP-069 (`baseline.sha256` y `baseline.suite_version`), el de la metodología de JUP-070 (`methodology.sha256`) y los de las fuentes del corpus (`sources`), que deben ser idénticos a los del propio banco de JUP-069. La herramienta fija además el hash de `apps/backend/app/services/assistant.py` (`TEMPLATE_SHA256`, en `tools/assistant-robustness.py`) porque la ejecución offline usa el servicio real. Si un PR cambia uno de esos ficheros, `assistant-robustness:validate` y la CI («OpenSpec») fallan hasta re-fijar. Pasos: (1) comprobar que las preguntas, las reglas y las cifras de las variantes siguen vigentes con el contenido nuevo; (2) si cambia una fuente del corpus, el banco de JUP-069 debe actualizar primero su propia referencia (y su `suite_version`), porque la validación exige que la batería y el banco declaren las mismas fuentes; después se copian a la batería `baseline.sha256`, `baseline.suite_version` y `sources`; (3) para obtener un hash se usa el resumen que calcula `file_digest` de la herramienta, que lee el fichero como texto UTF-8 y no depende de los finales de línea (por ejemplo, `python -c "import hashlib,pathlib,sys;print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').encode()).hexdigest())" <fichero>`); (4) si cambia `assistant.py`, actualizar `TEMPLATE_SHA256`, lo que cambia `harness_sha256` y `harness_commit` de los informes; (5) regenerar los informes de plantilla y sus `rows` de `docs/evidence/` y anotar la regeneración en el registro de la evidencia. La identidad de la batería es su hash (`suite_sha256`), que cambia con cualquier edición; el número `suite_version` es una etiqueta humana.

## Historial de cambios tras las revisiones (registro histórico)

Es un registro cronológico: donde una regla se repita con otro detalle, manda la más reciente (por ejemplo, los valores declarados que se describen en «Descripción de la ejecución con el colector de JUP-123») y la spec del change.

### Primera pasada (13/10/2026)

Las cifras esperadas de una variante pueden llevar una lista `aliases` propia en la batería (obligatoria de facto cuando el caso no hereda las reglas de JUP-070, como en JUP-071-002 y JUP-071-003); el lector numérico las usa antes que las reglas del banco y que la etiqueta. La validación exige riesgo `critical` en todo caso con cifras esperadas y una versión de batería con formato `x.y.z`.

El informe añade un desglose `categories` (tagging, allocation, costs, anomalies, scope) además del desglose por tipo de perturbación, que tiene un solo caso por grupo. El Markdown muestra el total previsto, `pass / total previsto`, `pass / (pass + fail)` o «no disponible» si no hay casos evaluados, y advierte de que el denominador `pass + fail` incluye fallos conocidos con juicios pendientes.

Con `--provisional`, cada caso crítico con menos de dos revisores por punto lleva `reduced_coverage` y `assessment_complete` es falso mientras exista alguno.

Los valores declarados `provider`, `alias` y `model_alias` del bloque `run` no admiten `:` ni prefijos con forma de clave (`sk-`, `key-`, `token-`...); es una comprobación heurística, no una garantía de que no haya secretos. Las salidas dentro del repositorio se limitan a `docs/evidence/`. Los prefijos de ruta extendida de Windows se normalizan antes de comparar; el CLI de JUP-070 conserva ese defecto (ver `openspec/findings/backlog.md`).

### Segunda pasada (13/10/2026)

Los rivales de una cifra son los alias de las demás cifras del caso, igual que en JUP-070, de modo que una cifra bajo la etiqueta de otra no se acepta. Los alias deben quedar no vacíos y ser únicos tras normalizar. La validación de la batería devuelve un error con el identificador del caso ante tipos mal formados o campos ausentes.

Los valores declarados `provider`, `alias` y `model_alias` son identificadores en minúsculas (`a-z`, dígitos, `.`, `/`, `-`) de hasta 64 caracteres, sin partes con forma de clave o de token; sigue siendo una comprobación heurística. Las rutas de red (UNC), incluidas las de recursos administrativos como `\\localhost\D$`, no se aceptan como salida, y los puntos o espacios finales de un componente se descartan antes de comparar. Dentro del repositorio solo se pueden escribir los informes generados `JUP-071-*-report.json` y `.md` de `docs/evidence/`.

El Markdown muestra el número de casos con cobertura reducida, si la evaluación está completa y el resultado por cada tipo de perturbación.

### Límites conocidos tras la tercera pasada

El lector numérico de JUP-070 solo mira la etiqueta anterior a la cifra: una respuesta correcta con la etiqueta de otra cifra antes de la propia (por ejemplo «de 10 EUR/pedido en julio a 6 EUR/pedido en agosto») puede quedar en `fail` en `numbers-N` y los juicios humanos no lo revierten. Ante un `fail` numérico en los casos con varias cifras, comprobar la respuesta a mano antes de atribuirlo al asistente. Está registrado en `openspec/findings/backlog.md`.

Los valores declarados del bloque `run` se escriben en minúsculas, sin `:` ni `@`; un alias con sufijo de proveedor (por ejemplo `alias-modelo:sufijo`) hay que declararlo sin ese sufijo. Los alias de `infra/litellm/config.example.yaml` y de ADR-0002 se aceptan.

### Distancia no medida y contrato del dashboard (16/10/2026)

El crudo admite fragmentos con `distance: null` (el servidor no informó distancia; nunca se escribe cero) y una lista opcional `public_evidence` por caso, que la hoja de revisión muestra junto a las citas. Un colector puede detectar `ACCEPTS_UNMEASURED_DISTANCE` en esta herramienta para exportar esa evidencia en lugar de bloquear la fila.

Para el dashboard de JUP-121, `python tools/assistant-robustness.py rows --input <informe-de-puntuacion.json> --output <fichero>` escribe el informe como `rows-v1` (identificadores y números, sin texto ni nombres), con los estados por categoría y por tipo de perturbación. Pass y fail, las tasas y la cobertura reducida van como juicio humano; las comprobaciones numéricas por regla, automáticas. Se valida primero la coherencia del informe; una tasa sin casos evaluados sale `not_measured` con valor nulo; una ejecución real no verificada deja `generation_model` nulo para que el dashboard la marque como sin modelo verificado. Si la recogida trae el hash de prompt que reporta el servidor y es el mismo en todas las muestras, el informe lo registra (no atestiguado) y `rows` lo copia a `prompt_sha256`; si difiere o falta, queda nulo. Un hash que no sean 64 hexadecimales en minúscula, una entrada marcada como atestiguada o este bloque en una ejecución de plantilla rechazan la colección; si el servidor emitiera mayúsculas habría que normalizarlo en el colector (pendiente de confirmar con #131). Dentro del repositorio solo se aceptan los ficheros generados `JUP-071-*-rows.json` de `docs/evidence`.

### Descripción de la ejecución con el colector de JUP-123 (16/10/2026)

El colector de JUP-123 escribe el `run-info` con seis cadenas. El bloque `run` acepta `generation` como una sola cadena, que registra como alias del modelo sin temperatura, y un commit declarado de 7 a 40 caracteres hexadecimales en minúscula. `provider`, `alias` y la propia cadena de `generation` siguen sujetos al patrón restringido (minúsculas, dígitos, `.`, `/`, `-`, hasta 64 caracteres y sin forma de clave), de modo que `SHA_DESPLEGADO_DECLARADO` u otros marcadores de la guía de ese colector hay que sustituirlos por valores reales. El adaptador del colector fija el commit y los hashes de esta herramienta en su plan: cualquier cambio posterior en la copia de JUP-071 obliga a preparar otro plan y a volver a leer los recibos.

### Revisión final (16/10/2026)

Las variantes de cumplimiento de tagging (JUP-071-002 y JUP-071-003) piden ahora una sola cifra, el cumplimiento por coste, igual que el caso de JUP-069 del que derivan; antes exigían además el coste etiquetable, que su pregunta no pide, y una respuesta correcta que daba solo el 10 % fallaba sin remedio por juicio humano.

Los números de las cifras esperadas, la temperatura declarada, las distancias recuperadas y las duraciones deben ser finitos; un entero demasiado grande para un número de coma flotante o un documento anidado miles de niveles terminan en un error controlado con código dos. La descripción de la ejecución de `collect` admite exactamente los seis campos declarados (commit, corpus, proveedor, alias, recuperación y generación): un campo adicional se rechaza por su nombre, sin repetir su valor, porque la descripción se guarda entera junto al crudo. `compare` rechaza con un error controlado informes que no tengan los campos esperados. La tabla de tipos de perturbación del informe muestra el total de cada grupo.

La validación de los valores declarados comprueba la forma y no el significado: `tbd` o `unknown` cumplen el patrón. Lo que se rechaza es lo que el colector de JUP-123 usa como marcador descriptivo (mayúsculas y guiones bajos) y lo que parece una clave.

**Limitación abierta para medir el chat real.** Las evidencias de corpus del chat de JUP-035 entrega A no traen `distance`. La cabeza `af8388d0` del colector de JUP-123 bloqueaba esas filas; la actual (`e0a0c41e`) detecta `ACCEPTS_UNMEASURED_DISTANCE` y exporta `distance: null` y `public_evidence`, que esta herramienta acepta sin inventar distancias. Falta validarlo con un backend real que devuelva evidencia de corpus y con la CI del colector en verde. Está registrado como tarea 6.6.
