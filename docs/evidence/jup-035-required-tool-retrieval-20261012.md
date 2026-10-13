# JUP-035: opciones conninfo de la recuperacion acotada

## Diagnostico comprobado

Recepcion historica preservada: operacion51dfed93-9027-4f8b-a403-6a8f5931db7c,
intento final07435a41-9e75-4ee4-858f-eb29840027b5. Completo tras dos429,
con omission retrieval_unavailable, evidencia/citas vacias y un par persistido.
No se reclasifica su VALIDATION_FAIL ni la causa no confirmada del envelope
anterior. El recibo no conserva la excepcion de recuperacion: no demuestra que
embeddings funcionara ni permite atribuir retrospectivamente todas las etapas.

Reproduccion no pagada en backend del stack autonomo-jup035-ai1536-20261011:
- Trusted peer presente, dimension1536 y transaccion read-only comprobada.
- Consulta ordinaria con vector sintetico: dos chunks, tenant-core correcto.
- Consulta acotada y aun SELECT1: ProgrammingError antes de conectar/consultar.
- Reconocimiento exacto de causa fija: invalid connection option "context".
  context es psycopg.AdaptersMap generado por SQLAlchemy, no opcion libpq.
- Excluido solo de comprobacion conninfo, conservado para AsyncConnection:
  ambas consultas devuelven dos chunks del tenant correcto. Fuente corregido
  ejecutado solo en proceso desechable; no instalacion, build o restart.

## Cambio minimo y evidencia

vector_store filtra context solo de la copia conninfo, sin tocar configuracion
efectiva, hostname/TLS/peer, filtros tenant/provider o politicas deadline/cancel.
ChatContext registra etapas cerradas configuration/embedding/vector_query/
candidate_validation/citations. Codigo fijo driver_context_option, categorias
ProviderError permitidas y fallback cerrado por etapa. ChatOperations propaga
UUID autenticados de operacion/intento al worker mediante ContextVar local.
Sin campos publicos nuevos ni valores, SQL crudo, claves, corpus, prompts o
mensajes arbitrarios de excepcion en los eventos. Omision publica sin cambios.

Expediente externo corrections/requiredtool-retrieval-20261012-*:
- sql-diagnosis.json, sql-isolation.json, driver-options.json: defectos previos.
- sql-fixed.json: correccion real SQL solo lectura; sin llamadas a modelos.
- design-spec: OpenSpec63/63 y guard solo especificacion canonica.
- red-focal: cinco FAIL significativos; guard solo suite contexto existente.
- green-focal: nueve PASS, incluyendo worker/cancelacion/timeout anteriores.
- green-affected-corrected:66 PASS/5 SKIP,1128 warnings retenidos,22.77s.
  SKIP: JUP086_VECTOR_TEST_URL ausente, no se acredita aislamiento real adversarial
  por esos tests. SQL sintetico propio es una comprobacion distinta acotada.
- green-affected exit4 anterior: nombre de test inexistente, no fallo de producto
  ni prueba Red; log conservado y seleccion corregida sin editar tests.
- mutation-focal: cuatro mutaciones en memoria detectadas por aserciones: context
  en conninfo, eliminar context efectivo, log de excepcion cruda y perder UUID.
  Guard sin cambios de producto. No sumar ejecuciones repetidas como casos unicos.

## 429 y limites

Dos429 de processor confirmados por validacion anterior; inspeccion propia de
logs gateway07:46:30Z-07:49:10Z no encuentra lineas429/motivos fijos retenidos.
No acredita ausencia de429 ni identifica origen/cupo: causa sigue no establecida.
No ajustes de limites, modelos, SDK, schema, prompt, retries o presupuesto.

No gasto, inferencia, admin, Git o publicaciones del desarrollador. SQL autorizado
fue solo lectura y vector sintetico: no acredita embeddings reales, relevancia
semantica/citas del recorrido completo o persistencia nueva. Revision independiente
y aceptacion focal pendientes. Presupuesto comunicado parent: .269134606 de .29,
restante .020865394, insuficiente para reserva conjunta .025; no llamada automatica.


