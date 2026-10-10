# Propuesta AWS para Economicon

> **Alcance actualizado el 10/10/2026:** el usuario confirma que AWS es exclusivamente documental y no se realizará despliegue. Este texto del 09/10 se conserva como antecedente; las fases operativas y preguntas de cuenta/presupuesto no son pendientes de JUP-060. La referencia vigente es [el esquema AWS](../architecture-aws.md), complementado por [Terraform sin ejecución](../../infra/aws-reference/README.md). No se requiere provisionar ni adaptar aplicaciones para aceptar la documentación.

09/10/2026 · Propuesta revisable, no decisión aceptada ni autorización de gasto. Origen: petición de planificación transmitida por Coordinador desde Discord (20:29 Europe/Paris). No se han consultado credenciales, inventariado cuentas AWS, creado recursos, cambiado fechas/roles ni provisionado accesos.

## Decisión que se propone

Primero, una **demo temporal privada en EC2**, con Compose y datos sintéticos; publicación persistente después de resolver los gates de producción. La referencia para cotizar es un host x86 de 4vCPU/16GiB, disco raíz30GiB y datos100GiB gp3, una AZ, acceso por Session Manager y sin puertos de entrada abiertos. Es dimensionado inicial para comparar costes, no una medición de capacidad ni una elección de región aprobada.

Cuenta/alias, región, techo de gasto y duración, objetivo privado/público y dominio se preguntaron al usuario y siguen pendientes. Hasta respuesta se usa **demo privada** como hipótesis de diseño. eu-west-3 es una opción a cotizar, no selección inferida de la zona horaria. No comprar dominio ni reservar infraestructura.

## Hechos y brechas

| Área | Evidencia existente | Brecha cloud que no se da por hecha |
| --- | --- | --- |
| Docker | JUP049/050 integradas: cuatro apps y nueve servicios mock; digests, healthchecks, volúmenes y orden backend→processor | No hay IaC AWS, AMI probada, ECR ni prueba de sizing en EC2 |
| CI/CD | JUP051 integrada; PR73 a75472d tiene CI verde y validación Paris5470395430 local 5/5 | JUP052 apunta a DockerServer, no AWS. Timer antiguo sigue activo; merge/instalación/promoción reales esperan decisión humana |
| Base operativa | CockroachDB single-node, migraciones por dueño de tabla, ADR0011 Accepted | Compose usa --insecure y opt-in local. ADR0006 no autoriza trasladar esa excepción a cloud/producción; se necesita variante segura antes de crear runtime AWS |
| Vector/cola | pgvector y RabbitMQ persistentes; aislamiento tenant y semántica de jobs documentados | Backup/restore de conjunto, TLS, roles DB y actualización con datos persistentes no acreditados en AWS |
| Web/auth | React compilado, API con JWT/tenant y CORS exacto | Frontend sirve Vite preview; autenticación demo ADR0014 Proposed no es evaluación de seguridad de servicio público |
| IA | JUP108 integrado con LiteLLM/DB bajo perfil ai y consumidores mediante overlay | Demo cloud propuesta comienza sin ai, sin claves de proveedor ni llamadas pagadas. JUP070 no acredita calidad generativa real |
| Evidencia funcional | Datos públicos/sintéticos y smoke, pruebas de error/rollback bajo sus SHA y hosts | No hay ensayo AWS, URL pública, TLS externo, restore o aceptación de usuario cloud |

Fuentes del proyecto: `docker-compose.yml`, `apps/frontend/Dockerfile`, `docs/adr/ADR-0006-runtime-secret-boundaries.md`, `ADR-0011-single-owner-per-table.md`, `ADR-0014-demo-auth-boundary.md`, `ADR-0015-local-compose-deployment-boundary.md`, `docs/deployment/dockerserver-cd.md`. ADR0015 conserva Compose como baseline, no selecciona hosting productivo.

