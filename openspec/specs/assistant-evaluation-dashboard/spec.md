# assistant-evaluation-dashboard Specification

## Purpose
Reunir en un dashboard de Grafana versionado los resultados de las evaluaciones del asistente (calidad con rúbrica, métricas de negocio y señales en vivo) y su evolución, normalizados desde los informes existentes, sin presentar lo no medido como cero ni confundir ejecuciones de prueba con ejecuciones reales.
## Requirements
### Requirement: Normalización de los informes a filas planas
El sistema DEBE (SHALL) convertir cada informe de evaluación soportado en una ejecución con sus metadatos y en filas planas de resultado. Cada fila tiene fuente, grupo, conducta, estado, recuento, valor, denominador, unidad y tipo de medida (A o B). Los informes soportados son: informe JSON de JUP-070 (`report_version` 1), resultados del benchmark de JUP-078 (`schema_version` 1), calibración de JUP-022 (`schema_version` 1) e informe de `tools/business-metrics.mjs` de JUP-068 (`schema_version` 1). La conversión no recalcula métricas: copia los valores del informe.

#### Scenario: Informe de JUP-070
- **WHEN** se normaliza `docs/evidence/JUP-070-run-2-report.json`
- **THEN** la ejecución lleva commit, fecha, versión y huella de la batería, huella del corpus, proveedor y alias de embeddings, parámetros de recuperación y alias del modelo de generación del bloque `run`
- **AND** hay una fila por estado de `counts` (`pass`, `fail`, `blocked`, `not_run`) con su recuento y con `cases` como denominador
- **AND** hay una fila por métrica del catálogo de JUP-067 con `k`, `n`, `rate` e intervalo de confianza cuando el informe los trae, y una fila por etapa de latencia

#### Scenario: Benchmark de JUP-078
- **WHEN** se normaliza `docs/evidence/JUP-078-benchmark-results.json`
- **THEN** cada modelo produce una fila `pass` con `successful` y una fila `fail` con `cases - successful`, ambas con `cases` como denominador
- **AND** la puntuación media por palabras clave, la latencia p95 y el coste se guardan como valores con su unidad, sin texto de los casos

#### Scenario: Calibración de JUP-022
- **WHEN** se normaliza `docs/spikes/JUP-022-retrieval-calibration.json`
- **THEN** cada punto del barrido produce filas de acierto de documento, acierto de sección y resultado vacío, con su `top_k`, su `max_distance` y el número de casos como denominador
- **AND** se marca el candidato elegido en `selection`

#### Scenario: Informe de negocio de JUP-068
- **WHEN** se normaliza el informe que produce `tools/business-metrics.mjs report` a partir de `docs/validation/JUP-068-example.json`
- **THEN** los estados de tiempo ahorrado, el tiempo ahorrado, la cobertura de gasto asignado y el ahorro potencial se guardan como filas de tipo B con sus denominadores
- **AND** la procedencia `synthetic` del informe se conserva en la ejecución

#### Scenario: Informe no soportado o mal formado
- **WHEN** un informe tiene una versión de esquema desconocida o le falta un campo obligatorio de su formato
- **THEN** la normalización termina con error, nombra el fichero y el campo, y no carga ninguna fila de esa regeneración

### Requirement: Lo no medido nunca es cero
El sistema DEBE (SHALL) conservar como no medido todo valor que el informe no midió: `null`, métricas con `available` igual a `false`, casos `blocked` o `not_run` y metadatos ausentes. Ese valor no se guarda como 0 ni se dibuja como 0 % en ningún panel.

#### Scenario: Métrica no disponible
- **WHEN** una métrica de un informe de JUP-070 tiene `available` igual a `false` o `rate` igual a `null`
- **THEN** su fila guarda el valor como nulo con el estado `not_measured`
- **AND** el panel la muestra como «No medido» y no como 0 %

#### Scenario: Casos bloqueados o no ejecutados
- **WHEN** una ejecución tiene casos `blocked` o `not_run`
- **THEN** esos recuentos se muestran como estados propios junto a `pass` y `fail`
- **AND** no se suman a `fail` ni reducen la tasa a 0 %

