# Cloud AWS — arquitectura documental

## CI/CD implementado sin despliegue — 21/10/2026

Origen: petición directa «Adelante, implementa el CI/CD siguiendo el plan y deja
preparado el primer ensayo, sin desplegar todavía en AWS». Título/ID de chat no
disponibles. [JUP-131](https://trello.com/c/NtiH8R4Z) creada mediante integración
DockerServer; no amplía ni reabre JUP-060/JUP-052. Ejecución asistida bajo Alejandro;
pairing/revisión/validación oficiales pendientes, sin atribuirlas a otras personas.

Base `bc94a4daea98e97b574d00f019d347fc61c2f915`, rama
`feat/JUP-131-aws-cicd-defensa`, worktree `../tfm-economicon-aws-cicd`.
Checkout antiguo y documentos previos conservados. [Plan](../planning/aws-cicd-defensa.md),
[runbook](../deployment/aws-defensa.md), [evidencia](../evidence/JUP-131-aws-cicd.md).

Cuenta AWS normal; appEspaña `eu-south-2`, controlParís `eu-west-3`, edgeus-east-1.
Dominio `economicon.danteinferno.es`, defensa29/10/2026, hora pendiente; saldo60€
comunicado. Dos ensayos propuestos23/27Oct, versión congelada28Oct.

Implementados bootstrapTerraform, stateS3 privado/versionado y artefactos aparte,
CodePipeline up/down manual, CodeBuild compartido concurrente1, lease de dominio,
SHA/config/plan vinculados, caducidadScheduler y cola de fallos, validación de
cuenta/CI/DNS/evidencias, buildECR, release mediante receta revisada, apagado de
escritores y retirada desde state, comprobación de residuos etiquetados.
Defaults y topología preservados; down parametriza solo protecciones de demo.
CI offline añadido sin credenciales; no tocar CD DockerServer.

Revisión técnica independiente asistida detectó archivo de limpieza sin lockfile,
escritores activos durante vaciado, permisoSLR y caducidadtrasaprobación; corregidos
con pruebas. Principal CloudFront verificado en documentación oficial:
`vpcorigin.cloudfront.amazonaws.com`. No es review/validación de roles humanos.

Paquete reproducible: `python tools/aws_demo/prepare.py --allow-incomplete`,
salida `.work/ensayo1/` ignorada. Readiness `aws_deployable=false`: faltan cuenta,
zona/motores/saldo/CI reales y receta/evidencia de adaptaciones PostgreSQL/Cognito/
Bedrock y datos. No se ha implementado ese trabajo de producto ni simulado aceptación.
No hubo llamadas API AWS, apply/destroy, recursos, credenciales, DNS ni gastos.

Siguiente paso: revisar cambios y completar entradas/aceptación; solo después de
una autorización futura de despliegue ejecutar el primer ensayo y medir coste,
tiempos y residuos. Fuente histórica JUP-060 abajo conserva su fecha original.

## Alcance vigente e incorporación a PR92 — 10/10/2026

El usuario confirmó que no habrá despliegue AWS y después pidió preparar Terraform e incorporar esquema/plantilla a JUP-060 («Completa el punto 1»). La referencia vigente es [arquitectura AWS](../architecture-aws.md) y [Terraform](../../infra/aws-reference/README.md), con [validación local](../../infra/aws-reference/VALIDACION.md). El código IaC se entrega sin plan real ni apply; no requiere cuenta, presupuesto o migraciones para aceptar la documentación. Las brechas PostgreSQL/Cognito/Bedrock son hipotéticas. CodePipeline/CodeBuild permanecen conceptuales y Terraform es alternativa a CDK/CloudFormation.

La propuesta EC2 del 09/10 queda como antecedente marcado en su cabecera; sus fases, preguntas de acceso/presupuesto y asignación de operador ya no son pendientes. Se reconciliaron arquitectura §6.3, OpenSpec y guías. Los fuentes de plantilla proceden del paquete documental local verificado por SHA; se excluyen ZIP, binarios, provider cache, state y tfvars reales. Ver [evidencia JUP-060](../evidence/JUP-060-validation.md).

Rama `docs/JUP-060-technical-architecture`, PR92, trabajo desde head `fec55b2f8997496fe0aea1c407522a2b51d289ff`; comentarios generales, reviews e inline leídos y vacíos antes de editar. Base documental c2995a1 conservada; fetch observó develop412ae41, sin atribuir nueva validación de runtime a ese cambio. Sin memoria, roles, merge ni recursos AWS. Pendientes generales: incorporación por Víctor a memoria, dictámenes Lucía/Paris y cierre OpenSpec/PR. El historial que sigue conserva evidencia del 09/10, no planificación operativa vigente.

## Antecedentes del 09/10

Verificado09/10/2026. Origen: petición de planificación cloud transmitida por Coordinador desde Discord20:29Europe/Paris. [Propuesta completa revisable](../planning/aws-deployment-proposal.md), guardada en ambos checkouts del proyecto; **solo planificación**, sin recursos, gasto, inventario de cuenta/credenciales ni IaC ejecutada.

## Conclusiones y decisiones propuestas

Se propone demo temporal privada con EC2x86/Compose ySSM, antes de considerar publicación persistente. Dimensionado inicial para cotizar:1host4vCPU16GiB,raíz30GiB+datos100GiBgp3,unaAZ,1IPv4 paraegress ySG siningress; sinNAT/ALB/EKS/AI. No elección deSKU/región/cuenta ratificada ni capacidad medida. Cuenta/alias/región/techo/duración/objetivo/dominio/operadores pendientes delusuario; preguntasasync presentadas, no respuestas observadas enestecorte.

ADR0006 no permite trasladar excepciónCockroachinsecurelocal aAWS por simplecambio dehost. Primeraimplementación requiereCompose seguro/TLSDB/secretos/roles/migraciones ypersistencia estable. El CDlocal crea releases/volúmenes porSHA; no es actualización de datos vivos cloud. IAMbuild/deploy/runtime separados,OIDC exactrepo/environment yoperación aprobadaSSM; ECRdigests; backupquiesced+restore, monitoring, expiry ycoste residual. Apppública necesita servidor estático adecuado/TLS/DNS/auth aceptados; Vitepreview/authdemo no producción. Se conservanADR0011/014/015, sin crearaceptación nueva.

Modelo de costes con cantidades, variablesregion/hours/retention yfuentes oficiales; sin total regional inventado, sin suponerFreeTier. IPv40.005USD/h ySecretsManagerreferencia0.40USD/secret/mes contrastados. AWSBudgets puede avisar conretraso, no hardcap; techo/duración/permisos/expiry yresponsable complementan alertas. Ningún presupuestoAI autorizado ni proveedor activado.

## Trello y responsables

Leídas103tarjetas por puenteDockerServer, snapshot-20261009T183522Z.json: no tarjeta AWS específica encontrada. JUP060 `69da44fd23884df0262389b1` es arquitectura final, **10Backlog**; roles actualesVíctorlider/Alejandropairing/Luciarevisión/Parisvalidación. Nota de planificación **6ac9369c206a85872b59ec4b**, readback snapshot-20261009T184700Z.json confirma misma tarjeta/lista6a773aaf43caafd588ce4539. Sin mover/cerrar, crear tarjetas, cambiarroles/fechas o declararalcancecloud aprobado. Implementador/operadorAWS/tarjetaimplementación aún porasignar mediante usuario/equipo, no inventados.

JUP052 mantieneDockerServer ysu propia aprobaciónoperativa pendiente. JUP089landing pública tiene dominio yroles propuestos, no autorización para exponer app. ProyectoTrello limitaMVP aAzure simulado/datasetpúblico ydespliegueprivado inicial; propuestaAWS no cambiaeso porafirmacióncompañero.

Drafts leídos enGitHub soloestado, sin acciones: #64/JUP101711f641, #66/JUP0176e25b30, #68/JUP068ce76492, #69/JUP036aee2571, todasOPEN/DRAFT yautorIber1to. Trabajo coordinadoenotroschats: no duplicar implementaciones/reviews/push o liberar drafts desdeestaplanificación. Su aceptaciónfuncional no se sustituye porinfra AWS.

## Handoff y pendientes

Víctor/060 puede contrastar diseño/alternativas conusuario, registraralcanceADR/OpenSpec ydeterminar si se necesita tarjeta de implementación. Después: Compose seguro local→IaC/change set/coste/permisos→aprobaciónapply→hostprivado→smoke/401/tenant/jobs→restoreRPO/RTOmedidos→UIprivada/pública si seaprueba→handoff/expiry/costeresidual. RPO24h/RTO2h son objetivospropuestos,no logros.

Antes de cualquier provisioning faltan lasdecisionespresupuesto/duración/cuenta/región/acceso/objetivo. DNS bloquea solo fasepública. Propuesta de cuentaAWSdisponible no se tomó como permiso de ejecutar. No copiarcredenciales,DockerServerstate ni datos existentes. Sin merge/deploy/timer/Discord/gastos. JUP052 ydrafts independientes no archivados.

Fuentes AWSprimarias09/10 sobreSSM/OIDC/Budgets/EC2/VPC/EBS/ECR/SecretsManager/ACM enlazadas enpropuesta. Lasarquitecturas/sizing soninferencias/propuestasdelautor,no recomendacionescontratadas ni ensayosAWS.
