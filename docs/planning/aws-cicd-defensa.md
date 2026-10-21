# Plan de CI/CD AWS para ensayos y defensa

20/10/2026 · Plan. Implementación autorizada21/10/2026 en JUP-131;
ver [runbook y límites](../deployment/aws-defensa.md). No ejecutado en AWS.

## Objetivo y decisiones de alcance

Reutilizar la arquitectura y Terraform de JUP-060 para dos ciclos de ensayo
crear → comprobar → destruir y una ejecución de defensa de unos diez minutos
de uso. La aclaración del usuario sustituye la interpretación de disponibilidad
permanente. Cuenta con 60 € comunicados: verificar saldo efectivo y cobertura.
No seleccionar otra arquitectura ni reducir AZ/servicios por inferencia.

El usuario confirma **cuenta AWS normal** el 20/10. Mantener la propuesta de
CodeConnections/CodePipeline/CodeBuild con roles de servicio. Esto no acredita
permisos IAM, cuotas ni saldo: comprobarlos en preflight.

Datos aportados por el usuario: región más cercana a España, dominio
`economicon.danteinferno.es`, defensa **29/10/2026**, hora pendiente.

### Configuración regional y DNS propuesta

- Aplicación/infraestructura: **Europe (Spain), `eu-south-2`**. Comprobar que la
  cuenta tiene habilitada esta región opt-in. Seleccionar tres AZ mediante la
  cuenta y validar versiones/tamaños de RDS/MQ y modelos Bedrock requeridos.
- Pipeline/CodeConnections/CodeBuild y buckets de bootstrap: **Europe (Paris),
  `eu-west-3`**, propuesta motivada por disponibilidad regional. La documentación
  de la conexión GitHub de CodePipeline excluye España; CodePipeline y CodeBuild
  sí tienen endpoints allí, lo que no demuestra disponibilidad de esa acción.
- CodeBuild ejecutado en París llama a APIs y ECR de España. Configurar región de
  infraestructura explícita, separada de región de bootstrap y provider edge
  `us-east-1`. No confiar en `AWS_REGION` del runner para los recursos demo.
  No hace falta una acción CodePipeline entre regiones si Terraform se ejecuta
  en el CodeBuild de París; sus permisos sí abarcan los recursos españoles.
- Frontend: `https://economicon.danteinferno.es`; API:
  `https://economicon.danteinferno.es/api`; callback Cognito:
  `https://economicon.danteinferno.es/auth/callback`.
- Nombre para certificado/origen ALB propuesto: `origin.economicon.danteinferno.es`.
  Es un nombre adicional de DNS/TLS, no exposición pública del ALB interno.
  Confirmar control DNS; la plantilla requiere una zona pública Route53 existente.
  Si `danteinferno.es` usa otro proveedor, preparar como propuesta una subzona
  `economicon.danteinferno.es` delegada a Route53 mediante NS en el proveedor
  actual. No migrar la zona padre ni cambiar DNS en esta entrega.
- CloudFront/ACM de edge y WAF mantienen `us-east-1` según la plantilla; ACM de
  origen va en España. Destrucción e inventario abarcan España, París y edge;
  la zona DNS y delegación se administran fuera del stack demo.

Verificado por documentación: Amazon MQ y CloudFront VPC origins admiten España;
no se ha verificado en la cuenta el catálogo completo ni la compatibilidad del
modelo IA, versiones, cuotas o tamaños de la plantilla.

Fuentes: `origin/develop` en `88a6ce4c8a6c523c061e82a0a1f63f495f5db8ec`,
`docs/architecture-aws.md`, `infra/aws-reference/` y `.github/workflows/{ci,cd}.yml`.
El checkout principal está en una rama anterior: implementar desde develop
actualizado, en rama propia con identificador Trello real todavía por determinar.

## Diseño del pipeline

Conservar GitHub como fuente y la CI existente. Implementar el flujo AWS
documentado: CodeConnections → CodePipeline → CodeBuild → Terraform/ECR/ECS/S3.
Terraform sustituye el paso conceptual CloudFormation; no administrar los mismos
recursos con ambos. El CD actual de DockerServer mantiene su alcance.

