# JUP-035 — historial canónico JSONB y transición propuesta

**APROBACIÓN HUMANA DEL DELTA JSONB — Paris vía Project Manager 10/10/2026 09:15:41 (Atlantic/Canary): «si hazlo».** Aprobado `jsonb-history-design.md` entregado03:20:56: esquema por conversación, final conjunto pregunta/respuesta, alternativas sin duplicar pregunta, migración003/backfill conservador y tabla histórica sin rutas activas. Autoriza adaptación Red→Green→mutación y pruebas afectadas; ventana SIN escritores y migración únicamente LOCAL AISLADA. Sustituye el estado pendiente de ejecución de esta misma propuesta; no acredita implementación ni aceptación. Conservar IDs/citas/metadata/precisión, operaciones separadas y fuente JSONB única; retirada activa exigida a Revisor, Validador y cierre PM. Presupuesto compartido0,20EUR desde02:54:46 permanece, readiness/cota/reserva antes de gasto. No producción/remoto/Git/publicación/archivo/destrucción. Versión aprobada exacta y hashes conservados externamente por TL.


**CAMBIO VIGENTE DE HISTORIAL — Paris vía PM 10/10/2026 03:01:32, con control independiente añadido03:03:01 (Atlantic/Canary).** Historial canónico: un JSONB por conversación; pregunta y respuesta completa se añaden juntas al finalizar, sin cambios al enviar ni por deltas. [Contrato concreto y migración propuesta](jsonb-history-design.md). Sustituye el mecanismo de filas `messages`, su desempate temporal y la ausencia de backfill del diseño anterior; originales/decisiones históricas conservados. Preferencia JSONB aprobada; esquema003/backfill y reescritura material pendientes de validación/despacho, SIN implementación de este delta. Los demás contratos funcionales permanecen. Nueva autorización PM02:54:46 permite pruebas reales necesarias por ruta aprobada hasta0,20EUR acumulados compartidos, con coste acotado/contador antes de llamar; sustituye únicamente la prohibición de gasto anterior. No amplía Git/publicación/remoto/archivo.

# Concreción externa del delta mínimo JSONB

Complementa el diseño anterior conforme TL10/10/2026 03:06:59. No implementación ni autorización material de migración.003 disponible por lectura local: sólo001_initial.py y002_chat_operations.py en migrations; confirmar de nuevo al abrir ciclo, sin gestionar Git. GET actual intacto; cursor/límites nuevos FUERA delta mínimo. Medir crecimiento/contención como riesgo, sin prometer escala ilimitada.036 sólo dependencia de integración ante incompatibilidad concreta según PM23:42:59, nunca bloqueo automático del035aislado. Legacy inconsistente aborta/error saneado/conservación/elevación del caso real, sin preguntar decisiones hipotéticas.

## Forma concreta, turnos y retry

`jsonb-history-shape-proposal.json` es ejemplo SINTÉTICO del documento canónico, no fixture aplicado. `schema_version` entero exacto1; `identity` tres strings no vacíos iguales al parent autorizado (no confiere permisos); `revision` entero no negativo de commits finales; `next_ordinal` entero no negativo; `messages` lista ordenada. Rechazar bool como entero, ID duplicado, ordinal ausente/duplicado/no contiguo, versión desconocida, identidad discordante o documento malformado. `next_ordinal == len(messages)`; el índice de cada elemento coincide con ordinal. Una finalización única incrementa revision UNA vez; observar/duplicar completed no la cambia. Documento vacío = revision0,next_ordinal0,messages[].

Cada elemento: ordinal entero; id string no vacío y único; role string original; author_id string original oNULL; question_id string oNULL; origin enum completed|legacy; content string exacta; metadata JSON original íntegro; created_at string RFC3339UTC con seis decimales, el mismo instante microsegundo SQL original. Para elementos nuevos role sólo user|assistant y metadata objeto conforme contrato; para legado conservar role/metadata originales válidos aunque no formen turno elegible. No aceptar metadatos originales como identidad/autorización. Retener authorNULL legítimo de assistant histórico sin inventar autor.

Turno nuevo = user con question_id=id seguido de assistant con question_id igual a ese user. Una misma actualización añade ambos al final con ordinalsN,N+1. Todos sus textos ya son completos y validados; timestamps pueden ser iguales y no ordenan la lista. El ordinal es orden canónico. Retry posterior añade sólo assistant con ordinalN y reference a userexistente exacto, previa comprobación de role/contenido/scope. El ejemplo A→B→retryA contiene cinco mensajes, dos preguntas y tres respuestas; historia presenta append-order y contexto elige latest por mayor ordinal para la preguntaA. No mover ni duplicar la pregunta, borrar respuestas anteriores o concatenar parciales.

