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

La focal expression19 mostró que el modelo añadió una conclusión roja después
del bloque amarillo correctamente calculado. Captura sintética de la oración
rechazada confirmó el defecto; el guard se conserva. Se separan dos variantes
privadas: narrativa (segmentos sin classify) y clasificación terminal
`answer={calculations:[AST],classification:classify}`. Esta última no contiene
texto libre; admite sólo notas neutrales enumeradas, sin métricas, recomendaciones
ni acciones adicionales. El servidor concatena los cálculos y la clasificación;
no elimina ni reescribe una conclusión equivocada del modelo.

El parser almacena el objeto privado acotado hasta su cierre, lo valida y emite
su respuesta antes del evento final. Mantiene4000 caracteres públicos,8KiB por
delta y12 operaciones compartidas. El coste es menor flexibilidad narrativa en
una respuesta clasificadora; los consejos libres pertenecen a una respuesta
narrativa posterior. Fuentes seleccionadas y correspondencia del denominador
siguen requiriendo comprobación semántica. Las notas enumeradas no declaran
que los datos del escenario sean facturación verificada.

Véase [diseño OpenSpec](../../openspec/changes/jup-035-auto-documentation/design.md)
y [continuidad](../continuidad/chat-conversacional.md).


La focal20 confirmó que ofrecer ambas variantes permite elegir narrativa y volver
a clasificar mediante prosa. La versión de contrato v7 restringe las respuestas
ok/partial a la variante terminal únicamente cuando el primer párrafo de la
pregunta actual solicita explícitamente clasificar o un semáforo y existe una
sola regla documental con numerador anclado. Preguntas conceptuales, negaciones,
ambigüedad y datos sin regla conservan narrativa; historial, documentos y párrafos
posteriores no pueden activar esta ruta. Es una detección léxica conservadora,
no comprensión universal de intención. La misma restricción se valida localmente
y en el esquema privado. La abstención permanece disponible si faltan datos.
Esto no identifica el ValueError no reproducido de la focal20 ni garantiza la
pertinencia de consejos narrativos: ambos siguen pendientes de evaluación real.


Corrección offline posterior a smoke21: el error cerrado de006 confirma ausencia
de una cita necesaria para el cálculo documental. En la variante totalmente
servidor, `evidence=[]` es obligatorio en la entrada privada. Tras validar todos
los AST y las notas enumeradas, el servidor proyecta exclusivamente los registros
usados por las operaciones y la regla desde el contexto documental autenticado.
No añade fuentes no utilizadas ni asigna una cita textual de la primera ventana.
Un resultado Python interno conserva esos registros; no hay bandera JSON que el
proveedor pueda enviar. El ensamblador exige igualdad exacta de registros y de
metadatos públicos contra authorized_evidence. Serializar y volver a leer el
resultado pierde esa capacidad interna y activa la validación narrativa ordinaria,
que sigue exigiendo support_quote. El contrato público y la autoridad financiera
no cambian; las citas se refieren al bloque calculado, no a prosa libre del modelo.
La rama terminal aparece primero sólo cuando la intención explícita la requiere;
la abstención permanece disponible. Esto no garantiza que el modelo elija bien
operandos o se abstenga correctamente: continúa la evaluación semántica.


El caso024 del survey21 mostró una operación artificial para volver a presentar
un importe de cada moneda. Se incorpora el segmento privado `{quantity:clave}`:
publica el valor y la unidad observados con origen «Dato aportado» o «Dato
documental», sin fabricar una suma ni una identidad aritmética. Una cantidad
documental conserva la obligación de citar su fuente; una cantidad del usuario
no crea evidencia ni autoridad financiera. Las hojas siguen excluidas como
operaciones de cálculo. El parser y render usan el mismo camino, con los límites
existentes de segmentos, caracteres y deltas. La comparación también publica los
valores evaluados exactos junto a la fórmula, sin redondear la verdad del límite.

El guard de clasificación libre usa asimismo etiquetas de filas intervalares
con provenance válida aunque falte la fórmula o partición completa. Esas filas
sólo amplían detección de conclusiones no verificadas, nunca el catálogo ejecutable;
no se prohíben palabras genéricas fuera de una conclusión de clasificación.


### Regla booleana terminal y contexto vecino (13/10/2026, survey22)

