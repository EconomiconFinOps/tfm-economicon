JUP: JUP-053
ADR: [ADR-0006, Accepted](../../../docs/adr/ADR-0006-runtime-secret-boundaries.md); aprobacion completa registrada en proposal.md.

## Context

Backend/processor cargan Settings y crean clientes durante el import. Backend
conserva `replace-me-auth-secret`; ambos usan conexiones con defaults locales.
Processor ya tiene SecretStr y validadores condicionales de IA que se reutilizan.
El seed hace UPSERT de la password en cada arranque; IngestTask persiste
`str(exc)` y structlog formatea excepciones sin redaccion final.

## Configuration and Startup

Usar BaseSettings por servicio, sin paquete compartido nuevo. Proponer
`RUNTIME_ENVIRONMENT=production|development|test`, con production por defecto;
`AI_EXECUTION_MODE=test` no habilita excepciones de seguridad. Los secretos no
tienen defaults, tampoco en test: fixtures explicitas inyectan valores aislados.
Test conserva validacion de formato y proveedores y nunca se deduce de pytest.
Configurar env_file=None por defecto; un `ECONOMICON_ENV_FILE` explicito permite
cargar dotenv mediante Pydantic. Entorno precede a dotenv; ignorar claves ajenas
del fichero compartido, validar las propias y usar SecretStr para secretos/DSN.

| Inventario | Tratamiento propuesto |
| --- | --- |
| AUTH_SECRET_KEY | Obligatorio, al menos 32 caracteres; rechazar vacio, espacios y placeholders conocidos, incluido replace-me-auth-secret, fuera de test. |
| DATABASE_URL | Explicita; DSN sin autenticacion solo bajo la excepcion local APPROVED descrita abajo, con opt-in desactivado por defecto. |
| VECTOR_DATABASE_URL / POSTGRES_PASSWORD | Externas y coherentes; rechazar password vacia o default postgres fuera de test. |
| RABBITMQ_URL / RABBITMQ_DEFAULT_USER / RABBITMQ_DEFAULT_PASS | Externas y coherentes; rechazar guest/guest y password vacia fuera de test. |
| RABBITMQ_ERLANG_COOKIE | Entrada externa requerida en Compose, sin fallback versionado; .env.example vacio. Conservar el cookie privado existente, sin generarlo, resetearlo ni rotarlo. |
| LITELLM_API_KEY | SecretStr, obligatoria solo si se selecciona litellm; mantener validacion de URL, alias, CR/LF, prefijo upstream y dimensiones. |
| OPENROUTER_API_KEY / LITELLM_MASTER_KEY | Solo entorno del gateway propuesto en infra/litellm; nunca app, VITE_* o build. No desplegar ni implementar clientes nuevos. |
| DEMO_SEED_ENABLED / DEMO_PASSWORD | Seed desactivado por defecto; al activarlo, password externa no vacia ni secret/placeholder fuera de test. |
| GRAFANA_ADMIN_PASSWORD | APPROVED: trasladar el valor existente a .env local ignorado, conservar password/autenticacion y quitar solo el fallback versionado; .env.example vacio. Mover un valor debil no lo fortalece. |
| AZURE_COST_* tokens / skiptoken | Fixtures sinteticas del simulador de datos publicos, no credenciales reales; mantener contrato y clasificacion local/test, nunca reutilizar contra Azure real. |

Mantener mocks sin exigir claves del gateway; evaluation conserva su rechazo
de mocks. Validar Settings no demuestra que exista un cliente LiteLLM funcional.
DSN se parsean con SQLAlchemy/urllib.parse, sin regex para extraer passwords.
Desenvolver SecretStr solo al entregar valores a drivers o funciones JWT.

Mover construccion de recursos a lifespan/factoria; importar app.main no conecta
ni necesita secretos. Los entrypoints validan antes de iniciar servidor, thread,
worker o inicializacion DB. El loader y lifespan convierten ValidationError y
fallos de inicializacion en errores estables sin input/context ni cadena cruda;
hide_input_in_errors es defensa adicional, no permiso para serializar errors().

## Approved Local Exception and Demo

