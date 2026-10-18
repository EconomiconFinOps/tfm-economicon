# Evidencia de desarrollo — JUP-127

JUP: JUP-127
Trello: https://trello.com/c/AG5fAbl3

Fecha:17/10/2026. Rama `feat/JUP-127-contextual-hybrid-retrieval`, base reconciliada
`3dc2268a0e03c89e09a4c051dbe69e02edb4beee` con develop1de41b90. Es evidencia del
responsable técnico; no representa validación humana ni publicación.

## Candidato y separación

Se preservan F1/F2/F3 del motor. El PM separa de la entrega el delta exclusivo E:
15archivos modificados y11añadidos, copia exacta externa antes de retirarlos;
manifiesto de custodia SHA256 `025ed4eaa4b1258048b3ba462144aade5eb881b2bef3a3fce904ad05aba4d8f3`.
No se portan otras features del chat. El perfil D, su descriptor de ejemplo y la
[guía](../rag-d-activation.md) completan la operación sin cambiar OFF general.

Manifiesto v1 anterior a formalización:1813archivos,
SHA256 `c84184e86e164ee499b7ebd89af2733f9153e9073ba2dcfb42f409594ba8d2ad`.
No fue evaluado: la rama e identificación oficial se incorporan después y el
candidato final se fija de nuevo antes de recibir referencias PM independientes.
No atribuir el delta sin commit al SHA base.

## Compatibilidad local con PR #134

Corrección acotada del 18/10/2026 sobre `bc9f6df7641990820696c710642ae9f93efe99f8`,
en copia auxiliar detached. Referencia de fase 2: `2de57bd0d4cef17556d86a74add4e75776dc52ab`;
se adaptan los ajustes de `b4783e77` y `d8a3fdf9`, no sus archivos completos.
El delta posterior de `3591ac7a12419de0780faea167dce44a1536d131` corrige la
limpieza ATX y limita el fallback a la posición de la columna metadata. Su paquete
de ocho rutas se comprobó por hash antes de adaptar sólo código/pruebas pertinentes.
C13 y el extractor Markdown ya coinciden y no se modifican.

Producto: `normalized.py` limpia sólo el título ATX; ambas rutas de `vector_store.py`
conservan título/sección manual y el recorrido legacy tolera exclusivamente
ProgrammingError SQL42703 cuya posición señala `dc.metadata` o `metadata` antes
de 003, tras rollback. Errores de provider u otras columnas no producen warning
ni reintento. La misma instancia utiliza
metadata al aparecer la migración. `EmbeddingTokenizerUnavailable` conserva el
diagnóstico de recurso/versión/hash al cruzar el límite de arranque y sigue siendo
ValueError. No cambian tokenizador, recursos, modelos, contratos públicos o deadlines.

Primera adaptación, anterior a `3591ac7a`: 100 backend afectados con PostgreSQL/pgvector real y generación
controlada; 28 processor de tokenizer/contexto/reproceso/publicación; nueve focales
SQL de correlación input/vector/caché, snapshot y concurrencia. Hay solapamiento de
módulos entre pasadas: no se suman como una batería única. Se conservan los ocho
fallos backend y dos processor reproducidos antes de la corrección.

Tras adaptar `3591ac7a`, nuevas comprobaciones focales: 23 de ATX/contexto,
27 de citas/SQL003/aislamiento y dos SQL de correlación contextual/plain, todas
conformes. Se conservan también dos rojos adicionales: timeout acotado del título
hostil y reintento incorrecto ante provider42703. Las cifras anteriores no se
presentan como repeticiones sobre estos bytes ni como dictamen independiente.

Las nuevas pruebas están en `test_new_document_citation_titles.py`,
`test_vector_metadata_migration_order.py` y los módulos processor existentes de
tokenization, space_context, generations_pgvector y reprocess_document. También
se añade `test_parent_metadata.py` de fase 2 con sus bordes y subproceso acotado.
Los recorridos backend de MD/manual ejecutan el processor con el mismo intérprete:
requieren dependencias de ambos servicios y el tokenizer externo. La CI actual
no define `JUP086_VECTOR_TEST_URL`; sus omisiones no acreditan estas pruebas.
La ruta legacy usa mock8D y la generación verificada mock1536D. Para SQL
se requieren las URL de pruebas desechables que documentan las fixtures; el recurso
cl100k externo debe prepararse con el builder fijado. No apuntar a bases de producto.
Cubren manual/Markdown sin título precargado en legacy/dense/hybrid, metadatos
antes/después de 003, cancelación, errores SQL ajenos, caché contextual frente a
plain y conservación del índice activo ante recurso ausente.