## Aceptación real posterior — 12/10/2026

Este corte completa los pendientes del diagnóstico anterior; no convierte sus
fallos, omisiones o límites en resultados favorables retroactivos.

La revisión interna de conninfo y diagnósticos concluyó REVIEW_PASS, sin
defecto bloqueante. Conserva un P3 de sensibilidad de tests: el test instala
directamente el scope de diagnóstico y no detectaría la eliminación del wrapper
de producción en ChatOperations. El wrapper fue inspeccionado y es correcto;
la mejora sugerida no es un defecto de producto ni se implementó en este cierre.

La validación interna posterior ejecutó una sola generación pública nueva del
caso JUP-069-010: completed en 16,703 s, un intento, sin retry. El contexto
original tenía evidence_ids vacíos. Después de la llamada nativa
search_documentation se recuperó corpus autorizado por tenant, se continuó con
resultado autenticado por HMAC y tool_choice none y se obtuvo respuesta estricta.
El manifiesto final contiene ocho identificadores de evidencia y 1.788 tokens
variables. Se persistió exactamente un par pregunta/respuesta; result e historial
recién consultados conservaron IDs, contenido y citas, sin operación activa.

El ledger acredita dos llamadas LLM y un embedding: 9.365 tokens de entrada y
455 de salida agregados por ambas llamadas LLM, 13 tokens del embedding.
Coste LLM 0,0060868125 USD; embedding 0,00000026 USD; total 0,0060870725 USD.
No se ejecutaron nuevas llamadas para redactar esta evidencia.

El fragmento citado pertenece al documento
415159ab-c602-447b-89cd-a92aac8096c8, chunk 1, fuente
business-rules.economicon-mvp, tenant-core, vector de dimensión 1536. El texto
completo almacenado en SQL respalda las cinco etiquetas y sus significados.
El preview es abreviado: no prueba por sí solo la tabla completa. Las reglas
owner como equipo y ausencia de PII están en otro chunk no citado; no se afirma
que la cita única respalde todas las frases de privacidad de la respuesta.
metrics y recommendations vacíos, period null y subscriptions vacías: el corpus
no adquirió autoridad financiera. El endpoint de evidencia financiera devuelve
items vacíos; las citas documentales se conservan en los metadatos del resultado.

Fuentes originales conservadas: required-integration-retrieval-review-20261012.md
y validador-requiredtool-retrieval-20261012-report.md, junto con los recibos
requiredtool-retrieval-20261012-focused010-1122, audit/reopen/ledger y settled-1126
del expediente externo corrections-runtime. Operación
c9fb8dee-2d50-4e6b-b245-d8a14a2d14ce; intento
4d22147b-2f7e-4088-acf1-6f29b308ddb8. Ejecución iniciada el 12/10 a
10:23:25.955 UTC sobre HEAD 954b44298ccd94994f3ac420a3aec55c32eeb521 más
delta local congelado; no fue una ejecución sobre el nuevo commit de entrega.

Referencia original de validación conservada, SHA256
46fc8e444711d0e8406a6bc117ee501d66a214dd228ae3a7f30d05bdaafb66a2.
Verificación local del validador 10:25:40 UTC; PM comunicó control independiente
PASS a 10:31:34 y nuevamente a 11:06:45 UTC antes del commit autorizado.
Estos controles detectan cambios; no acreditan aislamiento técnico de lectura.
La importación posterior requiere su propio checkpoint y controles independientes.

VALIDATION_PASS se limita a este ensayo y al alcance descrito. Corpus sintético
realmente almacenado, no datos de producción ni validación oficial Microsoft.
No full28 actual, JUP-070 formal, adversarial cross-tenant/user, cancelación SQL
remota forzada, build limpio o review humana. Los cinco tests de aislamiento
omitidos por falta de JUP086_VECTOR_TEST_URL siguen omitidos. Los informes
originales conservan sus estados pendientes anteriores y no se reescriben.

Véase [conciliación de la entrega](jup-035-delivery-reconciliation-20261012.md).
