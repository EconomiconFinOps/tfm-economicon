# JUP-046 — Evidencia técnica de alertas LLM

Fecha: 2026-10-10. [Tarjeta](https://trello.com/c/R6CVFCif).
Base: `c2995a118d419dfe725247bac9c6f219a3f0ea77` (`origin/develop`).
Rama propia: `feat/JUP-046-llm-alerts`. Contribución técnica para liderazgo;
no sustituye los dictámenes humanos `Revision JUP-046` y `Validacion JUP-046`.
[PR #105 en borrador](https://github.com/EconomiconFinOps/tfm-economicon/pull/105),
contra develop, implementación `c980ba2e9b20812c9227cfcbcf1d9814b6a1ebf0`.
La publicación del comentario de entrega en Trello fue rechazada por la revisión
automática antes de ejecutarse: exige autorización específica del contenido y
destino. No se publicó ningún comentario; el enlace operativo queda pendiente.

## Evidencia por criterio original

| Criterio Trello | Resultado técnico | Límite / pendiente |
| --- | --- | --- |
| Resultado funcional verificable | Métricas de operaciones LiteLLM completas, tres reglas Grafana y panel; errores/latencia, muestra mínima y recuperación verificables con dobles y motor real PromQL. | Sin llamadas a un modelo real ni calidad semántica certificada. |
| Pruebas necesarias añadidas y en verde | Linux: processor 466 pass / 57 skip; backend 910 pass / 34 skip. Node comprueba provisioning y extracción; promtool 2.55.1 pasa 19 escenarios. | Windows presenta discrepancias detalladas abajo; integraciones opt-in omitidas explícitamente. |
| Documentación y decisiones actualizadas | OpenSpec, runbook, convenciones Python y continuidad. | Política inicial de umbrales pendiente de confirmación operativa. |
| Pull request revisado y vinculado | PR #105 en borrador publicada en rama propia contra develop, para adopción de liderazgo. | Dictámenes humanos pendientes, no criterio aceptado. |
| Validación funcional y evidencia enlazadas | Evidencia técnica sintética aquí; reproduce errores, umbrales y recuperación. | Validación funcional independiente de Alejandro y enlace operativo pendientes; no criterio aceptado. |

## Métodos y resultados

Python 3.14.4 / Windows y **Python 3.12.13 / Linux**; Node 24.14.1,
packageManager pnpm 9.0.0, OpenSpec 1.8.0.
Instalación con `corepack pnpm install --frozen-lockfile --ignore-scripts`; lockfile intacto.

- Linux processor: `python -m pytest tests -q -p no:cacheprovider`, **466 pass /
  57 skip**, 12.01s; backend **910 pass / 34 skip**, 122.63s. Fuentes propias
  montadas sólo lectura, contenedores sin red, pytest 9.1.1, métricas nuevas incluidas.
  [Recibo y versiones](JUP-046-linux-tests.json).
- Windows processor: primera ejecución focal 52 pass / 1 fail. Suite completa:
  **460 pass / 57 skip / 6 fail**, 733.39s. Fallan las cuatro variantes de
  `test_jup023_attempt_deadline_interrupts_trickle`, `test_jup023_attempt_deadline_accepts_complete_response`
  y `test_json_depth_error_is_discarded_once_then_next_delivery_is_returned`.
  Son pruebas existentes; todas pasan en Linux sobre el mismo código de aplicación.
  No se alteró el transporte, la cola ni se relajaron umbrales. La atribución a
  carga/versión de Python es una hipótesis, no un diagnóstico aislado completo.
- Windows backend focal: **63/63** antes de inicialización de categorías y **12/12**
  después, con todos los casos nuevos. Suite completa interrumpida tras 61% y
  fallos sin resumen/traceback utilizable; no se declara verde ni causa confirmada.
- Node: **87/87** controles finales de alertas, política PR, CI y gobernanza,
  incluido el paso promtool. Higiene: **6/6** tests y **993** archivos correctos.
- `corepack pnpm jup:check:all`: 9 cambios correctos.
- `corepack pnpm openspec:validate`: 56/56 correctos.
- `python -m compileall -q apps/backend/app apps/processor/app`: correcto.
- `git diff --check`: correcto.

PromQL se ejecutó con la imagen ya disponible `prom/prometheus:v2.55.1` en
DockerServer. Comandos, desde directorio temporal con reglas extraídas:

```sh
node tools/llm-alerts-promtool.mjs --prepare <directorio-temporal>
docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,size=128m \
  -v <directorio-temporal>:/work:ro -w /work --entrypoint /bin/promtool \
  prom/prometheus:v2.55.1 test rules llm-tests.yml
```

Resultado **SUCCESS**, 19 escenarios. Incluyen igualdad de umbrales, volumen mínimo,
error aislado, persistencia 2m, recuperación con datos frescos, reset, series ausentes,
tráfico parado e independencia entre job/instance/operation. La regla y su condición
se extraen del mismo YAML de Grafana; no se prueba una implementación alternativa
de PromQL. El primer intento sin tmpfs falló por filesystem de sólo lectura; se
corrigió el entorno de prueba y el comando de CI, no las expresiones.
`promtool check rules`: **3 reglas válidas**. [Versión y huellas](JUP-046-promtool.json).

Grafana **11.3.0**, commit `d9455ff7db73b694db7d412e49a68bec767f2b5a`:
contenedor aislado `--network none`, sin puertos ni receptores, provisioning real.
`/api/health` correcto. El smoke comprueba carga de reglas y dashboard; ejecución
de reglas desactivada para aislamiento. Las transiciones se prueban con promtool,
no se declaran verificadas visualmente en Grafana. Enlace de runbook absoluto al
repositorio canónico; estará disponible en develop después de integrar.
[Recibo del smoke](JUP-046-grafana-smoke.json), con consultas/condiciones iguales a
las fuentes; sólo precede a la corrección posterior del enlace de runbook.

El primer intento Linux processor tuvo seis fallos por `jwt` ausente en su imagen
de producción al ejecutar tests que importan backend. Se aportaron PyJWT 2.13.0,
email-validator 2.3.0 y dnspython 2.8.0 desde la imagen backend existente a un
directorio de dependencias de prueba de sólo lectura. La suite completa pasó al
completar ese entorno; código y tests no se modificaron para resolverlo.

## Revisión interna y límites

Revisión técnica auxiliar detectó inicialización tardía de categorías que ocultaba
la primera ráfaga de un error nuevo, y enlace relativo de runbook no navegable desde
Grafana. Ambos se corrigieron con regresión; no es revisión humana atribuida al equipo.

Algunos comandos iniciales fallaron por permisos de temporales/subprocesos del
sandbox (pytest y Node EPERM); se repitieron fuera del sandbox y con temporales
propios. Estos fallos no se cuentan como defectos resueltos del producto.

No llamadas reales a LiteLLM/OpenRouter, alertas a Discord, despliegue del stack,
gasto ni tráfico de producción. Mock/falta de clave/health probes no se convierten
en degradación. Normal sin muestra suficiente no acredita salud. `NoData`/`Error`
tienen semántica separada; la primera muestra no reconstruye eventos previos.
Worker/API separados y múltiples procesos necesitan exposición adicional; el
contrato probado corresponde al runtime combinado existente. Evaluación JUP-067/070,
trazas existentes y salud JUP-047 siguen siendo señales complementarias.
