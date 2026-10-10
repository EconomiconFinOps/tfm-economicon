## ADDED Requirements

### Requirement: Clasificación verificable

El panel SHALL permitir combinar filtros por tipo y dificultad y ordenar las
recomendaciones, preservando desconocido como distinto de cero o dificultad baja.

#### Scenario: Filtros combinados y recuperación

- **WHEN** el ingeniero combina tipo y dificultad sin coincidencias
- **THEN** ve un estado vacío, exportación deshabilitada y una acción para restablecer filtros

#### Scenario: Ordenación monetaria

- **WHEN** ordena por ahorro
- **THEN** el orden compara importes de la misma moneda y base temporal sin convertir monedas ni tratar datos ausentes como cero

### Requirement: Evidencia y límites del ahorro

El panel SHALL mostrar la acción, justificación, evidencia y necesidad de
aprobación humana sin atribuir ahorro realizado ni ejecutar cambios de nube.

#### Scenario: Recomendación sin estimación

- **WHEN** JUP-033 devuelve coste observado y ahorro nulo
- **THEN** el detalle mantiene el coste observado separado y muestra ahorro no estimado

#### Scenario: Informe de impacto

- **WHEN** existe un informe JUP-034 compatible para la recomendación
- **THEN** muestra su ahorro mensual/anual, moneda, mes base y exclusiones sin recalcular impacto o solapamientos

### Requirement: Procedencia explícita

El panel SHALL distinguir los dobles de demostración de una consulta de cliente;
los errores y ausencia de datos no SHALL sustituirse silenciosamente por demo.

#### Scenario: Datos de muestra

- **WHEN** el usuario abre la demostración
- **THEN** ve que los datos son simulados e independientes del cliente seleccionado

#### Scenario: Fuente no disponible

- **WHEN** una consulta no puede obtener datos válidos
- **THEN** presenta un estado de error o no disponibilidad sin inventar recomendaciones

### Requirement: Exportación coherente y accesible

El panel SHALL exportar únicamente la selección visible con procedencia,
unidades y valores seguros, y SHALL permitir operar sus controles con teclado.

#### Scenario: Vista filtrada

- **WHEN** el usuario exporta tras filtrar
- **THEN** el archivo contiene las mismas recomendaciones visibles con el mismo significado de ahorro, desconocidos y dificultad

#### Scenario: Texto externo

- **WHEN** una acción contiene delimitadores, saltos de línea o sintaxis de fórmula
- **THEN** se exporta como texto sin generar HTML ejecutable ni fórmulas de hoja de cálculo
