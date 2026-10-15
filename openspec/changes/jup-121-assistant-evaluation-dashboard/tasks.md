## 1. Decisión, contrato y manifiesto (documentación)

- [x] 1.1 Redactar `docs/adr/ADR-0022-assistant-evaluation-results-in-grafana.md` con la plantilla `docs/templates/adr.md`: PostgreSQL con esquema `evaluation` y datasource integrado, alternativas descartadas (Pushgateway, promtool, TestData, Infinity, PostgreSQL aparte), Git solo para ejecuciones de hito, comando único de regeneración. Añadir su fila a `docs/adr/README.md`
- [x] 1.2 Escribir `docs/validation/evaluation-dashboard.md` con:
  - el contrato `rows-v1` (campos de ejecución y de fila, estados, `NULL` para lo no medido, sin texto libre);
  - el formato del manifiesto y los formatos admitidos;
  - la clasificación de ejecuciones no reales y la clave de comparabilidad;
  - la tabla de juicio humano o automático;
  - el comando de regeneración;
  - la nota de que JUP-071 entra por `rows-v1`.
- [x] 1.3 Crear `docs/validation/evaluation-runs.json` (`manifest_version` 1) con las dos ejecuciones de JUP-070, el benchmark de JUP-078, la calibración de JUP-022 y la entrada de JUP-068, todas con `milestone: true`

## 2. Normalización de informes (`tools/evaluation-dashboard.py`, pruebas en `scripts/tests/test_evaluation_dashboard.py`)

- [x] 2.1 Lectura y validación de manifiestos: varios `--manifest`, formatos admitidos, error por formato desconocido, por ruta inexistente o por `run_id` duplicado, y `milestone` por entrada
- [x] 2.2 Adaptador `jup-070-report-v1`:
  - metadatos del bloque `run`;
  - filas de `counts` con `cases` como denominador;
  - una fila por métrica con `k`, `n`, `rate` e `ci95`;
  - filas por etapa de latencia;
  - `available=false` o `rate` nulo pasan a `not_measured` con valor `NULL`;
  - error si falta un campo obligatorio o la versión es desconocida.
- [x] 2.3 Adaptador `jup-078-benchmark-v1`:
  - por modelo, `pass` = `successful` y `fail` = `cases - successful`;
  - puntuación, p95 y coste como valores con unidad;
  - commit y fecha `NULL`.
- [x] 2.4 Adaptador `jup-022-calibration-v1`: filas de acierto de documento, de sección y vacío por punto del barrido, con `top_k`, `max_distance`, casos como denominador y el candidato de `selection` marcado
- [x] 2.5 Adaptador `jup-068-input-v1`: ejecutar `node tools/business-metrics.mjs report`, normalizar como tipo B los estados y las cifras de tiempo, asignación y oportunidades con sus denominadores, y conservar `provenance`
- [x] 2.6 Adaptador `rows-v1` y validación común de filas que se aplica TAMBIÉN a la salida de los demás adaptadores, no solo a la entrada `rows-v1` (hallazgo M2 del QA de 2.2, el adaptador de JUP-070 copia sin validar tipos ni alfabeto): tipos numéricos en `value`, `numerator`, `denominator`, `ci_*` y `count`; `fullmatch` de `IDENTIFIER_RE` en `behavior`, `grp`, `metric_id`, `run_id` y en las cadenas de `run` salvo `run_at`; `status` frente a `CASE_STATUSES`/`VALUE_STATUSES`; rechazo de cualquier campo de texto libre fuera de identificadores y unidades. Decidir también si se rechazan `k` o recuentos negativos y `k > n` (hallazgo L2)
- [x] 2.7 Clasificación de ejecuciones y comparabilidad:
  - motivos `plantilla`, `doble`, `sintetica` y `sin_modelo_verificado`;
  - clave de comparabilidad con `suite_version` además de `suite_sha256` (JUP-022 no trae huella de la batería; las ejecuciones 1 y 2 de JUP-070 dan claves distintas);
  - tabla de juicio humano (recuentos `pass`/`fail`, ACC-1, ACC-3) o automático;
  - prueba que falla si el catálogo de JUP-067 tiene un identificador sin clasificar.
- [x] 2.8 Subcomando `rows` que escribe ejecuciones y filas normalizadas en JSON sin tocar la base; antepone el fichero a los mensajes de `AdapterError`, deriva `run_id` y `report_sha256` y decide qué hacer con un informe sin filas (hallazgo L4 del QA de 2.4: error o aviso); clasifica con `classify_run_row` sobre el `run` crudo del adaptador, no sobre uno ya clasificado (la validación rechaza las columnas nuevas), y el motivo `sintetica` de JUP-068 lo resuelve `adapt_jup068` con `synthetic`; al imprimir mensajes que incluyan nombres de clave desconocidos (`run.retrieval.<clave>`, `results[i].<clave>`) los escapa con `repr` o los trunca (hallazgo L1 del QA de 2.6)

## 3. Generación de SQL y carga

- [x] 3.1 Subcomando `sql` (aunque la validación común deja un alfabeto cerrado, el SQL se genera SIEMPRE con literales escapados, nunca por interpolación directa; `run.retrieval` va como `jsonb`, sin cota de enteros: hallazgos L2 y L4 del QA de 2.6):
  - script transaccional e idempotente con `CREATE SCHEMA/TABLE IF NOT EXISTS`, vaciado e inserción dentro de la misma transacción;
  - `NULL` conservados y escapado seguro de literales;
  - sin credenciales en la salida.