Trello oficial, snapshot09/10: no se encontró tarjeta AWS específica entre103tarjetas. **JUP060** (69da44fd23884df0262389b1) incluye arquitectura objetivo/despliegue final: Víctor liderazgo, Alejandro pairing, Lucía revisión, Paris validación. JUP052 conserva su alcance DockerServer; JUP089 es landing pública separada, con dominio pendiente y roles propuestos, no permisos para abrir la app. Esta propuesta se enlaza como aportación a060, sin cambiar alcance/estado ni crear tarjeta de implementación.

## Topología de la primera fase

| Recurso propuesto | Configuración revisable | Motivo / gate |
| --- | --- | --- |
| Cuenta/región | Cuenta del proyecto, región única y tags Project/Environment/Owner/ExpiresAt/CostCenter | Confirmar cuenta responsable, residencia y cuotas mediante acceso de lectura autorizado |
| VPC/subred | VPC dedicada o existente aprobada; una subred con ruta a IGW, EC2 con IPv4 pública para salida | Aplicación privada porque SG no permite ingress. No llamarla subred privada. Egress443/DNS necesario para SSM, registro, secretos; no NAT/ALB/EKS en esta fase |
| EC2 | Linux x86, clase M de4vCPU/16GiB como candidato; IMDSv2 y instance profile | Evitar asumir soporte ARM de digests. Comparar rate regional/capacidad y probar memoria/CPU antes de ratificar |
| Acceso | Identidad IAM federada/MFA; SSM, sin22 público ni keys compartidas | Administrador con shell restringida al host; espectadores con documento de sesión que solo permita frontend/API, no SQL/cola |
| Runtime | Compose cloud con imágenes por digest y namespace estable por entorno | Nueve servicios mock. No copiar el agente DockerServer como si ya soportara AWS |
| Disco | Raíz30GiB, datos100GiB gp3 cifrados; datos separados del root | Montajes estables para Cockroach/pgvector/Rabbit/Grafana. Preservar datos al actualizar/recrear apps; permisos por UID probados |
| Registro | ECR privado para4apps; retener dos versiones utilizables y aplicar política a imágenes viejas | Build en CI antes de desplegar; el host tira digests, no compila ni ejecuta source arbitraria |
| Secretos | Secrets Manager: material DB, cola, auth, Grafana/demo separados por función | Valores fuera de Git, userdata, logs/SSM parameters y VITE/ARG. Instance profile lee solo ARN autorizados; envfile0600 o montajes privados |
| Backup | Snapshot cifrado de datos tras detener writers y DBs ordenadamente; retención propuesta7copias | Restaurar en host/volumen nuevos y probarlo. Snapshot de disco activo no demuestra coherencia de la aplicación |
| Logs | CloudWatch con retención propuesta7d y métricas básicas; alarmas disco/CPU/status/backup | Scrapes y Grafana internos. No publicar metrics, consolas DB ni credenciales; SSM port-forward no graba payload de sesión |

La variante cloud de CockroachDB debe arrancar **sin --insecure**, con certificados, SAN de servicio y DSN verify-full. Roles compatibles con migraciones backend/processor segúnADR0011; no prometer runtime sin DDL mientras migran al arrancar. PostgreSQL necesita autenticación y transporte TLS validados. RabbitMQ queda privado, con usuario/vhost propio; transporte AMQPS y verificación CA se decide y prueba en el perfil seguro. Estos son cambios por implementar/validar antes del primer apply, no operaciones ya hechas.

No cambiar Cockroach por RDS PostgreSQL por conveniencia: dialecto, migraciones y contratos necesitan evaluación propia. No mover pgvector a servicio gestionado ni RabbitMQ a AmazonMQ sin comparación/ensayo de versiones y coste. No claimHA: el host y la AZ son puntos únicos de fallo.

## Red, TLS, DNS y presentación pública

**Demo privada:** control y túneles SSM sobre canal seguro; navegador accede a localhost, no a un dominio AWS inventado. La app conserva frontend/API en loopback con puertos locales iguales a los compilados y CORS. Propuesta de puertos cloud20060/20057, distintos de DockerServer19260/19257; confirmar libres antes de fijarlos. Dos sesiones de forwarding, una por puerto. Usar documento de sesión restringido a esos puertos para usuarios de la app; el operador puede tener un rol separado. No se ejecuta ahora.

