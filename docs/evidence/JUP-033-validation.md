# JUP-033 — Evidencia de implementación

Fecha de verificación: **10/10/2026**. [Tarjeta](https://trello.com/c/ndrittYl).
Base `origin/develop=c2995a1`, rama `feat/JUP-033-recommendations`, copia aislada
`tfm-economicon-jup033`. El checkout compartido no se ha editado.

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
| Pruebas necesarias añadidas y en verde | 30/30 reglas/API pasan. En la ejecución inicial se omiten 3 Cockroach por ausencia de URL; su comprobación separada se registra abajo. |
| Documentación y decisiones actualizadas | Contrato, README backend, OpenSpec, continuidad; se reutilizan ADR-0001/0008/0010 y guardrails JUP-024/084 sin ratificar nuevas decisiones. |
| Pull request revisado y vinculado | Preparación técnica en esta rama; revisión humana asignada y merge pendientes. |
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
datos compartidos. Resultado independiente pendiente de completar.

Gobernanza: trazabilidad de los 9 changes y limpieza del repositorio correctas;
OpenSpec **56/56** estricto. Primera ejecución Node bloqueada por `spawn EPERM`
del sandbox; al repetir fuera, **83 pruebas correctas** y una carga fallida por
dependencia `yaml` ausente en la copia nueva. Se está instalando el lockfile desde
caché para repetir ese control. No es un fallo de reglas de recomendaciones.

La primera ejecución pytest sin salida se detuvo identificando su línea exacta
de comando y se repitió fuera del sandbox sin plugins automáticos. La ejecución
confirmada conserva avisos de deprecación de dependencias bajo Python 3.14;
no se ocultan fallos de assertions con ellos.

## Límites y pendientes

- Sin prueba de Azure real, utilización, tarifas alternativas ni ahorro potencial/realizado.
- JUP-034/039/058 tienen un contrato publicado; sus integraciones no se han ejecutado.
- No se prueba UI ni se sustituye la demostración frontend de recomendaciones.
- Falta pairing atribuible de Lucia, `Revision JUP-033` de Paris y `Validacion
  JUP-033` de Victor. La auditoría interna automatizada no reemplaza estos roles.
- No merge, cambio de prioridades/fechas o aceptación de la tarjeta inferidos.