Legacy usersinrespuesta se conserva como elemento originlegacy,question_id=id; no constituye QA completo, no entra en resumen. Legacy assistantsinpregunta/vínculo verificable se conserva originlegacy,question_idNULL, sin inventar pareja. Si existe generation.question_message_id que refiere un userlegítimo de esa misma conversación, migración puede fijar el vínculo canónico; no deducirlo por cercanía/fecha/UUID cuando no existe, conforme spec de compresión («No adivinar parejas legacy sin vínculos; declarar exclusión y conservarlas»). Metadata original se preserva aun si el vínculo no es verificable; referencia opaca desconocida no autoriza leer otro documento ni convertirla en cita verificada. Inconsistencia estructural/scope/ID contradictorio aborta migración; datos originales se conservan. Los no vinculados siguen visibles y se declaran excluidos de QA/resumen por falta de vínculo. Retry explícito de userlegacy válido puede añadir una respuesta vinculada, sin duplicarlo.

Pregunta recuperable de operación sin final vive únicamente en chat_operations: NO se añade al documento hasta final. FailedA→completedB→retryA reutiliza mismo questionID y verifica contenido exacto. `completed.result_message_id` debe resolver una sola entradaassistant canónica; cualquier divergencia produce fallo de integridad y cero nueva inferencia. El documento no se expone crudo; projection pública retorna los campos MessageRecord actuales en ordinal-order, conservando metadata e IDs.

## Migración reanudable y conservación verificable

003 agrega sólo dialogue_historyJSONBNULL de modo aditivo, con DDL confirmado separado como002. No editar001/002 ni retirar tabla messages. Hook de backfill tras DDL y antes registrar003: por conversación bajo lock autorizar parent, leer TODOS sus hijos legacy, detectar scope discordante, construir candidato fijo y contrastarlo. Ventana exclusiva sin escritores: condición de ejecución aislada a validar en encargo material; no promesa de online migration con binariosviejos escribiendo.

Leer metadata como JSONBtext lossless o parse_floatDecimal/parse_intint; nunca roundtrip mediantefloat binario. Serializer canónico UTF8: claves de objetos ordenadas, arrays significativos, escapes JSON estándar, números JSON normalizados con exactitud decimal (sin convertirlos en strings), null/bools/int preservados. No transformar las cadenas dentro de metadata. Fechas SQL TIMESTAMPTZ normalizadas UTC a microsegundos conservando EXACTAMENTE el instante; no redondear ni ajustar fecha para ordenar. Recibo de precisión debe incluir números grandes/decimales largos, negativos, NULLautor, Unicode, fechas con zona y empates.

Hash de conservación por conversación: SHA256 de `{scope, records}` con records ordenados por ID, cada record contiene ID,role,content,metadata lossless,author_id y timestampUTC exacto. Excluir nuevos ordinals/origin/questionlink del hash de VALORES legacy, pero validarlos separadamente. Fuente y proyección del candidato sobre esos mismos campos deben tener igual hash/cardinalidad/conjunto de IDs. Hash identifica representación y detecta diferencias; no firma ni autoriza.

Guardar en documento un campo migration OPCIONAL (sólo documentos importados): version003,source_count,source_sha256. Inicializar revision0 y ordinals explícitos. Orden de importación mantiene orden legacy disponible y resuelve sólo vínculos válidos para el empate; nunca inventa fechas. Comparar documentopersistido contra candidato y contra fuente dentro de la transacción antes del checkpoint; c.commit terminado y migración reiniciable por documento. Si NULL, UPDATE scoped CONDICIONAL NULL instala una vez; si existe, comprobar misma identidad/version/recibo y todos valores legacy contra fuente congelada. No sobrescribir documento distinto ni renovar hash para fabricarPASS. Caída después de commit se resuelve por documento/recibo, no repite append. No writes activos mientras003sinregistrar.

Registro de versión003 sólo tras completar todas conversaciones y contraste global NULL0 + counts/IDs/hashes por conversación. Error aborta sin registrofinal; las ya migradas quedan retenidas para siguiente ejecución verificada. Backend verify-only después exige003/catálogo/docversion/identidad y ausenciaNULL, SIN consultar tabla messages. Validación completa se repite al leer/escribir el documento propio. El backfill y contrastefuente viven SOLO en migrador, no en handlers/startup productivo ni helpers de fallback. Originales messages retenidos frozen son evidencia/migración estrictamente necesaria, no canon paralelo ni dual-write.

## Afectados y gate próximo

Mantener inventario anterior: database.py y chat_repository.py reemplazan rutas porfilas; writer aislado append_message y helper18 retirados de rutasactivas; /messages usa la misma persistenciaJSONBfinal; contexto/result/recovery/latestQA leen documento; summaryderivado conserva linaje/source refs y cambia ordenlatest a ordinal. Metadata/codecs de documento preservan schemafinops/citas/usage; nunca extraen historia de ledgeroperacional. Constructor/verify/migrator/003 y tests de conservación/huérfanos/ausenciaSQLlegacy afectados. UI/API pública compatible, sin cambios de paginación. Docs oficiales porTL; receipts históricos no se borran ni se venden como resultados del nuevo mecanismo.

