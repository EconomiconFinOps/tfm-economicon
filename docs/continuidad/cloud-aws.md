# Cloud AWS — arquitectura documental

## Corrección de CI que bloquea PR154 — 23/10/2026

Origen: HAL9000, chat `01a1270c-e332-7462-9c90-706d49ade92c`.
Usuario pide resolver el fallo de CI comunicado por Víctor. Trabajo separado de
JUP-138, desde develop `84b53b74d02ff5831ef9dbdd4f9c7d8c40cd4d24`, en
`fix/JUP-131-ci-release-validation`; sin modificar la rama documental.

Dos causas: processor agota veinte minutos descargando paquetes del mirror Azure;
AWS offline compara incondicionalmente la aplicación actual con evidencia congelada
en PR146. Baseline reproducido: 69 pruebas, un error por digest y una omitida.
La corrección conserva receta/huellas y validación estricta de prepare/runner;
CI comprueba integridad histórica y regresiones sin renovar aceptación. APT tiene
reintentos5, esperas HTTP/HTTPS30s y límite total del paso8min.

Controlador local: 74 pruebas, 73 correctas y una omitida (PostgreSQL opt-in).
La preparación sigue `aws_deployable=false`, incluido el bloqueo por digest.
Pruebas de CI remoto/publicación aún pendientes en este corte; ver
[evidencia de corrección](../evidence/JUP-131-ci-regression.md).
Ningún despliegue AWS, cambio de datos, inferencia, merge ni dispensa de reviews.

## Excepcion humana de integracion y reconciliacion — 22/10/2026

Origen: HAL9000, chat `01a1270c-e332-7462-9c90-706d49ade92c`.
Orden directa: «Mergea tambien la 146, tienes excepcion humana para saltarte validaciones».
Esta autorizacion puntual sustituye el requisito de completar las validaciones
antes de integrar PR146; no atribuye una aprobacion a Lucia o Paris ni modifica
reviews, roles, gates o protecciones. La solicitud de cambios de Lucia sobre
41cace0d se conserva; las correcciones posteriores se describen debajo.

Se reconcilia el candidato8e879dae con developf224226d en una copia aislada.
El unico conflicto manual era el indice compartido de continuidad: se conservan
las entradas AWS, JUP133 y JUP135 y se actualizan sus integraciones verificadas.
CI/package.json y chat_gateway se combinan automaticamente conservando las
adaptaciones AWS y los cambios de develop. No se incluyen los cambios locales
no publicados de costes/accesos del otro checkout.

La CI tecnica del candidato8e879dae era conforme al corte previo. No se ejecuta
una nueva validacion funcional del resultado reconciliado por esta excepcion;
no se declara CI nueva superada ni aceptacion operativa. Este encargo no ejecuta
AWS, Terraform apply, despliegue, modelos, recursos o gasto.
La autorizacion se limita a PR146; no habilita otros merges ni despliegues.


## Correcciones PR146 implementadas — 22/10/2026

Usuario autoriza corregir revisión y dejar CI verde, sin desplegar. Leídas todas
las reviews/conversación/inline: lmatsan41cace sigue CHANGES_REQUESTED, sin
comentarios generales/inline nuevos. Las8solicitudes y menores están atendidas;
recibo y límites en [JUP-131-review-fixes](../evidence/JUP-131-review-fixes.md),
plan [aws-pr146-review-fixes](../planning/aws-pr146-review-fixes.md).

Guardia applications antes de subir/aplicar, CI pushdevelop exacta+ancestry,
CAS fase/config, entorno público de hijos, manifiesto/stop de tareas propias
anómalas, filtros recursivos de credenciales, receta nativa coherente y JWKS
1intento/30s incluidos fallos/concurrencia. Binding incluye plan_kind y aprobación
muestra SHA256 exportado. No se cambian reglas de reviews ni protecciones.

Windows: controlador69casos68PASS/1SKIP, focalbackend142PASS (Cognito34),
Terraform referencia12/control1PASS mock, OpenSpec89PASS, gobernanza15PASS y
localdoctor/smoke80PASS; trazabilidad/higiene conformes. Node/Git EPERM del
sandbox se resuelve repitiendo con permiso de proceso, sin cambiar tests.
Review técnica independiente APPROVE, sin nuevos P1/P2/P3; no sustituye humana.
Imagenbackend reconstruida a9fa0549a2d8; Linux sin red/raízRO/uid10001/tmp0700
repite controlador68PASS/1SKIP y backend142PASS. CI final por SHA pendiente de
publicación. Receta/evidencia renovada y validada offline:
apphash8a47bf3d8f88fbc45652bdcbe5ecb7f71c036c3e9d3bfc0b51bb556d36cd633d.

