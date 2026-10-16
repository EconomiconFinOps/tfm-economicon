## ADDED Requirements

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
