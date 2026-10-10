# Validación local de la plantilla Terraform

Fecha: 10/10/2026. Entregable: JUP-060, arquitectura documental AWS.

Revalidado al incorporarlo a `infra/aws-reference` en la PR92 el mismo día:
fmt, validate, seis runs mock y ocho rutas correctos desde la ubicación versionada.
Se reutilizó el proveedor previamente descargado mediante `-plugin-dir` y
`-lockfile=readonly`, con `TF_DATA_DIR` fuera del repositorio. La instalación
local informa `unauthenticated` porque no consulta de nuevo la firma del registro;
el paquete de origen fue verificado en la descarga inicial y se conserva el lockfile.

Entorno de comprobación: Windows, Terraform 1.13.3, proveedor hashicorp/aws 6.13.0 y Node.js 24.14.1. Terraform se descargó de releases.hashicorp.com y se contrastó el SHA-256 del ZIP con el fichero oficial de checksums. `terraform init -backend=false -input=false` instaló el proveedor firmado por HashiCorp y generó `.terraform.lock.hcl`.

| Comprobación | Resultado |
| --- | --- |
| `terraform fmt -check -recursive` | Correcto. |
| `terraform validate -no-color` | Configuración válida contra el esquema del proveedor. |
| `terraform test -no-color` | 6 escenarios correctos, 0 fallidos. Proveedores AWS regional y edge simulados. |
| `node tests/edge-functions.test.cjs` | 8 escenarios de rutas correctos. Conservación de headers/query en API y separación de assets/SPA. |

Escenarios Terraform: datos privados/cifrados y aplicaciones desactivadas por defecto; rechazo de activación sin adaptación; NAT único solo mediante opción explícita; rechazo de zonas de otra región; forma del despliegue de las tres aplicaciones con inputs ficticios; rechazo de familia PostgreSQL incompatible.

Se corrigió el uso de claves calculadas de validación ACM en `for_each`, sustituyéndolo por un registro explícito para cada certificado de un único dominio. Las pruebas comprueban también que no se cacheen respuestas ni errores de la API y que S3 mantenga bloqueo público. El dominio Cognito normaliza el identificador del pool a caracteres compatibles.

Todos los runs de Terraform tests usan `command = plan` y `mock_provider`. No se ejecutó un plan con proveedor AWS real, `apply`, `destroy`, SQL de bootstrap ni llamadas a Bedrock. No se consultaron cuentas AWS ni credenciales; los fixtures de tests son ficticios.

La validación acredita sintaxis, esquema y las invariantes comprobadas. No acredita funcionamiento cloud, disponibilidad de versiones/región, costes, permisos reales, DNS/TLS emitidos, conectividad, carga, aislamiento funcional del código, migraciones ni compatibilidad Cognito/Bedrock. Los límites están detallados en README.md.
