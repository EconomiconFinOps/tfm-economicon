## ADDED Requirements

### Requirement: Frescura de los datos de coste
El sistema DEBE (SHALL) calcular la frescura como los días enteros entre la fecha de referencia configurada y el último día con datos de coste, por inquilino, y contar los días sin registro entre el primero y el último día con datos de cada inquilino. Un día sin registro NO DEBE (SHALL NOT) contarse como un día de coste cero.

#### Scenario: Datos al día
- **WHEN** el último día con datos es el día anterior a la fecha de referencia
- **THEN** la frescura es de 1 día y se informa como medida

#### Scenario: Datos atrasados
- **WHEN** el último día con datos es anterior en 5 días a la fecha de referencia
- **THEN** la frescura es de 5 días y el informe lo señala

#### Scenario: Sin datos
- **WHEN** el inquilino no tiene ningún registro de coste
- **THEN** la frescura es `not_measured`

### Requirement: Reconciliación con aritmética independiente
El sistema DEBE (SHALL) sumar el coste de la fuente (el CSV del generador de datos) con aritmética decimal exacta, sin usar el código de normalización del producto, y compararlo con el total que devuelve el API de resumen de costes para el mismo periodo, inquilino y divisa. La diferencia se informa como entero en unidades menores y la reconciliación es correcta solo si es exactamente cero. Cada divisa DEBE (SHALL) reconciliarse por separado y nunca se suman divisas.

#### Scenario: Totales iguales
- **WHEN** fuente y API suman lo mismo para una divisa
- **THEN** la diferencia es 0 y `reconciled` es verdadero

#### Scenario: Diferencia de un céntimo
- **WHEN** la fuente y el API difieren en una unidad menor
- **THEN** `reconciled` es falso y la diferencia aparece en el informe

#### Scenario: Dos divisas
- **WHEN** el periodo contiene EUR y USD
- **THEN** se informa una reconciliación por divisa y ninguna se compensa con la otra

#### Scenario: API no disponible
- **WHEN** la pila no está levantada o el API no responde
- **THEN** la reconciliación es `not_measured` y nunca se declara correcta

### Requirement: Salida de la medición de datos
El sistema DEBE (SHALL) emitir un informe `rows-v1` con fuente `JUP-130-data`, grupo `data_quality` y tipo B, con la fecha de referencia y el commit, y una tabla Markdown reproducible. DEBE (SHALL) declarar que la fuente es un conjunto sintético y que reconciliar contra el propio generador no demuestra la integridad de datos reales de Azure.

#### Scenario: Declaración de límites
- **WHEN** se lee la tabla de la memoria
- **THEN** indica la fuente, el periodo y lo que la reconciliación no demuestra
