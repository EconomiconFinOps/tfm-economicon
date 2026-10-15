JUP: JUP-123

## Context

B preserva el flujo que ya recupera documentación en servidor y genera draft/final
sin herramientas nativas. Retirar tools no es una nueva solución pendiente.
El scorer previo conserva 253 juicios históricos y nueve incertidumbres.

## Decisions

Base de ingeniería actual: A/8ea5a0c4 sobre develop0543c5ee/JUP-038, reconciliada
localmente en B/7be57c05. Los39 archivos de aplicación afectados coinciden con
los bloques de A; la semántica B se conserva. Pruebas propias frontend/backend
conformes; la regresión Linux/SQL de7be quedó verificada y la del corte corregido72
consolida1793 identidades chat conformes, sin omisiones nativas pendientes. No importa el estado de sus
reviews ni sustituye su CI. La reconciliación A11f/Bab66f90c queda como antecedente.
Compatibilidad de disponibilidad/slots comprobada en API, frontend y CD; los rangos
libres siguen siendo prerrequisito de despliegue y el navegador final de B queda
para el candidato completo. Ver [continuidad A/B](../../../docs/continuidad/chat-entregas-a-b.md).

1. Reconciliar A por bloques usando la base Paris f63c150 para adiciones paralelas;
   mantener semántica B y controles de activación, cancelación y fecha de A.
2. N=3 inicial, N=5 de confirmación según criterios obligatorios y presupuesto.
   Sin selección del mejor intento ni omisión silenciosa de fallos técnicos.
3. Identidad por campaña, caso y repetición; banco y corpus inmutables. Conservar
   commit, hashes, entradas, fragmentos realmente usados, parámetros y costes.
4. Contabilidad viva y reserva conservadora antes de inferencias. Tope acumulado
   de10USD (ampliación explícita del usuario el15/10, posterior a2/5USD),
   incluyendo intentos fallidos, servicios auxiliares y todas las reservas anteriores.
   La vigencia de claves se autoriza por separado: mismas claves hasta15/10 a18:00París,
   sin reiniciar contadores ni liberar reservas pendientes.
5. Las coincidencias de palabras/números son diagnósticos, no veredictos semánticos.
   Citas requieren soporte de la afirmación, no sólo solapamiento léxico.
6. Las correcciones se evalúan contra la misma rúbrica congelada. Ninguna media
   compensa una regresión obligatoria; umbrales aún pendientes de revisores.

### Coste desconocido de un fallo terminal

COST_UNKNOWN_RESERVED conserva íntegra la cota original de una operación fallida
con entrada durable y recibo verificados. No es coste observado, no mejora el
resultado técnico y no libera saldo. El siguiente preflight suma esa reserva
completa, además de los contadores conservadores y la cota siguiente. El runner
sólo avanza tras verificar identidad, estado failed, SHA del recibo y que la
reserva no fue reducida. Operaciones activas o evidencia inconsistente bloquean.

El recuperador ofrece este tratamiento explícito cuando la consulta de una
generación devuelve404 después de verificar operaciónSQL, fases y preflight.
Un404 o un spend0 en el gateway no demuestra gratuidad. El recibo original y
la prueba del coste indeterminado se conservan. La campaña mantiene el fallo
como tal y no repite suPOST. Los artefactos distinguen gasto conocido y reservas.

## Risks and open questions

### Correcciones medidas015/003/013 — producto d2f8a440

El compilador documental exige la definición completa de budget en Conceptos
FinOps Basicos además de Budgets Y Forecast. Recuperación complementaria exacta
en el mismo snapshot/tenant/proveedor, sin otro embedding; cobertura incompleta
conserva la ruta general. Seguimiento, alertas y ausencia de apagado por defecto
proceden del corpus autorizado, no de una lista de hechos escrita en el prompt.