El cambio de título puede producir un nuevo hash contextual; la caché se comprueba
contra el input exacto, tokens, tenant y espacio. Build sigue leyendo metadata ya
persistida: no se promete limpieza retroactiva. No hubo llamadas reales, gasto,
campañas, migración de datos existentes, activación, reconciliación, commit o push.
Los dictámenes independientes y controles originales de este delta se entregan
al PM por separado; integración, conflictos con develop y roles humanos conservan
su fase y no quedan satisfechos por estas pruebas.

## Ejecuciones nuevas y riesgos cubiertos

| Comprobación | Resultado observado | Alcance |
| --- | --- | --- |
| Processor: generaciones PostgreSQL/pgvector |35PASS|Snapshot/CAS/rollback, fencing, permisos/tenant, publicación, caché concurrente y FTS/F3 reales. |
| Processor: contexto/lotes/reprocesado/chunking/contratos |117PASS|Preparación y límites deterministas, operador y contenido preservado. |
| Backend: política/config/inicio/recuperación/contexto/citas/historial |164PASS|Compatibilidad de contrato, literales y fuentes. |
| Node: doctor/Compose/CD/gobernanza/políticaPR |173PASS|111conformes iniciales y62doctor con dependencia propagada a hijos; no sumar reruns. |
| Node: CI |14PASS|Comandos existentes y nuevo colector conservados. |
| Colector |48PASS|Contrato público y rechazo de redirecciones, sin inferencia. |
| Perfil D |Conforme|Renderizado Compose real; doctor positivo y rechazos por mapping/deployment vacíos o dimensión incorrecta; dependencias/puertos simulados, no readiness de servicio. |
| CD |63 PASS únicos|61 conformes en Windows con Compose real y 2 POSIX conformes en Linux; los 3 SKIP iniciales quedan cubiertos por ejecuciones posteriores. |
| Declaración Grafana/.env |30 PASS|Se conserva declaración exacta/vacía/única/posición y cinco literales únicos; no se limita el crecimiento independiente del entorno. |
| OpenSpec/trazabilidad |79/79 y PASS|Incluye change JUP-127; controles de especificación, no aceptación ni CI remota. |

Pruebas reproducibles existentes: processor `test_embedding_generations_pgvector.py`,
`test_embedding_space_context.py`, `test_embedding_batch.py`, `test_reprocess_document.py`,
`test_structural_chunker.py`, `test_chunk_contracts.py`; backend `test_retrieval_policy.py`,
`test_verified_embedding_configuration.py`, `test_embedding_startup_wiring.py`,
`test_retrieval_contract.py`, `test_retrieval_failures.py`, `test_retrieval_traceability.py`,
`test_chat_contiguous_context_jup035.py`, `test_chat_context_assembly_jup035.py`,
`test_structured_citations.py`, `test_chat_history_context_jup035.py`. Consumidores
mediante `local:test`, `docker:validate`, `ci:check:test`, `cd:test`, `pr:check:test`,
`repository:governance:test` y `chat-collector:test`.

Entorno propio:Python3.12.13,PostgreSQL17/pgvector,tmpfs, código sólo lectura y
sin red externa/puertos publicados; retirado. Node24.17 local frente a22 de CI:
no sustituye CI remota. Dependencia yaml2.9.0 ya instalada, resuelta externamente;
ningún cambio de producto para hacer pasar el entorno. Se conservan fallos ACL,
loopback y dependencia originales junto con sus pasadas corregidas. No se repite
batería completa ni campañas por rutina: selección focal por encargo PM.

## Corrección de consumidores heredados

