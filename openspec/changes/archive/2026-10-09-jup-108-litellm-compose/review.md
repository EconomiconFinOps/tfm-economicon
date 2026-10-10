# JUP-108 — expediente técnico local

## Estado actual

Rama `feat/JUP-108-litellm-compose`, HEAD/base `ff2ea6be12abf1bea4789791c34efb46c3b55aa8` y delta local sin commit. Proceso CONTRIBUTING 2026-09-30/JUP-100. Asignación vigente por Paris (fecha08/10/2026, comunicadaPM09/10): Paris Arcos liderazgo, Lucía Mateo pairing/coautoría, Víctor Méndez revisión y Alejandro Aguado validación/pruebas/documentación. No se atribuye participación humana por asignación ni por trabajo de agentes.

La revisión técnica previa y la relectura focal reconciliada terminaron REVIEW_PASS, con MUT-01 resuelto. La validación independiente es favorable localmente para criterios1–6; el criterio7 conserva etapas posteriores pendientes. Excepción histórica aprobada expresamente; helper FAIL conservado. Aprobación humana final APPROVED y archivo autorizado según bloque vigente al final; publicación pendiente.

## Alcance y evidencia

Los siete criterios oficiales transmitidos por PM a las 22:44:00, los comandos, resultados, hashes, omisiones y la reconciliación autorizada están en [la evidencia](../../../../docs/evidence/JUP-108-validation.md). El alcance conserva mock e incorpora el perfil opcional ai, gateway/PostgreSQL reutilizados, claves virtuales independientes, redes, puertos, salud y persistencia. La guía exige un proyecto con volúmenes nuevos para pasar de mock8 a embedding1536.

Quedan fuera negocio, modelos, presupuestos, contratos IA, migraciones, DockerServer, chat web y RAG. No se autorizan nuevas llamadas reales. Véanse [diseño](design.md), [tareas](tasks.md) y [especificación](specs/containerized-runtime/spec.md).

## Revisión y sensibilidad

El REVIEW_FAIL inicial identificó solo MUT-01: faltaba evidencia localizada de tres operadores previstos. Su informe original se conserva. El Revisor ejecutó 44 casos Node PASS/1 SKIP y el opt-in Python Docker: 1 PASS con 26 comprobaciones; son campañas propias distintas de las del autor.

Desarrollador completó tres mutantes en copias externas con tests fijos: perfil, separación de claves y volumen. Cada uno provocó la aserción prevista; controles original y restaurado: dos PASS. La relectura independiente de las 23:06:23 terminó REVIEW_PASS actualizado, sin nuevas suites. Adenda SHA256 `393a6f6570d1d78ed229d079139938b772338963c3243df5243f16daab4a2396`.

Fuentes de operadores, test y runtime conservaron identidad tras el merge; la prueba de reutilización está en el paquete de integración. Esto acredita sensibilidad estática, no aceptación integrada ni ejecución sobre la base nueva.

## Validación y controles

Validador entregó un checkpoint previo, sin dictamen final: mock con nueve servicios sanos y health200, más bootstrap de gateway/DB/proveedor sintético. No generó claves virtuales ni peticiones de modelo. Retiró contenedores y redes, conservando seis volúmenes propios.

El original PM SHA256 `52fc2ff1f07cb4a844087ce0e21ad685f0cd876e3439e60a5f22c2ba40d256be` y sus retornos PASS se conservan. La reconciliación autorizada cambia el estado: requiere original PM nuevo antes de la siguiente relectura y validación. Son controles conductuales; no se afirma sandbox de lectura.

La evidencia real histórica del autor cubre endpoints del gateway: cuatro inferencias, 84 tokens y 0.000064405 USD atribuidos. El contador compartido no está conciliado; persistencia del gasto después de recrear solo se comprobó con upstream simulado. Las claves reales sí persistieron. No se presenta evidencia ajena como ejecución propia.

## Historial de aprobaciones y pendientes anterior al cierre final