La investigación conceptual sin cantidades ni evidencia financiera usa el método
completo y consecutivo de Cost Management Y Cost Analysis, con cláusulas literales
autorizadas. Solicita ámbito/periodo y parámetros ausentes sin convertir campos
del esquema Anomaly en prerrequisitos. La desviación hipotética de presupuesto
usa roles explícitos de coste final/presupuesto, moneda y mes compatibles, Decimal
con precisión80, operandos exactos y denominador cero explícito. Entradas fuera de
esa gramática conservan la ruta general; no se afirma un extractor universal.

Los rechazos de prosa aritmética registran sólo campo/índice cerrado, sin guardar
la prosa privada. No se inventa el campo o texto exacto del fallo histórico013:r3.
La nueva N3 del corte72a2f767 mide estas correcciones contra el banco, corpus y
rúbrica previos, con los84 recibos de7be intactos.1793 pruebas técnicas y recursos
firmados conformes no acreditan por sí solos calidad semántica ni aceptación.

### Capacidad de ejecución: corrección local posterior025

La N3 del corte72 conserva un fallo semántico025:r1: amplía a cualquier cambio
de producción una lista de comprobaciones que la fuente sólo exige a rightsizing.
`chat_resource_actions.py` reconoce órdenes directas mediante una gramática acotada
de verbos/recursos; no busca IDs del banco, no interpreta contexto recuperado como
instrucción y no es un clasificador universal. Preguntas conceptuales, negaciones
e instrucciones citadas conservan su ruta general.

El servidor liga la negativa y los próximos pasos a la petición completa, con
status refused y auxiliares privados vacíos. Explica sólo su capacidad real de
análisis, sin hacer pasar una política documental particular por una restricción
general. No ejecuta acciones ni depende de que el modelo respete esa prosa.
Const e ID ligado a la entrada se comprueban tanto en stream como en final y
en el contrato independiente del backend.238 pruebas locales y carga en frío de
ambos bundles conformes; sigue sin construir/activar/medir con proveedor. La N3
de72 permanece congelada y no se reetiquetan sus fallos.

### Calificadores documentales y tres valores — 2026-10-15

Producto2c79b32d: `chat_documentary_decisions.py` compila dos usos limitados de
secciones completas y autorizadas. La comparación conceptual conserva todos los
bloques de definición de actual/amortized cost, hasta la siguiente definición,
incluidas limitaciones posteriores. No reescribe «se aproxima»/«suele» como certeza
ni infiere un reparto equitativo. El consejo sobre commitments exige la gramática
completa de la sección: definición, comprobaciones de rightsizing y recomendación
con modalidad positiva de consejo, copiadas literalmente. Una excepción añadida
o política no reconocida no se aplica parcialmente.

El escenario explícito conserva demanda futura en tres valores y estado de
rightsizing con soporte de entrada. Se evalúa su conjunción sin convertir una
premisa desconocida en falsa cuando otra la decide. Eso es preparación declarada,
no autorización de compra. La respuesta ofrece consejo condicional y próximos
pasos; no crea métricas ni tarjetas de recomendaciones con severidad/ahorro no
evaluados. Otras preguntas/escenarios mantienen la ruta general. La incertidumbre
histórica no se adjudica por hacer este cambio.

468 pruebas focales processor/32 backend conformes, con el corpus original y
gateway simulado. Replay de84 sólo selecciona004/022r1/r2/r3, con citas, modalidad,
premisas y paridad pública preservadas; no modifica etiquetas históricas ni mide
al proveedor. Loader/pin actualizados. Linux, transferencia y limitaciones en
continuidad; aceptación real, criterios y adjudicación siguen pendientes.

### Etapas de ahorro y ecuación de realization — 2026-10-15

Producto1afa3815 compila tres roles monetarios explícitos, con moneda/unidad temporal
idénticas y fórmula verificado/identificado×100 aportada por el usuario. Permite
reordenar los campos y conservar cantidades iguales con roles distintos; no presume
que las etapas sean monótonas. El importe realizado del ejercicio es el verificado,
no el estimado ni la suma. Denominador cero queda indefinido y el redondeo usa≈;
porcentajes superiores a100no se recortan. Declaraciones incompletas, otros ámbitos,
unidades incompatibles o evidencia financiera del servidor conservan la ruta general.
El escenario sigue siendo hipotético: no confirma implementación, ahorro o causalidad.