Prerrequisitos del ensayo intactos: cuotas efectivas, roles/boundary, zona y
Cloudflare, CodeConnections/secretos París, coste/ventana60EUR y aceptación
humana con integración develop+CIpush antes de elegir SHA de despliegue.
No se ha consultado ni escrito AWS durante estas correcciones; no lanzar ensayo.

## Candidato Irlanda publicado y casos AWS abiertos — 22/10/2026

Commit bee31eca11a3c0ffe4fda4a77e8c89b8165b30d3 en PR146, borrador.
Cuotas consultadas tras envío: ambas CASE_OPENED, aún no aprobadas; Fargate
caso179267775500075 y CodeBuild caso179267775900317. No nuevos aumentos ni
recursos AWS. La única escritura en AWS son las dos solicitudes autorizadas.

Controlador55casos54PASS/1SKIP; backend135PASS/1SKIP y processor61PASS/6SKIP
en Windows/Linux. Terraform referencia12/control1PASS, OpenSpec89PASS y
gobernanza33PASS. Trazabilidad/higiene conformes; Node EPERM del sandbox
resuelto repitiendo con permiso de proceso, sin modificar producto/tests.
Review técnica regional APPROVE, sin nuevos P1/P2. Review humana41cace sigue
CHANGES_REQUESTED por8puntos previos; no hay validación ni merge autorizados.

ZIP limpio de bee31eca valida receta/evidencias y CA irlandesa. Hash de apps
2935d99c142d8cacd9b8f3bb694ff24e22747d87b10876416a796baecba5282b.
.work/ensayo1 apunta a Irlanda, cuenta/motores contrastados y nuevo SHA;
aws_deployable=false, preflight completo false; DNS/roles/conexión/secretos,
coste60EUR/ventana y reviews aún pendientes. Valores presupuesto restante y
estimación0 deliberados; caducidad del ejemplo provisional, no ventana aprobada.

Cierre verificado: [CI push39794617196](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39794617196)
SUCCESS y [CI PR39794797380](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39794797380)
SUCCESS para bee31eca11a3c0ffe4fda4a77e8c89b8165b30d3. SQL chat
39794624145 SUCCESS. Los ocho jobs técnicos pasan, y JUP policy pasa en PR.
El control separado JUP reviews sigue pendiente de resolver CHANGES_REQUESTED
y validación humana; no atribuir aceptación del conjunto ni merge. Registro de Trello actualizado por integración
DockerServer con readback conforme, sin mover/cerrar tarjeta ni publicar Discord.

## Irlanda autorizada y cuotas solicitadas — 22/10/2026

Usuario autoriza dos solicitudes y adaptación de configuración, sin despliegue.
Historial vacío antes de enviar, STS cuenta correcta. Respuestas guardadas
.work/aws-access/quota-requests.json.

- fargate eu-west-1 6: `f99f920429964ca680587d60e46e465dWHq54fCI`, PENDING al enviar.
- codebuild eu-west-3 1: `cda02ccd14c240a1882db2a85a62a7deVt04gbzC`, PENDING al enviar.

No son cuotas aprobadas. Solo estas mutaciones AWS autorizadas; sin recursos,
DNS/IAM/secretos/control creados. Código Irlanda implementado, TLS/CA nueva
SHA a11cf9a1d0aadd7db86f92cbaa496466daeb501bf1c5e429d8ce8914a01c15d6,
cuatro destinos Nova y rechazo de contrato español. Tests RED observados y
luego backend135PASS/1SKIP, processor61PASS/6SKIP, referenciaTF12PASS.
Controlador conforme salvo hash de receta deliberadamente pendiente de renovar.
Añadido gate de cuotas efectivas y permiso solo GetServiceQuota para los dos
ARNs exactos. Imágenes de producción backend fab7b1a4ebd8/processor54ddb1f177f5 construidas;
CA/contrato nativo/tmp0700/nonroot/readOnly comprobados. Linux focal135/61PASS
(mismos skips1/6); controlTF1PASS tras fijar atributos mock ARN conocidos para
evaluar la política real en plan. Revisión técnica incremental APPROVE sin nuevos P1/P2 regionales; no sustituye
los dictámenes humanos ni acepta los8puntos previos. CI del SHA final pendiente.

