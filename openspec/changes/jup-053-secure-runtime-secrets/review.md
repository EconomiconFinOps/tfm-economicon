# Revision JUP-053

## Estado

- Fecha: 2026-09-09.
- Base: `7d76fc376e0eca1aac6401304977575a2f92ceb5`, develop.
- Rama: `feat/JUP-053-secure-runtime-secrets`; diff local sin commit ni PR.
- Revision tecnica automatizada: pasada 1 FAIL; pasada 2 **PASS en alcance**.
  Los tres hallazgos de implementacion se verificaron corregidos.
- QA ejecutada: controles acotados conformes; dictamen de aceptacion completa
  **QA_FAIL / NEEDS_HUMAN** por RF-053-004. El smoke global sigue FAIL.
- Actualizacion 2026-09-10: Paris Arcos acuerda corregir RF-053-004 en
  JUP-020. La asignacion no modifica el ultimo dictamen QA ni aprueba el cierre.
- Aprobacion previa de Paris Arcos registrada en [proposal.md](proposal.md);
  no equivale a revision humana final, pairing ni validacion del equipo.
- Evidencia: [JUP-053-validation.md](../../../docs/evidence/JUP-053-validation.md).

## Alcance Revisado

Los 17 escenarios aprobados: configuracion externa, arranque controlado,
excepcion Cockroach local explicita, diagnosticos saneados, limites de build,
seed sin sobrescritura, password manual y conservacion de Grafana.
ADR-0006 Accepted. Sin cambios de migraciones, dependencias, contratos de
sesion/tenant o integracion funcional de la API.

## Hallazgos

| ID | Severidad | Alcance | Estado y accion |
| --- | --- | --- | --- |
| RF-053-001 | High | JUP-053 | Fixed, verificado en review 2. Se rechazan overrides query y opciones no escalares; solo sslmode, connect_timeout y application_name. Regresiones contra argumentos efectivos del driver y mutantes detectados. |
| RF-053-002 | Medium | JUP-053 | Fixed, verificado en review 2. Redaccion recursiva de claves con secretos raw/URL-encoded/form-encoded; metadata segura y campos sensibles preservados. |
| RF-053-003 | Medium | JUP-053 | Fixed, verificado en review 2. Causa original conservada para logging saneado, error persistido ingestion_failed y nack sin cambio. |
| RF-053-004 | High | Preexistente, fuera de JUP-053 | Open. Correccion en JUP-020 acordada por Paris Arcos el 2026-09-10. Backend anida text_content en payload, processor lo espera arriba. Ingesta aceptada termina failed tanto en base como en la implementacion actual. No corregido; reevaluacion QA y aprobacion final de JUP-053 pendientes. |

Referencias de la primera revision: ambos `app/core/runtime_secrets.py`
(validacion de DSN y redaccion de mappings), processor
`app/tasks/ingest.py`, backend `Database.create_job` y processor
`PipelineRunner._chunk`. Seguimiento en [findings](../../findings/backlog.md).
Los tres hallazgos de JUP-053 ya no bloquean QA; se repitieron Red/Green,
mutation, imagenes/smoke y revision. La correccion del defecto heredado se
ha asignado a JUP-020; no se ha reevaluado QA tras esa decision ni aprobado
el cierre de JUP-053.

## Decision Sobre RF-053-004

- Autor: Paris Arcos. Registro: 2026-09-10, 09:14 UTC.
- Solicitud: "ok crea un finding y anota que en la jup-020 se corregira este
  problema, ademas, añade en la card de trello una referencia al finding".
- Se conserva RF-053-004, ya existente, sin duplicarlo ni renumerarlo. JUP-053
  identifica el origen del hallazgo; JUP-020 es la JUP de correccion acordada.
- Accion pendiente en JUP-020: alinear el contrato de entrada entre backend,
  RabbitMQ, worker y pipeline; incluir una regresion de solicitud aceptada a
  trabajo completado y documentos/chunks/embeddings persistidos, sin perder
  el contexto de tenant. Refinar y aprobar su OpenSpec antes de implementar.
- Mantener Open/High hasta verificar la correccion. Revisar la dependencia
  de JUP-050 si su smoke exige esta ingesta documental antes de JUP-020;
  este registro no reordena el plan ni inicia otra JUP.
- Referencia añadida y releida en [JUP-020 privada](https://trello.com/c/1Y9HVCQs)
  el 2026-09-10 a las 09:16 UTC, autorizada expresamente. Descripcion original,
  nombre, lista, posicion, etiquetas, miembros, comentarios y fechas de entrega
  conservados; la nota indica que el finding aun es local y no esta publicado.
  [Tarjeta oficial](https://trello.com/c/Mi3kPCOD)
  sin modificar; replica manual por Paris pendiente.
- No autoriza cambiar QA a PASS, aprobar JUP-053, publicar codigo, crear PR,
  hacer merge o archivar. El fallo funcional sigue abierto.

## Gates Y Limites

- Red inicial valido: 133 casos nuevos; 119 fallos de comportamiento y 14 pass.
- Correccion de captura de logs acreditada contra la base; cuatro casos de
  lifecycle adicionales, tres Red y un control. Review 1 incorporo 55
  regresiones: 51 Red significativos y cuatro controles.
- Green3: **552 pruebas distintas aprobadas, 192 nuevas**, entre suites;
  no una ejecucion unica. No incluye escenarios OpenSpec ni repeticiones.
- Mutation 2: **11/11 mutantes seleccionados detectados**, incluidos los
  tres hallazgos. No es una medicion exhaustiva.
- Guards de planner, tester, coder y reviewer: PASS en sus fases.
- OpenSpec 28, trazabilidad 16 cambios e higiene 480 archivos: PASS.
- Build/typecheck frontend PASS. Lint heredado RF-082-002: 49 errores,
  no resueltos ni incrementados.
- Cuatro imagenes actualizadas, 42 capas, tres archivos de bundle y tres
  contextos sin sentinelas; 30 fixtures dotenv excluidas. Scan acotado de
  480 rutas con controles positivos, no ausencia universal de secretos.
- Smoke completo FAIL por RF-053-004; arranque, login y comprobaciones
  de credenciales especificas si pasan.
- QA reejecuto 448 casos y contrasto 104 anteriores: 552 distintos. Comprobo
  31 destinos Markdown locales, sin validar anchors ni URLs externas.
  Dieciseis escenarios tienen evidencia acotada automatizada o inspeccion;
  rotacion conserva evidencia runtime parcial: demo/JWT ejercitados,
  DB/broker/gateway solo procedimientos inspeccionados, sin rotaciones reales.
- CI remoto, pairing y validacion humana pendientes. Sin PR, commit/push,
  merge, archivado ni cambios en entornos compartidos. La unica actualizacion
  de tracker autorizada en este seguimiento es la referencia en JUP-020 privada.

## Aprobacion Post-QA

- Decision: **PENDING**.
- Aprobador: pendiente.
- Fecha: pendiente.
- Notas: correccion de RF-053-004 asignada a JUP-020; falta la reevaluacion de
  QA que corresponda y la aprobacion post-QA. No presentar aceptacion completa, cierre o publicacion
  como aprobados. Prerequisitos locales de QA satisfechos no equivalen a DoD final.
