# JUP-047 — evidencia técnica local

## Revisión y autoría

Consolidación E15, 08/10/2026, Atlantic/Canary. Código examinado: `feat/JUP-047-system-health-dashboard`, HEAD `8770897bab29c79df54659e362f89d97c28b132a`; padres `e1f58d01ed984be95021953bebb97ab9b5479ad0` y base incorporada `2f9a5f530c9fe3b60007ba5060c189133e353bf6`. Siete commits de develop; dos README combinados sin conflictos. El fetch de PM 13:11:51 es la última observación remota transmitida; no se acredita otra consulta.

Fuentes nativas: [change activo](../../openspec/changes/archive/2026-10-08-jup-047-system-health-dashboard/proposal.md), [diseño](../../openspec/changes/archive/2026-10-08-jup-047-system-health-dashboard/design.md), [review](../../openspec/changes/archive/2026-10-08-jup-047-system-health-dashboard/review.md), [tareas](../../openspec/changes/archive/2026-10-08-jup-047-system-health-dashboard/tasks.md), [mapa](../../openspec/changes/archive/2026-10-08-jup-047-system-health-dashboard/acceptance-map.md), [runbook](../runbooks/system-health.md). Proceso [CONTRIBUTING](../../CONTRIBUTING.md#review-and-validation-flow), 2026-09-30 (JUP-100).

Los ejecutores locales automatizados fueron Desarrollador, Revisor y Validador, con encargos separados. Roles humanos transmitidos por PM: Paris liderazgo, Víctor pairing, Alejandro revisión/M5 y Lucía validación. La asignación no acredita su participación ni convierte trabajo de agentes en trabajo humano. No hay PR, reviews humanas o vínculos oficiales acreditados. Esta evidencia no declara aceptación global.

## Campañas, resultados y entorno

| Campaña | Autoría y ejecución | Resultado |
|---|---|---|
| Implementación previa de retención/ciclo visible | Desarrollador, fases separadas con Red/Green/correcciones y originales conservados | 341 PASS históricos (123 frontend/218 backend); no se suman a la campaña completa nueva |
| Sensibilidad histórica | Desarrollador, copias restauradas y guards | 27 operadores dispuestos:25 kills reutilizados por identidad y dos reensayos de aquella fase; cero nueva mutación postmerge |
| Matriz nueva sobre el HEAD reconciliado | Desarrollador,35 comandos con exit 0, copia exacta 920 fuentes | 2013 PASS/0 FAIL/91 SKIP; build/lint/tipos y OpenSpec 53/53 |
| Revisión afectada postmerge | Revisor independiente,13:55; cotejo de delta, contratos y recibos | REVIEW_PASS local; cero suites/build/mutaciones propias nuevas |
| Validación afectada postmerge | Validador independiente, frontend 14:02:36–14:02:55 y backend 14:03:12–14:03:15 | LOCAL_POST_BASE_PASS; 85 frontend+10 backend PASS/0 FAIL/ERROR/SKIP |

La campaña completa del Desarrollador comprende Azure Cost API 59 PASS, processor 448 PASS/57 SKIP, backend 877 PASS/34 SKIP y frontend 629 PASS en 53 archivos. Contiene también el alcance de los 341 anteriores, por identidad de fuente; no se suman a 2013 ni se agregan los 95 del Validador. Los 123 frontend históricos abarcan ocho archivos; los tres archivos health/API propios contienen 99, sin confundir ambos ámbitos.

Entorno local: Windows, Python 3.12 aislado, Node 24.17.0 y dependencias existentes, datos sintéticos, SQLite, dobles de transporte y reloj. CI declara Node 22: esta ejecución local no acredita esa CI ni proveedores remotos. No hubo instalaciones ni activación de Docker/DB/gateway/servicios reales, navegador o nueva inferencia.

Integridad:920 fuentes del worktree y copia cotejadas; 29 propias no solapadas intactas,100 entrantes idénticas a develop y siete orígenes retirados conforme al target. El Revisor verificó las secciones completas de salud en ambos README y 145/145 artefactos del índice del Desarrollador. Validador verificó esos recibos y su propia copia antes/después. Los controles de módulos cargados señalan la copia examinada.

## Matriz mínima y equivalencia de ejecución

Se cotejaron 40 filas con todos los jobs, matrices y condiciones de CI y los siete mínimos de CONTRIBUTING. La campaña del Desarrollador acreditó:

| Mínimo | Ejecución observada | Resultado |
|---|---|---|
| jup:check:all | node tools/jup-check.mjs --all | exit 0 |
| pr:check:test | node --test tools/pr-policy.test.mjs | exit 0 |
| ci:check:test | node --test tools/ci-workflow.test.mjs | exit 0 |
| repository:governance:test | node --test tools/repository-governance.test.mjs | exit 0 |
| openspec:validate | CLI 1.8.0 validate --all --strict --no-interactive | exit 0,53 PASS/0 FAIL |
| test | Scripts completos de azure-cost-api, processor, backend y frontend, sin filtros que excluyan suites | PASS_EQUIVALENT; 2013 PASS/91 SKIP |
| build | Tres python -m compileall app y frontend vite build | PASS_EQUIVALENT, cuatro procesos exit 0 |

Además pasaron todos los scripts de gobernanza de CI, incluido synthetic-costs:test, trazabilidad/higiene, corpus, preguntas/labels, calibración/métricas, configuración gateway, topología Docker, tooling local y colaboración. Frontend: eslint src tests y los tres TypeScript (`--noEmit`, `-p tsconfig.node.json --noEmit`, `-p tsconfig.test.json --noEmit`) dieron exit 0.

Los scripts se ejecutaron directamente con los runtimes y dependencias ya instalados. shared-config no define test/build. La equivalencia omite solo orquestación/caché de pnpm/Turbo; conserva todos los paquetes, colecciones y assertions. **No se ejecutaron literalmente pnpm/Turbo ni instalación frozen-lockfile.** El intento pnpm 9 falló por caché ausente con red desactivada, exit 1 conservado; no se instaló nada para ocultarlo.

También se conserva el exit 1 del primer wrapper después de que el merge terminara exit 0: su verificador omitía orígenes de movimientos de OpenSpec. El control posterior comparó el delta completo con --no-renames, sin remerge, rollback ni cambio de producto. Fallos de pruebas y mutantes anteriores mantienen sus resultados originales. Estos incidentes de herramienta no son nuevos defectos de producto ni se convierten en PASS retrospectivo.

## Selección independiente y reproducción offline

Usar una copia de la revisión indicada, dependencias ya disponibles y configuración sintética de tests. No cargar dotenv privado ni activar variables opt-in de servicios reales. No hace falta abrir el panel, esperar diez minutos reales ni consumir proveedor. Estos comandos reproducen la **selección** efectivamente ejecutada; no fueron reejecutados en esta consolidación documental. Los recibos SHA 256 siguientes conservan el argv completo, configuración, rutas temporales, comandos y auditoría de origen de la ejecución original.

Frontend, desde apps/frontend, con Vitest 3.2.7 disponible:

```text
vitest run src/routes.integration.test.tsx src/layouts/SessionGate.validation.test.tsx tests/tenant-switching.test.tsx src/pages/ExecutiveCostDashboard.jup055.test.tsx
```

Observado en la ejecución independiente:85 PASS, exit 0. La campaña original añadió configuración externa de auditoría y reporteros JUnit, sin modificar producto o tests. Para reproducir el comportamiento ordinario se usa la configuración versionada; esa reproducción no sustituye la auditoría original ni se declara ejecutada aquí.

Backend, desde apps/backend con Python 3.12 y dependencias de requirements-dev disponibles:

```text
python -X utf8 -B -m pytest -p no:cacheprovider tests/test_assistant_service.py tests/test_billing_summary.py::test_invalid_selection_is_422_before_billing_read tests/test_tenant_isolation_api.py::test_citations_persist_and_reopen_with_authorized_conversation -q --tb=short -o faulthandler_timeout=60
```

Observado:10 PASS, exit 0. El comando original añadió auditoría externa de origen y rutas de JUnit/temporales. Para Windows, el adaptador externo de asyncio de la campaña completa conserva las dos fixtures no-network originales, sus denegaciones reales, pool 64, cierre y restauración; fixture desconocida causa error. Ese auxiliar no se copia al repositorio ni permite eludir las negativas de red.

Esperado/observado: apertura directa de ruta con sesión, navegación conserva tenant, sesión ausente o user/JSON parcial no hace fetch, cambio de tenant aísla borradores/respuestas tardías, facturación válida y asistente con/sin contexto y citas de conversación autorizada. **Caso de error:** billing rechaza selección inválida con 422 antes de leer datos (fechas y group_by inválidos). **Bordes:** user parcial sin fetch y error tardío ajeno aislado. Resultado favorable local, sin observación real de servicios.

Los controles documentales de E15 son OpenSpec estricto, trazabilidad global, higiene, enlaces relativos, whitespace del delta y guards de sus cuatro rutas. La evidencia conductual anterior sigue aplicando por identidad de producto/tests; no se repiten suites/build/mutación en este tramo.

## Criterios oficiales y límites

| Criterio | Esperado y observado | Dictamen del Validador y límite |
|---|---|---|
| AC1. Resultado funcional verificable | Composición ruta/sesión/tenant/billing/asistente conservada; 95 casos propios, incluido 422 previo a lectura | PASS_LOCAL_AFFECTED; sin M5/proveedor real ni visual nuevo |
| AC2. Pruebas necesarias añadidas y en verde |85+10 propios sin fallos/omisiones; campaña 2013/91 auditada y 35 comandos satisfactorios | PASS_LOCAL_AFFECTED; 91 integraciones opt-in y CI remota NOT_VALIDATED |
| AC3. Documentación y decisiones actualizadas | Sin TTL, ciclo visible 600000, UTC 1000 y Azure SIMULADO coherentes; README y especificación conservados; revalidación documental anterior favorable | PASS_LOCAL_AFFECTED; E14/VALIDATION_FAIL históricos no se reescriben |
| AC4. PR revisado y vinculado | No PR, enlaces ni reviews humanas acreditados | NOT_VALIDATED global |
| AC5. Validación funcional y evidencia enlazadas | Evidencia técnica local disponible; publicación/vínculos oficiales y controles humanos pendientes | NOT_VALIDATED global; M5 real pendiente con Alejandro |

Las 91 omisiones son NOT_VALIDATED: processor 52 CockroachDB,4 pgvector y 1 opt-in Docker; backend 14 CockroachDB,17 pgvector y 3 RabbitMQ. Son skips reales de fixtures existentes, no casos aprobados ni pruebas suprimidas. No se reclama CI remota, flujo literal pnpm ni un despliegue M5.

Paris aceptó la presentación que él observó a las 13:05:44; no se atribuye al Validador. No hay nuevo ensayo UI/teclado ni reapertura del [finding móvil diferido RF-026-002](../../openspec/findings/backlog.md#rf-026-002). **0,20 EUR es el techo autorizado acumulado incluido el histórico, no gasto acreditado**; la adenda corrige esa atribución del informe original sin modificarlo. Cero llamadas o gasto nuevos en estas campañas/consolidación.

Aprobación humana final post-base **PENDIENTE**, con bloque explícito en review.md. El archivo en esta misma rama está específicamente autorizado 13:11:51, pero requiere despacho posterior tras aprobación y DoD final del change activo. M5/Alejandro, pairing efectivo de Víctor y reviews humanas son externos, no sustituidos por agentes ni impedimento del gate local previo al archivo. PM coordina CI remota, PR, publicación y vínculos oficiales; no se ejecutan aquí.

## Fuentes y controles independientes

| Recibo original externo | SHA 256 |
|---|---|
| Manifiesto de 920 fuentes antes de E15 | `bd05c0949c44a67f27f11a53a2956a99874d01a0c29791d9b2d8a9b41db0133c` |
| Dev, handoff postmerge | `8af91a16368715db7d2c4a310c22db2da462e550ad27aea7207e04ca71ff13a2` |
| Dev, índice 145 artefactos | `4e4560577cdb6e86e862ce6b6974b9616362143b5b7191f3475150a0dea6d53d` |
| Revisor, handoff | `6ee24e1ba034c2a6114401f0cf35298dfec883cb71308bf712f9241ea702dc96` |
| Revisor, adenda techo/gasto | `2600b0b444a2f1897b04c8349c45d635bb7d712249448dbccbc185daafadf545` |
| Validador, handoff | `86852d562997a8b81be3a523e3a96a1a0f8ddfc471bf93b343ca22d947649a15` |
| Validador, informe | `2d67d1bae81c040df16d9fb2cac83b97a7ca64aac6a657311e4bbf1cda3d4977` |
| Validador, índice 32 artefactos | `fb3ad70443b8a102ad33c98e373c620ee7ba0be3b04f74cc021081169fe9f3da` |

PM conservó originales independientes Revisor `b7b15a4b43a3df69ad88a8e6345f54b3c42ed7dffff3fea69f9da7ad99915097` y Validador `37e35026768ff6cbfbdab818099c232cabc204d84594782baf13cc3b85918955`. TL 14:09:37 comunica retornos PASS contra los mismos originales; Val retorno 14:07:55, cero violaciones. Son hechos comunicados, no recibos nativos fabricados aquí ni prueba de sandbox de lectura.

Los originales, tiempos y logs permanecen fuera de Git; los hashes permiten a PM comprobar su correspondencia. Se publican solo conclusiones y referencias nativas estables, sin volcar credenciales, capturas privadas o ledger financiero.


## Aprobación humana final posterior a la base — 08/10/2026 14:36

Paris Arcos aprobó la entrega local final con respuesta literal «si» el 08/10/2026 a las 14:36, Atlantic/Canary; el segundo exacto del mensaje humano no está disponible. PM confirmó la decisión a las 14:36:07 y TL verificó la pregunta y respuesta originales. Fuente: mensaje humano `01a11bba-6640-7c71-8d13-3b541b40f4b4`, turno `01a11bba-65e9-7b81-a303-fe0c1ca509e8`; pregunta en turno `01a11bb9-af92-7fb3-934e-fe48c355393a`, chat PM `01a1063b-fed3-7480-a0d6-cc6f374ecacf`. La pregunta, alcance y fuente verificada se registran en [la aprobación de review.md](../../openspec/changes/archive/2026-10-08-jup-047-system-health-dashboard/review.md#post-validation-human-approval--approved).

Esta nota supersede únicamente el estado PENDING de la aprobación humana final post-base consignado históricamente en E15; conserva literalmente el contenido anterior, sus casillas y los resultados AC1–AC3 locales y AC4/AC5 globales NOT_VALIDATED. El código revisado sigue siendo `8770897bab29c79df54659e362f89d97c28b132a`, base `2f9a5f530c9fe3b60007ba5060c189133e353bf6`. Por identidad de producto, tests, base y alcance se reutilizan los dictámenes y campañas anteriores con sus fechas y límites; no son dictámenes nuevos ni nuevas ejecuciones.

El pre-validation DoD del change activo fue PASS por TL. El registro de aprobación y DoD final activo corresponden al TL; el archivo específicamente autorizado a las 13:11:51 requiere después un encargo separado. No se archiva aquí ni se concede permiso de commit, push, PR o publicación. Los controles humanos, M5 y vínculos oficiales conservan sus límites y responsables.


## Corrección de encabezados previa al archivo — 08/10/2026

OpenSpec 1.8.0 abortó el archivo antes de escribir: el parser canónico interpretó las notas históricas E12 de nivel 3 como requisitos adicionales sin escenarios. Paris autorizó literalmente «SI» el 08/10/2026 a las 15:07, Atlantic/Canary (segundos humanos no disponibles; confirmación PM 15:07:04), cambiar únicamente esos dos encabezados de `###` a `##` y añadir esta nota. Fuente verificada por TL: mensaje humano `01a11bd6-bc55-7692-8723-a5d23ba53a37`, turno `01a11bd6-bbfb-7a91-af64-63cbfd948fa4`, pregunta `01a11bd5-0b69-7be1-b355-a8310e05f788` en el chat PM.

Todo el texto histórico, requisitos, escenarios, casillas y aprobaciones anteriores permanece intacto. La aprobación final post-base de las 14:36 y el DoD final previo se conservan como hechos de su momento; TL renovará contexto, matriz y DoD final con el change ACTIVO antes de un nuevo despacho de archivo. Se preservan el aborto de la CLI y el rechazo inicial del encargo anterior a esta autorización concreta. No se reintenta el archivo en esta corrección ni se alteran producto o tests.


## Archivo específico y DoD final local — 08/10/2026

El change JUP-047 quedó archivado el 08/10/2026 en `openspec/changes/archive/2026-10-08-jup-047-system-health-dashboard`, en la misma rama `feat/JUP-047-system-health-dashboard`, código `8770897bab29c79df54659e362f89d97c28b132a` y base `2f9a5f530c9fe3b60007ba5060c189133e353bf6`. Se incorporaron los deltas a las especificaciones [health-status](../../openspec/specs/health-status/spec.md) y [system-health-dashboard](../../openspec/specs/system-health-dashboard/spec.md); los dos requisitos anteriores de health-status permanecen.

Paris aprobó la entrega local final el 08/10/2026 a las 14:36, Atlantic/Canary, con respuesta literal «si»; los segundos humanos no están disponibles y PM confirmó a las 14:36:07. Paris autorizó la corrección mecánica de los dos encabezados E12 a las 15:07, con respuesta literal «SI», confirmada por PM a las 15:07:04; el intento de archivo anterior quedó abortado sin cambios. Tras esa corrección, TL renovó el DoD final code/final con el change todavía ACTIVO: PASS, exit 0, sin errores; registro UTC `2026-10-08T14:16:00.6434523Z`. Se conserva [el resultado original exacto de ese DoD final renovado](../../openspec/changes/archive/2026-10-08-jup-047-system-health-dashboard/local-dod-final.json), SHA256 `4b1b13ff29ea848e7d71e37b99c2e660a81d2bbc8a8a9ca2bc388a74095fda82`. No se vuelve a ejecutar el helper tras retirar el directorio activo.

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