El chequeo real de CD falló antes de la corrección: una raíz nueva no generaba
`GRAFANA_EVALUATION_DB_PASSWORD`, obligatoria en Compose. El fallo original y su
diagnóstico se conservan. Se reutiliza el ajuste autorizado por PM desde el commit
local `4cf7782dedd50c65dd68b736ee9d1e356ec9a5bb` (procedente de `d4c545e7`): generar
sólo cuando falta, validar y conservar el valor configurado, con idempotencia.
Se portan pruebas focales sin retirar las aserciones de flags RAG/mapping de fase3.
Preparación real de raíces nueva/heredada y ambos slots conforme, sin desplegar.

También se reproduce el fallo heredado del test de `.env`:138 líneas frente a103
fijadas. Se reutiliza su corrección semántica de la misma fuente, conservando
la variable Grafana exacta, vacía, única y situada tras la contraseña de admin,
y los cinco literales relevantes únicos; no se fija un conteo global ajeno al
contrato. Las30 pruebas del datasource pasan. No cambia la configuración efectiva
del dashboard ni se rotan secretos compartidos.

## Matriz de los doce criterios oficiales

| Criterio | Evidencia técnica y límite |
| --- | --- |
| 1. Identidad del espacio | Configuración/lotes/espacio y rechazos de mapping/deployment; identidad remota actual pendiente de acreditación del operador al activar. |
| 2. Contexto separado y determinista | Suite de contexto y chunking, límites/avisos; descriptor original D e invariancia de content. |
| 3. Lotes/cache compatibles |117 processor y35 SQL incluyen lotes completos y caché por tenant/espacio/texto, carreras y ganador canónico. |
| 4. Dense/híbrido/literales |35 SQL y política backend, perfil efectivo, ocho consultas D guardadas; no interpretación de fórmulas. |
| 5. Generaciones/CAS/fencing |35 SQL: snapshot completo, permisos/catálogo, reanudación/constructor obsoleto, publicación, rollback/retención. |
| 6. Activar D con legado recuperable |Guía y negativos de flags/cabeza; ninguna activación compartida real se declara realizada. |
| 7. Concurrencia/tenant/plazo/cancelación |35 SQL y contratos backend, F1/F2 por hash y fuente actual; sin nueva inferencia por conflicto SQL. |
| 8. Contratos chat sin calculadora E |164 backend y custodia exacta del delta E; fuentes/citas/historial preservados, prompts/generación intactos respecto base pre-E. |
| 9. PG/Compose/CD/doctor |SQL real, renderizado perfil, doctor,63 CD y30 datasource; sin servicios productivos ni nuevos accesos. |
| 10. Campañas/resultados/coste |Custodia A–D/E/J5 diferenciada, hashes y corte financiero; evidencia histórica no es ensayo actual. |
| 11. Evaluadores distintos |REVIEW_PASS y VALIDATION_PASS locales sobre D-v2; originales íntegros y MISMAS referencias PM favorables al inicio, retorno y prearchivo. Ver cierre local debajo. |
| 12. Formalización y PR |JUP-127, change, ADR, continuidad/evidencia y mensaje PR preparados; cierre local aprobado por Paris. Archivo, Git/publicación, CI y reviews humanas conservan su fase. |

## Replay nuevo con datos históricos

Dump original D SHA256 `4f47e4541561869606794cd7a3ea15b402d8ed3445875bc1bb118fcddf0b07dd`
restaurado mediante pg_restore sin errores sólo en la base temporal propia.
Ocho consultas guardadas, cuatro por cada uno de los dos tenants, con texto/hash,
vector, captura y plan originales. Código actual devuelve ocho órdenes iguales
a esas capturas y conserva selección/citas. Cinco negativos/compatibilidad:
falta de cabeza, contextualOFF, hybridOFF, plan de otro tenant y modo legacyOFF.
Provider cerrado: cualquier cache miss aborta;0llamadas y0USD nuevos. No mide
generación, calidad de respuesta, estado del gateway actual ni mejora global.

## Campañas y límites conservados

A–D permanecen en custodia externa íntegra con272casos terminales y sus recetas,
raw,capturas y contabilidad. D histórica:68/68respuestas,64/68aceptaciones asistidas;
mejor contexto adicional, menor cobertura original que A/B. F3 corregida y la
base reconciliada distinguen este candidato. Los casos J5 y los análisis semántico
y de fragmentos permanecen diferenciados en el informe de campañas entregado al
liderazgo; no se recuentan como pruebas propias de esta formalización.

