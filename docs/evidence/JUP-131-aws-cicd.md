# Evidencia de implementación CI/CD AWS — JUP-131

Verificado21/10/2026. [Trello](https://trello.com/c/NtiH8R4Z).
[PR146 borrador](https://github.com/EconomiconFinOps/tfm-economicon/pull/146), sin merge.
Base `bc94a4daea98e97b574d00f019d347fc61c2f915`, rama
`feat/JUP-131-aws-cicd-defensa`. [Runbook](../deployment/aws-defensa.md).

## Alcance y resultado

Implementación local autorizada expresamente, **sin desplegar AWS**: bootstrap
Terraform separado, pipelines manuales CodePipeline/CodeBuild, runner con
SHA/config/plan, lease, caducidad, retirada recuperable y CI offline.
Se conserva arquitectura JUP-060 y CD DockerServer. No hay credenciales en Git.
Cuenta normal, appEspaña/controlParís, dominioeconomicon.danteinferno.es y
defensa29Oct2026. Fecha/hora de arranque definitiva y coste por comprobar.

## Comprobaciones ejecutadas

| Comando/comprobación | Resultado real |
| --- | --- |
| `python -m unittest discover -s tools/aws_demo -p 'test_*.py' -v` |24PASS: entradas, SHA/config/plan, cuentas/regiones/presupuesto, inventario propio, desbloqueo limitado, recetas inválidas, archivos de limpieza, normalización Windows/Linux, caducidad, parada de escritores, residuos y no ejecución cloud desde preparación |
| Terraform1.13.3 `fmt -check -recursive infra/aws-bootstrap infra/aws-reference` | PASS |
| `init -backend=false` / `validate` en bootstrap | PASS, proveedorAWS6.13.0 de caché, lockfile conservado |
| Terraform test bootstrap |1run mockPASS: dos pipelines manuales y serializados, storage privado/versionado y secretos por ARN |
| Terraform validate/test referencia |7runs mockPASS:6previos y perfil de retirada que conserva topología |
| Restaurar sourceZIP en `.work/expiry-source`, init `-backend=false -lockfile=readonly`, validate/test | PASS,7runs; lockfile sigue disponible en paquete de limpieza |
| `node --test tools/ci-workflow.test.mjs tools/cd-workflow.test.mjs tools/repository-governance.test.mjs` |36PASS |
| `node infra/aws-reference/tests/edge-functions.test.cjs` |8escenariosPASS |
| `openspec validate --all --strict --no-interactive` |88elementosPASS |
| `node tools/jup-check.mjs --all` | PASS, incluidaJUP-131 |
| `node tools/jup-cleanup-check.mjs` |2263archivosPASS en el corte de verificación |
| `git diff --check` | PASS |
| `python tools/aws_demo/prepare.py --allow-incomplete` | Genera paquete local; `aws_deployable=false`, `aws_preflight_executed=false`, `aws_resources_created=false` |

Windows/Python3.14. Algunas ejecuciones iniciales fallaron por restricciones de
spawn/temporales del sandbox y dependenciaYAML ausente en el nuevo worktree; se
repitieron sin cambiar producto, fuera del sandbox, reutilizando dependencias
locales mediante junction ignorada. Se usó el binarioTerraform existente fuera
del repositorio y provider de caché con lockfile, sin credenciales ni APIs AWS.
El job Linux/Python3.12 está incorporado en CI; su ejecución remota se registra
aparte y no se deduce de estas pruebas Windows.

La primera CI remota en `5c928f2a` detectó que el lockfile heredado solo tenía el
checksum de paquete instalado Windows: init Linux comprobaba el ZIP firmado, pero
validate no aceptaba el paquete Linux desempaquetado con `-lockfile=readonly`.
Corregido con `terraform providers lock -platform=windows_amd64 -platform=linux_amd64`:
ambas descargas firmadas por HashiCorp y h1Linux añadido a ambas raíces, manteniendo
AWS6.13.0. La CI posterior registra su resultado en PR146; no se oculta el fallo.
El hash de aplicación normalizado coincide Windows/Linux:
`8ac0ac1319ff23cbf734b8fd6fb73107536e074b2044ee898d41ca270ea32903`.

## Revisión técnica asistida

Un revisor independiente, según la guía de ejecución del plan, hizo revisión
estática sin modificar archivos ni acceder a AWS. Detectó: prefijoS3 de artefactos
incorrecto, lockfile ausente del ZIP, escritores activos al vaciar S3, permisoSLR
y falta de caducidadtrasaprobación. Se corrigieron bucket separado, fuente con
lockfiles, parada/waitECS antes del vaciado, principal oficial
`vpcorigin.cloudfront.amazonaws.com` y guardas de expiración antes de apply/release.
Se añadieron regresiones. La sugerencia inicial del principal llevaba un guion;
se contrastó y corrigió con [documentaciónAWS](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-service-linked-roles.html).
Esto no sustituye revisión/validación oficiales ni atribuye roles humanos.

## Primer ensayo: preparación y límites

Ejemplo versionado `infra/aws-cicd/ensayo1.example.json`; regenerar salida
`.work/ensayo1/{config,readiness,start-up,start-down}.json` desde el SHA elegido.
El configkey es SHA256 de bytes exactos; statekey
`economicon/defensa/ensayo1/terraform.tfstate`. No hay JSON de arranque ejecutado.

Faltan entradas reales de cuenta/zona/motores/saldo/CI, prerrequisitos bootstrap y
receta/evidencia de PostgreSQL/Cognito/Bedrock y datos. El pipeline rechaza esas
ausencias antes de crear infraestructura demo. No se ha implementado ni verificado
la adaptación de producto en esta entrega; no se rellena `application_adaptations_verified`
para eludirla. No hubo buildDockerLinux, SQL/cloud, emisiónTLS, DNS, coste medido,
apply/destroy ni aceptación funcional AWS. El primer ensayo no es lanzable todavía.

Revisión/validación de roles oficiales, asignación humana y ensayos reales
permanecen pendientes. No hay merge ni autorización de despliegue por este informe.
