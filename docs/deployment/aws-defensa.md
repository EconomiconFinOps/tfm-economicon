# CI/CD AWS y primer ensayo — JUP-131

## Atlas preparado para ECS — 24/10/2026

La ampliación autorizada está implementada en `feat/JUP-131-atlas-ecs`, basada
exactamente en Atlas/PR159+160 (`ffb5d307`). PR146 ya estaba integrada; este delta
requiere una PR propia. [Evidencia y límites](../evidence/JUP-131-atlas-ecs.md).

- La fase privada `backend monitoring` verifica e importa el SQL aditivo antes
  de activar servicios; conserva histórico ajeno y aborta conflictos.
- Grafana y Prometheus comparten una tarea privada de 0.5 vCPU/1 GiB; Grafana
  persiste metadatos en una DB separada del RDS existente y lee evaluaciones con
  otro rol. Tres dashboards, cinco secciones del narrativo y TLS verificado.
- `/grafana/` usa autenticación propia y cookies seguras; sin acceso anónimo.
  Las credenciales se generan en Secrets Manager durante el bootstrap autorizado
  futuro. No entregar al evaluador la contraseña administrativa de Grafana.
- Landing Pages y vídeo quedan fuera de las imágenes. Prometheus retiene sólo
  24h/256MB efímeros por tarea; el histórico de evaluaciones permanece en RDS.
- El máximo rolling calculado baja a5.5vCPU con aplicaciones150% y monitorización
  200%; se sigue exigiendo cuota efectiva6vCPU antes de crear infraestructura.

**Control de gasto:** el controlador rechaza techo>30EUR. El campo heredado
`available_credit_eur` es saldo verificado del proyecto, no crédito promocional.
No rellenar un saldo/estimación ficticios para obtener READY. Avisos AWS30USD no
son un apagado automático; el operador debe confirmar el correo de Budgets.

El cálculo reproducible `python docs/planning/costes-aws/atlas.py`, con precios
22Oct, IVA supuesto21% y margen20%, estima23.40EUR para un ciclo de2h y39.42EUR
para tres ciclos de2h. El programa completo anterior no cabe en30EUR con esas
hipótesis. Medir duración facturable, descontar gasto existente y ajustar el
alcance/ventana antes de autorizar el primer ensayo; sin cambiar la HA prevista.

Para preparar sin AWS: `python tools/aws_demo/prepare.py --config .work/ensayo1/config.json --output .work/atlas-prep --allow-incomplete`.
La configuración histórica sigue bloqueada por saldo/estimación, caducidad y
fuente antigua. Además, la receta conserva el digest de aceptación histórico:
la nueva evidencia de monitorización no declara aceptada toda la aplicación.
Antes del ensayo: aceptación offline del candidato completo, integración y CI
push exacta de develop, cuotas efectivas, bootstrap/control importando roles ya
creados, saldo/ventana y autorización humana de despliegue. Pruebas de AWS,
CloudFront/Cloud Map y comportamiento real de modelos continúan pendientes.


## Entrada Atlas del 24/10/2026: adaptación pendiente para ECS

Paquete recibido de HAL para preparar AWS, sin autorización de despliegue o
carga SQL. La guía de Atlas presupone un servidor Compose existente; el flujo
de este proyecto usa Terraform, ECS y una release fijada. No ejecutar sus
comandos Compose ni editar imágenes/releases ya publicadas.

La identidad del paquete es `ffb5d307772f697cffb8b1e73e6330250e093601`
(PR159/160 según la entrega). ZIP SHA256
`c4eb723006f5a83518b4791b4177bd26d8f61e14f975e208d5acc49d78411f14`.
Verificados localmente ZIP, 13 entradas SHA256SUMS y 12 archivos del manifiesto.
Recibo: `.work/aws-access/atlas-handoff-receipt.json`; referencias y procedencia
en [continuidad AWS](../continuidad/cloud-aws.md).

