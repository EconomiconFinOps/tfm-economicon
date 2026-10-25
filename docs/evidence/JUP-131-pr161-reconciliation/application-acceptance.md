# JUP-131 — aceptación offline del árbol reconciliado

Verificado el 25/10/2026, «Preparar despliegue en AWS», chat
`01a15abb-d5f3-7fd3-a622-ea9e73b0db18`. Alcance: código preparado para el ensayo
de la cuenta del máster `323188184300`; no acredita despliegue ni runtime AWS.

Base de aplicación aprobada: `0edd11eff3458683553bd4c36f3011b77c1d3de4`.
Candidato ejecutado por CI: `da13f069c0f92258bb2856ff33b204cc3b176e89`.
Huella calculada mediante `tools.aws_demo.control.application_digest`:

`5e19f3f4ff0db6039ebc42b2733d9dd4266e94b55c6fc8fac741c21876461e70`

Esta huella incluye Atlas/ECS y el contenido aprobado de PR162. Los deltas
posteriores `bfffb88b` y `964c9f55` sólo cambian la política de declaración de
PR161 y sus pruebas: `git diff da13f069 964c9f55 -- apps` está vacío.
`ApiError`, sus pruebas y requirements son idénticos a la base aprobada;
Starlette sigue fijado en 1.9.0. El digest anterior de la receta corresponde
a otra aplicación y queda sustituido, sin reinterpretar los informes históricos.

## Ejecuciones remotas comprobadas

- [CI de PR](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40187165537):
  **SUCCESS**, los once jobs completos sobre `da13f069`.
- [CI push de la rama](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40187163124):
  **SUCCESS**, mismo candidato. No es una ejecución push de `develop`.
- [SQL nativo](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40187165282):
  **SUCCESS**, backend 54 PASS y processor 8 PASS, sin inferencias.

| Contrato | Evidencia actual | Límites |
| --- | --- | --- |
| Aplicación y Cognito/PKCE | Backend 2732 PASS/369 SKIP; frontend 1427 PASS en 96 archivos, build y tipado correctos | Cognito/JWKS y transporte con fixtures; no login AWS real. Omisiones de integraciones opt-in no contadas como PASS |
| Bedrock y processor | Processor 2674 PASS/150 SKIP, incluidos adaptadores nativos y guardas de protocolo | SDK simulado; sin inferencias, permisos de cuenta ni calidad de salida real |
| PostgreSQL, embeddings y fixtures | Job `AWS PostgreSQL application`: 45 pruebas pgvector PASS y 8 pruebas operacionales/Atlas PASS en PostgreSQL 16 desechable | Inferencia simulada, bases reales locales del runner; no RDS AWS |
| Atlas y Grafana | Job `AWS monitoring isolated` PASS: 19 ejecuciones/1688 resultados, tres dashboards, datasources TLS sanas, acceso anónimo rechazado, sesión permitida y origen ajeno denegado, preferencias conservadas tras reinicio | Contenedores desechables en GitHub; no endpoints públicos ni ECS real |
| Azure | 81 PASS con Starlette 1.9.0 y ApiError congelado | API simulada; 1 aviso de deprecación del TestClient |
| Control y topología | 83 PASS/7 SKIP offline; 14 mocks Terraform de referencia + 1 de bootstrap PASS; OpenSpec SUCCESS | Los 7 controles de PostgreSQL opt-in se ejecutan en el job real separado. Terraform no aplica recursos |
| Landing | `Landing static checks` SUCCESS en Linux; carrusel y viñetas de PR162 conservados | No publica la landing ni cambia su hosting |

Los logs también registran avisos: backend 19571, processor 2388, SQL backend
88 y pgvector 1. Son ejecuciones exitosas con avisos, no resultados sin avisos.
Los resultados exactos y sus contextos se pueden consultar en los jobs enlazados.
Copias locales de logs: `.work/pr161-reconciliation/ci-40187165537.log` y
`sql-40187165282.log`; no contienen credenciales añadidas por esta preparación.

## Relación con la receta y siguiente fase

La receta conserva las cinco evidencias técnicas históricas y añade este recibo
con su SHA256. Sólo se renueva la aceptación **offline del código** identificado
por la huella. Los informes independientes de la reconciliación se publican al
cierre y deben corresponder al candidato que contiene esta actualización.

No se han construido/publicado aquí las imágenes finales de release, consultado
AWS ni ejecutado modelos. El runner conserva sus fases de build, preflight de
cuenta/cuota/modelos, controles de plan, aprobación humana, bootstrap y checker
funcional real. `application_ready` no se obtiene por cambiar la receta.
Antes del ensayo siguen siendo necesarios integración autorizada, CI push
SUCCESS del SHA exacto de `develop`, ventana UTC vigente y autorización del
ensayo. El generador local debe seguir marcando esos campos pendientes.