E cancelada por Paris:47terminales (38respuestas/9fallos),17noejecutados. Preparación
parcial de la secuencia48 no admitida no cuenta como fallo pagado. Gasto E válido
0.1581108250USD; preparación/diagnóstico/preflight E0.0105444175; histórico previo
0.7665115175000000000008; acumulado conciliado0.9351667600000000000008USD. Son recibos
del gateway cotejados, no factura independiente del proveedor. Reservas/unknown y
en vuelo0; recursos E retirados. Nada de ello reanuda E ni autoriza nuevas claves.

Fuentes externas conservadas: manifiesto D histórico
`c9ab6905852c6d3635abb59e60dda8d651e8a79b592316c7be176367bd45eda7`, readinessD
`037e16470871f981bf4b31d2fbe2064ffec5179444b0f84126092613b4168265`, cierre canceladoE
`724e80665d33bab58d39863bcf81d3118614537af39a4c11327eac4581c6f0c0`, informe de campañas
y análisis T-800 conservados por liderazgo. No se incluyen secretos ni raw privados
en Git; sus manifiestos permiten al liderazgo verificar procedencia exacta.

## Cierre técnico local aprobado — 17/10/2026

Candidato evaluado D-v2, sin commit sobre `3dc2268a`, manifiesto de 1820 archivos
SHA256 `cace8b0774d87b7d5d416ed5769bfffe1b35f9701490d60b1e613b92861aecc2`.
Revisor y Validador distintos, con contextos y recursos separados, entregaron:

- REVIEW_PASS técnico, original `independent-revisor/informe-original.md`, SHA256
  `a184d7f8b3e7731a3162dfde395d57a56705328eb1300230deec6d855dffcf14`.
- VALIDATION_PASS funcional técnico-operativo local, original
  `independent-validador/informe-validacion-D.md`, SHA256
  `688a1a26dd83900e7c55582b6611395fd7913cca755885f5669c5c7095845164`.

Ambos realizaron pruebas propias, conservaron sus incidentes de preparación y
declararon reutilización y límites. El Validador ejecutó también replay D propio,
verificó 51/51 fuentes del informe de campañas, 8/8 de receta y custodia E íntegra.
No quedan bloqueos técnicos o funcionales locales demostrados en ese alcance.
Los originales y sus borradores íntegros permanecen en custodia externa del
liderazgo; no se reescriben sus dictámenes ni los adversos anteriores.

Referencias ORIGINALES PM anteriores al despacho, conservadas sin sustituirlas:
Revisor `pm-revisor-D-v2-original.json`, SHA256
`b6f8bc88bbe825042c646da19f0a875860c3d721247c454e6da89f585150ac9f`;
Validador `pm-validador-D-v2-original.json`, SHA256
`82867d5e06881ee3a56404af83cc32f581c9cb4e00b22aa8f7690e546739570c`.
Roles y principal cotejaron al retorno el candidato y esas MISMAS referencias,
sin discrepancias. El PM repitió independientemente el retorno a las
13:58:53/57 UTC y el cotejo prearchivo a las 14:06:33/38 UTC: ambas referencias
`ok:true`, sin violaciones. Además cotejó/custodió los 20 artefactos seleccionados,
manifiesto SHA256 `2be9ba8ded747d7707590322db905d954aff5e257235d644bc4f01ac07dc4aaf`.

No se modificó el candidato ni Git durante la evaluación. Las herramientas
existentes de CD/perfil generaron datos/configuración y copias temporales
inalteradas fuera del candidato; no se editó código de copias para obtener PASS.
Recursos PostgreSQL/ejecutores propios retirados, tmpfs descartados y cero
contenedores propios restantes, sin tocar recursos compartidos. La detección
conductual no demuestra aislamiento técnico ni ausencia de ediciones transitorias
restauradas. Cero llamadas y 0 USD nuevos; E sigue cancelada.

El PM presentó resultados y mensaje PR; Paris aprobó el cierre y ordenó
«archiva, commitea y pr», autorización transmitida por PM el 17/10/2026 a las
15:06:24 Atlantic/Canary. Este apartado cierra sólo el hito local. No acredita
calidad nueva de respuestas, gateway actual, activación compartida, participación
humana, archivo ya ejecutado, CI remota o publicación. PM gestiona archivo/Git/CI/PR;
los mismos evaluadores comprobarán la vigencia del delta documental tras archivo.
Las revisiones humanas y la aportación efectiva de los roles siguen su proceso.


