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
