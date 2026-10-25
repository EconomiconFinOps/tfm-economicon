# assistant-evaluation-composition Specification

## Purpose
Presentar las mediciones existentes del asistente en una composición narrativa de Grafana que conserve fuentes, cohortes, unidades, denominadores y ausencias, permita comparar sólo ejecuciones compatibles y separe evidencia técnica de lectura y aceptación humanas.
## Requirements
### Requirement: Composición narrativa nativa y lenguaje funcional
El sistema SHALL evolucionar la entrada Grafana existente a cinco secciones: negocio y fiabilidad de datos; calidad y robustez del asistente; recuperación documental y citas; coste y rendimiento del chat; salud técnica y operación. SHALL conservar los UID previos, el aspecto visual y los contratos de medición; las cinco secciones SHALL abrirse desplegadas y seguir siendo plegables. SHALL conservar identificadores internos para trazabilidad sin usarlos como rótulos de presentación.

#### Scenario: Lectura de principio a fin
- **WHEN** una persona abre la composición
- **THEN** ve el resultado de una única campaña, sus fallos y casos sin medir, y puede seguir las cuatro familias de evaluación y sus límites
- **AND** no ve identificadores JUP, PR, ramas, SHA o agentes en títulos, selector, textos o etiquetas de procedencia

#### Scenario: Lectura de cinco secciones
- **WHEN** una persona abre la composición
- **THEN** identifica las cinco preguntas y distingue resultados de campaña, referencias históricas y señales en vivo
- **AND** ve tarjetas compactas, matrices de repeticiones, hitos, cambios antes/ahora y barras o series cuando sus datos permiten esas representaciones, sin identificadores internos en los rótulos

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

### Requirement: Indicadores existentes con ejecución y unidad identificables
La composición SHALL mostrar los indicadores seleccionados de robustez, recuperación, citas, rendimiento y operación usando las definiciones existentes. El detalle SHALL identificar la ejecución, fecha, unidad, estado, base y origen del juicio de cada fila; SHALL conservar identidad conocida del modelo, intervalos existentes y ausencia explícita cuando no se registraron.

#### Scenario: Dos campañas de robustez cargadas
- **WHEN** existen varias ejecuciones de una misma fuente
- **THEN** los resultados de cada fila se atribuyen inequívocamente a su ejecución y unidad y no se suman campañas distintas
- **AND** los selectores sólo afectan a los paneles que declaran depender de ellos

#### Scenario: Citas correctas con resultado de caso desfavorable
- **WHEN** una campaña tiene referencias válidas o citas literales y casos fallidos
- **THEN** ambos resultados permanecen visibles, cada uno con su base
- **AND** los indicadores estructurales no se describen como calidad semántica global

### Requirement: Diseño aprobado y carga conciliada sin nuevas campañas
La entrega SHALL presentar primero capturas de la composición real en Grafana aislado para aprobación humana visual. SHALL usar los datos existentes ya cargados, conciliar las consultas con esos datos y conservar la compatibilidad con el mecanismo de carga existente. La actualización de las seis campañas ya recogidas e integradas en PR156 SHALL realizarse sólo en el entorno local autorizado, con el cargador existente y el suplemento histórico opcional conservado; SHALL conciliar el histórico por contenido y conservar una copia previa recuperable. Otras campañas SHALL quedar fuera de esta adaptación, sin reconstruir resultados ausentes. SHALL conservar el arranque mediante Compose general y los otros dos dashboards.

#### Scenario: Informe fuera del conjunto autorizado
- **WHEN** un informe fuera de las seis campañas autorizadas no aparece en la instancia
- **THEN** se registra su ausencia y se usa la información ya cargada para esta entrega; su actualización queda fuera del alcance actual
- **AND** no se ejecutan nuevas operaciones de evaluación ni se convierten resultados ausentes o fallidos en medidos favorables

#### Scenario: Propuesta visual antes de implementación
- **WHEN** está preparada la composición local
- **THEN** se muestran capturas de las cinco secciones y del conjunto a Paris antes de modificar el dashboard versionado
- **AND** se mantiene la separación entre aprobación visual, comprobación técnica y reviews humanas

### Requirement: Evoluciones existentes con comparabilidad y fuente explícitas
La composición SHALL conservar cada observación automática, el juicio registrado como humano sólo en hitos y la latencia mediana/p95 de campaña en los detalles de Calidad y Coste, con cohorte, medida, variante, unidad, fecha y tipo de juicio. SHALL sustituir las nubes duplicadas por matrices, hitos y barras de repeticiones de una misma cohorte/población, sin atribución causal. Los históricos completos SHALL conservar su alcance temporal propio y no depender de Campaña/Referencia; las barras SHALL declarar su campaña, población, segundos, fechas y bases. El registro de configuración SHALL conservar fecha, texto y tipos originales, accesibles en Calidad, sin crear un juicio humano.