Excepcion local APPROVED: `ALLOW_INSECURE_LOCAL_DATABASE=false` por defecto.
Solo development/test mas opt-in y DSN dirigido a loopback o al servicio
cockroachdb del Compose aislado permiten la conexion local sin autenticacion.
El operador debe confirmar datos desechables, puertos loopback y ausencia de uso
compartido; no se puede probar eso solo con una URL. Production siempre rechaza
el opt-in. La aprobacion completa no activa el opt-in; TLS/provisioning sigue
requiriendo otro alcance aprobado.

Conservar operator@example.com, identificadores, roles y hashing existentes.
DEMO_SEED_ENABLED permite crear cuenta/asociaciones demo ausentes, no sobrescribir
password de cuenta existente ni reasignar identidades. El formulario mantiene
email y password vacia. Detectar la password heredada conocida fuera de test
y detener con instruccion de rotacion; desactivar seed no elimina ese riesgo.
La rotacion de cuenta existente exige actualizar explicitamente su password_hash
con el hash generado por la funcion actual y una operacion parametrizada sobre
su ID, tras confirmacion del operador. Cambiar DEMO_PASSWORD no modifica ese hash.
No borrar usuarios, resetear volumenes ni introducir migraciones automaticamente.

## Diagnostics and Packaging

Redactar campos sensibles por nombre, contenedores anidados y valores de secretos
activos conocidos, incluida su forma URL-encoded, tras interpolacion y formateo
de excepciones y antes de JSONRenderer; cubrir structlog y logging estandar.
Conservar tipo, mensaje saneado, traceback sin locales y request_id de JUP-042.
No registrar bodies, Authorization, cookies, settings ni URLs completas; logs
de acceso usan ruta plantilla o marcador estable para rutas desconocidas.
HTTP 422 omite inputs/context sensibles; fallos internos y jobs guardan codigo
estable, nunca str(exc). Probar tambien stderr, excepciones encadenadas y arranque.
El access_token legitimo de login sigue su contrato. No se promete detectar
secretos desconocidos pegados en contenido de usuario ni todas sus codificaciones.

Compose usa referencias requeridas para secretos obligatorios y mantiene
condicional LITELLM_API_KEY. Documentar generacion externa salvo Grafana, escape de passwords en
DSN y coincidencia cliente/servidor; no pasar secretos como ARG, ENV de imagen o
VITE_*. Revisar contextos raiz (frontend/simulador) y de backend/processor para
excluir .env y variantes anidadas antes de COPY, incluidas capas intermedias.
Las muestras contienen campos secretos vacios y comentarios, no claves utilizables.
Grafana usa `${GRAFANA_ADMIN_PASSWORD:?required}` desde .env local excluido de
Git, contextos Docker y bundles, conservando la precedencia del entorno existente.
Solo trasladar la fuente: no eliminar, generar, rotar ni resetear password,
cuenta o volumen actuales; mantener autenticacion. No se acredita fortaleza.

## Approved File Surfaces

Superficies autorizadas por el gate registrado en proposal.md, sin cambios
de alcance respecto al borrador validado y aprobado.

| Area | Archivos propuestos |
| --- | --- |
| Backend | apps/backend/app/core/config.py; app/core/logging.py; app/core/request_context.py; app/main.py; app/run.py; app/db/database.py; app/api/routes/auth.py; app/api/dependencies.py (app/ relativo a apps/backend). |
| Processor | apps/processor/app/core/config.py; app/core/logging.py; app/core/request_context.py; app/main.py; app/run_api.py; app/run_worker.py; app/run_all.py; app/run_azure_cost_ingestion.py; app/workers/runner.py; app/tasks/ingest.py (app/ relativo a apps/processor). |
| Configuracion/UI | .env.example; .gitignore; .dockerignore; apps/backend/.dockerignore; apps/processor/.dockerignore; docker-compose.yml; apps/frontend/src/pages/LoginPage.jsx. |
| Documentacion | README.md; apps/backend/README.md; apps/processor/README.md; apps/frontend/README.md; infra/litellm/README.md; docs/manuals/python-service-conventions.md. |
| Tests nuevos | apps/backend/tests/test_secret_config.py; apps/backend/tests/test_secret_boundaries.py; apps/backend/tests/test_demo_seed.py; apps/processor/tests/test_secret_config.py; apps/processor/tests/test_secret_boundaries.py. |
| Tests existentes | apps/backend/tests/test_run_entrypoint.py; apps/processor/tests/test_run_entrypoints.py; apps/processor/tests/test_ai_settings.py; apps/processor/tests/test_agent_runtime.py; apps/processor/tests/test_azure_cost_client.py; test_logging_config.py y test_request_id_middleware.py en ambos tests/; tools/docker-topology.test.mjs. |

