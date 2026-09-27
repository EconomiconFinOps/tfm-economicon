# Evidencia de validacion JUP-014

- Fecha: 2026-09-19.
- Repositorio: `EconomiconFinOps/tfm-economicon`.
- Rama: `feat/JUP-014-normalize-cost-hierarchy` hacia `develop`.
- Tarjeta: https://trello.com/c/xLIfC3am.
- Liderazgo: Lucia Mateo; pairing: Paris Arcos Martin; revision: Victor
  Mendez; validacion, pruebas y documentacion: Alejandro Aguado.

## Alcance implementado

- `ResourceId`, `ResourceName` y `BillingAccountId` expuestos como
  dimensiones consultables en la API Azure simulada
  (`docs/api/azure-cost-query-mapping.json`).
- `resource_id` y `resource_name` promovidos a campos tipados en
  `AzureCostNormalizer`, con el mismo patron de alias que JUP-013.
- Deteccion no bloqueante, dentro de una misma tanda de normalizacion, de
  un `resource_id` reportado bajo mas de un `resource_group`
  (case-insensitive, preservando el casing original por fila), persistida
  en la columna JSONB `resource_group_conflicts`.
- Migracion aditiva `004_resource_hierarchy.py`: nuevas columnas
  nullable, backfill desde `dimensions` para las dos primeras,
  `transactional = False` desde el inicio.
- Guardarraiz automatico (`app/db/migration_safety.py` +
  `tests/test_migration_safety.py`): detecta cualquier migracion que
  combine "anadir columna" + `UPDATE` en el mismo fichero sin
  `transactional = False`, cubriendo las migraciones reales (cero
  violaciones hoy) y casos reconstruidos pre/post-fix de JUP-013.
  Documentado en `docs/manuals/python-service-conventions.md`.
- `openspec/findings/backlog.md`: registrado `RF-014-001` (validacion de
  jerarquia entre ejecuciones historicas, fuera de alcance).

## Correccion durante la validacion: limite real de 2 dimensiones

El diseño original asumia que se podia anadir `ResourceId` como tercera
dimension de agrupacion junto a `ResourceGroup` + `ServiceName`. Un ensayo
real end-to-end (ver mas abajo) devolvio `400 BadRequest`: la API Azure
simulada limita `grouping` a 2 elementos
(`apps/azure-cost-api/app/models.py`, `Field(max_length=2)`), replicando
una limitacion real de Azure Cost Management.

Investigacion del historial: `ServiceName` se anadio exactamente en
JUP-013 (`bba770f`), llenando el hueco hasta el limite de 2 que ya existia
desde JUP-074 — no fue una decision deliberada de prioridad que esta
tarjeta deba respetar por encima de su propio objetivo.

Resuelto quitando `ServiceName` del `grouping` por defecto de
`run_azure_cost_ingestion.py`, quedando `ResourceId` + `ResourceGroup` — el
par que esta tarjeta necesita para la deteccion de jerarquia.
`service_name` deja de poblarse en la ingesta real por defecto, en la
misma situacion en la que ya estaban `subscription_name`/
`billing_account_id` antes de esta tarjeta (el normalizador los sabe
promover, pero la consulta por defecto no los pide). Nada en el codigo
consume `service_name` hoy (`GET /billing/summary` sigue devolviendo cifras
mock, `RF-091-004`).

## Validacion automatizada

| Comprobacion | Resultado |
| --- | --- |
| `azure-cost-api`: `pytest tests` | 59/59 |
| `processor`: `pytest tests` (sin la suite de CockroachDB real) | 273/273 |
| `processor`: `pytest tests/test_azure_cost_cockroach_integration.py` con CockroachDB 24.1.11 real desechable | 34/34 (17:25 min) |
| `pnpm openspec:validate` | 30/31 (el unico fallo, `containerized-runtime`, es preexistente en `develop`, no introducido aqui) |
| `pnpm jup:check:all` | Todos los cambios activos enlazados y completos |
| Governance/CI node tests (`jup-check`, `pr-policy`, `ci-workflow`, `delivery-roadmap`, `repository-governance`, `jup-cleanup-check`, `assistant-corpus`, `llm-gateway-config`) | 56/56 |
| Frontend: `lint` / `typecheck` / `build` | Correcto (sin tocar frontend) |
| `backend`: `pytest tests` | 115/115 (sin tocar backend) |

