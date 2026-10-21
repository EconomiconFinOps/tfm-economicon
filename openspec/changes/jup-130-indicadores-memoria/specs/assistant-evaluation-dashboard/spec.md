## ADDED Requirements

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
