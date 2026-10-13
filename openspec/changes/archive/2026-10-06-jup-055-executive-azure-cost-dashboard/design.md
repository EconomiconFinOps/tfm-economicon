# Diseño JUP-055: panel ejecutivo de costes almacenados

## Contexto y límites

Contexto externo verificado suministrado por el Coordinador el 06/10/2026;
inspección local sobre `048837278bb063d6ee3abafcdb0b71c51b560f94`.
JUP-026 está integrado: `GET /billing/summary` v2 devuelve periodo UTC,
totales y grupos por moneda como cadenas de dos decimales, recuentos y
omisiones. `monthly_spend` es el total del intervalo para una sola moneda,
no una serie. `savings_identified` es null.

No se requiere acceso directo a Azure: el panel muestra registros normalizados
almacenados, que pueden proceder del simulador. No certifica que estén todos
los cargos de Azure ni transforma ausencia en cero. Se conservan el contrato,
la autorización y la política conservadora de solapamiento
[ADR-0010](../../../../docs/adr/ADR-0010-azure-cost-source-overlap.md).
No se propone ADR nuevo, dependencia ni decisión transversal.

Responsabilidades humanas recibidas: Paris Arcos Martin (líder), Victor Mendez
(pairing), Alejandro Aguado (revisión), Lucia Mateo (validación). Esta asignación
no prueba participación ni sustituye sus futuras actuaciones.

## Selección de meses y consultas

Dos controles de mes, con etiquetas «Mes inicial» y «Mes final», expresan meses
inclusivos `YYYY-MM`. Aceptar meses de año 0001 a 9998 para que el límite
exclusivo sea representable; rechazar vacío, formato/calendario inválido y
inicio posterior al fin antes de consultar. Aceptar un mes, cruces de año,
meses en curso y futuros: no truncar a seis ni al calendario actual. Las
etiquetas identifican meses en curso/futuros, sin proyección.

El valor inicial se calcula en UTC: los seis meses completos inmediatamente
anteriores al mes actual. Con reloj octubre de 2026: abril–septiembre de 2026.
Construir límites sin depender del huso local ni de la interpretación local
de Date; contemplar el tratamiento especial de años 0–99 en JavaScript.

Febrero–agosto de 2026 implica consulta total
`[2026-02-01, 2026-09-01)` y siete consultas mensuales consecutivas.
Marzo–junio implica cuatro puntos. Enumerar exactamente un mes por entrada,
incluso si está vacío o falla. La agrupación y clave de tag son comunes a todas
las peticiones. Se ofrecen solamente subscription, resource_group, service,
project y tag; tag requiere clave no vacía. No duplicar en JavaScript el
algoritmo Unicode de canonicalización del backend: enviar la clave seleccionada,
mostrar la canónica devuelta por la respuesta total y comprobar que las
respuestas mensuales tengan esa misma clave canónica. Para otra agrupación,
omitir tag_key de las peticiones y de la identidad efectiva de consulta.

Una consulta agregada obtiene el total/desglose del periodo y una por mes
obtiene puntos y extremos. Si el intervalo tiene un mes, reutilizar la respuesta
total: una sola petición. No sumar totales mensuales redondeados ni grupos para
reemplazar el total agregado. El backend suma Decimal antes de redondear cada
consulta: meses o grupos pueden diferir unos céntimos del total. Explicarlo junto
a la serie/desglose; no redistribuir el residual.

## Organización técnica y aislamiento

Mantener `useCostKpis` para consumidores existentes; añadir un hook ejecutivo
pequeño que use `fetchBillingSummary`, `isBillingSummary` y React Query.
Utilidades puras separan enumeración/límites, importes y comparación para que
los tests observen reglas de negocio. No modificar backend ni API pública.

La clave del conjunto incluye namespace ejecutivo, versión 2, tenant activo,
generación de sesión, límites de todo el intervalo, group_by y tag solicitado
efectivo. Nunca incluye el token. La sesión existente limpia/cancela cache;
el conjunto consume el AbortSignal de Query y los servicios conservan sus
guardas de generación. Desmontar/cambiar ámbito aborta peticiones iniciadas y
no inicia pendientes. Usar un máximo de **tres peticiones simultáneas**,
incluyendo el total, que se inicia primero. No imponer un máximo de meses:
el intervalo amplio tarda más, mantiene indicador de carga y puede cancelarse.