Propuesta: dos pipelines manuales, `aws-demo-up` y `aws-demo-down`.
Sin aprovisionamiento por cada push. Source con detección automática desactivada,
ejecución fijada a SHA revisado y evidencia de CI satisfactoria para ese SHA.
No usar simplemente el último develop al aprobar un plan anterior.
Autenticación mediante roles de servicio AWS, sin claves permanentes en GitHub.
Comprobar que la identidad operadora permite CodeConnections/IAM/CodeBuild;
registrar cualquier limitación antes de proponer otra vía.

### Separación del estado y del ciclo de vida

| Conjunto | Contenido | Ciclo de vida |
| --- | --- | --- |
| Bootstrap | Bucket de state cifrado/versionado, bloqueo S3, roles, conexión GitHub, pipelines, CodeBuild, bucket de artefactos y limpieza programada | Fuera del destroy de la demo; retirar al acabar todos los ciclos |
| Demo | Recursos de `infra/aws-reference/`, imágenes ECR y datos sintéticos del ciclo | Crear y destruir en cada ensayo/defensa |
| Externo | Zona DNS existente y credenciales de acceso administrativo autorizadas | Referenciar; no destruir |

Bootstrap inicial con una identidad autorizada: el pipeline no puede crear sus
propios permisos antes de existir. Su state también debe quedar protegido y
recuperable. La conexión a GitHub puede requerir completar instalación/autorización.
CodeBuild y su controlador permanecen fuera de la VPC de demo; operaciones SQL
privadas se ejecutan mediante tareas ECS puntuales dentro de esa VPC.

State demo: bucket de bootstrap, clave `economicon/defensa/<cycle_id>/terraform.tfstate`,
`encrypt=true`, `use_lockfile=true`. Un solo escritor por ciclo; exclusión mutua
también entre up/down. No interrumpir Terraform al llegar una ejecución nueva.
Un ciclo parcialmente creado se recupera usando la misma clave, no otro state.

Cada ciclo registra `cycle_id`, SHA, cuenta, región, dominios, caducidad, imágenes,
versión Terraform/proveedor, planes y recursos. Nombres únicos compatibles con
los límites reales: ayudan a evitar colisiones con secretos pendientes de borrar,
snapshots y recursos globales. No duplicar dominios activos entre ciclos.

### Pipeline de creación

1. **Preflight y CI:** identidad/cuenta esperadas, región, crédito disponible,
   permisos, cuotas, versiones RDS/MQ, DNS y certificados; validar CI del SHA.
   `terraform fmt -check -recursive`, `init -backend=false`, `validate`, pruebas
   mock y `node tests/edge-functions.test.cjs`. Fijar Terraform 1.13.3 y lockfile
   existente inicialmente; no actualizar versiones sin comprobaciones.
2. **Build:** construir las tres imágenes Linux x86_64, probarlas y guardar
   artefactos identificados por SHA antes de arrancar recursos facturables.
   No compilar ni introducir secretos dentro de las imágenes.
3. **Plan de infraestructura:** init con backend remoto y configuración del ciclo;
   `terraform plan -out=infra.tfplan` con aplicaciones desactivadas. Revisar
   inventario, coste de la ventana completa y política de retirada; aplicar
   exactamente ese plan. Plan binario/state pueden contener secretos: acceso
   restringido, cifrado y retención corta; resumen público sanitizado.
4. **Publicación y bootstrap:** publicar imágenes en los ECR creados y fijar digests;
   poblar secretos mediante canal seguro; tarea ECS controlada para pgvector,
   roles mínimos, vhost MQ y migraciones backend → processor. Crear fixtures,
   corpus/índices y usuario–tenant demo de forma reproducible e idempotente.
   Bootstrap con identidad privilegiada separada del runtime.
5. **Aplicaciones y frontend:** habilitar aplicaciones solamente tras comprobar
   sus adaptaciones; generar y aplicar un segundo plan que incorpore digests.
   Compilar frontend con outputs reales de API/Cognito, subir build a S3 y
   esperar despliegue CloudFront/ECS, salud ALB y DNS/TLS.
6. **Aceptación:** login/tenant, consulta de costes, recuperación documental y
   respuesta del asistente según el guion elegido. Registrar una URL funcional,
   SHA/digests, resultados y hora READY. Infraestructura creada no equivale a
   aplicación funcionando. Medir duración y gasto observado de todo el ciclo.