Pruebas nuevas obligatorias: vacío/envío/delta documentoidéntico; finalatómico(revision+1,dos mensajes)/rollback/duplicadocompleted sinappend; A→B→retryA; Stop/deadlinefences; multiowner/cinco productores; lectura/contexto/recovery/compresión desdeJSONB aun si snapshotlegacy difiere; detector de SELECT/INSERT/UPDATE messages bloqueados fuera de migrador; backfill reinicio/preexistente distinto/errorfailclosed/conservación numérica y timestamps/legítimos no vinculados. No alterar expectativasfuncionales para conservar tests de estructura reemplazada.

Próximo gate: TL valida forma técnica y consolida spec/contrato; PM solicita aprobación material CONCRETA del esquema/backfill aislado y contrato revisado. No se repregunta preferenciaJSONB ni se ejecuta el delta antes del despacho. Coordinación036 únicamente si conflicto de integración concreto; crecimiento se registra/mide, no se introduce bloqueo hipotético.

## Ejemplo sintético de A → B → retry A

```json
{
  "schema_version": 1,
  "identity": {"tenant_id": "synthetic-tenant", "user_id": "synthetic-user", "conversation_id": "synthetic-conversation"},
  "revision": 3,
  "next_ordinal": 5,
  "messages": [
    {"ordinal": 0, "id": "q-A", "role": "user", "author_id": "synthetic-user", "question_id": "q-A", "origin": "completed", "content": "Pregunta A", "metadata": {}, "created_at": "2026-10-10T02:00:00.123456Z"},
    {"ordinal": 1, "id": "a-A", "role": "assistant", "author_id": "synthetic-user", "question_id": "q-A", "origin": "completed", "content": "Respuesta completa A", "metadata": {"generation": {"question_message_id": "q-A"}}, "created_at": "2026-10-10T02:00:00.123456Z"},
    {"ordinal": 2, "id": "q-B", "role": "user", "author_id": "synthetic-user", "question_id": "q-B", "origin": "completed", "content": "Pregunta B", "metadata": {}, "created_at": "2026-10-10T02:01:00.000001Z"},
    {"ordinal": 3, "id": "a-B", "role": "assistant", "author_id": "synthetic-user", "question_id": "q-B", "origin": "completed", "content": "Respuesta completa B", "metadata": {"generation": {"question_message_id": "q-B"}}, "created_at": "2026-10-10T02:01:00.000001Z"},
    {"ordinal": 4, "id": "a-A-retry", "role": "assistant", "author_id": "synthetic-user", "question_id": "q-A", "origin": "completed", "content": "Nueva respuesta completa A", "metadata": {"generation": {"question_message_id": "q-A"}}, "created_at": "2026-10-10T02:02:00.000003Z"}
  ]
}

```

## Retirada activa y controles independientes

# JUP-035 — delta documental consolidado JSONB

Estado: propuesta material pendiente de validación/despacho de ejecución. Preferencia JSONB aprobada por Paris vía PM 10/10/2026 03:01:32; controles de retirada requeridos vía PM 03:03:01. Diseño Dev fuente: `jsonb-canonical-history-delta-design.md` en su carpeta de implementación externa. No migración ni producto implementados. La versión pre-code anterior permanece conservada; no se reescribe la evidencia original.

## Cambio mínimo

Añadir `conversations.dialogue_history JSONB`, documento versionado e identificado por tenant/usuario/conversación con revisión y orden explícito. Al completar una generación validada, la misma transacción agrega pregunta y respuesta completas al documento y confirma la operación. En un retry de pregunta ya guardada conserva la pregunta y agrega la respuesta alternativa vinculada. No modifica historial al enviar, esperar o recibir deltas. `chat_operations` conserva control durable y entrada no confirmada; `dialogue_summary` es derivado con linaje/CAS, jamás historial alternativo.

Todas las lecturas activas de historial, resultados, retry, recuperación y contexto/compresión pasan por el documento. La proyección pública conserva IDs, metadatos, citas y forma `messages`. No fallback por filas ni dual-write. El escritor legacy local `/messages`, actualmente pareja atómica/exclusión409, se adapta a la misma fuente JSONB. La corrección de desempate del bloque18 deja de ser mecanismo activo y se conserva como evidencia histórica, no aceptación JSONB.

## Migración propuesta y riesgos

Nueva migración003 aditiva (disponibilidad a confirmar), sin alterar001/002 aplicadas: columna y backfill reanudable por conversación en ventana aislada sin escritores, verificado antes de registrar versión. NULL significa no migrado, no vacío/fallback. Conversación nueva inicializa documento vacío válido. Backend verify-only rechaza catálogo/documentos incompletos o incoherentes.