Nueva revisión humana lmatsan sobre41cace CHANGES_REQUESTED recibida y leída
completa, con8puntos previos (applicationsplan/source/leaseCAS/env/ARNcleanup/
publicvalues/recipeproviders/JWKS). No se corrigen ni dan por aceptados por el
cambio regional; requieren seguimiento antes de aceptación/merge/ensayo.
No hubo comentarios generales ni inline nuevos en ese momento.

## España deja de ser requisito; alternativa contrastada — 22/10/2026

Usuario indica expresamente que España NO es requisito y pide otra región sin
bloqueos. No habilitar eu-south-2 por los planes anteriores. Comprobadas por API
Irlanda/Paris/Francfort/Estocolmo: habilitadas sin opt-in; todas las cuotas
CodeBuild Linux Small/Medium/Large/XL/2XL =0 y Fargate On-Demand vCPU =0.
Virginia/Ohio tambien CodeBuild Medium0 y Fargate0. No se encontró una región
sin estos bloqueos entre las seis comprobadas; no extrapolar a todo AWS ni
afirmar que solo cambiando región el ensayo queda lanzable.

Irlanda eu-west-1 candidata compatible: AZa/b/c available, RDS db.t4g.medium
PostgreSQL16.9..16.15 MultiAZ ofertado, MQ mq.m5.large RabbitMQ3.13 con
CLUSTER_MULTI_AZ. TitanV2 ACTIVE ON_DEMAND y perfil EU NovaMicro ACTIVE; desde
Irlanda devuelve4destinos (eu-central-1/eu-north-1/eu-west-1/eu-west-3), frente
a5desde España. Solo metadatos; no se invocaron modelos ni se probaron permisos
de inferencia reales. Fargate Irlanda0 adjustable=true.

Siguiente paso propuesto: Fargate Irlanda cuota6vCPU para servicios/rolling y
CodeBuild Paris Medium1; solicitudes NO enviadas. Antes comprobar historial y
cuotas de otros servicios/uso concurrente. Region candidata, no lanzamiento
autorizado. Control Paris preservado. Codigo/receta/validadores aun fijan España:
si se adopta Irlanda, adaptar de forma coherente IAM, ARNs, preflight, TLS/CA,
MQ/S3 y contratos/fingerprints de embeddings y perfil4destinos, con regresión
y CI nueva. No sustituir texto globalmente ni trasladar evidencia española
a bytes cambiados. Paquete ensayo1 anterior no constituye configuración Irlanda.

Evidencia ignorada .work/aws-access/region-quotas.json e ireland-candidate.json.
Consulta MQ corregida de list-broker-instance-options (inexistente) a
describe-broker-instance-options; resultado final conforme. Ningun cambio AWS.

## Preflight inicial y presupuesto aclarado — 22/10/2026

CLI STS confirma cuenta7607/root. Solo lectura: ec2 describe-regions devuelve
España not-opted-in, Paris/Virginia opt-in-not-required. Route53 no devuelve zona
coincidente danteinferno.es; CodeConnections Paris vacio; SecretsManager con
filtro de nombre economicon en Paris vacio (no afirmar ausencia global).
Unica politica IAM local Inicio_Apagado, no boundary del proyecto. Cuota
CodeBuild Paris L-2DC20C30 (Linux/Medium) =0; Terraform usa ese tamaño, solicitar
al menos1 y comprobar aprobacion antes de pipelines. No solicitud enviada.

DNS publico: diva.ns.cloudflare.com y salvador.ns.cloudflare.com. Usuario confirma
acceso Cloudflare y aclara que60EUR es LIMITE TOTAL de gasto, no credito AWS.
No tratar available_credit_eur=60 como saldo/promocion confirmado; paquete
permanece bloqueado. Coste real/estimacion y margen pendientes. No se consulto
Cost Explorer ni se ejecutaron inferencias.

Orden propuesto: cuota+region, identidad/roles/boundary fuera de root, zona y
delegacion de subzona en Cloudflare, CodeConnections/secretos Paris, estimacion
y ventana, plan/autorizacion de bootstrap y ensayo. .work/aws-access guarda
preflight-readonly.json y preparacion-cuenta.md con comandos NO ejecutados.
No mutaciones AWS ni cambios DNS/permisos/recursos en este hito.

