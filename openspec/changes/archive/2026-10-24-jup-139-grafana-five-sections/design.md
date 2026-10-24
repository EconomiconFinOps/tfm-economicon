JUP: JUP-139
Trello: https://trello.com/c/npVVicNQ

# Diseño aprobado — cinco secciones y tres evoluciones

## Contexto y decisiones de alcance
Se conserva la arquitectura de ADR-0022: informes versionados cargados en PostgreSQL/evaluation mediante el loader existente; Grafana provisionado por Compose; Prometheus para señales en vivo. Este refinamiento no decide otra arquitectura ni requiere un ADR nuevo por defecto.

La base local observada el 23/10 contiene 13 ejecuciones y 665 filas; la campaña seleccionada del 21/10 tiene 7 favorables, 21 fallidos y 1 sin evaluar. El informe del 22/10 existe en Git pero no está cargado. Paris decide el 23/10/2026 usar los datos ya disponibles y actualizar las campañas después de publicar el dashboard; los originales pendientes no bloquean esta entrega. Se conserva la compatibilidad con el loader existente, sin incorporar ni reconstruir resultados nuevos. Cifras de partida fechadas, no contadores fijados en el dashboard nuevo.

## Composición vigente v6
1. Negocio y fiabilidad: tarjetas de precisión/cobertura, barras de eventos detectados/esperados, tabla de conciliación/frescura. Ejemplos de ahorro/tiempo sintéticos, si se conservan, en detalle identificado.
2. Calidad/robustez: cuatro tarjetas en fila, matrices por repetición del juez IA y del instrumento, hitos humanos y categorías. Detalle nativo con seis conjuntos completos: conducta, ausencias, cobertura, automático, humano y configuración.
3. Recuperación/citas: matriz de calibración, proporciones de recuperación vacía y contexto citado, cantidad/vecindad, consultas con recuperación sin citas, referencias válidas y citas literales. No equivaler uso observado del contexto a relevancia ni citas estructurales a exactitud.
4. Coste/rendimiento: tarjetas por campaña, contexto y tablas compactas, barras estimado/facturado y mediana/p95 por repetición compatible. La comparación fija de dos modelos conserva sus dos observaciones y sus límites; el histórico completo pasa al detalle. Mantener separados coste reportado y facturación, llamadas/intentos y consultas, muestras históricas de modelos y campaña seleccionada.
5. Salud técnica: series HTTP/errores, consultas e ingestas por minuto, vacíos/fallos de recuperación y alertas existentes. Desplegada por defecto, con el selector temporal global y detalle temporal compacto junto a alertas. Las cinco secciones siguen siendo plegables.

## Diseño visual
Reutilizar colores, tipografía, espaciado y jerarquía existentes. Título/pregunta, explicación breve, máximo cuatro tarjetas principales por bloque y diagnóstico desplegable. Las matrices conservan porcentaje/base y dirección frente a R1, sin promediar medidas ni afirmar causalidad. Las barras respetan bases y poblaciones; las dos observaciones históricas de modelos no sugieren tendencia. No añadir rótulos JUP/PR/SHA/agentes en la presentación.

## Fuentes y filtros
Inventario de métricas completo antes de diseñar consultas. Los controles de campaña/referencia sólo gobiernan paneles que realmente dependen de ellos. Referencias fijas y series vivas identificadas. Metadatos por fila: ejecución, fecha, batería, modelo conocido/declarado, unidad, estado, base y tipo de juicio. Ocultar identificadores técnicos de la portada sin perder la posibilidad de conciliar cada resultado.

## Datos y fallos
Sin filas/denominador cero: No medido, no cero supuesto. Se preservan pass/fail/blocked/not_run; cualquier agregado visual documenta su agrupación y permite ver el desglose. Sin pareja compatible no se infiere mejora. Conservar precisión original, intervalos aportados por el informe y ausencia de intervalos cuando no estén calculados.

## Entorno y revisión
Propuesta en un Grafana/PostgreSQL aislado con informes existentes, sin modificar el Grafana local compartido, ejecutar modelos ni tocar AWS. Evidencia: capturas de cinco secciones y vista completa para aprobación de Paris. Después de esa aprobación, cambio versionado y pruebas proporcionadas; Revisor/Validador independientes con controles PM originales; aprobación final/archivo/CI/reviews humanas y merge en sus etapas autorizadas.

## Antecedente de tres evoluciones — representación sustituida por v6
Los paneles originales 7/8/24 de Evaluación del asistente se reutilizan como 2101/2102/4101. Se conservan filtros de estado/unidad/etapa, identidad por clave de comparabilidad y filtro de hitos para judgment=human. Las etiquetas dicen juicio registrado como humano y no acreditan una nueva revisión humana. Las claves internas se conservan en datos y se presentan como cohortes diferenciadas. Las anotaciones de evaluation.config_changes sólo se vinculan a estas tres gráficas.

Las dos proporciones aparecen juntas al final de Calidad y robustez; la latencia de campaña aparece en Coste y rendimiento, en ms y separada de HTTP. Recorren todas las campañas cargadas con una ventana relativa propia de 30 días; Campaña/Referencia no las filtran. Cada observación válida aparece como punto. Sólo se unen puntos de la misma serie comparable; ausencia únicamente si no hay observaciones elegibles. En intervalos absolutos se aplica la ventana elegida por Grafana. La configuración temporal no modifica ni agrupa los informes.

