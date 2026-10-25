# Review de jup-106-synthetic-cost-data

JUP: JUP-106. Tarjeta: https://trello.com/c/JwumJnIf. Rama `feat/JUP-106-synthetic-cost-data` sobre develop `f0cacdd`.

## Resumen

Se añade `scripts/synthetic_costs.py`, una herramienta con los subcomandos `apply`, `status` y `remove` que carga, consulta y retira un conjunto determinista de datos de coste sintéticos (2026, tenant `tenant-growth` por defecto) en las tablas `azure_cost_ingestion_runs` y `azure_cost_records`, con las pruebas `scripts/tests/test_synthetic_costs.py`, el documento `docs/validation/JUP-106-synthetic-costs.md` con los valores esperados, y el paso `synthetic-costs:test` en CI. No cambia `apps/`, migraciones, el simulador ni el dataset público.

## Decisiones

- Inserción directa en las tablas de costes y no un fixture nuevo en el simulador (D1 del diseño): evita contaminar el dataset público y permite casos que la ingesta no produce (fila sin fecha, importe fuera del rango seguro).
- `tenant-growth` por defecto, con guarda: la herramienta se niega a cargar si el tenant tiene datos de coste reales y la retirada borra solo filas sintéticas (D2).
- Marcado por prefijo reservado `synthetic-jup106-`, y solo cuenta como sintética una ingesta cuyo `request.synthetic` sea el booleano JSON `true` y un registro que pertenezca a una ingesta sintética (D3, endurecido tras la pasada adversarial).
- La comprobación de datos reales se repite dentro de la transacción de escritura.
- Fuente solo ASCII para que la tubería de PowerShell no la altere.
- Aplicabilidad de ADR: no aplica. No hay una decisión arquitectónica duradera ni transversal; es una herramienta local de validación.

## Validación

Comandos y resultados (detalle en `docs/evidence/JUP-106-validation.md`):

- `corepack pnpm synthetic-costs:test`: 46 pruebas; con `sqlalchemy` pasan 38 y se omiten 8 (las de CockroachDB), y en el job de CI (Python 3.12 sin paquetes) pasan 37 y se omiten 9: la CI no ejecuta ninguna sentencia de `SqlStore`. Con CockroachDB v24.1.11 real y desechable (`JUP086_COCKROACH_TEST_URL`): 46 de 46, con la prueba validando la URL y la marca del nodo y usando una base propia que borra al terminar.
- Rojo previo: las pruebas fallaron por la ausencia de la herramienta; las de los hallazgos de la pasada adversarial fallaron antes de corregirlos (nombre de tenant con salto de línea, carrera entre comprobar y escribir, retirada con registros reales colgando).
- Mutantes: 25 de 25 de lógica y 7 de 7 de SQL real detectados en la primera ronda tras cerrar tres supervivientes con pruebas nuevas; 14 más sobre el código añadido tras la pasada, con 12 detectados y 2 que solo pueden detectarse con la prueba de base de datos real (viven en `SqlStore`) y que sus equivalentes con SQL real sí detectaron.
- Extremo a extremo con el stack aislado: carga, idempotencia, `/billing/summary` frente a los valores esperados (12 de 12 comprobaciones), recorrido del dashboard de develop con los mismos importes que la API, retirada que deja `tenant-growth` vacío y `tenant-core` intacto, y carga rechazada con datos reales.
- `corepack pnpm openspec:validate` 47 de 47, `jup:check` y `jup:check:all`, `jup:cleanup:check` (840 archivos), `ci-workflow` y `repository-governance` 25 de 25, `assistant-metrics:test` y `git diff --check` limpios; enlaces del documento sin romper.

## Adversarial Review (pass 1)

Un revisor independiente recibió solo el change, la base, el head y los contextos de esquema y de agregación del backend, y ejecutó las pruebas con y sin CockroachDB real. Veredicto: **accept**, sin BLOCKING ni HIGH.

| ID | Severidad | Estado | Resumen | Cierre |
| --- | --- | --- | --- | --- |
| ADV-1 | MEDIUM | Confirmado | `validate_tenant` aceptaba un salto de línea final (`$` con `re.match`) y escribía el tenant con `\n` | Corregido con `fullmatch`; pruebas con `\n`, `\r\n`, tabulador, NUL y Unicode |
| ADV-2 | MEDIUM | Confirmado (simulado) | Carrera entre comprobar datos reales y escribir: una ingesta real intermedia se mezclaba con los datos sintéticos | Corregido: la comprobación se repite en la transacción de escritura y la carga aborta con `refused`; pruebas con el almacén simulado y con CockroachDB real |
| ADV-3 | MEDIUM | Confirmado | Un registro real colgando de una ingesta sintética hacía fallar `remove` con `IntegrityError` | Corregido: `remove` se niega con un mensaje y salida 2 sin borrar nada; pruebas simuladas y con CockroachDB real |
| ADV-4 | LOW | Confirmado | Una ingesta con `request.synthetic = "true"` (texto) y el id reservado se consideraba sintética | Corregido: solo vale el booleano JSON `true`; prueba con SQL real |
| ADV-5 | LOW | Confirmado | Con dos `apply` simultáneos solo uno gana; los demás ven `IntegrityError` genérico en lugar de `already-present` | Sin cambios: ver abajo |
| ADV-6 | LOW | Confirmado, discutible | `remove` no recibe `--tenant` y retira el conjunto sintético de todos los tenants; sin filas imprime «0 ingestas y 0 registros» sin un aviso explícito; `apply` también se niega ante ingestas reales sin registros (más estricto que la spec) | Sin cambios: ver abajo |
| ADV-7 | LOW | Confirmado | Dos mutantes sobrevivían (`page_count`, texto de `request.change`) | Corregido con una prueba que fija todos los campos de las ingestas |