## Autenticación CLI comprobada — 22/10/2026

Renovado el flujo que había caducado. El navegador externo lo abre aws login;
la selección en el navegador integrado sí completó el retorno local. CLI informó
perfil economicon-proyecto actualizado. La espera posterior era la pregunta
opcional de instalación de skills/MCP de AWS: respondido n, sin instalar extras.
STS get-caller-identity --profile economicon-proyecto --region eu-west-3
terminó exit0 y confirmó la cuenta esperada y ARN root. Acceso temporal efectivo,
no claves permanentes nuevas. Los párrafos anteriores de login pendiente quedan
superados por esta comprobación. No guardar códigos/URLs de callback ni tokens.
No se ha creado infraestructura ni modificado permisos/roles/regiones.
Antes de desplegar sigue pendiente preparar acceso por roles y los prerrequisitos
externos del runbook; sesión root limitada por acuerdo a comprobaciones de lectura.

## Acceso inicial a la cuenta — 22/10/2026

Usuario confirmó que la cuenta terminada7607 es la destinada al proyecto/60EUR.
Consola abierta como root con MFA; no hay usuarios IAM, hay7roles existentes
de servicios/otros usos. No se han cambiado roles, claves ni políticas.
España no figura en el selector entre regiones activas (17deshabilitadas);
confirmación formal de estado regional pendiente. No habilitada por este turno.

AWS CLI2.38.4 instalado para el usuario en
%LOCALAPPDATA%/Programs/Amazon/AWSCLIV2/aws.exe, MSI oficial de Amazon con firma
Authenticode Valid comprobada y salida0. No se han creado claves permanentes.
Iniciado aws login --profile economicon-proyecto --region eu-west-3; segunda
pestaña de navegador espera selección de sesión por el usuario. Login aún
pendiente, sin get-caller-identity ni preflight CLI ejecutado. No registrar URLs
de autorización, códigos ni tokens. Tras login verificar identidad y limitar
las operaciones iniciales a lectura; preparar accesos de operación por separado,
sin desplegar infraestructura ni ampliar permisos sin revisión concreta.

## Cierre de preparación offline — 22/10/2026

Candidato publicado41cace0daef38f5461cb086a107a94ee95be3759 en PR146
(borrador). [CI técnica39762874111](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39762874111)
SUCCESS: ocho jobs técnicos, incluido processor completo; policy omitida en push.
[SQL nativo chat39762881374](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39762881374)
SUCCESS. Las pruebas locales con cinco fallos de esperado quedan superadas por
la ejecución completa verde del candidato. ZIP limpio del SHA valida receta,
hash de aplicación344e7fd765ed9f59baad45a886104105ace479a5a81b3993097f9c8f0db13091
y cuatro evidencias. Guardas destroy/count corregidas y dictamen incremental
técnico APPROVE; no aceptación real AWS.

Usuario autorizó elegir responsables: Alejandro Aguado liderazgo, Lucia Mateo
pairing, Victor Mendez revisión, Paris Arcos Martin validación. Actualizados
mediante integración Trello DockerServer, tarjeta6ad8e4097bda49d228e90b91,
y PR146; readback conforme. Son asignaciones, no pairing/reviews realizados.
JUP policy SUCCESS en39764363226 tras actualizar esos metadatos; el resto de
ese relanzamiento está en curso sobre el mismo SHA ya probado. JUP reviews sigue pendiente
de Revision JUP-131 y Validacion JUP-131 humanas. Sin merge/cierre de tarjeta.

.work/ensayo1/config.json/readiness.json/start-up.json/start-down.json y
prerequisitos.md preparados para SHA41cace/CI39762874111. aws_deployable=false,
aws_preflight_executed=false, crédito0 y entradas de cuenta/DNS/motores pendientes.
Contenedor PG propio y volumen anónimo retirados tras comprobar etiqueta; túnel
propio PID25980 cerrado. Ningún servicio ajeno modificado.

Se avisó explícitamente: ya es necesaria la sesión con AWS para preparar/verificar
identidad y roles/boundary, conexión GitHub París y referencias Secrets Manager,
España/cuotas/motores/modelos, DNS y saldo/coste/ventana. No se ha accedido a AWS
ni se autoriza despliegue por preparar el acceso; no recoger secretos en chat.
Runbook docs/deployment/aws-defensa.md concreta entradas y secuencia futura.