## Archivo ejecutado y adaptación documental — 17/10/2026

El PM confirmó a las 15:10:10 Atlantic/Canary la ejecución correcta de OpenSpec1.8
`archive jup-127-contextual-hybrid-retrieval --yes`, con validación y promoción
activas. Change en `openspec/changes/archive/2026-10-17-jup-127-contextual-hybrid-retrieval`
y doce requisitos en `openspec/specs/verified-contextual-retrieval/spec.md`.
Validación previa al archivo:79/79, ejecutada por PM. Se adaptan los enlaces
relativos del design archivado hacia docs y los de ADR/continuidad hacia el
change. El motor, perfiles, contratos, pruebas y base no cambian por este paso.
Se congelará el estado postarchivo para adenda de vigencia de los mismos roles,
con dos referencias PM nuevas; las originales anteriores y sus verificaciones
permanecen conservadas. No se atribuyen todavía commit, push, CI remota, PR o
participación humana, ni se afirman aplicados fixes posteriores de JUP-124/125.

## Corrección focal tras CI39040100565 — 17/10/2026

PM publicó `6ba7d299c6809408581368bb29fc0394849a9aac`. La CI posterior detectó
9 fallos backend y 2 processor; se conservan sus logs originales y el dictamen
adverso. No se creó la PR. Los PASS y adendas anteriores conservan su alcance;
no se extienden automáticamente al candidato corregido.

Se reproducen exactamente los once fallos sin red: backend 9FAIL/120PASS/17
omisiones y processor 2FAIL/51PASS. Una traza externa observa `TypeError` en
`assistant.py:273`: la fixture sustituía la clase de origen usada por `isinstance`.
Los constructores se simulan ahora en `app.main`, donde startup los utiliza;
la prueba de importación mantiene su guarda previa y sus aserciones intactas.
No se modifica el manejo de errores ni la recuperación de producción.

Las otras dos pruebas contaban llamadas individuales aunque el lote generaba y
persistía los cuatro vectores correctos. Ahora comprueban lote único con los
chunks exactos, vectores y orden, ausencia de efectos al reentregar y proveedor
individual compatible. El rechazo de evidencia comprueba ambos métodos sin
llamadas. No se cambia el pipeline para acomodar las pruebas.

Comprobaciones nuevas, sin sumar reruns como casos únicos:

- Backend, cuatro módulos afectados:129PASS/17omisiones CockroachDB, sin servicio
  opcional; los nueve casos originalmente fallidos pasan.
- Backend, límites de secretos e inicio, recuperación/contexto/citas/historial:
  179PASS.
- Otros consumidores directos de la fixture compartida:651 passed, 151 skipped, 6021 warnings in 49.06s.
- Processor, ingesta y reentrega:55PASS, incluidas las dos variantes individuales
  añadidas; contexto/lotes/reprocesado/chunking/pipeline:126PASS.

Contenedores propios desechables, fuentes de sólo lectura y red deshabilitada;
sin nuevas llamadas ni coste. Motor F1/F2/F3, receta D, opciones por defecto,
base y dependencias PR133/134 intactos. Originales, logs y diagnóstico quedan
custodiados fuera de Git en `ci-fix-39040100565`. Se congela el candidato para
dos referencias PM nuevas y reevaluación por los mismos roles independientes.
Commit/push, CI remota posterior y PR por navegador corresponden al PM; todavía
pendientes. No hay nueva campaña, activación compartida ni participación humana
acreditada por esta corrección.

## Integración local de la base final — 18/10/2026

Composición en copia nueva: checkpoint local `27a69cb0da1935dd01919da7d8810862b3bed554`
(padre `bc9f6df7641990820696c710642ae9f93efe99f8`) con base de fase 2
`f8dd03bc719429af70b1b5d86c1565071b76876c`, que incorpora develop
`0e686f9180d5ce195391e634a79ef2d6d3182af6`. No se atribuyen los cambios
sin commit al checkpoint ni se extienden los dictámenes de la copia anterior.

