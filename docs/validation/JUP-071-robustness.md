# Robustez ante datos incompletos o ambiguos — JUP-071

[Tarjeta](https://trello.com/c/H0woDubz) · [Casos](JUP-071-robustness-cases.json) · [Herramienta](../../tools/assistant-robustness.py) · [Evidencia](../evidence/JUP-071-validation.md)

La campaña ejecuta 16 perturbaciones y sus 13 referencias originales de
[JUP-069](JUP-069-questions.json). Reutiliza el transporte, los prompts y la
comprobación numérica de [JUP-070](JUP-070-evaluation.md). No cambia la batería
original ni los umbrales de aceptación generales. Todos los importes y tenants
son sintéticos. Las rúbricas no se envían al chat ni se indexan.

| Variantes | Riesgo comprobado |
| --- | --- |
| 001–005 | Tag ausente con asignación suficiente, null, vacío, desconocido y conflicto owner/costcenter |
| 006–007 | Coste compartido sin reparto aprobado o con pesos contradictorios |
| 008–010 | Denominador omitido, cero o volumen de negocio ausente |
| 011–012 | Periodos no comparables o no identificados |
| 013–014 | Moneda omitida y unidades temporales incompatibles |
| 015–016 | Ingesta parcial y ausencia de acceso al tenant real |

Los casos 001–003 requieren `answer`: la información disponible basta para una
respuesta limitada. Rechazar todo no constituye robustez. Doce variantes requieren
`clarify` y una `abstain`; aclarar puede incluir un cálculo parcial fundado. Todos
los casos de esta campaña se tratan como críticos para exigir dos juicios humanos
distintos, incluso cuando no tienen cifras esperadas. Esto amplía el criterio de
criticidad numérica de JUP-070 a decisiones de asignación con datos inciertos.

## Reproducir la evidencia local

Python 3.12 o posterior, desde la raíz de la copia. Crear previamente una carpeta
`../evaluacion-jup071` fuera del repositorio. Los comandos usan rutas relativas
válidas tanto en PowerShell como en shells POSIX.

```sh
python tools/assistant-robustness.py validate
python -m unittest discover -s scripts/tests -p test_assistant_robustness.py -v
python tools/assistant-robustness.py prepare --output ../evaluacion-jup071/inputs.json
python tools/assistant-robustness.py offline --retrieval fixed --output ../evaluacion-jup071/fixed-raw.json
python tools/assistant-robustness.py score --raw ../evaluacion-jup071/fixed-raw.json --output ../evaluacion-jup071/fixed-report.json --report ../evaluacion-jup071/fixed-report.md
python tools/assistant-robustness.py offline --retrieval empty --output ../evaluacion-jup071/empty-raw.json
python tools/assistant-robustness.py score --raw ../evaluacion-jup071/empty-raw.json --output ../evaluacion-jup071/empty-report.json --report ../evaluacion-jup071/empty-report.md
```

`offline` llama al `AssistantService.answer` real del checkout, con recuperación
vacía o un fragmento fijo del corpus correspondiente al caso. El fragmento fijo
lleva distancia artificial cero: **no se ejecutan embeddings, búsqueda vectorial,
HTTP, SQL, gateway ni modelo**. Se importa el servicio de la versión de plantilla
actual, que no requiere dependencias externas. Si JUP-035 cambia su constructor o
lo hace asíncrono, adaptar explícitamente este runner y volver a medir. El hash
fijado del servicio impide que `offline` ejecute silenciosamente otro código; nunca
reemplazar silenciosamente el servicio por respuestas esperadas.

Los dos modos son condiciones de prueba diferentes, no repeticiones equivalentes.
Su latencia no se mide: no se interpreta como rendimiento del servicio desplegado.

## Recoger desde un chat desplegado

El adaptador reutiliza `collect_cases` de JUP-070: login, conversación nueva por
caso, prompt exacto y petición de mensaje. No hay reintentos. Conserva un error de
transporte como `blocked`; un login fallido aborta la campaña, sin inventar 29
respuestas. `DEMO_PASSWORD` se establece mediante el entorno, nunca en la línea
de comandos ni en evidencia versionada.

Crear fuera de Git una ficha sin secretos con `commit`, `corpus`, `provider`,
`alias`, `retrieval` y `generation`, siguiendo JUP-070. Incluir en ella versión del
dataset, prompt del sistema, alias/temperatura reales y evidencia de configuración
del despliegue. Son datos declarados por quien opera, no mediciones del cliente.

```sh
python tools/assistant-robustness.py collect --tenant tenant-core --run-info ../evaluacion-jup071/run-info.json --output ../evaluacion-jup071/live-raw.json
python tools/assistant-robustness.py review-sheet --raw ../evaluacion-jup071/live-raw.json --output ../evaluacion-jup071/review.md --judgments-template ../evaluacion-jup071/judgments.json
```

La recogida se etiqueta siempre `live_unverified`. El contrato HTTP actual no
atestigua qué modelo generó la respuesta. Un alias en la ficha, un HTTP 200,
embeddings reales o una prueba del gateway por separado **no acreditan generación**.
El hash del servicio local identifica el código inspeccionado, no el desplegado;
el commit de la ficha debe contrastarse con el despliegue por separado.

## Puntuar sin inventar juicios

La hoja muestra pregunta, contexto, rúbrica, respuesta completa, citas y
fragmentos. Mantener hoja, crudos, fichas y juicios fuera de Git. La herramienta
rechaza sus salidas dentro de este checkout. No registrar credenciales en la ficha.

En la plantilla de juicios, cada lista vacía se completa por las personas que
realmente juzgaron el punto. `raw_sha256` vincula los juicios al crudo completo:
no trasladarlos a otra respuesta ni cambiar ese hash para reutilizarlos.

```json
{"reviewer": "identificador de quien revisó", "result": "fail", "note": "motivo concreto"}
```

Cada punto `behavior`, `required-N` y `forbidden-N` necesita dos personas distintas.
`forbidden-N` pasa cuando **no** ocurre la conducta prohibida. No se usan regex para
declarar una prohibición semántica satisfecha. Los nombres se normalizan sin tildes
ni mayúsculas; duplicar una identidad es error. Desacuerdo conserva `fail`.
La herramienta valida la estructura de los juicios, no autentica identidades.

```sh
python tools/assistant-robustness.py score --raw ../evaluacion-jup071/live-raw.json --judgments ../evaluacion-jup071/judgments.json --output ../evaluacion-jup071/report.json --report ../evaluacion-jup071/report.md
```

`--provisional` permite un juicio por punto y marca el informe. Sin juicios se
comprueban sólo cifras; no se genera ningún juicio ficticio. `check_number` conserva
las limitaciones conocidas de JUP-070 (por ejemplo cifras escritas con palabras).
El eco del prompt se informa como diagnóstico, no como prueba semántica autónoma.

| Estado | Significado |
| --- | --- |
| `pass` | Todas las cifras y todos los juicios requeridos pasan |
| `fail` | Existe un fallo conocido, incluso si quedan otros juicios pendientes |
| `blocked` | Error de infraestructura al recoger ese caso |
| `not_run` | Falta respuesta o faltan juicios, sin otro fallo ya comprobado |

`assessment_complete=false` conserva cualquier falta de juicio aunque el estado
sea `fail`. Se publican cuatro conteos y `pass/total`, con todos los casos en el
denominador. También se publica `pass/(pass+fail)`, con denominador explícito y
`null` si está vacío: incluye fallos conocidos con juicios pendientes y no mide
cobertura de revisión humana. No convertir `0/29` de una campaña sin juicios en tasa de error
semántico del modelo. Las parejas muestran resultados original/perturbado; no se
afirma regresión causal si el original ya falla o está pendiente.

Los informes sólo contienen IDs, hashes, estados, resultados por punto y versiones,
sin textos de respuestas ni nombres. No son el formato del calculador JUP-067:
los subgrupos propios no equivalen a su batería completa, sus métricas de relevancia
ni sus umbrales globales. Para aquellas métricas ejecutar JUP-070 con los 28 casos.

## Repeticiones y aceptación pendiente

Hacer al menos tres recogidas separadas con los mismos casos y configuración;
puntuar cada una conservando todas, incluidas las malas:

```sh
python tools/assistant-robustness.py compare ../evaluacion-jup071/report-1.json ../evaluacion-jup071/report-2.json ../evaluacion-jup071/report-3.json
```

`compare` rechaza distintos corpus/configuración, suite, versión del runner,
servicio local, Python, tipo de ejecución o provisionalidad y crudos duplicados.
Los hashes facilitan auditoría, pero no prueban independencia de una captura
manipulada: quien valida debe comprobar crudos y trazas.

`generative_robustness_accepted` permanece falso en todos los informes de esta
versión. Para una conclusión generativa faltan contraste de JUP-035 integrado,
evidencia del commit/modelo/prompt desplegado, tres recogidas reales iguales y los
juicios independientes. Entonces el equipo debe revisar explícitamente el contrato
de procedencia y la interpretación de resultados; no editar el booleano a mano.
La presente entrega completa el instrumento y su evaluación local acotada. No
declara la tarjeta aceptada, las revisiones humanas hechas ni robustez generativa.

## Cambios tras la revisión adversarial (13/10/2026)

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

Los valores declarados del bloque `run` se escriben en minúsculas, sin `:` ni `@`; un alias con sufijo de proveedor como `deepseek-v4-pro:free` hay que declararlo sin ese sufijo. Los alias de `infra/litellm/config.example.yaml` y de ADR-0002 se aceptan.
