# Cinco secciones de Asistente y evidencia

JUP-139 · rama `feat/JUP-139-grafana-five-sections` · base `93624f77b2481d64ba40e95f211a9e53451f9e0e`.
Paris aprueba la propuesta visual v6 y autoriza su implementación el 23/10/2026.
La entrega local R8 fue aprobada por Paris el 24/10/2026; archivo y evaluación
del delta autorizados, publicación pendiente. Esta guía describe el diseño; resultados y límites están en la
[matriz](../evidence/JUP-139-validation.md). La aprobación visual no acepta por sí sola el producto.

Abrir el UID `economicon-assistant-evidence`, «Asistente y evidencia». Reúne las
medidas de los dashboards de evaluación y métricas técnicas. Los otros dos UID
permanecen intactos y disponibles; no se autoriza retirarlos. La cobertura de medidas
no replica todos los campos de auditoría de la vista anterior (versión de batería,
commit, proveedor/cuantización, indicador de hito y calibración elegida). Sus datos
siguen en PostgreSQL y en el dashboard original. El arranque continúa
mediante el provisioning de Compose, con PostgreSQL/evaluation y Prometheus existentes.

| Sección | Lectura y alcance |
| --- | --- |
| 1 · Negocio y fiabilidad | Cuatro tarjetas en una fila: precisión 5/5, cobertura total 5/7, detectable 5/5 y retraso 0 d del detector sintético. Eventos y conciliación/frescura por cliente/divisa en pareja. Referencia fija del 30/10; no beneficio empresarial observado. |
| 2 · Calidad y robustez | Campaña y modelo declarado, cuatro tarjetas, matrices de repeticiones compatibles para juez IA e instrumento, hitos humanos provisionales y categorías. El detalle conserva conducta, ausencias, cobertura, histórico automático, humano y configuración. |
| 3 · Recuperación y citas | Cuatro tarjetas de campaña y pareja calibración/documento-sección, con referencias fijas del 15/10 y 8/10 separadas. Dos opciones de detalle: Campaña y Calibración. Citas estructurales no acreditan calidad semántica global. |
| 4 · Coste y rendimiento | Contexto/fechas/método, cambios Antes/Ahora/Diferencia, desglose y cuatro tarjetas. Barras de mediana/p95 por repetición, factura de 75 consultas del 21–22/10 y comparación histórica de 84 respuestas por modelo del 16/10. Cuatro opciones de detalle: Gateway, Cambios, Tiempos e Histórico. |
| 5 · Salud técnica y diagnóstico | Cuatro estados/volúmenes, series HTTP/errores y volúmenes en pareja, alertas y detalle temporal compacto. Diagnóstico conserva todas las medidas y Procedencia todas las ejecuciones. Las cinco secciones se abren desplegadas y siguen siendo plegables. |

## Selectores y lectura de las tablas

Campaña elige dinámicamente la última robustez con fecha al abrir sin selección
previa. Lectura de casos distingue Instrumento original y Juez IA · provisional,
cuando existe. No toma resultados humanos o reglas como sustituto del juez ausente.
Referencia empieza sin pareja y exige otra ejecución anterior compatible.

Campaña/Referencia/Lectura sólo afectan a las consultas que los nombran. Tiempos
elige Todas las operaciones, Sólo completadas o Etapa total histórica para las
barras y el desglose; no altera la población de la tarjeta p95. Negocio, factura y
modelos mantienen sus referencias fijas. Las señales operativas usan el rango
global; los históricos de detalle conservan su ventana relativa de 30 días y el
filtro temporal nativo en rangos absolutos.

Los selectores al pie de las tablas son controles nativos de Grafana 11.3: sus
etiquetas empiezan por el conjunto y continúan con los encabezados. Una guía breve
identifica cada opción. Indicador aparece primero, seguido de Valor y Base; los
anchos permanecen acotados en escritorios normal y amplio. Para ver el contexto
íntegro, pulsar un indicador y su icono de inspección. El detalle comparado extenso
y el diagnóstico permiten desplazamiento horizontal; no se eliminan sus columnas.

## Calidad, repeticiones y juicio humano

R1/R2/R3 son repeticiones de la misma cohorte, ordenadas por fecha. Banco y
Robustez permanecen separados. La matriz muestra porcentaje y base de cada
medida, sin promediarlas. El color señala dirección frente a R1: favorable,
contraria, sin cambio o no medido; no aceptación ni causalidad.