Cada ejecución construye un conjunto nuevo; no completa sus huecos con respuestas
de otra ejecución. Comprobar en cada respuesta fechas solicitadas, UTC,
group_by y compatibilidad de tag canónico; una discrepancia es error de esa
consulta, aunque el guard de estructura pase. Clasificar fallos por consulta
sin convertirlos en cero. Una cancelación no se registra como error mensual
visible. Evitar reintentos automáticos de conjuntos parciales y de errores
409/422: botón «Reintentar» vuelve a obtener **todo** el conjunto bajo la misma
selección, con el mismo límite de concurrencia.

No usar placeholderData de otra selección. Durante cualquier carga/refetch,
ocultar importes y comparaciones anteriores, mantener los controles y anunciar
«Cargando costes»; cache no implica actualidad. Mostrar valores solo cuando
el conjunto actual termina y sus metadatos corresponden a la selección activa.
Las respuestas tardías de otro tenant, periodo, agrupación o generación no
cambian la pantalla. Sin token/tenant o selección inválida no hay peticiones.

El contrato no incluye revisión común ni snapshot entre peticiones. La coherencia
garantizada es de selección, ámbito y ejecución, no transacción entre meses:
una ingesta concurrente puede cambiar valores durante la carga. La interfaz
declara que son consultas de registros almacenados y permite recargar. No
certificar conciliación exacta entre meses y total ni implementar infraestructura
de snapshot; sería ampliación de contrato.

## Importes, monedas y comparación

Totales y tabla muestran todas las monedas separadamente. Para tendencia y
comparación, un selector de moneda toma la unión de monedas presentes en la
respuesta total y en respuestas mensuales válidas. Retener la moneda elegida
si sigue presente; si no, escoger primera moneda con orden determinista.
No convertir, sumar monedas, ni obtener moneda del alias nullable `currency`.
Si no existe moneda observada, no inventar una ni un KPI.

Interpretar cadenas de dos decimales mediante céntimos BigInt. La presentación
monetaria conserva su precisión, signo y código de moneda, incluso por encima
de Number.MAX_SAFE_INTEGER; no usar Number/parseFloat para sumas, resta,
porcentaje o importes exactos.


Para cada moneda, la comparación usa el **primer y último mes con coste
registrado distinto de cero dentro del intervalo**, en orden cronológico.
Esta regla sustituye operativamente a los extremos seleccionados y a la
comparación con base cero de la primera versión aprobada. Las aprobaciones
anteriores permanecen históricas, sin modificación.

Recorrido lineal de las posiciones mensuales existentes, sin mutarlas:
- Un punto exitoso con coste exacto no null y céntimos BigInt distintos de cero
  es elegible, incluidos créditos negativos y cantidades no dibujables.
- Un resultado exitoso sin moneda o con coste cero no es elegible. Sigue
  apareciendo en su posición de serie/tabla; cero registrado sigue siendo cero.
- Retener primer y último elegibles, su número, índices/meses efectivos y
  posición de errores. No elegir usando value de Recharts: null puede ser un
  coste grande válido. No añadir consultas ni ordenar una serie ya cronológica.
- Diferencia = último elegible menos primero elegible; porcentaje = diferencia /
  primero elegible × 100. La base elegible es no cero por construcción.
  Conservar dinero exacto, redondeo porcentual entero/racional a dos decimales,
  mitades alejadas de cero y ausencia de -0,00 %. No reinterpretar créditos.

Dos o más elegibles: retornar meses efectivos junto con diferencia/porcentaje
y límites observados. La página usa esos meses para la etiqueta de comparación,
nunca los controles de rango como sustituto; el rango completo permanece
identificado en la selección/totales/desglose. Ejemplo enero–diciembre con datos
solo marzo–agosto: doce posiciones y comparación agosto frente a marzo.
Febrero100, marzo90, junio300, agosto150 sigue dando +50.00 EUR / +50.00%
si febrero/agosto son primer/último elegibles. Base negativa -100→-50 conserva
+50.00 EUR / -50.00%, con aviso de base negativa; no se deduce ahorro.

Con resultados mensuales conocidos y un elegible: «Solo hay un mes con coste
para comparar», sin resta/porcentaje. Con ninguno: «No hay meses con coste
en este periodo», también si hay registros cuyo coste es todo cero. Se trata
de costes de los registros consultados, no garantía de cobertura Azure completa.
Sin una moneda observada no inventar una moneda o KPI. Un único mes seleccionado
puede dar uno o ninguno de estos estados según su coste observado.

