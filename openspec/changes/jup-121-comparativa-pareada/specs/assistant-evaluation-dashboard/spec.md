## ADDED Requirements

### Requirement: Comparación local provisional separada de aceptación
El dashboard SHALL conservar la naturaleza provisional del informe JUP-063 y no
representar sus juicios como aceptación ni como checks automáticos de calidad.

#### Scenario: Proyección del informe pareado
- **WHEN** se carga un informe PAIRED_LOCAL_PROVISIONAL_COMPARISON con dos modelos
- **THEN** se generan una ejecución y 18 filas de grupo paired_local_provisional
- **AND** los tres juicios locales por modelo llevan judgment null
- **AND** no se emiten cases/pass ni ACC-1 ni se inventa adjudicación independiente

#### Scenario: Nulo fuera del grupo provisional
- **WHEN** una fila A ordinaria carece de judgment
- **THEN** se rechaza como antes sin ampliar la excepción a otros grupos o métricas

### Requirement: Fidelidad de cifras y unidades
La proyección SHALL conservar costes de fases USD, segundos de generación,
recuentos y metadatos no registrados del informe, sin transferir aceptación.

#### Scenario: Latencia o coste no medido
- **WHEN** un valor está ausente o es null
- **THEN** se muestra No medido y no se publica cero
- **AND** la observación del agregador no se usa como fecha de ejecución

#### Scenario: Informe incoherente
- **WHEN** los tamaños de modelos difieren o los recuentos no suman su total
- **THEN** se rechaza todo sin generar salida parcial

### Requirement: Carga acotada preserva ejecuciones existentes
El modo SQL preserve-existing SHALL modificar sólo la identidad del informe
pareado, de forma transaccional e idempotente, sin DDL, roles ni vaciado global.

#### Scenario: Segunda carga del mismo informe
- **WHEN** se aplica dos veces el mismo script sobre la base existente
- **THEN** el conjunto de datos no cambia y otras ejecuciones permanecen intactas

#### Scenario: Error o colisión de identidad
- **WHEN** falla una inserción o un run_id pertenece a otra huella completa
- **THEN** la transacción aborta y se conservan todas las filas anteriores