| Elemento | Encaje en la preparación AWS |
| --- | --- |
| Landing y vídeo | HAL mantiene Pages `economicon-landing` y `https://landing-economicon.danteinferno.es/`. No añadir servicio ECS, bind de medios ni subdominio `landing-demo-jupiter` por este paquete. `demo-jupiter` y su `/grafana/` pertenecen a la instalación existente; no acreditan los futuros endpoints AWS. |
| Versión | El ensayo sigue fijado a `8e879dae3f23d52f46ea2b625ca1f2eebd22cd4a`. Antes de incorporar Atlas, reconciliar los cambios necesarios, revisar compatibilidad con el runtime AWS y regenerar digest/evidencias/CI para el SHA resultante. No reutilizar la CI anterior ni tomar cambios posteriores automáticamente. |
| Mediciones | `02-anadir-evaluaciones.sql` aporta 19 ejecuciones/1688 resultados declarados. Para una futura carga AWS, incorporar el SQL con hash al artefacto revisado y adaptar una tarea privada con transacción, bloqueo, rechazo de colisiones y conservación del histórico. El runner actual no tiene una fase de evaluación habilitada; no ejecutar `evaluation-dashboard.py load`, que vacía tablas. |
| Grafana | La referencia AWS actual no define servicio Grafana; su observabilidad usa CloudWatch/SNS. El UID `economicon-assistant-evidence`, sus cinco secciones, lector DB y otros dos dashboards son requisitos de una adaptación todavía pendiente. No suponer que la ruta Compose `/grafana/` existe en AWS. Cualquier servicio/ruta/secretos nuevos requiere plan, cuota y coste revisados. |
| Aceptación futura | Verificar carga inicial y repetida, histórico adicional y colisiones; lector de solo lectura, cinco secciones y los otros dos dashboards. Las pruebas del autor en contenedor desechable no acreditan nuestro runtime. No hacen falta inferencias nuevas para comprobar esta importación. |

Primero resolver la integración de versión y el alcance de Grafana en AWS;
después preparar su delta y verificaciones offline antes de un ensayo autorizado.
Conservar las dependencias vigentes: cuota efectiva, roles/secretos, revisión,
ventana/caducidad renovada y presupuesto. El umbral solicitado el 24/10 es30EUR;
el presupuesto de avisos creado es30USD, sin corte automático y con verificación
de correo pendiente en ese corte. Las referencias posteriores a60EUR son históricas.


## Acceso de revisión del evaluador — 22/10/2026

Por solicitud del usuario se ha creado el usuario de consola
`economicon-evaluador-carlos`. Fecha aclarada expresamente:30/11/2026 incluido,
Europe/Paris. Permisos bloqueados por Deny temporal desde
`2026-11-30T23:00:00Z` (01/12 00:00 local), también para sesiones existentes.
El usuario/perfil no se eliminan automáticamente: el bloqueo se aplica a las
acciones AWS y habrá que retirar la identidad cuando deje de ser necesaria.

Política `economicon-evaluador-carlos-hasta-20261130` usada como política de
identidad y permissions boundary, sin grupos, políticas adicionales ni access
keys. Permite revisión de configuración/metadatos en Irlanda/París/Virginia,
configuración de buckets economicon y zona delegada, roles/políticas economicon.
Algunos listados de infraestructura de consola muestran metadatos de toda la
cuenta en esas regiones. No permite leer documentos S3, secretos, datos DynamoDB,
contenido de logs, descifrar KMS, invocar modelos ni ejecutar pipelines/tareas.

Primer acceso: cambiar contraseña, entrar en «Credenciales de seguridad» y
registrar MFA con nombre `economicon-evaluador-carlos`; cerrar sesión y volver
a entrar con MFA para revisar recursos. Antes de MFA sólo se permite su propia
configuración inicial de contraseña/MFA. Contraseña inicial en un archivo local
privado, con ACL sólo para el usuario Windows del operador y SYSTEM, fuera deGit;
entrega al evaluador pendiente del operador. No correo enviado ni contraseña en
este documento. No se ha probado el login real del evaluador ni su MFA personal.

AWS Access Analyzer sin findings;23simulaciones de política favorables, lectura
posterior del documento y del límite de permisos conforme;6simulaciones más del
principal real con su boundary confirman lectura/cambio/MFA/fecha. Evidencias públicas
locales `.work/aws-access/evaluator-{policy,validation,simulations,access-receipt}.json`.
No se ha activado Organizations/IdentityCenter; la cuenta no pertenece a una
organización. Ningún cambio a aplicación, bootstrap, DNS o cuotas por este alta.