El TLS del túnel no significa que HTTP interno o conexiones DB sean TLS: describir cada frontera. La variante DB segura es gate incluso para este entorno remoto; no heredar el opt-in local insecure.

**Publicación posterior:** subdominio `app.<dominio_aprobado>` separado de landing089. Elegir terminación TLS: ALB+ACM con targetprivate, o reverse proxy en host con certificado ACME/ACM exportable y renovación probada. No tratar un certificado ACM no exportable como fichero instalable sin más enEC2. ConALB, cotizarALB/LCU/IPv4 y limitar SGhost alSG delbalanceador; decidir cifrado hasta targets. Si se eligeproxy, cotizarEIP/certificado/renovación y limitar ingress443;80 solo si realmente necesario para redirects/validación.

Build frontend público con `VITE_API_BASE_URL=https://app.<dominio>/api`, proxy con stripping de prefijo y CORS exacto; probar rutas/API/assets/401. Reemplazar Vitepreview con servidor estático adecuado. Gate de auth pública: decisión explícita sobre IdP/MFA/revocación, cuentas/tenant, rate limiting y datos permitidos; no presentar el login demo como producción. DNS, certificados, renovación y propietario requieren aceptación del usuario. No publicar SQL, AMQP, Grafana, /metrics ni documentos privados.

## Entrega, IAM y persistencia

Proponer IaC declarativa (CloudFormation para evitar estado Terraform añadido), en rama/change aprobados después de aceptar diseño; no template/apply creado ahora. Exportar change set, permisos, recursos y coste antes de aplicar. Si el equipo ya usa Terraform/CDK en la cuenta, el usuario puede seleccionar ese estándar; no hay IaC AWS encontrado en este repo.

1. CI build/test de SHA revisado produce cuatro imágenes y manifiesto con digests/arch/tag/fecha. Se preservan los checks existentes y contratos del proyecto.
2. GitHub OIDC con `aud=sts.amazonaws.com` y sujeto restringido al repo `EconomiconFinOps/tfm-economicon` y environment cloud-demo; branch/environment protegido. Sin claves AWS largas en GitHub. Build role solo uploadECR de los4repos; deploy role separado, sin lectura general de secretos ni permiso amplio de cuentas.
3. Deployment manual con aprobación del usuario/environment: manifiesto aprobado en S3 o artefacto verificado; SSM ejecuta documento/version conocidos en instancias con tags del entorno. No `AWS-RunShellScript` abierto a cualquier instancia/comando para espectadores.
4. Instance role: ECRpull, secretos ARN específicos, objeto/manifiesto y logs del entorno; separar permisos de snapshots/borrado/destrucción para el operador aprobado. Acceso humano por federación/MFA, sin inventario de cuentas o creación de usuarios en esta propuesta.
5. Copia previa a migración; namespace de datos **estable**. No usar volúmenes DB nuevos por SHA como JUP052 local: eso no preservaría datos vivos entre releases cloud. Infra de datos y apps con lifecycle distinto; appmanifest anterior y snapshots vinculados.
6. Orden: DB/cola/vector saludables → backend y migraciones de sus tablas → processor/migraciones propias → frontend → smoke. Gate auth/login/401, tenant, ingesta/billing/job. Registrar SHAimagen/manifiesto y estado observable; CIverde no acredita runtime.
7. Rollback de apps solo si schema compatible; si no, restore previo autorizado con pérdida posterior explícita. No `down -v`, no regenerar passwords sobre volúmenes existentes. Restaurar DB/vector/cola como conjunto y tratar jobs publicados/duplicados/pendientes.

## Backup, monitoring y cierre de costes