`chat_savings_realization.py` se integra en el registro de terminales de escenario.
El esquema privado sólo permite el ID ligado a toda la entrada, status insuficiente
y auxiliares vacíos. El servidor calcula/renderiza; no se permite que el proveedor
redacte una ecuación libre.419 pruebas focales processor/30 backend conformes,
incluidos seis recorridos de gateway simulado con lectura1/7/8192bytes y rechazo
de la ecuación libre. No se relaja esa invariante.

El replay de84recibos selecciona sólo021r1/r2/r3 y produce80EUR/mes/40% con paridad
de streaming/final/público.021r3 histórico permanece failed y su reserva íntegra:
no se recuperó la ecuación privada original ni se acredita haber reproducido su
causa exacta. Esto corrige localmente la posibilidad de generar esa ecuación para
el escenario admitido, sin probar al proveedor real. Ver continuidad para Linux,
hashes y medición pendiente;004/022 siguen requiriendo tratamiento/adjudicación.

### Atributos del desglose y regla de reparto ausente — 2026-10-15

Producto localb3528bcf añade dos compiladores de escenarios explícitos, con
cantidades y nombres variables. `chat_cost_breakdown.py` consume una declaración
completa de período/suscripción/moneda/vista y hasta12 servicios únicos; calcula
suma, máximo, empates y participación. Retiene créditos con signo, no interpreta
una participación sobre total no positivo y marca aproximación al redondear.
La declaración de cobertura completa se conserva como dato no verificado.
`chat_shared_allocation.py` exige coincidencia de importe/moneda/activo entre
petición y escenario, equipos distintos y la declaración de regla aprobada ausente
y consumo desconocido. Conserva el coste shared, pide regla/base/datos y no asigna
cargos. Usa hechos del escenario: no elige citas documentales como justificación
ni afirma haber comprobado una política real. Evidencia financiera del servidor
tiene prioridad: impide sustituirla por esas rutas hipotéticas.

Los terminales de escenario comparten selección/esquema/renderizado en
`chat_segments.py`, con ID ligado a la entrada y auxiliares vacíos. No se silencian
contradicciones de prosa después de emitirse: el proveedor recibe el terminal
cerrado. Esto no resuelve interpretación general de cualquier relato; preguntas
compuestas, datos incompatibles o declaraciones fuera de las gramáticas conservan
la ruta existente. No se declara aceptación por reconocer los ejemplos del banco.

375 pruebas focales processor/27 backend conformes y replay de84recibos que sólo
selecciona001/009r1/r2/r3, con paridad streaming/final/público; etiquetas históricas
intactas. Ver continuidad para las pruebas Linux y pin de recursos. Cambios aún
sin activar ni medir con proveedor;021 y las incertidumbres004/022 siguen abiertas.

### Cobertura ponderada y diagnóstico estructural — 2026-10-14

Producto local654298d4: `chat_weighted_coverage.py` compila una partición explícita
de recursos conformes/no conformes y sus costes en moneda común. Admite cantidades
variables, cardinales y un ordinal sólo cuando identifica el único recurso restante.
Exige cerrar toda la declaración; ambigüedad, negaciones, tareas múltiples, grupos
que no suman o datos financieros autorizados conservan la ruta general. Es una
gramática limitada de escenarios, no un extractor semántico universal ni una política
de tagging codificada. El usuario declara qué recursos cumplen y que todo el coste
es etiquetable. El servidor calcula ambos denominadores y ambos porcentajes con
Decimal; coste cero queda indefinido. El terminal ligado al hash de pregunta/datos
sólo admite status insuficiente y auxiliares vacíos, evitando omisiones del resultado
o contradicciones generadas. No convierte datos hipotéticos en métricas reales.

