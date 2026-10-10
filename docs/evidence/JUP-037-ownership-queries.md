# JUP-037 — Evidencia de implementación

Verificación del líder asistida por herramientas, 10/10/2026 (Europe/Paris).
No sustituye `Revision JUP-037` de Paris ni `Validacion JUP-037` de Victor.
Tarjeta: https://trello.com/c/n4Aplko2. Base: c2995a1 (`origin/develop`).

## Criterios de la tarjeta

| Criterio | Entrega y prueba | Estado |
| --- | --- | --- |
| Resultado funcional verificable | Consulta estructurada de proyecto/application/owner/cost_center/tag, respuesta exacta y evidencia persistida; schema/servicio/API/UI en esta rama | Implementado; ver resultados abajo |
| Pruebas necesarias añadidas y en verde | `test_ownership_questions.py`, `test_ownership_provenance.py`, `ownership-conversations.test.tsx`, `CostEvidence.test.tsx` y regresión AnswerEvidence | 209 backend, 35 frontend en verde; límites abajo |
| Documentación y decisiones actualizadas | [Contrato](../api/ownership-questions.md), OpenSpec y [continuidad](../continuidad/consulta-ownership.md) | Entregado |
| Pull request revisado y vinculado | [PR #100](https://github.com/EconomiconFinOps/tfm-economicon/pull/100) draft contra develop; revisión Paris y pairing Lucia no acreditados | Vinculada; revisión pendiente, no marcar cumplido |
| Validación funcional y evidencia enlazadas | Esta evidencia contiene pruebas automatizadas con dobles explícitos y SQL sintético; dictamen Victor pendiente | Pendiente validación humana |

## Entorno y resultados

Windows; Python 3.12.13, pytest 9.1.1, FastAPI 0.142.2, Pydantic 2.13.5,
SQLAlchemy 2.0.54, psycopg 3.3.6; Node 24.14.1, pnpm 9.0.0, Vitest 3.2.7.
Dependencias pnpm instaladas con lockfile congelado; sin cambios al lockfile.
CockroachDB v24.1.2 efímero en DockerServer, puerto remoto/local loopback 56537,
organización `processor-integration-tests`. El fixture crea/elimina su base propia;
ningún servicio o dato de la aplicación se modifica.
Contenedor y túnel propios retirados tras las pruebas; eliminación verificada.

Entrega enlazada desde [Trello](https://trello.com/c/n4Aplko2#comment-6ac9ede7d532f7533a85b38d);
la tarjeta queda En curso, sin aceptar criterios humanos ni cerrar.

- OpenSpec estricto: **56 pasan / 0 fallos**.
- Trazabilidad JUP y limpieza del repositorio: **PASS**.
- Gobernanza (`pr-policy`, `ci-workflow`, `repository-governance`): **82 pasan**.
- Typecheck frontend (source, node, tests): **PASS**.
- Lint de los ocho archivos frontend cambiados: **PASS**.
- Build frontend: **PASS**, advertencia existente de chunk mayor de 500 kB.
- Regresión final de escape de etiquetas y hash: **2 pasan**; selector `-k` incluyó
  además un caso SQL omitido en este pase sin DB (se comprueba en la batería SQL).
- Backend focal con SQL: **209 pasan / 0 fallos / 0 omisiones**, exit 0,
  254,36 s. Incluye 60 casos nuevos de ownership/procedencia y regresiones de
  billing, presupuesto, citas y retrieval. Advertencias deprecadas del adaptador
  datetime de SQLite/Python 3.12, sin fallo funcional.
- Frontend focal: **35 pasan**: 23 de integración (HTTP simulado) y 12 de
  componentes. El pase final de integración terminó con exit 0 en 134,57 s;
  ninguna aserción se modificó para resolver los tiempos de espera.
- CI de implementación b85b51b: **todos los checks técnicos en verde** en
  [workflow PR](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035453987).
  [JUP reviews](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035454090)
  falla por faltar los dos dictámenes humanos. El commit posterior solo actualiza
  documentación y archiva OpenSpec; no atribuirle automáticamente esa CI anterior.

El primer intento dentro del sandbox produjo errores de ACL de temporales y
`spawn EPERM`. Se repitieron comandos autorizados fuera del sandbox. Un intento
SQL concurrente encontró una base de fixture preexistente y fue rechazado por
su protección; se recreó solo el contenedor propio antes del pase definitivo.
La primera ejecución frontend tuvo 20 pass / 15 fallos de tiempo de espera con
dos workers; el pase secuencial con los límites temporales documentados pasó.
Un pase backend con salida redirigida se interrumpió por falta de progreso visible
y se sustituyó por salida inmediata/diagnóstico. Ninguno de esos intentos se
presenta como validación funcional satisfactoria.

## Reproducción

Desde `apps/backend`, con dependencias de `requirements.txt` y de test instaladas:

```powershell
$env:JUP086_COCKROACH_TEST_URL='cockroachdb+psycopg://root@127.0.0.1:56537/defaultdb?sslmode=disable'
python -u -m pytest tests/test_ownership_questions.py tests/test_ownership_provenance.py tests/test_billing_summary.py tests/test_budget_evaluation.py tests/test_citations.py tests/test_retrieval_contract.py tests/test_retrieval_failures.py -vv -p no:cacheprovider -o faulthandler_timeout=90 --basetemp=RUTA_TEMP_NUEVA --tb=short --maxfail=1
```

El fixture exige un clúster efímero vacío, usuario root sin contraseña, conexión
loopback no estándar y la organización arriba indicada. No apuntar a otro clúster.
SQLite verifica auth/membresía/propiedad y persistencia real de mensajes con un
doble explícito de billing; no acredita SQL financiero. Los casos Cockroach
ejecutan el repositorio real con ingestas/costes sintéticos: tenants cruzados,
fuentes incompletas, límites de fecha, overlap, precisión y etiquetas distintas.

Desde la raíz, los scripts habituales `pnpm --filter @finops/frontend ...`
pueden utilizarse; en esta máquina se usaron los ejecutables Node directos por
fallos/bloqueos de wrappers:

```powershell
node apps/frontend/node_modules/vitest/vitest.mjs run --root apps/frontend --config node_modules/.cache/jup037-validation.config.mts tests/ownership-conversations.test.tsx tests/conversations.test.tsx tests/tenant-switching.test.tsx --reporter=verbose
```

Para el entorno Windows cargado, la configuración efímera anterior combina
`vite.config` con un setup `configure({ asyncUtilTimeout: 10000 })` de
`@testing-library/react`, `maxWorkers: 1`, `testTimeout: 30000` y
`hookTimeout: 30000`. Se guardó exclusivamente en
`apps/frontend/node_modules/.cache/`; no modifica aserciones, código ni timeout
de tests versionados. Es necesario aumentar también el límite propio de Testing
Library (1 s por defecto), no solo el timeout del runner. Los tres archivos de
componentes se ejecutaron con la configuración habitual.

## Límites y pendientes

- Fixtures application/owner sintéticos: no acreditan datos desplegados ni
  disponibilidad de esas dimensiones en el mapping de Azure simulado actual.
- Sin catálogo JUP-015 validado, equivalencias semánticas nuevas, interpretación
  libre, conversión de divisas ni reparto de costes.
- JUP-036 PR69 no integrada; contrato compatible por diseño, combinación no probada.
- Sin ensayo visual manual, stack completo, proveedor IA ni despliegue.
- Pairing Lucia, revisión Paris, validación Victor, CI final y merge/cierre pendientes;
  este documento no los sustituye ni modifica atribuciones.
