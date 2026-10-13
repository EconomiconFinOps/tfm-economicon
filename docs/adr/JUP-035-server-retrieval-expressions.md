# JUP-035: recuperación del servidor y expresiones locales

Fecha: 2026-10-13. Estado: implementación autorizada; aceptación real pendiente.
PR: https://github.com/EconomiconFinOps/tfm-economicon/pull/121

La campaña completa de f6c7895 produjo 18 respuestas completadas y 10 fallos,
además de respuestas completadas semánticamente incompletas. La decisión previa
del modelo y su plan con referencias introdujeron errores de unidades, referencias
y selección de resultados. Los recibos negativos se conservan; CI verde no es
aceptación. Se sustituye `structured-documentation-v3` por
`server-documentation-v4`, como decisión técnica para atender la solicitud del
usuario de corregir y validar PR121 dentro del presupuesto autorizado.

El servidor determina una consulta con los primeros 2048 caracteres de la
pregunta canónica. Bajo el intento ya activo ejecuta una recuperación documental
con el tenant autenticado y el deadline original. El control privado conserva
el nombre de transporte `tool_call`, pero no representa una llamada del modelo:
su digest vincula la consulta exacta y el transporte HMAC vincula claim, tenant,
usuario e intento. No se envían mensajes assistant/tool fabricados al proveedor.
Después se hace una sola generación final, sin reintentos locales ni fallback.

Esto recupera también para saludos y aclaraciones: añade coste de embedding y
latencia, y comparte la pregunta con el mismo proveedor de embedding ya
configurado. No amplía destinatarios ni permisos. El contenido recuperado es dato
no confiable y no obliga a citarlo. Si no hay fuentes pertinentes se conserva una
respuesta útil no accionable. El límite de una recuperación es por intento.

El formato privado final conserva segmentos de prosa y añade expresiones
tipadas autocontenidas. Las hojas eligen una cantidad indivisible valor/unidad
observada en la pregunta actual o en documentos efectivos autenticados, con origen
conservado y opciones documentales separadas por identificador de fuente. El
catálogo documental exige unidad explícita y coincidencia íntegra entre el
fragmento del mensaje recuperado y authorized_evidence. Su límite global128
preserva primero todos los operandos del usuario; una fuente omitida no aporta
cantidades. La regla documental no adquiere autoridad de facturación y sólo se
aplica al KPI y alcance definido por el propio documento. Un vocabulario cerrado
normaliza alias inequívocos; `$` y `¥` no se convierten a monedas supuestas.
Un encabezado monetario puede abarcar su lista dentro de una oración; un contexto
diario solo abarca su entrada o una observación inmediatamente ligada a su
baseline diario. Cardinales escritos de cero a veinte pueden heredar una
población inequívoca próxima; ordinales no se convierten en recuentos. Fechas,
conteos y umbrales no heredan moneda. Entradas ambiguas permanecen sin dimensión.

Las operaciones son suma, diferencia, cociente, porcentaje, variación relativa
con base explícita y comparación terminal. Decimal evalúa sin `eval`, con
profundidad máxima4, doce operaciones globales, 128 cantidades y cotas de
magnitud y precisión. Un cero denominador genera un bloque explícitamente
indefinido, nunca un resultado inventado. Una conversión no autorizada tampoco
produce número. Estructuras inválidas, hojas ajenas e incompatibilidades de
dimensión se rechazan. Las ecuaciones libres no se reparan.

La campaña expression14 mostró respuestas que publicaban una hoja como
`cantidad = cantidad` en lugar de calcular, y confundían un umbral con una
variación. La raíz publicada exige ahora una operación; las hojas solo sirven
como operandos. Los números originales pueden seguir apareciendo en prosa.
Un elemento de assumptions, limitations o next_actions contiene exactamente
un segmento de texto de hasta500 caracteres, sin expresiones. Los cálculos se
concentran en answer. Así el esquema deja de anunciar hasta128 segmentos cuya
suma excedería el límite público de500 y produciría rechazo al final.

Cada expresión se presenta como un bloque completo que identifica una comparación
booleana y evita sustituir opacamente IDs de resultados. La prosa circundante aún
puede interpretar mal ese bloque y requiere revisión semántica. El mismo renderer proyecta el
stream y el candidato final. Se mantienen Unicode, rechazo de duplicados,
normalización global de espacios, 4000 caracteres de answer, 500 por elemento
de lista y deltas de 8192 bytes. La pareja y metadata se persisten atómicamente
solo tras validar el final. Las expresiones no autorizan métricas financieras.