## Prepublication Reconciliation (2026-09-10)

La auditoria focal comunicada identifica el cookie de Erlang agregado por
origin/develop cb27009. Es una concrecion del alcance RabbitMQ/Compose existente:
usar `${RABBITMQ_ERLANG_COOKIE:?required}` y campo vacio en .env.example, con
fuente privada excluida de Git, contextos Docker y bundles. Conservar precedencia
de entorno; nunca recuperar automaticamente el fallback publicado por upstream.
Para una instalacion existente, documentar que su operador obtiene el cookie
privado ya existente sin imprimirlo ni incluirlo en evidencia. Una instalacion
nueva debe recibir un valor privado externo; el cambio no genera ni sustituye
cookies, ni toca .env, instalaciones o volumenes reales. Si el cookie existente
coincide con el valor publicado, escalar: cambiarlo/rotarlo, alterar clustering o
persistencia, o mantener ese fallback mediante otra excepcion exige aprobacion.
La password Grafana se conserva exactamente, sin nueva rotacion ni secret manager.

Conservar la propagacion upstream request_id entre job y worker de JUP-044 y
sus cinco tests. Las fixtures del tester deben incluir request_id en el job;
no asumir que un contexto ambiente sustituye la identidad del mensaje.
Conservar archivos archivados y findings incorporados; RF-044-002/JUP-096 y
RF-053-004/JUP-020 no se resuelven en esta reconciliacion. La comprobacion
integrada queda pendiente y no modifica criterios globales ni decisiones ADR.

## Validation and Rotation

Comandos propuestos, no ejecutados aqui: `corepack pnpm openspec:validate`,
`corepack pnpm jup:check -- --change jup-053-secure-runtime-secrets`,
`corepack pnpm jup:cleanup:check`, `corepack pnpm docker:validate` y
`corepack pnpm llm-gateway:test`. Las suites usan `python -m pytest tests -q`
desde cada servicio Python; frontend usa `corepack pnpm --filter @finops/frontend
build` y `corepack pnpm --filter @finops/frontend typecheck`.

Preservar los siete checks de CI: JUP policy, OpenSpec, Python tests
(azure-cost-api), Python tests (backend), Python tests (processor), Frontend build
y Frontend type check. Governance conserva todos sus comandos existentes.
JUP policy se verifica con `corepack pnpm pr:check -- --event <github-event.json>`
en etapa PR, PENDING hasta disponer del evento; no inventar evidencia.
JUP-087 reporta historicamente 49 infracciones react/prop-types; no es una cifra
verificada hoy. Volver a medir `corepack pnpm lint` en la base de comparacion y
contrastar el cambio sin ampliar alcance para resolver esa deuda. Frontend test
es placeholder y no acredita cobertura; tampoco se declara resuelto el baseline.

QA demostrara arranque/fallo con entorno sintetico aislado, Docker disponible y
sin reutilizar stacks ni credenciales ajenas. Revisara fuentes versionadas,
ejemplos, contextos/capas y bundle con sentinelas y patrones conocidos, informando
cobertura y falsos positivos solo por ruta/categoria. No leer stores ni .env reales.
Rotar JWT exige reiniciar consumidores e invalida tokens previos; no cambiar TTL
ni claims. DB/RabbitMQ/gateway requieren rotar primero en el servicio propietario
y actualizar consumidores coordinadamente. Postgres con volumen existente
no rotan por cambiar env. Documentar pasos de su operador, verificacion y retorno
a una credencial valida no comprometida; no recuperar defaults ni borrar datos.