Ataques que resistieron (informe del revisor): valores esperados del documento frente a `fetch_billing_summary` sobre una base real (totales, desgloses por las cinco agrupaciones, marzo vacío, febrero con cero y 10,50 USD, julio con el importe grande, estado `empty` tras la retirada); atomicidad de la inserción ante un conflicto de clave primaria; determinismo (dos cargas dan filas idénticas); protección de filas reales con el prefijo en mayúsculas, precedido de otro texto o con la petición no objeto; lógica de tres valores de SQL con NULL; secretos (ni la URL ni la traza salen en ninguna salida); invocación real por la entrada estándar con Python 3.12; CI (una línea nueva, sin cambiar disparadores ni permisos) y la ausencia de inyección SQL, porque todo valor va enlazado.

No ejecutó: una ingesta real del processor en paralelo (la carrera se simuló con una inserción equivalente), Python 3.10 y 3.11, ni la interfaz; el recorrido de la interfaz lo hizo el autor del change (ver evidencia).

## Revisión de PR (Víctor, Request changes sobre `558a149`)

1. La prueba contra CockroachDB real no protegía el nodo: usaba la URL tal cual, migraba y borraba filas sin condición en `defaultdb`, y dejaba el nodo inservible para las suites del backend y del processor. Corregido con base propia, validación de URL y marca, y limpieza al terminar.
2. Ocho mutantes relevantes sobrevivían a las pruebas (campos de un registro, `INSERT` con campos cambiados u omitidos, `subscription_id` constante, `count_real` sin filtrar por tenant). Corregido con referencias escritas a mano para las cinco agrupaciones y la comparación campo a campo con SQL real; los ocho se detectan (tres también en CI).
3. Los recuentos eran ambiguos: son 46 pruebas, y la CI ejecuta 37 y omite 9; no ejecuta ninguna sentencia de `SqlStore`. Corregido en la descripción del PR, la evidencia, este review y la guía.

Observaciones atendidas: `status` y `apply` deciden `present` solo por identificadores y `remove` acepta `--tenant` sin usarlo, ambas escritas en «Límites» de la guía y en RF-106-002, y una prueba fija la salida 2 con un tenant inválido. `scripts/synthetic_costs.py` no cambia.

## Barrido del patrón

- ADV-1 (`$` con `re.match` en un validador de identificador): en el repositorio, `apps/processor/app/agents/guardrails.py` define `SAFE_SOURCE` y `SAFE_STATUS` con `^...$` pero ambos se usan con `fullmatch`; `apps/backend/app/core/config.py` usa `fullmatch`. No hay otro caso.
- ADV-2 (comprobar y luego escribir en conexiones distintas): solo en `apply`.
- ADV-3 y ADV-4: solo en `delete_synthetic`, `count_real` y `SYNTHETIC_RUNS` de esta herramienta; las demás herramientas de `scripts/` no borran filas ni usan un prefijo reservado.

## Riesgos

- Dependencia del esquema: la herramienta inserta en columnas de las migraciones 002 a 004, y un cambio de esquema la rompería. La prueba contra CockroachDB real lo detecta al ejecutarla, no en CI. Es un riesgo propio del cambio, y se mitiga con esa prueba y con la documentación del límite; no se acepta como sin cubrir.
- `tenant-growth` deja de estar vacío mientras los datos estén cargados. Está avisado en el documento y la retirada lo restaura; es una decisión de diseño (D2).
- ADV-5 y ADV-6, LOW, quedan sin corregir; Lucia los acepta el 2026-10-07 y se registran como RF-106-001 y RF-106-002 en `openspec/findings/backlog.md`.

## Hallazgos fuera de alcance

Ninguno nuevo en el producto. Observación para JUP-055 y JUP-104: el dashboard de develop no tiene comparación entre meses ni gráfico de serie propios, así que este conjunto se usa para validar la comparación en la #77, y JUP-104 supone `tenant-growth` vacío de costes (el documento avisa).

## Human Approval

- Change: jup-106-synthetic-cost-data
- Approval type: post-review
- Decision: approved
- Approver: Lucia
- Date: 2026-10-07
- Adversarial review: accept (pass 1); accepted findings: ADV-5 y ADV-6 (LOW), registrados como RF-106-001 y RF-106-002 en `openspec/findings/backlog.md`
- Archive decision: archive
- Notes: aprobada la herramienta, el conjunto de datos sinteticos y su documento de valores esperados, con los hallazgos ADV-1 a ADV-4 y ADV-7 corregidos con prueba. El recorrido del dashboard de develop solo cubrio totales, desgloses, hueco, cero y dos monedas; la comparacion entre meses se valida con estos datos en JUP-055 (#77). La revision de PR y la validacion funcional de otros miembros quedan en Trello y en el PR; no se ha ejecutado Python 3.10 ni 3.11, ni una ingesta real en paralelo.
