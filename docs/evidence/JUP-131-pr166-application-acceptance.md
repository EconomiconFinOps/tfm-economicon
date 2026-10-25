# JUP-131 — aceptación offline del candidato integrado de PR166

Verificado el 25/10/2026 en «Preparar despliegue en AWS», chat
`01a15abb-d5f3-7fd3-a622-ea9e73b0db18`. Cuenta objetivo del máster:
`323188184300`. Esto acredita código y servicios locales desechables, no un
despliegue satisfactorio en AWS ni calidad generativa con Bedrock.

Candidato ejecutado: `1fb78d609555e51a5353c1f541b6a520046fff0a`, incorpora
`develop`/PR164 `390721f92d60d29358de62e9cebf99ee028190a2`. Su única modificación
adicional dentro de `apps/` es la fixture de presupuesto de contexto descrita
en [la evidencia de PR166](JUP-131-rds-parameter-drift.md). Código de aplicación
idéntico a esa base; `ApiError` idéntico a `0edd11ef`, Starlette fijado en 1.9.0.

Huella `tools.aws_demo.control.application_digest`, confirmada tanto en el
checkout como en un archivo limpio generado con `git archive` del candidato:

`3c2a471c9cb35ddafaa8d9a956361f18da5dda53a6e4cb58a1223a15ee997479`

## Verificaciones remotas

- [CI de PR](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40209401446):
  SUCCESS, los once jobs completos sobre el candidato integrado.
- [CI push](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40209397897):
  SUCCESS sobre el mismo SHA. No es un push de develop.
- [SQL nativo](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40209401487):
  SUCCESS, backend 54 PASS y processor 8 PASS, sin inferencias.

| Contrato | Resultado confirmado | Límite |
| --- | --- | --- |
| Backend, Cognito y contexto | 2732 PASS, 369 SKIP | Integraciones opt-in omitidas; transportes/JWKS con fixtures |
| Processor y Bedrock | 2676 PASS, 150 SKIP | SDK y generación simulados; no se han invocado modelos |
| Frontend | 96 archivos de pruebas PASS, build y tipado correctos | No acredita recorrido público en AWS |
| PostgreSQL | Job de aplicación PASS, incluidas ocho pruebas operacionales/Atlas | PostgreSQL 16 desechable, no RDS |
| Grafana/Atlas | TLS, tres dashboards, identidades Atlas, denegación anónima y reinicio PASS | Contenedores locales del runner, no ECS público |
| Azure | Job completo PASS; pin Starlette 1.9.0 conservado | API simulada |
| Control y topología | 105 pruebas offline OK, nueve integraciones omitidas; Terraform referencia 14 PASS y bootstrap 1 PASS | Proveedores mock, sin recursos AWS creados |
| Gobierno y landing | OpenSpec 92 PASS, JUP policy y landing SUCCESS | JUP reviews sigue requiriendo dictámenes humanos o excepción expresa |

Backend registra 19587 avisos y processor 2388: éxito con avisos, no una
ejecución sin avisos. Logs públicos guardados en
`.work/master-rehearsal/pr166-ci-1fb78d60.log` y `pr166-sql-1fb78d60.log`.
La revisión independiente del agente `/root/review_aws_build_context` también
es favorable para este SHA; no sustituye revisiones humanas ni concede merge.

## Relación con la receta y siguiente ensayo

`infra/aws-cicd/release.json` conserva las evidencias históricas y añade este
recibo con su hash. Se renueva la aceptación offline de los bytes identificados;
los cambios de receta/documentación posteriores no modifican esos bytes.
El ensayo retirado mantuvo su fuente original `0a36a663` y no usó esta receta.

Antes de otro intento se requiere integración autorizada, CI push verde del SHA
exacto de develop, configuración nueva con ventana UTC vigente y resolución del
paso de Cloud Map. La política actual sigue fallando en creación automática;
no se amplían aquí sus permisos. La recuperación administrativa anterior sí
probó creación/importación y retirada con permiso temporal sobre la zona exacta,
pero no es aceptación de CI/CD completo. `application_ready` requiere todavía
el bootstrap y los checks funcionales reales del runner.