Ciclo RGR seguido en cada tarea de codigo de producto: test en rojo antes
de implementar, verde despues, suite completa sin regresiones, commit por
tarea.

## Validacion real de extremo a extremo

Se levanto un CockroachDB 24.1.11 desechable (sin volumen persistente,
puerto SQL solo en `127.0.0.1`, marcado con
`SET CLUSTER SETTING cluster.organization = 'processor-integration-tests'`)
y la API Azure simulada real (`uvicorn`) con el mapping actualizado de esta
tarjeta. Se ejecuto `app.run_azure_cost_ingestion` contra ambos, con
`RUNTIME_ENVIRONMENT=development` y `ALLOW_INSECURE_LOCAL_DATABASE=true`
para el opt-in local explicito.

- Resultado: `38` filas persistidas (antes `34`, con el grouping viejo
  `ResourceGroup` + `ServiceName`), cubriendo `31` recursos distintos en
  `9` resource groups distintos, para la suscripcion de muestra
  `64e355d7-997c-491d-b0c1-8414dccfcf42`.
- `38/38` filas con `resource_id` y `resource_group` poblados.
- `0` conflictos de jerarquia detectados — esperado: el dataset de muestra
  es un unico periodo estatico (menos de un mes), sin recursos que se
  muevan de resource group en la ventana consultada.
- Contenedor y base de datos manual (`jup014_manual`) desechables,
  verificados y retirados al finalizar. No se tocaron `develop` ni
  entornos compartidos.

## Bug real encontrado y corregido durante la validacion

`SqlAzureCostRepository.fetch_records` devolvia `resource_group_conflicts`
como lista de Python (JSON no distingue lista de tupla), rompiendo el
round-trip exacto con la tupla que produce `AzureCostNormalizer`. Detectado
por el test de integracion real contra CockroachDB (`test_fresh_migrations_and_repository_round_trip`),
no por los tests unitarios con conexion falsa — estos usan una conexion
simulada que nunca serializa a JSON de verdad. Corregido convirtiendo a
tupla en la lectura; 34/34 tests de integracion en verde tras el fix.

## Limitaciones y residuales

- `resource_group_conflicts` no se puede rellenar retroactivamente para
  filas ya ingeridas antes de esta tarjeta: es una senal calculada por
  lote de normalizacion, no un dato bruto disponible en `dimensions`.
  Queda `NULL` para datos historicos, documentado en `tasks.md`.
- `service_name` deja de poblarse en la ingesta real por defecto (ver
  seccion de correccion arriba). No es una regresion nueva: es la misma
  situacion en la que ya estaban `subscription_name`/`billing_account_id`.
- La validacion de jerarquia entre ejecuciones historicas de ingesta queda
  fuera de alcance, registrada como `RF-014-001`.

## Correccion tras la validacion del 2026-09-25

Alejandro Aguado reprodujo dos defectos en `_flag_resource_group_conflicts` tras integrar la PR #41 y devolvio la tarjeta a En curso. Se corrigen en la rama `fix/JUP-014-resource-conflict-detection`, sin reabrir el cambio archivado.

- Defecto 1: `RES-1` y `res-1` se trataban como recursos distintos. Ahora `resource_id` se compara sin distinguir mayusculas (con `casefold`, la convencion del repo) y cada fila conserva su valor original.
- Defecto 2: una fila sin `ResourceGroup` dentro de un recurso con conflicto lanzaba `AttributeError`. Ahora se normaliza sin error.
- Decision de Lucia (responsable) para el caso no cubierto por la spec: con dos o mas grupos observados, la fila sin grupo guarda todos esos grupos como senal de inconsistencia; con un solo grupo conocido, no hay conflicto. Recogida en la spec como escenarios nuevos.

### Revision adversarial