#### Scenario: Metadato ausente
- **WHEN** un informe no trae commit, fecha o prompt (como el benchmark de JUP-078, que no trae commit ni fecha)
- **THEN** el metadato se guarda como nulo y se muestra «no registrado»
- **AND** ninguna herramienta lo rellena con un valor deducido

### Requirement: Tipo de ejecución visible
El sistema DEBE (SHALL) clasificar cada ejecución como real o no real, con los motivos `plantilla`, `doble`, `sintetica` o `sin_modelo_verificado`, y mostrarla de forma distinguible en cada panel que la incluya.

#### Scenario: Ejecución de plantilla
- **WHEN** el alias del modelo de generación de una ejecución de JUP-070 es `plantilla-sin-modelo`
- **THEN** la ejecución se clasifica como no real con el motivo `plantilla`

#### Scenario: Ejecución con dobles
- **WHEN** el proveedor o el alias de embeddings de una ejecución es `mock`
- **THEN** la ejecución se clasifica como no real con el motivo `doble`, además de cualquier otro motivo que le corresponda

#### Scenario: Ejecución sintética
- **WHEN** el informe declara `synthetic` igual a `true` o `provenance` igual a `synthetic`
- **THEN** la ejecución se clasifica como no real con el motivo `sintetica`

#### Scenario: Panel con ejecuciones mezcladas
- **WHEN** un panel muestra ejecuciones reales y no reales
- **THEN** las no reales se distinguen por rótulo y estilo y su motivo es visible en el panel o en su leyenda

### Requirement: Sin texto de preguntas ni de respuestas
El sistema DEBE (SHALL) guardar y mostrar solo cifras, estados, identificadores y metadatos. Ni la base del dashboard ni sus paneles contienen texto de preguntas, de respuestas, de fragmentos recuperados ni de juicios.

#### Scenario: Carga de informes
- **WHEN** se cargan los informes del manifiesto
- **THEN** ninguna columna de texto libre de la base contiene enunciados, respuestas, fragmentos o notas de revisores
- **AND** los identificadores de caso, como `JUP-069-024`, se pueden guardar

### Requirement: Recuentos conciliados con el informe original
El sistema DEBE (SHALL) garantizar que los recuentos y denominadores que muestra el dashboard coinciden con los del informe original de cada ejecución.

#### Scenario: Conciliación tras la carga
- **WHEN** se cargan los informes del manifiesto versionado y se consultan los recuentos con las mismas consultas que usan los paneles
- **THEN** para cada ejecución, cada recuento por estado y cada `k` y `n` por métrica coincide con el del informe original

### Requirement: Regeneración con un único comando
El sistema DEBE (SHALL) regenerar los datos del dashboard con un único comando documentado. El comando lee un manifiesto versionado con los informes de hito y, opcionalmente, manifiestos locales fuera de Git, y reemplaza los datos anteriores de forma atómica e idempotente.

#### Scenario: Regeneración repetida
- **WHEN** se ejecuta el comando dos veces seguidas con los mismos manifiestos
- **THEN** la base queda con el mismo número de ejecuciones y filas que tras la primera vez

#### Scenario: Ejecución local no versionada
- **WHEN** se pasa además un manifiesto local con una ejecución que no es de hito
- **THEN** la ejecución aparece en el dashboard marcada como no de hito
- **AND** el manifiesto versionado del repositorio no cambia

#### Scenario: Fallo a mitad de la carga
- **WHEN** la carga falla después de empezar
- **THEN** la base conserva los datos de la regeneración anterior completa

### Requirement: Dashboard con tipos de medida separados
El sistema DEBE (SHALL) provisionar desde ficheros versionados, sin pasos manuales, un dashboard con una sección por tipo de medida: A (calidad con rúbrica), B (métricas de negocio) y C (señales en vivo). Cada panel declara en su título o descripción su tipo, qué mide y qué no demuestra. La latencia y la disponibilidad de una campaña (A) nunca comparten panel con la latencia y la disponibilidad del tráfico real (C).

#### Scenario: Grafana arranca
- **WHEN** se levanta el entorno con `docker compose up` y se ejecuta el comando de regeneración
- **THEN** el dashboard y su datasource están disponibles sin configuración manual, junto al dashboard de métricas técnicas

