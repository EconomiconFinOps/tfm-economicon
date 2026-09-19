# Evidencia de validacion JUP-013

- Fecha: 2026-08-26.
- Repositorio: `EconomiconFinOps/tfm-economicon`.
- Rama: `feat/JUP-013-normalize-azure-costs` hacia `develop`.
- Pull request: https://github.com/EconomiconFinOps/tfm-economicon/pull/14.
- Tarjeta: https://trello.com/c/vw0xIKRN.
- Liderazgo: Alejandro Aguado; pairing: Lucia Mateo; revision: Paris Arcos
  Martin; validacion, pruebas y documentacion: Victor Mendez.

## Alcance implementado

- Contrato FinOps explicito sobre el normalizador de JUP-077.
- Alias EA, FOCUS y Azure Query reconciliados sin duplicar la ingesta.
- Resource group, servicio, proyecto, tags y consumo opcional tipados.
- Dimensiones desconocidas preservadas y tags legacy parseados de forma tolerante.
- Hash estable entre aliases equivalentes y rechazo de contradicciones.
- Migracion 003 aditiva, backfill e indices de analisis.
- Repositorio SQL actualizado para persistir y recuperar los nuevos campos.
- Consulta por defecto de resource group y servicio.

## Validacion

- Processor: `133 passed` con Python 3.12.
- Azure Cost API: `58 passed`.
- Backend: `10 passed`.
- Gobierno: JUP, politica de PR, CI, roadmap, repositorio, corpus, gateway e
  higiene superados.
- OpenSpec estricto: `17 passed, 0 failed`.
- Build de frontend de produccion superado.
- `git diff --check` y compilacion Python superados.
- CI remota inicial: seis checks superados en
  https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/33005896036.

## Validacion real en dockerserver

Se construyeron imagenes limpias de API y processor desde `bba770f` y se
levantaron CockroachDB 24.1.11 y la API simulada en un proyecto Docker aislado.
El entorno temporal y sus volumenes se retiraron al finalizar.

- Migraciones aplicadas: `001`, `002` y `003`.
- Slice por defecto `ResourceGroup + ServiceName`: 34 filas; las 34 contienen
  ambos campos tipados.
- Slice `Project + CostCenter`: 23 filas; 16 con tags y 11 con proyecto `Foo`.
- Repeticion del slice por defecto: mismo run ID
  `416193ab-2ecc-5247-b609-8e1eec396a85` y 34 filas, sin duplicados.
- Run ID de tags/proyecto: `2b7b7f60-84ce-5a9c-8993-6afeca571aa4`.

La salida solo contiene scopes, IDs, contadores y dimensiones del dataset
publico. No contiene credenciales ni se ha enviado ningun mensaje a Discord.

## Decisiones

Los campos dimensionales son opcionales porque Azure Cost Query solo devuelve
las agrupaciones solicitadas. La suscripcion de alcance permanece obligatoria en
la tabla y procede del path de la consulta. JUP-013 no construye la jerarquia de
JUP-014 ni calcula los KPIs de JUP-026.

## Integracion del 2026-09-08

Las secciones anteriores son evidencia historica del 26/08, no aprobaciones ni
resultados del nuevo head. Esta actualizacion prepara PR #14 antes de PR #19.

- Base incorporada: `278769c41e0b190f0fc348c5ad2079c4fb765326` (`develop`, JUP-094).
- Merge de actualizacion, sin reescribir historia: `c152b261c7e35d29df3503aa6bdcfd4463d22b0b`.
- Commit de implementacion probado: `aab79d1c8cd2e41741b3f9ae45668781b2fdfd2e`.
  Se registro el mismo contenido sobre el que se ejecutaron las pruebas.
- Arbol de `apps/processor`: `bae6127474e20e43e6dacb8d9de2a016269c0be3`.
  Los siguientes cambios de evidencia/checklist no modifican ese codigo.
- Contexto: Python 3.12.13 en Windows; pnpm 9; Docker de WSL Ubuntu con
  `cockroachdb/cockroach:v24.1.11`, nodo sin volumen persistente y puerto SQL
  publicado exclusivamente en `127.0.0.1:36413`.
- Ejecucion automatizada coordinada por el asistente; no atribuida a Lucia,
  Victor o Paris. Los cuatro responsables asignados no cambian.

### Defectos reproducidos y corregidos

1. La actualizacion 001/002 con seis filas fallaba con `UndefinedColumn` en el
   backfill de 003. El runner ahora conserva transacciones por migracion y 003
   opta explicitamente por autocommit para hacer visible el DDL ya completado.
   La version solo se registra despues del upgrade; los fallos se propagan.
2. Las etiquetas serializadas antiguas no llegaban a `tags` y `project`.
   El backfill incorpora los pares disponibles sin borrar dimensiones fuente.