#### Scenario: Histórico completo e hitos separados
- **WHEN** existen mediciones históricas con fecha y valor
- **THEN** cada observación permanece accesible en la tabla de su sección, con contexto íntegro inspeccionable y originales conciliables
- **AND** humano sólo incluye hitos medidos de ese origen y no acredita participación humana adicional
- **AND** sin fecha o valor el diagnóstico conserva el registro sin una posición temporal inventada

#### Scenario: Repeticiones de una misma cohorte
- **WHEN** se comparan R1/R2/R3 de una campaña
- **THEN** la matriz conserva proporción/base y dirección frente a R1, sin mezclar Banco con Robustez ni inferir aceptación o causalidad
- **AND** las barras separan todas las operaciones, sólo completadas y etapa histórica; muestran segundos y n de su población, nunca HTTP ni media como p95
- **AND** la ausencia de una medida permanece ausente y un cero medido sigue siendo cero

### Requirement: Evaluaciones provisionales y poblaciones separadas
La composición SHALL distinguir instrumento original, juez IA automático provisional y juicio humano registrado, sin reemplazar filas humanas no medidas ni equiparar criterios semánticos, casos y operaciones. SHALL traducir los identificadores internos para presentación y conservarlos ocultos para conciliación completa. SHALL mantener sus cinco secciones, acceso íntegro a los tres históricos, fuentes fijas y UID existentes.

#### Scenario: Respuestas disponibles revisadas y fallos técnicos
- **WHEN** existen resultados del juez IA y operaciones sin respuesta verificable
- **THEN** la lectura de casos identifica su origen y conserva pass/fail/blocked/not_run propios sin sumarlos con otro método
- **AND** la cobertura diferencia respuestas previstas, disponibles y criterios aplicables; una cobertura completa de disponibles no oculta fallos técnicos
- **AND** el humano no medido permanece no medido, no cero ni juicio IA atribuido a una persona

#### Scenario: Coste y latencia de ámbitos distintos
- **WHEN** hay coste reportado de completadas, gasto del gateway y latencias terminales
- **THEN** cada fila y serie conserva unidad, denominador y población: todas las operaciones, sólo completadas o etapa total histórica
- **AND** no se sustituyen factura histórica, tiempos de generación/HTTP o medidas ausentes con esos valores
- **AND** sólo se agrupan para comparación observaciones de la misma cohorte, medida, variante, población y origen del juicio

#### Scenario: Carga autorizada sin perder histórico
- **WHEN** se cargan los dieciocho informes versionados y el suplemento histórico opcional
- **THEN** se concilian diecinueve ejecuciones y1688resultados con las fuentes, incluidas las504filas IA, conservando exactamente las13ejecuciones/665filas previas
- **AND** la copia previa es recuperable y una transacción fallida no deja carga parcial
- **AND** el diagnóstico identifica todas las filas y oculta identificadores internos en la presentación, sin importar el CSV financiero ni ejecutar campañas

### Requirement: Detalle legible y ausencia operativa explícita
Las tablas SHALL conservar todas sus columnas con indicador, valor y base próximos, origen secundario acotado, guía del selector nativo e inspección del texto completo. SHALL distinguir en Salud contador presente en cero, tasa no calculable por denominador cero, ausencia de serie y error de origen, conservando las consultas temporales y las alertas existentes.

#### Scenario: Escritorios normal y amplio
- **WHEN** se lee la composición a 1280 y 2425 px
- **THEN** las tarjetas permanecen en filas, los gráficos útiles en pareja y los valores no se alejan del indicador por una columna de origen sobredimensionada
- **AND** todas las opciones de Calidad, Recuperación y Coste conservan datos, bases, unidades, estados e intervalos; el contexto extenso se abre con el inspector nativo

#### Scenario: Recuperación sin denominador o sin series
- **WHEN** los contadores presentes tienen cero consultas terminadas
- **THEN** se muestra tasa no calculable y no 0 %, manteniendo las consultas temporales originales
- **AND** si faltan series se indica ausencia; un error sigue siendo error, sin atribuir inactividad ni crear tráfico para rellenar datos

#### Scenario: Entorno existente de entrega
- **WHEN** GENERAL ya contiene 19 ejecuciones/1688 resultados
- **THEN** se reutiliza sin recargarlo; los ensayos SQL y Prometheus afectados usan recursos desechables propios
- **AND** se presentan resultados, informes independientes y capturas a Paris antes de subir, sin retirar dashboards ni heredar un dictamen anterior