El parser anota únicamente campo, tipo, modo e índices0..127 cuando falla un render
de segmento, grupo de prosa o terminal. El gateway reconstruye ese pequeño evento
desde listas cerradas; no conserva contenido privado. El rechazo de ecuaciones
libres permanece. Esto permite diagnosticar una futura021; no reconstruye su
candidato histórico ni acredita que la causa semántica de021 esté corregida.

226 pruebas focales processor,24 backend y seis nuevas de fragmentación conformes.
Replay de84recibos c7 selecciona sólo011r1/r2/r3 y entrega10%/90% con paridad pública;
no altera juicios históricos ni sustituye medición pagada. Ambos loaders propios
aceptan versiónb6aa3330f1ea2f6d0cea1a12dc67ba17a1ce090cf19a99f97eba5b78a8b649c8.
Ver continuidad para evidencia, pruebas Linux y pendientes001/009/021/004/022.

### Corte vigente después de N3 c7 — 2026-10-14

Supera los estados «pendiente de medir» de los cortes históricos inferiores.
La medición de c7 terminó: 83 respuestas y 1 fallo técnico; revisión local
70 conformes, 7 inciertas y 6 fallos de contenido. No permite aceptación.
Ver [informe y comparación](../../../docs/validation/JUP-123-c7e2d561-N3-local-review.md).

El siguiente contrato debe separar tres responsabilidades: extraer hechos
con fuente y ámbito, determinar resultados/reglas que deben cubrirse y redactar
sobre esos hechos. Que una expresión sea correcta no garantiza que el modelo
la seleccione (011r3); que una cita sea literal no garantiza que seleccione el
pasaje pertinente (009r1). No resolverlo añadiendo preguntas del banco a un router
de expresiones regulares ni degradando validadores para que termine la operación.

Hechos aportados mantienen autoridad hipotética, distinta de facturación
contrastada. Atributos conocidos no pueden reaparecer como ausentes (001r2).
Los calificadores documentales deben conservarse en conclusión y auxiliares:
«conviene» no se convierte en «exige» y no confirmado no se convierte en falso.
La cobertura debe distinguir sección recuperada incompleta de política ausente;
015 necesita la regla de investigación, no otro ajuste global de estilo.

Antes de otra campaña: implementar y contrastar fuera del banco ejemplos de
valores/monedas/ámbitos alternativos, fuentes incompletas y contradicciones;
comprobar streaming/final/backend. Registrar explícitamente qué parte de la
extracción sigue siendo semántica y no atribuirle garantías deterministas.
La cota final 4.423039035/5USD incluye reservas completas desconocidas; no basta
restar esa cifra para autorizar otra N3. Cada operación exige admisión viva.

### Compilador local de secciones completas — 2026-10-14

Primer bloque implementado después de medir c7. `chat_policy_sections.py`
reconstruye una sección desde rangos posicionales autorizados, con encabezado
inicial y siguiente encabezado que cierre su extremo. Comprueba cada carácter
solapado; no rellena huecos ni considera el final del chunk como final de política.
Tablas y listas se compilan como unidades literales, cada una contenida íntegra
en un fragmento real. Conserva valores, negaciones y calificadores como datos.
El contrato no contiene una copia de los tags o reglas del banco.

El enrutador léxico reconoce temas conceptuales de reglas de tagging y apagado
por presupuesto; no compara preguntas completas del banco. Rechaza negaciones,
peticiones múltiples, cálculos, configuraciones reales y otras políticas.
Sus límites son explícitos: preguntas fuera de esas rutas conservan la síntesis
general, que aún necesita evaluación. La garantía de cobertura no se extiende
a una extracción semántica arbitraria.

Una sección completa y única produce un terminal privado ligado al hash de
pregunta, sección y fuentes. El esquema sólo admite ese terminal y auxiliares
vacíos; servidor y parser producen todas las unidades y las mismas citas.
Un contexto financiero de pantalla no convierte una definición en métrica.
Con secciones parciales, incompatibles, ambiguas, demasiado largas o no citables,
no se fuerza el terminal ni se inventa el texto ausente.

