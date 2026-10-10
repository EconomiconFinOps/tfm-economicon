# JUP-028 — Evidencia de detección de candidatos de gasto no asignado

Verificación: 10/10/2026, Europe/Paris.
[Trello](https://trello.com/c/RG9O2Ltx).
Rama: `feat/JUP-028-unallocated-cost`.
Base: `origin/develop` en `c2995a118d419dfe725247bac9c6f219a3f0ea77`.
Worktree aislado: `../tfm-economicon-jup028`, relativo al checkout canónico.

Estado de esta evidencia: implementación, pruebas locales acotadas y regresión
Linux final disponibles; [PR #104](https://github.com/EconomiconFinOps/tfm-economicon/pull/104) publicada en borrador. Revisión y validación independientes pendientes; los checks de la PR conservan el estado de CI.
Este documento registra evidencia técnica propia; no es una review
`Validacion JUP-028` ni acredita aceptación de la tarjeta.

## Alcance Comprobable

`GET /billing/unallocated-cost` identifica candidatos basados en las etiquetas
observadas, con fechas explícitas UTC y pertenencia al tenant autenticado. La
respuesta declara `detection_basis=observed_required_tags` y
`allocation_status=not_evaluated`: no determina asignación financiera definitiva.

Las cinco dimensiones son owner, environment, application, cost_center y
project. Los costes se particionan por conjunto exacto de defectos, de modo que
una fila sin varias etiquetas aporta su coste una sola vez. Se separan monedas,
cargos positivos, ajustes negativos firmados y netos; se rechazan las fuentes
completadas solapadas antes de devolver importes. No requiere migración.

Fuentes de detalle:

- [Contrato y ejemplo de API](../api/unallocated-cost.md).
- [Especificación](../../openspec/changes/jup-028-unallocated-cost/specs/unallocated-cost/spec.md)
  y [diseño](../../openspec/changes/jup-028-unallocated-cost/design.md).
- [Pruebas de JUP-028](../../apps/backend/tests/test_unallocated_cost.py),
  [servicio](../../apps/backend/app/services/unallocated_cost.py) y
  [esquema](../../apps/backend/app/schemas/unallocated_cost.py).
- [Continuidad](../continuidad/gasto-no-asignado.md).

## Evidencia Por Criterio De La Tarjeta

La lectura actual de Trello mediante la integración oficial de DockerServer
confirmó los cinco criterios mínimos y los roles sin cambios. La consulta
inicial no encontró una PR existente de JUP-028.

| Criterio mínimo | Evidencia y estado al 10/10/2026 |
| --- | --- |
| Resultado funcional verificable | Endpoint y contrato implementados; respuesta autenticada, importes de referencia y SQL real verificados por la ejecución local acotada. Sólo candidatos por metadatos; no asignación financiera definitiva ni despliegue. |
| Pruebas necesarias añadidas y en verde | 55 pruebas locales aprobaron con los 22 casos JUP-028 originales. La regresión Linux final aprobó 934 pruebas, incluidos los 23 casos JUP-028 finales y la frontera 20000/19999 con neto cero; 21 pruebas quedaron omitidas y no se consideran validadas. |
| Documentación y decisiones actualizadas | Contrato API, OpenSpec, esta evidencia y continuidad disponibles; límites y dependencias sin integración declarados. OpenSpec estricto, trazabilidad y controles descritos más abajo aprobaron. |
| Pull request revisado y vinculado | PR #104 publicada en borrador y enlazada en Trello; revisión humana pendiente. No se acredita con los tests locales. |
| Validación funcional y evidencia enlazadas | Evidencia funcional técnica propia disponible; enlace publicado en Trello, validación independiente de Paris Arcos Martin pendiente. |

## Entorno Y Versiones

| Componente | Versión o identificación |
| --- | --- |
| Python local Windows | 3.12.13, entorno `../tmp/pr65-review-venv` relativo a la raíz del repositorio |
| pytest | 9.1.1 |
| FastAPI | 0.142.2 |
| Pydantic | 2.13.5 |
| SQLAlchemy | 2.0.54 |
| sqlalchemy-cockroachdb | 2.0.4 |
| psycopg | 3.3.6 |
| httpx | 0.28.1 |
| CockroachDB real | v24.1.11, contenedor exclusivo `economicon-jup028-tests` |
| Identificador del clúster de prueba | `cluster.organization=processor-integration-tests` |
| Node.js / pnpm | 24.14.1 / 9.0.0 |
| Imagen de regresión Linux | `jup047-review-20261008-6c760562-review-tests:latest` |
| Digest de la imagen Linux | `sha256:e1fda2000bd56cfa35278e56e5a4de42c937061e9a851327b6fb902218da8c8f` |
| Copia Linux exclusiva de código | `/tmp/economicon-jup028-985d`, montada de sólo lectura |

Las fixtures de costes e identidades son sintéticas. Las consultas de coste de
los casos marcados Cockroach se ejecutan contra una base real compatible con
el SQL del servicio. Los clientes de recursos del API son dobles de prueba;
no se comprueba una integración real de RabbitMQ, Redis, OpenAI ni del resto
de servicios a través de estas pruebas. Los casos de autorización, fechas y
redacción del error usan SQLite y, cuando corresponde, un doble explícito del
repositorio para comprobar que no se leen costes o que no se filtran detalles.

## Ejecución Local Acotada

Desde `apps/backend`, con el intérprete Python 3.12.13 descrito y el clúster
exclusivo accesible por el puerto local 28428:

```text
JUP086_COCKROACH_TEST_URL=cockroachdb+psycopg://root@127.0.0.1:28428/defaultdb?sslmode=disable
python -m pytest tests/test_unallocated_cost.py tests/test_billing_summary.py tests/test_tenant_isolation_api.py -q
```

Resultado: **55 passed**, 911.22 s; 723 avisos de deprecación de adaptación de
fechas SQLite. Los avisos no se presentan como fallos funcionales. Esta
ejecución recogió las 22 pruebas JUP-028 originales antes de añadirse el caso
final de frontera; no es evidencia de ejecución de ese caso añadido.

Cobertura funcional de los casos ejecutados:

| Caso | Resultado comprobado |
| --- | --- |
| Grupos excluyentes y referencias monetarias | EUR: positivos 100.00, completos 80.00, candidatos 20.00; ajustes -36.00, de los que -6.00 son candidatos; neto 64.00 y neto candidato 14.00. Los grupos owner, application y owner+cost_center+project aportan 10.00, 6.00 y 4.00, sin duplicar los defectos múltiples. |
| Valores inválidos y ausencia de fallback semántico | 26 registros con null, vacíos, marcadores, tipos no string, identificadores inválidos o entorno inválido resultan candidatos. Organization no sustituye owner; una columna project no sustituye el tag project requerido. |
| Identificadores y entornos aceptados | Ocho variantes válidas y los límites portables de identificador conservan metadatos completos, sin grupos candidatos. |
| Precisión y varias monedas | USD conserva `9007199254740993.01` como string decimal; costes 0.006/0.004 producen 40.00% a partir de pesos sin redondear, aunque sus importes visibles redondeen independientemente. |
| Ajustes, cero y vacío | GBP sin positivos conserva ajustes -20.00 y porcentaje null con `negative_adjustments_only`; JPY conserva filas de coste cero y `zero_cost_only`. Un periodo vacío no inventa una moneda de importe cero. |
| Ámbito y datos sin fecha | Se excluyen tenants ajenos, joins de tenant/suscripción incompatibles, ingestas incompletas/fallidas y fechas fuera de `[inicio, fin)`. Una fila elegible sin fecha produce `partial` y contador visible. |
| Solapamientos | Dos ingestas en la misma suscripción/día devuelven 409 sin importes incluso con tags completos y monedas distintas. Otras suscripciones o días no se confunden con solapamiento. |
| Acceso y selección | Falta de autenticación, tenant sin pertenencia o tenant ausente producen 401/403/400; once selecciones inválidas o incompletas producen 422 sin consulta de costes. El error 409 no expone el mensaje privado del repositorio. |

La comparación con JUP-017 se basa en reutilizar su predicado y su convención
de porcentaje complementario; no se ejecutó aquí el endpoint de su PR #66 ni
una integración combinada de ambas PR.

## Controles De Repositorio

Desde la raíz del worktree:

| Comando | Resultado registrado |
| --- | --- |
| `python -m compileall -q apps/backend/app` | Completado en la comprobación inicial. |
| `node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs` | 82 pruebas aprobadas. |
| `pnpm openspec:validate` | 56 elementos aprobados en validación estricta. |
| `pnpm jup:check:all` | Correcto. |
| `pnpm jup:cleanup:check` | Correcto. |
| `node tools/jup-check.mjs --change jup-028-unallocated-cost` | Correcto; trazabilidad de este cambio con Trello. |
| `openspec validate jup-028-unallocated-cost --strict --no-interactive` | Cambio válido. |
| `git diff --check` | Correcto en la comprobación documental inicial. |

Tras añadir el puntero de continuidad a AGENTS.md, el control de gobernanza
del repositorio volvió a ejecutarse: **13 pruebas aprobadas**.

La batería local no sustituye los checks de CI de la PR. El cambio OpenSpec permanece activo mientras la PR está en borrador. Un intento de publicar su archivo técnico fue rechazado por revisión automática al requerir autorización de archivo; se restauró el cambio activo, sin pérdida de especificación ni código.

## Regresión Completa: Incidencia Windows Y Resultado Linux

La ejecución amplia de backend en Windows se interrumpió por una incompatibilidad
de una fixture de salud existente: intercepta `socket.connect` y también alcanza
la creación del `asyncio.ProactorEventLoop`. Se reprodujo aisladamente:

```text
python -m pytest tests/test_health_provider_admission_jup047.py::test_uncertifiable_or_restart_state_never_sends[price_verified] -q
```

Resultado de la reproducción: **1 failed**, 9.54 s. No se cambiaron archivos de
producto de salud para sortearlo. La ejecución Windows completa no se presenta
como aprobada ni se atribuye automáticamente este fallo al producto JUP-028.

La regresión Linux completa terminó sobre la copia exclusiva de sólo lectura
y el mismo Cockroach real de pruebas: **934 passed, 21 skipped**, 2436 avisos,
157.49 s. Incluye los 23 casos finales de JUP-028 y el caso añadido
`test_displayed_complement_matches_tag_coverage_even_when_net_cost_is_zero`:
positivos 20000, metadatos completos 19999 y ajuste -20000 producen candidato
1.00, porcentaje complementario 0.00 y neto 0.00. Esta ejecución sí acredita
ese caso que todavía no existía al recoger la batería local de 55 pruebas.

Comando ejecutado por SSH en DockerServer:

```bash
docker run --rm --name economicon-jup028-backend-tests \
  --label task=JUP-028 --network host --cpus=2 --memory=3g \
  -v /tmp/economicon-jup028-985d:/work:ro -w /work/apps/backend \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e 'JUP086_COCKROACH_TEST_URL=cockroachdb+psycopg://root@127.0.0.1:28428/defaultdb?sslmode=disable' \
  --entrypoint python jup047-review-20261008-6c760562-review-tests:latest \
  -m pytest tests -q -p no:cacheprovider --basetemp=/tmp/jup028-pytest
```

Versiones efectivas Linux: Python 3.12.13, pytest 9.1.1, FastAPI 0.141.1,
Pydantic 2.13.5, SQLAlchemy 2.0.52, sqlalchemy-cockroachdb 2.0.4,
psycopg 3.3.5 y httpx 0.28.1. Las versiones Windows de la tabla anterior
corresponden sólo a esa ejecución local.

Las **21 pruebas omitidas no se consideran validadas**. Corresponden a
integraciones condicionales existentes: `test_embedding_parity` requiere el
cliente LiteLLM del processor, ausente en esta imagen; la integración RabbitMQ
requiere `JUP086_RABBITMQ_TEST_URL` y su hook de reinicio; el aislamiento vectorial
requiere `JUP086_VECTOR_TEST_URL`. No se atribuyen recuentos por archivo que no
se hayan medido. El recuento aprobado no acredita esas integraciones ni todos
los servicios reales. No se ha cambiado código de salud para lograr el
resultado Linux ni se presenta como resuelto el problema de fixture Windows.

## Límites Y Dependencias

El [contrato API](../api/unallocated-cost.md#ámbito-doble-cómputo-y-dependencias)
registra el contraste local del 10/10 con el candidato
`docs/finops/tagging-taxonomy.json` de JUP-015 y
`docs/api/showback.md` de JUP-027. Coinciden las cinco claves y reglas de la
taxonomía. Showback atribuye por una dimensión y permite project con fallback
desde columna; esta ruta evalúa exclusivamente tags, pondera positivos y
presenta dos decimales. Es una comparación de contratos locales, no una
integración probada ni una declaración de merge de esas tarjetas. Sus entregas
de referencia son las PR en borrador
[JUP-015 #88](https://github.com/EconomiconFinOps/tfm-economicon/pull/88) y
[JUP-027 #101](https://github.com/EconomiconFinOps/tfm-economicon/pull/101);
los enlaces no acreditan una prueba combinada.

No se validaron despliegue, interfaz de usuario, datos reales Azure, completitud
de facturas, catálogos corporativos, reglas de reparto, estados financieros
shared/excluded, recursos individuales ni reasignación. Datos agregados pueden
haber perdido owner/application; el resultado describe lo almacenado. La
reutilización de JUP-017 no integra el resto de PR #66. No se suman porcentajes,
dimensiones de showback ni diagnósticos solapados de endpoints distintos.

La política reutilizada tiene SHA-256
`7F95EF43BA5A5EE62392E44E0766CA46AF0D608F182CAC1BCFF3390398FFA039`;
esa identidad verifica el módulo reutilizado, no la integración de toda PR #66.

## Entrega Y Participación Pendientes

El encargo autorizado procede del chat
`01a1248a-4e9e-7963-a891-5d8cb49345a6` del 10/10/2026. Se mantuvieron los roles
reales registrados: Victor Mendez, liderazgo; Alejandro Aguado,
pairing/coautoría; Lucia Mateo, revisión; Paris Arcos Martin, validación.
La asignación no acredita trabajo conjunto, revisiones ni aceptación.

Entrega publicada: PR #104 draft contra develop; comentario Trello `6ac9ee6799d750dfd0c25c14`, 10/10/2026 09:51 Europe/Paris, mediante integración oficial. Pendientes: participación/pairing, revisión de Lucía y validación de Paris. No se afirma cierre, merge ni aceptación. El check JUP reviews requiere ambas reviews humanas; consultar el estado técnico de CI en la PR.

Limpieza confirmada: retirado el contenedor exclusivo
`economicon-jup028-tests`, terminado el túnel SSH local del puerto 28428 y
retirado automáticamente el contenedor de regresión Linux mediante `--rm`.
No quedan servicios de pruebas JUP-028 ejecutándose. Se conserva la copia de
fuentes `/tmp/economicon-jup028-985d` para reproducción.
