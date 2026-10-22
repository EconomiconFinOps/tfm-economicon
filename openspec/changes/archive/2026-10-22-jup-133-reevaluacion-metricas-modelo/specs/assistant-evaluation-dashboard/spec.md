## ADDED Requirements

### Requirement: Identidad del modelo de generación en cada ejecución
La ejecución normalizada DEBE (SHALL) poder registrar, además del alias `generation_model` y del `commit`, cuatro campos opcionales: `generation_model_id` (identificador del modelo servido), `generation_provider` (proveedor que lo sirvió), `generation_quantization` (cuantización, por ejemplo `fp8`) y `gateway_config_sha256` (huella de la entrada del gateway que resuelve el alias, con su modelo, proveedor y parámetros). Un campo que el informe no trae DEBE (SHALL) guardarse como `null` y mostrarse como «no registrado»; nunca se rellena con un valor deducido. Los cuatro campos DEBEN (SHALL) existir en `rows-v1`, en la tabla `evaluation.runs` y en las tablas por ejecución del dashboard junto al alias.

#### Scenario: Ejecución con la identidad completa
- **WHEN** se normaliza un informe que trae los cuatro campos
- **THEN** la ejecución los conserva y el dashboard muestra modelo, proveedor y cuantización junto al alias

#### Scenario: Informe antiguo sin identidad
- **WHEN** se normaliza un informe que no trae ninguno de los cuatro campos
- **THEN** quedan en `null` y el dashboard muestra «no registrado» en cada uno
- **AND** la clave de comparabilidad de esa ejecución es la misma que antes de este cambio

#### Scenario: Campo con valor no válido
- **WHEN** `generation_quantization` es una cadena vacía, un número o una cadena de más de 80 caracteres, o `gateway_config_sha256` no es un sha256 hexadecimal de 64 minúsculas
- **THEN** la carga termina con un error que nombra el fichero y el campo, y no carga ninguna fila

#### Scenario: Fichero rows-v1 anterior a este cambio
- **WHEN** se carga un fichero `rows-v1` anterior a este cambio
- **THEN** sigue siendo válido sin los cuatro campos

### Requirement: Ejecuciones históricas rotuladas con su modelo por anotación del manifiesto
Una entrada del manifiesto DEBE (SHALL) poder llevar un objeto `model_identity` con las claves `generation_model_id`, `generation_provider`, `generation_quantization` y `gateway_config_sha256`, que rellena solo los campos que el informe no trae. La carga NO DEBE (SHALL NOT) modificar el informe original ni su huella. Si el informe y la anotación declaran valores distintos para el mismo campo, la carga DEBE (SHALL) terminar con un error que nombra los dos valores. Las ejecuciones de GLM-5.2 de `docs/validation/evaluation-runs.json` DEBEN (SHALL) quedar anotadas con su modelo, proveedor y cuantización cuando la evidencia del repositorio los acredita, y con `null` en lo que no se pueda acreditar.

#### Scenario: Informe histórico anotado
- **WHEN** una entrada del manifiesto anota `generation_model_id` para un informe de JUP-070 que no lo trae
- **THEN** la ejecución normalizada lleva ese valor
- **AND** `report_sha256` es el mismo que sin la anotación

#### Scenario: Anotación en conflicto con el informe
- **WHEN** el informe declara un proveedor y la anotación declara otro distinto
- **THEN** la carga falla con `error: <fichero>: <campo>: …` y no carga ninguna fila

#### Scenario: Clave desconocida en la anotación
- **WHEN** `model_identity` trae una clave que no es una de las cuatro
- **THEN** la carga falla nombrando la clave

#### Scenario: Valor no acreditable
- **WHEN** la evidencia del repositorio no acredita la cuantización de una ejecución antigua
- **THEN** la anotación no la inventa y el dashboard la muestra «no registrada»

## MODIFIED Requirements

### Requirement: Evolución entre ejecuciones comparables
El sistema DEBE (SHALL) mostrar la evolución de las métricas de la sección A solo entre ejecuciones comparables: misma fuente, misma huella de batería y de corpus, mismo proveedor y alias de embeddings, mismos parámetros de recuperación, mismo alias del modelo de generación, mismo identificador de modelo, mismo proveedor, misma cuantización y misma huella de la configuración del gateway cuando alguna ejecución los registra, mismo prompt cuando el informe lo registra y mismo tipo de ejecución. Dos ejecuciones con el mismo alias y distinta identidad de modelo NO DEBEN (SHALL NOT) formar una serie. Una ejecución que no registra la identidad y otra que sí la registra NO son comparables; dos que no la registran conservan la clave que tenían antes de este cambio. Cada cambio de batería, alias de modelo, identificador de modelo, proveedor, cuantización, configuración del gateway, prompt o corpus entre ejecuciones consecutivas de la misma fuente se marca con una anotación que nombra lo que cambió. Las métricas que dependen de juicio humano se muestran en series separadas que incluyen solo ejecuciones de hito.

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

#### Scenario: Mismo alias, distinto modelo
- **WHEN** dos ejecuciones de la misma fuente comparten `generation_model` `economicon-chat` pero difieren en `generation_model_id`
- **THEN** no forman una misma serie y la anotación de cambio nombra el identificador de modelo

#### Scenario: Mismo modelo, distinto proveedor o cuantización
- **WHEN** dos ejecuciones comparten alias e identificador de modelo pero difieren en `generation_provider` o en `generation_quantization`
- **THEN** no forman una misma serie y la anotación nombra el campo que cambió

#### Scenario: Identidad registrada frente a no registrada
- **WHEN** una ejecución trae la identidad del modelo y otra de la misma fuente y alias no la trae
- **THEN** no forman una misma serie y la anotación indica que una de las dos no registra el modelo

#### Scenario: Historial sin identidad intacto
- **WHEN** se cargan solo ejecuciones que no registran la identidad
- **THEN** sus claves de comparabilidad y sus series son idénticas a las anteriores a este cambio