247 pruebas focales processor y dos backend con corpus real correctas. Ambos
loaders propios cargan en frío la misma nueva versión. Replay de los84 recibos
c7 activa sólo010r1/r2/r3 y conserva once unidades/streaming/final/ensamblado;
no mide al proveedor ni cambia etiquetas históricas. 015 carece de la sección
completa en esos recibos: sigue pendiente, aunque el compiler ya admite su lista
completa en la prueba de corpus real. Siguiente bloque: recuperación de la sección
por tenant/provider en el mismo snapshot SQL, con límites y cancelación existentes.
No sustituir esta prueba por un JSON local presentado como retrieval real.

### Recuperación exacta de la sección — comprobada con pgvector

Backend añade una expansión opcional según el tema conceptual admitido, dentro
de la conexión REPEATABLE READ de la búsqueda actual. No hay otro embedding.
Los encabezados candidatos se localizan en documentos del tenant con embeddings
del proveedor activo; el parser original de Markdown debe confirmar un único
encabezado real y su cierre. Se permiten dos candidatos como centinela de
ambigüedad, documentos de hasta65536 bytes y seis chunks como máximo; el séptimo
es centinela de presupuesto, no una muestra que pueda recortarse silenciosamente.

La consulta de chunks usa posiciones literales en el texto normalizado del mismo
documento/snapshot y comprueba continuidad antes de dar prioridad. Conserva las
distancias reales; el filtro de similitud del ranking no impide obtener una
política por su sección explícita. La selección total sigue limitada a20,
con omisiones explícitas si el límite de evidencia es inferior. Los pasos SQL
reutilizan el control de plazo/cancelación existente y no abren otra conexión.

Producto fb7d9ea0, pruebas adicionalesddb64eb5:46 casos Linux/pgvector correctos,
sin omisiones, con XML durable. Incluyen actualización concurrente de texto y
chunks (se conserva una sola versión), tenant/proveedor, límite de seis, byte
limit con UTF8 y ambigüedad entre dos documentos. Los servicios B vigentes no
cambiaron; sólo PostgreSQL/runner desechables sin red externa. La sección de
presupuestos llega completa al compilador, incluida investigación/no apagado.
Esto no es una campaña LLM de015 ni aceptación de B; no se alteran sus recibos.
17 pruebas de recursos y carga independiente de ambos servicios conformes.

### Cortes históricos previos a la medición de c7

Correcciones locales posteriores a00dc: el prefijo de modo hipotético incluye
comparación aritmética derivada de campos explícitos adyacentes forecast/budget
en la misma moneda. Es cobertura numérica, no extractor general de hechos,
verificador de ámbito/periodo ni predictor. Conserva el resto de la respuesta y
no actúa con fuentes financieras del servidor. Roles ambiguos o unidades distintas
mantienen la ruta general. Casos cambiados/negativos cubiertos por contraejemplos.

003r1 conservaba19repeticiones de un mismo pasaje en una parcial de3918caracteres.
Deduplicación por(source_id,passage) sólo en answer, después de validar la cita;
no elimina pasajes únicos ni deja vacíos auxiliares/recomendaciones. La gramática
de generación ofrece24bloques (hasta20referencias y espacio de síntesis), mientras
los límites de compatibilidad del renderer y los4000caracteres públicos siguen
vigentes. No se acepta una final truncada ni se finge que se evitó un finish=length.
El mecanismo todavía necesita medición real del proveedor.

Los hashes de contrato/manifest se regeneran al cambiar esquema, módulos y prompt;
los activos se guardan enLF para que Windows ygitarchive coincidan. Cargaenfrío
backend/processor conforme. El fixture de contexto arranca su plazo sintético
después de preparar/tokenizar datos y usa el mismo fenceSQL ypayload; expectativas
409/413 intactas. No cambia plazos ni controles de producción.

