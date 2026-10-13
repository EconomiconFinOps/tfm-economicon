# Pruebas críticas — JUP-054

Trello: https://trello.com/c/ZsxwmagI. Auditoría: 2026-10-10, base
`c2995a118d419dfe725247bac9c6f219a3f0ea77`. Resultados de ejecución y límites:
[evidencia JUP-054](../evidence/JUP-054-validation.md).

Segunda pasada (2026-10-10): candidato `e1c2a8f` (`develop` tras cinco PR posteriores a la #93), cobertura
medida como diagnóstico y nueve huecos cubiertos con pruebas nuevas. Ver la columna «Delta JUP-054», la
sección [Medición de cobertura](#medición-de-cobertura-diagnóstico) y la
[evidencia](../evidence/JUP-054-validation.md#segunda-pasada-cobertura-del-candidato-final).

La referencia del 27/08 (58 Azure + 126 processor + 10 backend) es histórica.
JUP-087 incorporó Vitest y resolvió el baseline de lint; JUP-085/086/096 añadieron
contratos de autenticación, aislamiento y migraciones. Se reutilizan esas suites.
No se establece un porcentaje de cobertura arbitrario ni se equipara un test
con dobles a una validación de infraestructura.

## Matriz requisito / riesgo / suite

Rutas relativas a la raíz; las llaves agrupan archivos existentes.

| Área / riesgo | Suite reutilizada | Componentes reales / límites | Delta JUP-054 |
| --- | --- | --- | --- |
| Auth: token inválido, expiración, exposición de secretos | `apps/backend/tests/test_{auth_api,security_utils,secret_boundaries}.py`; frontend `tests/auth-session.test.tsx` y tests de expiración | JWT, rutas y guards reales; almacén de usuarios doble en auth API, fetch doble en frontend | Sin duplicación. Login con almacén real seguido de todas las rutas sigue fuera de esta evidencia |
| Tenant: lectura/escritura cruzada, membresía revocada, redelivery | Backend `test_tenant_isolation_{api,repository,vector}.py`; processor `test_tenant_isolation_{jobs,costs,malformed_queue,integration}.py` | Rutas/repository/SQL reales en SQLite; variantes Cockroach/vector/Rabbit opt-in. Tokens creados por fixture | Se amplía el recorrido existente con GET de historial, igualdad íntegra de mensajes, JSONB y 404 para otro tenant **Segunda pasada:** `GET /tenants` devuelve sólo las membresías del usuario (`test_tenants_route.py`), la creación de conversaciones usa el tenant y el usuario del contexto y queda aislada después (`test_conversation_creation.py`) y una reserva de cola rechazada no crea trabajo (`test_job_reservation_rejection.py`), con SQLite real; las variantes opt-in siguen sin ejecutarse en CI. |
| Azure: contrato, paginación, errores e idempotencia | Azure `test_{query_api,resilience,repository}.py`; processor `test_azure_cost_{client,ingestion,cockroach_integration}.py` | API local sobre CSV; cliente unitario con respuestas dobladas; Cockroach opt-in | `apps/processor/tests/test_azure_api_contract_integration.py`: API local real por HTTP loopback → UrllibTransport → cliente → normalizador → SQL SQLite; no Azure cloud **Segunda pasada:** fallos de red reales del transporte y páginas malformadas (`test_azure_client_failures.py`), rechazo de runs ajenos y atomicidad de las guardas de `rowcount` con triggers de SQLite (`test_azure_cost_scope_rejection.py`) y filtros o agrupaciones no soportados del simulador (`apps/azure-cost-api/tests/test_unsupported_filters.py`). Límites: la semántica de `rowcount` de CockroachDB no se demuestra y el transporte deja escapar excepciones crudas (`RF-054-004`), sin fijar. |
| RAG: selección, evidencia, dimensiones y aislamiento | Backend `test_retrieval_{contract,failures,traceability,contract_pgvector}.py`, `test_citations.py`; processor `test_{embedding_pipeline,vector_dimensions,tenant_isolation_vector}.py` | Embeddings deterministas y vector doubles en offline; pgvector real opt-in | Reutiliza el recorrido real y comprueba conservación de citas al reabrir Segunda pasada: sin cambios. |
| Agente: salida inválida y efectos parciales | Processor `test_agent_runtime.py`, `test_ingest_task.py` | Guardrails reales, proveedor y agente doblados por separado en suites anteriores | `test_agent_ingestion_integration.py`: AgentRuntime + LangGraph + IngestTask + repositorio SQLite; proveedor/embeddings/vector explícitamente doblados. Éxito normalizado y rechazo sin escritura vectorial **Segunda pasada:** guardrails de entrada y de salida (`test_guardrail_validation.py`) y reentrega idempotente de un trabajo completado y payload persistido corrupto (`test_ingest_redelivery.py`). Defectos: `RF-054-001` corregido después por JUP-113 (ver la fila «Ingesta: fallos permanentes y reintentos») y `RF-054-002` sin fijar. |
| Frontend: navegación, caché entre tenants, errores visibles | `apps/frontend/tests/{session-and-dashboard,tenant-switching,ingestion,conversations,dashboard-tenant-transition}.test.tsx`; `src/routes.integration.test.tsx` | Route tree, componentes, QueryClient, storage y API client reales en jsdom; fetch doble. No navegador/backend real | Vitest directo en CI; se conservan suites de JUP-087 y posteriores Segunda pasada: sin cambios ni pruebas nuevas; los avisos de `TagCoveragePanel` quedan diferidos (`RF-054-006`). |
| Docker/runtime: wiring, salud, migraciones, fallos de transporte | `tools/{docker-topology,local-doctor,local-smoke,litellm-compose}.test.mjs`; processor `test_{schema_migration_ownership,tenant_isolation_integration,litellm_docker}.py`; backend `test_rabbitmq_publisher_integration.py` | Tests de herramientas estáticos/doblados no prueban stack levantado. Integraciones opt-in usan servicios reales aislados | Ejecución acotada de recorrido real, detallada en evidencia; no acredita todo Compose ni gateway/LLM real Segunda pasada: sin cambios. |
| Ownership y cobertura de etiquetado (JUP-037, JUP-017; posteriores a la PR #93): selección inválida, evidencia de coste, procedencia, aislamiento entre tenants y ponderación | Backend `test_ownership_{questions,provenance}.py`, `test_tag_coverage.py`; frontend `tests/ownership-conversations.test.tsx`, `src/components/{CostEvidence,TagCoveragePanel}.test.tsx` | Las preguntas de ownership se prueban offline con datos propios. La procedencia y el SQL de cobertura de etiquetado (`fetch_tag_coverage`, `tag_policy.py`) sólo contra CockroachDB real (opt-in, omitidas en CI); offline únicamente periodos inválidos y precedencia de autenticación con la base doblada. Frontend con `fetch` doble | **Segunda pasada:** contrato de las rutas de billing con la base doblada (200, esquema y 409 sin fugas) en `test_billing_error_contract.py`; el SQL real sigue sólo en CockroachDB (`RF-096-004`). Los avisos del panel de etiquetado quedan diferidos (`RF-054-006`). Huecos y decisión en la [evidencia](../evidence/JUP-054-validation.md#huecos-de-cobertura) |
| Ingesta: fallos permanentes y reintentos (JUP-113; `RF-086-004`, `RF-054-001`) | Backend `test_ingest_source_admission.py`; processor `test_ingest_source_contract.py`, `test_ingest_permanent_input_failure.py`, `test_queue_message_redelivered.py`, `test_ingest_bounded_retry.py`, `test_completed_result_shape.py`, `test_completed_result_exposure.py`, `test_completed_result_json_representation.py`; opt-in `test_ingestion_retry_integration.py` y `test_ingestion_jsonb_string_integration.py`; tabla compartida `docs/api/ingest-source-contract-cases.json` | Ruta HTTP real y SQLite en el backend con la cola doblada; en el processor `IngestTask`, `AgentRuntime`, LangGraph y `ProcessorWorker` reales sobre SQLite con el broker y el almacén vectorial doblados. El opt-in usa CockroachDB, pgvector y RabbitMQ reales | Admisión del `source` (422 sin efectos), descarte en una entrega del fallo permanente de entrada, tope de una reentrega con la marca `redelivered`, reencolado sin tope si no se puede leer o registrar el estado, y forma del resultado guardado de un `completed`. **Límite:** CI ejecuta todo menos `test_ingestion_retry_integration.py` y `test_ingestion_jsonb_string_integration.py`, que se omiten sin servicios reales (`RF-096-004`); la rama del JSONB ya decodificado se comprueba allí con CockroachDB real y en CI solo con un doble. Evidencia en [JUP-113](../evidence/JUP-113-validation.md#pruebas-con-servicios-reales-tareas-61-a-63) |

## Suites obligatorias en CI

`.github/workflows/ci.yml` conserva los contextos existentes:

- `Python tests (azure-cost-api)`, `Python tests (backend)` y `Python tests (processor)`:
  Python 3.12, instalación de `requirements-dev.txt`, compileall y pytest directo.
  Las nuevas pruebas offline entran por descubrimiento normal de pytest.
- `Frontend build`: lint → **Vitest directo** → build. Un fallo bloquea el job.
  `Frontend type check` sigue separado. No se crea otro job que repita Vitest.
- `OpenSpec`: trazabilidad, gobernanza, corpus, contratos, topología y OpenSpec.
- `JUP policy` y `JUP reviews`: controles de proceso, no sustituyen pruebas.

CI no provisiona bases/broker para las suites opt-in (seguimiento RF-096-004).
Sus skips deben conservarse en el informe. La prueba de reinicio RabbitMQ requiere
además el hook `request.config.jup086_owned_rabbit_restart`; la prueba Docker de
LiteLLM requiere `JUP023_DOCKER_FAKE=1`. Poner URLs no activa esas dos pruebas.

## Reproducción local sin caché Turbo

Instalar Node y Python compatibles con CI y las dependencias fijadas de pnpm:

```sh
corepack pnpm install --frozen-lockfile
corepack pnpm --filter @finops/frontend test
corepack pnpm --filter @finops/frontend lint
corepack pnpm --filter @finops/frontend typecheck
corepack pnpm --filter @finops/frontend build
corepack pnpm jup:check:all
corepack pnpm pr:check:test
corepack pnpm ci:check:test
corepack pnpm repository:governance:test
corepack pnpm openspec:validate
```

Si hace falta limitar recursos: `corepack pnpm --filter @finops/frontend exec
vitest run --maxWorkers=1`. El test del paquete ejecuta `vitest run`; no pasa por
Turbo. No usar logs reproducidos desde `.turbo` como prueba recién ejecutada.

En **cada** `apps/backend`, `apps/processor`, `apps/azure-cost-api`, crear un
entorno Python 3.12, instalar y ejecutar directamente (PowerShell usa
`.venv/Scripts/python.exe`; POSIX `.venv/bin/python`):

```sh
python -m venv .venv
# Activar el entorno correspondiente al shell.
python -m pip install -r requirements-dev.txt
python -m compileall -q app
python -m pytest tests -q -ra -p no:cacheprovider --junitxml=results.xml
```

Los tres servicios se ejecutan desde su directorio porque todos contienen un
paquete Python `app`. No mezclar sus imports en el mismo proceso pytest.
Usar un `--basetemp` único y escribible si pytest no puede acceder al temporal
del sistema. Los XML/logs son artefactos de ejecución, no código fuente.

## Recorrido con infraestructura real

Reutiliza `apps/processor/tests/test_tenant_isolation_integration.py`. Crear un
CockroachDB `v24.1.11`, pgvector `pg17` y RabbitMQ `3.13-management` **desechables**,
sin volúmenes persistentes, en puertos loopback no estándar. En el nodo de prueba
Cockroach ejecutar `SET CLUSTER SETTING cluster.organization =
'processor-integration-tests'`. No ejecutar esta instrucción en un nodo compartido.

Variables exclusivas del proceso de pruebas (ejemplo de puertos libres):

```sh
export PROCESSOR_COCKROACH_TEST_URL='cockroachdb+psycopg://root@127.0.0.1:46454/defaultdb?sslmode=disable'
export JUP086_VECTOR_TEST_URL='postgresql+psycopg://postgres@127.0.0.1:45454/postgres'
export JUP086_RABBITMQ_TEST_URL='amqp://guest:guest@127.0.0.1:45654/%2F'
# Desde apps/processor, con el entorno activado:
python -m pytest tests/test_tenant_isolation_integration.py -q -ra -p no:cacheprovider
```

Las credenciales de ejemplo son las predeterminadas de servicios efímeros;
no contienen secretos operativos. Configurar pgvector aislado con autenticación
trust sólo en ese loopback de prueba. Si Docker es remoto, publicar en su loopback
y tunelizar esos puertos por SSH; no exponer el nodo inseguro a la red.

Los fixtures validan el destino, crean bases/colas con UUID y eliminan sólo lo
creado. Exigen Cockroach sin bases/tablas de aplicación y pgvector limpio.
Ejecutar un único proceso pytest por nodo Cockroach; backend y processor en serie.
Detener únicamente los contenedores/túnel creados para esta ejecución al terminar.

JUP-113 añade `apps/processor/tests/test_ingestion_retry_integration.py` (15 casos, mismas tres variables;
se omite sin ellas): un trabajo envenenado seguido de uno válido de otro tenant, el tope de una reentrega
con la marca `redelivered` real del broker, la primera entrega interrumpida y el resultado JSONB inválido con
CockroachDB. Con `python -m pytest tests/test_ingestion_retry_integration.py -q -ra -p no:cacheprovider` desde
`apps/processor`. En la ejecución de JUP-113 se creó el RabbitMQ con un usuario propio
(`RABBITMQ_DEFAULT_USER`/`RABBITMQ_DEFAULT_PASS`) y se usó `amqp://usuario:clave@127.0.0.1:PUERTO/%2F`; no se
probó con `guest`.

## Medición de cobertura (diagnóstico)

JUP-054 (segunda pasada) mide la cobertura de un SHA concreto, sin exigirla en CI y
sin umbral. La herramienta se instala sólo en contenedores Linux desechables
(`python:3.12`, `node:22`); no forma parte de los `requirements-dev.txt`, de
`package.json` ni de `pnpm-lock.yaml`. Se mide el árbol versionado, sin volúmenes
compartidos ni puertos publicados. Docker 29.8.1; imágenes y versiones exactas en la
[evidencia](../evidence/JUP-054-validation.md#entorno-de-medición).

Servicios Python (sustituir `SERVICIO` por `azure-cost-api`, `backend` o
`processor`; uno cada vez, porque la contención de CPU altera las pruebas con plazos):

```sh
SHA=<sha-de-develop-a-auditar>
git archive --format=tar "$SHA" | docker run -i --name cov python:3.12 sh -c '
  mkdir /src && tar -x -C /src && cd /src/apps/$0
  python -m pip install -q -r requirements-dev.txt pytest-cov==7.1.0
  python -m compileall -q app
  python -m pytest tests -q -p no:cacheprovider --cov=app --cov-branch     --cov-report=json:/tmp/coverage.json --cov-report=term:skip-covered
' SERVICIO
docker cp cov:/tmp/coverage.json . && docker rm cov
```

Frontend:

```sh
git archive --format=tar "$SHA" | docker run -i --name cov node:22 sh -c '
  export CI=true COREPACK_ENABLE_DOWNLOAD_PROMPT=0
  mkdir /src && tar -x -C /src && cd /src
  corepack enable && corepack pnpm install --frozen-lockfile
  corepack pnpm --filter @finops/frontend add -D @vitest/coverage-v8@3.2.7
  cd apps/frontend
  corepack pnpm exec vitest run --coverage.enabled --coverage.provider=v8     --coverage.include="src/**" --coverage.reporter=text-summary     --coverage.reporter=json-summary --coverage.reportsDirectory=/tmp/cov-fe     --coverage.reportOnFailure=true
'
docker cp cov:/tmp/cov-fe . && docker rm cov
```

La versión de `@vitest/coverage-v8` debe ser la del Vitest resuelto en el lockfile.
`add` modifica sólo la copia del contenedor. Antes de usar una cifra se compara la
línea final de pruebas aprobadas, fallidas y omitidas con la ejecución de CI de ese
SHA; si no coinciden la cifra no es la cobertura del candidato. El código ejecutado
únicamente por subprocesos no aparece en la medición.

## Interpretación

Éxito offline demuestra los componentes y contratos indicados, no fiabilidad de
un LLM, Azure real, despliegue cloud, ni comportamiento visual en navegador.
Éxito del recorrido real demuestra sólo esos escenarios y las versiones registradas.
No se acredita revisión ni aceptación humana sin sus dictámenes. La excepción
por plazo del MVP autorizada para el cierre de JUP-054 se documenta en la
[evidencia de entrega](../evidence/JUP-054-validation.md#entrega-y-atribución).
