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
