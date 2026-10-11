# Evidencia técnica — JUP-054

Fecha: 2026-10-10. [Trello](https://trello.com/c/ZsxwmagI).
[PR #93](https://github.com/EconomiconFinOps/tfm-economicon/pull/93), rama
`test/JUP-054-critical-flows`. Base: `c2995a118d419dfe725247bac9c6f219a3f0ea77`.

## Entrega y atribución

Siete casos nuevos conectan componentes que antes se probaban por separado:
API Azure local HTTP → cliente → normalizador → SQL SQLite (4); AgentRuntime →
LangGraph → IngestTask → SQL SQLite (3). Se amplía el recorrido real existente
CockroachDB/RabbitMQ/pgvector con GET del historial, igualdad de mensajes/citas,
JSONB y denegación entre tenants. No se reimplementa producto ni se repite JUP-087.
Vitest se invoca directamente dentro de su job CI, sin caché Turbo.

[Matriz, límites y reproducción](../testing/critical-flows.md).
OpenSpec: `jup-054-test-strategy-and-critical-flows`.

Contribución preparada en copia aislada
`C:/Users/DanteInferno/Documents/Economicon/tfm-economicon-jup054`; el checkout
compartido y las ramas ajenas permanecen intactos. Roles confirmados por la
integración oficial de DockerServer el 10/10: Lucia Mateo, liderazgo; Paris
Arcos Martin, pairing; Victor Mendez, revisión; Alejandro Aguado,
validación/pruebas/documentación. Son las asignaciones nominales iniciales, no
una certificación de participación efectiva.

**Excepción por entrega del MVP fuera de plazo, autorizada por el usuario el
10/10/2026:** completar la implementación y el cierre de JUP-054 sin esperar la
adopción y los dictámenes humanos inicialmente pendientes. La ejecución,
pruebas, documentación e integración se atribuyen a Alejandro (`Iber1to`) con
asistencia de Codex. La revisión técnica asistida no encontró hallazgos nuevos;
incluye autorrevisión de las aserciones de historial, no independencia humana.
No se acredita pairing ni aprobación humana no observados. Se usa la excepción
administrativa ya existente, sólo mediante PR y tras los controles técnicos,
sin alterar protecciones. [Registro de atribución](../contributions/README.md#excepción-de-entrega-del-mvp--jup-054).

OpenSpec archivado en
`openspec/changes/archive/2026-10-10-jup-054-test-strategy-and-critical-flows/`;
los tres requisitos están en `openspec/specs/critical-flow-testing/spec.md`.

## Resultados aprobados

[CI push 38035094870](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035094870)
y [CI PR 38035169344](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035169344)
aprobados sobre `69b9e7fb91a3ab1c7f5578aa46b4c29a494a0df5`. Los logs del primero
conservan estos conteos. Los checks del head vigente se consultan en la PR.

| Verificación | Resultado observado |
| --- | --- |
| Backend completo, CI Linux | 898 passed, 34 skipped |
| Processor completo, CI Linux | 455 passed, 57 skipped, incluidos los 7 casos nuevos |
| Azure Cost API completo, CI Linux y Windows | 59 passed |
| Frontend completo, CI Linux | 629 passed en 53 archivos |
| Frontend lint, tipos y build | Exit 0 en Windows y CI Linux; aviso existente de bundle grande |
| Nueva integración agente, Windows aislada | 3 passed |
| Repetición final de los 7 casos juntos, Windows | 7 passed, 24.53 s, con timeout de contrato final de 10 s |
| Nuevo contrato Azure, Windows aislado | 4 passed |
| Recorrido real tenant/historial, Linux aislado | 3 passed, 14.23 s; sin skips |
| Checks locales CI/política/gobernanza | 82 passed |
| Trazabilidad / OpenSpec | Exit 0 / 56 passed, 0 failed |

Son **2041 pruebas de aplicación aprobadas en CI**, más los tres escenarios
reales externos a CI. Los 91 skips de servicios no prueban sus integraciones.
`JUP reviews` no dispone de dictámenes humanos y no se presenta como verde;
su exigencia para este cierre queda exceptuada por la autorización anterior.

### Revalidación tras integrar JUP-102

Durante el cierre se actualizó la base con `d7c0725` (PR #108): dimensión
vectorial explícita desde Settings. Los conflictos se limitaban al puntero
AGENTS y al índice de continuidad; se conservaron ambas aportaciones.
La actualización sí afecta a migraciones usadas por el recorrido real.

Sobre los fuentes reconciliados se repitió el archivo completo
`test_tenant_isolation_integration.py` y el caso
`test_vector_settings_pgvector.py::test_new_schema_settings_sources_and_real_retrieval[default-8]`:
**4 passed en 13.23 s, 0 skips** (3 recorridos JUP-054 y una comprobación JUP-102).
Se usaron los mismos servicios desechables, una red propia sin puertos publicados
y PostgreSQL con contraseña exclusiva de prueba. Se transfirieron los mismos
130 fuentes permitidos, más ese único archivo de pruebas JUP-102.
Artefactos `.artifacts/jup054/linux-reconciled-{source.tar.gz,real.log,real.xml,python-dependencies.txt}`.
Los contenedores y la red exclusivos se retiran al terminar; recibo
`reconciled-cleanup.txt`. No se modifica ni reinicia infraestructura compartida.

Los conteos de la tabla anterior pertenecen a la base inicial. El CI completo
del último commit de PR #93 se vuelve a ejecutar tras esta reconciliación;
los tests incorporados por JUP-102 pueden aumentar los conteos.

## Intentos Windows y contraste

Los intentos que fallaron se conservan, no se borran de la evidencia:

- Backend completo: 729 passed / 169 failed / 34 skipped. En 145 fallos, los
  fixtures de JUP-047 interceptan `socket.connect` usado por el `socketpair`
  interno de asyncio Proactor en Windows, antes de invocar el endpoint. Los
  otros 24 afectan a observaciones con plazos breves de DNS, publisher,
  embeddings y concurrencia. Backend no tiene cambios respecto a la base.
- Processor completo: 448 passed / 7 failed / 57 skipped. Cuatro plazos de
  streaming existentes, dos subprocessos existentes a 30 s y una lectura HTTP
  del nuevo contrato a 2 s. Las siete nuevas pruebas pasaron por separado.
- Frontend Windows: se observaron timeouts a 5 s y errores de expectativas bajo
  carga; se interrumpió el intento tras completar las 629 pruebas en CI Linux.
  No se atribuye un conteo final de éxito al intento interrumpido.
- Integración real Windows: 3 fallos (subprocess a 30 s y publicación 503).
  Misma suite y aserciones en Linux: 3 passed. No se relajan sus plazos ni guards.

Todos los tests completos afectados pasan en CI Linux. La carga es una
explicación compatible para los plazos; no prueba por sí sola su causa. La
colisión socketpair/guard en Windows sí está confirmada por la traza.
El fixture nuevo de contrato usa finalmente 60 s de readiness y 10 s de lectura:
no evalúa latencia, que ya tiene su suite específica. No se modifica ningún
límite temporal del producto ni de pruebas existentes.

## Entorno, artefactos y ciclo de vida

Windows: Node 24.14.1, pnpm 9.0.0, Vitest 3.2.7, Python 3.12.13. Entorno virtual
nuevo con requirements-dev de los tres servicios; CI usa Node 22 y entornos
Python separados. Linux aislado: Python 3.12.13, FastAPI 0.143.0, SQLAlchemy
2.0.54, psycopg 3.3.6, pytest 9.1.1, LangGraph 1.2.14, httpx 0.28.1.
Dependencias Python resueltas completas: `.artifacts/jup054/*python-dependencies.txt`.

Comandos completos y límites de fixtures están en la matriz. Se usaron pytest
por servicio y Vitest directo; ningún resultado deriva de un hit de Turbo.
Los nuevos tests finales se ejecutan juntos con:

```sh
# Desde apps/processor, con el entorno Python activado:
python -m pytest tests/test_azure_api_contract_integration.py tests/test_agent_ingestion_integration.py -q -ra
```

Para el recorrido real se crearon exclusivamente `economicon-jup054-crdb`,
`economicon-jup054-vector`, `economicon-jup054-rabbit` y `economicon-jup054-runner`,
con límites de recursos y sin volúmenes compartidos. DockerServer recibió sólo
130 archivos fuente/fixtures revisados (550528 bytes), sin dotenv, repositorio
Git, entornos ni archivos personales. El runner usó red puente privada,
`--cap-drop ALL` y `no-new-privileges`; proxies propios proporcionaron loopback
para respetar los guards existentes. La alternativa inicial de copiar el proyecto
completo con red del host fue rechazada por la revisión automática y no se ejecutó.

Imágenes del recorrido real (IDs Docker):

- Cockroach `v24.1.11`: `sha256:89bda255c52b25f463c7a9373ffedef122a4d9f1b432aa34b897970fe864a66c`.
- pgvector `pg17`: `sha256:cf134a767f474095eeba57e0117be8e568e011a63f33fbf252f14c9b760f8e6f`.
- RabbitMQ `3.13-management`: `sha256:e582c0bc7766f3342496d8485efb5a1df782b5ce3886ad017e2eaae442311f69`.

Artefactos locales en `.artifacts/jup054/`, excluidos de Git:

| Archivo | SHA-256 |
| --- | --- |
| `linux-reviewed-source.tar.gz` | `C916D51A5733247B1D338C215552F5AA593ED5DF71DA7D238DD140C8C0D0BF59` |
| `linux-real-integration.xml` | `9CDC6F84E7341BE67D9B00FC636AABF0C253B32195A7C9879A427BFBB4626F22` |
| `ci-38035094870.log` | `8F557C6BF99F41587EF0EA3330F359D6CA5F08050384711F191C5EC094703519` |

XML, logs y comandos de la ejecución real quedan conservados. Se retiran los
contenedores/red/túnel propios tras comprobar sus etiquetas de propiedad;
recibo local `cleanup.txt`. No se toca ningún servicio compartido.

## Criterios y límites de la entrega

| Criterio de Trello | Evidencia / situación |
| --- | --- |
| Resultado funcional verificable | Contratos, persistencia y errores comprobados en las suites nuevas y reales |
| Pruebas necesarias añadidas y en verde | 7 casos nuevos, suite CI completa y recorrido real aprobados; limitaciones Windows arriba |
| Documentación y decisiones actualizadas | Matriz, OpenSpec, este informe y continuidad |
| Pull request revisado y vinculado | PR #93 enlazada; revisión técnica asistida sin hallazgos, requisito de revisión humana exceptuado por plazo MVP |
| Validación funcional y evidencia enlazadas | Evidencia técnica por criterio; aceptación independiente exceptuada por plazo MVP |

La PR registra el evento de integración administrativa y Trello el cierre de la
tarjeta conforme a esta excepción. Sin mensajes Discord. La evidencia no acredita Azure
cloud, LLM externo, gateway LiteLLM real, reinicio RabbitMQ, todas las migraciones,
Compose completo ni navegador real. RF-096-004 (infraestructura en CI) sigue separado.

## Segunda pasada: cobertura del candidato final

Fecha: 2026-10-10. [Trello](https://trello.com/c/ZsxwmagI). Rama
`test/JUP-054-final-candidate-coverage`. OpenSpec:
`jup-054-final-candidate-coverage`. Las secciones anteriores son la primera pasada
(PR #93) y se conservan con su atribución; ésta no las modifica ni las repite.
Es una contribución con el flujo ordinario de revisión y validación: la excepción
de plazo del MVP que cerró la PR #93 no se extiende a ella. Estado: **en curso**.

### Candidato auditado y referencia

- Candidato: `develop` en `e1c2a8f64399ec9434b57ac31d86ac9b09e73f72`
  (`origin/develop` comprobado el 2026-10-10; sin commits posteriores). Se mide el
  árbol de ese commit con `git archive`, no el de la rama de trabajo.
- Referencia de CI: [ejecución 38079384876](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38079384876),
  evento `push` sobre `develop` y ese SHA. Seis jobs en `success`: Frontend build,
  Frontend type check, OpenSpec y las tres Python tests (azure-cost-api, backend y
  processor). `JUP policy` figura `skipped` porque sólo se evalúa en pull requests.
- Los registros de Actions exigen autenticación y el entorno de medición no tiene
  credencial: el resultado por job se verificó con la API pública y los conteos se
  copiaron a mano de los registros desde una sesión autenticada de GitHub (el
  paso `Run tests` de cada job Python y `Test frontend journeys` del job
  `Frontend build`).

| Servicio | Resultado del job | Aprobadas | Fallidas | Omitidas | Línea del registro |
| --- | --- | --- | --- | --- | --- |
| azure-cost-api | success | 59 | 0 | 0 | `59 passed, 1 warning in 0.61s` |
| backend | success | 960 | 0 | 62 | `960 passed, 62 skipped, 2408 warnings in 122.01s (0:02:02)` |
| processor | success | 462 | 0 | 65 | `462 passed, 65 skipped, 822 warnings in 11.61s` |
| frontend (Vitest en `Frontend build`) | success | 654 | 0 | 0 | `Test Files  56 passed (56)` / `Tests  654 passed (654)` |
| **Total** | | **2135** | **0** | **127** | |

Son los conteos de la referencia de CI, no de esta pasada. Respecto al cierre de la
PR #93 (2048 aprobadas y 99 omitidas) el candidato suma 87 aprobadas y 28
omitidas más. El origen de esas omitidas nuevas no se ha investigado todavía: la
auditoría de huecos (grupo 3) debe separar cuáles son suites opt-in con servicios
reales y cuáles no.

### Entorno de medición

Contenedores Linux desechables equivalentes a CI, sin volúmenes compartidos con el
repositorio ni puertos publicados. La herramienta de cobertura se instala sólo
dentro del contenedor; no entra en el repositorio ni en `pnpm-lock.yaml`.

| Elemento | Valor |
| --- | --- |
| Docker (cliente y servidor) | 29.8.1, `linux/amd64` |
| Imagen Python | `python:3.12`, `sha256:63828510c8b5ccce3bf0d6fabd6f3d17d4effa1ffe690f80a67c8e2d394e03ee`, Python 3.12.15 |
| Imagen Node | `node:22`, `sha256:0e5f906573693feaa1e21057ebdcfdb5bd5021f050b2dc7c9deceb629c7da2a8`, Node v22.23.3, corepack 0.36.0 |
| pnpm | 9.0.0 (`packageManager` del repositorio) |
| Cobertura Python | `pytest-cov==7.1.0`; `coverage` lo resuelve pip y se anota al medir (última publicada: 7.16.2) |
| Cobertura frontend | `@vitest/coverage-v8@3.2.7`, la misma versión que el Vitest resuelto en `pnpm-lock.yaml` (3.2.7) |

CI usa Python 3.12 y Node 22 en `ubuntu-latest`. Las imágenes coinciden en la
versión mayor/menor; el parche exacto de CI no se ha podido leer (ver arriba), así
que no se afirma que coincida.

### Cobertura medida del candidato

Medición del 2026-10-10 sobre el árbol de `e1c2a8f` (`git archive`), con los
comandos de [la matriz](../testing/critical-flows.md#medición-de-cobertura-diagnóstico).
Es un **diagnóstico**: no hay umbral ni se exige en ningún check. Cada cifra sólo
vale si la ejecución instrumentada reproduce a CI para ese servicio.

| Servicio | Reproduce CI | Líneas | Ramas | Archivos medidos |
| --- | --- | --- | --- | --- |
| azure-cost-api | Sí: 59 passed, 1 warning | 95,6 % (518/542) | 88,7 % (94/106) | 10 |
| backend | Sí: 960 passed, 62 skipped, 2408 warnings | 87,0 % (2950/3391) | 77,7 % (730/940) | 51 |
| processor | Sí: 462 passed, 65 skipped, 822 warnings | 88,8 % (1757/1979) | 76,0 % (357/470) | 55 |
| frontend | Sí en el 2.º intento: 56 archivos y 654 passed | 90,4 % (2990/3306) | 95,1 % (1109/1166) | 43 de 44 |

Los servicios Python usan `coverage` 7.16.2 con `pytest-cov` 7.1.0, líneas y ramas
sobre `app`, incluidos los archivos que ninguna prueba importa. El frontend usa
Vitest 3.2.7 y `@vitest/coverage-v8` 3.2.7 sobre `src/**`. La versión de Vitest
fue la misma antes y después de añadir el proveedor (3.2.7). El único archivo
de `src` fuera del informe es `src/test/setup.ts`, infraestructura de pruebas que
Vitest excluye por defecto. **Las ramas del frontend (V8) y las de Python
(`coverage`) se cuentan con criterios distintos y no son comparables entre sí.**

Intentos que no se ocultan:

- **Frontend, 1.er intento: 653 passed y 1 failed**, con el informe sin escribir.
  Falló `tests/login-session-expired-notice.test.tsx` (tarea 4.1: no encontró el
  botón «Sign in» en la espera por defecto). Se repitió el servicio completo, con
  la misma imagen y el mismo comando salvo forzar la escritura del informe: 56
  archivos y 654 passed. La prueba pasa sola y sin instrumentar (9 de 9). La causa
  no está probada; es compatible con que la instrumentación alargue la espera de
  una prueba con plazo corto, y no se cambió ningún plazo ni guard. Se usa la cifra
  del 2.º intento porque reproduce a CI.
- Los tres servicios Python reprodujeron a CI en el primer intento. La ejecución
  fue como `root` en un contenedor sin red restringida durante la instalación; CI
  usa un usuario sin privilegios. No se observó ninguna diferencia de resultado.

Pruebas que lanzan subprocesos o procesos hijo, y cuyo código hijo esta medición
no observa: processor `test_azure_api_contract_integration.py`,
`test_ingest_task.py`, `test_litellm_docker.py`,
`test_schema_migration_ownership.py` y `test_tenant_isolation_integration.py`;
backend `test_managed_resolver.py`, `test_rabbitmq_publisher.py`,
`test_system_health_boundaries_jup047.py` y el apoyo `billing_support.py`. Las
líneas no cubiertas que dependan de ellas se contrastan a mano en el grupo de
auditoría antes de llamarlas hueco. azure-cost-api no lanza subprocesos.

### Huecos de cobertura

Auditoría sobre `e1c2a8f`, con el criterio de la decisión 5 del diseño: un hueco es
**crítico** si es código de un flujo de la matriz, o añadido después de la PR #93,
que ninguna prueba ejecuta y que decide autorización o pertenencia a un tenant,
validación de entrada, tratamiento de errores con efecto visible o una escritura.
Las líneas citadas son del árbol `e1c2a8f`. **La clasificación está pendiente de
aprobación (tarea 4.1): hasta entonces no se ha escrito ninguna prueba.**

#### Procedencia del código nuevo

`git log 1f57f91..e1c2a8f -- apps` devuelve tres commits: JUP-017 (`76221e8`:
cobertura de etiquetado, backend y panel), JUP-037 (`d057537`: consultas de
ownership, backend y conversaciones) y JUP-105 (`412ae41`, sólo `routes.tsx` y
configuración del frontend). JUP-068 (`e1c2a8f`) y JUP-064 no cambian código de
aplicación.

#### Omitidas: todas son opt-in

Las 127 omitidas de CI se reprodujeron sin instrumentar (processor 462/65 y
backend 960/62 en el contenedor) y se agruparon por motivo. **Ninguna es
inesperada**: todas exigen una base, un broker o un doble que CI no provisiona.

| Servicio | Omitidas | Origen |
| --- | --- | --- |
| backend | 62 | CockroachDB 42 (`test_tag_coverage` 22, `test_billing_summary` 7, `test_ownership_provenance` 5, `test_job_publication` 2, `test_tenant_isolation_api` 2, y 1 en cada uno de `test_budget_evaluation`, `test_ownership_questions`, `test_rabbitmq_publisher_integration` y `test_tenant_isolation_repository`); pgvector 17 (`test_retrieval_contract_pgvector` 12, `test_tenant_isolation_vector` 5); RabbitMQ 3 |
| processor | 65 | CockroachDB 52 (`test_azure_cost_cockroach_integration` 34, `test_ingest_task` 6, `test_schema_migration_ownership` 6, `test_tenant_isolation_costs` 3, `test_tenant_isolation_integration` 3); pgvector 12 (`test_vector_settings_pgvector` 8, `test_tenant_isolation_vector` 4); Docker 1 (`test_litellm_docker`) |

El aumento de 28 omitidas del backend frente al cierre de la PR #93 coincide con
`test_tag_coverage` (22) + `test_ownership_provenance` (5) + `test_ownership_questions` (1).
Consecuencia relevante: **todo el SQL de cobertura de etiquetado (`fetch_tag_coverage`
y `tag_policy.py`, JUP-017) y la procedencia de ownership (JUP-037) sólo se prueban
contra CockroachDB real y CI no los ejecuta.** Offline sólo corren las pruebas de
periodo inválido y de precedencia de autenticación, que sustituyen la base por un
doble antes de llegar al SQL. Este código se lista aparte y **no es un hueco de esta
pasada ni queda acreditado por ella**; lo cierra `RF-096-004`.

#### Contraste de lo que depende de procesos hijo

Se repitió la medición de backend y processor registrando también los procesos hijo
(`patch = subprocess`, configuración sólo dentro del contenedor). Resultado:
processor idéntico (222 líneas sin cubrir); backend gana 12 líneas
(`managed_resolver.py` 6 y `rabbitmq_queue.py` 6) y las mismas pruebas pasan (960/62
y 462/65). `dns_resolver_child.py` (60) y `system_health_runtime.py` (75) no ganan
ninguna: el primero se lanza como script aislado y el segundo con `spawn`, y la
herramienta no llega a esos procesos. Por tanto esas líneas **no se han verificado**
y se clasifican abajo con esa salvedad, sin darlas por ejecutadas.

#### Huecos críticos propuestos para cubrir

Prioridad A: aislamiento y escrituras; B: validación y errores; C: bajo coste o
alcance limitado.

| ID | Prio | Código sin cubrir (`e1c2a8f`) | Qué falta | Prueba propuesta |
| --- | --- | --- | --- | --- |
| H-01 | A | backend `api/routes/billing.py` 40-44, 93-94 | Las rutas `GET /billing/tag-coverage` (éxito y esquema) y el 409 `ambiguous_cost_source` de ésta y de `/billing/summary` sólo se ejercitan con CockroachDB | Rutas reales con autenticación y pertenencia reales y la base doblada: 200 con contrato, 409 con `{"detail":{"code":"ambiguous_cost_source"}}` |
| H-02 | A | backend `api/routes/tenants.py` 12 | `GET /tenants` no tiene prueba funcional (sólo el preflight de `test_cors.py`); devuelve los tenants del usuario | SQLite real: cada usuario ve exactamente sus membresías, otro usuario no ve las ajenas, sin token 401 |
| H-03 | A | backend `api/routes/assistant.py` 63, `db/database.py` 497-507 | La creación de conversación con éxito no se ejecuta offline (sólo sus rechazos) | SQLite real: crea en el tenant activo y a nombre del usuario; otro tenant no la ve |
| H-07 | A | processor `tasks/ingest.py` 30-31, 72-74 | Mensaje persistido corrupto y reentrega de un trabajo ya completado (devuelve el resultado guardado sin reprocesar) | `IngestTask` con repositorio SQLite: la reentrega no reejecuta el pipeline ni escribe vectores; el JSON corrupto es `InvalidJobMessage` |
| H-08 | A | processor `repositories/azure_cost.py` 74, 117, 194, 221, 248 | **Corregido al ejecutar la tarea 5.4:** `complete_run` y `fail_run` con un run ajeno ya estaban cubiertos en SQLite; faltaban `start_run` con un run ajeno (sólo existía la variante CockroachDB) y las guardas de integridad por `rowcount`, que ninguna prueba ejercita (el helper `ReportZeroUpdatedRows` está definido y sin uso) | SQLite real: `start_run` ajeno lanza `PermissionError` sin tocar el run, y cuando la base afecta 0 filas las guardas lanzan su excepción y la transacción se revierte entera |
| H-04 | B | backend `api/routes/jobs.py` 39, 49 | Cola que no acepta la reserva (`not_sent`) y resultado de publicación fuera de contrato | Cola doble y SQLite: respuesta de error controlada y ningún trabajo creado |
| H-06 | B | processor `agents/guardrails.py` 56, 65, 71, 75, 98-106, 111, 123, 131-133, 138, 146-147 | Validación de entrada del agente (origen, payload, estado, metadatos) y de su salida (respuesta vacía o JSON inválido), y el recorte de metadatos | Funciones reales del guardrail: cada entrada inválida se rechaza con su error; la respuesta vacía o no JSON no retiene la carga del proveedor |
| H-09 | B | processor `clients/azure_cost.py` 92-97, 286-318 | Fallos de transporte (tiempo agotado, conexión rechazada) y páginas malformadas del productor | Servidor HTTP real de loopback, como en la primera pasada, y un puerto cerrado: errores tipificados y ningún registro escrito |
| H-11 | B | azure-cost-api `query_engine.py` 55, 57 | Filtro con dimensión o etiqueta no soportada debe dar 400 | `TestClient` real: 400 `BadRequest` con el nombre rechazado |
| H-05 | C | backend `core/tag_policy.py` 3-20, `database.py` 303-310 | Contrato de `tag_rule_sql`: clave desconocida y uso de constantes cerradas (frontera de inyección SQL) | Función pura: clave fuera de la política lanza `ValueError`; ninguna entrada ajena aparece en el SQL |
| H-10 | C | processor `normalization/azure_cost.py` 184-185, 192, 203-204, 224, 234, 258-260, 276, 285 | Filas con importes no numéricos o no finitos, etiquetas en conflicto o dimensiones no admitidas | Normalizador real: cada fila se rechaza con `AzureCostNormalizationError` antes de persistir |
| H-12 | C | frontend `components/TagCoveragePanel.tsx` 23, 43, 51 | Avisos «Datos parciales» y «Solo costes cero» y la política de reintento | Componente real con `fetch` doble: aparecen con los datos que los provocan |

#### Aceptados (sin prueba nueva, con motivo)

| ID | Código | Motivo |
| --- | --- | --- |
| A-01 | backend `models/domain.py` (0 %) | Ningún archivo de `apps/` ni de `tools/` lo importa en `e1c2a8f` (`git grep`); código sin uso |
| A-02 | frontend `hooks/useCostKpis.ts` (0 %) | Ningún archivo de `src` ni de `tests` lo importa; hook sin uso. La retirada es un cambio de producto |
| A-03 | frontend `main.tsx`, `App.tsx` (0 %) | Arranque y montaje; las pruebas montan el árbol de rutas por su cuenta. El `QueryClient` por defecto ya consta en `RF-098-002` |
| A-04 | frontend guardas `Tenant required` (`ConversationsPage` 31-32, 42-43, 65-66; `IngestPage` 37-38, 46-47) | Inalcanzables: la consulta no se habilita y el envío no se ofrece sin tenant activo |
| A-05 | frontend `components/ui/select.tsx`, `ui/dialog.tsx` | Envoltorios de Radix con pruebas propias del disparador y los colores; el resto es comportamiento de la biblioteca |
| A-06 | frontend `data/demo/executiveCostDashboard.ts` | Datos de demostración fijos, sólo protegidos por la guarda de colores |
| A-07 | backend `dns_resolver_child.py`, parte de `managed_resolver.py` | Proceso hijo aislado que `test_managed_resolver.py` ejecuta; la medición no lo observa (ver contraste). No verificado línea a línea |
| A-08 | backend `run.py` 25; processor `run_api.py` 23, `run_worker.py` 12-19, `run_all.py` 41 | Cableado de arranque sin lógica propia |
| A-09 | backend `database.py` 449, 465; `migration_runner.py` 14-36 | Ramas defensivas que sólo se alcanzan con una base que viola su contrato, y un ejecutor de migraciones con SQL de CockroachDB que sólo corre contra la base real |

#### Diferidos (se registrarán como `RF-054-NNN` al aprobar)

| ID | Código | Por qué se difiere |
| --- | --- | --- |
| D-01 | backend `system_health_runtime.py` 36-86, 135-160 | Los sondeos de base, vector y cola y el despacho del hijo no los ejercita ninguna suite, tampoco las opt-in (`git grep` sin resultados). Necesita servicios reales: `RF-096-004` |
| D-02 | backend `config.py` 55-67, `runtime_secrets.py` 41-44, 50, 74, 89, 111-112, 120 | Validación de configuración de arranque sin caso negativo (URL de salud con credenciales, clave de pasarela con prefijo `sk-or-`) |
| D-03 | backend `embedding_provider.py` 123-127, 153-160, 185-191 | Proveedor `mock` por defecto sin prueba unitaria, clasificación de fallos de transporte y handshake TLS |
| D-04 | processor `clients/litellm.py` 100-134, 156-194, `agents/providers.py` 56-57, 66, 68, `embeddings/chunker.py` 4-8, 16, `embeddings/providers.py` | Clasificación de errores y de coste del cliente de la pasarela, y validación de parámetros |
| D-05 | processor `workers/runner.py` 26-66 | Ciclo de vida del worker; se construye con servicios reales |
| D-06 | processor `run_azure_cost_ingestion.py` 49-103 | CLI manual: códigos de salida y salida JSON |
| D-07 | azure-cost-api `repository.py`, `main.py` 37-38, 44, `models.py` | Errores de carga de contrato y de fixture en el arranque |
| D-08 | frontend `components/ExportButton.tsx` 22-75 y ramas menores de `SessionGate`, `DashboardPage`, `IngestPage`, `useSystemHealth` | Exportación CSV de pantallas de demostración y ramas de presentación de bajo riesgo |

Recomendación de alcance: cubrir las prioridades A y B (9 huecos) y decidir sobre C
(3) según el tiempo. Si se prefiere acotar, el orden sugerido es H-02, H-03, H-07,
H-08, H-01. Queda además la decisión de ampliar o no `RF-096-004`: es la causa de
que el mayor volumen de código nuevo (JUP-017 y JUP-037) no se ejecute en CI.

#### Decisión sobre los huecos (2026-10-10)

Decisión de Victor sobre la lista anterior, tomada antes de escribir ninguna prueba:

- **Se cubren las prioridades A y B (9 huecos):** H-02, H-03, H-07, H-08, H-01, H-04,
  H-06, H-09 y H-11. Cada uno con un archivo de pruebas nuevo, sin tocar las
  pruebas existentes (tareas 5.1 a 5.9).
- **La prioridad C (H-05, H-10, H-12) no se cubre en esta pasada** y pasa a
  diferidos junto con D-01 a D-08. Se registrarán como `RF-054-NNN` al cerrar.
  Con ello esta pasada no añade pruebas de frontend.
- **`RF-096-004` no se amplía.** Provisionar CockroachDB, pgvector y RabbitMQ en
  CI toca `ci.yml` y sus pruebas de política, fuera del alcance acordado. Las 127
  omitidas y el código que sólo ellas ejercitan (JUP-017 y JUP-037) quedan
  documentados como evidencia de esa prioridad.
- **Los aceptados (A-01 a A-09) y los diferidos (D-01 a D-08) se dan por conformes.**
  A-01 y A-02 (código sin uso) son candidatos a retirarse, pero eso es un cambio de
  producto y no se hace aquí.

Como el código de producto ya existe, las pruebas nuevas pasan a la primera. Su
valor se acredita rompiendo a mano el comportamiento cubierto y comprobando que la
prueba falla (decisión 7 del diseño), no con mutación automática.