## Prerrequisitos autorizados y preparados — 22/10/2026

El usuario autoriza crear roles, DNS y conexión GitHub mientras se resuelven las
cuotas, sin desplegar aplicación/control. Se han creado únicamente:

- Zona pública `economicon.danteinferno.es`, ID `Z0908169205CKOWLEJ2DZ`.
  La zona responde SOA directamente en Route53; esto NO prueba delegación padre.
- Conexión `economicon-github` en París:
  `arn:aws:codeconnections:eu-west-3:605600557607:connection/df45512d-c3c4-44ca-93ca-c4ae399eb637`.
  Usuario completó autorización de GitHub; API confirma AVAILABLE.
- Boundary `arn:aws:iam::605600557607:policy/economicon-runtime-boundary`.
  Access Analyzer sin findings,15 simulaciones IAM conformes y revisión técnica
  independiente favorable. Ceiling de futuros roles ECS ensayo*/defensa*, no
  concede permisos por sí misma. No está adjunta a los roles de control.
- Roles base `economicon-defensa-build`, `economicon-defensa-deploy`,
  `economicon-defensa-pipeline`, `economicon-defensa-expiry`, con relaciones de
  confianza de la plantilla actual y sin políticas de permisos asociadas.
  Sus permisos efectivos se configurarán al preparar el bootstrap completo,
  cuando se conozcan buckets, tabla, logs y referencias de secretos concretos.

No se han creado CodeBuild, pipelines, buckets, bases, tareas Fargate ni secretos,
ni se han ejecutado modelos. Ninguna clave permanente generada. La zona cuesta
0,50USD/mes más consultas; no se prorratea por días. Presupuesto restante del
proyecto y coste completo del ciclo siguen sin verificarse.

### Delegación comprobada en Cloudflare

Por petición expresa del usuario se envió a «Jarvis», proyecto «Neon Bastion»,
chat `01a14bba-2515-7672-8bb3-ce01b4b54e4b` en host local. Operación limitada a
cuatro registros NS con nombre `economicon`, TTL Auto, en `danteinferno.es`:

- `ns-1509.awsdns-60.org`
- `ns-2005.awsdns-58.co.uk`
- `ns-995.awsdns-60.net`
- `ns-54.awsdns-06.com`

Conservar NS del padre `diva.ns.cloudflare.com` y `salvador.ns.cloudflare.com`.
Si existen DS o registros incompatibles, comprobar conflicto antes de sustituir
nada. No crear destinos A/AAAA/CNAME de aplicación todavía. Verificar después
NS desde autoritativo padre y SOA del hijo; no confundir propagación pública con
consulta directa a Route53. Jarvis comunicó ejecución terminada; comprobación
independiente22/10/2026 19:36UTC:1.1.1.1 y8.8.8.8 devuelven los cuatro NS
esperados, y ns-54.awsdns-06.com responde SOA del hijo (serial1). Las consultas
directas Windows a los dos NS padre devolvieron error de servidor; no se atribuye
a este chat una verificación autoritativa completa. Jarvis informa preservados
los20registros anteriores y los NS padre. No se han creado destinos de aplicación.

### Incorporación futura al estado Terraform

Los cuatro roles se crearon por API para preparar IAM sin ejecutar el grafo
completo del control. Antes del bootstrap autorizado, con inputs reales y
estado local protegido, IMPORTAR los cuatro roles en `infra/aws-bootstrap`:

```text
aws_iam_role.build     -> economicon-defensa-build
aws_iam_role.deploy    -> economicon-defensa-deploy
aws_iam_role.pipeline  -> economicon-defensa-pipeline
aws_iam_role.expiry    -> economicon-defensa-expiry
```

Después revisar el plan completo; no intentar crearlos otra vez ni mantener dos
estados dueños de esos roles. Boundary, zona y conexión siguen siendo referencias
externas del bootstrap, como prevé el diseño. No se ha importado ni aplicado
Terraform ahora. Artefactos públicos de preparación y readback en
`.work/aws-prerequisites/`; no contienen credenciales. Los secretos de GitHub/MQ,
Fargate efectivo6vCPU, CI pushdevelop/aceptación y ventana/coste aún son requisitos
de lanzamiento. DNS delegado verificado y CodeBuild Medium efectivo15 en París
(se requería1). Los secretos/control siguen pendientes. El paquete ensayo1
permanece bloqueado.