Honestidad ante errores/metadata incompatibles:
- Error antes del primer o después del último elegible impide determinar los
  extremos; no mostrar variación numérica. Identificar el mes/causa y explicar
  la imposibilidad de determinar meses con coste. No saltarlo como ausencia.
- Si hay menos de dos elegibles y cualquier error, no afirmar uno/ninguno:
  el error podría ocultar un mes con coste. Mostrar la limitación, sin cifras.
- Error estrictamente entre dos elegibles ya establecidos no cambia su
  posición de extremos: cálculo observado permitido con aviso explícito
  de errores interiores, manteniendo gap y causa en la tabla mensual.
- Datos exitosos partial pueden aportar costes elegibles, manteniendo
  advertencia de parcialidad de los meses/resultados observados; no afirmar
  completo. Una respuesta inválida continúa siendo error, nunca partial/empty.
- Agregado fallido sigue ocultando resultados como antes. Sesión/carga/refetch
  conservan sus reglas de aislamiento; no se modifica hook ni backend.

La utilidad actual compareEndpoints concentra elegibilidad, extremos efectivos
y estado de comparación; puede conservar su nombre interno. Extender su
resultado disponible con firstMonth/lastMonth y la limitación de error interior;
el porcentaje disponible ya no tiene una base cero elegible. Estado no disponible
con reason distingue uno/ninguno de incertidumbre por error.
Página consume ese resultado sin repetir selección de extremos. No modifica
el array completo de MonthlyCostPoint empleado por tabla/Recharts.
Mantener máximo tres solicitudes, política de cohortes, metadata y monedas.
Complejidad O(N) y estado de selección acotado; reutilizar primitives existentes.


Recharts necesita Number: convertir únicamente para representación, cuando
los céntimos se puedan representar como entero seguro. Para valores fuera del
límite, no dibujar ese punto y explicar la limitación; la tabla accesible y
tooltip de los puntos dibujados mantienen los importes exactos. No truncar
ni limitar un coste para hacerlo caber en la gráfica. Las líneas no conectan
huecos por ausencia, error o representación; valores negativos son dibujables.

## Estados y calidad de datos

- Sin ámbito: guía de selección, sin datos previos.
- Entrada inválida: motivo junto a controles, sin consulta.
- Carga/refetch: mensaje anunciado y sin cantidades antiguas.
- Fallo de consulta total: no presentar totales, desglose, serie ni comparación
  como resultado válido; conservar mensajes y reintento. No recuperar total
  sumando meses exitosos.
- Total válido con fallo mensual: total y desglose disponibles, serie con meses
  fallidos explícitos; cálculo de extremos solo bajo las reglas anteriores.
- `409 ambiguous_cost_source`: advertencia específica de posible solapamiento,
  sin importes para la consulta afectada ni acción de reemplazo/confirmación.
  Un 409 mensual es error de ese mes; no significa cero.
- 401: usar invalidación existente; no repetir consultas pendientes de esa sesión.
  403, 422, 5xx/red y respuesta inválida conservan error, sin fallback demo.
- Sin registros: mensaje «Sin datos»; no importe cero inventado.
- Registros cero: mostrar 0.00 y recuento, distintos de ausencia.
- Partial: respetar `data_status`, `missing_dimension_count` y
  `excluded_undated_count`. Grupos null muestran «Sin dimensión» y, donde
  corresponda, «Sin suscripción». No inferir nombres de servicios/unidades.
  El recuento de indatados es global del tenant y puede repetirse por mes:
  no sumar estos recuentos para inventar una cifra del intervalo.

No hay promesa de cobertura temporal completa por recibir status available.
Un grupo project/tag es la dimensión almacenada, no una unidad organizativa
inferida. «Ahorro potencial: no disponible» continúa explícito; no calcularlo
a partir de la diferencia entre meses.

## Inventario visual y composición

Reutilizar el armazón de navegación y sesión actual, `MetricCard` (label,
value, detail, tone), `SectionCard` y Recharts. `StatusPill` tiene un estilo
sano único: reservarlo para identidad/estado apropiado existente; no usarlo para
errores o «completo». Las alertas conservan los patrones de texto/semántica de
estado ya usados en la página.

Inventario local: primitivos ui de label/select/separator/dialog/tooltip; no
hay primitive button/input/slider. Reutilizar los que encajen y los patrones
nativos de input/select/button ya existentes, sin instalar componentes ni
inventar slider. Citar y cumplir
[ADR-0003](../../../../docs/adr/ADR-0003-frontend-typescript.md),
[ADR-0004](../../../../docs/adr/ADR-0004-frontend-shadcn-ui.md) y
[ADR-0012](../../../../docs/adr/ADR-0012-frontend-color-tokens.md).
Verificar nombres de enlaces antes de la entrega.

