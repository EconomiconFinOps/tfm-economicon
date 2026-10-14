JUP: JUP-123

## Context

B preserva el flujo que ya recupera documentación en servidor y genera draft/final
sin herramientas nativas. Retirar tools no es una nueva solución pendiente.
El scorer previo conserva 253 juicios históricos y nueve incertidumbres.

## Decisions

1. Reconciliar A por bloques usando la base Paris f63c150 para adiciones paralelas;
   mantener semántica B y controles de activación, cancelación y fecha de A.
2. N=3 inicial, N=5 de confirmación según criterios obligatorios y presupuesto.
   Sin selección del mejor intento ni omisión silenciosa de fallos técnicos.
3. Identidad por campaña, caso y repetición; banco y corpus inmutables. Conservar
   commit, hashes, entradas, fragmentos realmente usados, parámetros y costes.
4. Contabilidad viva y reserva conservadora antes de inferencias. Tope acumulado
   de 5 USD (ampliación explícita del usuario el 2026-10-14 desde 2 USD),
   incluyendo intentos fallidos y servicios auxiliares facturables.
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