Revisor independiente (sin acceso al razonamiento de la implementacion) sobre spec y diff.

| Pasada | Veredicto | Findings y resolucion |
| --- | --- | --- |
| 1 | accept | ADV-2 (regla de fila sin grupo ausente en la spec): anadida a la spec. ADV-3 (`null` explicito lanzaba `AttributeError`): corregido. ADV-4 y ADV-5 (grafia guardada y orden dependientes del orden de filas): corregidos. ADV-6 (guardas distintas en las dos pasadas): corregido. ADV-1 (`casefold` frente a la comparacion de Azure): registrado como `RF-014-002`, convencion de todo el repo. |
| 2 | changes-requested | ADV-7/ADV-8/ADV-9: la spec prometia tolerar `null` en cualquier dimension, pero el cliente de Azure rechaza el `null` antes de normalizar y el normalizador lo rechaza en dimensiones no promovidas, `Tags` y alias. Resuelto acotando la spec a `resource_id` y `resource_group` y registrando `RF-014-003`. ADV-10 y ADV-11: riesgos aceptados (abajo). |
| 3 | accept | ADV-12 (valor vacio o en blanco junto a un alias con valor se rechaza, comportamiento previo a este fix): la spec aclara que la reconciliacion de alias se aplica antes y `RF-014-003` lo recoge. ADV-13 (frase inexacta del barrido): corregida abajo. |

Barrido de patron: las llamadas a `casefold()` de la funcion corregida quedan protegidas frente a valores vacios o nulos. El resto de llamadas del processor (`_take`, `_comparable`, etiquetas, migracion 003, servicio de ingesta) reciben siempre texto ya validado.

### Riesgos aceptados por Lucia (2026-09-27)

- ADV-10: el alias de tipo `DimensionValue` no incluye `None`, aunque `_comparable` ya lo acepta. Solo afecta a la anotacion de tipos.
- ADV-11: cada fila de un recurso con conflicto guarda la lista de los otros grupos, asi que el tamano crece con filas por grupos. Es aceptable porque en Azure un recurso pertenece a un unico resource group en cada momento y solo aparece bajo varios si se mueve dentro del periodo consultado, que es de una sola suscripcion: en la practica son 2 o 3 grupos. Se revisara si se implementa `RF-014-001` (validacion entre ejecuciones historicas), porque ampliaria el periodo comparado.

### Pruebas

- 16 casos nuevos en `apps/processor/tests/test_azure_cost_ingestion.py`: `ResourceId` en otra capitalizacion, grupo ausente, vacio, en blanco o `null`, combinaciones de ambos, un solo grupo conocido, `null` explicito en cinco dimensiones promovidas, estabilidad frente al orden de filas y orden de la lista.
- Processor: 292 passed, 34 skipped (los omitidos requieren CockroachDB real).

### Validacion con base de datos real (2026-09-27)

- Tests de integracion opt-in `tests/test_azure_cost_cockroach_integration.py` contra un nodo CockroachDB v24.1.11 desechable (sin volumen, solo en `127.0.0.1`, marcado con `cluster.organization`): 34 passed en 16 min; el fixture borro todas sus bases de prueba. Nota de entorno: el script de entrada de la imagen termina el contenedor al intentar crear `defaultdb`; se arranco con `--entrypoint /cockroach/cockroach`.
- Ingesta real con el stack de `docker compose` y la consulta por defecto: 38 filas en 4 paginas, 31 recursos, ninguno con varias grafias de `ResourceId` y 0 conflictos. En este dataset el resultado es el mismo antes y despues del fix, asi que no sirve como evidencia por si solo.
- Control positivo: las filas de los dos casos de la validacion del 2026-09-25 pasaron por el servicio de ingesta, el normalizador y el repositorio reales contra CockroachDB. Guardado leido por SQL: `RES-1`/`rg-old` con `["rg-new"]`, `res-1`/`rg-new` con `["rg-old"]`, `res-2` sin grupo con `["rg-new", "rg-old"]` y las dos filas de `res-2` con grupo con el otro grupo.