Objetivos **propuestos, no medidos**: RPO24h, RTO2h para demo; backup antes de cada migración y restore ensayado antes de aceptar persistencia. Parar ingresos/workers y DBs de forma ordenada para snapshot consistente; registrar checkpoint, counts/hash de fixtures y jobs. Mantener snapshot+manifest+schema+referencias a versión de secretos (no valores). pg_dump/backup nativo puede añadirse tras validar versión/licencia/consistencia; no asumir que basta un snapshot caliente.

Alarmas propuestas: disco>80%, backup sin éxito en24h, health fallido sostenido, cola/job error y consumo deCPU/memoria; umbrales finales tras observar una carga representativa. CloudWatch/session metadata, no payload de túnel. Correlacionar HTTP/job sin secretos, publicar una evidencia sanitizada y retención de logs7d propuesta.

Expiry: responsable debe detener runtime, terminar EC2 y eliminar volúmenes/snapshots/ECR/S3/secretos retenidos según política aprobada; comprobar coste residual. StopEC2 no elimina EBS, snapshots ni ElasticIP. Terraform/CloudFormation destroy no debe borrar datos por sorpresa: política de Retain/backup y plan de eliminación deben ser visibles. No prometer coste cero por apagar la app.

## Presupuesto revisable

No se aprueba un importe por esta propuesta. Variables: Hhoras encendido, Thoras almacenamiento, rateEC2regional, p_gp3/p_snapshot/p_ECR/p_logs/p_S3, transferencia, secrets/calls, impuestos y cambio de moneda. Cantidades iniciales:1host4vCPU16GiB,130GiBgp3,1IPv4,4repos hasta20GiB, logs hasta1GiB/día,7snapshots(retención, cobroincremental real a estimar),6secretos,0NAT/0ALB/0EKS/0AI. Duración pendiente; no suponer FreeTier/créditos.

`Coste = H*p_EC2 + (130*p_gp3 + GBsnapshot*p_snapshot + 20*p_ECR + 6*p_secret)*(T/730) + H*0.005 + GBlogs*p_logs + GBegress*p_egress + S3/requests/secretsAPI + costes opcionales TLS/DNS + impuestos`.

La fórmula es hoja de planificación, no tarifa regional confirmada. IPv4 publicadoAWS0.005USD/h →0.12/día o3.65/730h para unaIP; SecretsManager referencia0.40USD/secret/mes →2.40/mes para6, API aparte. No mezclar tipoWindows de un ejemploM6i con nuestra instanciaLinux: cotizarLinuxOnDemand enregión aprobada. No reservar SavingsPlan/RI para demo temporal.

Antes delapply: exportar AWSCalculator con región/SKU/hours/retention, añadir margen propuesto20%, techo totaldelusuario y coste residual postexpiry. Alertas50/80/100%actual/previsión; AWSBudgets no corteinstantáneo, puede haberretraso. El controlreal combina cuotas/permisos/duración/tamaño y stop manual aprobado. PresupuestoAI separado delAWS; perfilai desactivado, ninguna llamada como parte delensayo inicial.

## Orden de trabajo y aceptación

| Orden | Entrega verificable | Responsable por roles actuales / decisión | Dependencias y criterio para avanzar |
| --- | --- | --- | --- |
| 0 | Decidir privado/público, cuenta/región, presupuesto/duración, dominio y operadores | Usuario decide; Victor consolida060, Alejandro aporta esta propuesta | Respuestas registradas; no provisioning antes |
| 1 | Diagramas/ADR propuesto y mapa local→AWS con costeCalculator | 060: Victor líder, Alejandro pairing, Lucia revisa, Paris valida | Aceptación de arquitectura y alcance; definir tarjeta de implementación si falta, sin crearla aquí |
| 2 | Variante Compose segura y lifecycle datos/images; pruebas locales sincloud | Implementador/roles de ejecución por asignar; propietarios060 revisan diseño | Sin insecure, TLS/secrets/roles/migrations/CORS probados; manifests yrollback correctos |
| 3 | IaC/change set y IAM mínimo; inventario read-only de cuenta aprobada | OperadorAWS por confirmar porusuario; roles de implementación aúnnoasignados | Cuotas/coste,políticaRetain/expiry ychange set aprobados, ninguna cuenta creada automáticamente |
| 4 | Primera instancia privada + bootstrap/imagepull | Operador autorizado; validación independiente según tarjeta asignada | 9servicios,sinAI,nopublicingress,SSM restringido,secretos ausentes deGit/logs/build |
| 5 | Smoke/401/tenant/jobs ybackuprestore en recursos propios | Paris rolvalidación060 de arquitectura; QA deejecución según rolaprobado | 5checks,estado/manifiesto/paths/puertos,restoreRPO/RTOmedidos ycoste real; no etiquetaspassed deplan |
| 6 | Ensayo de UI con actor autorizado, publicación opcionalTLS/DNS/auth | Usuario autoriza; JUP089 solo landing ydominio, noapp; roles nuevaejecución porconfirmar | Publicación aparte,certificado/renovación/rate limits yconformidad; no abrirDockerServer |
| 7 | Handoff ycaducidad/costeceroresidual verificado | Líder ejecución/operador designados porusuario | Runbook,backup/owner/fecha real,demostración porsegundapersona;Trellodictámenes yestado actualizados |

