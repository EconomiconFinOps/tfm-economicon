# Revision JUP-053

## Estado

- Actualizacion: 2026-09-10.
- Producto probado: `cb0403661f7fd9d69f7122965e401a60d89314f2`.
- Base integrada: `cb270093035252a10c343f97d64262c8e74e0ef2`, develop.
- Rama: `feat/JUP-053-secure-runtime-secrets`; publicacion de PR autorizada.
- Revision tecnica automatizada: pasada 1 FAIL, pasada 2 PASS en alcance;
  revision de reconciliacion **REVIEW_PASS**, sin nuevos bloqueos en alcance.
- QA final de la reconciliacion: **QA_PASS_WITH_APPROVED_EXCEPTIONS**.
  Dictamen registrado el 2026-09-10 a las 10:13 UTC. La QA del 09/09 conserva su
  dictamen historico FAIL; no se transforma el smoke global fallido en PASS.
- Paris Arcos autoriza cierre acotado y PR con RF-053-004 abierto en JUP-020.
  QA de la version reconciliada completada; CI y revision humana pendientes.
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
| RF-053-004 | High | Preexistente, fuera de JUP-053 | Open, correccion asignada a JUP-020. Paris Arcos autoriza cierre acotado de JUP-053 y PR con esta anotacion. Backend anida text_content en payload, processor lo espera arriba; el smoke integral historico sigue FAIL. No corregido; no se afirma una ingesta funcional. |

Referencias de la primera revision: ambos `app/core/runtime_secrets.py`
(validacion de DSN y redaccion de mappings), processor
`app/tasks/ingest.py`, backend `Database.create_job` y processor
`PipelineRunner._chunk`. Seguimiento en [findings](../../findings/backlog.md).
Los tres hallazgos de JUP-053 ya no bloquean QA; se repitieron Red/Green,
mutation, imagenes/smoke y revision. La correccion del defecto heredado se
ha asignado a JUP-020. La revision de la reconciliacion tambien pasa;
la QA final confirma la preparacion para publicar con la excepcion aprobada.

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
- Esa primera solicitud no autorizaba publicar o cerrar JUP-053. La solicitud
  posterior de cierre y PR se registra al final de este documento; no modifica
  el resultado del smoke fallido ni autoriza merge o archivado.

## Reconciliacion Verificada (2026-09-10)

- Se incorpora develop cb27009 mediante merge local cb040366, conservando
  tracing JUP-044, sus cinco pruebas, archivos y findings importados.
- Cookie RabbitMQ externo obligatorio, ejemplo vacio y procedimiento que
  preserva el valor privado existente; sin generar, rotar o tocar .env real.
  Se resuelven los tres conflictos de worker, Compose y manual sin perder
  tracing, cierre de recursos ni diagnosticos saneados.
- Red: topologia 25 pass/2 fail frente a 26 pass anteriores; tres expectativas
  de Compose ausente/vacio/presente fallan antes del cambio. Fixture RF-053-003
  ajustada al request_id del mensaje sin eliminar ninguna assertion.
- Green integrado: 115 backend, 257 processor y 82 Node = 454 casos reejecutados.
  Reutilizacion verificada: 34 Cockroach, 58 Azure y 12 colaboracion = 104.
  Total **558 distintos, 193 nuevos de JUP-053**; cinco nuevos de JUP-044
  importados no se atribuyen a JUP-053. Build/typecheck frontend reutilizados.
- Mutation: dos baselines pasan y dos mutantes fallan por comportamiento:
  causa original RF-053-003 (repeticion) y fallback cookie (nuevo). Acumulado
  de **12 mutantes unicos seleccionados**, no un score universal.
- RabbitMQ aislado real: diez comprobaciones PASS, incluido arranque/reinicio
  con misma credencial/volumen, logs sin valores secretos, rechazo de cookie
  ausente/vacio y limpieza de un contenedor y un volumen propios, sin red creada.
  Primer intento sin imagen fijada en cache fallo antes de crear recursos;
  pull del digest declarado y reintento correctos. No rotaciones reales.
- Tester y reviewer contrastan 494 hashes de fuente; manifiesto antes/despues
  identico: `702E9BAE7302B50752103E67C440C0645D4B3C84C5EAA7F84149779665B99521`.
  Guards de ambas fases sin cambios. El diff de PR contra develop pasa higiene
  de whitespace; se conserva una linea final vacia heredada de una spec upstream.
- RF-044-002 sigue Open en JUP-096 y RF-082-002 conserva 49 errores de lint.
  Imagenes y smoke completo del 09/09 siguen siendo evidencia historica.

## QA Final (2026-09-10)

- QA_PASS_WITH_APPROVED_EXCEPTIONS: sin bloqueos nuevos en alcance.
- OpenSpec 29, trazabilidad JUP-053 y 12 cambios activos, higiene 494 rutas
  y ambos diff checks: exit 0. Dieciseis destinos Markdown locales y tres
  anchors de los cinco documentos verificados, sin rotos.
- Manifiesto de 494 entradas: 489 fuentes intactas y cinco documentos de
  evidencia esperados. Guard qa-final-prepr-20260910: cero cambios/violaciones.
- QA inspecciona los 558 resultados, 12 mutantes y diez checks runtime;
  no reejecuta suites, builds ni Docker. Reutilizacion y limites declarados.
- DoD qa PASS. Primer DoD final exit 20 por conservar qa=FAIL historico y
  faltar el evento de aprobacion. Tras registrar este dictamen y la autorizacion
  humana existente, DoD final PASS (exit 0) el 2026-09-10 a las 10:14 UTC.
- RF-053-004 sigue Open/High para JUP-020. La excepcion no valida la ingesta
  completa. CI remoto, pairing y revision/validacion humana pendientes.

## Gates Y Limites Historicos (2026-09-09)

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
- En esa fase: CI remoto, pairing y validacion humana pendientes; no habia PR
  ni commit/push, merge, archivado o cambios en entornos compartidos.

## Aprobacion Post-QA

- Decision humana: **APPROVED para cierre acotado y publicacion**.
  Condicion de QA final satisfecha por el dictamen registrado arriba.
- Aprobador: Paris Arcos. Fecha de registro: 2026-09-10, 09:59 UTC.
- Solicitud posterior a la QA y a la decision sobre el finding:
  "vale ahora cierra la jup 053 con la anotacion correspondiente y haz el pr".
- Alcance aceptado: controles de secretos de JUP-053, manteniendo RF-053-004
  Open/High para JUP-020 y el smoke integral historico FAIL. No acepta la
  ingesta como funcional ni autoriza excepciones nuevas de seguridad.
- Autoriza preparar commits, publicar la rama/PR a develop y anotar el
  seguimiento privado. No autoriza merge, archivado, cambios en el Trello
  oficial, responsables, credenciales reales o entornos compartidos.
- La revision automatizada no acredita pairing ni validacion humana del equipo.
  CI remoto y revision humana son gates de merge. La tarjeta debe permanecer
  en revision/validacion, no Hecho, mientras falten esos requisitos.