PM informó diseño y correcciones previamente aprobados. La autorización expresa de reconciliación de Paris, transmitida a las 23:11:43, consta en la evidencia. La fuente humana pre-código localizada es el mensaje `01a11d20-6fb3-7743-9510-51592abce453` del chat `01a07c55-c454-7bb3-8053-cbf2ad70d2ec`, posterior a la pregunta explícita de aprobar diseño e iniciar implementación; no se inventa su segundo exacto. PM conserva la verificación de decisiones.

Aprobación humana final posterior a validación: PENDING. DoD, archivo, PR y reviews humanas mantienen sus etapas y permisos. La excepción de desarrollo/revisión/validación en el chat autor no acredita independencia; los controles locales registrados y las reviews humanas posteriores son separados.

No se han localizado completamente los recibos mínimos globales, matriz ni guards históricos de diseño/Red/Green. No se reconstruyen snapshots retroactivos ni se declara DoD PASS sin la evidencia o disposición requerida. Antes de cierre/archivo, TL determina aplicabilidad y PM canaliza las decisiones humanas necesarias. La recopilación no bloquea la reconciliación ya autorizada ni exige repetir baterías por rutina.


## Dictámenes reconciliados y disposición histórica — 08/10/2026

Revisor focal REVIEW_PASS, adenda SHA256 `d10605bacdf1b925aa300142deed6beacdd9e02e27efc594ece3ff7fc5bdeb8e`; Validador favorable local1–6/criterio7parcial, informe SHA256 `7a7081474b0fb73310b18067f3222c6c43153ca9d365b570253ce9f77b4343ec`. Alcance ejecutado, mapa literal de criterios, fuentes, entornos, controles, recibos y límites están en el último apartado de la evidencia enlazada. FAIL/MUT-01, checkpoint previo y recibos reales del autor permanecen separados.

Guard Revisor nuevo originalPMd84f… y retorno independientePM22:38:28UTC PASS; Validador nuevo originalPM4f8d…/guard propio retorno22:51:14UTC PASS. PM conserva control independiente de retorno y final documental; no se declara sandbox ni se sustituye su referencia. TL consolida únicamente evidencia/tareas/review, sin modificar producto/tests/Git.

Matriz de checks: conciliación por entradas y equivalencias nativas, originales/contextos preservados, más local:test74/74actual y controles documentales actuales; no nueva campaña global/CIremota. Guardas históricas iniciales diseño/Red/Green todavía no localizadas: NO VERIFICADAS, sin snapshots retrospectivos ni DoDPASS falso. PM canaliza disposición humana si no se localizan; no hay fallo funcional inferido ni obligación inventada de repetir baterías.

Aprobación humana final posterior a esta validación: **PENDING**; decisión/aprobador/hora no inventados. Archivo, PR, CI/revisiones humanas separadas y merge: **PENDING**, con autorización específica propia. Alejandro revisa y Lucía valida la futura PR; primera favorable hacia develop Comment, segunda Approve conforme al proceso y estado real. Ninguna review humana presentada por estos agentes.


## Excepción histórica aprobada exclusivamente para JUP-108 — 09/10/2026

Paris respondió «la apruebo» a la propuesta concreta de aceptar la ausencia de los tres registros históricos `guard-desarrollador-design`, `guard-desarrollador-red` y `guard-desarrollador-green`. PM confirmó y registró la decisión el09/10/2026 a las00:07:28Atlantic/Canary; es hora de registro, no segundo acreditado del mensaje humano. Fuente preservada: `jup108-historical-guards-exception-approved-20261009.md` en el expediente externo PM.

La excepción se limita a JUP-108 y se sustenta en aprobación pre-code comprobada, diseño/especificación y Red/Green históricos atribuidos, mutaciones sensibles, revisión/validación independientes actuales y originales/controles PM preservados. **Se resuelve por decisión humana la falta de esas referencias; no se afirma que los guards históricos pasaron.** No se fabrican snapshots, sustituyen originales, modifica el helper ni extiende la excepción a otras tareas/directrices.