### Servicios y cuotas

Corte22/10/2026 19:36–19:37UTC: FargateIrlanda L-3032A538 efectiva0,
solicitud6 CASE_OPENED/caso179267775500075; CodeBuildMediumParís L-2DC20C30
efectiva15, suficiente para1. Su solicitud1 sigue CASE_OPENED/caso179267775900317:
el valor efectivo comprobado es distinto del estado administrativo del caso.
No se han reiterado solicitudes ni ejecutado builds/tareas. Recibos locales
`.work/aws-access/{quota-status-user-check,dns-status-user-check}.json`.

| Servicio | Papel en Economicon |
| --- | --- |
| IAM | Identidades temporales y permisos: build, despliegue, pipeline y retirada. |
| Route53 | DNS del subdominio delegado para los certificados y destinos futuros. |
| CodeConnections | Acceso autorizado al repositorio GitHub desde AWS. |
| CodePipeline | Secuencia manual de validar, compilar, planificar, aprobar, aplicar y retirar. |
| CodeBuild | Ejecuta builds, pruebas y Terraform; la cuota Medium1 permite una ejecución simultánea. |
| ECS/Fargate | ECS coordina tareas y Fargate aporta CPU/memoria para los tres contenedores. Se solicitan6vCPU para capacidad/rolling. |
| ECR | Registro de imágenes de contenedor por digest. |
| RDS PostgreSQL | Bases operativa y vectorial con pgvector. |
| Amazon MQ | RabbitMQ para trabajos de ingesta y procesamiento. |
| S3 | Frontend, documentos y, en el control separado, estado/artefactos. |
| Cognito | Inicio de sesión y verificación de identidad. |
| Bedrock | Embeddings Titan y respuestas Nova del asistente. |
| ALB, CloudFront, WAF | Entrada privada a API, publicación web y protección HTTP. |
| Secrets Manager, KMS | Secretos y cifrado. |
| CloudWatch, Scheduler, DynamoDB | Logs/alertas, caducidad del ensayo y bloqueo del ciclo. |

Las solicitudes de cuota pueden tardar horas o días; AWS no da aquí una fecha
garantizada. CASE_OPENED significa caso enviado a Support, no capacidad efectiva.
No confundir el tamaño/cupo solicitado con recursos funcionando o gastos de uso.

