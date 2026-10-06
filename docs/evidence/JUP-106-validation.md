# JUP-106 — evidencia de validación local

Fecha: 06/10/2026. Rama `feat/JUP-106-synthetic-cost-data` sobre develop `f0cacdd`. [Tarjeta](https://trello.com/c/JwumJnIf). Datos sintéticos de coste para validar la funcionalidad de costes; la guía de uso y los valores esperados están en [docs/validation/JUP-106-synthetic-costs.md](../validation/JUP-106-synthetic-costs.md) y el change en [openspec/changes/jup-106-synthetic-cost-data](../../openspec/changes/jup-106-synthetic-cost-data/review.md). Estos resultados son del autor del cambio y no sustituyen las reviews `Revision JUP-106` y `Validacion JUP-106` de los responsables.

## Alcance comprobado

Una herramienta (`scripts/synthetic_costs.py`) que carga, consulta y retira un conjunto determinista de diez registros y dos ingestas completadas (2026, EUR y USD, con un cero registrado, un crédito, un importe por encima de `Number.MAX_SAFE_INTEGER`, un registro sin dimensiones y otro sin fecha) en las tablas de costes de `tenant-growth`. No cambia `apps/`, migraciones, el simulador ni el dataset público.

## Pruebas, mutantes y adversarial

| Comprobación | Resultado |
| --- | --- |
| `corepack pnpm synthetic-costs:test`, Python 3.12, sin base de datos | 45 correctas, 8 omitidas (las de CockroachDB) |
| Mismas pruebas con CockroachDB v24.1.11 real y desechable (`JUP086_COCKROACH_TEST_URL`) | 45 de 45, unos 115 s por las migraciones |
| Rojo inicial | falló por la ausencia de la herramienta; las pruebas de los hallazgos de la adversarial fallaron antes de corregirlos (tenant con salto de línea, carrera, retirada con registros reales colgando) |
| Mutantes de lógica (25 en la primera ronda) | 22 detectados y 3 supervivientes (estado con `or`, `created_at` del reloj, tenant ajeno solo en registros), cerrados con pruebas nuevas; 25 de 25 tras ello |
| Mutantes de SQL con CockroachDB real | 5 primero y 2 supervivientes cerrados con pruebas nuevas; 7 de 7 tras ello; control positivo con un mutante identidad |
| Mutantes sobre el código añadido tras la adversarial (14) | 12 detectados; 2 viven en `SqlStore` y solo los detecta la prueba con SQL real, que detectó sus equivalentes |
| Revisión adversarial independiente | accept, sin BLOCKING ni HIGH; 3 MEDIUM y 1 LOW corregidos con prueba, 1 LOW de pruebas corregido, 2 LOW sin cambios (ver review.md) |
| Barrido del patrón `^...$` con `re.match` | sin otros casos; los validadores vecinos usan `fullmatch` |

Dos defectos de la herramienta los destapó la propia prueba contra SQL real, antes de la adversarial: un registro con el prefijo reservado se consideraba sintético aunque su ingesta no lo fuera, y la comparación `request->>'synthetic' = 'true'` daba NULL con `request = '{}'` y dejaba la fila sin contar. Ambos están corregidos.

## Extremo a extremo (stack aislado, proyecto `jup106`)

`docker compose -p jup106 build` y `up -d --wait` con nueve servicios sanos; la herramienta se ejecutó dentro del contenedor del processor con `python - <comando> < scripts/synthetic_costs.py`.

| Paso | Resultado |
| --- | --- |
| `status` antes | `absent`, sin datos reales |
| `apply` | `loaded`: 2 ingestas y 10 registros; ambas `completed` en CockroachDB |
| `apply` otra vez | `already-present`, sin escrituras |
| `/billing/summary` de `tenant-growth` (script contra la API real, 12 comprobaciones) | los siete meses por separado, enero a julio, cada agrupación (suscripción, servicio, grupo de recursos, proyecto y etiqueta `cost_center`), el recuento de registros sin fecha y sin dimensión, y `tenant-core` sin datos: todas coinciden con los valores esperados del documento |
| Recorrido del dashboard de develop con Playwright (Chromium 1440×900, una vez) | `Coste total del periodo` con 90,00 EUR y 9007199254741028,76 USD, desgloses por suscripción, servicio y grupo de recursos, marzo con «Sin datos de costes», febrero con 0,00 EUR y 10,50 USD, y `Core Finance` sin datos; mismos importes que la API |
| `remove` | 2 ingestas y 10 registros; `tenant-core` conserva sus 38 registros y su ingesta |
| `remove` otra vez | 0 y 0, salida 0 |
| `apply` tras retirar y `remove` | `loaded` y después retirada completa |
| Ingesta del dataset público en `tenant-growth` y `apply` | `refused`, salida 2; `remove` retira 0 y las 38 filas reales de cada tenant siguen |
| Limpieza | `docker compose -p jup106 down -v`, contenedor desechable eliminado y copia de `.env` borrada |

Las capturas del recorrido están en una carpeta local del autor (`D:\p106-evidence`) y no se versionan.

## Comprobaciones generales

`corepack pnpm openspec:validate` 47 de 47; `jup:check` del change y `jup:check:all`; `jup:cleanup:check` (840 archivos); `ci-workflow` y `repository-governance` 25 de 25, con un control negativo (quitando el paso de `ci.yml`, el test falla); `assistant-metrics:test`; `git diff --check origin/develop...HEAD` limpio; enlaces del documento comprobados.

## No validado

- Python 3.10 y 3.11 (se ejecutó con 3.12); la tubería de PowerShell (la fuente es ASCII, pero no se probó el comando de PowerShell).
- Una ingesta real del processor en paralelo con `apply` (la carrera se probó con una inserción equivalente, también contra CockroachDB real).
- Que la prueba contra CockroachDB real corra en CI: no corre, como el resto de las que necesitan servicios.
- La comparación entre meses y el gráfico de serie: el dashboard de develop no los tiene (son de JUP-055), así que no se recorrieron.
- La ingesta y el simulador, que este cambio no ejercita.

## Pendiente en Trello

Revisión y validación de los responsables de la tarjeta sobre el PR, y validar la #77 (JUP-055) con estos datos.