#### Scenario: Descripción de cada panel
- **WHEN** se revisa cualquier panel del dashboard
- **THEN** indica si es de tipo A, B o C, qué mide y qué no demuestra

#### Scenario: Latencia de campaña y de tráfico real
- **WHEN** se revisan los paneles de latencia y de disponibilidad
- **THEN** ningún panel combina consultas a los resultados de campaña con consultas a las métricas en vivo

### Requirement: Estados con denominadores
El sistema DEBE (SHALL) mostrar cada resultado de la sección A y de la sección B con sus recuentos `pass`, `fail`, `blocked` y `not_run`, o con el numerador y el denominador de la métrica, y con la batería, la versión, el commit, el modelo y la fecha de la ejecución. Ningún resultado aparece solo como tasa.

#### Scenario: Resultado de una ejecución
- **WHEN** se consulta el resultado de una ejecución de JUP-070 en el dashboard
- **THEN** se ven los cuatro estados con sus recuentos y el total de casos, además de los metadatos de la ejecución

### Requirement: Evolución entre ejecuciones comparables
El sistema DEBE (SHALL) mostrar la evolución de las métricas de la sección A solo entre ejecuciones comparables: misma fuente, misma huella de batería y de corpus, mismo proveedor y alias de embeddings, mismos parámetros de recuperación, mismo modelo de generación, mismo prompt cuando el informe lo registra y mismo tipo de ejecución. Cada cambio de batería, modelo, prompt o corpus entre ejecuciones consecutivas de la misma fuente se marca con una anotación. Las métricas que dependen de juicio humano se muestran en series separadas que incluyen solo ejecuciones de hito.

#### Scenario: Una sola ejecución comparable
- **WHEN** una serie tiene una sola ejecución, o ninguna otra ejecución comparable
- **THEN** el panel de evolución muestra «Sin datos: no hay con qué comparar»
- **AND** no dibuja una línea ni un punto en 0 %

#### Scenario: Ejecuciones de JUP-070 con configuraciones distintas
- **WHEN** se cargan las ejecuciones 1 y 2 de JUP-070, que difieren en el proveedor de embeddings (`mock` frente a `litellm`) y en `max_distance`
- **THEN** no forman una misma serie y cada una muestra «Sin datos: no hay con qué comparar»

#### Scenario: Cambio de configuración
- **WHEN** dos ejecuciones consecutivas de la misma fuente difieren en la batería, el modelo, el prompt o el corpus
- **THEN** el dashboard muestra una anotación en la fecha de la segunda que nombra lo que cambió

#### Scenario: Prompt no registrado
- **WHEN** las ejecuciones no registran el prompt ni su huella
- **THEN** los metadatos muestran «prompt no registrado» y no se genera ninguna anotación de cambio de prompt

#### Scenario: Métrica con juicio humano
- **WHEN** una ejecución que no es de hito tiene métricas que dependen de juicio humano
- **THEN** esas métricas no aparecen en las series de juicio humano
- **AND** sus métricas automáticas sí aparecen en las series automáticas

### Requirement: Señales en vivo como síntomas
El sistema DEBE (SHALL) incluir una sección C, separada de A y B, con las señales que ya emite el sistema: consultas por minuto, latencia p95, tasa de error y proporción de búsquedas sin contexto y con fallo de recuperación sobre las consultas al asistente que terminaron (respondidas más fallidas por la recuperación). La sección se rotula como síntomas de salud y de falta de base, no como medida de acierto, y enlaza al dashboard de métricas técnicas.

#### Scenario: Proporción de búsquedas sin contexto
- **WHEN** el backend ha registrado consultas al asistente y búsquedas vacías en la ventana del panel
- **THEN** el panel muestra la proporción de búsquedas vacías sobre las consultas
- **AND** si no hubo consultas en la ventana, muestra «Sin datos» y no 0 %

#### Scenario: Rótulo de la sección
- **WHEN** se revisa la sección C
- **THEN** su rótulo indica que son síntomas y que no demuestran que las respuestas sean correctas