Composición refinada: cabecera actual; controles de meses/agrupación/tag y avisos; SectionCard de desglose del intervalo; tarjetas de total y variación; SectionCard de tendencia por moneda y tabla exacta accesible por mes.
Conservar tipografía, jerarquía, `rounded-lg`, bordes, degradado card/accent,
sombras, espaciado y patrón de iconos ya presentes. No rediseñar Layout.

Colores solo de `styles/theme.css`; ejes y series de tokens existentes y
`components/chartTheme.ts` para tooltip. Una selección no crea nueva paleta ni
tonos dinámicos. MetricCard usa tono neutro para variación firmada. Conservar
focus visible, labels asociados, uso por teclado y mensajes aria-live; tabla
con caption/headers y alternativa al gráfico. No depender solo del color.

Probar escritorio 1440×900 y móvil 390×844, sin desbordamiento de página;
la tabla puede desplazarse dentro de su contenedor. Capturas muestran normal,
carga, vacío, error/parcial, selección y foco. Comparar con referencia del mismo
runtime y datos donde corresponda: deben coincidir armazón y lenguaje visual;
las diferencias de contenido previstas por JUP-055 se documentan. No afirmar
igualdad de píxeles de contenidos demo y datos nuevos.

## Alternativas y riesgos

No usar solo seis meses fijos: incumple el intervalo arbitrario. No usar
`monthly_spend` como serie, meses consecutivos como base comparativa, ni sumas
de meses para el total. Añadir endpoint serie/snapshot sería eficiente para
intervalos enormes, pero amplía backend/contrato y no es necesario para el TFM.
Elegir consultas existentes con cola de tres es verificable y proporcional.

No transformar null en cero; no conectar huecos para sugerir una trayectoria
continua. Retirar inventario/exportación demo evita exhibir métricas sin contrato,
sin abrir el alcance de exportaciones. README mínimo necesita coordinación con
JUP-104/JUP-105. Los costes de intervalos grandes y la falta de snapshot común
son límites explícitos; si se pide resolverlos con backend, volver a diseño.

## Criterios oficiales y evidencia prevista

| Criterio Trello recibido | Escenarios y tareas | Evidencia futura |
| --- | --- | --- |
| Resultado funcional | Todos los escenarios de executive-cost-dashboard; tareas 2–4 | Red/Green; ejecución independiente de rangos, monedas, extremos, aislamiento y estados |
| Tests en verde | Casos funcionales, errores y regresión; tareas 2, 3, 5 | Comandos/resultados por revisión, checks aplicables y mutantes clasificados |
| Docs/decisiones actualizadas | README y este diseño, ADR existentes; tareas 4, 5 | Instrucciones reproducibles y enlaces comprobados; sin ADR nuevo |
| PR revisada y enlazada | Tarea 6 | PR autorizada a develop, enlace Trello autorizado, review humana titulada y evidencia de pairing real |
| Validación funcional/evidencia enlazada | Tareas 5, 6 | Informe independiente por criterio, caso límite, capturas y review humana Validacion JUP-055 |

Criterios de PR y validación son puertas futuras, no resultados de diseño.
Proceso de reviews: dos personas asignadas, dos reviews separadas; a develop,
la primera satisfecha es Comment y la segunda Approve cuando ambas están
satisfechas. Ningún agente reemplaza participación humana.

## Red, Green, mutación y validación

Red debe fallar por comportamiento ausente con producto intacto: rango inclusivo
siete/cuatro meses, defecto primero–último, defecto precisión/monedas, huecos,
exclusión de cero para extremos, cancelación y concurrencia. Reutilizar pruebas JUP-026 para costes,
cinco agrupaciones, null, créditos, estados y legado. Solo corregir sus
expectativas de controles demo/días que el nuevo alcance sustituye explícitamente;
no debilitar pruebas de contratos ni aislamiento.

Green implementa producto sin modificar tests aprobados. Ejecutar tests
frontend, typecheck, lint/build y regresiones/workspace que exijan CI y
descubrimiento vigente; el Coordinador reconciliará la matriz exacta antes
del encargo. Mutación cubre límites UTC, último elegible no cero, signo/base,
cero/ausencia, moneda, clave tenant/generación, rechazo de metadatos,
concurrencia/cancelación y conexión de huecos. Usar herramienta existente
compatible en copia desechable, sin alterar producto final ni instalar runner;
si no existe, presentar excepción concreta al Coordinador, sin darla por aprobada.

