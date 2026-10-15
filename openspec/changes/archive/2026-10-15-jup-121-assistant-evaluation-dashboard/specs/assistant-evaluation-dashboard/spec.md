## Purpose

Reunir en un dashboard de Grafana versionado los resultados de las evaluaciones del asistente (calidad con rúbrica, métricas de negocio y señales en vivo) y su evolución, normalizados desde los informes existentes, sin presentar lo no medido como cero ni confundir ejecuciones de prueba con ejecuciones reales.

## ADDED Requirements

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