Corte actual N3 e23e495b:84recibos,78respuestas/6fallos técnicos. Revisión local
de todas las respuestas terminada:68conformes/8inciertas/2fallosdecontenido.
014r2/r3 omite el exceso relativo;022 falla3veces por soporte visible propio
de recomendaciones. Ver [informe local](../../../docs/validation/JUP-123-N3-local-review.md).
La reserva se revisó después de congelar calibración, sin ajustes intermedios;
era históricamente conocida. Ajustarla después exige nueva evidencia independiente.

Corrección posterior aún local: rationale de recomendación selecciona un único
pasaje documental autorizado; interpretación en action. Los modos sin autoridad
documental no ofrecen citas en auxiliares. No se corrige una salida inválida
asignándole fuentes inferidas ni se debilita el renderer. Los diagnósticos de
013r3/021r3 identifican la invariante de autoridad, no el campo privado exacto:
esta inconsistencia del esquema es comprobada, su causalidad en esos dos intentos
es hipótesis pendiente de medición. El runtime e23 permanece sin modificar.

El entorno compartido anterior no demuestra procedencia del candidato nuevo.
Colector y baseline real N3 completados el 2026-10-14: 84 recibos, 77 operaciones
completadas y 7 fallidas preservadas. Pendientes adjudicación independiente,
acuerdo de criterios y comparación del candidato corregido. El candidato e94 completó regresión Linux y43pruebas SQL reales; el historial017
se verificó en navegador, sin nueva generación. El candidato posterior requiere
su propia validación. La campaña comparativa quedó parcial41/84 por presupuesto.
No afirmar cierre por superar pruebas unitarias ni por reunir 84 recibos.

## Premisas y conclusiones — integración en curso, 2026-10-14

Los fallos026/028 no se resuelven comprobando sólo que una cita sea literal.
Se introduce un evaluador trivalente acotado (`chat_premises.py`), integrado primero en la combinación de comparaciones numéricas
verificadas; la ruta de premisas textuales continúa pendiente. Una premisa conocida tiene procedencia; una premisa
no evaluada conserva valor desconocido, sin evidencia negativa inventada.
AND/OR/NOT usan lógica de Kleene. Se validan todas las ramas y se conservan
las premisas desconocidas aunque otra condición determine el resultado.

La frontera de confianza es explícita: el evaluador NO interpreta lenguaje
natural ni demuestra implicación documental. Sólo admite objetos construidos
por código de servidor; no diccionarios de verdad/procedencia del proveedor.
El enlazador deberá contrastar identidad, ámbito, instante y soporte semántico
con la entrada capturada o la fuente autorizada. Citar una frase literal no
basta para establecer su valor. Una regla ambigua no produce una premisa falsa.

Integración pendiente, por orden:
1. Enlazar hechos tipados con observaciones/fragmentos originales. Registrar
   lo que no se ha medido como desconocido. No deducir gasto cero de cero filas.
2. Aplicar reglas explícitas con sus propias fuentes, separando evidencia de
   la regla de evidencia de los hechos; la regla general no verifica al cliente.
3. Una misma decisión alimenta respuesta, limitaciones y recomendaciones.
   La redacción de esos terminales no puede sustituir desconocido por falso.
   Conservar el resto de la síntesis útil y el alcance original del chat.
4. Derivar citas de reglas y premisas utilizadas; nunca añadir fuentes sólo
   por aparecer en el retrieval. No declarar resuelta la pertinencia general.
5. Verificar por replay de026/028, contraejemplos, streaming/final y backend;
   actualizar el contrato de recursos sólo cuando la ruta esté integrada.

Treinta pruebas del núcleo cubren las tablas de verdad y límites, pero no
acreditan el enlazador, extracción, redacción ni la corrección del producto.
No se cambia el candidato desplegado ni la campaña congelada para este trabajo.

### Fuente disponible para el enlazador de cobertura

Inspección de `apps/backend/app/services/chat_context.py::ChatContext.billing`
(14/10/2026): la consulta se ejecuta por tenant y periodo; `BillingSummary`
valida resultados, y la comparación con pantalla incluye importes, grupos,
conteos y estado. La evidencia cost_query expone métricas, periodo, agrupación
y data_status. Ese contrato no aporta una certificación de cobertura de ingesta
para el periodo completo. `available` y `matched_at_verification` no autorizan
inferirla. Tampoco los fragmentos FinOps generales acreditan cobertura financiera.