3. La revision encontro rechazo de tags numericos legacy, union incompleta de
   tags individuales/serializados y mezclas de consumo parcial incompatible.
   Las regresiones adicionales fallaron antes de corregir esos tres casos.

Red observado: 11 fallos/14 aciertos en la primera bateria de recuperacion;
despues 5 fallos/161 aciertos por tags serializados; en la ronda de revision,
12 fallos/3 aciertos en los 15 nuevos casos. No se cuentan errores de entorno
como pruebas Red del producto.

### Validacion automatizada actual

Todos los comandos siguientes finalizaron con codigo 0, salvo las excepciones
explicitas de lint y los fallos Red descritos arriba. Cada servicio usa su propio
entorno `.venv` con `requirements-dev.txt`.

| Comprobacion | Comando y contexto | Resultado |
| --- | --- | --- |
| Processor con BD real | En `apps/processor`: `.venv/Scripts/python.exe -m pytest tests -q --tb=short --basetemp=<temporal-de-tarea>` con la variable de integracion indicada abajo | 181 passed; 34 casos reales; 130.50 s |
| Processor habitual/CI | Mismo comando sin `PROCESSOR_COCKROACH_TEST_URL` | 147 passed, 34 skipped |
| Backend | En `apps/backend`: `.venv/Scripts/python.exe -m pytest tests -q --basetemp=<temporal-de-tarea>` | 17 passed; 2 avisos heredados de clave de test corta |
| Azure Cost API | En `apps/azure-cost-api`: `.venv/Scripts/python.exe -m pytest tests -q --basetemp=<temporal-de-tarea>` | 58 passed; 2 avisos de deprecacion de dependencias |
| Frontend | `corepack pnpm --filter frontend build` | Vite 5.4.21, 89 modulos; build correcto |
| TypeScript | `corepack pnpm --filter frontend typecheck` | Ambos proyectos correctos |
| OpenSpec | `corepack pnpm openspec:validate` | 23 passed, 0 failed |
| Trazabilidad | `node tools/jup-check.mjs --all` | 18 cambios activos enlazados |
| Corpus | `node tools/assistant-corpus.mjs validate` | Correcto |
| Whitespace | `git diff --cached --check` | Correcto |

Las ocho suites de gobierno, roadmap, CI, corpus, gateway e higiene se ejecutaron
con el siguiente comando desde la raiz: 55 pruebas correctas.

```text
node --test tools/jup-check.test.mjs tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/delivery-roadmap.test.mjs tools/repository-governance.test.mjs tools/jup-cleanup-check.test.mjs tools/assistant-corpus.test.mjs tools/llm-gateway-config.test.mjs
```

El puente de colaboracion paso 12 pruebas con clientes simulados mediante
`apps/backend/.venv/Scripts/python.exe -m unittest discover -s tools/collaboration/tests -v`.
No se enviaron mensajes externos como parte de esas pruebas.

Para activar las pruebas reales se uso
`PROCESSOR_COCKROACH_TEST_URL=cockroachdb+psycopg://root@127.0.0.1:36413/defaultdb?sslmode=disable`.
El nodo desechable se marco previamente con la sentencia independiente
`SET CLUSTER SETTING cluster.organization = 'processor-integration-tests'`.
La fixture rechaza URLs de aplicacion, puertos predeterminados, nodos sin marca
y bases/tablas de usuario existentes; crea y elimina solo bases de nombre
aleatorio propias. Nunca debe apuntarse a un entorno compartido.

Cobertura real: instalacion limpia, upgrade de seis filas/ cinco grupos de
tenant-suscripcion-moneda, igualdad de IDs/costes/totales/dimensiones, indices,
persistencia de campos opcionales, aliases equivalentes, costes cero/negativos,
ingesta idempotente y rechazos sin persistencia parcial. Se inyectaron fallos
despues de DDL, backfill SQL, primer indice y antes de registrar la version.
Los seis tests del runner verifican rollback, reintentos, perdida del acuse de
una version ya confirmada, omision de versiones aplicadas y aislamiento posterior.
Otros 15 casos reales cubren tags numericos, fuentes mixtas y consumo parcial.

Despues de registrar `aab79d1`, se repitio una prueba de humo sobre ese commit:
`test_fresh_migrations_and_repository_round_trip` y
`test_legacy_upgrade_preserves_rows_backfills_and_ingestion[None]`, ambos en
`tests/test_azure_cost_cockroach_integration.py`: 2 passed en 13.29 s, codigo 0.

### Mutacion focalizada y revision

Siete mutantes en memoria, cada uno en un proceso aislado, fueron detectados por
fallos funcionales esperados de los tests versionados. No hubo supervivientes ni
errores de preparacion. No es una puntuacion de mutacion de todo el proyecto.

