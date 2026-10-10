# JUP-035 — Evidencia de implementación

Fecha: 10/10/2026. [Trello](https://trello.com/c/BJfABykd).
Base: `412ae411c7f3a9b51f65407974962ac2b4545686` (develop).
Implementación realizada bajo el encargo del usuario de asumir las funciones
técnicas conservando el rol de Paris en Trello. No acredita pairing de Víctor,
revisión independiente de Alejandro ni validación de Lucía.

## Resultado por criterio

| Criterio | Evidencia | Límite |
| --- | --- | --- |
| Generación por modelo configurado | Backend conectado a `/v1/chat/completions`; prueba HTTP real con upstream sintético verifica roles, alias, schema, respuesta y citas. | Modelo/gateway pagado no ejecutado; clave virtual no disponible en entorno ni `.env`/`.env.local` de este checkout. |
| Afirmaciones con evidencia del tenant | Cada afirmación lleva IDs y citas literales validadas contra contexto autorizado; pruebas rechazan fuentes inventadas, citas ajenas, signos, unidades y cifras nuevas. | No acredita equivalencia semántica ni resistencia universal a inyección; requiere JUP-070. |
| Sin evidencia, abstención | 28/28 preguntas JUP-069 enviadas al endpoint sin contexto: 201, `insufficient_data`, cero citas/claims y cero llamadas al modelo. | Control de ausencia de contexto, no puntuación de la batería con corpus/modelo. |
| Fallo/timeout comprensible | 503 saneado, ninguna respuesta asistente inventada; tests de timeout/auth/formato, draft retenido y reintento explícito. | Pregunta documental se guarda antes del fallo; retry crea otro intento. |
| Datos de coste | JUP-037 consulta SQL por tenant y selección; generación recibe el resultado y conserva snapshot completo y límites. | Prueba de adaptador con SQL de mensajes real y doble explícito de facturación. JUP-036 ausente de base; selección automática de todo JUP-084 no implementada. |
| Historial RF-087-002 | CockroachDB v24.1.11 real aislada: POST→GET, ambos mensajes y metadata generativa idéntica, tenant ajeno 404. | No se reescribe la normalización JSONB ya integrada; browser y SQL se prueban por separado. |
| UI accesible/responsive | Chromium: pendiente, error, draft, retry, recarga, enlace de cita/foco y anchuras 1440/375 px. Se corrigió overflow de cabecera/nav. | HTTP interceptado y respuestas sintéticas, no E2E completo con modelo. |

## Comprobaciones realizadas

- Nuevas pruebas backend: **70 PASS**, incluidas CockroachDB y las 28 preguntas
  sin contexto. Después se añadió prueba de transporte HTTP real local: la suite
  de generación/configuración/secretos pasó **163/163**. Recuentos solapados,
  no sumarlos como pruebas únicas.
- Regresión focalizada chat/retrieval/citas/tenant/costes: **182 PASS / 4 SKIP**
  antes de habilitar la prueba opcional de CockroachDB. Suite API generativa
  con CockroachDB y adaptador de costes: **7 PASS** antes de añadir la batería.
- Suite frontend completa: **649/649 PASS** con `--maxWorkers=2`. La ejecución
  inicial sin límite produjo 13 timeouts/fallos entre 649; se conservó ese hecho,
  y el rerun limitado pasó sin cambiar aserciones ni timeouts. Tras los últimos
  ajustes de responsive/citas: **14/14** pruebas afectadas PASS.
- TypeScript aplicación/tests, ESLint y build Vite: PASS. Aviso previo de bundle
  JS mayor de 500 kB conservado, sin modificación del splitting en esta tarjeta.
- Política PR, CI, gobernanza, gateway y topología Docker: **124/124 PASS**.
- OpenSpec estricto **58/58**, trazabilidad completa y `git diff --check`: PASS.
- Suite backend completa en Windows/Python 3.14: detenida por `--maxfail=3`
  con **393 PASS / 9 SKIP / 3 FAIL** en
  `test_health_provider_admission_jup047.py`. Su fixture bloquea
  `socket.socket.connect`, interceptando el `socketpair` de asyncio en Windows
  antes de llamar al endpoint. Archivos de esa fixture sin cambios en JUP-035.
  No se declara verde el backend general de Windows; CI Linux queda separada.
- Intentos iniciales de pytest en sandbox fallaron por permisos de temporales;
  las ejecuciones citadas se repitieron fuera del sandbox. El shim pnpm local
  produjo `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY`; se ejecutaron los mismos
  binarios instalados de TypeScript/Vitest/ESLint/Vite directamente.

## Reproducción

```text
# apps/backend
python -m pytest tests/test_chat_generation.py tests/test_chat_generation_api.py -q
python -m pytest tests/test_chat_generation.py tests/test_secret_boundaries.py tests/test_embedding_settings.py -q
# apps/frontend (o scripts equivalentes de pnpm)
node node_modules/typescript/bin/tsc --noEmit
node node_modules/typescript/bin/tsc -p tsconfig.test.json --noEmit
node node_modules/eslint/bin/eslint.js src tests
node node_modules/vitest/vitest.mjs run --maxWorkers=2
node node_modules/vite/bin/vite.js build
# raíz
node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs tools/llm-gateway-config.test.mjs tools/docker-topology.test.mjs
node node_modules/@fission-ai/openspec/bin/openspec.js validate --all --strict --no-interactive
node tools/jup-check.mjs --all
```

Evidencia local de navegador, reportes y XML de tests: espacio de coordinación
`materiales/07-evidencias/JUP-035-2026-10-10/`, fuera del repositorio de producto.
Cockroach temporal `economicon-jup035-cockroach-test`, sin volúmenes y con
almacenamiento en memoria; puerto remoto de loopback 56335, túnel SSH de pruebas.

## Pendientes para aceptación

Validación con el alias real y clave virtual autorizada, campaña JUP-069 con
corpus/modelo según metodología JUP-070, juicios humanos y revisión independiente.
El change permanece activo y la entrega se publica en borrador. No hay merge,
despliegue compartido, cierre de tarjeta ni consumo de proveedor durante estas
comprobaciones.