Una respuesta mostró comparaciones correctas pero una conclusión AND falsa.
La variante `answer.boolean` fija regla, baseline y observado a un descriptor
servidor: gramática acotada de delta relativo/absoluto, comparadores explícitos
y AND/Y u OR/O. No hay umbrales del banco codificados. El servidor construye
ambos deltas, evalúa límites y combinador y redacta toda la conclusión. Base cero
es indefinida, con lógica ternaria; no se reemplaza por un número. Roles ambiguos,
monedas incompatibles, reglas contradictorias, negaciones o cadenas adicionales
no autorizan esa variante. Dos condiciones deben caber en un span documental
autenticado: una regla cortada se rechaza sin completarla por inferencia.
Reglas usuario/corpus se deduplican sólo con igualdad semántica exacta; la regla
aportada por usuario no necesita una cita artificial. El contrato público sigue
exigiendo evidencia para ok, por lo que un cálculo user-only conserva
insufficient_data sin inventar autoridad financiera. Las variantes terminales
prohíben prosa libre auxiliar; la abstención de clasificación requerida sólo
admite mensajes neutrales cerrados, sin saltar el guard mediante status.

La recuperación anterior sólo expandía vecinos presentes en top20 vectoriales.
Ahora una consulta posicional inmediata bounded en la misma transacción
REPEATABLE READ carga vecinos de seeds sin otra embedding ni búsqueda semántica.
Tenant, proveedor, documentos/índices y top_k permanecen vinculados; no recursión.
El timeout/cancelación común se aplica antes de cada consulta. Los vecinos pueden
estar fuera del umbral vectorial: son contexto contiguo, no nuevos hits relevantes.
Esto corrige una carencia demostrable, no prueba la causa exacta del fallo005/007.

Evidence se ordena después del texto en el esquema privado para permitir elegir
soporte de afirmaciones ya redactadas. Const/enums y verificación literal siguen
intactos; cambiar el orden no demuestra entailment ni aceptación semántica.

### Narrativa respaldada y escenarios sin fuentes (13/10/2026, survey23)

Survey23 pasó19/28 criterios semánticos; los28 recibos conservaron los límites
y la atomicidad. No está aceptada. La narrativa de003 atribuyó un método a
documentos pero seleccionó evidence vacía;001 repitió cálculos y redactó una
suma incoherente;022 terminó con una referencia de recomendación ausente de las
fuentes seleccionadas. No se conoce si ese ID era inventado o autorizado pero
omitido: no se atribuye una causa más concreta que el error observado.

El contrato privado v10 separa narrativa libre respaldada (al menos una fuente
seleccionada, también en estados de abstención) de `answer.scenario`, compuesto
por cantidades originales y expresiones de datos aportados por el usuario. Esta
última rama prohíbe prosa libre y operandos documentales, conserva evidence vacía
y status insufficient_data por el contrato público vigente, pero presenta el
cálculo completo como hipotético sin afirmar que falten sus operandos.
`answer.request.reason` ofrece motivos genéricos cerrados; el servidor deriva
status y un siguiente paso útil, sin que JSON pueda sobrescribirlos. Incluye
saludo, aclaración, datos autorizados, cobertura/ingesta, base comparable,
documentación no contrastada, fuera de alcance y ejecución no habilitada.
El modelo aún puede seleccionar un motivo improcedente: esa necesidad sigue
sujeta a evaluación semántica. No se eliminan las explicaciones documentales.

Recommendation selecciona registros de evidencia privados completos. Cada uno
se contrasta con el registro y la ventana literal autorizados antes de deduplicar;
el servidor une sólo esas selecciones explícitas y proyecta los evidence_ids
públicos. No autocita el retrieval, no fabrica citas para una afirmación y no
demuestra entailment. No concede autoridad para métricas ni ahorro estimado.

El límite12 pasa a contar evaluaciones numéricas estructuralmente distintas,
más cada comparación/comprobación de clasificación, con memoización de los
subárboles idénticos. Sustituye el conteo de cada repetición descrito arriba:
no se aumenta el tope12 ni se afirma que el cache corrija prosa falsa. Cada
ocurrencia se valida de nuevo a su profundidad real antes del cache, restaura
provenance y usa un catálogo aislado cuya mutación se rechaza. Trece operaciones
distintas siguen fallando; segmentos, bytes, caracteres, profundidad y magnitud
mantienen sus límites. La salida repetida sigue contando para el límite textual.

Una razón evaluada de denominador/base cero añade una petición de cobertura o
base comparable; no supone que cero sea ausencia de ingesta ni garantiza un
denominador futuro positivo. El resultado público, SSE y JSONB siguen idénticos.
No cambia el modelo/proveedor, una recuperación/generación,3200tokens, deadline
ni el presupuesto autorizado. La batería completa del candidato sigue pendiente.