| Operador | Evidencia de deteccion |
| --- | --- |
| Volver transaccional 003 | `UndefinedColumn` al actualizar la tabla existente |
| Omitir el backfill Python de tags | Fallo de la fila `legacy-serialized-tags` |
| Reejecutar versiones completadas | Violacion de unicidad de `effects.version` |
| Registrar version antes del upgrade | El upgrade observa su marca prematura |
| Aplicar validacion estricta a tags legacy | Rechazo de `cost_center` numerico |
| Invertir precedencia del merge de tags | `project` retenido se sobrescribe con `Jupiter` |
| Omitir compatibilidad de unidad retenida | Se obtiene `2 Hours` en vez de conservar `(None, Hours)` |

Se uso un probe local no versionado, sin dependencias nuevas ni reescritura de
archivos de producto. Cada ejecucion comprueba que pytest falla en el cuerpo del
test y por la causa esperada; fallos de fixture, coleccion o herramientas no
cuentan como mutantes detectados. El resultado de revision tecnica y los
hallazgos cerrados estan en [review.md](../../openspec/changes/jup-013-normalize-azure-costs/review.md).
La auditoria tecnica local de QA dio QA_PASS el 08/09: evidencia y tareas
coherentes, tres enlaces Markdown relativos correctos y ningun bloqueo tecnico
pendiente. El gate local de entrada a QA y el control de higiene (404 archivos)
pasaron. Este resultado no cierra los gates humanos ni demuestra CI del nuevo head.

### Linea base y limites

- `corepack pnpm --filter frontend lint` mantiene 49 errores `react/prop-types`
  en nueve `.jsx` (codigo 1). `git diff --exit-code origin/develop -- apps/frontend pnpm-lock.yaml`
  devuelve 0: no hay errores nuevos introducidos por cambios frontend de esta PR.
  El lint heredado no se presenta como corregido.
- Una ejecucion local habitual tuvo un `WinError 10053` en el servidor HTTP de
  test; la repeticion completa paso sin cambios. Los problemas iniciales de ACL
  de temporales y acceso a dependencias se resolvieron con temporales propios y
  ejecucion permitida, sin modificar requisitos ni lockfile.
- No se han probado volumenes superiores al lote de 1.000 filas, interrupcion
  dentro del bucle Python ni migradores concurrentes. La migracion no incorpora
  coordinacion concurrente ni reintentos automaticos.
- La comprobacion real es del processor y sus servicios/repositorios contra BD;
  no representa validacion humana ni una migracion sobre entornos compartidos.

### Gates pendientes y orden de integracion

La consulta de reglas efectivas de GitHub del 08/09 exige siete checks, rama
actualizada, una aprobacion elegible con descarte de aprobaciones obsoletas y
conversaciones resueltas. No se usara bypass de administrador.

Se verificaron los siete checks sobre el head publicado
`3edfa60b0e49d055243284a47341f87694f70ea5` en la
[ejecucion 34245176166](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/34245176166):
`JUP policy`, `OpenSpec`,
`Python tests (azure-cost-api)`, `Python tests (backend)`, `Python tests (processor)`,
`Frontend build` y `Frontend type check`, todos completados con `success`.
Un commit posterior, incluso solo documental, requiere repetir esa verificacion.
Consultar los [checks de PR #14](https://github.com/EconomiconFinOps/tfm-economicon/pull/14/checks).

La aprobacion anterior de Paris figura como `DISMISSED` tras el push; no existen
conversaciones de revision pendientes en la consulta del 08/09. El solicitante
confirma que es Paris Arcos; esto identifica al revisor, no aporta una nueva
aprobacion. La solicitud automatizada de revision no se envio.

La actualizacion del cuerpo de PR fallo con HTTP 403 usando la integracion
disponible; su texto historico sigue desactualizado. Este archivo y el diff
publicado contienen los resultados nuevos. No se afirma haber actualizado ese
cuerpo ni haber recibido nuevas aprobaciones.

Tras terminar las pruebas se verificaron y retiraron el contenedor
`jup013-merge-20260908-tester-crdb` y su red exclusiva
`jup013-merge-20260908-tester`; no habia volumenes persistentes ni otros
contenedores conectados a esa red. No se tocaron recursos compartidos.

La tarea 3.5 permanece abierta: Lucia debe aportar pairing; Victor, validacion
funcional; Paris, revision del ultimo head. Sus evidencias deben incluir autor,
fecha, commit y resultado. La aprobacion anterior de Paris es historica.
Tambien sigue pendiente la aprobacion humana post-QA. No se ha efectuado merge.
Solo entonces procede squash a `develop` y actualizar PR #19 sobre ese resultado.
No se modifica Trello, no se archivan cambios adicionales y no se promueve a `main`.
