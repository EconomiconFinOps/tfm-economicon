# Review JUP-067

## Resumen

El change define como se miden las metricas tecnicas del asistente y entrega un calculador de referencia. Hay un catalogo versionado de 17 metricas en seis familias (exactitud, relevancia y confianza de la recuperacion, fundamento, latencia, robustez de la salida y disponibilidad), un formato de resultados por caso sin texto de preguntas, respuestas ni credenciales, y `tools/assistant-metrics.py`, que valida un fichero de resultados contra la bateria de JUP-069, las etiquetas de JUP-022 y el catalogo, y calcula cada metrica con la biblioteca estandar, sin red y de forma determinista. No cambia el backend, el processor ni el frontend.

## Decisiones

- Objetivos provisionales: se adoptan los de ADR-0002 como referencia, siempre junto al valor y con su origen, nunca como puerta de aceptacion ni veredicto (decision de Lucia, 2026-10-04).
- Puntos `required` (JUP-070): una persona en los casos no criticos y dos independientes en los criticos (los que tienen alguna cifra esperada: 14 de 28); cada comprobacion juzgada registra quien la decidio.
- Publicacion: los informes se generan por ejecucion y cada ejecucion real queda como foto fechada en la evidencia de la tarjeta que la haga; no hay pagina viva en `docs/`.
- Alcance acordado a partir de las notas de tutoria: se anaden la confianza de la recuperacion (REL-4), la disponibilidad del chat (AVL-1) y el tamano del corpus en los resultados. Quedan fuera, con su motivo en `design.md`, el juez basado en un modelo, ROUGE, BLEU y la similitud de embeddings de la respuesta (JUP-070), la trayectoria del agente (el chat no es agentico), la definicion de incidente y las metricas de negocio (JUP-068).
- El formato obliga a registrar una comprobacion por cada punto de la rubrica, distingue un fallo de proveedor (caso `blocked`, sin datos de respuesta) de un fallo de esquema (caso `fail` con una respuesta recibida), y trata una cifra sin rastro en un caso critico como un fallo de fundamento aunque cumpla la rubrica.
- Las tasas de citas, referencias de evidencia y confianza se calculan sobre los casos `answer`; las metricas de llamada (latencia, fallos por categoria) cuentan todas las llamadas intentadas, incluidas las de los casos `blocked`.

## Validacion

Comandos y resultados completos en [docs/evidence/JUP-067-validation.md](../../../docs/evidence/JUP-067-validation.md): 98 pruebas del calculador, 105 mutantes manuales detectados sin supervivientes, `openspec:validate` 45/45, trazabilidad, higiene, pruebas de gobernanza y CI correctas. El unico fallo de las pruebas de herramientas (`ports already published by this Compose project are not busy`, de JUP-050) es de la maquina de la autora, que tiene su propio stack en los puertos, y no de este change.

## Adversarial Review

Cinco pasadas del agente `adversarial-reviewer`, cada una sobre el head vigente y sin ver el razonamiento de la implementacion. Cada hallazgo BLOCKING o HIGH se reprodujo antes de arreglarlo, se arreglo con una prueba escrita antes del codigo y, cuando la prueba no distinguia el fallo, con un mutante que la hace fallar.

### Pass 1 - revise (2 HIGH, 5 MEDIUM, 3 LOW)

- HIGH: un caso critico con una cifra sin rastro podia quedar como `pass`; una llamada fallida con latencia entraba en los percentiles y en la tasa de fallos. Arreglados.
- MEDIUM y LOW: coherencia entre `blocked` y los agregados (se documento que las metricas de llamada cuentan los casos `blocked`), CLI con entradas hostiles (enteros enormes, anidamiento, rutas de salida), salida por tuberia en Windows, lista de campos permitidos y longitud del texto libre en lugar de un escaneo por nombre, hash de las definiciones del catalogo, escenario del percentil con su minimo, proveedor `mock` sin distinguir mayusculas y rangos de los parametros de recuperacion. Arreglados.

### Pass 2 - revise (1 BLOCKING, 2 HIGH)

- BLOCKING: un entero JSON enorme en un campo numerico lanzaba una traza. HIGH: un `pass` sin comprobaciones de la rubrica y parametros de recuperacion incoherentes. Arreglados junto con la coherencia entre `outcome`, fallos, `structured_ok` y latencias, mensajes de error acotados, argumentos de la CLI (`--generated-at`, rutas iguales, carpetas inexistentes) y la inyeccion de Markdown por `--generated-at`.

### Pass 3 - revise (1 HIGH, 5 MEDIUM)

- HIGH: una llamada fallida admitia citas, referencias de evidencia y fragmentos de una respuesta que no existio. Un fallo de proveedor es ahora siempre un caso `blocked` sin datos de respuesta, y un fallo de esquema un `fail`. Arreglados tambien la proteccion de la bateria, las etiquetas y el catalogo frente a `--output`, los formatos de la cabecera (commit, fecha, hashes, proveedor, alias), las tasas de answer, la cifra equivocada del ejemplo trabajado (con una prueba que la compara con el calculo) y los detalles cosmeticos del informe.

### Pass 4 - revise (1 HIGH, 4 MEDIUM)