El enlazador debe separar como mínimo:
- `query_has_rows`: observación de la consulta contrastada, con su scope.
- `queried_total_is_zero`: sólo un total explícito contrastado para una moneda;
  no se construye a partir de una lista vacía ni mezcla monedas.
- `period_coverage_complete`: desconocido mientras no exista evidencia específica.
- `period_spend_is_zero`: no se deriva de query_has_rows=false; requiere total y
  cobertura completos en el mismo scope/periodo/moneda.

Los escenarios textuales del usuario, incluido026, mantienen procedencia
hipotética y no pasan a este canal de autoridad financiera. La integración
requiere además una ruta de escenario explícita y sus contraejemplos; no usar
una mera coincidencia de palabras para simular observaciones autenticadas.

### Integración numérica verificada

render_boolean construye premisas a partir de resultados de _numeric y del
comparador de la regla ya ligada al catálogo. evaluate combina esos resultados;
no recibe la verdad escrita por el modelo. Conserva la semántica anterior y
no cambia las fuentes documentales. Las pruebas de streaming/final incluyen
falso AND desconocido=falso y falso OR desconocido=desconocido, sin convertir
el operando desconocido en falso. Queda pendiente el enlace textual descrito
arriba; esta integración no cierra026/028 ni suple la campaña real incompleta.

### Terminal documental de reporting (implementado localmente)

Para clasificación showback/chargeback, una gramática cerrada enlaza el escenario
completo con la presencia/ausencia explícita de repercusión contable. No extrae
ese hecho de una frase aislada ni acepta instrucciones o condiciones adicionales.
Un bloque completo de definiciones y sección documental autentificada proporciona
la regla; un hash de entrada+fuente liga el terminal privado. La respuesta usa
la decisión del servidor, explicita que la calidad no se evaluó y conserva citas
literales. Se rechazan auxiliares libres en ese terminal, incluido el rationale
que causó028. El resto de rutas conserva su capacidad narrativa/recomendaciones.

La política admitida está codificada como una gramática documental, con términos
explícitos del corpus. Una política modificada o un escenario fuera de gramática
no se consideran equivalentes automáticamente. Su soporte requiere ampliación
justificada con pruebas; la ruta general no hereda garantías de este terminal.
El replay028 prueba selección y renderizado con entradas originales, no una
nueva respuesta del proveedor ni todo el espacio de preguntas conceptuales.

### Terminal de gasto desconocido en escenario incompleto

Implementado para una declaración completa de consulta vacía e ingesta incompleta
con pregunta de gasto cero y periodo coincidente. No acredita cobertura real ni
incorpora documentos generales como evidencia financiera. La premisa de gasto
cero es desconocida; el resultado explica qué falta sin afirmar un gasto positivo.
El terminal rechaza auxiliares del modelo y queda ligado al hash de la pregunta.
No toma prioridad sobre evidencia financiera del servidor. Otras formulaciones,
periodos contradictorios o datos añadidos retienen la ruta narrativa; esta ruta
cerrada no constituye una solución general de comprensión semántica. Replay026
y verificación de selección sobre calibración preservados fuera del repositorio.

## Auditoría de preparación para revisión — candidatofa5e9527, 2026-10-14

Esta tabla describe evidencias y pendientes; no modifica los criterios ni
convierte pruebas sintéticas en validación del modelo.