## Candidato integrado y revisión técnica — 22/10/2026

Desarrollo local ee934326 más develop4567e8e7, recursos JUP132 v4 conservados y
ADR AWS renumerado0027. Receta real release.json, fixtures y checker completos.
Backend Linux2714PASS/369SKIP; processor2666PASS/150SKIP más5fallos de esperado
ledger, corregido a005 y7focalesPASS. Nativo/v4 66PASS;3imágenes construidas y
/tmp privado como uid10001 comprobado con volumen ordinario/raízRO. TF12PASS.
Controlador53casos,52PASS/1SKIP; SQL opt-in previamente comprobado.

Revisión técnica independiente encontró P1: destroy rechazaba política Bedrock
con count[0]. Reproducido RED y corregido con regresión/guardas de ámbito.
Dictamen incremental APPROVE tras comprobar la corrección; las reviews humanas siguen siendo requisito
separado. Publicación y CI del SHA final todavía pendientes en este corte.
No se ha accedido a AWS. Avisar al usuario al estar listo para preparar/verificar
roles, identidad, DNS, CodeConnections/secretos, modelos/cuotas y crédito.
No pedir secretos en chat. Runbook actualizado con entradas externas concretas.
Los pendientes de Nova/develop/receta/imágenes anteriores quedan superados por
este hito; aceptación real en AWS permanece pendiente.

## Fixtures y checker implementados; integración pendiente — 22/10/2026

Turno previo y actual clasificados como progreso: cambios verificables en código
y pruebas. [Evidencia](../evidence/JUP-131-aws-fixtures-checks.md).
Fixture sintético versionado Core12,50EUR/Growth999,99EUR, corpus por tenant y
generaciones Titan1024, reintento sin inferir de nuevo ni sobrescribir conflictos.
Bootstrap secuencial de cinco tareas conectado; no declara application_ready.
6 PASS processor, incluidos dos casos PG/pgvector reales con SDK Bedrock simulado;
bases UUID retiradas. Constructor PgVectorStore acepta motor externo para
conservar connect_args TLS del bootstrap. CI PG incluye esas pruebas.

Nuevo `tools/aws_demo/checks.py`: guardas comunes, estabilidad ECS/ALB/CloudFront,
login Cognito/sub, aislamiento401/403, importe, ingesta Markdown mediante S3/MQ,
chat con cita del nuevo documento y schema/uso. Informe privado sin secretos;
runner lo publica incluso al fallar, READY solo tras éxito. Instrumento probado
con HTTP/SDK simulados, controlador total49PASS/1SKIP(50). No ejecutado en AWS.

Hallazgo previo a receta: Nova exige raíz de tool schema limitada a
type/properties/required; chat actual tiene anyOf/$defs. Próximo paso: envolver
de forma equivalente y adaptar lectura Converse/ConverseStream, conservando
validación y streaming. Fuente exacta en evidencia. No confundir soporte de
toolChoice (confirmado documentalmente) con soporte del schema enviado actual.
Dockerfiles ya declaran VOLUME /tmp con uid10001/modo0700 por contrato ECS;
pendiente build/prueba con volumen normal, no solo tmpfs. No repetir todos los
tests anteriores antes de estos cambios de integración.

Siguen pendientes Nova, develop/JUP-132 v4/ADR, receta, pruebas Linux finales,
CI del candidato y revisión. Todos estos cambios aún locales. Mantener aviso al
usuario cuando se necesite entrar en AWS; todavía queda trabajo offline útil.
Contenedor PG propio/túnel56328 conservados para fixtures; broker propio retirado.

Comprobación posterior: adaptación Nova implementada sin fusionar ramas del
schema. Wrapper response con referencias locales reubicadas, lector incremental
y validación original/duplicados/envoltura. Recibo de tokens nativos completo
independiente de un precio que sigue desconocido. 57 PASS Windows de protocolo,
schema, factories, resumen y revisión privada; Terraform referencia12PASS.
Sustituye el pendiente de implementación Nova anterior. Faltan regresión Linux
del conjunto integrado, receta, develop/ADR, CI final y revisión.

## MQ e identidad de ensayo preparados parcialmente — 22/10/2026