### Requirement: Contrato de entrada para la robustez
El sistema DEBE (SHALL) documentar el formato de filas planas como contrato versionado de entrada, de modo que un informe de robustez futuro (JUP-071) pueda cargarse sin cambiar el dashboard. La sección de robustez, por categoría y tipo de perturbación comparada con su caso base, existe en el dashboard y muestra «Sin datos» mientras no haya filas de robustez.

#### Scenario: Sin informes de robustez
- **WHEN** ningún manifiesto incluye resultados de robustez
- **THEN** los paneles de robustez muestran «Sin datos» y no 0 %

#### Scenario: Filas de robustez que siguen el contrato
- **WHEN** se carga un fichero de filas planas válido según el contrato con fuente de robustez
- **THEN** sus filas aparecen en los paneles de robustez sin modificar el dashboard

### Requirement: Acceso de Grafana de solo lectura
El sistema DEBE (SHALL) dar a Grafana acceso a los resultados solo con un rol de lectura limitado al esquema de evaluación. La credencial de ese rol se toma de una variable de entorno obligatoria y no se versiona.

#### Scenario: Grafana intenta escribir
- **WHEN** se intenta escribir en el esquema de evaluación o leer otro esquema con el rol de Grafana
- **THEN** PostgreSQL rechaza la operación

#### Scenario: Falta la credencial
- **WHEN** se arranca el entorno sin la variable de la contraseña del rol de lectura
- **THEN** Compose se niega a arrancar e indica qué variable falta, igual que con las demás credenciales obligatorias

### Requirement: Tasa de error distingue ausencia de errores de ausencia de tráfico
El panel «Tasa de error del backend» DEBE (SHALL) valer 0 cuando hay peticiones y ninguna termina en 5xx, y mostrar «Sin datos: no hubo peticiones» solo cuando no hay peticiones en la ventana.

#### Scenario: Tráfico sin errores 5xx
- **WHEN** el backend recibe peticiones y ninguna responde 5xx
- **THEN** el panel muestra 0 %
- **AND** no muestra «Sin datos»

#### Scenario: Sin tráfico
- **WHEN** no hay peticiones en la ventana
- **THEN** el panel muestra «Sin datos: no hubo peticiones»

### Requirement: Latencia del backend rotulada con su alcance
El panel de latencia p95 de la sección C DEBE (SHALL) indicar en su título que agrega todas las rutas y en su descripción que son las rutas del backend y que no es la latencia de las consultas al asistente.

#### Scenario: Lectura del panel
- **WHEN** se lee el título del panel de latencia de la sección C
- **THEN** dice «todas las rutas»
- **AND** su descripción dice que son las rutas del backend y que no es la latencia de las consultas al asistente

### Requirement: Resultados por métrica y ejecución
La sección A DEBE (SHALL) incluir una tabla con una fila por métrica y variante, con su nombre legible, y una columna por ejecución, sin repetir los metadatos de la ejecución en cada fila. Cuando exista, DEBE (SHALL) mostrar el intervalo de confianza del 95 % junto al valor. Lo no medido DEBE (SHALL) mostrarse como «No medido».

#### Scenario: Nombre legible
- **WHEN** se muestra una métrica del catálogo de JUP-067
- **THEN** la fila lleva su identificador y su nombre (por ejemplo «ACC-1 · Casos con resultado pass»)
- **AND** toda métrica del catálogo tiene nombre

#### Scenario: Una columna por ejecución
- **WHEN** hay dos ejecuciones de JUP-070 cargadas
- **THEN** la tabla tiene una columna por ejecución y una fila por métrica y variante

#### Scenario: Intervalo de confianza
- **WHEN** una métrica tiene límite inferior y superior del intervalo
- **THEN** la celda muestra el valor, el numerador y el denominador y el intervalo
- **AND** una métrica sin intervalo no muestra uno inventado

#### Scenario: Métrica no medida
- **WHEN** una métrica no se midió en una ejecución
- **THEN** su celda dice «No medido» y no 0 %

### Requirement: Resumen de la última campaña
La sección A DEBE (SHALL) empezar con un resumen de la última campaña de JUP-070: fecha, tipo de ejecución, casos aprobados sobre el total y si existe alguna ejecución con modelo real.