- [x] 3.2 Vista `evaluation.config_changes` (cambios de batería, modelo, prompt o corpus entre ejecuciones consecutivas de la misma fuente; sin anotación de prompt cuando no está registrado) y consultas de comparabilidad (series con al menos dos ejecuciones)
- [x] 3.3 Subcomando `load` (hallazgos del QA de 3.1: el rol y los permisos van en un script APARTE del de `build_sql`, que no puede contener `GRANT`, `PASSWORD`, `CREATE ROLE` ni `DROP`; se ejecuta después de crear el esquema y en el mismo `psql`; `CREATE ROLE` no tiene `IF NOT EXISTS`, se usa un `DO` que mira `pg_roles` o `ALTER ROLE`; la contraseña se escribe con `sql_literal` con `standard_conforming_strings` activo en esa sesión; se pasan a `psql` bytes UTF-8, con `PGCLIENTENCODING=UTF8` si hace falta; el `TRUNCATE` bloquea brevemente la lectura de Grafana hasta el `COMMIT`):
  - pasa el script al `psql` de `postgres-pgvector` por la entrada estándar con `ON_ERROR_STOP`;
  - crea o actualiza el rol `grafana_evaluation_reader` con `USAGE` y `SELECT` solo sobre `evaluation`;
  - toma la contraseña de `GRAFANA_EVALUATION_DB_PASSWORD` y la envía solo por la entrada estándar;
  - termina con error claro si falta la variable.
- [x] 3.4 (hallazgos del QA de 3.3: documentar que `docker compose exec` necesita la pila levantada y el `.env` completo —también en CI y DockerServer, donde se puede usar `--psql-command "docker exec -i <contenedor> psql …"`—; que la contraseña de Grafana y la de `load` son la misma variable; y que los tests con PostgreSQL real necesitan Docker) Scripts `evaluation-dashboard:load`, `evaluation-dashboard:rows` y `evaluation-dashboard:test` en `package.json`, y `evaluation-dashboard:test` en el paso «Validate governance tooling» de `.github/workflows/ci.yml`

## 4. Grafana y compose

- [ ] 4.1 Datasource `apps/monitoring/grafana/provisioning/datasources/evaluation-postgres.yml` (uid `evaluation-postgres`, rol de lectura, contraseña por variable). `GRAFANA_EVALUATION_DB_PASSWORD: ${GRAFANA_EVALUATION_DB_PASSWORD:?required}` en Grafana dentro de `docker-compose.yml`, la variable sin valor en `.env.example` y `tools/docker-topology.test.mjs` actualizado
- [ ] 4.2 Prueba estructural del dashboard (en `scripts/tests/test_evaluation_dashboard.py`) escrita antes que el JSON. Comprueba:
  - cada panel tiene `Tipo: A|B|C`, `Mide:` y `No demuestra:`;
  - ningún panel mezcla `prometheus` y `evaluation-postgres`;
  - los paneles de evolución tienen `noValue` «Sin datos: no hay con qué comparar»;
  - los paneles de valor muestran «No medido» para `NULL`;
  - existen las secciones A, B y C y la sección de robustez.
- [ ] 4.3 (hallazgos del QA de 3.2: las anotaciones usan `run_at AS time, annotation AS text, array_to_string(changes, ',') AS tags` de `evaluation.config_changes`; cada panel de evolución define `noValue` «Sin datos: no hay con qué comparar» y se alimenta de `evaluation.comparable_runs`, filtrando por `comparability_key`, y por `is_real` donde convenga, porque la vista incluye ejecuciones no reales y varias claves; hay que castear `case_count`/`denominator` (`bigint`) si un panel los mezcla con `value` (`double precision`)) Dashboard `apps/monitoring/grafana/dashboards/assistant-evaluation.json` (uid `economicon-assistant-evaluation`):
  - sección A: ejecuciones con metadatos y motivos de no real, estados con denominadores, ACC/REL/GRD, evolución automática y de juicio humano con anotaciones de `config_changes`, LAT/STR/AVL de campaña, calibración, benchmark y robustez vacía;
  - sección B: negocio;
  - sección C: síntomas en vivo con las expresiones del diseño y enlace al dashboard técnico.

## 5. Pruebas con base real

- [ ] 5.1 Conciliación: tras cargar el manifiesto versionado en un PostgreSQL real, las mismas consultas SQL de los paneles devuelven los recuentos de estado y los `k`/`n` de cada informe original. La prueba se omite si no hay base, igual que las pruebas existentes con servicios reales
- [ ] 5.2 Permisos: el rol de Grafana no puede escribir en `evaluation` ni leer las tablas de embeddings
- [ ] 5.3 Idempotencia y atomicidad: dos cargas seguidas dejan los mismos recuentos y una carga que falla a mitad conserva la carga anterior

## 6. Validación de extremo a extremo y documentación

- [ ] 6.1 Validación con `docker compose up` y `corepack pnpm evaluation-dashboard:load`. Comprobar y capturar:
  - el dashboard provisionado junto al técnico;
  - la ejecución 2 de JUP-070 (plantilla) con sus 28 casos por estado y rotulada como no real;
  - las ejecuciones 1 y 2 con «Sin datos: no hay con qué comparar» en evolución;
  - la robustez y los no medidos sin 0 %;
  - la sección C con y sin tráfico.
- [ ] 6.2 Actualizar la documentación: guía de arranque y regeneración (README de monitorización o `docs/validation/README.md`), nota de despliegue sobre la variable nueva para DockerServer, y fila del tema en `docs/continuidad/README.md` con su resumen
- [ ] 6.3 Crear `docs/evidence/JUP-121-validation.md` con evidencia por criterio de aceptación de la tarjeta, lo no validado y por qué (robustez de JUP-071, despliegue en DockerServer). Ejecutar `corepack pnpm openspec:validate`, `corepack pnpm jup:check -- --change jup-121-assistant-evaluation-dashboard` y `corepack pnpm jup:cleanup:check`