Existe una dependencia fuera del código de CI/CD: la guía Terraform identifica
adaptaciones PostgreSQL/Cognito/Bedrock y carga de datos. El pipeline debe
comprobar evidencia real y bloquear la aceptación funcional si faltan; no marcar
`application_adaptations_verified=true` para saltar la comprobación.

### Pipeline de retirada

1. Resolver el ciclo exacto en el registro: cuenta, región, state, inventario y
   caducidad. Permitir únicamente recursos de demo; excluir bootstrap y externos.
2. Parar escrituras y tareas. Guardar evidencia sanitizada y los datos previstos
   por el guion. Fixtures demo deben ser reconstruibles sin conservar bases vivas.
3. Aplicar un plan preparatorio que desactive protecciones de borrado RDS/ALB/
   Cognito mediante parámetros explícitos del perfil de ensayo. La configuración
   general conserva sus defaults protegidos. Definir en ese perfil si hay snapshot
   final; usar sufijo único si se conserva y contabilizarlo hasta su retirada.
4. Vaciar únicamente buckets/ECR identificados en ese state: incluir versiones y
   delete markers S3. No hacer borrado global por nombre parcial o solo por tag.
   Confirmar antes si hay retención/Object Lock u otras restricciones.
5. `terraform plan -destroy -out=destroy.tfplan`; comprobar alcance y aplicar ese
   plan. Esperar la retirada de CloudFront, VPC origin, ENI y dependencias; permitir
   reintentos acotados con refresh/plan nuevo ante cambios, sin borrar state.
6. Comprobar state e inventario regional y us-east-1. Registrar snapshots, secretos
   en recuperación, claves KMS pendientes de borrado y logs/almacenamiento que
   subsistan, con fecha y tratamiento de cada uno. Nunca declarar coste cero
   solamente por un destroy correcto. Clave KMS: ventana actual de borrado 30 días;
   secretos: recuperación actual 30 días. Reutilización de nombres debe probarse.

La retirada debe poder ejecutarse tras un apply parcial o un fallo de smoke.
Preparar en bootstrap una caducidad de seguridad que solicite el down del ciclo
si sigue vivo. No programarla a diez minutos desde el inicio del apply: usar una
ventana operativa completa, visible y configurable, y una extensión controlada
para evitar interrumpir la defensa. Fallos de limpieza deben quedar como fallo
operativo con recursos residuales identificados, no como pipeline verde.

## Cambios previstos, sin implementación en esta entrega

| Archivo/directorio | Responsabilidad |
| --- | --- |
| `infra/aws-bootstrap/` | State remoto, IAM, CodeConnections, CodePipeline, CodeBuild y caducidad |
| `infra/aws-reference/versions.tf` | Activar backend S3 parcial |
| `infra/aws-reference/{variables,data,edge,identity}.tf` | Perfil explícito de ensayo y protecciones parametrizadas |
| `infra/aws-reference/tests/architecture.tftest.hcl` | Probar defaults protegidos y perfil eliminable |
| `infra/aws-cicd/buildspec-{validate,build,plan,apply,release,destroy}.yml` | Pasos CodeBuild y contratos de artefactos |
| `tools/aws_demo/` | Registro del ciclo, preflight, bootstrap, smoke y verificación de residuos |
| `.github/workflows/ci.yml` | Incorporar validaciones sin AWS y conservar checks existentes |
| `docs/deployment/aws-defensa.md` | Runbook probado, ventanas, recuperación y retirada final |

## Secuencia de trabajo y criterios de aceptación

- [ ] **Preparación:** con cuenta normal confirmada, comprobar permisos, región/DNS, fecha de
  defensa, crédito utilizable y disponibilidad de aplicaciones compatibles.
  Registrar alcance con identificador Trello/OpenSpec existente o nuevo real.
- [ ] **Backend y control:** implementar bootstrap y roles por función, bloqueo,
  SHA fijo y ejecuciones manuales. Pruebas: up/down simultáneos se excluyen;
  cuenta errónea y state ajeno se rechazan; planes/secretos no aparecen en logs.