La tercera robustez conserva juez IA 7/21/1 de 29 e instrumento 0/8/21 de 29;
completadas 28/29 mide operaciones, no aciertos. Puntos requeridos 37/54 y conducta
15/28 usan sus propias bases. Cobertura separa 28/29 previstas, 28/28 disponibles
y 144/144 criterios; no oculta la operación fallida. Modelo declarado no significa
modelo atestiguado. Humano no medido permanece ausente y no se sustituye por IA.

Los 310 registros automáticos, 28 humanos sólo hitos y 24 de latencia permanecen
accesibles en sus secciones mediante el detalle completo; se sustituyen las nubes
duplicadas, no los datos. Cohorte, variante, población, unidad, juicio y fecha
acompañan cada observación. Sin fecha/valor no se inventa una posición temporal.
Las cinco configuraciones conservan texto, tipos de cambio y fecha originales,
con ámbito público y advertencia de no causalidad; no son evaluaciones humanas.

## Coste, tiempo y ausencia de datos

Coste reportado por operación, total liquidado del gateway y factura son medidas
distintas. La factura fija cubre 75/75 consultas (73 Flash y 2 GLM); las tasas de
rechazo 429 y error 5xx usan 124 intentos, 0/124. No se suman consultas e intentos
ni se atribuye esta factura a las seis campañas nuevas.

p95 significa que aproximadamente el 95 % finaliza en ese tiempo o menos. La
tarjeta terminal de robustez muestra 62,96 s sobre 29 operaciones, incluidas las
fallidas: no es media ni tiempo puro del LLM. Si sólo existe la etapa histórica,
se declara ese alcance. Barras y desglose separan poblaciones: en el primer Banco,
p95 de todas las operaciones es 144,176595 s sobre 28 y sólo completadas es
92,600543 s sobre 27. Las barras usan segundos fijos; no se autoescalan a minutos.
Los originales en ms siguen disponibles para conciliación. No se inventan fases
de generación, embeddings, recuperación ni tiempos HTTP ausentes.

En Salud, un contador presente en cero no equivale a una serie ausente. Si la
base de consultas terminadas es cero, las tarjetas indican «Sin tasa · 0
terminadas»; no 0 %. Sin serie se indica «Sin serie disponible» y los errores
siguen siendo errores. Las dos consultas temporales originales permanecen en el
detalle compacto junto a las alertas; su vacío no se rellena con tráfico fabricado.

## Datos, pruebas y entrega

GENERAL reutiliza sus 19 ejecuciones/1688 resultados ya cargados: 18/1670 del
manifiesto y suplemento histórico 1/18. Esta implementación no recarga ese entorno,
ni ejecuta nuevas campañas, modelos, embeddings, importaciones financieras o gasto.
Las pruebas SQL usan PostgreSQL desechable propio y escenarios transaccionales con
ROLLBACK; no modifican GENERAL. Los estados Prometheus se comprueban con promtool
y series de prueba aisladas. No se repiten suites generales sin impacto.

Los originales R1–R7, los intentos desfavorables y la propuesta aprobada se conservan
externamente. Cada ronda independiente identifica el candidato exacto y nuevas
referencias originales del PM. Resultados y capturas normales/amplias se presentan
a Paris antes de subir nada. Una captura larga con zonas sin cargar no sustituye
el recorrido nativo de las cinco secciones. La lectura externa por una persona y
sus respuestas reales siguen siendo una comprobación humana, no una inferencia de CI.

Roles comunicados: Paris liderazgo, Alejandro pairing, Lucía revisión y Víctor
validación. La asignación no acredita participación. Archivo, Git de escritura,
publicación, reviews humanas y merge conservan sus etapas y permisos específicos.

## Cierre autorizado — 24/10/2026

Paris aprobó la entrega local R8 tras revisión y validación independientes y la
coordinación confirmó develop idéntico a la base. El [cambio archivado](../../openspec/changes/archive/2026-10-24-jup-139-grafana-five-sections/proposal.md)
y sus requisitos promovidos mantienen evidencia, límites y tareas realizadas.
La evaluación del delta documental y las etapas de publicación siguen separadas.
