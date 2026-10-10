# JUP-034 — Evidencia de implementación

Fecha: 2026-10-10. [Tarjeta](https://trello.com/c/Hdwz4SXw).
Base: `c2995a118d419dfe725247bac9c6f219a3f0ea77` (`origin/develop`).
Rama: `feat/JUP-034-impact`. Esta evidencia de implementación no sustituye
`Revision JUP-034` ni `Validacion JUP-034` de las personas asignadas.
[PR #96 draft](https://github.com/EconomiconFinOps/tfm-economicon/pull/96), contra
develop. Código probado en `08fbcfa86cdc752012ef2b792d61180c366c4dd9`; los commits
posteriores que sólo registren enlaces/resultados no cambian el runtime.

## Criterios de la tarjeta

| Criterio | Entrega y evidencia | Estado |
| --- | --- | --- |
| Resultado funcional verificable | POST autenticado `/recommendations/impact/evaluate`; [contrato y ejemplo](../contracts/recommendation-impact.md); mensual/anual y cartera sin scopes duplicados | Implementado y comprobado con datos sintéticos |
| Pruebas necesarias en verde | `apps/backend/tests/test_recommendation_impact.py`: aritmética independiente, precisión, desconocidos, solapes, monedas y autorización real/SQLite | 54/54 propias; batería amplia limitada por fallo previo Windows |
| Documentación y decisiones actualizadas | Contrato versionado, OpenSpec, README backend y [continuidad](../continuidad/impacto-recomendaciones.md) | Preparado |
| Pull request revisado y vinculado | PR #96 draft enlazada; revisión humana aún no emitida | Vinculación entregada; revisión pendiente |
| Validación funcional y evidencia enlazadas | Ejemplo sintético y pruebas por escenario; Alejandro conserva la validación independiente | Validación humana pendiente |

## Entorno y comprobaciones

Windows; Python 3.14.4, FastAPI 0.115.12, Pydantic 2.12.5, httpx 0.28.1,
SQLAlchemy 2.0.52, pytest 9.0.3, Node 24.14.1. CI usa Python 3.12/Node 22;
no se declara equivalencia sin sus resultados.

CI sobre el código publicado `08fbcfa`: [backend Linux/Python3.12](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035231095/job/114164172826)
**952 passed, 34 skipped**, 120.56s. Los skips se mantienen como límites de
integraciones opcionales; no son evidencia de ejecución CockroachDB/pgvector reales.
También SUCCESS OpenSpec, azure-cost-api, processor, frontend build y typecheck
en ese run, y JUP policy en [evento PR](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035278744).
`JUP reviews` pendiente/fallido por ausencia de los dictámenes humanos; draft
conservado. La comprobación CI anterior acredita el runtime del código y no
convierte en verde la batería Windows incompleta descrita debajo.

- `python -m compileall -q app` en backend: correcto.
- `node tools/jup-check.mjs --all`: 9 changes correctos.
- OpenSpec 1.8.0 `validate --all --strict --no-interactive`: **56/56**.
- `node tools/jup-cleanup-check.mjs`: correcto.
- `corepack pnpm install --offline --frozen-lockfile --ignore-scripts`: correcto,
  547 paquetes desde caché; lockfile sin cambios.
- Gobernanza: **70/70** tests de política PR/repositorio + **12/12** de workflow CI.
  Primer intento limitado por `spawn EPERM` del sandbox Windows y `yaml` aún
  ausente; repetición fuera del sandbox tras instalar dependencias correcta.
- Ejecución del JSON documentado con `ImpactRequest.model_validate_json` y
  `evaluate_recommendation_impact`: **55.00 EUR/mes, 660.00 EUR/año**;
  `schedule-vm` excluida por `rightsize-vm`, desconocida conservada y observado null.
- Batería backend local: **355 passed, 8 skipped, 1 failed** con `--maxfail=1`.
  Falla `test_health_provider_admission_jup047.py::test_uncertifiable_or_restart_state_never_sends[price_verified]`:
  el bloqueo de `socket.connect` del test también bloquea el `socketpair` interno
  de `asyncio` en Windows/Python 3.14. Reproducido el mismo fallo exportando sólo
  `apps/backend` desde la base limpia `c2995a1` a una copia temporal, sin JUP-034.
  No se modifica ese test ajeno ni se declara pasada la batería completa.
- Ejecuciones con `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'` para excluir plugins
  globales ajenos a requirements-dev, y `--basetemp=.pytest_cache/jup034-full-clean`.
  El padre `.pytest_cache` se creó antes. Intentos previos tuvieron permisos de
  temporales y un padre inexistente; no son evidencia funcional del producto.
- Suite propia: **54 passed, exit 0, 74.59 s**. Comando desde `apps/backend`:
  `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; $env:PYTHONUNBUFFERED='1'; python -m pytest tests/test_recommendation_impact.py -vv -s -o faulthandler_timeout=30 --basetemp=.pytest_cache/jup034-impact-final --maxfail=1`.
  479 avisos de deprecación de dependencias; sin fallos JUP-034. Incluye 7
  casos de rechazo de autenticación/tenant, 5 de campos de autoridad/observado
  prohibidos y cálculo con aplicación real, además de referencias matemáticas.

## Límites

Inputs del ejemplo y tests son sintéticos. JWT, pertenencia de tenant, validación
del body y cálculo se ejercitan con la aplicación real; infraestructura externa
de startup usa los dobles establecidos y DB SQLite en las pruebas propias.
No se midieron beneficios, costes reales, aceptación del usuario, idoneidad de
acciones ni precios de proveedor. No hay LLM, cloud, despliegue o costes externos.
JUP-033 es un productor en otra rama simultánea: IDs y tipos contrastados por
lectura; no se declara integrada su salida ni se importa código ajeno.
La selección evita doble conteo sólo si el productor declara de forma completa
las mismas claves atómicas para costes equivalentes. No verifica esas claves
contra facturación. La selección greedy no garantiza el máximo global.

Roles de Trello preservados: Lucía liderazgo, Paris pairing, Víctor revisión,
Alejandro validación. Pairing, dictámenes humanos, merge y cierre pendientes.
La publicación asistida usa la cuenta configurada de Alejandro. Es contribución
técnica en rama propia, no validación independiente ni reasignación del liderazgo.
Si Alejandro figura como autor de la PR canónica, no puede validar esa misma PR:
el liderazgo debe regularizar la entrega y, cuando corresponda, acordar cualquier
reasignación explícitamente en Trello antes de satisfacer los gates humanos.

Vinculación Trello mediante integración DockerServer confirmada por relectura:
comentario `6ac9ece763aa2861b02209f3`, 2026-10-10T07:44:39.713Z. No se modificaron
descripción, fechas, prioridad, roles ni lista; sin cierre ni mensajes Discord.
