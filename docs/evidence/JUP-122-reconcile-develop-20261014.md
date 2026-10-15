# JUP-122: reconciliacion local con develop

Fecha: 14/10/2026, Atlantic/Canary. Rama `feat/JUP-122-chat-engineering`.
Paris autoriza el merge local; commit/push y publicaciones finales quedan
reservados al PM. No se modifican otras ramas ni se levantan reviews oficiales.

## Referencias y delta

- HEAD/primer padre: `11f8433404f786c065ad35f13f673465fa26caf5`.
- Develop/segundo padre fijado tras fetch: `0543c5ee671cb1b400254561f5bdc6e419664510`.
- Base anterior: `c30a7d0f28c04cae757b424222b34b232814303e`.
- Arbol AUTO_MERGE: `b7a96c6780dd6cbb36214fbf14b6e73e7620d629`.
- Delta completo de develop: un commit JUP-038/#128, 71 archivos, 10514
  inserciones y 29 eliminaciones, incluidos pruebas, evidencias y archivo
  OpenSpec. Sin nuevas migraciones ni cambios de dependencias.

El delta funcional incorpora seleccion de episodio, snapshot de una sentencia
SQL filtrado por tenant, explicador determinista con Decimal y procedencia
sintetica, evidencia tipada, formulario/enlace y documentacion. Se inspeccionan
los contratos, persistencia, formularios y renderer, ademas de las dos rutas
en conflicto. Las partes nuevas sin conflicto se conservan del merge automatico.

## Resolucion semantica

`apps/backend/app/api/routes/assistant.py`: conserva lectura/explicacion de
JUP-038 y sus codigos 404/409 sin recuperar RAG ni inventar causas. Mantiene
la guarda de conversacion ocupada de A; sustituye la escritura individual
incompatible por prepare_message y un append_pair atomico. Conserva la
correlacion tecnica generation.question_message_id del historial de A,
incluida en respuesta e historial. Sin modificar el bloque anomaly_evidence
ni su contrato. Error de persistencia revierte el turno y no incrementa la
metrica de respuestas completadas. Respuesta con serializador vigente de A.

`apps/frontend/src/components/AnswerEvidence.tsx`: conserva las fuentes
pequenas, foco accesible y validacion de referencias; incorpora AnomalyEvidence
despues de CostEvidence. Prioridad: citas validas, costes, anomalias, aviso
de referencias documentales no respaldadas. No reintroduce el aviso vacio.

Tres suites API de anomalias observan ahora el historial JSONB real, no la
tabla legacy messages; usan el spy append_pair y exigen una unica escritura,
scope y roles correctos. Se conservan los controles de integridad, cifras,
privacidad y errores; se añaden rollback despues de escribir y bloqueo antes
de leer una anomalia. La prueba frontend del aviso vacio adopta la ausencia
ya aprobada en A, conservando los avisos de evidencia invalida. test-support
declara explicitamente GET capabilities false, manteniendo la deteccion de
cualquier otra peticion HTTP inesperada.

## Comprobaciones focales

| Control | Resultado |
| --- | --- |
| Backend API, integridad, escala, esquema, explicador y chat desactivado | 191/191 PASS, sin omisiones |
| Frontend evidencias, formulario/enlaces y chat condicionado | 138/138 PASS, ocho archivos |
| Consumidores de fixture: sesion, tenant, propiedad y conversaciones | 38/38 PASS adicionales |
| Typecheck app y tests | PASS |
| Build frontend | PASS |
| Lint frontend | 0 errores, 1 aviso previo ChatPresentation.tsx:101 |
| OpenSpec estricto | 72/72 PASS |

Los tests HTTP backend usan SQLite real para identidad/tenant/historial y
un doble exclusivamente para el snapshot que requiere Cockroach; el
explicador es el de producto. El test de tres respuestas en una conversacion
conserva la igualdad HTTP/historial de propiedad, anomalia y RAG. Se comprueban
rollback, errores sin escritura y privacidad de logs. Los tests frontend
montan rutas reales y simulan respuestas HTTP, no reemplazan aceptacion humana.

Se conserva el primer fallo API (metadatos correlacionados no contemplados
por la prueba de #128), el fallo del aviso redundante y la tanda frontend
con capabilities no interceptadas y contaminacion posterior. Se adaptan
fixtures/asserts a la implementacion combinada, sin relajar producto o
eliminar las comprobaciones. Los recibos no se sobrescriben.
Avisos SQLite, Radix ref y tamano/import dinamico de build permanecen
documentados; no se corrigen fuera de alcance.

Un diff contra HEAD confirma sin cambios main/startup, rutas y esquema del
chat nuevo, escritor JSONB, planificador, capabilities/preflight, componentes
de chat, redes/CD, tokenizer/Docker, exclusiones de secretos, dependencias y
fixture SQL. Su evidencia previa se reutiliza; no se afirma nueva ejecucion.

No nuevas llamadas a proveedor, gasto, servicios, bateria28 o suites
generales. No se repite Cockroach nativo: snapshot/explicador de develop y
escritor de A permanecen intactos; se prueba la combinacion de su caller con
SQLite. La comprobacion nativa independiente focal puede usarse para la
aceptacion posterior si PM lo requiere, sin repetir las suites completas.

## Reproduccion y entrega

```sh
cd apps/backend
python -m pytest tests/test_anomaly_explanation_api.py tests/test_anomaly_explanation_integrity_api.py tests/test_anomaly_explanation_scale_api.py tests/test_anomaly_explanation_schema.py tests/test_anomaly_explanations.py tests/test_chat_disabled_jup122.py -q
cd ../frontend
corepack pnpm test -- src/components/AnswerEvidence.test.tsx src/components/AnswerEvidence.anomaly.test.tsx src/components/AnomalyEvidence.test.tsx tests/anomaly-explanation-conversations.test.tsx tests/anomaly-explanation-link.test.tsx src/pages/AnomaliesPanel.explain-link.test.tsx tests/chat-capabilities-jup122.test.tsx tests/chat-anomalies-screen-jup035.test.tsx --maxWorkers=2
corepack pnpm test -- tests/session-and-dashboard.test.tsx tests/tenant-switching.test.tsx tests/ownership-conversations.test.tsx tests/conversations.test.tsx --maxWorkers=2
corepack pnpm typecheck
corepack pnpm lint
corepack pnpm build
cd ../..
corepack pnpm openspec:validate
corepack pnpm jup:check -- --change jup-122-chat-engineering
corepack pnpm jup:cleanup:check
```

Recibos completos, SHAs del candidato y diff frente a AUTO_MERGE quedan
fuera de Git, en jup122-reconcile-develop-20261014. El merge se prepara y
resuelve sin commit ni push; las rutas manuales se enumeran en ese manifiesto.
PM conserva su guard independiente y la aprobacion de publicacion.

Plan minimo posterior: revision independiente de ambos conflictos y de las
adaptaciones de pruebas; validacion de una explicacion con evidencia y
reapertura, un episodio ajeno o no explicable sin escritura, y convivencia
con citas compactas y acceso desactivado. No nueva bateria de 28 ni pruebas
reales del modelo por rutina. Tras esos controles, PM gestiona commit de
merge, push y CI; Victor/Lucia mantienen sus dictamenes oficiales pendientes.
