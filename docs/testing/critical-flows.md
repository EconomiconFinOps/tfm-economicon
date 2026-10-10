# Pruebas críticas — JUP-054

Trello: https://trello.com/c/ZsxwmagI. Auditoría: 2026-10-10, base
`c2995a118d419dfe725247bac9c6f219a3f0ea77`. Resultados de ejecución y límites:
[evidencia JUP-054](../evidence/JUP-054-validation.md).

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
| Tenant: lectura/escritura cruzada, membresía revocada, redelivery | Backend `test_tenant_isolation_{api,repository,vector}.py`; processor `test_tenant_isolation_{jobs,costs,malformed_queue,integration}.py` | Rutas/repository/SQL reales en SQLite; variantes Cockroach/vector/Rabbit opt-in. Tokens creados por fixture | Se amplía el recorrido existente con GET de historial, igualdad íntegra de mensajes, JSONB y 404 para otro tenant |
| Azure: contrato, paginación, errores e idempotencia | Azure `test_{query_api,resilience,repository}.py`; processor `test_azure_cost_{client,ingestion,cockroach_integration}.py` | API local sobre CSV; cliente unitario con respuestas dobladas; Cockroach opt-in | `apps/processor/tests/test_azure_api_contract_integration.py`: API local real por HTTP loopback → UrllibTransport → cliente → normalizador → SQL SQLite; no Azure cloud |
| RAG: selección, evidencia, dimensiones y aislamiento | Backend `test_retrieval_{contract,failures,traceability,contract_pgvector}.py`, `test_citations.py`; processor `test_{embedding_pipeline,vector_dimensions,tenant_isolation_vector}.py` | Embeddings deterministas y vector doubles en offline; pgvector real opt-in | Reutiliza el recorrido real y comprueba conservación de citas al reabrir |
| Agente: salida inválida y efectos parciales | Processor `test_agent_runtime.py`, `test_ingest_task.py` | Guardrails reales, proveedor y agente doblados por separado en suites anteriores | `test_agent_ingestion_integration.py`: AgentRuntime + LangGraph + IngestTask + repositorio SQLite; proveedor/embeddings/vector explícitamente doblados. Éxito normalizado y rechazo sin escritura vectorial |
| Frontend: navegación, caché entre tenants, errores visibles | `apps/frontend/tests/{session-and-dashboard,tenant-switching,ingestion,conversations,dashboard-tenant-transition}.test.tsx`; `src/routes.integration.test.tsx` | Route tree, componentes, QueryClient, storage y API client reales en jsdom; fetch doble. No navegador/backend real | Vitest directo en CI; se conservan suites de JUP-087 y posteriores |
| Docker/runtime: wiring, salud, migraciones, fallos de transporte | `tools/{docker-topology,local-doctor,local-smoke,litellm-compose}.test.mjs`; processor `test_{schema_migration_ownership,tenant_isolation_integration,litellm_docker}.py`; backend `test_rabbitmq_publisher_integration.py` | Tests de herramientas estáticos/doblados no prueban stack levantado. Integraciones opt-in usan servicios reales aislados | Ejecución acotada de recorrido real, detallada en evidencia; no acredita todo Compose ni gateway/LLM real |

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

## Interpretación

Éxito offline demuestra los componentes y contratos indicados, no fiabilidad de
un LLM, Azure real, despliegue cloud, ni comportamiento visual en navegador.
Éxito del recorrido real demuestra sólo esos escenarios y las versiones registradas.
No se acredita revisión ni aceptación humana sin sus dictámenes. La excepción
por plazo del MVP autorizada para el cierre de JUP-054 se documenta en la
[evidencia de entrega](../evidence/JUP-054-validation.md#entrega-y-atribución).