| Requisito | Evidencia comprobada | Estado / paso pendiente |
| --- | --- | --- |
| Reconciliar A/develop | merge-base confirma318a56f y c30a7d0 ancestros del candidato | Base actual incorporada; A/PR130 sigue abierta con tokenizer/reviews pendientes; revalidar si cambia |
| Identidades caso/repetición y ausencias | Baseline84/84 y candidato41/84 con hashes y agregados;43ausencias explícitas | Implementado; no declarar completa la campaña candidata |
| Contabilidad y procedencia | Ledger común, controles de hash/runtime y reserva que detuvo nuevas llamadas | Preservados; contador histórico conservador1.683584087 no es lectura viva actual |
| Línea base repetida |84recibos baseline,77completed/7failed conservados | Recogida completa; adjudicación independiente pendiente |
| Comparación emparejada |41muestras de e94:29fail→pass y regresión026r1 | Descriptiva/parcial; no acredita al candidato posterior |
| Correcciones semánticas |005determinista,026/028replay local,110/134pruebas focales y108gateway | Gramáticas cerradas; variantes no reconocidas conservan ruta general; aceptación no demostrada |
| Gateway y contrato público |12pruebas nuevas en108PASS; esquemas, streaming/final y rechazo de contradicciones | Probado con proveedor simulado, no ejecución final pagada |
| Linux | fa5e9527:244processor/64backendPASS,exit0; archivo e imágenes registrados | Superficies modificadas verificadas; no equivale a suite completa ni calidad real |
| SQL | fa5e9527:43PASS58.30s en instancia exclusiva limitada | Contratos SQL verificados; no prueba pérdida de red después deCOMMIT |
| Navegador | e23:historial real017/026/028 a1280/390px,6checks;028fuentedocumental visible,0mutaciones/0pageerrors | Lectura API/backend real verificada porIDdecampaña; falta nueva generación/streaming y aceptaciónN3; no hereda juicio semántico |
| Especificación e higiene | OpenSpec estricto JUP123 válido; higiene1609archivosOK | Comprobado en9f52; CLI instalada en checkoutauto, sin instalar red |
| Criterios y N5 | Tareas1.4/2.4/3.3 abiertas; pregunta al usuario sobre acuerdo existente | No inventar acuerdo, porcentaje ni dispensa de revisores |
| Revisión externa/publicación | B no publicada; borrador técnico y evidencia local disponibles | No integrar ni afirmar listo para aprobación mientras faltan los puntos anteriores |

Comandos de comprobación local:
- `git merge-base --is-ancestor 318a56f31828be50f8960860f69172f51046734d HEAD`
- `git merge-base --is-ancestor c30a7d0f28c04cae757b424222b34b232814303e HEAD`
- `../tfm-economicon-jup035-auto/node_modules/.bin/openspec.cmd validate jup-123-chat-semantic --strict --no-interactive`
- `node tools/jup-cleanup-check.mjs`

La comprobación de higiene necesitó ejecución fuera del sandbox para invocar
`git` (EPERM inicial); no hubo una modificación del control ni descarga de paquetes.
El ejecutable openspec no está instalado en este checkout: se usó el ya instalado
en el workspace. Los fallos iniciales de herramientas no cuentan como aprobados.


## Cierre de recogida del candidato e23e495b — 2026-10-14

N3 recogida por completo:84recibos/78completed/6failed, sin selección del mejor
intento. Todos VERIFIED_PUBLIC_SNAPSHOT y sin ausencias ni duplicados según el
agregador. Snapshot externo inmutable candidate-cap5-n3-complete con originales,
derivados, pruebas de coste y backupSQLite;manifestSHA de257archivos. El controlador
terminó conCOLLECTED y aceptaciónNOT_ASSESSED. No atribuir estas métricas a
aceptación semántica ni al código posterior sólo por compartir rama.

Contador final conservador2.078111791USD; reservas íntegramente retenidas1.601760USD
incluyen5fallos de coste desconocido yseed0.002. Cota conjunta3.679871791USD dentro
del máximo5 autorizado. Mantener esos costes/reservas en nuevas decisiones; no
reiniciar contabilidad ni asumir que los costes desconocidos fueron gratuitos.

La comparación por requisitos aún requiere juicios:13muestras locales provisionales
remapeadas por hashes idénticos,65pass/8uncertain/422unreviewed. Los revisores no
han acordado un umbral nuevo; N5 y adjudicación independiente continúan pendientes.