Continúa el objetivo activo, sin despliegue ni llamadas a la cuenta AWS.
El usuario pide aviso cuando sea necesario conectarse para preparar acceso;
todavía no es necesario: quedan datos/corpus, checks y receta verificables offline.
La futura sesión debe preparar acceso por roles y completar las entradas del
runbook; no pedir ni registrar claves en el chat.

Bootstrap ahora ejecuta bases backend/processor, administración MQ y fixtures de
identidad backend. `aws_bootstrap_broker.py` valida HTTPS España, limita respuestas,
no sigue redirects y prepara vhost con marcador de ciclo/SHA y usuarios sin tags
de administración. Contrato probado con transporte simulado; publicación/consumo
con RabbitMQ real todavía pendientes.
`aws_bootstrap_identity.py` crea el usuario Cognito con SUPPRESS y contraseña
permanente; exige sub UUID, correo verificado y marcador custom inmutable antes
de modificar contraseñas. Vincula por sub; rechaza colisiones de correo/usuario,
tenants o membresías y autoriza solo tenant-core, con login local inutilizado.
El cliente permite autenticación administrativa para el checker y excluye el
marcador de atributos escribibles. No se ha llamado a Cognito real.

Verificado en este corte: 20 tests backend PASS (MQ, identidad y bootstrap DB);
la asociación SQL usa SQLite con la migración inicial real, aún sin aceptación PG
específica de esa asociación. Controlador completo de las cuatro tareas probado
con SDK simulado: éxito y fallo MQ, retiro de definiciones y manifiesto sin
credenciales. Terraform referencia 12 PASS con proveedores mock, incluyendo
atributo inmutable y auth administrativa. Logs ignorados `identity-controller`,
`identity-tools`, `identity-terraform`; nuevos tests versionados correspondientes.
La última CI publicada sigue cubriendo 3e543b6f, no estos cambios sin publicar.

Verificación posterior del mismo hito: 20 PASS también en Linux/Python3.12,
sin red/raíz RO/tmpfs; controlador 44 PASS/1 SKIP (45 casos totales).
`test_postgresql.py` ejecutó migraciones, reintentos y asociación de identidad
contra PG16 desechable: PASS, incluido rechazo de membresía conflictiva;
bases UUID y administración temporal retiradas. Prueba AMQP real opt-in
`test_bootstrap_broker_wire_jup131.py`: PASS en RabbitMQ3.13 management,
digest `sha256:e582c0bc7766f3342496d8485efb5a1df782b5ce3886ad017e2eaae442311f69`.
Dos bootstraps consecutivos, publish con confirmación, consumo/ack, denegación de
otra cola y acceso administrativo denegado. Transporte de management loopback
HTTP solo en test; TLS Amazon MQ sigue pendiente del ensayo. Contenedor propio
`economicon-jup131-broker-test` y volumen anónimo retirados tras verificar etiqueta.
Logs `identity-linux`, `identity-pg`, `broker-wire` en el directorio ignorado.
Esto sustituye los pendientes de PG/AMQP de los párrafos anteriores; no acredita
integración AWS ni cierra las otras tareas del objetivo.

Esta sección sustituye los pendientes MQ/identidad/controlador de la sección
anterior solo en cuanto a implementación y pruebas simuladas descritas. Siguen
pendientes fixtures coste/corpus/vectorización, checks reales, receta, integración
develop/JUP-132, CI final y revisión. `application_ready=false` se mantiene.

## Bootstrap DB privado implementado localmente — 22/10/2026

Continúa el mismo objetivo; no es su cierre. [Evidencia y comandos](../evidence/JUP-131-aws-bootstrap-db.md).
Nuevo `tools/aws_demo/bootstrap.py`: guardas CodeBuild/config/identidad,
credenciales persistidas coherentemente para reintentos y secuencia de tareas
privadas backend→processor. `private_tasks.py`: imágenes digest/SG privados,
espera de exit0, parada ante timeout, retirada y manifiesto. Imágenes incluyen
`app.aws_bootstrap` y helper común para migraciones owner/roles SCRAM. Terraform
añade rol/SG separado, bundle SM sin valores, referencia MQ admin y fija modos
verify y Cognito. El SDK del controlador tiene lock explícito instalado por buildspec.