Revisor inspecciona código/tests/docs; Validador ejecuta instrucciones por
criterio y un caso límite/error, incluyendo pruebas visuales reales.
No confundir tests de componente con validación navegador ni con revisión humana.

## Estado del diseño

Las aprobaciones históricas se conservan en proposal.md. El criterio no cero está aprobado por Paris; esta revisión técnica se presenta a su gate antes de nuevos Red/Green/docs/datos.
Solo comprobaciones documentales están permitidas en esta fase. El informe de
handoff registrará comandos y resultados reales, sin declarar Green ni aceptación.


## Refinamiento de composición y datos de comprobación — 06/10/2026

Paris solicita que «Desglose del periodo» sea el primer bloque de resultados
debajo de la selección de meses/agrupación. El cambio aproxima el resultado de
«Agrupar por» a su control: no añade un filtro ni cambia su significado.
Los totales, tendencia y comparación continúan cubriendo todos los registros
del tenant y periodo, separados por moneda. Se conserva la identidad de
consultas y la agrupación común de las peticiones según el contrato vigente;
no se optimiza ni cambia la red en este refinamiento.

Orden de lectura y disposición: cabecera; controles y sus ayudas/avisos;
estados anunciados y advertencias aplicables; desglose del periodo; totales;
comparación; tendencia con su selector de moneda y tabla mensual; explicaciones
del origen. Los avisos pueden preceder al desglose para no ocultar carga,
error o parcialidad. En un resultado válido el desglose será el primer bloque
de resultados, antes de cualquier total, comparación o tendencia, tanto en
el DOM accesible como visualmente. No simular el orden solo con CSS.
Se mueve una sola instancia del SectionCard existente con toda su tabla,
caption, moneda, recuentos, etiquetas null y aviso de redondeo. Conservar
las condiciones actuales: agregado fallido/carga no muestran datos previos,
y sin totales no aparece una tabla vacía inventada.

Alternativas: mantener el desglose al pie requiere buscar el efecto del selector;
duplicarlo crea dos resultados equivalentes y repite lectura; filtrar las
tarjetas/tendencia alteraría el alcance. Mover el bloque existente es suficiente
y no añade controles, estilos, contratos, dependencias o arquitectura.

### Datos sintéticos propuestos, versión 2

Preparar tras aprobación y despacho separado una versión de referencia externa
al repositorio sobre la base desechable exclusiva. Conservar los archivos
originales de referencia/seed y sus hashes, exportar el estado previo y registrar
la nueva versión, fecha, filas e identidad del runtime. No aplicar datos en esta
fase ni reutilizar capturas/resultados de la versión anterior como vigentes.

Preservar USD y tenant-growth sin cambios. Repartir cada fila EUR de tenant-core
entre sub-jup055-a y una nueva sub-jup055-c. Mantener un único run completado
por suscripción: el existente de core-a conserva sus 8 filas EUR y 3 USD;
el nuevo core-c contiene 8 filas EUR; growth mantiene sus 2 filas. Resultado
previsto: 21 registros y 3 runs completados en 2 tenants. Todas las fechas son
el día 15 de su mes de 2026. No crear un segundo run completado para core-a
con las mismas fechas. Distintas suscripciones pueden compartir fecha.
IDs/hashes de las filas nuevas serán únicos y estables; no duplicar filas al
repetir una carga. Una precondición incumplida detiene la preparación, no limpia
otros datos ni modifica otros stacks.

En la tabla siguiente cada entrada de dimensión sigue servicio / proyecto.
Las filas A usan rg-jup055-finance y las C rg-jup055-platform. Los tags
organization repiten el proyecto de su fila y environment=test. Los nombres
son sintéticos, no alias atribuidos a Azure.

| Mes | EUR original | A: coste / servicio / proyecto | C: coste / servicio / proyecto |
| --- | ---: | --- | --- |
| febrero | 100.00 | 60.00 / Compute / Finance | 40.00 / Storage / Platform |
| marzo | 90.00 | 30.00 / Storage / Finance | 60.00 / Compute / Platform |
| abril | 0.00 | 0.00 / Compute / Platform | 0.00 / Storage / Finance |
| mayo | 40.00 | 10.00 / Storage / Platform | 30.00 / Compute / Finance |
| junio | 300.00 | 200.00 / Compute / Finance | 100.00 / Storage / Platform |
| julio | -20.00 | -5.00 / Storage / Finance | -15.00 / Compute / Platform |
| agosto | 150.00 | 120.00 / Compute / Platform | 30.00 / Storage / Finance |
| septiembre | -50.00 | -20.00 / Storage / Platform | -30.00 / Compute / Finance |

