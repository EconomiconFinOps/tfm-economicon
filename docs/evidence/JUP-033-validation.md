# JUP-033 — Evidencia de implementación

Fecha de verificación: **10/10/2026**. [Tarjeta](https://trello.com/c/ndrittYl).
Base `origin/develop=c2995a1`, rama `feat/JUP-033-recommendations`, copia aislada
`tfm-economicon-jup033`. El checkout compartido no se ha editado.

[PR #97 draft](https://github.com/EconomiconFinOps/tfm-economicon/pull/97),
código validado `1c8dabf62c99a7ec55a0367d3e1c418a5c05733f`; la actualización
posterior completa únicamente documentación y el propósito de la spec.
CI técnica del código **7/7 verde** en la ejecución de PR
[38035291884](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035291884).
`JUP reviews` queda rojo por ausencia de los dos dictámenes, como corresponde
al draft. Trello En curso, nota `6ac9edbb7d64a2e99928110b`, sin marcar criterios
de aceptación como completados.

Esta es evidencia técnica del liderazgo, no una review `Validacion JUP-033`
ni aceptación humana. Asignaciones de la tarjeta leídas en vivo mediante
DockerServer `/home/danteadmin/economicon-collaboration`: Alejandro Aguado,
Lucia Mateo, Paris Arcos Martin y Victor Mendez, respectivamente liderazgo,
pairing, revisión y validación. No se acredita aquí pairing ni dictámenes.

## Entrega verificable

- [Contrato y uso](../architecture/optimization-recommendations.md).
- [Ejemplo generado](JUP-033-example.json) desde la fixture sintética
  `source()` en `apps/backend/tests/test_recommendations.py`. EUR con crédito
  sin proyecto, dos proyectos positivos y un importe USD superior a 2^53;
  no es facturación de un cliente ni evidencia de ahorro.
- Servicio y schema en `apps/backend/app/{services,schemas}/recommendations.py`;
  ruta en `apps/backend/app/api/routes/billing.py`.
- 17 pruebas de reglas/contrato y 13 de API con identidad/membership reales y
  doble explícito del resumen de costes; tres escenarios adicionales de SQL
  en Cockroach mediante fixture aislada optativa.

## Criterios mínimos de la tarjeta

| Criterio | Evidencia / estado |
| --- | --- |
| Resultado funcional verificable | GET autenticado genera propuestas de tagging e investigación, contexto de proyecto, costes exactos, moneda y evidencia. Ejemplo y tests enlazados; no hay aplicación cloud ni ahorro estimado. |
| Pruebas necesarias añadidas y en verde | 30 reglas/API y 3 Cockroach reales pasan; backend completo en CI Linux: 928 pass, 37 skip de integraciones optativas. Limitación local Windows registrada abajo. |
| Documentación y decisiones actualizadas | Contrato, README backend, OpenSpec, continuidad; se reutilizan ADR-0001/0008/0010 y guardrails JUP-024/084 sin ratificar nuevas decisiones. |
| Pull request revisado y vinculado | PR #97 draft enlazada; revisión humana asignada y merge pendientes. |
| Validación funcional y evidencia enlazadas | Evidencia del liderazgo aquí; validación independiente de Victor pendiente. No marcar la tarjeta como aceptada. |

## Ejecuciones

Entorno local: Windows, Python **3.14.4**, pytest **9.0.3**, FastAPI **0.115.12**,
Pydantic **2.12.5**, SQLAlchemy **2.0.52**, Node **24.14.1**, pnpm **9.0.0**.
La CI usa su configuración propia, incluido Python 3.12; no se confunden entornos.

Desde `apps/backend`:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/test_recommendations.py tests/test_recommendations_api.py -q
```

Resultado final de la batería específica: **30 passed, 3 skipped**, 99.06 s.
Temporales exclusivos fuera de Git. Autenticación y membership ejecutan SQL
real SQLite; `fetch_billing_summary` se sustituye sólo en los casos `[sqlite]`.
Las pruebas comprueban que no se llaman cola, embeddings ni escrituras de
jobs/conversación, y que los fallos de selección/tenant no consultan costes.
Se prueban ahorro nulo, referencias válidas, importes enormes, créditos/cero,
monedas, empates, estabilidad/cambio de IDs, truncamiento y HTTP 409.

Los tres escenarios `[cockroach]` ejercitan SQL real, controles de fuente,
project/fallback, fechas, créditos y un proyecto `60+60` en dos suscripciones
frente a otro de `100`. Requieren `JUP086_COCKROACH_TEST_URL` hacia un clúster
efímero vacío identificado como `processor-integration-tests`; nunca reutilizar
datos compartidos. **Resultado: 3 passed, 13 deselected, 62 warnings, 89.14 s**:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:JUP086_COCKROACH_TEST_URL='cockroachdb+psycopg://root@127.0.0.1:49333/defaultdb?sslmode=disable'
python -m pytest tests/test_recommendations_api.py -q -k real
```

CockroachDB **24.1.11**, psycopg **3.2.13**, sqlalchemy-cockroachdb **2.0.4**;
Docker cliente **29.4.0**, servidor **29.6.2**. Instancia efímera propia en
memoria, sin volúmenes, publicada sólo en loopback del servidor y accesible por
túnel SSH. Se ejecutó el binario `/cockroach/cockroach` directamente tras fallos
del wrapper de inicialización con el puerto de pruebas. Contenedor
`jup033-sql-20261010-a2f9033d` retirado y túnel detenido, puerto local libre.
No se modificaron bases ni contenedores existentes.

Gobernanza: trazabilidad y limpieza correctas; OpenSpec **56/56** estricto antes
y después del archivo/promoción. Primera ejecución Node bloqueada por `spawn
EPERM`; al repetir fuera, 83 pruebas correctas y una carga fallida por `yaml`
ausente. Tras `corepack pnpm install --frozen-lockfile --offline`, el control
restante pasa **12/12**: **95 pruebas de herramientas distintas en verde**.

`corepack pnpm build`: **4/4 tareas correctas, sin caché**, 3m49s. Primer intento
falló por el fallback pnpm del entorno (`ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY`).
Se antepuso al PATH **sólo del proceso** un `pnpm.cmd` temporal que llama a
`corepack.cmd pnpm`; `corepack pnpm exec pnpm --version` confirmó **9.0.0**.
No cambios globales. Avisos existentes: chunk frontend >500 kB y outputs de
Turbo para compileall; no afectan al resultado.

La primera ejecución pytest sin salida se detuvo identificando su línea exacta
de comando y se repitió fuera del sandbox sin plugins automáticos. La ejecución
confirmada conserva avisos de deprecación de dependencias bajo Python 3.14.

La regresión general local `python -m pytest tests -q --disable-warnings` se
interrumpió al 67% tras múltiples fallos. **No se declara verde en Windows.**
Diagnóstico reproducido de su primer bloque con
`python -m pytest tests/test_health_provider_admission_jup047.py -x -q --tb=short`:
la fixture bloquea `socket.connect`; `asyncio` de Windows necesita ese método
para crear su socketpair antes de atender el ASGI y dispara «Only controlled
gateway doubles are permitted in Red». El test y los servicios de salud no
cambian respecto de la base. No se modifica esa protección en JUP-033.

La regresión completa del mismo código sí pasa en
[CI Linux, ejecución 38035246060](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035246060):
**928 passed, 37 skipped**, 104.31 s. Python **3.12.15**, pytest **9.1.1**,
FastAPI **0.143.0**, Pydantic **2.14.0**, SQLAlchemy **2.0.54**. Los saltos
corresponden a integraciones optativas sin sus URLs; los tres escenarios
Cockroach de esta tarjeta se ejecutaron por separado como consta arriba.

## Límites y pendientes

- Sin prueba de Azure real, utilización, tarifas alternativas ni ahorro potencial/realizado.
- JUP-034/039/058 tienen un contrato publicado; sus integraciones no se han ejecutado.
- No se prueba UI ni se sustituye la demostración frontend de recomendaciones.
- Falta pairing atribuible de Lucia, `Revision JUP-033` de Paris y `Validacion
  JUP-033` de Victor. La auditoría interna automatizada no reemplaza estos roles.
- No merge, cambio de prioridades/fechas o aceptación de la tarjeta inferidos.