Preservar todo historial legítimo, incluso incompleto legacy, con IDs/contenido/metadata/citas/fechas/precisión. Comparar cardinalidad, IDs y representación fiel de campos por conversación; ordenar legado de forma estable con vínculos válidos donde existan, sin inventar mensajes o fechas. Inconsistencia comprobada bloquea migración conservando originales, con error saneado/elevación. Tabla histórica puede permanecer congelada y no canónica solo como soporte identificado de migración/recuperación auditada; ningún lector/escritor productivo alternativo. No DROP/DELETE ni rollback automático de autoridad.

Un documento creciente requiere medir tamaño y contención en Cockroach; este delta no agrega retención, límites o paginación nuevos ni promete escala ilimitada. Mantener GET actual. No llamadas LLM durante migración. Reintentos SQL usan candidato/IDs congelados; commit ambiguo se resuelve por operación y mensaje dentro del documento, sin regenerar. Resumen derivado inválido se invalida en el mismo commit y reconstruye desde originales JSONB.

JUP-036 sigue referencia PM PR69 draft SHA aee2571e038f2b6d7071a7cb055b06b968d67a0e, no integrada. PM coordina acuerdo de escritor JSONB para integración; solo incompatibilidad concreta eleva bloqueo, no dependencia genérica que detenga desarrollo aislado autorizado de035.

## Delta de requisitos y escenarios

- Historial canónico único por conversación: mostrar orden explícito, autorizar identidad y usar documento para todas las rutas productivas. Error de documento falla cerrado; no consulta alternativa a messages.
- Guardado final atómico: enviar/deltas/waits no cambian documento; final validado agrega pareja una sola vez junto a completed. Rollback, Stop confirmado y deadline impiden modificación parcial/tardía.
- Retry/recuperación: pregunta lógica única, respuestas alternativas completas e IDs preservados, latest QA coherente, resultID resuelto desde documento; GET/commit incierto no generan llamadas.
- Transición legacy: preservación exacta, restart sin duplicación, versión solo tras backfill verificado, scope inválido bloqueado sin destrucción. Ninguna escritura paralela al historial por filas.
- Compresión: originales/latest answers/linaje/frontera desde JSONB; invalidación/CAS ante retry; derivado no suplanta historial.
- Retirada activa: inventario y ejercicio que detecte SQL de mensajes fuera de migración/soporte autorizado. Históricos y pruebas de migración legítimos se identifican, no se borran para pasar una búsqueda textual.

## Delta de tareas y documentación

1. Validar forma concreta del documento, tipos/revisión/ordinals y representación de alternativas/legacy legítimo; aprobar esquema y estrategia003/backfill aislado antes de implementar materialmente.
2. Actualizar bajo checkpoint documental separado design/history-persistence/spec/tasks y referencias de contexto/compresión/integración/matriz/resumen. Marcar mecanismos antiguos sustituidos y fuentes humanas fechadas, sin alterar aprobaciones históricas.
3. Despachar Red/Green/mutación separados con paths exactos por ciclo: documento/migración/verificación; final/rollback/idempotencia; lectura/retry/recuperación; contexto/compresión; integración/UI afectada. Adaptar tests de estructura retirada, preservando criterios funcionales; repetir solo pruebas afectadas y obligatorias.
4. Retirar/adaptar `database.py` append_message/append_pair/fetch y helper18, `chat_repository.py` complete/result, rutas assistant/chat, contexto y resumen, runner/readiness/config/tests/smoke dependientes. Processor no pasa a ser dueño del historial; transporte privado/tokenizer no cambian por este delta.
5. Revisor independiente: evidencia específica de ausencia de persistencia antigua activa, escritores/lectores alternativos, doble fuente y helpers/config/contratos/tests/docs obsoletos; restos estrictamente necesarios identificados con motivo y sin ruta alternativa.
6. Validador independiente: flujos documentados y estado DB prueban fuente JSONB, no writes al enviar/deltas, final atómico exactamente una vez, lectura/retry/recuperación/compresión y migración aislada sin pérdida/escritura paralela. Guard PM antes/después y roles sin escrituras, un ejecutor cada vez; TL consolida sin sustituir dictámenes.

## Decisión adicional a elevar

Aprobación concreta de esquema/documento y migración003/backfill/ventana SOLO en entorno aislado, con contrato de pruebas revisado. No reconsultar preferencia JSONB ya aprobada. No pedir decisiones hipotéticas de datos inexistentes, paginación fuera de alcance o acuerdo036 como bloqueo genérico. Producción/remoto, Git/publicación/archivo siguen sin autorización. Presupuesto nuevo0,20EUR acumulado permanece íntegro sin llamadas/reservas.