El esquema usa `$defs` por nivel y un único catálogo, sin intersecciones
redundantes de literales. Backend y processor cuentan exactamente el esquema
final efectivo y el contexto; ya no reservan una segunda petición de decisión.
Se mantiene salida máxima3200, modelo y proveedor, deadline/cancelación y todas
las reglas de autoridad y citas del contrato público FinOpsResponse1.0.

Límites: comprobar un extracto literal acredita origen, no pertinencia. Calcular
una expresión acredita esa operación, no que el modelo haya elegido la base
semántica correcta. La aritmética usa pregunta y documentos efectivos, no reconstruye valores
ambiguos de recuerdos. La respuesta completa, citas y completitud requieren una
nueva campaña real y recorrido UI; no se afirma corrección universal de prosa.

La campaña expression15 (192b687) completó23 casos y falló5, con27 HTTP429
observados y dos rechazos de contenido. Sus respuestas completas conservan
errores semánticos de denominador, interpretación de porcentajes y omisiones:
no constituye aceptación. Se elimina la contradicción entre la política base
de ingesta (toda cifra exigía evidencia financiera) y los ejercicios del chat
mediante CHAT_SYSTEM_PROMPT separado, con base/hash propios. SYSTEM_PROMPT de
ingesta no cambia. El esquema privado fija ahorro estimado y divisa a null,
como ya exigía el firewall del chat; no se rellena una pareja inválida.

Ensayo posterior acotado: reasoning high con exclude=true, declarado en el
manifest/assembler. Conserva3200 tokens totales (razonamiento y salida comparten
el límite),120 segundos y el mismo endpoint GLM5.2/DeepInfra. No se expone ni
guarda razonamiento privado; se miden uso, finish_reason y respuesta pública.
La primera salida vacía/truncada detiene el ensayo para evaluar el límite, sin
repetirla idéntica. Es una hipótesis de mejora semántica, no una causa demostrada
de los fallos anteriores ni una aceptación anticipada. Referencias primarias:
https://openrouter.ai/docs/guides/best-practices/reasoning-tokens y
https://docs.z.ai/guides/capabilities/thinking .

Pruebas previstas: consulta alterada/HMAC/aislamiento, una generación después de
retrieval, cancelación de ambas fases, uso privado y público, esquema/conteo
idénticos, límites y unidades, texto/expresión partido, stream=final=JSONB,
fuentes efectivas y rechazo sin reparación. El banco JUP-069 no se modifica.

### Clasificación por intervalos documentales (13/10/2026)

La focal expression17 corrigió el denominador de005 y027, pero005 llamó rojo al
10% y013 trasladó esos umbrales a presupuesto. Se añade `classify` al AST privado:
el servidor evalúa intervalos y devuelve etiqueta y comparaciones como un bloque.
No cambia FinOpsResponse, JSONB ni el límite global de12 operaciones.

La extracción admite una gramática cerrada: fórmula explícita `KPI: nombre % =
numerador / denominador * 100` y lista de2 a8 intervalos porcentuales con límites
abiertos/cerrados. Exige partición completa sin huecos/solapamientos; cualquier
fila no interpretable invalida la regla. No presupone etiquetas ni umbrales.
Los rangos del Markdown original conservan identidad posicional de sección;
encabezados internos cambian el alcance. Sólo se reconstruyen fragmentos contiguos
con solapamiento idéntico. Secciones homónimas distintas no se unen.

El catálogo visible al modelo incluye KPI, sección, límites y fuentes. El
numerador exige una etiqueta léxica inequívoca en la misma cantidad del usuario;
no se traduce semánticamente ni se permite aplicar reglas de un KPI a otro.
El denominador sigue siendo elegido por el modelo: se comprueba su aritmética y
dimensión, pero este vínculo no garantiza universalmente su pertinencia.
Las fuentes de la regla deben figurar en la evidencia final seleccionada.

Un control acotado rechaza conclusiones libres que usan vocabulario explícito
de clasificación y etiquetas de las reglas disponibles, incluso sin `classify`;
las citas literales requieren su fuente. No prohíbe palabras genéricas fuera de
ese contexto ni promete detección universal de contradicciones en prosa.
Ambigüedad documental significa no clasificar, no inventar una regla. Las pruebas
locales no sustituyen la próxima focal ni la batería semántica completa.

Véase [diseño OpenSpec](../../openspec/changes/jup-035-auto-documentation/design.md)
y [continuidad](../continuidad/chat-conversacional.md).
