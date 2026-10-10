# Forecasting de gasto Azure — JUP-031

Verificado el 10/10/2026. Origen: encargo «Implementa JUP-031 — Generar forecasting
de gasto Azure», delegado desde el chat `01a1248a-4e9e-7963-a891-5d8cb49345a6`.

## Alcance y decisiones

[Tarjeta](https://trello.com/c/uV9ywMry), id `69da3f88bac54030dcc58518`, P1 Valor
FinOps. Lectura oficial DockerServer confirma descripción/roles sin cambios desde
el snapshot `materiales/07-evidencias/hito-mvp-2026-10-09/backlog-dispatch-source.json`.
Paris liderazgo, Victor pairing, Alejandro revisión y Lucia validación; no atribuir
participación o aceptación sin evidencia. No había PR/rama031 previa.

Worktree propio `tfm-economicon-jup031`, rama `feat/JUP-031-forecast`, base
`c2995a1` (`origin/develop`). API autenticada `GET /billing/forecast`, agrupaciones
suscripción/servicio/proyecto, historia mensual hasta24 meses y horizonte1–3.
Lector SQL sólo ingestas completas del tenant, protección de fuentes ambiguas,
monedas separadas y project tipado/tag. Servicio compara referencia último mes
con tendencia lineal en tres cortes temporales; exige9–11 meses según horizonte.
Ausencias no son cero. Límites empíricos sin cobertura estadística prometida.

No tocar JUP-030/anomalías, frontend o run rate. La muestra pública de junio2024
no tiene historia suficiente; fixtures largas sólo sintéticas. Observaciones
mensuales no garantizan cobertura de facturación; advertencia explícita en API.

## Evidencia y próximos pasos

[Runbook](../runbooks/azure-spend-forecast.md), [evidencia por criterio](../validation/JUP-031.md)
y [OpenSpec](../../openspec/changes/jup-031-azure-spend-forecast/design.md).
64 pruebas específicas aprobadas:16 cálculo,34 API (lector doble explícito),
14 lector/SQL (10 SQL reales y4 guardas), incluidas12 observaciones SQL→forecast.
OpenSpec56/56,70 pruebas PR/gobierno+12CI correctas; regresión costes/tenants79pass
11skip y build4/4 sin caché. Globaltest: Azure59pass; processor445pass57skip3fail
fuera del delta (dos timing pendientes y JSONprofundo aceptado enPython3.14,
reproducción confirmada). Backend/frontend global interrumpidos porTurbo;
no declarar suite total verde. Base temporalSQL y túnel retirados. Publicador
Iber1to/identidad GitAlejandro coincide con revisor asignado: entrega en borrador
para Paris, con independencia de revisión por resolver sin reasignar por inferencia.
[PR103](https://github.com/EconomiconFinOps/tfm-economicon/pull/103) publicada
en borrador contra develop; implementación `8675c7ad1f67361e77d0dd40f172d95b301319ad`.
NotaTrello `6ac9ee311832e0c3b92c81c8` publicada por el puente oficial y releída:
lista y descripción intactas. Logs/caché local de las ejecuciones generales
conservados en `../materiales/07-evidencias/JUP-031-implementacion-2026-10-10/turbo-cache`
respecto a la raíz del checkout. Temporales pytest propios retirados.
CI38035592277 de implementación8675c7a: los siete checks policy/OpenSpec/Python3
servicios/frontendbuild/typecheck SUCCESS. Processor pasa en workflowPython3.12;
los tres fallos locales3.14 siguen documentados, sin atribuir causas de timing
como demostradas. JUP reviews FAILURE por dictámenes pendientes.
Review/validación/pairing/aceptación humanas pendientes. Sin merge, cierre o Discord.
