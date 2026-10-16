## MODIFIED Requirements

### Requirement: Latencia del backend rotulada con su alcance
El panel de latencia p95 de la sección C DEBE (SHALL) indicar en su título que agrega todas las rutas y en su descripción que son las rutas del backend y que no es la latencia de las consultas al asistente.

#### Scenario: Lectura del panel
- **WHEN** se lee el título del panel de latencia de la sección C
- **THEN** dice «todas las rutas»
- **AND** su descripción dice que son las rutas del backend y que no es la latencia de las consultas al asistente

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