Comprobado: controlador43PASS/1SKIP; backend11PASS más runtime previo106PASS Linux;
processor14PASS; PostgreSQL roles/verify2PASS Windows y Linux, combinado16PASS
Linux. Terraform12+1PASS mock, diff-check conforme. El test de rol reproduce
y corrige TEMPORARY permitido por PUBLIC; ahora deniega tablas temporales,
persistentes y esquemas en las bases de aplicación, conservando DML/login.
Windows venv SDK1.43.117 no tiene el pin1.43.114 en caché offline; la paridad del
lock se comprobó en la imagen Linux instalada1.43.114, no se atribuye ese fallo a código.

Ruling: avanzar la fase SQL/secretos, independiente del modelo generativo,
mientras sigue pendiente integración de JUP-132. No declarar Bedrock ni el
objetivo completo aceptados por cerrar esta fase. Cambios aún sin publicar.
Bootstrap solo implementa fase database y dice application_ready=false.
Down ya incluye barrido de definiciones bootstrap huérfanas: namespace/cuenta y
etiquetas Project/Environment/Purpose/SourceSha exactas, sin tocar otras fuentes;
inventario distingue INACTIVE y no declara coste cero. Dos pruebas adicionales
conformes. Faltan MQ, Cognito/tenants/fixtures/corpus/vectorización, checks, receta
y CI final, además de integración simulada completa del controlador.
Mantener cuenta/DNS/roles/crédito/ventana como entradas externas del runbook.

Recurso local intencionalmente conservado para los próximos tests de fixtures:
contenedor propio `economicon-jup131-native-vector-test`, etiqueta JUP-131,
sin volúmenes y puerto remoto loopback25432. Túnel nuevo handle56328; el anterior
no daba conexión. Al retirar, verificar PID/comando exacto; no tocar otros SSH.
Las bases UUID y roles creados por los tests se eliminan. No hay recursos AWS.

## Runtime privado preparado parcialmente — 22/10/2026

Continuación del objetivo completo de adaptación, sin AWS. Cerradas conexiones
S3 por rol, HMAC en fichero privado y CA/TLS RDS empaquetada; DNS/SG8003 para chat.
Runner incluye permisos/modelos antes del bootstrap y preflight estricto de
metadatos Bedrock; deploy solo puede consultar esos perfiles. Config frontend
Cognito corregida. Ver [evidencia runtime](../evidence/JUP-131-aws-runtime.md).
Este hito sustituye la anotación anterior de contrato no conectado al runner.

Verificado este corte:95PASS Windows y95PASS Linux/Python3.12 sin red, raízRO,
tmpfs y usuario no root;7PASS supervisor processor; controlador30PASS/1SKIP;
Terraform referencia12PASS y bootstrap1PASS con mocks; diff-check conforme.
Código local aún sin publicar, no cubierto por la CI remota3e543b6f.
CA pública oficial España SHA256
`6e4db6870d865a83140270728f62fbdb73202a3a017dc500ae2605e3d17344c0`,
procedencia y rotación documentadas junto a ambos recursos. No hay credenciales
ni certificados privados en Git. Sin llamadas API de cuenta AWS o despliegue.

Siguiente: rol/tareas de bootstrap, modo verify de esquema processor (hoy migra
al arrancar), SQL/MQ/identidad/fixtures/corpus, checks y receta real. Conservar
reconciliación develop/modelo/ADR y CI final como pendientes. No presentar este
hito como aceptación AWS ni como final del objetivo. Paquete sigue no lanzable.

## Verificación de CI y desbloqueo — 22/10/2026

Origen: petición «Comprueba que la CI quede en verde y concreta qué necesitamos
para desbloquear el primer ensayo para desplegar en AWS». Chat ID no disponible.
GitHub consultado: PR146 draft, head `3e543b6fd58283c5d942ce9899fa7a00faa1d985`,
sin reviews/conversación/inline. [CI39681182813](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39681182813)
SUCCESS con ocho jobs técnicos y policy omitido por push. Esta comprobación
supersede las referencias a CI pendiente de los apartados anteriores; no cubre
Bedrock local sin publicar. No se ha integrado ni desplegado.

Fetch develop `4567e8e7`: merge-tree identifica conflicto solo en índice de
continuidad del head publicado. JUP-132 cambia modelo/recursos activos a v4;
revalidar compatibilidad semántica con Bedrock. Colisión ADR-0026 a reconciliar.
Los cambios locales de Bedrock/packaging/vector/IAM siguen en curso; se conservan.
El test nuevo importaba un módulo inexistente: implementado contrato offline
de identidad/perfil EU/destinos exactos; no conectado aún al runner.
Verificación de este corte: unittest controlador27PASS/1SKIP, Terraform10PASS
con mocks y diff-check conforme. Preparación offline vuelve a declarar
`aws_deployable=false`; no sustituirlo por READY.

