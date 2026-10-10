# JUP-030 — Evidencia tecnica de deteccion de costes

Fecha: 2026-10-10. [Tarjeta](https://trello.com/c/ScxJi1TO).
Base: `c2995a118d419dfe725247bac9c6f219a3f0ea77` (`origin/develop`).
Rama de contribucion: `feat/JUP-030-cost-anomalies`.
PR de contribucion en borrador: [#91](https://github.com/EconomiconFinOps/tfm-economicon/pull/91).
CI tecnica del codigo `0b35a72`: **7/7 SUCCESS** en
[run 38035032995](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035032995),
incluidos frontend build/typecheck, tres servicios Python, OpenSpec y JUP policy.
`JUP reviews` permanece pendiente de los dictamenes humanos requeridos.

Esta evidencia de implementacion no es una review `Validacion JUP-030`.
Roles registrados y conservados: Lucia Mateo liderazgo, Paris Arcos Martin
pairing, Victor Mendez revision, Alejandro Aguado validacion. La asignacion
no acredita participacion ni autoriza atribuir dictamenes humanos.

## Criterios de la tarjeta

| Criterio original | Evidencia y estado |
| --- | --- |
| Resultado funcional verificable | API autenticada `/billing/anomalies/evaluate`, con alertas por importe y aumento entre periodos. Las dos integraciones nuevas usan CockroachDB real, migraciones del proyecto y costes sinteticos: Compute actual 10.00 frente a 1.00 anterior produce 9.00 / 900.00%; otro tenant queda excluido. Entrega bajo demanda; panel y notificaciones programadas pendientes. |
| Pruebas necesarias anadidas y en verde | `test_anomaly_evaluation.py` y regresion focal de presupuesto/billing: **150 passed**, cero skips, 27.96 s, con base real activada. Incluye limites exactos, precision decimal, creditos, baseline cero/negativo/ausente, moneda, grupos, calidad, IDs, 422, 401/403/400 y 409 en cualquiera de los periodos. |
| Documentacion y decisiones actualizadas | [Contrato y reproduccion](../api/cost-anomalies.md), OpenSpec y continuidad. **56/56** validaciones OpenSpec estrictas; nueve changes trazables. |
| Pull request revisado y vinculado | PR de contribucion [#91](https://github.com/EconomiconFinOps/tfm-economicon/pull/91) vinculada, en borrador; review humana pendiente. No se declara cumplido. |
| Validacion funcional y evidencia enlazadas | Evidencia tecnica aqui; validacion funcional independiente asignada pendiente. No se declara cumplido. |

## Reproduccion

En `apps/backend`, instalar `requirements-dev.txt` en un entorno propio.
Usar una instancia CockroachDB desechable exclusivamente de pruebas. Las
salvaguardas existentes exigen loopback, puerto no estandar, usuario root,
base defaultdb vacia, `sslmode=disable` y organizacion
`processor-integration-tests`; crean y eliminan bases con nombre aleatorio.
Nunca apuntar esta variable a un servicio compartido o datos reales.

```sh
export JUP086_COCKROACH_TEST_URL='cockroachdb+psycopg://root@127.0.0.1:28430/defaultdb?sslmode=disable'
python -m pytest tests/test_anomaly_evaluation.py tests/test_budget_evaluation.py tests/test_billing_summary.py -q -x -p no:cacheprovider
# 150 passed, 1548 warnings in 27.96s
python -m pytest tests -q -p no:cacheprovider
# 997 passed, 21 skipped, 2976 warnings in 142.17s
python -m compileall -q app
# PASS
```

Ejecucion focal: DockerServer, contenedores efimeros exclusivos
`economicon-jup030-tests` y `economicon-jup030-runner`, sin volumen ni datos de
produccion. La copia contiene `apps/backend/app`, `tests`, requisitos y
`apps/processor/app` para ejecutar las migraciones reales.
CockroachDB imagen `cockroachdb/cockroach:v24.1.11`, image ID
`sha256:89bda255c52b25f463c7a9373ffedef122a4d9f1b432aa34b897970fe864a66c`.
Python 3.12.13 (Linux GCC 14.2.0); pytest 9.1.1, Pydantic 2.14.0, FastAPI 0.143.0,
SQLAlchemy 2.0.54, psycopg 3.3.6, sqlalchemy-cockroachdb 2.0.4.
Las advertencias focales son deprecaciones del adaptador datetime de SQLite.
La regresion completa pasa **997 tests**, omite **21** pruebas de integraciones
externas no habilitadas (RabbitMQ/pgvector) y no tiene fallos. Sus advertencias
adicionales son claves JWT sinteticas cortas y fork desde procesos con threads.
Compilacion de todo `app` completada sin errores. No se ejecuto el frontend
localmente porque no hay cambios en su codigo; CI conserva su build/test normal.

Comprobaciones de repositorio (Node 24.14.1; OpenSpec 1.8.0):

```sh
node --test tools/jup-check.test.mjs tools/pr-policy.test.mjs tools/repository-governance.test.mjs
# 77 passed
node --test tools/ci-workflow.test.mjs
# 12 passed
node tools/jup-check.mjs --all
# 9 changes OK
node tools/jup-cleanup-check.mjs
# OK
openspec validate --all --strict --no-interactive
# 56 passed, 0 failed
git diff --check
# sin errores
```

## Limites de la evidencia

- Los tests unitarios/API usan SQLite para autenticacion y dobles explicitos
  de los agregados. Las dos pruebas `test_real_cost_*` usan el repositorio SQL
  real. Las cifras son sinteticas, no gasto Azure de un cliente.
- Una revision tecnica interna del servicio, ruta y pruebas no encontro
  defectos; no sustituye a Victor ni a la validacion independiente.
- El frontend no cambia: JUP-057 conserva su fixture. No se ha validado
  conexion de UI, entrega por correo/Discord, scheduling, persistencia,
  resolucion de alertas, ni consumidor conversacional JUP-038.
- La comparacion de periodos usa reglas inclusivas configurables; no cumple
  por si sola la regla diaria estricta de JUP-084. No hay modelo estadistico,
  prueba de causa, severidad inferida, prediccion ni ahorro acreditado.
- Billing v2 no demuestra cobertura diaria, frescura ni snapshot atomico
  entre ambos periodos; el contrato devuelve `completeness=not_verified`.
- Los intentos Windows se interrumpieron tras problemas de sandbox/fixtures
  y carga de dependencias; no se cuentan como PASS. La evidencia Python
  aceptada procede del entorno Linux aislado. No se modificaron permisos
  de seguridad ni dependencias del checkout compartido para resolverlo.
