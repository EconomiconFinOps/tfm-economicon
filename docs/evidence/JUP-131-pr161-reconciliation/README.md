# PR161 — reconciliación con la versión aprobada

25/10/2026. Base aprobada: `0edd11eff3458683553bd4c36f3011b77c1d3de4`.
Candidato de revisión: `812697387918c25e905a240fa35573091d9fdc16`.
Cuenta destino única: `323188184300`, Irlanda/París. Sin merge ni despliegue AWS.

- [Aceptación offline](application-acceptance.md): CI completa del árbol de
  aplicación, PostgreSQL/Atlas y Grafana reales en contenedores de GitHub,
  resultados, omisiones y límites. Nueva huella de aplicación en la receta.
- [Revisión independiente](revision.md) y [validación independiente](validacion.md):
  dictámenes de los agentes autorizados, con hallazgos y revalidaciones.
- `revision.json`, `validacion.json` y `manifest.json`: atribución, candidato
  común y SHA256 de los documentos. No son reviews de cuentas humanas.
- [Informes del 24/10](../JUP-131-pr161-agents/README.md): histórico conservado;
  el arreglo mutable de ApiError de aquel corte fue sustituido por el pin
  aprobado Starlette 1.9.0 y la restauración de ApiError congelado.

El coordinador sólo publica los informes recibidos y genera el manifiesto;
no convierte hallazgos negativos en aprobaciones. `JUP reviews` verifica el
candidato, las huellas, las identidades atribuidas y el alcance exclusivo de
PR161. Los cambios de código posteriores exigen revalidación de ambos agentes.
La política general y las solicitudes de cambios de GitHub siguen vigentes.

Pruebas adicionales del coordinador: Azure 81 PASS; controlador offline
83 PASS/7 SKIP (las integraciones opt-in tienen job propio); Terraform mock
14+1 PASS; política 111 PASS tras dos correcciones de ambigüedad declarativa;
workflow/workspace 21 PASS; edge 8 PASS; landing local 35 PASS/1 SKIP por symlink.
Linux ejecuta la batería de landing completa. No hubo llamadas ni mutaciones AWS.

La CI de publicación final se consulta en
[PR161](https://github.com/EconomiconFinOps/tfm-economicon/pull/161/checks);
recibo local `.work/pr161-reconciliation/final-ci-status.json`. La configuración
local, las dos solicitudes y sus hashes quedan en `.work/master-rehearsal/`.
El check técnico verde no sustituye la integración y CI push exacta de develop,
la ventana UTC ni la autorización del ensayo.