El resultado original del helper sigue FAIL por esos tres registros ausentes, con matriz aceptada y sin errores de artefactos; se conserva sin alteraciones. La disposición humana se registra separadamente: no es un DoD nativo PASS. Los controles de repositorio aplicables y la revisión/validación local están acreditados con sus límites, por lo que3.2 queda completada bajo esta excepción expresa. El criterio7 global y3.3 siguen pendientes de sus etapas posteriores.

PM verificó independientemente el estado anterior a este registro a las23:06:58UTC del08/10 contra el mismo original SHA256 `4f8d3fcce42d0b61939e18fcb8f46dcd630dbed3ad57a6346f9cc6f3dddbd266`: exactamente seis documentos autorizados y ninguna otra diferencia/HEADchange. Este registro posterior sólo modifica evidencia/review/tasks, con control documental propio separado; PM conserva su referencia y control final pertinente.

Esta aprobación **no** es aprobación final de la entrega ni autoriza archivo OpenSpec, commit/push, PR, publicación o merge. No se repiten pruebas funcionales por el registro. Aprobación final humana, disposición final aplicable y archivo específicamente autorizado en la misma rama preceden las etapas de PR/CI/reviews humanas e integración.


## Post-validation approval — APPROVED, archivo autorizado y roles vigentes

Paris respondió «apruebo» al paso explícito de aprobación final de la entrega y autorización para archivar OpenSpec en esta misma rama, con la excepción histórica ya aprobada. PM registró la decisión el09/10/2026 a las00:08:45Atlantic/Canary; es hora de registro, no segundo exacto del mensaje humano. Fuente preservada: `jup108-final-approval-and-roles-20261009.md` del expediente PM.

Asignación vigente expresamente indicada por Paris, con fecha de asignación08/10/2026: **Paris Arcos liderazgo; Lucía Mateo pairing/coautoría; Víctor Méndez revisión de PR; Alejandro Aguado validación, pruebas y documentación**. La fuente de este cambio es la comunicación humana directa transmitida por PM, no una nueva lectura de Trello. No se presume participación realizada; se conservan atribuciones y asignaciones históricas con sus fuentes/fechas.

Revisión y validación locales favorables y controles aplicables acreditados; excepción exclusivamente JUP-108 para referencias históricas diseño/Red/Green no localizadas. Se conserva el FAIL original del helper y la aprobación de excepción separada, sin inventar PASS/guards/snapshots ni modificar el helper. El cierre final se registra bajo esa disposición humana expresa, no como DoD nativo PASS.

Se autoriza únicamente el archivo OpenSpec de JUP-108 en `feat/JUP-108-litellm-compose`, promoviendo su delta al canónico y conservando evidencia/resultado local. PR, CI y reviews humanas de Víctor/Alejandro permanecen hitos posteriores; commit/push, PR, comentarios/publicaciones y merge no están autorizados. La aprobación final/archivo no completan el criterio7 global ni atribuyen reviews humanas a los agentes.


## Archivo ejecutado — 09/10/2026

OpenSpec archivó este cambio como `2026-10-09-jup-108-litellm-compose` en la misma rama, con validación activada y promoción canónica: tres requisitos añadidos y uno modificado en `containerized-runtime`. El resultado final previo al archivo se conserva en [local-dod-final.json](local-dod-final.json): helperFAIL por los tres guards históricos y excepción humana explícita, más aprobación final/archivo independientes. No se ejecuta ni declara un DoD nuevo sobre una ruta activa ya inexistente.

Roles operativos para la futura PR: Paris Arcos liderazgo, Lucía Mateo pairing/coautoría, Víctor Méndez revisión, Alejandro Aguado validación/pruebas/documentación; fuente humana directa con fecha de asignación08/10/2026. Historial anterior preservado. PR/CI/reviews humanas/merge y permisos de publicación permanecen posteriores, no completados por el archivo.