- [ ] **Ciclo eliminable:** parametrizar exclusivamente comportamiento operativo
  de prueba; validar mock perfil protegido y demo, vaciado solo de recursos del
  state y recuperación tras fallo parcial. No alterar topología sin decisión.
- [ ] **Release funcional:** automatizar imágenes, bootstrap privado, frontend y
  smoke real; probar idempotencia de fixtures y errores de migración/salud. Una
  aplicación incompatible detiene release sin ocultar el fallo con mocks.
- [ ] **Ensayo 1:** crear desde vacío, verificar y destruir. Medir tiempos por fase,
  inventario residual y coste facturado cuando esté disponible.
- [ ] **Ensayo 2:** repetir desde vacío con el mismo procedimiento y SHA candidato;
  verificar ausencia de colisiones, reconstrucción de datos y repetibilidad.
- [ ] **Defensa:** congelar SHA/digests/guion del ensayo aprobado. Desplegar con
  antelación basada en el máximo medido más margen, probar READY, presentar
  diez minutos y retirar al finalizar. No compilar ni cambiar versiones en directo.
- [ ] **Cierre:** retirar bootstrap/artefactos cuando ya no se necesitan, conservar
  evidencia fuera del stack, registrar pendientes de borrado y revisar facturación.

## Presupuesto y calendario

Calendario propuesto, no reservas ni tareas externas creadas (Europe/Paris):

| Fecha 2026 | Entrega |
| --- | --- |
| 20–22 octubre | Preflight, DNS/IAM, implementación CI/CD y validación sin recursos demo |
| 23 octubre | Ensayo1 completo y retirada; medir duración/coste |
| 24–26 octubre | Resolver fallos y cerrar compatibilidad/repetibilidad |
| 27 octubre | Ensayo2 con SHA candidato y retirada |
| 28 octubre | Congelar SHA/digests/guion y verificar saldo/remanentes |
| 29 octubre | Despliegue anticipado, READY, defensa10min y retirada |

La hora de arranque del29 se fija al conocer hora de defensa y tiempos medidos.
No mantener RDS/MQ/NAT activos desde el día anterior por defecto.

Planificar dos ensayos y defensa dentro de los 60 € comunicados, incluyendo
creación, espera, uso, destrucción y recursos conservados entre ciclos. No hay
cotización regional confirmada ni garantía todavía de que alcance el crédito.
No estimar coste como diez minutos multiplicados por una tarifa horaria:
incluir reglas de facturación de cada servicio, CodeBuild/CodePipeline, RDS/MQ,
NAT/IPv4, almacenamiento, WAF, DNS, logs, snapshots e IA si entra en la demo.

CloudFront documenta hasta quince minutos para crear el VPC origin; no es un
plazo total del despliegue. El ensayo debe medir también RDS, MQ, certificados,
distribución, bootstrap y borrado. La hora exacta de defensa sigue pendiente.

## Fuentes técnicas verificadas el 20/10/2026

- [CodeConnections en CodePipeline](https://docs.aws.amazon.com/codepipeline/latest/userguide/action-reference-CodestarConnectionSource.html).
- [Limitaciones regionales de conexión GitHub](https://docs.aws.amazon.com/codepipeline/latest/userguide/connections-github.html).
- [Amazon MQ: regiones](https://docs.aws.amazon.com/general/latest/gr/amazon-mq.html).
- [Regiones opt-in](https://docs.aws.amazon.com/accounts/latest/reference/manage-acct-regions.html).
- [Backend S3 y bloqueo Terraform](https://developer.hashicorp.com/terraform/language/backend/s3).
- [Retirada RDS y snapshots](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_DeleteInstance.html).
- [CloudFront VPC origins](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html).
- [Tarifas CodePipeline](https://aws.amazon.com/codepipeline/pricing/),
  [CodeBuild](https://aws.amazon.com/codebuild/pricing/) y
  [Amazon MQ](https://aws.amazon.com/amazon-mq/pricing/).

Revisión propia: alcance reconciliado con la aclaración, separación de bootstrap,
planes por SHA, arranque funcional, limpieza tras fallo y costes residuales.
Usuario autoriza implementar el21/10. Pendientes revisión/validación oficiales y
comprobaciones reales de cuenta/compatibilidad. Primer ensayo preparado offline;
no es lanzable con los ejemplos sin completar los prerrequisitos.