Referencias manuales de febrero–agosto, únicamente EUR:
- Total: 100 + 90 + 0 + 40 + 300 - 20 + 150 = 660.00; 14 registros.
- Suscripción: A = 60 + 30 + 0 + 10 + 200 - 5 + 120 = 415.00;
  C = 40 + 60 + 0 + 30 + 100 - 15 + 30 = 245.00; 7 registros cada una.
- Grupo de recursos: rg-jup055-finance/A = 415.00 y
  rg-jup055-platform/C = 245.00; 7 registros cada uno, ámbito conservado.
- Servicio: Compute = 60 + 60 + 0 + 30 + 200 - 15 + 120 = 455.00;
  Storage = 40 + 30 + 0 + 10 + 100 - 5 + 30 = 205.00; 7 cada uno.
- Proyecto: Finance = 60 + 30 + 0 + 30 + 200 - 5 + 30 = 345.00;
  Platform = 40 + 60 + 0 + 10 + 100 - 15 + 120 = 315.00; 7 cada uno.
- Tag organization: Finance = 345.00 y Platform = 315.00 EUR;
  environment=test = 660.00 EUR. No sumar USD de la misma etiqueta.
- Serie EUR conserva 100, 90, 0, 40, 300, -20, 150; extremos agosto
  frente a febrero conservan +50.00 EUR y +50.00 %. Marzo–junio total
  430.00, variación +210.00 / +233.33 %; abril–mayo solo mayo con coste;
  julio–septiembre conserva -30.00 / +150.00 % con base negativa.

USD permanece en core-a: febrero 10.01, agosto 15.02 y septiembre
9007199254740993.01, servicio Storage, proyecto TFM, rg-validation;
tag organization=Platform. Febrero–agosto total USD 25.03 separado de EUR;
los meses intermedios mantienen huecos. El extremo septiembre queda identificable
para la prueba de precisión y omisión gráfica. Growth conserva febrero
999.00 y agosto 1999.00 EUR, total 2998.00 y delta +1000.00, sin contaminación
de core. Los recuentos de core EUR cambian deliberadamente (dos filas por mes),
pero los costes y comparaciones no. No afirmar igualdad de recuentos históricos.

El seed SQL original es la fuente para las columnas persistidas: project=TFM
y resource_group=rg-validation. El último campo de las tuplas JSON originales
(Finance/Platform/Growth) coincide con organization, no con project. La versión
2 usará columnas nombradas para evitar confundir tag con proyecto. Referencias
esperadas se escriben por aritmética explícita de estas filas, sin importar
utilidades del producto ni usar respuestas API/UI como oráculo.

### Pruebas proporcionadas y evidencia afectada

Red: un caso observable de orden accesible del selector, caption del desglose,
totales, comparación y tendencia; más un recorrido de cambio servicio→proyecto
con grupos diferentes y cantidades idénticas en total/serie/comparación. Usar
la prueba de agrupación existente si basta y fortalecerla en rutas asignadas;
no snapshots de JSX ni assertions de clases/índices que copien estructura
interna. Producto actual debe fallar por orden del resultado, no por entorno.
No duplicar la batería de lógica monetaria ya cubierta.

Green: mover el bloque sin tocar hook, dinero o contratos, conservando avisos
y gating. Ejecutar casos afectados, suite frontend, tipos, lint y build según
matriz del Coordinador. Comprobar sensibilidad del caso de orden en copia
desechable mediante recolocación al pie; reutilizar la excepción manual solo
si el Coordinador confirma que cubre esta fase. No instalar runner.

Preparación de datos separada: comprobar precondiciones de la DB desechable,
guardar copia/consulta de referencia v1, aplicar únicamente las filas EUR
asignadas y el run C en una transacción, comprobar 21 filas, 3 runs,
identidad de tenants/subs, importes y ausencia de fuentes solapadas;
guardar fixture v2 y SQL exacto externamente. Obtener respuesta API real para
los grupos y contrastarla con los importes anteriores como evidencia observada,
no como fuente de los esperados. Ninguna consulta de cambio se ejecuta ahora.