Fuentes oficiales consultadas22/10/2026:
[cuotas](https://docs.aws.amazon.com/servicequotas/latest/userguide/request-quota-increase.html),
[horas o días](https://docs.aws.amazon.com/r53recovery/latest/dg/working-with-rs-service-quota-checks.html),
[precio DNS](https://aws.amazon.com/route53/pricing/),
[delegación](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/CreatingNewSubdomain.html),
[conexión](https://docs.aws.amazon.com/codeconnections/latest/APIReference/API_CreateConnection.html).

## CI del controlador y aceptación de la aplicación — 23/10/2026

`AWS demo offline` comprueba la receta, las huellas de sus evidencias y scripts,
y las guardas del controlador. Una CI verde no renueva la aceptación de `apps/`.
La receta versionada conserva la huella del candidato que se evaluó; no debe
actualizarse automáticamente al cambiar la aplicación.

`prepare.py` y el runner siguen exigiendo coincidencia exacta de la aplicación
mediante `validate_recipe_files`. Si difiere, la preparación registra
`Release evidence application tree differs` y `aws_deployable: false`; el runner
rechaza la receta. `--allow-incomplete` sólo permite guardar ese informe bloqueado
en CI. Antes de desplegar hay que evaluar el nuevo candidato y registrar evidencia
que lo respalde, además de satisfacer los demás prerrequisitos de este runbook.

La instalación de LibreOffice/Tesseract en CI tiene un máximo de ocho minutos,
cinco reintentos APT y esperas HTTP/HTTPS de treinta segundos por operación de red.
El límite del paso acota el total; no garantiza disponibilidad del mirror.

## Correcciones de revisión — 22/10/2026

Las ocho solicitudes PR146 están implementadas con regresiones en
[el recibo de revisión](../evidence/JUP-131-review-fixes.md). Pendientes CI final
publicada y nueva aceptación humana; CHANGES_REQUESTED no se elimina con tests.
No hay autorización para desplegar.

Antes del ensayo, seleccionar un SHA integrado en develop y su run CI de push
completed/success del mismo SHA. Un run de PR, rama de trabajo o ejecución manual
no es válido. El runner comprueba ancestry con develop antes de provisionar.
Cada binding distingue infra/applications/destroy; planes anteriores deben
regenerarse. La aprobación muestra SHA256 del plan exportado por la acción que
lo generó. Revisar su binding privado en S3, la configuración y el contenido.
El plan applications vuelve a validarse antes de aplicar y no puede alterar
RDS/MQ/Cognito ni reemplazar/borrar recursos.

## Región vigente — 22/10/2026

Usuario autoriza Irlanda eu-west-1 para aplicación, París eu-west-3 para control
y Virginia para edge. Solicitudes Fargate6vCPU Irlanda/CodeBuild Medium1 París
enviadas; aprobación pendiente. Consultar los valores efectivos antes de lanzar:
una solicitud PENDING no habilita despliegue. Preflight del runner exige6/1.
Los60EUR son límite total del proyecto, no crédito AWS. CuentaCLI verificada,
DNS Cloudflare administrable por usuario; faltan zona/delegación, roles/boundary,
CodeConnections/secretos, coste/ventana y reviews. No ejecutar apply por esta guía.

La CI histórica41cace y las evidencias españolas previas no aceptan esta
adaptación. CI del nuevo candidato debe comprobarse por SHA exacto.

Implementación preparada el21/10/2026. [Trello](https://trello.com/c/NtiH8R4Z),
[plan](../planning/aws-cicd-defensa.md), [decisión](../adr/ADR-0027-aws-defense-lifecycle.md).
**No se ha desplegado nada en AWS.** El ensayo1 está preparado localmente, pero
no es lanzable hasta completar sus entradas y la evidencia funcional pendiente.

## Corte de verificación — 22/10/2026

La [CI39681182813](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39681182813)
terminó SUCCESS para `3e543b6fd58283c5d942ce9899fa7a00faa1d985`: ocho jobs
técnicos conformes y JUP policy omitido en el evento push. Incluye PostgreSQL
real, controlador offline, backend/processor, frontend y OpenSpec. No valida los
cambios locales posteriores de Bedrock ni una ejecución en AWS.

El candidato local incorpora develop `4567e8e7`, incluidos los recursos v4 de
JUP-132. El ADR AWS pasa a0027 para conservar el ADR0026 del modelo por defecto.
La receta real `infra/aws-cicd/release.json` conecta runtime nativo, cinco tareas
privadas de arranque, datos sintéticos por tenant y checker funcional.

Verificación del conjunto: backend Linux2714PASS/369SKIP; processor Linux
2666PASS/150SKIP y cinco fallos de una expectativa antigua del ledger, corregida
para incluir005 (sus siete casos focales pasan). Compatibilidad nativa/v4:
66PASS. Las tres imágenes se construyen y funcionan como uid10001 con raíz de
solo lectura y volumen ordinario /tmp privado. Terraform referencia12PASS;
controlador53casos,52PASS/1SKIP (el opt-in SQL se comprobó por separado).
La revisión técnica independiente encontró un bloqueo de destroy con count;
regresión reproducida y corregida conservando las guardas de ámbito/acciones.

Estas pruebas no acreditan permisos ni inferencia real de AWS. La CI final debe
verificarse por su SHA tras publicar el candidato; el run histórico anterior no
lo cubre. La revisión y validación humanas de CONTRIBUTING siguen pendientes.
`prepare.py --allow-incomplete` conserva el paquete bloqueado por las entradas
externas y `aws_preflight_executed=false`; no se llama a AWS.

### Qué desbloquea el primer ensayo

| Bloque | Trabajo o dato concreto | Criterio para avanzar |
| --- | --- | --- |
| Código preparado | Bedrock, tareas privadas, fixtures y checks conectados a outputs y receta real | Hash del árbol y evidencias verificados offline; aceptación real pendiente del ensayo |
| Integración y aceptación | Publicar el candidato reconciliado y obtener revisión/validación según CONTRIBUTING | CI SUCCESS del SHA final; no reutilizar el run de3e543b6f para código posterior |
| Acceso a cuenta | ID12dígitos y acceso mediante identidad/rol autorizado; Irlanda habilitada y boundary aprobada | Preflight futuro verifica identidad, cuotas, AZ, versiones RDS/MQ y permisos efectivos |
| DNS | Zona pública Route53 o delegación de la subzona de `danteinferno.es`, con zone ID | Control de `economicon.danteinferno.es` y `origin.economicon.danteinferno.es` para certificados y registros |
| Conexión de fuente | ARN CodeConnections AVAILABLE en París para este repositorio | Instalación de GitHub completada; origen manual fijado al SHA revisado |
| Secretos y modelos | ARN de los secretos GitHub/MQ en París, boundary IAM; disponibilidad y permiso de los modelos elegidos | Solo referencias públicas en configuración; valores en Secrets Manager. Metadatos/permisos de modelo verificados en la cuenta, no inferidos del catálogo |
| Coste y ventana | Presupuesto restante verificado, estimación del ciclo completo, margen residual, caducidad UTC y horario de defensa29/10 | Coste compatible con60€ y ventana de ensayo acordada. El ejemplo23/10 18:00UTC debe confirmarse antes de usarlo |
| Lanzamiento | Preparación del bootstrap de control y paquete revisado; autorización futura de despliegue | No ejecutar apply ni iniciar pipelines hasta recibir esa autorización |

Los tres primeros bloques de código/integración se preparan en el proyecto;
las referencias de cuenta, DNS, conexión y crédito deben proceder de sus
administradores. No pedir ni guardar contraseñas o tokens en Git/chat. El primer
ensayo verificará arranque, aceptación funcional, retirada y residuos: esos
resultados no pueden acreditarse antes del despliegue autorizado.

## Componentes y uso local

- `infra/aws-bootstrap/`: control en París, state S3 privado/versionado, artefactos
  separados, lease DynamoDB del dominio, roles y dos pipelines manuales.
- `infra/aws-reference/`: arquitectura existente en Irlanda, edge en us-east-1;
  backend S3 parcial y opción `rehearsal_teardown=false` protegida por defecto.
- `infra/aws-cicd/buildspec.yml`: único runner serializado para ambos pipelines.
- `tools/aws_demo/`: controlador, validadores, instalador Terraform1.13.3 con
  SHA256 fijado y preparación offline; proveedor AWS6.13.0 conservado.
- CI `AWS demo offline`: pruebas Python, Terraform validate/test con mocks y
  ocho escenarios de rutas; sin roles ni credenciales AWS.

Desde la raíz del repositorio:

```powershell
python -m unittest discover -s tools/aws_demo -p 'test_*.py' -v
python tools/aws_demo/prepare.py --allow-incomplete
```

Se generan `.work/ensayo1/config.json`, `readiness.json`, `start-up.json` y
`start-down.json`. Esta orden nunca llama a AWS, lee credenciales ni crea roles.
`--allow-incomplete` permite generar un paquete bloqueado; **no significa READY**.
Sin esa opción, la preparación devuelve exit2 si faltan entradas/evidencia.
Los ejemplos no contienen IDs reales ni secretos y fallan por diseño al validarse.

## Entradas que faltan para habilitar el ensayo

1. Cuenta12dígitos y permisos de la identidad administradora. Irlanda debe tener
   tres AZ utilizables y cuotas/motores/tamaños comprobados.
2. Zona Route53 pública existente que controle `economicon.danteinferno.es` y
   `origin.economicon.danteinferno.es`. Si DNS está fuera de AWS, se puede delegar
   solo la subzona; no migrar la zona padre. No se ha cambiado ningún registro.
3. Conexión GitHub CodeConnections AVAILABLE en París, limitada al repositorio
   EconomiconFinOps/tfm-economicon; completar instalación como administrador.
4. Secretos existentes en París con JSON `token` (GitHub Actions solo lectura) y
   `password` (MQ). Usar KMS administrado por Secrets Manager; si usan una clave
   propia, añadir permiso decrypt acotado antes de ejecutar. Ningún valor en Git,
   config, CLI arguments, outputs o comentarios.
5. Boundary IAM revisada y existente para roles runtime ECS. El deploy role exige
   esa boundary al crearlos y no puede quitarla. Revisar su política antes de
   provisionar: tiene permisos regionales amplios para crear el stack en la
   **cuenta dedicada del proyecto**, no una cuenta con cargas ajenas. DNS se limita
   a una zona y se deniega acceso del deploy role a los buckets de control.
6. Saldo utilizable, coste estimado regional de todo el ciclo y caducidad UTC.
   Los60€ comunicados no son una estimación ni saldo comprobado. Definir margen
   para otros ensayos/defensa y costes residuales. Presupuestos no son un corte.
7. SHA revisado y run CI SUCCESS del mismo SHA. No basta un run de otra rama/SHA.
8. **Aceptación de aplicación en AWS:** ejecutar las tareas y checks ya preparados
   con el SHA/receta revisados. La receta versiona hashes de aplicación y cuatro
   evidencias; no rellenarlos ficticiamente ni sustituir checks por true.

La entrega actual incluye [runtime privado](../evidence/JUP-131-aws-runtime.md),
[bootstrap de bases](../evidence/JUP-131-aws-bootstrap-db.md),
[adaptadores Bedrock](../evidence/JUP-131-bedrock.md) y
[fixtures/checker](../evidence/JUP-131-aws-fixtures-checks.md). El siguiente paso
que necesita la cuenta es preparar/verificar identidad y roles, conexión GitHub,
referencias de secretos, DNS, modelos, cuotas y crédito. Se avisará al usuario
antes de esa sesión. No se necesitan claves de acceso pegadas en el chat.
La preparación de estos prerrequisitos y el despliegue deben mantenerse como
acciones explícitas; todavía no se ha ejecutado ninguna en AWS.

## Contrato de la receta de release

`release.example.json` es documentación, no una receta ejecutable.
`application_sha256` se calcula con `application_digest`: contenido/nombres ordenados
de `apps/`, incluyendo Dockerfiles/lockfiles y excluyendo secretos/cachés. Textos
UTF-8 y evidencias se normalizan a LF para reproducir Windows/Linux; binarios se
conservan byte a byte. Plan y config siempre se verifican por bytes exactos. Así se
evita intentar guardar dentro de un commit su propio SHA, imposible de fijar.

Los comandos son arrays `['python','tools/aws_demo/script.py', ...]`, sin shell.
Son código de confianza revisado junto al SHA del pipeline. Reciben por entorno
`DEMO_OUTPUTS`, y en bootstrap `DEMO_IMAGES`, con ficheros privados de outputs y
digests. Deben fallar con exit distinto de0 ante cualquier incumplimiento.

Bootstrap debe poblar secretos vía Secrets Manager, ejecutar tareas ECS privadas
con rol de bootstrap separado (pasado como ARN/configuración pública y sujeto a
la boundary), crear roles DB/vhost, habilitar vector y migrar backend antes del
processor. Los comandos deben esperar éxito y salida0 de todas las tareas;
`startedBy` debe identificar el ciclo. No abrir DB/broker para el runner público.
La receta también debe generar fixtures/corpus/vectorización y usuario–tenant.

Checks deben esperar ECS/ALB/CloudFront y probar login/tenant, consulta de costes,
retrieval y respuesta real del asistente con el guion aceptado. Un simple /health
no basta. Las claves públicas de frontend/Cognito se obtienen de outputs; adaptar
sus nombres al frontend compatible al cerrar la aceptación. Todo secreto queda
en Secrets Manager; `application_environment` contiene exclusivamente valores públicos.

## Secuencia futura de ensayo1 (no ejecutada)

1. Revisar/crear los prerrequisitos anteriores y aprobar el plan bootstrap.
   Copiar `terraform.tfvars.example` a un fichero ignorado, fuera de Git.
   Bootstrap usa inicialmente state local protegido y luego debe migrarse a una
   clave propia `economicon/bootstrap/terraform.tfstate` del bucket de control.
   Guardar ese bootstrap state; nunca está en la clave de demo ni se destruye con ella.
2. Completar configuración en copia local del ejemplo, generar paquete y verificar
   `readiness.json`. Conservar `aws_preflight_executed=false` hasta ejecutarlo.
3. Tras una autorización futura de despliegue, subir config a la clave SHA256
   indicada por readiness en el bucket de control. El runner rechaza otra clave
   o un contenido distinto. No subir valores secretos.
4. Lanzar manualmente `economicon-defensa-up` usando `start-up.json` y región
   París. Lleva sourceRevisions COMMIT_ID y ConfigKey. No hay trigger por push.
5. `validate` comprueba configuración/cuenta, receta/evidencia, CI exacto y DNS;
   `build` produce imágenes antes de crear recursos demo; `plan` toma lease del
   dominio, instala la caducidad y guarda plan binario + binding privado.
6. Revisar plan/binding y coste; aprobar etapa manual. `apply` verifica binding,
   lease y caducidad. `release` publica digests, ejecuta bootstrap, aplica servicios,
   publica frontend y comprueba aceptación. READY requiere terminar esa fase.
7. Guardar duraciones y resultados; lanzar down con la misma configuración/SHA.
   No reaprovechar `ensayo1` tras destruir: usar `ensayo2` o `ensayo1b`, por los
   secretos/KMS en borrado diferido. El dominio admite un solo ciclo activo.

Los JSON de inicio están preparados, pero no se han ejecutado sus comandos.
El ejemplo de ensayo1 caduca23Oct18:00UTC; confirmar la ventana antes de usarlo.
El29 de octubre desplegar con margen según las mediciones; hora de defensa pendiente.

## Retirada y recuperación

Down: comprobar mismo lease/config/SHA → desbloquear solo protecciones de recursos
que existan → guardar plan destroy → aprobación manual → verificar plan/inventario
→ escalar servicios0 y esperar tareas detenidas → vaciar versiones S3 e imágenes
ECR del state → aplicar plan → comprobar state vacío → registrar residuos.

El plan de unlock se rechaza si crea/reemplaza/elimina recursos o cambia algo
distinto de protecciones. Un apply parcial se limpia desde su state original,
sin inventar un entorno nuevo y sin recrear recursos que aún no existen.
Después de un fallo revisar el diagnóstico privado, corregir y relanzar down;
no usar `state rm`, `force-unlock` ni vaciado global como atajo. Un plan obsoleto
se regenera; los IDs de state deben coincidir antes de tocar almacenamiento.

La validación de arranque exige una ventana máxima de ocho horas hasta caducidad.
La caducidad programa un CodeBuild desde el paquete fuente del mismo SHA, con
lockfiles incluidos; ejecuta down sin esperar aprobación manual como salvaguarda
de este entorno explícitamente desechable. No es una garantía de apagado: revisar
ejecución/cola/fallos y cola SQS de entregas fallidas del Scheduler. Un fallo del
build se consulta además en CodeBuild, aunque Scheduler haya entregado la solicitud.
Ambos pipelines y la caducidad comparten runner concurrente1;
Terraform usa bloqueo S3 y el dominio un lease sin TTL automático. Extender la
caducidad requiere actualizar la configuración/registro de forma controlada;
no editar solo un JSON y reutilizar el plan anterior.

State vacío no demuestra coste cero. El informe registra KMS pendiente30d,
secretos en recuperación30d, posibles backups/logs y bootstrap en París. Comprobar
inventario/costes en Irlanda, us-east-1 y París y registrar cada remanente. El runner
consulta recursos etiquetados del ciclo en Irlanda/us-east-1 y conserva el lease
si quedan activos; registra KMS/Secrets con borrado diferido. La
verificación independiente de facturación y recursos no gestionados es manual;
no se presenta como automatizada. Tras los tres ciclos, retirar bootstrap según
plan separado; el bucket de state tiene `prevent_destroy` y nunca se vacía por demo.

## Evidencia y límites

Ver [evidencia JUP-131](../evidence/JUP-131-aws-cicd.md). Pruebas locales/mock no
acreditan permisos/cuotas, soporte de versiones, duración, coste, DNS/TLS, build
Linux real, bootstrap SQL ni aceptación de la aplicación en AWS.

Receta/evidencias comprobadas también desde un ZIP de git archive del candidato
68ced055, sin archivos generados locales. Revisión técnica incremental APPROVE
tras corregir destroy/count; no sustituye las dos reviews humanas. La prueba
de preparación bloqueada usa explícitamente account_id pendiente, sin depender
de que falte una receta. Nuevo contrato de receta integrado en CI.