Lista concreta de bloqueo y criterios en
[runbook, corte22/10](../deployment/aws-defensa.md#corte-de-verificación--22102026).
Pendientes nuestros: completar bootstrap/checks/fixtures/receta, integración y
CI final. Externos: cuenta/rol/boundary, zonaDNS/delegación, conexiónGitHub y ARNs
de secretos, cuotas/motores/modelos, crédito real/estimación y ventanaUTC.
Hora defensa29Oct pendiente. No se han solicitado ni guardado valores secretos,
ejecutado llamadas AWS, iniciado pipelines, aplicado Terraform o hecho merge.

## Adaptaciones autorizadas y en curso — 21/10/2026

El usuario autoriza completar aplicación y scripts para desbloquear el ensayo,
sin desplegar. Se conserva JUP-131/PR146 y el worktree aislado; plan adicional
en [aws-application-adaptations](../planning/aws-application-adaptations.md).
El objetivo completo sigue activo: Bedrock, bootstrap/checks, fixtures y receta
real permanecen pendientes, junto con las entradas externas de cuenta/DNS/IAM/
crédito. No declarar READY por completar estos dos primeros bloques.

PostgreSQL: DSN operativo aceptado y SQL común; integración real PostgreSQL16 con
backend/processor/pgvector, migraciones dos veces y coste EUR12.50 aislado por
tenant PASS. Cockroach24.1.11:50PASS de esquema/chat/reconciliación y4PASS de
resumen tras preparar venv/tokenizer correctos. Ver
[evidencia SQL](../evidence/JUP-131-postgresql.md). CI añade job PostgreSQL real.

Cognito: backend RS256/JWKS y modo explícito; sub firmado debe existir como id
local y las membresías siguen en DB. Sin enlace por email ni login local en ese
modo. Frontend code/PKCE/state/callback, expiración y logout. Backend31PASS,
frontend1397PASS, tipadoPASS, lint0errores/1aviso previo. Ver
[evidencia Cognito](../evidence/JUP-131-cognito.md). Aún sin pool/usuario AWS.

Los tests SQL utilizan exclusivamente contenedores propios desechables
`economicon-jup131-pg-test` y `economicon-jup131-crdb-test`, sin volúmenes;
puertos remotos loopback25432/25433 a través de túneles SSH. No tocar despliegues
existentes. Entornos locales propios en `.work/aws-application/venv` y
node_modules ignorados; estado detallado en `.work/aws-application/progress.md`.
Retirar contenedores y túneles al terminar la validación del objetivo.

Siguiente: Bedrock nativo y coherencia de dimensión/espacio vectorial (TitanV2
ofrece256/512/1024; RAG verificado actual1536), después tareas privadas y guion
funcional. Catálogo público no acredita acceso de la cuenta. Sin AWS/API, DNS,
credenciales cloud, gasto, merge ni dictámenes oficiales. La CI verde anterior
corresponde a7f11f0d2; nuevos cambios requieren su propia CI al publicarse.

## CI/CD implementado sin despliegue — 21/10/2026

Origen: petición directa «Adelante, implementa el CI/CD siguiendo el plan y deja
preparado el primer ensayo, sin desplegar todavía en AWS». Título/ID de chat no
disponibles. [JUP-131](https://trello.com/c/NtiH8R4Z) creada mediante integración
DockerServer; no amplía ni reabre JUP-060/JUP-052. Ejecución asistida bajo Alejandro;
pairing/revisión/validación oficiales pendientes, sin atribuirlas a otras personas.

Base `bc94a4daea98e97b574d00f019d347fc61c2f915`, rama
`feat/JUP-131-aws-cicd-defensa`, worktree `../tfm-economicon-aws-cicd`.
[PR146](https://github.com/EconomiconFinOps/tfm-economicon/pull/146) publicada como
borrador. Primer head5c928f2a; CI Linux detectó h1Linux ausente del lockfile,
corregido mediante providers lock multiplataforma firmado sin cambiarAWS6.13.0.
El resultado remoto posterior queda en PR146; no hay merge ni despliegue.
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
