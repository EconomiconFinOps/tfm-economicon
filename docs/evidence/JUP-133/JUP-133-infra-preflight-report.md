# JUP-133 — Preparación de tres repeticiones por campaña

Estado a 23/10/2026: **recogida no iniciada; admisión bloqueada por presupuesto**.
Este informe registra preparación y comprobaciones previas, no seis ejecuciones
del asistente. Ninguna campaña está aceptada. [Informe estructurado](JUP-133-infra-preflight-report.json).

## Alcance y autorización

- [JUP-133](https://trello.com/c/Yv1ETc2G): JUP-070, sección A, 28 preguntas × 3;
  JUP-071, 29 casos × 3. Total: 171 conversaciones independientes previstas.
- Rama `test/JUP-133-campanas-infra-tres-repeticiones`, creada desde
  `develop` `84b53b74d02ff5831ef9dbdd4f9c7d8c40cd4d24`; destino del PR: `develop`.
- El usuario autorizó expresamente el lanzamiento en este chat el 23/10,
  sustituyendo para este encargo la condición de confirmación de Lucía. No se
  atribuye esa autorización a Lucía.
- Después pidió sustituir 1,50 USD por el mínimo del colector: **tope total
  autorizado 6,50 USD**. El límite global de la demo sigue siendo 10 USD.
- No hay dos personas designadas para puntuar. Los resultados que lleguen a
  obtenerse serán provisionales y los juicios humanos permanecerán pendientes.
  No se han creado ni reutilizado juicios de agentes o de campañas anteriores.
- La carga en una base compartida requiere confirmación específica, todavía
  ausente. Esta preparación no cambia aplicaciones, claves, accesos ni cuotas
  del gateway.

## Bloqueo comprobado

`tools/assistant-eval.py` reserva 6,50 USD antes de cada operación nativa.
`tools/evaluation_budget.py` rechaza reservas de chat inferiores y no admite una
nueva operación cuando la suma del gasto y la reserva supera el tope. El contrato
está documentado en [Evaluación de índices](../../embedding-indexes.md#evaluación).

Una comprobación local sin red reprodujo `Campaign budget would be exceeded`
con el tope inicial de 1,50 USD; el ledger quedó sin operaciones y no se llamó al
chat. Tras la ampliación a 6,50 USD, la aritmética sigue bloqueando la admisión:
6,50 de reserva + ≈0,077 de consumo anterior = **≈6,577 USD**. La reserva es
preventiva, no una predicción del coste de una respuesta, y se necesita de nuevo
antes de cada operación.

Se ha propuesto **7,50 USD totales**, pendiente de autorización. El mero aumento
a 6,577 permitiría, aproximadamente, la primera operación; después habría que
sumar su consumo. No se ha elevado el presupuesto a la cifra propuesta ni se ha
reducido la protección del colector.

Antes de una recogida también debe quedar preparado el adaptador de liquidación:
el CLI nativo no proporciona el callback `account`. El colector exige recibos de
todos los intentos y embeddings, confirmación de operación terminada y captura
de la recuperación efectiva. El `usage` final y `/evidence` inicial no bastan;
un coste desconocido conserva la reserva y detiene nuevas admisiones. No se ha
probado aún ese recorrido en esta campaña.

## Configuración declarada y referencia de coste

Lectura del gateway de DockerDevelop, sin inferencia nueva:

| Campo | Valor declarado |
| --- | --- |
| Alias | `economicon-chat` |
| Modelo | `openrouter/deepseek/deepseek-v4.1-flash` |
| Proveedor / cuantización | `deepinfra` / `fp8` |
| Huella de la entrada | `9b345f3017a142d5f2db605a8921ec6fc488b2d97977edb069733aeee670c4f8` |
| Embeddings | `economicon-embedding` → `openrouter/openai/text-embedding-3-small` |
| ZDR / reintentos del router | configurado / 0 |
| Reserva de salida del runtime | 11.000 unidades; final de 10.000 según la versión congelada |

La huella se calculó en el servidor con JSON canónico, excluyendo `api_key`,
conforme al algoritmo de `gateway-config-hash.mjs`. Describe configuración;
**no verifica qué modelo respondió**, porque no se han recogido respuestas.

La referencia disponible son cinco operaciones del ensayo de DockerDevelop del
23/10: **0,0192297384 USD**, media **0,00384594768 USD** por operación, incluidos
los intentos y embeddings registrados por el gateway. Es atribución por ventanas
UTC y clave, sin conciliación con factura upstream; no es un piloto nuevo ni una
muestra cuya representatividad para las 171 preguntas esté demostrada.

| Campaña | Estimación por repetición a esa media | Tres repeticiones |
| --- | ---: | ---: |
| JUP-070 A, 28 casos | 0,10768653504 USD | 0,32305960512 USD |
| JUP-071, 29 casos | 0,11153248272 USD | 0,33459744816 USD |
| Total nuevo | — | 0,65765705328 USD |

Incluido el histórico aproximado del plan: **≈0,73465705328 USD**. Aplicar a las
171 muestras el máximo observado de aquella muestra daría 1,5302541024 USD
nuevos; tampoco es una cota máxima garantizada. Las cifras de la tabla son
proyecciones, **no costes medidos de las repeticiones nuevas**. Los 0,1215362872
USD históricos de la demo son otro ámbito y no sustituyen el acumulado del plan.

## Estado separado de cada repetición

| Campaña | Repetición | Casos previstos | Recogida | Coste medido | Juicios humanos |
| --- | ---: | ---: | --- | --- | --- |
| JUP-070 A | 1 | 28 | `not_run` | `not_measured` | `not_run` |
| JUP-070 A | 2 | 28 | `not_run` | `not_measured` | `not_run` |
| JUP-070 A | 3 | 28 | `not_run` | `not_measured` | `not_run` |
| JUP-071 | 1 | 29 | `not_run` | `not_measured` | `not_run` |
| JUP-071 | 2 | 29 | `not_run` | `not_measured` | `not_run` |
| JUP-071 | 3 | 29 | `not_run` | `not_measured` | `not_run` |

La admisión de los seis lotes está `blocked`; no se atribuye fallo al modelo.
La comparación de resultados está `not_measured`, no se han ejecutado los
scorers sobre respuestas inexistentes y no hay aceptación. Costes no medidos
se guardan como `null`, nunca como cero.

## Comprobaciones y carga

- `node tools/validation-questions.mjs validate`: 28 preguntas, 7 categorías,
  fuentes y rúbricas conformes. Esto valida las entradas, no las respuestas.
- `python tools/chat-eval-jup071.py --suite-root . prepare --repetitions 3`:
  plan de 87 muestras guardado, sin inferencia. Se comprobaron 29 muestras por
  repetición y los identificadores de las tres repeticiones.
- Dashboard existente `economicon-assistant-evaluation`, lectura por API como
  Viewer a las **13:20:02 UTC**: **20 consultas SQL HTTP 200, sin errores**;
  tres devolvieron cero filas. Esto acredita consultas del dashboard existente,
  no una revisión visual del navegador ni una carga nueva.
- La base de DockerDevelop conserva **17 ejecuciones y 765 resultados**. El
  manifiesto versionado tiene 12 ejecuciones; cargarlo sin preservar las
  incorporaciones locales retiraría esas ejecuciones de la proyección.
- Carga: **`not_run`**. `evaluation-runs.json` permanece intacto: añadir seis
  entradas ahora las presentaría indebidamente como ejecuciones nuevas. No hay
  `rows-v1` de respuestas no recogidas. DockerServer y las bases compartidas no
  se han modificado.

Cuando existan resultados: conservar las ejecuciones actuales, preparar el
manifiesto combinado y SQL de reemplazo con `evaluation-dashboard.py rows/sql`,
mostrar los recuentos y diferencias, y solicitar confirmación de la base concreta
antes de `load`. Después se comprobarán fecha/modelo y consultas de las nuevas
ejecuciones. No trasladar la comprobación actual a una futura carga.

## Ubicaciones y siguiente paso

Fuera de Git, respecto del workspace que contiene este checkout:
`materiales/07-evidencias/JUP-133-campanas-infra-20261023/` contiene
`jup070-inputs.json`, `jup071-plan.json`, `offline-admission-ledger.json`,
`preflight-report.json`, `dashboard-baseline.json` y los scripts de preparación.
Las futuras respuestas, fichas, hojas y juicios deberán permanecer fuera de Git.
Solo este informe y su resumen JSON se incorporan en `docs/evidence/JUP-133/`.

Pendiente: resolver el tope total para admitir reserva más gasto acumulado;
preparar y verificar la liquidación de todos los intentos y la extracción;
recoger, puntuar por separado y comparar las seis repeticiones sin fabricar
juicios; obtener autorización concreta de carga y comprobar el dashboard.

Origen: chat «Levantar Jupiter en dockerDevelop»,
`01a16421-03a0-7460-b110-24738407ccb1`. No se declara completada la campaña.