Validador tras la entrega: en tenant-core y febrero–agosto EUR recorrer
suscripción, grupo de recursos, servicio, proyecto y tag; capturar el control
con su desglose cercano y verificar filas/importes contra v2, mientras total
660.00, serie y +50.00/+50.00 % permanecen iguales. Probar USD, mes cero,
crédito, ausencia y cambio a growth; comprobar que carga/error no dejan tabla
vieja y que el orden de lectura conserva avisos. Documentar dataset versión,
viewport y revisión de código en cada evidencia. Repetir revisión técnica y
validación afectadas; el informe anterior queda histórico.

Este refinamiento no resuelve ni rebaja el criterio móvil original: el
Validador observó overflow del Layout compartido también en rutas vecinas.
Reparación del Layout y proxy de latencia siguen fuera del despacho, pendientes
de decisión del Coordinador/Paris. Sesión/latencia/metadatos y otras áreas
NOT_VALIDATED del informe anterior continúan pendientes, aunque las pruebas
de implementación aporten evidencia complementaria. No declarar JUP cerrada.

| Solicitud de Paris | Escenarios delta | Tareas | Evidencia prevista |
| --- | --- | --- | --- |
| Desglose junto al selector | Breakdown follows selection; Grouping preserves financial scope | 7.1–7.3 | Red/Green del orden y cambio de grupos; captura/lectura accesible |
| Datos EUR con dimensiones distintas | Grouping preserves financial scope | 7.4–7.6 | Fixture v2 con sumas independientes; SQL/DB/API real y captura por agrupación |
| Conservar finanzas/aislamiento | Reutilizar escenarios existentes de meses, monedas, cero, crédito y scope | 7.3, 7.6 | Regresión y validación afectada, referencias v2 e historial v1 separado |



## Comparación por meses con coste no cero — revisión de 06/10/2026

Criterio expresamente aprobado por Paris y transmitido por el Coordinador a
las 10:54:35; despacho analysis-design comparison-design-1 a las 11:00:05.
El diseño técnico validado se presenta para su siguiente gate antes de código.
Este apartado y la sección de importes/spec son operativos: sustituyen extremos
seleccionados, bloqueo por ausencia exitosa en el borde y porcentaje de base
cero. No cambian intervalo/totales/desglose/tendencia ni borran aprobaciones,
pruebas/evidencia históricas de esas decisiones anteriores.

### Trazabilidad de las pruebas a sustituir en Red

Preservar fuera del repositorio la revisión/hash de ambos tests antes de cambiar
expectativas, junto con logs Red/Green/mutación anteriores. En Red registrar un
mapa de sustituciones por el nuevo requisito humano, no corregir tests para
obtener verde ni reducir cobertura de dinero, errores o gráficos.

| Caso existente | Motivo/expectativa operativa nueva | Cobertura que se conserva |
| --- | --- | --- |
| un único mes se consulta una vez y carece de comparación | Actualizar mensaje a uno o ninguno elegible; junio positivo produce «Solo hay un mes con coste para comparar» | Una petición, fechas correctas, sin cifra comparativa |
| base 0.00 y último12.00 en fixture con interiores5.00 | Abril0 deja de ser base: mayo5 es primer elegible, septiembre12 último; +7.00 / +140.00%, etiquetas mayo/septiembre | Abril0 se conserva en tabla/gráfico; sin Infinity/NaN/negativo cero |
| extremo ausente first/last/currency no se sustituye | Sustituir prohibición antigua por selección dentro de éxitos no cero de EUR: mayo–septiembre o abril–agosto; mismos costes100→100, variación0.00/0.00% | Hueco/otra moneda no se convierten en cero ni se usan como base EUR |
| bases negativas, precisión grande, múltiples monedas, error interior, partial | Mantener sus importes válidos; añadir extremos efectivos o límites donde corresponda | Fórmula/signo/redondeo/precisión, null gráfico, monedas, errores/omisiones |
| rangos, aislamiento/metadata, ausencia vs cero, orden del desglose/agrupación | Conservar sin rebajar; solo ajustar texto comparativo si cambió por regla humana | Meses completos, cero/huecos, cache/cancelación, red/DOM y singularidad |

Nuevos casos proporcionados: doce meses con elegibles marzo–agosto y bordes
vacíos/ceros; negativos elegibles, iguales no cero (0.00% calculable); moneda
con extremos efectivos distintos; uno/ninguno con todos éxitos; error/409 y
metadata inválida antes/después y con uno/ninguno; error interior observado;
partial exitoso, coste exacto no dibujable y total neto cero con meses +20/-20 elegibles (-40.00/-200.00%). Basar expectativas en importes
explícitos y etiqueta de meses, no en reutilizar utilidades del producto.
Evitar repetir batería monetaria ya cubierta. Cada error debe preservar causa,
no degradarse al mensaje «sin coste».