- HIGH: un caso critico con todos los puntos de la rubrica cumplidos y una cifra inventada no se podia registrar. Ahora es un `fail` por fundamento. Arreglados tambien las citas repetidas (se cuentan), los ajustes de generacion a `null`, la latencia de las tres etapas en toda llamada completada y su suma, los rangos del backend (`top_k` de 1 a 20, distancia maxima en (0, 2]), los enlaces duros y el BOM, y seis huecos de pruebas detectados con mutantes.

### Pass 5 - revise (1 HIGH, 5 LOW)

- HIGH: un fallo de esquema (llamada completada) podia omitir sus latencias. Arreglado. Tambien se arreglaron la grafia de `rule` en una comprobacion juzgada, la fecha inexistente, el texto "sin umbral" cuando no hay distancia maxima y el texto desfasado de `design.md`.
- El revisor no encontro regresiones ni ninguna combinacion de reglas que impida representar un caso real valido: timeout tras recuperar fragmentos, fallo de esquema, `clarify` y `abstain` parciales, cobertura `none` y cifra sin rastro en un caso critico con la rubrica cumplida.

### Cierre

La revision adversarial se da por cerrada tras la quinta pasada con los hallazgos LOW siguientes aceptados explicitamente por Lucia (2026-10-04) y registrados en `openspec/findings/backlog.md` (RF-067-001 a RF-067-004):

| Hallazgo | Disposicion |
| --- | --- |
| Los valores de `alias`, `model_alias` y `heading` solo se filtran por longitud y alfabeto, no por contenido: una cadena con forma de clave de API cabria en un alias | Aceptado. El formato rechaza campos y textos largos, pero no inspecciona el significado de un valor corto. Quien produzca los resultados (JUP-070) no debe incluir credenciales. RF-067-001 |
| STR-2 da recuentos por categoria y no su proporcion sobre todos los fallos | Aceptado. Los recuentos permiten calcularla. RF-067-002 |
| El tamano del corpus se imprime en una linea tras la tabla de latencia, no pegado a cada fila | Aceptado. Aparece en la cabecera y bajo la tabla. RF-067-003 |
| Un `fail` por `schema_validation` puede traer checks en `pass` y citas o cifras de una respuesta que no se parseo | Aceptado. Es coherente con una respuesta recibida que no cumple el esquema. RF-067-004 |

Notas sin cambios, discutibles o dependientes de JUP-070: las comprobaciones `forbidden` se registran como decididas por regla aunque algunas conductas de la rubrica (por ejemplo, inventar una causa raiz) las juzgue una persona; no se cruzan las peticiones 5xx de la disponibilidad con los casos `blocked` porque el formato no los relaciona; `provider` y `alias` son los del embedding y la generacion va en `generation.model_alias`, y JUP-070 debe confirmar que el formato le basta.

## Barrido de patrones

- Reglas de validacion que obligan al productor a falsear un dato (hallazgos de las pasadas 1 y 4): se revisaron todas las reglas de `validate_case` buscando una combinacion valida que no se pueda representar; las sondas de la pasada 5 cubren los casos reales de los grupos `answer`, `clarify` y `abstain`.
- Excepciones no controladas en el CLI (pasadas 2 y 4): la lectura, el calculo y la escritura devuelven un error con codigo 2 y nunca una traza; hay pruebas para enteros enormes, anidamiento, JSON ilegible, rutas de salida y estructuras inesperadas.
- Comparaciones de cadenas sin normalizar (pasadas 1, 3 y 5): los decisores, la regla y el proveedor `mock` se comparan sin distinguir mayusculas ni espacios. Los identificadores de la bateria y de las etiquetas se comparan exactos a proposito.
- Poblaciones `answer` frente a todas (pasadas 3 y 4): ACC-1, ACC-2, REL-1 a REL-4, GRD-1 y GRD-3 usan los casos `answer`; GRD-2 usa todos los casos evaluados porque cuenta cifras inventadas en cualquier caso; las metricas de llamada usan todas las llamadas intentadas.

## Riesgos

- Los riesgos sobre el comportamiento del propio calculador estan cubiertos por pruebas y mutantes, no aceptados.
- Aceptado: el formato nace antes de la primera ejecucion real y puede quedarse corto; va versionado (`results_version`) y JUP-070 puede subirlo, con ejemplo y controles negativos.
- Aceptado: la muestra de la bateria es pequena (28 casos, 2 `abstain`), por lo que toda tasa se publica como `k de n` con intervalo de Wilson al 95 %.

## Findings registrados

RF-067-001 a RF-067-004 en `openspec/findings/backlog.md`, aceptados por Lucia arriba.

## ADR

No aplica: son definiciones de metricas y una herramienta de calculo, no una decision de arquitectura duradera. Se enlaza ADR-0002 como origen de los objetivos provisionales sin sustituirlo ni ratificarlo.

## Human Approval

- Change: jup-067-assistant-technical-metrics
- Approval type: post-review
- Decision: approved
- Approver: Lucia
- Date: 2026-10-04
- Adversarial review: accepted findings: RF-067-001, RF-067-002, RF-067-003 y RF-067-004 (LOW, pasada 5), aceptados por Lucia y registrados en `openspec/findings/backlog.md`
- Archive decision: archive
- Notes: aprobadas las definiciones de las metricas, el formato de resultados y el calculador, con los objetivos de ADR-0002 como referencia provisional y sin puerta de aceptacion. La revision de PR y la validacion funcional de otros miembros quedan en Trello y en el PR; no se ha ejecutado el asistente real (lo hara JUP-070).
