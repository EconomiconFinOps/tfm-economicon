# Cloud AWS — planificación de despliegue

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