Red estrecho contra producto intacto debe fallar porque todavía usa extremos
seleccionados y razón de base cero; conservar diferencia entre fallos del nuevo
requisito y fallos de entorno. Green bajo tests fijos modifica únicamente
utilidad/página asignadas; hook, API y datos sin cambios de comportamiento.
Mutación manual en copia bajo excepción existente: ignorar ceros/ausencia,
elegir mes anterior o por valor gráfico, excluir negativos, etiquetas efectivas,
uno/ninguno, saltar errores exteriores y silenciar límites interiores.
Clasificar resultados sin porcentaje exhaustivo ni instalar herramientas.

### Reconciliación de documentación e integración

En despacho documental posterior, modificar mínimo del README en «Panel
ejecutivo de costes»: extremos efectivos no cero, negativos, mensajes de uno/
ninguno, distinción errores y partial, rango completo y recorrido anual.
Sustituir instrucciones sobre base cero y extremos seleccionados; aclarar que
mayo–julio2024 con muestra solo junio permite un mes observado y el mensaje de
uno, sin comparación numérica. Registrar referencias por moneda y versión de
datos; layout/colores/otras rutas sin nueva afirmación. Estado al 06/10/2026:
el README fue actualizado en el despacho documental separado y comprobado por
la revisión técnica interna; no se modificó durante el análisis del diseño.

Mantener filas/versionado de dataset EURv2 aprobados y artefactos v1 originales.
Solo cambiar referencia esperada de comparación, en nueva revisión externa:
- Abril–septiembre core: totalEUR420.00, primeros/últimos elegibles mayo40 y
  septiembre-50; diferencia-90.00 y porcentaje-225.00%. Abril0 permanece cero.
- Abril–mayo: totalEUR40.00, solo mayo40 elegible; mensaje de uno, sin antigua
  diferencia+40 ni porcentaje no calculable por base cero.
- Abril únicoEUR: cero observado, ningún elegible; mensaje de ninguno.
- Año2026 coreEUR: total610.00, febrero100→septiembre-50; -150.00 / -150.00%;
  doce posiciones, enero/octubre/noviembre/diciembre sin datos.
- Febrero–agostoEUR660.00,+50.00/+50.00%; marzo–junio430.00,+210.00/+233.33%;
  julio–septiembre-30.00/+150.00% siguen iguales y se etiquetan efectivos.
- USD elige sus propios meses febrero/agosto/septiembre; su septiembre enorme
  sigue elegible aunque no se dibuje. SeptiembreUSD único explica un elegible.
- Growth mantiene importes, aislamiento y febrero→agosto de su propia moneda.
No se aplica DB ni se reescribe referencia histórica en esta fase.

Después de integrar comparación, disposición, docs y dataset autorizado, una
revisión/validación independiente consolidada demuestra escenarios afectados
y límites restantes. No solicitar pruebas repetidas sobre entregas intermedias
ni presentar PASS anteriores como cumplimiento del criterio sustituido.
Revisor valora código/tests/docs; Validador demuestra criterios, caso error/límite
y captura de meses efectivos/rango/todos los puntos. Ambos conservan rol humano
pendiente. Overflow de Layout compartido/proxy y otras áreas NOT_VALIDATED
permanecen pendientes separados, sin rebajar el criterio móvil original.

| Criterio operativo | Escenarios delta | Tareas | Evidencia prevista |
| --- | --- | --- | --- |
| Primer/último coste no cero por moneda | Year interior; Zero/missing edges; Negative/large; Per currency | 8.2–8.4 | Red/Green con importes y meses explícitos; mutaciones de elegibilidad |
| Uno/ninguno y errores honestos | One/no; Inner errors; Unknown endpoints; Partial | 8.2–8.4 | Mensajes/cifras/avisos/gaps en tests y backend/UI real |
| Todo el intervalo conservado | Year interior; Grouping financial scope | 8.3, 8.5–8.6 | Total/grupos/12 posiciones/ceros/gaps sin filtros, referencia v2 actualizada |
| Docs y aprobación/trazabilidad | Este diseño y README actualizado | 8.1, 8.5–8.6 | Validación documental, approval gate y revisión/validación integradas |