No duplicar draft64/66/68/69 ni sus dueños: esta planificación usa sus capacidades como dependencias/evidencia según SHA, no realiza su código/reviews/merge ni mueve tarjetas. La demo cloud no termina JUP065 ni acredita M5/modelo real. JUP052 requiere su propia decisión de ventana; no se usa como autorizaciónAWS ni se amplía su scope.

## Decisiones pendientes y handoff

Bloquean provisioning: importe/duración,aliascuenta/region/operador, objetivo privadoopúblico, tratamiento de TLS/datos ynuevoalcance cloud aprobado. Dominio solobloquea fase pública; no bloquea desarrollar diseño deprivada. Informaciónsolicitada alusuarioporformulario, sinclaves; no respuesta observada alpreparareste corte. Ningún permiso inferido de «AWS disponible» o de mensajecompañero.

Siguiente acción revisable deVíctor/060: contrastar propuesta, escoger alternativa y límites conusuario, registrar ADR/OpenSpec/alcance; distribuir implementación solo cuandoexista tarjetaautorizada. No está ratificada otraasignación. La anotaciónTrellose limita a enlazar planificación, no a marcaraceptación ni fechas.

## Fuentes oficiales contrastadas09/10/2026

- [SessionManager: acceso sin inbound y límites de logging](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html).
- [Port forwarding SSM y plugin local](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html).
- [OIDC GitHub e IAM: restringir sujeto/repo/environment](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html).
- [AWSBudgets: costes/avisos con retraso](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html).
- [IPv4 y NAT: preciosVPC](https://aws.amazon.com/vpc/pricing/).
- [EC2 LinuxOnDemand: cotizarregión/arquitectura](https://aws.amazon.com/ec2/pricing/on-demand/).
- [EBS precios](https://aws.amazon.com/ebs/pricing/) y [consistencia de snapshots](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-creating-snapshot.html).
- [ECR precios](https://aws.amazon.com/ecr/pricing/) y [SecretsManager precios](https://aws.amazon.com/secrets-manager/pricing/).
- [Certificados ACM exportables paraEC2](https://docs.aws.amazon.com/acm/latest/userguide/acm-exportable-certificates.html).

Las afirmaciones de diseño/sizing/RPO/RTO son propuestas del autor. Fuentes sustentan mecanismos y tarifas citadas, no viabilidad/coste total deEconomicon ni autorización deaprovisionamiento.
## Corte de PR draft — 09/10/2026

Lectura de estado únicamente: #64/JUP-101711f641, #66/JUP-0176e25b30, #68/JUP-068ce76492 y #69/JUP-036aee2571 están abiertas y draft, autorIber1to. La liberación/reconciliación se coordina en sus chats existentes; no se realiza desde esta propuesta cloud. No se añade dependencia de aceptar todo ese trabajo para planificar infra: para el ensayo se fija un SHA integrado con capacidades verificadas y sus límites.
