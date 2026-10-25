# JUP-131 — aceptación offline de la aplicación de PR171

Verificado el25/10/2026 en «Preparar despliegue en AWS», chat
`01a15abb-d5f3-7fd3-a622-ea9e73b0db18`. Cuenta objetivo323188184300.
Esto acredita código y servicios locales desechables; la aceptación AWS de la
generación sigue pendiente.

Candidato ejecutado: `f1f8cca2c9df5712fcac705356a3ad44f501030a`, reconciliado
con develop `8bf61d44e6924ed61af6aae79ceb45797b94fb03` (PR169 y PR170).
Incluye la [afinidad de réplicas](JUP-131-chat-replica-affinity.md) y el dashboard
vigente. ApiError permanece idéntico a0edd11ef y Starlette fijado en1.9.0.
Huella de `application_digest`, idéntica en checkout y archivo limpio del commit:

`4a138a04e79dc34794eab05b07908327af40e2f17ddb2472afc5e7eb07ed8795`

## Verificaciones del candidato

- [CI PR40233382450](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40233382450): SUCCESS, once jobs.
- [CI push40233377430](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40233377430): SUCCESS. Es la rama de trabajo, no develop.
- [SQL nativo40233382359](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40233382359): SUCCESS,54 pruebas backend y8 processor.

| Contrato | Resultado confirmado | Límite |
| --- | --- | --- |
| Backend y Cognito | 2740 PASS,369 SKIP | Integraciones opt-in omitidas; no recorrido público de navegador |
| Processor y Bedrock | 2676 PASS,150 SKIP | SDK/modelos simulados; no inferencia real |
| Frontend | 96 archivos de pruebas PASS, build y tipado correctos | Ejecución en runner |
| PostgreSQL | 45 pruebas pgvector y8 operacionales/Atlas PASS | PostgreSQL16 desechable, no RDS |
| Grafana y Atlas | Job aislado TLS/dashboards/reinicio PASS | Paquete19 runs/1688 resultados; ver límite de evolución abajo |
| Azure | 81 PASS; ApiError y pin Starlette conservados | API simulada |
| Gobierno, control y topología | OpenSpec, JUP policy, AWS demo offline y landing SUCCESS | JUP reviews exige todavía reviews humanas o excepción específica |

Éxito con avisos: backend19569, processor2388, Azure1; no se ocultan los SKIP.
La suite local específica de afinidad/resúmenes pasó89/89. La revisión técnica
independiente del código es favorable y la revalidación de integración añadió
22 pruebas offline propias. No constituye aprobación humana de integración.
Logs públicos guardados en `.work/master-rehearsal/pr171-ci-f1f8.log` y
`pr171-sql-f1f8.log`; huella en `pr171-application-tree.json`.

## Límite de los nuevos paneles de evolución

PR169 incorpora dos proyecciones adicionales en el manifiesto general y los
paneles8401–8403. El paquete Atlas para AWS conserva19 runs/1688 resultados y
no contiene ese suplemento; esos paneles quedan sin esas filas en un bootstrap
limpio, como explica el panel8400. Se conserva el conjunto original verificado.
No se presenta la nueva evolución como cargada ni se añade una carga cloud
fuera de la receta del ensayo. El informe de integración registra este límite.

## Vinculación con la receta

`infra/aws-cicd/release.json` conserva los recibos anteriores, añade éste y
actualiza la huella de aplicación. Los cambios posteriores de receta/evidencia
no alteran los bytes de apps ya ejecutados. El ensayo3 permanece ligado a su
fuente anterior y se está retirando; no se cambia su configuración inmutable.
Antes de ensayo4 son necesarios integración autorizada, CI develop SUCCESS del
SHA exacto, cierre del ciclo previo, preflight vigente y preparación con nueva
caducidad. La aceptación funcional real y retirada seguirán ejecutándose en AWS;
esta actualización documental no las sustituye ni declara READY.