Se preserva el lector verificado y se adapta la expansión de vecinos y políticas
de B al tenant, generación y espacio capturados. Los vecinos pueden estar fuera
del umbral/pool semántico inicial; no se pide otro embedding y el pool final
sigue limitado a veinte. Políticas: ambigüedad de dos documentos, límite de
65536 bytes antes de transportar el texto, secciones de 4096 caracteres y seis
fragmentos más centinela. Se mantienen posiciones literales únicas, los dominios
canónico/legacy y el máximo de 64 tramos. No hay rescate con datos legacy mutables.
La fixture de operación negocia ahora `server-documentation-v4`, el protocolo
de la base incorporada, en lugar del nativo antiguo.

Comprobaciones propias sobre esta composición, sin sumar selecciones solapadas:

- Expansión verificada nueva: 22/22, SQL real; vecinos fuera del pool, snapshot
  frente a modificación legacy, políticas/definición complementaria en dense e
  hybrid, coordenadas canónicas/legacy, ambigüedad, bytes, fragmentos, literalidad,
  consulta acotada por deadline y máximo de tramos.
- Citas nuevas, fallback 003, posiciones estructuradas, políticas legacy y vecinos:
  55/55 en la primera selección; la ampliación de expansión anterior se repitió
  por cobertura nueva, no se considera otro conjunto único.
- Contrato SQL y aislamiento por tenant más expansión anterior: 34/34 en otra
  selección parcialmente solapada.
- Processor, tokenizer/contexto, metadata padre, generaciones/caché y reprocesado:
  83/83, sin omisiones.
- Negativos SQL externos de aceptación sin rescate legacy: 8/8 sobre la copia
  nueva; el auxiliar anterior se conserva idéntico, no se traslada su PASS antiguo.
- Consumidores unitarios de recuperación y políticas: 75/75.
- Operación pública con SQL real (cuatro combinaciones de preparación/modo),
  contexto y vecinos: 49/49. Citas y metadatos de generación persistidos sin
  conceder autoridad financiera a la documentación. El generador es controlado.
- Contrato de recursos processor y paridad de módulos: 18/18. Bundle real y
  diagnóstico backend: 6/6. Ambas huellas de código de políticas coinciden con
  `f53ea3d187cc2ace2f86000c630d290396fb24b86dcb5e6ac409905c91dfd57c`.
- OpenSpec estricto 80/80; gobernanza 26/26; trazabilidad de nueve changes e
  higiene conformes. Sin cambios Git del ejecutor.

Se conservan el rojo inicial de integración y los fallos de preparación de la
primera selección: un documento que debía quedar fuera se publicó antes de
capturar la generación y el caso de bytes excedía primero el límite de chunk.
Se corrigieron únicamente esos datos, sin ampliar límites ni modificar aserciones.

El fix de recursos publicado de fase 2 `fdcccf8e2171ba755b5a998ba9fb5a737dba2a91`
se incorpora tras contrastar el contrato efectivo; los dos archivos de producto
y tres documentos completos coinciden con su delta, y su fila de continuidad
se conserva junto a la de JUP-127. No se cambian loader, módulos, prompts,
versiones ni controles. CI de ese fix aún en curso según PM al entregarlo;
sus dictámenes no se heredan. El compuesto requiere congelación con dos
referencias PM nuevas y sus evaluaciones independientes propias.
No se declara todavía cierre, CI del compuesto, aceptación remota ni roles humanos.
Herramientas de prueba fijadas y fuentes de sólo lectura en contenedores aislados,
PostgreSQL/pgvector real; generación y embeddings simulados, cero llamadas o gasto.

### Corrección del consumidor tras la evaluación del compuesto

Los originales sobre `552c23d3` se conservan: REVIEW_FAIL P2 del consumidor de
métricas (258 pruebas conformes no cubrían ese contrato) y NEEDS_CONTEXT de la
validación (146 casos conformes, frontera de sección pendiente). Sus dos guardas
originales y el retorno independiente del PM fueron conformes antes de modificar
el candidato; no se sustituyen por referencias nuevas para ocultar el resultado.

El backend marca expresamente las admisiones posicionales y de política. La
proyección de métricas conserva distancia y pareja generación/espacio, o ambos
nulos en legacy, y valida su coherencia con la ejecución. No atribuye a FTS una
expansión ni admite una distancia densa sin procedencia explícita fuera del umbral.
El control de tenant/proveedor/generación y los límites de recuperación no cambian;
la validación offline no se presenta como verificación criptográfica del origen.

