# Evidencia JUP-119 — datos de demo por una sola ruta y fecha de referencia

Tarjeta: [JUP-119](https://trello.com/c/HtjtmPaJ). Change: `jup-119-coherent-cost-data-reference-date`. Rama: `feat/JUP-119-coherent-cost-data-reference-date`. Decisión: [ADR-0021](../adr/ADR-0021-demo-cost-data-single-path-and-reference-date.md). Contrato de la fecha: [reference-date.md](../api/reference-date.md). Guías: [docs/demo/JUP-107/](../demo/JUP-107/preparacion.md).

Validación hecha por la líder de la tarjeta bajo la excepción temporal del 2026-10-11. No sustituye la revisión ni la validación de las personas con esos roles en Trello. Fechas de ejecución: 2026-10-13, en Windows con Docker Desktop.

## Criterios de la tarjeta

| Criterio | Evidencia |
| --- | --- |
| Una sola vía de carga, con la misma estructura. | `scripts/demo_dataset.py` genera el CSV en formato de exportación de Azure; la segunda API simulada (`azure-cost-api-demo`, perfil `demo`) lo sirve y `scripts/demo_data.py` lo carga con la ingesta del processor, sin insertar filas. `scripts/synthetic_costs.py` y `synthetic_anomalies.py` ya no existen. Prueba extremo a extremo con CockroachDB real (`apps/processor/tests/test_demo_data_end_to_end.py`): los totales por tenant, mes, moneda, servicio y proyecto guardados son idénticos a los recalculados del CSV con `Decimal`, incluido `9007199254740993`. |
| Carga repetida sin duplicados. | La misma prueba: un segundo `apply` responde `already-present` y las cuentas de ingestas y registros no cambian; `remove` dos veces deja 0 y un tenant con costes ajenos hace que `apply` se niegue con código 2 sin escribir. 14 pruebas con almacén simulado (`test_demo_data.py`). En el stack real: `status` `absent` → `apply` (`loaded: 7 parejas...`) → `status` `present`; `remove` imprimió `Retirados 7 ingestas, 1370 registros y 5 episodios de anomalia derivados de ellos.`, el segundo `remove` 0/0/0 y volver a cargar dejó `present`. |
| Cobertura continua hasta el 30/10/2026. | Ventana común del 1/7 al 30/10/2026; `test_demo_dataset.py` (26 pruebas) comprueba un registro por día y tenant, nada fuera de la ventana, el hueco distinguible del cero registrado en dólares y que los ficheros versionados son idénticos a los regenerados. |
| Con la fecha fijada a un día concreto, ninguna pantalla ni respuesta del asistente muestra datos posteriores. | Backend con CockroachDB real (`test_reference_date_costs.py`, 12 pruebas; cuatro mutantes del tope, todos muertos): resumen, cobertura de etiquetas, presupuesto, consulta de prueba de anomalías, lectura diaria de la detección y pregunta de responsables no incluyen registros posteriores; periodo entero en el futuro igual a periodo sin datos. Episodios (`test_reference_date_episodes.py`, 4 pruebas; tres mutantes muertos): ocultos al retroceder la fecha y visibles al avanzarla. Frontend (8 pruebas nuevas, 887 en total) y navegador real con la referencia en 2026-10-30. |
| Documentado qué es público desplazado y qué es sintético. | Manifiestos por conjunto (`derived/manifest.json`, `demo/manifest.json`), [guía de datos](../data/azure-sample-dataset.md), README y guion de la demo; el aviso precede a la primera cifra (D1) y lo comprueba una prueba. |
| Decisión de diseño registrada, con su impacto en el ADR-0001. | ADR-0021 (alternativas descartadas, dos agrupaciones, casos raros a pruebas, fecha de referencia, episodios ocultos al retroceder). |

## Sondeo y mediciones

- Sondeo con CockroachDB real (nodo desechable): cruzan cero, crédito, dos monedas y servicio o grupo ausentes; no cruza el importe con céntimos por encima de 2^53 (`9007199254740993.01` llega como `9007199254740994`, la API devuelve en coma flotante lo que no es entero) ni las cuatro dimensiones (la API agrupa por dos como mucho); rechaza `dataset_origin` y una fila sin fecha. Un entero grande sin céntimos cruza exacto por la API, el cliente y el normalizador.
- Una primera medida de 133 s por llamada de la CLI era un artefacto de usar `localhost` en el DSN en Windows (espera de IPv6 hasta agotar el tiempo de conexión); con `127.0.0.1`, `initialize()` tarda 2,6 s en una base nueva y 0,4 s ya migrada. Carga completa de las 7 parejas: 23,9 s (siete llamadas a la CLI).

## Comprobación contra el stack real

Stack aislado `docker compose -p jup119` con volúmenes nuevos, `.env` de siempre y `COST_REFERENCE_DATE=2026-10-30` solo por línea de comandos; Chromium 1243 y Playwright 1.63.0 fuera del repositorio.

- El `up` normal no cargó datos. `demo_data.py apply` por el perfil `demo` cargó las 7 parejas.
- `resumen.py` de la guía: Growth Ops `data_status: partial`, `EUR 61580.74 370`, `USD 0.87 70`; Core Finance `data_status: available`, `EUR 79337.00 569` (coinciden con la guía).
- Receta de navegador: **12 pasos `pass`** (D1 a D12: cabecera «Fecha simulada: 30/10/2026», aviso sintético sin importes antes de la declaración, totales, desglose, hueco del gráfico con 2 puntos para 3 meses, comparación EUR +2351.54 / +12.12 %, «Comparación no disponible» en USD, etiqueta `project`, aviso de datos parciales, aislamiento entre clientes, detección con Compute «Alta (P1)» y «Revisado hasta el 29/10/2026», importe `9007199254741837.50`). Control positivo: con `F03` alterada la receta falla en D3 con «F03: falta la fila Compute EUR 28099.21 (92)» y deja el resto en `not_run`.
- Tres pantallas con campos ausentes, vistas en la interfaz real sin errores de página ni de red: cobertura de etiquetas «Cumple: 0.00 % · No cumple: 100.00 %» (0 de 370 registros cumplen); responsables por centro de coste «Datos insuficientes: ningún registro de la selección tiene centro de coste», con «Periodo UTC: 2026-10-01 a 2026-11-01» y «Fecha de referencia: 2026-10-30»; desglose por grupo de recursos todo «Sin dimensión», por suscripción, con «Datos parciales: 440 registros sin dimensión».
- Hallazgos del ensayo: Git Bash convierte `/repo/...` en una ruta de Windows (el cargador usa `working_dir: /repo`); el CockroachDB del stack se detuvo solo una vez con «disk slowness detected» por el disco lento de Docker Desktop de esta máquina (`RF-119-008`); el aviso «Datos sintéticos de demostración» del panel de anomalías dependía de una marca que la ingesta no pone, y se arregló en el backend con su prueba. El stack se paró con `down -v`.

## Pruebas automáticas

- Backend con CockroachDB real (nodo desechable en memoria, `127.0.0.1`): 1161 pasan y 21 se omiten, sin las cuatro suites de salud del proveedor (`test_health_provider_*_jup047.py` y `test_system_health_jup047.py`), que fallan en esta máquina con `ProactorEventLoop` con o sin estos cambios (el fallo conocido de Windows de JUP-114, `RF-119-004`). En la última ejecución completa (después de la pasada 3 de la revisión) fallaron además 10 pruebas de `test_managed_resolver.py` por un plazo de 3 s al arrancar procesos hijos reales con la máquina cargada; ese fichero no cambia en este change y sus 14 pruebas pasan en solitario y junto a las suites de este change (72 pasan).
- Processor con CockroachDB real: 907 pasan, 40 omitidas y falló una (`test_agent_runtime.py::test_jup023_attempt_deadline_interrupts_trickle[2-body]`, otro plazo de tiempo; el change solo añade un fichero de prueba y las 4 variantes pasan en solitario); API simulada: 81; frontend: 887 pruebas (68 ficheros), `typecheck`, `lint` y `build`; scripts: `demo-dataset:test` (29), `demo-data:test` (22), `synthetic-demo:test` (47); `docker:validate` (36), `local:test` (74), `llm-gateway:test`, `cd:test`, `ci:check:test`, `jup:check:test`, `jup:cleanup:test`, `roadmap:test` y `repository:governance:test`; `corepack pnpm lint`, `openspec:validate` (68 de 68), `jup:check:all`, `jup:cleanup:check` y `git diff --check`.
- La prueba de contrato `test_litellm_docker.py` del processor se omite (no se ejecuta sin el gateway).

## Qué no se validó

- Ensayo humano de la demo: no hay; la receta es una ejecución automatizada.
- La interfaz con una fecha de referencia distinta de 2026-10-30 no se ha recorrido en el navegador real (la guía de anomalías con la referencia en 2026-09-21); lo cubren las pruebas del backend con CockroachDB real y las del frontend.
- El arranque por el perfil `demo` en un entorno que no sea esta máquina (Linux) y el tiempo de carga fuera de ella.
- Las cuatro suites de salud del proveedor y el servicio de carga diaria o el batch periódico (fuera de alcance, JUP-115).
- Revisión, validación y aprobación de otras personas: se siguen en Trello.
