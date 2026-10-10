# JUP-038 — Evidencia de la contribución

Verificado el 2026-10-10, base `origin/develop` `c2995a1`.
[Tarjeta](https://trello.com/c/QzkjVY7P). Contribución independiente en
`feat/JUP-038-explain-anomalies`; no es la review humana `Validacion JUP-038`.

## Criterios de la tarjeta

| Criterio original | Evidencia y estado |
| --- | --- |
| Resultado funcional verificable | Explicador determinista, ruta autenticada e historial. Contrato probado con dobles y siete escenarios contra módulos candidatos JUP-030; SQL de coste real y despliegue conjunto pendientes. La base sin JUP-030 responde 503. |
| Pruebas necesarias añadidas y en verde | Pruebas unitarias, API y adaptador añadidas; resultados reproducibles debajo. |
| Documentación y decisiones actualizadas | [Contrato](../contracts/JUP-038-anomaly-explanations.md), [OpenSpec](../../openspec/changes/jup-038-explain-anomalies/), README backend y continuidad. |
| Pull request revisado y vinculado | [PR #94](https://github.com/EconomiconFinOps/tfm-economicon/pull/94) en borrador contra develop; revisión de Víctor pendiente. No se acredita revisión humana por una inspección automática. |
| Validación funcional y evidencia enlazadas | Este informe acredita comprobaciones técnicas; aceptación funcional independiente de Alejandro pendiente, sin autoaprobar la contribución. |

Roles preservados desde Trello, contraste mediante integración oficial
DockerServer: Lucía Mateo liderazgo, Paris Arcos Martin pairing, Victor Mendez
revisión, Alejandro Aguado validación/pruebas/documentación. No se atribuyen
pairing, reviews, aceptación ni cambio de responsable por este trabajo.

## Entorno y comandos

Windows, Python 3.14.4, pytest 9.0.3, Pydantic 2.12.5, FastAPI 0.115.12,
SQLAlchemy 2.0.52; Node 24.14.1, pnpm 9.0.0, OpenSpec 1.8.0.
Dependencias JS instaladas con `corepack pnpm install --frozen-lockfile --offline --ignore-scripts`.

Desde `apps/backend`, para las pruebas nuevas:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/test_anomaly_explanations.py tests/test_anomaly_explanations_api.py -q -p no:cacheprovider --basetemp <directorio-temporal-exclusivo>
```

Las pruebas nuevas pasan **50/50**: explicador **26/26** y API/adaptador
**24/24**. La ejecución API final fuera de sandbox terminó con exit 0 en
158.38 s (648 advertencias de deprecación de dependencias), sin cambios a
fixtures ni al comportamiento de os.mkdir. El explicador cubre umbral inclusivo, dos reglas,
porcentaje exacto frente a redondeo, decimales >2^53, base ausente/cero/crédito,
calidad parcial, etiquetas adversariales, desajustes numéricos y evidencia
desactualizada/inexistente. Las pruebas API verifican autenticación y SQL
SQLite real para pertenencia/conversación/historial; detector y costes son
dobles explícitos, sin llamadas a embeddings/retrieval/modelos.

La primera ejecución en sandbox produjo WinError 5 al usar directorios de
pytest, y Node produjo `spawn EPERM`. Se repitieron fuera del sandbox con
temporales propios. Esos intentos fallidos no se cuentan como pruebas verdes.

Desde la raíz:

```text
node tools/jup-check.mjs --all
node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs
node tools/jup-cleanup-check.mjs
node node_modules/@fission-ai/openspec/bin/openspec.js validate --all --strict --no-interactive
python -m compileall -q apps/backend/app scripts/check_anomaly_explanation_candidate.py
git diff --check
```

Resultados: trazabilidad de nueve changes PASS; gobernanza **82/82**;
OpenSpec **56/56**; higiene, compilación y diff check PASS.

## Contraste con el candidato JUP-030

```text
python scripts/check_anomaly_explanation_candidate.py --detector-root <copia-JUP-030>
```

**7/7 PASS**, nueva ejecución sobre el código de explicación final. El script
carga explícitamente los dos módulos de la copia solicitada mediante importlib
y ejecuta el adaptador y el explicador. La facturación es un doble sintético;
no simula que se haya probado SQL de coste o un despliegue.

Casos: absoluto, ambas reglas, base ausente, base cero, datos parciales,
importe grande y cambio de evidencia. Hashes SHA-256 de los módulos candidatos:

| Archivo en JUP-030 | SHA-256 |
| --- | --- |
| apps/backend/app/schemas/anomalies.py | 5570a6000c71c2f63d57d5ce41213a7f869aa328c8e91f17eeb573276455ce0b |
| apps/backend/app/services/anomalies.py | 1660951e333180429a534be54253360242af320e6f9207f64c3856b72e34300b |

Los archivos estaban sin commit al contrastarlos. Los hashes fijan únicamente
esa evidencia; la combinación que se integre necesitará revalidación.

## Pendientes y límites

- Integración de JUP-030 y prueba conjunta con SQL de coste real; no basta con
  el probe ni con que CI pase sobre dobles.
- Selección visual y enrutado libre JUP-035/036: contrato disponible, conexión
  no declarada implementada. No se ha probado un navegador ni el flujo completo.
- Conformidad de Lucía, pairing real, revisión y validación independientes.
  OpenSpec permanece activo hasta satisfacer integración y aceptación.
- No hay diagnóstico causal, ahorro demostrado, conversión monetaria, Azure
  real, coste de modelos, despliegue ni ejecución de infraestructura.
- Las escrituras de los dos mensajes no son atómicas, como en el chat actual;
  no se promete idempotencia de reintentos.