#### Scenario: Solo ejecuciones de plantilla
- **WHEN** todas las ejecuciones de JUP-070 cargadas son no reales
- **THEN** el resumen dice que la última campaña es no real y que todavía no hay evaluación con modelo real
- **AND** muestra los casos aprobados sobre el total

#### Scenario: Sin ejecuciones
- **WHEN** no hay ninguna ejecución de JUP-070 cargada
- **THEN** el resumen dice «Sin datos» y no una campaña a 0

### Requirement: Etiquetas con un solo sentido
Las tablas DEBEN (SHALL) llamar «Tipo de ejecución» a la clasificación real o no real, no mostrar una columna de resultado cuando todas las filas están medidas y mostrar las variantes en español.

#### Scenario: Tipo de ejecución
- **WHEN** se abre cualquier tabla de resultados
- **THEN** la clasificación real o no real se llama «Tipo de ejecución»
- **AND** «Estado» solo designa el estado de los casos

### Requirement: Unidades legibles en la sección B
La sección B DEBE (SHALL) mostrar numerador y denominador con la misma unidad que el valor (minutos, euros), no en milisegundos ni en céntimos.

#### Scenario: Tiempo ahorrado
- **WHEN** se muestra un tiempo en milisegundos
- **THEN** el valor y su numerador salen en minutos

### Requirement: Latencia de la campaña en la evolución automática
El dashboard DEBE (SHALL) incluir un panel de evolución de la latencia de la campaña (mediana y percentil 95 de la etapa total) separado de las proporciones, con las mismas reglas de comparabilidad.

#### Scenario: Una sola ejecución comparable
- **WHEN** la latencia de la campaña solo tiene un punto en una serie
- **THEN** el panel dice «Sin datos: no hay con qué comparar» y no dibuja línea

#### Scenario: Dos ejecuciones comparables
- **WHEN** una serie de latencia tiene dos puntos medidos
- **THEN** se dibuja en milisegundos, discontinua si la ejecución no es real

### Requirement: Cifras calculadas y no mostradas documentadas
La guía del dashboard DEBE (SHALL) listar las cifras que se calculan o que no se cargan y no se muestran, con el motivo de cada una.

#### Scenario: Apartado de la guía
- **WHEN** se lee `docs/validation/evaluation-dashboard.md`
- **THEN** existe un apartado «Calculado y no mostrado» con el motivo de cada cifra omitida

### Requirement: Anotaciones de cambio de configuración en todas las evoluciones
La capa «Cambios de configuración» DEBE (SHALL) aplicarse a todas las gráficas de evolución de la sección A, incluida la evolución de la latencia de la campaña, y a ningún otro panel.

#### Scenario: Evolución de la latencia con un cambio de batería
- **WHEN** dos pares de ejecuciones comparables de la misma fuente tienen entre sí un cambio de batería
- **THEN** la evolución de la latencia de la campaña muestra la marca vertical del cambio
- **AND** las otras evoluciones siguen mostrándola

#### Scenario: Otros paneles
- **WHEN** se inspecciona el filtro de la capa de anotaciones
- **THEN** solo incluye las gráficas de evolución

### Requirement: Estado de los casos solo de las campañas de JUP-070
El panel «Estado de los casos por ejecución» DEBE (SHALL) mostrar únicamente ejecuciones de JUP-070.

#### Scenario: Ejecución de otra fuente con recuentos de casos
- **WHEN** hay una ejecución de otra fuente con filas de recuento de casos
- **THEN** el panel no la muestra
- **AND** las campañas de JUP-070 siguen apareciendo con sus recuentos y denominador

### Requirement: Contrato de clasificación para nuevas fuentes
La guía DEBE (SHALL) indicar a las fuentes futuras qué filas marcar como juicio humano o automático y qué grupos no reutilizar.

#### Scenario: Fuente con proporciones derivadas del resultado de un caso
- **WHEN** una fuente emite una proporción que sale del resultado de un caso
- **THEN** la guía exige marcarla como juicio humano para que no entre en la evolución de métricas automáticas

#### Scenario: Grupos de JUP-070
- **WHEN** una fuente nueva elige sus grupos
- **THEN** la guía le pide no reutilizar los de las familias de JUP-070