Se conservan los rojos nuevos. Las tres suites del consumidor terminan con
227 PASS / 1 omisión por Node ausente en la imagen Python; ese único caso de
paridad Python/Node pasa por separado en el host con Node instalado. Tras los
últimos controles de tipos, los 15 casos nativos y sus subcasos pasan. El
productor SQL y adaptador/validador reales pasan 46 casos, incluidos ocho de
4096/4097 preparados externamente por el principal. Los diez recorridos SQL
de vecinos/políticas repiten el CLI real con sus resultados capturados: acepta
las expansiones identificadas y rechaza el mismo dato al quitar la procedencia,
sin relajar el umbral. Las selecciones solapadas no se suman.

No hay cambios de modelo, prompt, regla financiera, recursos/pins, dependencias,
API pública o receta. La reevaluación afectada de esta corrección se entrega
por separado, después de nuevas referencias PM; los dictámenes adversos anteriores
no se reescriben. Cero inferencias y gasto; no se repite una campaña.


## Correcciones solicitadas por Lucía sobre 57fe7c57 — 18/10/2026

El humano autoriza una excepción puntual de implementación asistida para los dos
bloqueantes de la review `PRR_kwDOT_7PXs8AAAABS6ChrA`. Alejandro aporta las
correcciones asistidas, Paris conserva liderazgo, Lucía revisión y Víctor validación.
Este trabajo no es un dictamen independiente ni una aceptación del candidato.

La comparación literal aplica NFC y casefold sin perder límites de tokens,
operadores ni unidades. La elegibilidad de anclas queda limitada al rescate léxico:
el carril denso conserva todos los candidatos de la generación/tenant capturados
con distancia inclusiva0.6. Las comparaciones no soportadas continúan sin rescate
léxico por otro identificador. No se cambian modelos, vectores, prompts, opciones
por defecto ni generaciones persistidas.

Esto **cambia la receta D de recuperación**. Las cifras de campañas y las revisiones
históricas se conservan con sus bytes y alcance; no acreditan el comportamiento
corregido ni una mejora de calidad. No se ejecutan nuevas inferencias ni campañas.
Las observaciones no bloqueantes de esa review quedan fuera de este ajuste.

Evidencia propia local: baseline de política27PASS/3FAIL en los tres nuevos controles
de normalización; candidato30PASS. Contrafactual y logs fuera de Git en
`materiales/07-evidencias/PR139-correcciones-20261018/`. Nueve casos PostgreSQL/
pgvector reales dan **6FAIL/3PASS en57fe7c57 y9PASS corregidos**, con idénticas
aserciones. Cubren identificadores en distintas cajas, NFC/NFD, y/o, fechas,
borde exacto0.6 (vector entero2,4,2,1; exclusión0.599999), aislamiento y no-rescate
comparativo. El SQL usa generaciones construidas/activadas por el processor real
con proveedor mock, FTS real y vectores sintéticos; no mide calidad ni uso real.

Destino DockerServer expresamente autorizado por el humano el18/10, fuentes .py
con allowlist y hashes (sin documentos ni credenciales). PostgreSQL17.11 imagen
`pgvector/pgvector:pg17` sha256cf134a767f474095eeba57e0117be8e568e011a63f33fbf252f14c9b760f8e6f;
Python3.12.13 y tokenizador0.14.0 fijado en runtime existente. Cada contenedor
propio limitado a1CPU/1GB, PostgreSQL sólo loopback y tmpfs; retirada de todos
confirmada. Dos errores iniciales de harness (dependencia pytest y cwd) se
conservan como errores, no como fallos del producto ni ejecuciones válidas.

El descriptor de espacio y los vectores no cambian: las huellas identifican la
preparación/embedding, no estos bytes del lector. `literal_context_v1` conserva
sus guardas completas; corregir su aplicación no migra el índice ni crea un
proveedor/modelo nuevo. El SHA del código fija la variación de recetaD a revalidar.
OpenSpec80/80PASS. CI remota y dictámenes humanos del candidato siguen pendientes.
No hay publicación ni aprobación nueva por este registro local.
