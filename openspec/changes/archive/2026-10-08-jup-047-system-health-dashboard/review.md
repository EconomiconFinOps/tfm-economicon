# JUP-047 — revisión y validación locales posteriores a develop

## Revisión examinada y proceso

08/10/2026, Atlantic/Canary. Rama `feat/JUP-047-system-health-dashboard`; revisión de código `8770897bab29c79df54659e362f89d97c28b132a`, con padres `e1f58d01ed984be95021953bebb97ab9b5479ad0` y `2f9a5f530c9fe3b60007ba5060c189133e353bf6`. El segundo padre es la base incorporada; PM comunicó su fetch a las 13:11:51. No se acredita una nueva comprobación remota.

Proceso: [CONTRIBUTING.md](../../../../CONTRIBUTING.md#review-and-validation-flow), versión 2026-09-30 (JUP-100). Alcance aprobado: conservar observación real y fecha sin TTL, timeout actual con historia del éxito anterior, ciclo visible de 600000 ms con apertura/manual/ocultación/desmontaje, aislamiento de sesión/tenant, tolerancia UTC inclusiva de 1000 ms y Azure SIMULADO. [Diseño](design.md), [tareas](tasks.md), [correspondencia E15](acceptance-map.md) y [runbook](../../../../docs/runbooks/system-health.md).

## Resultado de revisión técnica

**REVIEW_PASS local**, Revisor automatizado independiente, cierre 13:55. Cero suites, builds o mutaciones nuevas propias; inspección del delta, contratos compartidos y evidencia recibida. Sin hallazgos nuevos que requieran corrección en el alcance revisado. Este registro consolida el dictamen recibido; no convierte al Desarrollador en Revisor ni determina aceptación.

Se examinaron siete commits entrantes y los dos README solapados. El delta expandido incluye 109 rutas (102 con detección de movimientos), con 100 archivos entrantes idénticos al destino y siete orígenes retirados conforme a él. Se conservaron 29 rutas propias no solapadas y 818 fuentes anteriores fuera del delta. Las secciones completas de JUP-047 en ambos README quedaron preservadas. Manifiesto y copia de ejecución: 920 fuentes idénticas, sin cambios de dependencias, lockfile, requisitos Python o configuración de compilación.

El alcance indirecto incluye importaciones de assistant/billing/vector en backend y las páginas ejecutiva/conversaciones en las rutas frontend. Se contrastó su integración con sesión/tenant y la suficiencia de la campaña nueva; no se realizó una revisión exhaustiva de todos los productos de las otras JUP incorporadas.

## Fases y comprobaciones preservadas

La implementación anterior conservó fases separadas: Red 185 PASS/42 fallos significativos; primer Green no satisfactorio (214 backend PASS/4 FAIL); corrección de tests, Green y mutaciones posteriores con originales intactos. El cierre histórico acreditó 341 casos (123 frontend y 218 backend) y 27 operadores dirigidos dispuestos: 25 kills reutilizados por identidad y dos reensayos de aquella fase. F16/F19 SURVIVED, B04 TOOL_FAILURE y los fallos originales siguen siendo historia; no se transforman retrospectivamente en PASS. No hubo nueva mutación posterior al merge, porque no cambió la conducta propia de JUP-047.

Campaña nueva del Desarrollador sobre la revisión reconciliada: **2013 PASS/0 FAIL/91 SKIPPED**, 35 comandos exit 0; build de los cuatro paquetes, lint y tres TypeScript satisfactorios; OpenSpec estricto 53/53. Los mismos 123+218 casos están incluidos en esos 2013; no se suman otra vez. El Revisor auditó los recibos y sus hashes, sin presentarlos como ejecución propia. [Detalle, comandos, matriz y límites](../../../../docs/evidence/JUP-047-validation.md).

Matriz de 40 filas y siete mínimos de CONTRIBUTING: `test` y `build` acreditados mediante los scripts completos de los cuatro paquetes participantes, sin omitir suites ni assertions. Ejecución nativa equivalente con dependencias existentes; no se ejecutaron literalmente pnpm/Turbo ni una instalación frozen-lockfile. El fallo de caché offline de pnpm permanece. Node local 24.17 frente a Node 22 de CI; no equivale a CI remota verde. Los 91 opt-in no ejercitados permanecen NOT_VALIDATED.

Los controles de fuentes del Desarrollador y los independientes cotejaron las 920 rutas. PM conservó originales distintos para Revisor y Validador; TL comunicó retornos PASS contra los mismos originales, sin violaciones. Esto es detección de integridad, no sandbox de solo lectura. La consolidación E15 es exclusivamente documental, con checkpoints separados para tres OpenSpec y un archivo de evidencia; no altera producto, tests, requisitos ni aprobaciones.

## Resultado de validación independiente

**LOCAL_POST_BASE_PASS**, Validador automatizado independiente, informe 14:05. Ejecución propia nueva: **85 frontend + 10 backend PASS, 0 FAIL/ERROR/SKIP**. AC1–AC3: PASS_LOCAL_AFFECTED; AC4–AC5: NOT_VALIDATED globalmente. No constituye validación humana de GitHub ni aceptación global.

Se ejecutaron rutas reales, sesión y tenant, navegación, facturación ejecutiva y asistente/citas. Caso de error: selección de billing inválida devuelve 422 antes de consultar datos. Bordes adicionales: sesión/user parcial impide fetch y respuestas/errores tardíos de un tenant no contaminan el siguiente. No hubo navegador, servicios reales ni nuevas inferencias. Los 95 casos, los 2013 del Desarrollador y los 341 históricos son campañas distintas; sus totales no se suman.

La revalidación documental previa fue LOCAL_DOCUMENTARY_PASS y resolvió AC3 localmente. Su VALIDATION_FAIL original por README con TTL conserva su fecha y resultado; E14 se mantiene literal y E15 registra los hechos posteriores. [Validación durable y criterios](../../../../docs/evidence/JUP-047-validation.md).

## Hallazgos, riesgos y participación

Sin corrección nueva solicitada en esta revisión local. El finding [RF-026-002](../../../findings/backlog.md#rf-026-002) mantiene su disposición diferida; no se reabre ni se declara corregido. Paris aceptó la presentación observada por él a las 13:05:44 y no pidió más UI/teclado. Esa observación no se atribuye al Validador.

La adenda del Revisor precisa: **0,20 EUR es el techo autorizado acumulado, incluido el histórico; no es gasto acreditado**. Los importes del ledger no prueban ese gasto. Esta revisión/validación/consolidación no hizo llamadas reales ni añadió gasto.

Roles humanos comunicados por PM: Paris Arcos liderazgo, Víctor pairing, Alejandro revisión/M5, Lucía validación. Sus asignaciones no acreditan trabajo realizado por los agentes ni participación humana. M5 real con Alejandro y participación/reviews humanas permanecen externos; no son un defecto ni bloquean por sí mismos el gate local previo al archivo. CI remota, PR, publicación y vínculos oficiales siguen bajo coordinación de PM.

No hay PR, eventos, fechas, enlaces o revisiones humanas acreditados en este registro. Las reviews `Revision JUP-047` y `Validacion JUP-047` se solicitarán después del archivo autorizado, por las personas asignadas y con los eventos/orden de CONTRIBUTING; siguen pendientes y son gates de integración. No se declara excepción de identidad ni sustitución de esas reviews.

## Post-validation human approval — APPROVED

- Decisión: APPROVED para la entrega local final posterior a la base `2f9a5f530c9fe3b60007ba5060c189133e353bf6`, código revisado `8770897bab29c79df54659e362f89d97c28b132a`.
- Aprobador: Paris Arcos; respuesta literal «si» a «¿Apruebas esta entrega local final? Después completaré el archivado ya autorizado y te mostraré la propuesta de PR antes de publicarla.».
- Fecha/hora de aprobación: 08/10/2026 14:36, Atlantic/Canary; no se dispone del segundo exacto del mensaje humano. PM confirmó la decisión a las 14:36:07; esa hora no se atribuye al mensaje humano.
- Fuente: PM, chat `01a1063b-fed3-7480-a0d6-cc6f374ecacf`; mensaje humano `01a11bba-6640-7c71-8d13-3b541b40f4b4`, turno `01a11bba-65e9-7b81-a303-fe0c1ca509e8`; pregunta en turno `01a11bb9-af92-7fb3-934e-fe48c355393a`. TL verificó la pregunta y respuesta originales y remitió la fuente el 08/10/2026 14:37:15. Recibo de esa fuente SHA256: `952c448edeac7c4e205f58614e04918292739cf1fb5f9a83b55b53d1747ddecd`.
- Notas y siguientes gates: esta decisión supersede el PENDING anterior de este bloque y los estados históricos E15, conservados en los otros documentos. El pre-validation DoD del change activo fue PASS por TL; corresponde al TL registrar la aprobación y ejecutar el DoD final con el change todavía activo. La autorización específica de archivo del 08/10/2026 13:11:51 sigue vigente; el archivo requiere un encargo separado después del DoD final. No se ha archivado ni se concede permiso de commit, push, PR o publicación. AC4/AC5 globales, participación y reviews humanas mantienen sus límites; no se atribuyen nuevos dictámenes técnicos ni ejecuciones.

## Procedencia verificable

Recibos originales conservados fuera del repositorio; los hashes identifican su contenido, no son enlaces públicos ni autorizaciones:

| Artefacto | SHA 256 |
|---|---|
| Revisor, review-handoff.json | `6ee24e1ba034c2a6114401f0cf35298dfec883cb71308bf712f9241ea702dc96` |
| Revisor, informe original | `edab496a4a93f474b603366101b92a949e61cc81149ec6d78bac8d0e798a97c1` |
| Revisor, adenda de techo frente a gasto | `2600b0b444a2f1897b04c8349c45d635bb7d712249448dbccbc185daafadf545` |
| Validador, handoff.json | `86852d562997a8b81be3a523e3a96a1a0f8ddfc471bf93b343ca22d947649a15` |
| Validador, informe | `2d67d1bae81c040df16d9fb2cac83b97a7ca64aac6a657311e4bbf1cda3d4977` |
| Desarrollador, handoff postmerge | `8af91a16368715db7d2c4a310c22db2da462e550ad27aea7207e04ca71ff13a2` |
| Original independiente PM para Revisor | `b7b15a4b43a3df69ad88a8e6345f54b3c42ed7dffff3fea69f9da7ad99915097` |
| Original independiente PM para Validador | `37e35026768ff6cbfbdab818099c232cabc204d84594782baf13cc3b85918955` |

Los retornos de PM son hechos comunicados por TL el 08/10/2026 14:09:37; este documento no inventa recibos nativos de esos controles ni sustituye sus originales.


## Corrección de encabezados previa al archivo — 08/10/2026

OpenSpec 1.8.0 abortó el archivo antes de escribir: el parser canónico interpretó las notas históricas E12 de nivel 3 como requisitos adicionales sin escenarios. Paris autorizó literalmente «SI» el 08/10/2026 a las 15:07, Atlantic/Canary (segundos humanos no disponibles; confirmación PM 15:07:04), cambiar únicamente esos dos encabezados de `###` a `##` y añadir esta nota. Fuente verificada por TL: mensaje humano `01a11bd6-bc55-7692-8723-a5d23ba53a37`, turno `01a11bd6-bbfb-7a91-af64-63cbfd948fa4`, pregunta `01a11bd5-0b69-7be1-b355-a8310e05f788` en el chat PM.

Todo el texto histórico, requisitos, escenarios, casillas y aprobaciones anteriores permanece intacto. La aprobación final post-base de las 14:36 y el DoD final previo se conservan como hechos de su momento; TL renovará contexto, matriz y DoD final con el change ACTIVO antes de un nuevo despacho de archivo. Se preservan el aborto de la CLI y el rechazo inicial del encargo anterior a esta autorización concreta. No se reintenta el archivo en esta corrección ni se alteran producto o tests.


## Archivo específico y DoD final local — 08/10/2026

El change JUP-047 quedó archivado el 08/10/2026 en `openspec/changes/archive/2026-10-08-jup-047-system-health-dashboard`, en la misma rama `feat/JUP-047-system-health-dashboard`, código `8770897bab29c79df54659e362f89d97c28b132a` y base `2f9a5f530c9fe3b60007ba5060c189133e353bf6`. Se incorporaron los deltas a las especificaciones [health-status](../../../specs/health-status/spec.md) y [system-health-dashboard](../../../specs/system-health-dashboard/spec.md); los dos requisitos anteriores de health-status permanecen.

Paris aprobó la entrega local final el 08/10/2026 a las 14:36, Atlantic/Canary, con respuesta literal «si»; los segundos humanos no están disponibles y PM confirmó a las 14:36:07. Paris autorizó la corrección mecánica de los dos encabezados E12 a las 15:07, con respuesta literal «SI», confirmada por PM a las 15:07:04; el intento de archivo anterior quedó abortado sin cambios. Tras esa corrección, TL renovó el DoD final code/final con el change todavía ACTIVO: PASS, exit 0, sin errores; registro UTC `2026-10-08T14:16:00.6434523Z`. Se conserva [el resultado original exacto de ese DoD final renovado](local-dod-final.json), SHA256 `4b1b13ff29ea848e7d71e37b99c2e660a81d2bbc8a8a9ca2bc388a74095fda82`. No se vuelve a ejecutar el helper tras retirar el directorio activo.

El archivo aplica la autorización específica de las 13:11:51 y el encargo separado posterior al DoD final. Esta nota supersede únicamente los pendientes históricos de aprobación local, DoD final y archivo; no borra historia ni cambia casillas, requisitos, escenarios o dictámenes técnicos. No acredita M5, participación ni reviews humanas, AC4/AC5 globales, CI remota o vínculos oficiales. Commit, subida, PR y publicación siguen pendientes con sus permisos propios. No hay pruebas de producto, builds, mutaciones, llamadas o gasto nuevos por este archivo.


## Corrección de feedback PR81 — entrega local del Desarrollador, 08/10/2026

Alcance aprobado por Paris y transmitido por PM20:47:37 Atlantic/Canary: excluir la credencial diagnóstica completa exacta o incrustada de reported_model antes de IPC/recibo/retención/DTO, manteniendo éxito funcional cuando solo falla metadata; coordinar sonda finita configurable2..8 s (default8), agregación18 s y GETcliente20 s. POST30/35 y polling30, autenticación/tenant, contabilidad, ruta y aislamiento permanecen. Partida HEAD aa8f276ba04dba51148d11a8d6315dec26d8d32c, base local2f9a5f530c9fe3b60007ba5060c189133e353bf6; cambios locales aún sin commit. Proceso2026-09-30/JUP-100; Paris/Víctor/Alejandro/Lucía conservan sus roles humanos.

| Comprobación del incremento | Resultado comprobado por Desarrollador |
| --- | --- |
| Red significativo | Backend19 FAIL; frontend GET1 FAIL/POST1 PASS |
| Green backend completo | 896 PASS,0 FAIL,0 ERROR,34 SKIP no validados |
| Frontend afectado | 99 PASS en tres suites |
| Dos suites modificadas, comprobación final | 91 PASS,0 SKIP |
| Sensibilidad dirigida | 14/14 regresiones detectadas, sin supervivientes/inválidos; cuatro reensayadas tras estabilizar sesión, diez reutilizadas por identidad verificada |
| Controles originales/restaurados | Backend26 PASS y frontend61 PASS en cada control; copias restauradas |
| Controles técnicos | Tipos frontend3/lint/build, compileall app, OpenSpec CLI53/53, trazabilidad e higiene924 fuentes PASS; diff-check exit0 |
| Compose local propio, sin LLM | Seis lecturas sanas DB/cola/processor/vector y actividad1,457..1,685 s; dos Azure detenido failed/connection1,584..1,693 s; dos recuperado ok1,734..1,782 s |

No se suman campañas ni se atribuyen ejecuciones históricas al incremento. Las34 omisiones opt-in JUP086 (Cockroach14/Rabbit3/pgvector17) permanecen NOT_VALIDATED por URLs de fixture ausentes. Entorno Python3.12.14/Node24.17; CI Node22 y CI remota no comprobados de nuevo. Entradas nativas con dependencias existentes; no frozen-install pnpm/Turbo global nuevo. Compileall no se presenta como linter independiente.

Compose usó HTTP real autenticado desde el backend propio en red interna, imágenes existentes, código Green montado en lectura, datos y credenciales sintéticos y proveedor deshabilitado. Docker local28CPU/33,6GB difiere del entorno de Lucía8CPU/7,7GB; no acredita reproducción equivalente. Ruta host/navegador no validada. Azure conserva procedencia simulada; proveedor desconocido no se convierte en éxito. Proyecto propio jup047-correction-20261008-7ebc71 disponible para validación; sin tocar realtrial ajeno. No llamadas pagadas, credenciales reales ni gasto nuevos.

Incidencias preservadas: Red inicial sin IPC agotado240s sin resultado; Green416PASS/4FAIL por dobles incompatibles y corrección separada1PASS/3FAIL seguida4PASS; post-mutation25PASS/1FAIL por tokens de sesiones distintas, corregido reutilizando la misma sesión sin cambiar igualdad/helper global/producto. Fallos instrumentales de captura/higiene/Compose/host conservados. Ninguno se convirtió retrospectivamente en PASS. Seis snapshots originales/guards distintos PASS;924 fuentes y13 rutas de implementación autorizadas, cinco docs de diseño fijos durante Dev. No se modificaron producto/tests/Git durante este cierre TL.

Procedencia: paquete externo jup047-review-corrections-implementation-20261008/DELIVERY.md, delivery-handoff.json SHA256 `d5d09b5bb9ee7694a5335bc8c2c4e84f709c33bdbd5fea9cf793bc19001be20f`, artifact-index.json SHA256 `2cc4da9136addea8ae62f4dc02fbc75951a8fea619a2baa2ece0e500e79f446f`. Recibos, referencias y límites permanecen fuera de Git; el TL contrastó el índice y los924 hashes finales antes de su cierre documental. El control no acredita sandbox ni sustituye originales y controles independientes del PM.

Estado: implementación entregada, revisión y validación independientes del incremento PENDING; aprobación humana final nueva PENDING. Evidencia anterior no afectada conserva revisión/base/fecha/entorno originales. Móvil diferido y M5 simulado/externo no se reabren; las reviews humanas de Alejandro y Lucía, CI y publicación siguen bajo PM. Archivo previo conservado, sin desarchivar, commit/push ni publicación autorizados por este registro.


## Cierre técnico independiente del incremento PR81 — 08/10/2026

Este cierre actualiza únicamente los pendientes técnicos locales del incremento correctivo; conserva los resultados históricos, el archivo previo y sus aprobaciones con su alcance original. HEAD recibido `aa8f276ba04dba51148d11a8d6315dec26d8d32c`, base `2f9a5f530c9fe3b60007ba5060c189133e353bf6`; incremento todavía sin commit publicado. Aprobación humana final nueva PENDING. Roles humanos: Paris líder, Víctor pairing, Alejandro revisión, Lucía validación; proceso 2026-09-30/JUP-100.

Revisor examinó el incremento y ejecutó 26 casos backend y 2 frontend PASS (59 no seleccionados). Su REVIEW_FAIL original identificó solamente DOC-01: un párrafo histórico de diseño parecía mantener pendiente el contrato temporal ya aprobado. TL añadió la aclaración sin borrar el párrafo; la relectura independiente terminó REVIEW_PASS a las 21:42:19 Atlantic/Canary, sin repetir suites. Addendum SHA256 `5d7df1e1cf80d3a9a512374fc803cdd383b0825be70464c4bd45a7d73970bb4a`; el fallo inicial no se reescribe.

Validador entregó LOCAL_CORRECTIVE_SCOPE_PASS_WITH_DECLARED_LIMITS: 18 casos propios PASS (10 configuración/presupuesto, 4 tiempo/recuperación, 4 credencial exacta/incrustada con recibo, POST, replay y GET de otro usuario). Conservó las aserciones originales de credenciales en un adaptador externo Windows que permite IPC loopback y deniega conexiones externas. El intento nativo bloqueó socketpair interno de asyncio; Linux carecía de pytest y no ejecutó casos. Ambos intentos quedan registrados, sin atribuirles éxito ni cambiar producto/tests.

Seis GET autenticados desde el host con DB/cola/procesador/vector sanos: 1,891–2,250 s; dos Azure simulado detenido failed/connection: 5,968–6,078 s; dos recuperados ok/simulated: 1,953–2,266 s. Todos inferiores a 18 s servidor/20 s cliente. Panel autenticado /system-health: sano, caída y recuperación 6→5→6; proveedor sin verificar y actividad vacía declarados correctamente. Capturas persistentes de los tres estados y procedencia SHA256 del build Vite en el informe externo. Cuotas agregadas verificadas de seis contenedores: 8 CPU/7040 MiB; host físico 28 CPU/33,6 GB y navegador fuera de cuotas. No es reproducción física exacta del entorno de Lucía. Recursos propios detenidos y conservados, puente/pestañas cerrados; sin LLM pagado, secretos reales o servicios ajenos.

Evidencia externa: jup047-corrections-validation-20261008/REPORT.md SHA256 `b8e2fe5677720eec1487f6ca71be62e82807273fa735dfe9aba1544ad32af07e`; result.json `73ecdbc619e3f7ac65efbbb01c2cf17afe12414ff0ec7fea1e55de1270b548a8`; evidence-index.json `b70788aee82926497d67b7fe425751a36c33fb78bf07fbd4d94890fa191b13a4`, 19 archivos verificados por TL. No se suman campañas: 896 backend PASS/34 SKIP y 99 frontend PASS son Green previo del Desarrollador; 14/14 mutantes detectados pertenecen a aquella campaña y conservan su disposición individual.

PM comunicó control independiente de retorno Validador PASS, salida 0/sin violaciones, a las 22:04:08 Atlantic/Canary, contra el mismo original SHA256 `272a036944049b30a9390a28c76e860ee6f35eb166e6120de521d061efb835df`. Validador repitió su guard final PASS/0 violaciones a las 21:05:19 UTC y cedió la plaza a las 22:05:32 Atlantic/Canary. PM había comunicado retornos Revisor y DOC-01 PASS a las 21:39:07 y 21:43:20. TL verificó identidad de las 924 fuentes respecto al original validado antes de esta adenda y conserva comprobación de identidad de producto/tests al cierre. Controles conductuales, sin afirmar sandbox de lectura; PM conserva el control independiente final antes de publicación.

AC1–AC3 acreditados únicamente para este incremento local. AC4 global y vínculo/publicación de AC5 NOT_VALIDATED aquí; requieren PM y participantes humanos. Las 34 pruebas opt-in JUP086, CI remota, proveedor pagado y DockerServer/M5 remoto no se han validado en esta campaña. Móvil sigue diferido; la observación informativa de desplazamiento horizontal global a 390 px no es un PASS móvil ni amplía el alcance.

Pendientes: aprobación humana final nueva, control final independiente PM, autorización específica y ejecución de commit/push, lectura oficial actualizada de todas las reviews/comentarios/conversación, CI y vínculos tras publicar, respuesta autorizada y relectura/revalidación por Alejandro y Lucía. No se desarchiva, no se altera el DoD activo histórico ni se solicita nuevo archivo. Este registro no autoriza publicaciones ni sustituye reviews humanas. PM aplica sus comprobaciones y, si propusiera publicar con acciones propias pendientes, las dos confirmaciones específicas exigidas.


## Aprobación humana final del incremento correctivo — 08/10/2026

Paris respondió literalmente «aprobado» a la pregunta explícita de aprobación final de la entrega correctiva y autorización de commit/subida a PR81. Fuente: confirmación del Project Manager en el chat `01a1063b-fed3-7480-a0d6-cc6f374ecacf`, 08/10/2026 22:12:11 Atlantic/Canary; no se dispone del segundo exacto del mensaje humano. PM confirmó además su control independiente final previo: sólo los cuatro documentos de cierre diferentes y las otras 920 fuentes intactas frente al original validado, sin cambios Git.

Esta decisión supersede únicamente los estados PENDING de aprobación final humana del incremento y de autorización de commit/subida consignados arriba; conserva esos registros históricos, dictámenes, resultados y límites. PM ejecutará commit/subida a PR81 y comprobará CI. El comentario/respuesta requiere que PM lo muestre y Paris lo apruebe: todavía no está autorizado. Las reviews humanas de Alejandro y Lucía y los restantes gates oficiales permanecen pendientes. TL sólo registra esta aprobación, sin producto/tests, Git, nuevas pruebas, delegación ni publicación.
