# Evidencia técnica — JUP-039

Verificación: 2026-10-10. Tarjeta https://trello.com/c/ojFr6fCU. Base
`c2995a118d419dfe725247bac9c6f219a3f0ea77`, rama
`feat/JUP-039-savings-summary`. Entrega en copia aislada; no cambios del
checkout compartido, otros roles ni otras tarjetas.

## Criterios de la tarjeta

| Criterio | Evidencia | Estado y límites |
| --- | --- | --- |
| Resultado funcional verificable | Servicio determinista, comando `/ahorro inicio fin`, petición savings_query, adaptador033/034 | Incremento técnico implementado. Runtime financiero pendiente de loaders reales; por defecto503 explícito. |
| Pruebas necesarias añadidas y verdes | test_savings_summary.py, test_savings_sources.py, test_savings_summary_api.py y regresiones de asistente | Resultados finales se registran debajo; fuentes sintéticas y repositorios SQLite reales en API. |
| Documentación y decisiones actualizadas | Contrato docs/api/savings-summary.md, OpenSpec jup-039-savings-summary, continuidad | Conserva las diferencias entre candidatos033 y escenarios034 y la dependencia pendiente. |
| PR revisado y vinculado | PR draft de contribución para liderazgo Paris | Revisión humana pendiente; no sustituida por auditoría interna. |
| Validación funcional y evidencia enlazadas | Pruebas automatizadas, smoke con funciones productoras y este informe | Validacion JUP-039 de Lucia pendiente; no aceptación de tarjeta. |

## Entorno y comandos

Python 3.14.4, pytest 9.0.3, Pydantic 2.12.5, Node 24.14.1, yaml 2.9.0,
OpenSpec fijado por repositorio a1.8.0. Windows. No llamadas a modelo/Azure,
ni aprovisionamiento, migraciones o cambios de datos del entorno compartido.

Desde `apps/backend`, con dependencias de requirements-dev.txt instaladas:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/test_savings_summary.py tests/test_savings_sources.py tests/test_savings_summary_api.py -q -p no:cacheprovider --basetemp <directorio-temporal-nuevo>
python -m pytest tests/test_tenant_isolation_api.py tests/test_citations.py tests/test_assistant_service.py tests/test_retrieval_failures.py tests/test_retrieval_traceability.py -q -p no:cacheprovider --basetemp <otro-directorio-temporal-nuevo>
```

Resultados: servicio/schema **85 passed** (4.63s); adapter **44 passed** (5.76s);
API de ahorro y regresiones del asistente **118 passed, 2 skipped** (218.39s).
Las dos omisiones requieren JUP086_COCKROACH_TEST_URL externo; no se afirman
comprobadas. Regresiones finales HTTP de controles/epoch y clasificación502:
**7 passed, 21 deselected** (49.30s), después de las correcciones de auditoría.
Los avisos deprecación de Python3.14
proceden de Pika/FastAPI/SQLite; no hubo fallos de aserción.

Los temporales de pytest bajo Python3.14 fallaron en sandbox Windows por ACL antes de las
aserciones. Los intentos cancelados no cuentan como pruebas. La ejecución
verificable usa directorios dedicados y permiso fuera de ese sandbox. También
se desactiva autoload de plugins globales ajenos al proyecto, que demoraba los
imports. No se modifican conftest, dependencias del proyecto ni políticas para
forzar un resultado.

Desde la raíz:

```text
node tools/jup-check.mjs --all
node tools/jup-cleanup-check.mjs
node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs
openspec validate --all --strict --no-interactive
python -m compileall -q apps/backend/app
git diff --check
```

Traces JUP9/9; OpenSpec56/56; políticas PR/gobernanza70/70 y CI12/12;
higiene y compileall correctos. Node requirió ejecución con procesos hijos
permitidos. Se reutilizó yaml2.9.0 en node_modules propio; ningún cambio de
lockfile. No se ejecutó build frontend porque no cambia código frontend.

## Compatibilidad con productores locales

```text
python scripts/validate_savings_producers.py --recommendations-root <copia-JUP033> --impact-root <copia-JUP034>
```

El script opt-in importa únicamente las funciones de las copias confiadas
indicadas. No convierte esas copias en dependencias runtime o de CI.
[Resultado y SHA-256 de los cuatro archivos productores](JUP-039-producer-smoke.json).
Dos ejecuciones correctas con los mismos hashes: temporal inicial y script
versionado. Recomendaciones y evidence IDs los generó033;034 calculó escenarios
sintéticos. Caso0.006+0.006 conserva filas mensuales0.01 y total original0.01,
sin convertirlo en0.02 al sumar cifras redondeadas; anual0.07 por fila y0.14
original. Se conservan null y la validación de costes emparejados.

Esto acredita compatibilidad local de funciones y serialización en esas versiones,
no autenticación de los productores, persistencia, APIs, Azure, CockroachDB,
stack Docker, sesión de navegador, usuarios piloto ni integración desplegada.
El proveedor033 no incluye tenant_id: su loader servidor debe garantizar el
aislamiento; el consumidor no puede acreditar ese aislamiento a partir del hash.

## Participación y pendientes

Roles asignados conservados: Paris liderazgo, Victor pairing, Alejandro revisión,
Lucia validación. La cuenta GitHub consultada es Iber1to, con autor Git Alejandro.
Esta es una contribución técnica en rama propia para el responsable; no es una
review independiente de Alejandro ni reassignment implícito de liderazgo.
El equipo debe resolver adopción y revisión independiente antes de readiness.
No coautoría, pairing, reviews humanas, aceptación ni ahorro realizado inventados.

Pendientes concretos: integrar loaders033/034 autoritativos, acordar escenarios
con scopes atómicos y fuentes verificables, probar el runtime conjunto, obtener
participación/reviews y archivar OpenSpec antes de abrir revisión formal.
Sin merge, cierre/movimiento de tarjeta, Discord o archivo del chat.
