## ADDED Requirements

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
El panel de latencia p95 de la sección C DEBE (SHALL) indicar en su título y su descripción que agrega todas las rutas del backend y que no es la latencia de las consultas al asistente.

#### Scenario: Lectura del panel
- **WHEN** se lee el título del panel de latencia de la sección C
- **THEN** dice que son todas las rutas del backend

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
