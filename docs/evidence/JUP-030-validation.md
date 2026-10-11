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

## Revalidacion sobre `develop` (2026-10-11)

El PR #91 se cerro el 10/10 sin integrar y la contribucion se retoma en `feat/JUP-030-anomaly-evaluator`, rehecha sobre `develop` en `4406477` con los dos commits originales (autoria conservada). Se trabaja con la excepcion temporal del 2026-10-11: sin revision ni validacion humanas de otras personas en GitHub; esta seccion no es una review `Validacion JUP-030`.

Ejecutado el 2026-10-11 en Windows con el entorno virtual del backend, sin CockroachDB (Docker no estaba disponible):

```sh
cd apps/backend
python -m pytest tests/test_anomaly_evaluation.py tests/test_budget_evaluation.py tests/test_billing_summary.py tests/test_tag_coverage.py -q -p no:cacheprovider
# 149 passed, 32 skipped (las pruebas con CockroachDB real no se ejecutan sin la base)
corepack pnpm openspec:validate
# 62 passed, 0 failed
```

- La revision adversarial independiente (`review.md`) ejecuto 84 casos del archivo de anomalias y los ataques de limites exactos, importes por encima de 2**53, linea base ausente o no positiva, errores por la capa real (500 generico sin filtrar mensajes, 409 de fuente ambigua, 401/403/422 sin lectura de datos) y aislamiento entre tenants: todos resistieron.
- Se cerro un hueco de test (ADV-3): un cambio solo en la calidad del periodo base debe cambiar `evidence_id`; con el test nuevo falla la mutacion que la quita del hash.
- Las integraciones con CockroachDB real se ejecutaron despues en esta misma rama: ver la seccion siguiente (181 pruebas, cero omitidas).

## Validacion con Docker y CockroachDB real (2026-10-11)

Tras la revalidacion nativa se repitio la validacion con Docker Desktop, sobre la rama `feat/JUP-030-anomaly-evaluator` en `7d0b61d`.

**1. Pruebas con CockroachDB real.** Nodo desechable `cockroachdb/cockroach:v24.1.11` (`start-single-node --insecure`, puerto local 26299, `cluster.organization = 'processor-integration-tests'`):

```sh
cd apps/backend
JUP086_COCKROACH_TEST_URL='cockroachdb+psycopg://root@127.0.0.1:26299/defaultdb?sslmode=disable'   python -m pytest tests/test_anomaly_evaluation.py tests/test_budget_evaluation.py tests/test_billing_summary.py tests/test_tag_coverage.py -q -p no:cacheprovider -rs
# 181 passed, 0 skipped, 0 errors (12 min 29 s)
```

Para esa ejecucion se subio solo en la copia local, y se revirtio despues (`git status` limpio), el plazo de 60 s a 400 s de `subprocess.run(... timeout=60)` en `apps/backend/tests/billing_support.py`, porque las migraciones del processor tardan mas en esta maquina. Un primer intento con el plazo original dio 32 errores por esa causa (no por el codigo), y los 149 restantes pasaron.

**2. Extremo a extremo por HTTP.** Stack aislado `docker compose -p jup030` (todos los servicios sanos tras repetir una vez el `up` por un fallo de arranque interno de CockroachDB, ajeno al cambio), ingesta del dataset publico de Azure (`tenant-core`, 38 filas, 2024-06-02 a 2024-06-19) y llamadas a `POST /billing/anomalies/evaluate` con el usuario demo (contrasena leida del entorno del contenedor, nunca impresa). Importes esperados calculados antes con SQL independiente sobre `azure_cost_records`:

| # | Peticion | Esperado | Observado |
| --- | --- | --- | --- |
| 1 | `resource_group`, 10-19 jun 2024, umbral `0.03` y subida 50 % con minimo `0.01` | `zfinops` 0,03 frente a 0,01 (+0,02; 200,00 %): umbral y subida. `DevTestLab` 0,03 frente a 0,00: solo umbral (base no positiva, sin division) | 2 alertas exactamente asi; `deviation_status: baseline_nonpositive` en DevTestLab; `cause_status: not_established` |
| 2 | Misma peticion repetida | `id` y `evidence_id` identicos | Identicos |
| 3 | Solo umbral `0.04` | Sin alertas, `baseline_period` nulo | Sin alertas, `evaluation_status: evaluated` |
| 4 | Solo subida 50 % con minimo `0.05` | Ninguna alerta (el incremento 0,02 no llega al minimo) | Sin alertas |
| 5 | Mismo periodo en `tenant-growth` | Sin datos, no se ven los de `tenant-core` | `data_status: empty`, `evaluation_status: unavailable` |
| 6 | Sin ninguna regla | 422 antes de leer datos | 422 |
| 7 | `end_date` en 2999 | 422 | 422 |
| 8 | Moneda `EUR` (sin datos) | Sin evaluacion | `evaluation_status: unavailable` |
| 9 | Periodo de julio de 2024 (sin datos) | Sin evaluacion | `empty` en ambos periodos |
| 10-12 | Tenant ajeno, sin token, importe como numero JSON | 403, 401, 422 | 403, 401, 422 |
| 13 | `group_by: service` (la ingesta por defecto no rellena el servicio) | Calidad honesta | `data_status: partial`, 18 registros sin dimension, grupo `null`, 0,05 frente a 0,01 (+400,00 %) |

**3. Hallazgo RF-030-001 comprobado con SQL real.** En CockroachDB `lower('ΑΣ')` devuelve `ασ` y `lower('ας')` devuelve `ας` (distintos), mientras que en Python los dos dan `ας`. La divergencia entre la agrupacion SQL y la normalizacion del servicio existe de verdad; el finding sigue aceptado y abierto.

**Limpieza.** Stack, volumenes y nodo desechable eliminados (`docker compose -p jup030 down -v`); sin contenedores ni volumenes restantes.

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