La comparación existente por métrica se conserva (330), con referencia distinta, anterior y compatible. Los paneles de ingestas/consultas declaran Prometheus explícitamente; las alertas usan el listado nativo de Grafana. El detalle conserva run_id oculto y una etiqueta de ejecución con fecha UTC completa y registro distinto, unidad, estado, base, intervalo y origen del juicio. La campaña predeterminada se resuelve dinámicamente: última campaña de robustez cargada, incluidas las que carezcan de medidas; después banco de evaluación. No hay un run_id congelado en el selector.

## Antecedente de puntos del 23/10/2026 — representación sustituida por v6
Paris autoriza conservar cada observación aislada como punto y conectar únicamente las comparables. Las tres consultas leen evaluation.runs porque la vista comparable_runs también excluye ejecuciones sin pareja; la vista y los otros dos UID permanecen intactos. Un catálogo común de claves identifica la misma cohorte entre las tres gráficas; una clave nula/vacía se aísla por ejecución. La serie incluye métrica, variante, grupo, unidad y origen del juicio, y la transformación nativa particiona por esa identidad. Puntos siempre visibles, interpolación lineal sólo dentro de cada serie y sin puentear nulos. Sin fecha o valor no se inventa un punto: el registro sigue en Diagnóstico.

Datos ya cargados:196observaciones automáticas,28de juicio registrado sólo hitos y6de latencia; cada serie tiene una observación y no se conectan cohortes. Se conservan los casos SQL de un punto, dos compatibles, dos incompatibles, fecha/valor ausentes, hitos, unidades y tipos de juicio. No se simulan campañas en las capturas de resultados.

## Adaptación aprobada a las seis campañas existentes — 23/10/2026

Paris autoriza por coordinación PM a las19:31:44Atlantic/Canary adaptar esta composición a PR156, cargar únicamente el entorno local propio y evaluar de forma independiente el delta antes de mostrar resultados/capturas y subir nada. La base fue reconciliada por PM a db8f69ab5e2d4a42931cd6dc7412b99e855f0148. Esto sustituye la decisión previa de diferir exclusivamente esas seis campañas ya recogidas; no autoriza nuevas generaciones, gasto, importación del CSV financiero, archivo, commit/push/PR o retirada de dashboards. Los originales R1–R4 y sus dictámenes corresponden a sus candidatos históricos y se conservan sin extensión automática.

Se conserva la composición de cinco secciones,16tarjetas principales y tres evoluciones. La lectura visible de casos elige instrumento original o juez IA provisional cuando existe; no se rellenan filas humanas con IA. Cobertura mantiene respuestas previstas/disponibles/criterios y ausencia humana separadas. Las tablas traducen métricas/variantes y ocultan sus identificadores originales para conciliación. Los pares comparan grupo,identificador,variante,estado y unidad iguales, además de fuente/clave/orden temporal.

Coste reportado de completadas, gasto liquidado de todas las operaciones y factura histórica son poblaciones distintas. Las latencias distinguen terminal de todas las operaciones, terminal sólo completadas y etapa total histórica; ninguna sustituye generación o HTTP ni reconstruye etapas ausentes. Las series conservan esta población,el juicio y la cohorte; la igualdad de modelo declarado no conecta histórico. Los tiempos y costes permanecen medidas existentes,sin puntuación nueva.

Carga nativa local comprobada:19ejecuciones/1688resultados (18/1670versionados+suplemento histórico1/18). Snapshot13/665ySQLrecuperable conservados; aborto transaccional demuestra rollback íntegro antes de la carga efectiva; los13runs/665resultados previos permanecen exactos. No otras bases,modelos o gasto. El CSV1370es una instantánea y no se importa.


## Aplicación de v6 y conservación completa

La propuesta aprobada se traslada al UID de producto con título normal, edición
deshabilitada y sin el enlace temporal al original. Campaña/Lectura se resuelven
dinámicamente y Referencia comienza sin pareja; el selector Tiempos gobierna
exclusivamente barras y desglose. La tarjeta p95 terminal conserva su población
total y una definición visible, con base y fallidas explícitas.

Las nubes 2101/2102/4101 y el anillo 106 se consolidan, conservando cada registro en
las opciones locales 8301/8303. Las tablas de detalle empiezan por indicador,
valor y base; anchos acotados en 1280 y 2425 px e inspector nativo para el contexto
íntegro. Sus nombres de conjunto preceden a los encabezados del selector nativo.
Valores, intervalos, estados, originales de tiempo, identidades y tipos de cambio
se mantienen para conciliación. Configuración es un registro separado, no un juicio
humano ni un efecto causal. El diagnóstico global conserva todas las filas.

Salud conserva las señales originales, distinguiendo tasa no calculable por
base 0, cero observado, ausencia de serie y error. Una nota explica el contrato
general sin fijar a producción el diagnóstico temporal del prototipo. No se genera
tráfico para llenar paneles ni se mezclan PostgreSQL histórico y Prometheus vivo.

La corrección se verifica únicamente en contratos afectados. Los informes previos
se conservan y no se extienden por declaración del autor; revisión y validación
independientes identifican manifiesto fijo y originales PM propios de esta ronda.
