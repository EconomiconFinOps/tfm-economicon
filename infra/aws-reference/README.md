# Plantilla Terraform de Economicon para AWS

Complemento técnico de [JUP-060 — Documentar arquitectura técnica](https://trello.com/c/alMIpBOQ) y del [esquema de arquitectura](../../docs/architecture-aws.md). Preparado el 10/10/2026 por petición del usuario. **Se entrega el código de infraestructura, sin ejecutar despliegue.** La petición de plantilla amplía el entregable documental; no reactiva el plan de desplegar AWS.

Terraform define una arquitectura de referencia con frontend público y servicios privados. No convierte el checkout actual en una aplicación compatible con PostgreSQL, Cognito o Bedrock. Los servicios ECS de aplicación están desactivados por defecto hasta que existan imágenes adaptadas. `deploy_applications = false` no es un modo gratuito: un `apply` crearía el resto de la infraestructura y generaría costes. No se ha ejecutado `apply` ni un plan contra AWS.

## Contenido

| Archivo | Recursos y función |
| --- | --- |
| `versions.tf` | Terraform >= 1.13.3, proveedor AWS 6.13.0 fijado y proveedor adicional us-east-1. |
| `variables.tf` | Entradas, restricciones de región/AZ, versiones de motores, imágenes y activación explícita de aplicaciones. |
| `network.tf` | VPC /16; tres subredes públicas de salida, tres privadas de aplicación y tres de datos sin ruta a internet; NAT por AZ, endpoint S3 y Security Groups. |
| `data.tf` | Dos RDS PostgreSQL Multi-AZ cifradas, MQ RabbitMQ en tres AZ, KMS, contenedores de secretos y buckets S3 privados/versionados. |
| `edge.tf` | ACM y DNS, ALB interno, CloudFront VPC origin, S3 OAC, funciones de rutas y WAF con límite por IP. |
| `identity.tf` | Cognito User Pool, cliente público de OAuth code y dominio administrado. Login con PKCE a implementar en frontend. |
| `compute.tf` | ECR, ECS Fargate, roles por servicio, logs y descubrimiento DNS del simulador Azure. |
| `observability.tf` | Alarmas básicas de errores API y espacio RDS; SNS sin suscriptores. |
| `outputs.tf` | Referencias a endpoints, buckets, ECR, Cognito y ARN de secretos; no muestra contraseñas. |
| `terraform.tfvars.example` | Parámetros ficticios, sin credenciales. Las versiones de motor son ilustrativas. |
| `backend.s3.hcl.example` | Ejemplo de estado remoto con bloqueo S3; necesita un bucket preexistente y no está activado. |
| `bootstrap/vector.sql` | Instalación de extensión vector para una hipotética fase de bootstrap, nunca ejecutada por Terraform. |
| `tests/` | Pruebas con proveedores simulados y pruebas locales de las funciones de rutas. |

## Flujo representado

```text
Usuario → Route 53 → CloudFront + WAF + ACM
                        ├─ estáticos → S3 privado mediante OAC
                        └─ /api/* → VPC origin → ALB interno → backend Fargate
                                                               ├─ RDS operativo
                                                               ├─ RDS vectorial
                                                               └─ MQ → processor Fargate
                                                                         ├─ RDS
                                                                         ├─ S3 documentos
                                                                         └─ Azure Cost API simulada
Cognito: identidad del usuario; permisos de tenant: aplicación y base operativa.
Bedrock: permisos IAM optativos para backend/processor; no se invoca ningún modelo.
```

La plantilla desarrolla la variante de acceso público del documento. No crea Client VPN ni implementa la alternativa EC2/Compose. La VPC tiene Internet Gateway porque lo necesita CloudFront VPC origins; las tareas no reciben IP pública. NAT proporciona la salida HTTPS para ECR, secretos, logs y APIs; S3 utiliza un endpoint gateway. Los endpoints interface son una alternativa a estudiar, no están incluidos.

`/api` se elimina mediante una CloudFront Function antes de llegar a FastAPI. Authorization, X-Tenant-Id, query strings y cookies se reenvían, excluyendo Host para usar el nombre TLS del origen. La API y sus errores no se cachean. Las rutas SPA sin extensión apuntan a index.html únicamente en el comportamiento estático; un error API no devuelve el HTML del frontend. El ALB bloquea `/metrics` y `/metrics/*`.

HTTPS cubre usuario → CloudFront → ALB. El tramo ALB → contenedor y el acceso al simulador usan HTTP dentro de la VPC, limitado por Security Groups. No se declara cifrado extremo a extremo. RDS fuerza TLS y MQ exige AMQPS; las imágenes y DSN deben verificar certificados. Si el diseño exige TLS entre contenedores, requiere listener/certificados de aplicación adicionales.

## Validación local sin AWS

Desde esta carpeta, con Terraform instalado:

```powershell
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate
terraform test
node tests/edge-functions.test.cjs
```

`init` descarga el proveedor oficial y verifica su integridad; no aprovisiona recursos. `validate` comprueba configuración y esquema. Todos los bloques de `tests/architecture.tftest.hcl` usan `mock_provider` y `command = plan`: se simulan proveedores regionales y de edge, sin consultar AWS. Los identificadores y la contraseña de prueba son fixtures ficticios. No se necesitan credenciales AWS, archivo tfvars real ni backend remoto para estas comprobaciones.

La evidencia de validación acompaña al paquete en `VALIDACION.md`. El lockfile conserva la versión y checksums del proveedor. La versión fijada se eligió para reproducibilidad; no se afirma que sea la última. Una actualización requiere regenerar lockfile y repetir comprobaciones.

## Requisitos de una hipotética utilización futura

Estos requisitos explican los límites de la plantilla; no son tareas de despliegue aprobadas ni condiciones para entregar la documentación.

1. **Cuenta, región y DNS:** zona pública Route 53 existente y control de ambos nombres. Confirmar soporte de VPC origins, Fargate, versiones/tamaños RDS y MQ, cuotas de ALB/Security Groups y modelos Bedrock en la región. Los nombres `example.com` y los IDs del ejemplo no permiten desplegar. Los certificados se validan por DNS: regional para el origen, us-east-1 para CloudFront.
2. **Aplicación:** migrar realmente el dialecto/SQL/migraciones de CockroachDB a PostgreSQL; integrar Cognito y resolver usuarios/tenants; adaptar proveedor Bedrock, dimensión vectorial y reindexación; mantener contrato del simulador. No basta con modificar variables. Los defaults mock/litellm del checkout no se cambian con esta plantilla.
3. **Bootstrap de datos:** crear usuarios/roles mínimos y vhost MQ, habilitar pgvector, ejecutar las migraciones del backend antes del processor mediante un único ejecutor controlado. Los servicios no se ordenan como `depends_on` de Docker Compose: necesitan reintentos y tolerancia a dependencias. Terraform crea las bases, no las tablas ni los roles de negocio. No se da a las aplicaciones acceso al secreto administrador RDS ni se inyecta la cuenta administrador MQ.
4. **Artefactos:** construir imágenes Linux x86_64 sin privilegios, con Python y healthchecks en los puertos 8000/8001/8002; publicarlas en los ECR de salida y usar sus digest sha256. El filesystem raíz es de solo lectura, con `/tmp` escribible. El comando de entrada de cada imagen debe ejecutar el servicio correspondiente.
5. **Frontend:** compilar con la URL de API `/api` o la salida `api_base_url`, implementar callback Cognito y PKCE y cargar el build en el bucket frontend. `VITE_*` solo lleva valores públicos. Terraform no compila ni sube el frontend ni crea usuarios Cognito.
6. **Secretos:** poblar fuera de Terraform los secretos JSON descritos abajo y reiniciar tareas tras rotarlos. Habilitar `deploy_applications` y `application_adaptations_verified` solo tendría sentido tras verificar esos requisitos y aportar las tres imágenes por digest. El booleano no verifica por sí mismo la aplicación.

| Secreto runtime | Claves JSON requeridas por la plantilla |
| --- | --- |
| backend | DATABASE_URL, VECTOR_DATABASE_URL, RABBITMQ_URL, AUTH_SECRET_KEY |
| processor | DATABASE_URL, VECTOR_DATABASE_URL, RABBITMQ_URL, AZURE_COST_API_TOKEN |
| azure-cost-api | AZURE_COST_VALID_TOKENS, AZURE_COST_SKIPTOKEN_SECRET |

AUTH_SECRET_KEY se conserva como requisito del arranque actual hasta que una adaptación revisada a Cognito lo retire. `AZURE_COST_VALID_TOKENS` y `AZURE_COST_API_TOKEN` deben contener el mismo token de simulación autorizado. Usar DSN URL-encoded, usuarios limitados, nombre correcto de base/vhost y validación TLS; no reutilizar las credenciales admin. Si una imagen adaptada necesita otras claves, actualizar explícitamente su contrato de secretos. No ponerlas en `application_environment`, que está destinada solo a configuración no secreta.

`bedrock_model_arns` vacío no concede permisos de inferencia. Su configuración admite ARNs exactos de modelos fundacionales de la región; perfiles de inferencia entre regiones, Marketplace y otros mecanismos de acceso no están resueltos. El acceso/modelo, sus parámetros, costes y capacidad requieren revisión separada. No se contrata throughput ni se crea una Knowledge Base.

## Estado Terraform y persistencia

El proveedor guarda `mq_admin_password` en el estado aunque la variable sea `sensitive`; ese atributo oculta la salida, no cifra el state. Si se utilizara, aportar el valor por un canal seguro como `TF_VAR_mq_admin_password`, proteger state/planes con cifrado, acceso restringido y exclusión de Git. RDS genera y administra su propia contraseña en Secrets Manager: Terraform referencia el ARN, no lee el valor. Los secretos de aplicación se crean vacíos, sin versiones ni valores almacenados por Terraform.

El backend local existe solo para esta referencia sin ejecución. Para un uso real, preparar un bucket de estado privado con versionado, cifrado y mínimo privilegio, activar `backend "s3" {}` y usar `backend.s3.hcl.example` sin credenciales. Ese bucket se administra fuera de este stack para no destruir su propio estado. No se incluye un provisioner ni un script que ejecute comandos al aplicar.

RDS, ALB y Cognito tienen protección de borrado. S3 y ECR no permiten vaciado forzado. La eliminación futura requeriría una decisión explícita y tratamiento de datos, snapshots, objetos y versiones; no se entrega un `destroy` automático. El sufijo de snapshots finales debe ser único para evitar colisiones con snapshots existentes. El estado, claves y backups sobrevivientes siguen teniendo coste si se conservaran.

## Cobertura y límites

- Tamaños de Fargate, RDS y MQ son referencias, no resultados de carga. Se crean dos instancias RDS Multi-AZ y tres NAT por defecto: no es un perfil de bajo coste. `single_nat_gateway = true` reduce NAT a uno a cambio de dependencia entre AZ.
- WAF tiene una regla de rate limit por IP. No sustituye autorización, control de tenant, límites de uso por usuario ni un análisis de seguridad. Cognito limita creación de usuarios al administrador y permite MFA; MFA no se impone a todos.
- El rol processor puede leer/escribir todo el bucket documental del entorno. El aislamiento por tenant depende del código; una separación IAM por tenant requeriría un diseño adicional.
- Hay logs de contenedores, Container Insights y dos tipos de alarma. No se incluyen métricas funcionales personalizadas, alarma por antigüedad de cola, suscripciones SNS, logs de acceso ALB/CloudFront, trail de CloudTrail, AWS Budgets ni simulacros de recuperación. Son extensiones del diseño documental, no funciones ya implementadas en este paquete.
- No se configura autoscaling: `desired_count` es fijo. Los despliegues ECS usan circuit breaker y rollback de tareas; no revierten migraciones de datos.
- Terraform sustituye CDK/CloudFormation para el aprovisionamiento representado. No se deben administrar los mismos recursos con ambos estados. CodePipeline/CodeBuild del esquema siguen siendo conceptuales; esta plantilla no instala CI/CD ni conecta GitHub.
- `validate` y pruebas mock no acreditan disponibilidad regional, aceptación por APIs AWS, coste, permisos reales, aplicación funcional, certificados emitidos, conectividad ni compatibilidad de SQL/IA. No se ha desplegado ni generado gasto AWS.

## Referencias

- [Proveedor AWS 6.13.0](https://registry.terraform.io/providers/hashicorp/aws/6.13.0/docs).
- [CloudFront VPC origins en Terraform](https://registry.terraform.io/providers/hashicorp/aws/6.13.0/docs/resources/cloudfront_vpc_origin).
- [Amazon MQ en Terraform](https://registry.terraform.io/providers/hashicorp/aws/6.13.0/docs/resources/mq_broker).
- [RDS en Terraform](https://registry.terraform.io/providers/hashicorp/aws/6.13.0/docs/resources/db_instance).
- [Requisitos de CloudFront VPC origins](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html).
- [Arquitectura y fuentes del proyecto](../../docs/architecture-aws.md).