### Requirement: Orden de lectura de la sección A
La sección A DEBE (SHALL) mostrar el resumen, las ejecuciones, el estado de los casos, la tabla por métrica y ejecución y las evoluciones antes que la calibración, el benchmark y la robustez, y dejar al final las tablas por fila de detalle.

#### Scenario: Evoluciones tras la matriz
- **WHEN** se lee la sección A de arriba abajo
- **THEN** las gráficas de evolución están justo detrás de la tabla por métrica y ejecución

#### Scenario: Detalle al final
- **WHEN** se llega al final de la sección A
- **THEN** las tablas por fila de exactitud y de latencia están después de la robustez

### Requirement: Títulos de la sección C que no se cortan
Los paneles de un tercio de ancho de la sección C DEBEN (SHALL) llevar un título de 40 caracteres como máximo y el título de la latencia DEBE (SHALL) conservar «todas las rutas».

#### Scenario: Título de la latencia
- **WHEN** se lee el título de la latencia p95
- **THEN** mide 40 caracteres o menos y dice «todas las rutas»

### Requirement: Fecha sin ambigüedad en la tabla por métrica y ejecución
Las columnas de la tabla por métrica y ejecución DEBEN (SHALL) rotularse con la fecha en formato año-mes-día y hora, igual que el resto de tablas.

#### Scenario: Cabecera de columna
- **WHEN** se muestra una ejecución del 8 de octubre de 2026 a las 20:13 UTC
- **THEN** su columna empieza por `2026-10-08 20:13`

### Requirement: Paneles de los indicadores de la memoria
El sistema DEBE (SHALL) incluir en el dashboard de evaluación un panel por cada indicador de JUP-130 (calidad de la detección de anomalías, coste de IA y calidad de datos), con su tipo, «Mide:» y «No demuestra:», un solo datasource y las reglas de lo no medido ya vigentes. Los paneles NO DEBEN (SHALL NOT) mezclar filas de otras fuentes en sus series ni reutilizar los grupos de JUP-070.

#### Scenario: Descripción del panel
- **WHEN** se revisa cualquiera de los tres paneles
- **THEN** indica su tipo, qué mide y qué no demuestra, y pasa las pruebas estructurales del dashboard

#### Scenario: Indicador no medido
- **WHEN** un indicador carece de medición (por ejemplo, el coste de IA sin gateway)
- **THEN** su panel muestra «Sin datos» o «No medido» y no 0

#### Scenario: Fuente ajena
- **WHEN** existen filas de otra fuente con la misma métrica
- **THEN** cada panel de JUP-130 solo muestra las filas de su propia fuente (`JUP-130-anomalies`, `JUP-130-ai-cost` o `JUP-130-data`)

#### Scenario: Panel de negocio de JUP-068
- **WHEN** se cargan las ejecuciones de coste de IA y de datos, que son de tipo B
- **THEN** el panel «Tiempo, asignación y ahorro» sigue mostrando solo las ejecuciones de JUP-068

#### Scenario: Tres indicadores, tres fuentes
- **WHEN** se cargan los tres informes de JUP-130
- **THEN** el dashboard no anota cambios de configuración entre ellos ni los agrupa como una serie comparable

### Requirement: Carga de los indicadores con el comando existente
El sistema DEBE (SHALL) cargar los informes de JUP-130 con el comando `evaluation-dashboard:load` sin pasos manuales nuevos: los informes se listan en el manifiesto versionado y se validan con el contrato `rows-v1`. Tras levantar la pila y ejecutar ese comando, los paneles DEBEN (SHALL) mostrar los datos de la última medición versionada.

#### Scenario: Pila nueva
- **WHEN** se levanta la pila con `docker compose up` y se ejecuta `evaluation-dashboard:load`
- **THEN** al abrir Grafana los tres paneles muestran los datos de los informes versionados, comprobado en el navegador

#### Scenario: Informe inválido
- **WHEN** un informe de JUP-130 incumple el contrato `rows-v1`
- **THEN** la carga se detiene indicando el campo y no deja datos a medias

#### Scenario: Carga repetida
- **WHEN** se ejecuta la carga dos veces seguidas
- **THEN** los paneles muestran lo mismo
