# assistant-evaluation-composition Specification

## Purpose
Presentar las mediciones existentes del asistente en una composición narrativa de Grafana que conserve fuentes, cohortes, unidades, denominadores y ausencias, permita comparar sólo ejecuciones compatibles y separe evidencia técnica de lectura y aceptación humanas.
## Requirements
### Requirement: Composición narrativa nativa y lenguaje funcional
El sistema SHALL ofrecer una entrada de Grafana con resultado de una campaña, diagnóstico, recuperación/calibración, comparación histórica de modelos y secundarios plegables de coste, anomalías, datos, salud y detalle. SHALL conservar identificadores y contratos internos sin mostrarlos como rótulos de la presentación. Los UID previos SHALL seguir disponibles para auditoría y operación.

#### Scenario: Lectura de principio a fin
- **WHEN** una persona abre la composición
- **THEN** ve el resultado de una única campaña, sus fallos y casos sin medir, y puede seguir las cuatro familias de evaluación y sus límites
- **AND** no ve identificadores JUP, PR, ramas, SHA o agentes en títulos, selector, textos o etiquetas de procedencia

### Requirement: Datos existentes y ausencias explícitas
El sistema SHALL consultar mediciones existentes con su fuente, cohorte, fechas, unidades y denominadores. SHALL representar una ausencia como Sin datos o No medido, nunca como cero, y SHALL acotar cada agregado histórico a un solo informe.

#### Scenario: Manifiesto real sin campaña experimental
- **WHEN** sólo está cargado el manifiesto versionado de la base, sin la campaña experimental ni el suplemento de modelos
- **THEN** el selector no inventa esas ejecuciones y sus paneles no muestran las cifras del prototipo
- **AND** la recuperación histórica y los indicadores sintéticos conservan sus límites

#### Scenario: Proyección experimental separada
- **WHEN** se carga el informe experimental existente en un espacio de prueba separado
- **THEN** se conservan sus recuentos y denominadores y se identifica una repetición, una persona evaluadora y modelo sin verificar
- **AND** las perturbaciones no se suman como otra campaña ni las citas se presentan como éxito global

### Requirement: Comparación sin falsa mejora
El sistema SHALL permitir seleccionar campaña y referencia, exigir fechas ordenadas, misma fuente y misma clave de comparabilidad para comparar sus filas, y declarar la ausencia o incompatibilidad sin inferir mejora. SHALL mostrar sólo cambios observados de medidas existentes, sin puntuación compuesta, tendencia o superioridad estadística.

#### Scenario: Corpus o batería distintos
- **WHEN** la pareja cambia de clave de comparabilidad
- **THEN** aparece No comparable y no se muestra una mejora causal ni una diferencia entre esas filas

#### Scenario: Pareja compatible
- **WHEN** dos ejecuciones distintas tienen fechas ordenadas, fuente y clave iguales
- **THEN** el detalle muestra lado a lado las mismas medidas, unidades y estados, con igualdad exacta, aumento o disminución observados
- **AND** las ausencias siguen sin rellenarse con cero

### Requirement: Evidencia de lectura y trazabilidad
La entrega SHALL incluir guía, continuidad, capturas antes/después y matriz criterio/evidencia. La prueba de lectura SHALL registrar respuestas reales de una persona que no conocía el dashboard, o declarar ese criterio pendiente; una comprobación de agentes SHALL NOT atribuir participación humana.

#### Scenario: Lectura humana no realizada
- **WHEN** aún no se dispone de una persona externa
- **THEN** la matriz declara el criterio no validado y conserva el guion y siguiente acción para recoger evidencia

