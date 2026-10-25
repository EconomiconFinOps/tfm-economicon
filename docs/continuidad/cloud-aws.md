# Cloud AWS — arquitectura documental

## Ensayo2: fallo de arranque y retirada en curso — 25/10/2026 19:12 Europe/Paris

Origen: chat «Preparar despliegue en AWS», `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
La infraestructura terminó correctamente y las cinco imágenes se publicaron.
Las seis tareas privadas de bootstrap terminaron con exit0 y limpieza de sus
task definitions, verificadas a las18:57:38 local. Grafana y Azure arrancaron,
pero backend y processor salieron con `StartupError: Chat capacity configuration
is invalid.` La receta de AWS conserva CHAT_MAX_ACTIVE=2 y el código integrado
requiere5–8. No se alcanzó aceptación, ni se declara la aplicación disponible.
Los avisos previos de RabbitMQ siguen pendientes de comprobar una vez resuelto
el arranque; no se ha demostrado todavía la salud AMQP de la aplicación.

Release `fcf9baed-e629-422e-bb87-1a29f19917d0` detenido a las19:01:32.
La primera retirada `9266ef74` falló antes de mutaciones por el lock S3 que dejó
el apply interrumpido. Se verificaron identidad, fuente, configuración, lease
TEARDOWN, proceso STOPPED, ausencia de otros builds/pipelines y ETag. Revisión
independiente favorable48 pruebas offline. Se retiró únicamente ese lock
`2bb9a909-59ed-08e5-d7f2-2de334e62312` a las19:11:49, con ausencia posterior
confirmada. Los recibos de retirada fallida están en `expire-attempt1/`.

Retirada reanudada a las19:12:15: CodeBuild
`economicon-defensa:dee7cab8-9bc5-46f7-a274-933f4dc56e93`, fuente92e792ce y
configuración originales, timeout45/cola5. Antes de retirarlo había169 recursos
en estado; la limpieza aún no está confirmada. Scheduler19:57:15 y permiso exacto
de retirada de la zona privada conservados hasta el cierre verificado.

Corrección local en `fix/JUP-131-aws-chat-capacity`: receta5 para ambos servicios,
validación previa de valores5–8 y coherencia entre componentes. Regresión contra
la función real de capacidad y bloqueo de prepare/runner antes de AWS. La nueva
prueba falló antes del cambio y pasa después; suite del controlador112 pruebas,
103 PASS/9 omitidas, con Python3.14 fuera del problema de ACL temporal del sandbox.
No cambian aplicaciones, ApiError ni starlette1.9.0. Publicación, CI y revisión
independiente pendientes; la excepción PR166 no se extiende a otra PR.

Recibos públicos bajo `.work/master-rehearsal/ensayo2/`:
`bootstrap-public-summary.json`, `runtime-failure-public-details.json`,
`release-stop-request.json`, `retirement-failure-public.json`,
`stale-lock-observed.json`, `stale-lock-review.json`, `stale-lock-recovery.json`
y `expire-start.json`. Los scripts revisados conservan sus hashes. No afirmar
CodePipeline completo ni coste cero; bootstrap permanece separado.

Los cortes siguientes conservan el historial del mismo ciclo.

## Ensayo2: infraestructura lista y aplicación en arranque — 25/10/2026 18:48 Europe/Paris

Apply `economicon-defensa:fe2f28b8-c09b-4272-bd2b-97b6b7b622bf` SUCCESS,
verificado a las 18:48:28. Terraform registra 162 recursos, lease INFRA_READY;
ambas RDS available, privadas y Multi-AZ; RabbitMQ RUNNING. CloudFront
`E13ISJ5NL7INAL` y origen privado `vo_F0UT7XR8dUECtcRPnCf4E3` Deployed.
Se aplicó el plan exacto de 160 altas sobre la VPC y namespace ya gestionados.

Release iniciado a las 18:48:44: CodeBuild
`economicon-defensa:fcf9baed-e629-422e-bb87-1a29f19917d0`, timeout40/cola5.
Fuente y configuración conservadas. La guarda confirmó tiempo suficiente y
el apagado de respaldo de las 19:57:15 antes de arrancar. Pendientes publicación
de imágenes, bootstrap privado, ECS, frontend y aceptación real; aún no afirmar
que la aplicación está disponible. Recibos bajo `.work/master-rehearsal/ensayo2/`:
`infra-apply-progress.json`, `infra-apply-status.json` y `release-start.json`.

Los cortes siguientes conservan el historial del mismo ciclo.

## Ensayo2: importación real completada y plan completo en aplicación — 25/10/2026 18:28 Europe/Paris

Origen: chat «Preparar despliegue en AWS», `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
La revisión independiente v2 fue favorable: 48 comprobaciones offline nuevas,
con los hashes exactos de `ensayo2/operation-review.json`. El reintento administrativo
creó y verificó la zona privada `Z042108134CH6PL7JM3CQ` en VPC
`vpc-0ecece9ac7704a3c0`. AWS devolvió de nuevo el identificador de namespace
`ns-mviwfparozab6kes`, con una operación y zona nuevas; no confundir con la zona
del intento compensado. Sus recibos anteriores están en `namespace-attempt1/`.

La importación declarativa real y el plan completo terminaron SUCCESS a las
18:26:40: CodeBuild `economicon-defensa:cb242c7d-f990-4144-a90c-5ceaad84cac6`.
Terraform gestionaba entonces exactamente la VPC y el namespace. Revisión del
plan completo a las 18:28:01: 160 altas, cero cambios/bajas, recursos preparados
sin cambios; dos RDS PostgreSQL16.9/db.t4g.medium privados, cifrados y Multi-AZ,
RabbitMQ privado CLUSTER_MULTI_AZ y límites de permisos de todos los roles.
Plan SHA256 `609671657df3719317f6e6fc9dd1b5d3870a72b270b228293dfc9c47a3831232`,
versión S3 `RgdwSEFmkw9i9L73Daj7XXaB22IoWGU0`, binding
`DhXGCWKv4sTaD8H8JzUSKHWHSoPGY0bK`. Se aplica ese mismo fichero.

Apply iniciado a las 18:28:30: CodeBuild
`economicon-defensa:fe2f28b8-c09b-4272-bd2b-97b6b7b622bf`, timeout45/cola5.
Fuente `92e792cec74e62f9fe1ae5b609a76fa482757a74`, configuración y caducidad
19:57:15 Europe/Paris conservadas; Scheduler verificado y lease APPLYING.
Aplicación todavía no disponible. Falta éxito del apply, release y aceptación.
La operación sigue siendo asistida; no acredita el CodePipeline completo.
Recibos públicos: `.work/master-rehearsal/ensayo2/import-plan-status.json`,
`infra-review.json`, `infra-apply-start.json` y `namespace-preparation.json`.

Los cortes siguientes conservan el historial del mismo ciclo.

## PR166 integrada y preparación asistida de ensayo2 — 25/10/2026 17:50 Europe/Paris

**Actualización 18:19 Europe/Paris:** import-plan `98fe4c9e` FAILED a las18:12:26.
Terraform CLI import evalúa mapas for_each encadenados de S3/RDS que aún no están
en el estado. No fue un fallo de la cuota ni de creación Cloud Map. Compensación
real completada: namespace `ns-mviwfparozab6kes`, zona `Z05604133DE9RSLZUOUOW`
y permiso temporal retirados; estado sólo VPC, lease APPLYING y Scheduler original
conservados. No se creó el resto de infraestructura.

Fallo reproducido con Terraform1.13.3 y terraform_data, sin AWS: CLI import falla
por el mismo for_each; bloque import y plan dirigido guardado aplican exactamente
una importación y cero altas/cambios/bajas. No prueba aún el importador AWS real.
Recibo `ensayo2/import-reproduction-receipt.json`. Se prepara v2 operativa con
importación declarativa del namespace nuevo, guardas de identidad y plan, eliminación
del bloque en finally y comprobación posterior de dos recursos en estado. Históricos
de scripts/dictámenes preservados en `ensayo2/operational-v1/`; tras la revisión, el
reintento guardará los recibos fallidos en `namespace-attempt1/`. Sin cambiar fuente,
configuración ni caducidad. Delta pendiente de revisión y de ejecución real.

Los cortes siguientes conservan los pasos anteriores del mismo ciclo.

**Actualización 18:10 Europe/Paris:** build de cinco imágenes SUCCESS. Plan VPC
`ae48d70834c1f8dbdd5a33f29c9e8267f034deff8bda6ec18ac631f9f4b4c1ed`, una alta,
cero cambios/bajas, revisado sobre versiones S3 exactas. Scheduler verificado a
las 18:05:11 con fuente `ALfd9WxmBjuSdeoyDaDUNUNl99ze.h0y`, timeout45/cola5,
caducidad19:57:15. Apply VPC `5e4392e1` SUCCESS; VPC `vpc-0ecece9ac7704a3c0`
10.60.0.0/16 verificada, estado inicial de un recurso, lease APPLYING.
Namespace SSO `ns-mviwfparozab6kes`, nombre `economicon-ensayo2.internal`, zona
privada `Z05604133DE9RSLZUOUOW`, identidad/VPC/tags comprobados. Permiso temporal
`economicon-ensayo2-cloudmap-retirement` limitado a Get/Delete de esa zona y
caducidad20:57:15UTC. Importación y plan completo iniciados por CodeBuild
`economicon-defensa:98fe4c9e-6a22-47ef-ba50-84dc60032ee6` a las18:09:53.
Todavía pendientes de éxito; no aplicar el plan completo sin revisar sus bytes.
Recibos `ensayo2/vpc-review.json`, `expiry-protected.json`, `vpc-apply-status.json`,
`namespace-preparation.json` e `import-plan-start.json`. Cierre de política temporal
preparado en `close-zone-permission.py`, revisión independiente33 pruebas PASS;
no ejecutarlo antes de retirada y ausencias verificadas.

Los cortes siguientes conservan los pasos anteriores del mismo ciclo.

**Actualización 17:57:35 Europe/Paris:** revisión operativa independiente favorable,
73 comprobaciones offline. Hashes y límites en
`.work/master-rehearsal/ensayo2/operation-review.json` y `.md`. Configuración
`configs/95e43262a1349eb779acf752b81f53d86bd1225eccbd6b59b3a768e9a9c311ea.json`,
fuente `92e792ce`, estado `economicon/defensa/ensayo2/terraform.tfstate`, caducidad
`2026-10-25T18:57:15Z` (19:57:15 local). S3 subido y hash/versiones verificados;
CodeBuild `economicon-defensa:85892647-b06a-43ef-9d83-4364e464348a` iniciado para
validar y construir cinco imágenes, timeout20/cola5. No nuevo CodePipeline.
Todavía sin VPC/namespace ni aplicación; Scheduler se arma en el plan y se
verifica/pinea antes del apply. Tras destroy normal se necesita cierre administrativo
de la política temporal exacta; no lo hace automáticamente la compensación del
namespace huérfano. La estimación 23,40 EUR se conserva de la misma topología y
ventana de dos horas, no representa una lectura nueva de facturación ni un límite
confirmado de Pontia. Recibos `ensayo2/execution.json` y `build-start.json`.

El corte de las 17:50 que sigue describe la preparación anterior al arranque.

Origen: chat «Preparar despliegue en AWS», `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
El usuario autorizó expresamente la excepción de las dos revisiones humanas y el
bypass de PR166 para `96031072d59d67b1922b3a1e63efa9361317acef`. Integrada por
squash a las 17:25:59 como `92e792cec74e62f9fe1ae5b609a76fa482757a74`; árbol
idéntico al revisado, sin cambiar reglas. CI PR/push y SQL del candidato SUCCESS;
CI de develop `40211640718` SUCCESS. El check de revisiones humanas fallido se
cubre con esa excepción concreta; no se presenta como aprobado automáticamente.
Recibos locales `pr166-merge-receipt.json` y `pr166-final-verification.json` bajo
`.work/master-rehearsal/`. [Autorización registrada en PR166](https://github.com/EconomiconFinOps/tfm-economicon/pull/166#issuecomment-6400139256).

Preflight AWS sólo lectura de las 17:34:49 en la cuenta máster `323188184300`:
64 vCPU Fargate Irlanda, 30 builds medios París, CodeConnection AVAILABLE,
zona pública correcta y sin registros de aplicación en conflicto, acceso de
modelos disponible, clases/versiones RDS y MQ y tres AZ válidas. Se comprobaron
sólo metadatos de los secretos; no valores ni inferencias. Recibo
`.work/master-rehearsal/ensayo2/aws-preflight.json`. Ensayo1 sigue cerrado.

Para el primer despliegue autorizado se prepara una ejecución asistida sobre el
CodeBuild existente: plan de una VPC y apply exacto, creación SSO del namespace
privado de esa VPC, importación, plan nuevo completo y apply del mismo fichero
revisado. Mantiene el lease APPLYING desde la primera mutación hasta INFRA_READY.
El apagado se arma antes de la VPC y se fija a una versión S3 de la fuente, con
45 minutos de timeout y 5 de cola. Sólo se prevé permiso temporal Get/Delete
sobre la zona privada exacta, con caducidad; la zona pública queda fuera.
No es una validación del CodePipeline completo sin asistencia. La creación
automática de Cloud Map con las condiciones IAM actuales continúa sin resolver.

Scripts locales `.work/master-rehearsal/ensayo2/operate.py` y
`remote-operation.py`, aún en revisión. Incluyen recibo durable e idempotencia de
namespace y compensación asistida si no llega a importarse; después de importar
lo retira Terraform. La ventana vulnerable entre creación e importación necesita
esa asistencia. No se ha subido configuración nueva ni iniciado builds o recursos
del nuevo ciclo en este corte. La siguiente operación depende de revisión
favorable de los scripts exactos, fuente/CI fijas y ventana UTC nueva de dos horas.

Los apartados siguientes son cortes históricos superados por este estado.

## Ensayo retirado y correcciones de PR166 — 25/10/2026 16:54 Europe/Paris

Origen: chat «Preparar despliegue en AWS», `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
Terraform terminó la retirada con cero recursos administrados a las 16:35:52.
El build `economicon-defensa:1a946185-0a36-4878-a5c1-1a47f0970ef6` figura FAILED:
la guarda posterior encontró 39 referencias que Resource Groups Tagging API
conservaba tras borrar los recursos. No fue un fallo del destroy. Lecturas de
EC2, ECS y Cognito confirmaron las 39 retiradas; NAT/endpoints deleted, cluster
INACTIVE sin tareas/servicios y restantes objetos ausentes. Auditoría renovada
a las 16:47:50, recibo `recovery-2/authoritative-residual-audit.json`.

Con autorización humana expresa para el cierre y revisión independiente de
44 casos simulados, se verificaron otra vez estado, ausencia de builds activos,
lease y Scheduler exactos. A las 16:47:58 se confirma retirada de la política
`economicon-ensayo1-cloudmap-retirement`, los dos logs RDS (0 bytes declarados),
el Scheduler `economicon-ensayo1` y su lease. Namespace y zona privada ausentes;
ambas bases, RabbitMQ y NAT retirados. Snapshots RDS y backups retenidos vacíos
en lectura 16:36. Se conservan bootstrap, artefactos y estado de control; una
clave KMS y cinco secretos tienen borrado diferido de 30 días. No se afirma coste cero.
No reejecutar los scripts de cierre sobre este estado ya cerrado.

Recibo local `.work/master-rehearsal/recovery-2/final-cleanup-manual.json` y S3
`cycles/ensayo1/0a36a663463a57227da676c40710f9614f73eba2/retirement-manual-verification.json`
en el bucket de control. Mantienen explícitamente FAILED y `manual_closure=true`;
no sustituyen el informe original. La aplicación nunca llegó a estar disponible.

PR166 añade lectura autoritativa para los tipos de residuo observados. Un error
de permisos, timeout, identidad inesperada o recurso desconocido sigue bloqueando
el cierre; sólo ausencia exacta o estado retirado válido permite clasificarlo como
metadatos. Regresión roja previa, luego 105 pruebas offline OK (9 integraciones
omitidas). Revisión detectó además `NatGatewayNotFound`, corregido con regresión.

La CI previa de PR166 falló dos veces en la prueba de proyección de pantalla;
no era un fallo aleatorio: PR164 avanzó develop a `390721f9` mientras el push
probaba la base anterior. El nuevo catálogo de cantidades de pantalla aumentó el
schema esencial y la fixture calculaba el margen sobre pantalla vacía. Base nueva
incorporada; se adapta sólo el presupuesto sintético de esa prueba al schema real
y se exige conservar algunas filas y omitir otras. Límites de producción, ApiError,
Starlette 1.9.0 y código de aplicación no se modifican respecto a develop.
El fichero completo de contexto supera 35 pruebas locales con datos sintéticos.

Actualización tras la CI de `1fb78d609555e51a5353c1f541b6a520046fff0a`:
CI PR `40209401446`, push `40209397897` y SQL `40209401487` SUCCESS. Backend
2732 PASS/369 SKIP, processor 2676 PASS/150 SKIP; PostgreSQL y Grafana reales en
contenedores de CI conformes. Revisión independiente favorable del agente
`/root/review_aws_build_context`; informe local `pr166-final-agent-review-1fb78d60.md`.
Se renueva la receta con huella `3c2a471c9cb35ddafaa8d9a956361f18da5dda53a6e4cb58a1223a15ee997479`,
confirmada también en git archive limpio. [Aceptación offline](../evidence/JUP-131-pr166-application-acceptance.md)
conserva los informes históricos y sus límites. El delta de receta/documentación
posterior no cambia la aplicación. Sus dictámenes y resultados exactos de CI se
enlazan en [PR166](https://github.com/EconomiconFinOps/tfm-economicon/pull/166);
el recibo local de cierre de verificación es `.work/master-rehearsal/pr166-final-verification.json`.

Diagnóstico adicional de Cloud Map: todas las variantes fallidas incluían la
condición `route53:VPCs`; no se probaron CalledVia sola ni ViaAWSService sola.
No afirmar que falta CalledVia ni que se necesitan permisos incondicionales.
La creación administrativa seguida de importación y permiso de retirada sobre
el ARN exacto sí tiene evidencia positiva; mantenerla como alternativa operacional
explícita si no se resuelve la creación automática. Proteger la zona pública y
no reutilizar la simulación IAM como prueba de funcionamiento. No se han cambiado
permisos después del cierre ni creado un nuevo probe.

Siguiente: obtener los dictámenes humanos o una nueva excepción explícita para
PR166, esperar CI del SHA integrado y fijar ventana/configuración nuevas. El
siguiente ciclo será `ensayo2` para no reutilizar nombres de secretos en borrado
diferido. Preparación local en `.work/master-rehearsal/ensayo2/`, bloqueada hasta
fijar SHA/CI de develop, caducidad UTC y paso de Cloud Map. La excepción PR165 no
cubre PR166. No hay ensayo activo ni nuevo plan/apply/release en curso.

Los apartados siguientes son cortes históricos superados por este estado.

## Retirada del ensayo parcial y PR166 — 25/10/2026 16:23 Europe/Paris

Origen: chat «Preparar despliegue en AWS», `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
La creación SSO del namespace real terminó SUCCESS; `ns-i7zfoolrhzpzzoon`,
zona privada `Z06979883KOG825R65CPX`, VPC `vpc-04906b177fcafc9b0`. Importado en
el mismo estado: serial 14, 159 instancias administradas antes de la retirada.
No usar ya el fallback de borrado de namespace huérfano.

El build de recuperación `7f131eb4-0297-4da3-8d16-128e3fa65498` falló por la
guarda del plan: tres altas Cloud Map y una modificación no permitida de
`aws_db_parameter_group.main`, exclusivamente `apply_method` pending-reboot a
immediate. Plan `d2dbcfb23b35ae409d12c6ac4b1c27ffc8ba790222fd975500ea3d7e7973fc86`
rechazado, nunca aplicado. AWS confirma parámetro dinámico, SSL1, método
pending-reboot y ambos PostgreSQL in-sync; recibo
`.work/master-rehearsal/rds-parameter-evidence.json` de las 16:21:36.

Se preparó un override operacional equivalente al ajuste permanente de PR166:
`fe57d673f07ead07023076522578bb609a378dce4ac9d7cc8bfc0ab3e96de905`.
La fuente archivada sigue siendo `0a36a663`; la diferencia de infraestructura
se registra expresamente, sin atribuir identidad íntegra de árbol desplegado.
Revisión independiente favorable: cuatro casos Scheduler, siete de arranque
de retirada y sintaxis/importación. Scheduler actualizado y leído de nuevo a
las 16:16:52: sólo cambia BuildspecOverride; hora 17:02:05, configuración,
cuenta, rol, DLQ y reintentos conservados. Recibo `recovery-2/expiry-protected.json`.

La ventana no permitía completar plan/apply/release con el margen previsto.
No se iniciaron recovery-2 plan/apply ni release. Retirada manual iniciada a
las 16:19:15 con CodeBuild `1a946185-0a36-4878-a5c1-1a47f0970ef6`, fase expire,
misma versión S3, configuración y override. Timeout30min, cola5 y margen5
anteriores al apagado programado; concurrencia real1 verificada. Última lectura
16:22: BUILD/IN_PROGRESS. No se ha confirmado aún eliminación ni estado vacío.

Siguiente: esperar el resultado; verificar inventario/estado vacío, lease y
Scheduler retirados y ausencia de residuos activos; retirar después la política
inline temporal `economicon-ensayo1-cloudmap-retirement` del rol deploy, cuyo
Get/DeleteHostedZone se limita a la zona exacta y caduca a las 19:02:05.
Bootstrap, artefactos y estado de control de París deben conservarse. No afirmar
coste cero: claves/secretos con borrado programado, backups/logs y control requieren
inventario. Si falla, conservar estado y diagnosticar antes de un nuevo destroy.

[PR166](https://github.com/EconomiconFinOps/tfm-economicon/pull/166), candidato
inicial `f74829e9`, declara pending-reboot y añade regresión (rojo13/1, luego
architecture7PASS/fmt). CI remota en curso; reviews humanas pendientes, excepción
PR165 no extensible. ApiError y Starlette1.9.0 intactos. Cloud Map automático
sigue sin resolución permanente: la simulación no prueba su contexto real y
CloudTrail no devuelve CreateHostedZone en la ventana consultada; las llamadas
CreatePrivateDnsNamespace son asíncronas. No afirmar CI/CD integral validado.

Los apartados siguientes son cortes históricos superados por este estado.

## Recuperación operacional del intento 3 — 25/10/2026 15:56 Europe/Paris

La prueba administrativa del DNS privado terminó correctamente: creación SSO,
borrado real por `economicon-defensa-deploy` con Get/DeleteHostedZone limitado
al ARN exacto, operación SUCCESS, namespace y zona ausentes y política retirada.
Recibo `.work/master-rehearsal/cloudmap-admin-recovery/probe-delete-verification.json`.
No se ha ampliado CreateHostedZone. Ambos probes anteriores del rol deploy
fallaron y se limpiaron; la causa precisa del contexto IAM interno sigue sin
demostrarse. Esta es una recuperación operacional, no prueba de CI/CD completo.

Tras revisión independiente favorable de scripts (23 comprobaciones locales y
sintaxis generada), se solicita a las 15:56:42 el namespace del plan aprobado
`economicon-ensayo1.internal`, VPC `vpc-04906b177fcafc9b0`, con las mismas etiquetas
que Terraform. Operación `2pwcbo7emohi7ubdbn77duypgkv2irak-jh7a7wpw` pendiente.
Hasta importarlo no está cubierto por el estado: si falla, ejecutar el fallback
revisado `cloudmap-admin-recovery.py retire-orphan application` y comprobar su
retirada; nunca borrar por ese camino un namespace presente en estado.

Recuperación preparada en `.work/master-rehearsal/recover-partial-apply.py`:
fuente archivada aprobada `0a36a663`, misma configuración/ciclo/estado, import
`NAMESPACE_ID:VPC_ID`, prefijo `recovery-1`, plan completo con exactamente tres
altas Cloud Map y ninguna modificación/baja. Aplicación sólo de los mismos bytes
cuyo hash se revisó; lease APPLYING hasta transición condicional INFRA_READY.
Release usa el runner y las cinco imágenes originales. Scheduler UTC 16:02:05
conservado; builds limitados a 10/10/35 minutos, cola 5 y margen de 15. Con esa
guarda release debe iniciarse antes de 16:07:05 Europe/Paris. No se ha lanzado aún.
La política temporal sobre la zona real, cuando se añada, deberá retirarse tras
el destroy normal: el runner no la administra. Aplicación no disponible todavía.

## Intento 3: fallo real de DNS privado — 25/10/2026 15:31 Europe/Paris

Actualización 15:54: dos pruebas reales con el rol deploy (`ViaAWSService` +
VPC exacta y después sólo VPC exacta, ambas temporales) fallaron con el mismo
ACCESS_DENIED. Las dos fueron retiradas: namespace, zona y política ausentes.
Esto no demuestra qué contexto interno evalúa Cloud Map; no se ha concedido
CreateHostedZone sin restricciones. Se prepara recuperación operacional con
la fuente aprobada intacta: creación SSO del namespace exacto, importación
`NAMESPACE_ID:VPC_ID` al mismo estado, plan separado con sólo tres servicios
Cloud Map y aprobación del hash de los mismos bytes que se aplicarán.

Prueba previa de retirada: SSO creó `economicon-ensayo1-admin-probe.internal`,
namespace `ns-gssdzcywqdriywgn`, zona privada `Z0292811SIRBSXXT6RO4`, VPC
`vpc-04906b177fcafc9b0`. Política temporal `economicon-ensayo1-cloudmap-retirement`
sólo permite Get/DeleteHostedZone sobre ese ARN hasta 19:02:05 Europe/Paris;
se quitará al confirmar retirada. CodeBuild `b8adc050-217e-4a3f-8385-6e8b2386753c`
comprueba el borrado desde deploy; todavía pendiente a este corte. El namespace
real aún no se ha creado. Scripts/recibos en `.work/master-rehearsal/cloudmap-admin-recovery/`
y `recover-partial-apply.py`. Agente independiente revisa guardas e importación;
incluido fallback de retirada por ID si queda un namespace fuera del estado.
No se ha integrado código nuevo ni reutilizado una aprobación de plan anterior.

Actualización 15:36: pipeline FAILED, confirmado a las 15:34:21; apply terminó
con 158 recursos en estado serial 13. Diagnóstico final confirma el fallo de
Cloud Map; ambos RDS available/Multi-AZ, RabbitMQ RUNNING y CloudFront creado.
Estado, bloqueo APPLYING y Scheduler conservados. Prueba temporal de permisos
preparada, todavía sin ejecutar, con caducidad y VPC exacta del ensayo.

Origen: chat «Preparar despliegue en AWS», `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
Operación Cloud Map `2pwcbo7emohi7ubdbn77duypgkv2irak-jh7a7wpx`, iniciada
15:14:39, termina FAIL/ACCESS_DENIED: el rol `economicon-defensa-deploy` no
puede ejecutar `route53:CreateHostedZone`. La política aplicada coincide con
el hash revisado. No hay namespace ni zona privada en el estado. La simulación
verde suministraba artificialmente `aws:CalledVia` y `route53:VPCs`; no demuestra
que la llamada real incluya ambos. El proveedor 6.13.0 sí envía la VPC a Cloud
Map y espera su operación. El formato VPC coincide con la documentación AWS.
No se ha demostrado todavía cuál de las condiciones falla. Recibo público:
`.work/master-rehearsal/cloudmap-live-readonly.json`; revisión independiente
de `/root/review_aws_build_context` coincide en esa limitación.

A las 15:29:21: estado serial 8 con 148 instancias; RabbitMQ RUNNING, ambos
PostgreSQL privados Multi-AZ terminando configuración/copia inicial y tres NAT
available. La ejecución `d76e2632` sigue en apply esperando los recursos ya
iniciados. Bloqueo APPLYING y Scheduler ENABLED hasta 17:02:05 conservados.
Las lecturas/cifrado S3 y la transición DynamoDB han funcionado realmente.
Aplicación, release y aceptación aún pendientes. Antes de recuperar se requiere
diagnóstico real, plan nuevo sobre el estado parcial y revisión; no reutilizar
el plan inicial ni liberar el bloqueo como en los intentos 1/2. Si no se completa
en la ventana, tramitar retirada con el estado conservado y verificar residuos.

Los apartados siguientes conservan su corte histórico.

## PR165 integrada; intento 3 en apply — 25/10/2026 15:12 Europe/Paris

Origen: chat «Preparar despliegue en AWS», `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
El usuario respondió «Sí, integrar PR165 con esa excepción» para el candidato
`0eafcc3d5ec430aa19856d3789b08836e8b52c28`. Excepción a los dos dictámenes
humanos y bypass limitados a esta PR/head; reglas del repositorio conservadas.
CI técnica PR `40198638031`, push `40198374987` y SQL `40198378762` SUCCESS;
agente `/root/review_aws_build_context` APPROVE del candidato completo. Lectura
de conversación, reviews e inline sin comentarios pendientes. `JUP reviews`
continuaba FAILURE por dictámenes humanos ausentes; no se atribuyen como hechos.

Merge a las 14:49:48 como `0a36a663463a57227da676c40710f9614f73eba2`, árbol
idéntico al revisado. Corregida la codificación de tildes del registro público;
esa edición relanzó la CI de PR ya integrada y canceló la CI develop por
concurrencia. Duplicado `40199574776` cancelado y CI push `40199406946`
relanzada: intento 2 SUCCESS sobre el SHA integrado. Ningún cambio de código adicional.

Plan bootstrap renovado a las 14:52:21: 0 altas, una actualización de
`aws_iam_role_policy.deploy`, 0 bajas. SHA256 de la política renderizada
`192e51b077c09b8f1da8ca8a2e79bf5f1e30d7c21848a2914ccf2c25a5fba584`, idéntico
al probado. Aplicado a las 15:01:37: 0 altas, 1 cambio, 0 bajas; lectura IAM
posterior confirma el mismo hash. SSO del máster válida, cuenta `323188184300`, cuota
Fargate Irlanda 6, CodeBuild París 30, conexión GitHub AVAILABLE y DNS nuevo
confirmados a las 14:38. Antes del arranque se vuelve a comprobar identidad,
cuota, ausencia de estado/bloqueo/Scheduler y de ejecuciones up activas.
Bootstrap conservado. ApiError y Starlette 1.9.0 permanecen intactos.

Intento 3 `d76e2632-5502-4671-94a2-34a673131b3f` iniciado a las 15:02:07
con fuente `0a36a663` y CI `40199406946`. ConfigKey
`configs/d4c916914c46f962bf87e5dec0ee6e0daeb7990aa2d9c786398e3d1167f6cc94.json`,
caducidad `2026-10-25T16:02:05Z` (17:02:05 Europe/Paris). Preparación local
deployable sin bloqueos; digest de aplicación conservado. Validación y cinco
imágenes SUCCESS. Plan de 162 altas/0 cambios/0 bajas revisado, incluyendo dos
PostgreSQL privados/cifrados Multi-AZ, RabbitMQ privado CLUSTER_MULTI_AZ, tres
NAT, ALB interno, CloudFront y nueve roles con boundary. Sin servicios ECS de
aplicación en esta fase. Binding, configuración y fuente exactos; plan SHA256
`f2189677537e368440397af748f2c373a56a3619fcedb9654b9587c0c57dd708`.
Scheduler ENABLED con fuente/configuración/caducidad nuevas confirmadas.
Aprobación enviada a las 15:12:32 bajo autorización vigente de primer
despliegue. Apply en curso; aplicación aún no disponible. Siguiente paso:
vigilar creación y release, comprobar aplicación y retirada.
Hito 15:15:04: transición DynamoDB real a APPLYING correcta; estado S3 presente
con 104 instancias gestionadas. Dos PostgreSQL 16.9/db.t4g.medium Multi-AZ
privados en creación, RabbitMQ CLUSTER_MULTI_AZ en creación y tres NAT pending.
Scheduler sigue ENABLED. Ya existen recursos de aplicación: no tratar esta
ejecución como los intentos 1/2 sin infraestructura ni liberar su bloqueo;
ante fallo conservar estado y tramitar retirada verificada.
No reutilizar configuración ni aprobación del intento 2.
Recibos en `.work/master-rehearsal/pr165-ci-receipt.json`,
`pr165-agent-review.json`, `pr165-authorization.json`, `pr165-merge-receipt.json`,
`bootstrap-permissions-plan-review.json`, `bootstrap-permissions-apply-receipt.json`,
`pr165-develop-ci-receipt.json`, `ensayo1-execution.json`, `infra-plan-review.json`
y `attempt3-infra-approval-receipt.json`. Trello actualizado por DockerServer,
comentario de arranque `6ade0c29763e098b7e1e1264`; historial y columna conservados.

Los apartados siguientes conservan su corte histórico.

## PR165: corrección del bloqueo y permisos dependientes — 25/10/2026

Origen: mismo chat «Preparar despliegue en AWS», `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
PR165 <https://github.com/EconomiconFinOps/tfm-economicon/pull/165> añade alias
DynamoDB y permisos dependientes de Route 53, S3 e IAM para el proveedor Terraform.
El segundo fallo fue DynamoDB antes de apply; la carencia DNS se confirmó después
mediante simulación IAM de la política actual, sin provocar un despliegue parcial.
Sólo llamadas delegadas por Cloud Map; creación privada con VPC de Irlanda,
DNS público directo limitado a la zona ya aprobada. Se añaden cuatro lecturas S3
y configuración de cifrado sólo en los prefijos del ensayo, y consulta de
perfiles sólo para roles economicon. Deny de bootstrap conservados. La simulación
de la política anterior reproduce diez rechazos; el ajuste final se evalúa con
32 escenarios IAM, todos PASS; Access Analyzer sin hallazgos, suite88PASS/9SKIP
y Terraform mock1PASS. Plan bootstrap0altas/1política/0bajas, todavía sin aplicar.
Operaciones reales de Cloud Map/S3/retirada pendientes del ensayo.

Revisión de agente favorable para `e57550e6` sólo sobre DynamoDB; CI técnica PR
`40196473065`, push `40196469214` y SQL `40196473137` SUCCESS para ese head.
El nuevo delta IAM requiere revisión/CI propias antes de integrar. `JUP reviews`
FAILURE por revisiones humanas ausentes; excepciones PR161/163 no lo cubren.
Sin aplicación, bloqueo ni Scheduler activos. Bootstrap/artefactos conservados.
Evidencia y referencias: [correcciones](../evidence/JUP-131-dynamodb-lease.md).

## Segundo intento: condición DynamoDB corregida — 25/10/2026 14:09 Europe/Paris

Origen: mismo chat «Preparar despliegue en AWS», `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
La ejecución `2855d9da` terminó Failed en apply antes de inicializar Terraform.
Error confirmado: DynamoDB ValidationException, `cycle` es reservado en la
ConditionExpression de transición PLANNED→APPLYING; bloqueo conservado PLANNED.
Se corrigió el alias tanto al actualizar como al liberar el bloqueo, preservando
las condiciones de ciclo/SHA/ConfigKey/fase. Cuatro pruebas de contrato y
concurrencia primero rojas, después suite88PASS/7SKIP. Prueba DynamoDB real
roja/verde con actualización sin cambio de fase y lectura consistente idéntica.

Retirada de control14:09:29: tras comprobar pipeline Failed, ninguna ejecución
up activa, estado ausente y sin recursos etiquetados de aplicación, se invalidó
el plan aprobado, se eliminó sólo su Scheduler y se liberó condicionalmente
su bloqueo. Bootstrap y artefactos conservados; ya no existe la caducidad15:52
de ese intento. Próximo ensayo requiere nuevo SHA/CI/configuración/ventana.

Rama `fix/JUP-131-dynamodb-lease-aliases`; revisión/CI/integración pendientes.
La autorización de bypass de PR163 era exclusiva de esa PR/head y no se extiende
a esta corrección. Evidencia: [DynamoDB lease](../evidence/JUP-131-dynamodb-lease.md).
Recibos `.work/master-rehearsal/lease-live-red.json`, `lease-live-green.json`,
`attempt2-control-retirement.json`; snapshot en `attempts/2/`. ApiError,
Starlette1.9.0, arquitectura y permisos intactos. Aplicación AWS no disponible.

## PR163 integrada con excepción nueva — 25/10/2026 13:44 Europe/Paris

Origen: mismo chat «Preparar despliegue en AWS», `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
El usuario autoriza expresamente «Sí, integrar PR163 con esa excepción» tras
identificar el head `f48a72e817aa0cbc9f3959826008be6ff51aed53`, el build real,
CI técnica/SQL y la revisión independiente. Excepción a las revisiones humanas
y bypass limitados a PR163/head; ninguna regla del repositorio modificada.
No se atribuyen reviews humanas ni se declara verde `JUP reviews`, que fallaba
por los dos dictámenes ausentes. Conversación, reviews e inline leídos, vacíos.

CI técnica PR `40193776368`, push `40193771005` y SQL `40193776351` SUCCESS.
Agente `/root/review_aws_build_context` APPROVE del head final; evidencia
atribuida en el cuerpo de PR163. Merge completado a las13:44:53 como
`6851ec7aa6b477b8c1859cb325126777c1c7994b`, árbol idéntico al revisado.
CI push develop `40194488245` SUCCESS. Reintento
`2855d9da-f725-443f-94c2-e6287f7c71a5` iniciado13:52:38 Europe/Paris con nueva
ventana hasta `2026-10-25T14:52:34Z` (15:52:34 local). ConfigKey
`configs/21d87ff3a7657a5f55cbc8c05492dc732bd47d66137caafb1a3cedd9b34b416e.json`,
fuente6851ec7a y CI exacta; digest de aplicación conservado. Antes del arranque
se volvieron a comprobar cuenta, cuota6, ausencia de estado/lease/Scheduler
y ninguna ejecución up activa. Validación/build/plan todavía pendientes;
la retirada programada debe verificarse cuando plan la cree.

Hito14:01: validación y build de las cinco imágenes SUCCESS. Plan real162altas,
0cambios y0bajas: dos PostgreSQL16.9/db.t4g.medium Multi-AZ privados/cifrados,
RabbitMQ3.13/mq.m5.large CLUSTER_MULTI_AZ privado, tres NAT, ALB interno,
CloudFront/WAF, identidad y soporte ECS; nueve roles con boundary del máster.
Sin servicios ECS de aplicación en esta primera fase. Binding/config/fuente
verificados; SHA256 `4b65a10202a72f7ff96dcfcc994ce5bfba66a6e566baaaf17e235c318a944146`.
Scheduler `economicon-ensayo1` ENABLED con caducidad exacta y configuración/fuente
del reintento. Aprobación enviada14:01:41 bajo autorización de primer despliegue;
apply en curso. Recibos `infra-plan-review.json` e `infra-approval-receipt.json`.
Plan binario privado bajo ACL local; no valores de secretos en recibos públicos.

Recibos: `.work/master-rehearsal/pr163-ci-receipt.json`, `pr163-merge-receipt.json`
y `trello-pr163-merged-receipt.json`. Trello actualizado por la integración
DockerServer; evidencia detallada en comentario `6addfa9fa587346b41f86f98`,
resumen en descripción y todo el historial conservado. El intento1 sigue
archivado; no había aplicación, lease, estado ni Scheduler a las13:34.

## Ensayo1: validación correcta y corrección del build Azure — 25/10/2026

Origen: mismo chat «Preparar despliegue en AWS», `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
Bootstrap aplicado: 4 roles importados, 23 recursos creados, 4 actualizados y
0 destruidos. Estado migrado a S3 en París, clave separada
`economicon/bootstrap/terraform.tfstate`, AES256/versionado/lockfile; plan
posterior sin cambios. Bucket `economicon-defensa-control-20261025121111843900000002`.

Al crear los pipelines AWS lanzó dos ejecuciones con `configs/NOT_READY.json`.
Ambas fallaron antes de ejecutar el controlador: el secreto GitHub contenía
el token entre llaves sin clave JSON. Se corrigió su estructura a la clave
`token`, conservando el valor exactamente y la versión anterior en Secrets
Manager. Procesado sólo en memoria; ningún token en logs, archivos o mensajes.
El recibo público describe formato/resultado, nunca el valor.

Primer intento real: ejecución `0c9fb3aa-5e75-492a-a187-073ece7e70ce`, iniciada
13:17:22 Europe/Paris, fuente `2087855c`, CI40191355921, ventana hasta
`2026-10-25T14:17:20Z` (15:17:20 local). Validación del runner SUCCESS a13:19,
incluida autenticación GitHub, cuotas y contrato. Backend/processor construidos;
build Azure falla porque el contexto `apps/azure-cost-api` no contiene los
`COPY apps/azure-cost-api`, `docs/api` y `fixtures/azure-cost` del Dockerfile.
No se alcanzó plan/apply/release: infraestructura de aplicación y Scheduler
del ensayo no creados. El bootstrap/control y los dos tar de imágenes permanecen.

Corrección en `feat/JUP-131-aws-build-context`: Azure usa raíz como ya hace
Compose; processor conserva su carpeta y los demás contextos permanecen.
Prueba contra los COPY reales de las cinco imágenes: falla primero en las
cinco rutas Azure y pasa tras el cambio. Suite offline:84 PASS/7 SKIP.
Build real linux/amd64 y contenedor sin red conformes: archivos presentes,
Starlette1.9.0 y UID10001; contenedor y etiqueta temporal retirados. Aplicación,
ApiError, requisitos y receta de aceptación intactos. Revisión/CI/integración
de esta corrección pendientes; el bypass anterior sólo cubría PR161/e4ac8461.
PR de corrección: <https://github.com/EconomiconFinOps/tfm-economicon/pull/163>.
Revisión técnica independiente de `bcb42f15` favorable; su prueba dirigida pasa
en el candidato y reproduce las cinco ausencias al restaurar en memoria el
contexto anterior. El índice se corrige para distinguir cortes históricos.
Lectura AWS13:34 confirma ausencia de estado/lease/Scheduler del ensayo y de
recursos etiquetados del ciclo en Irlanda/Virginia. Recibo y configuración del
intento conservados en `.work/master-rehearsal/attempts/1/`.

Evidencia versionada: [corrección de contexto](../evidence/JUP-131-aws-build-context.md).
Recibos locales `.work/master-rehearsal/`: `bootstrap-apply-receipt-20261025.json`,
`bootstrap-state-migration-20261025.json`, `github-secret-format-20261025.json`,
`ensayo1-execution.json`, `ensayo1-status.json`, `azure-build-context-docker-receipt.json`.
Trello actualizado por su integración DockerServer al arrancar. No reutilizar
la configuración del intento fallido tras integrar: fijar nuevo SHA/CI y
ventana, conservar este historial y revisar de nuevo el plan real.

## Primer despliegue autorizado: sesión, integración y bootstrap — 25/10/2026

Origen: «Preparar despliegue en AWS», chat `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
El usuario confirma la renovación SSO y autoriza expresamente el bypass de
administrador exclusivamente para el head `e4ac8461` de PR161, bajo la excepción
de agentes documentada. Merge completado a las 13:02 Europe/Paris como
`2087855c81319ef6fbc2bc82bbf7148b192065ad`; árboles Git idénticos al head revisado.
No se han modificado reglas del repositorio. CI push develop `40191355921`
SUCCESS, y CD DockerServer automático `40191355988` SUCCESS, comprobados 13:10.

STS confirma la sesión SSO y la cuenta única `323188184300`. Preflight de sólo
lectura a las 13:05 Europe/Paris: Fargate Irlanda aplicada6vCPU, CodeBuild Medium
París30, CodeConnections AVAILABLE, zona pública del máster sin destinos de
aplicación conflictivos, modelos Nova/Titan autorizados por metadatos y clases
RDS/MQ disponibles. No se han invocado modelos ni leído valores de secretos.
DNS público conserva los cuatro NS verificados a las 12:42. El token GitHub
almacenado sirve a las lecturas de CI; AWS usa SSO temporal.

Plan bootstrap actualizado y revisado: 4 importaciones de roles existentes,
23 altas, 4 cambios de descripción/tags y 0 destrucciones. SHA256 del plan:
`b8635190c207d7336846378d9bb0db1c91437dbf759d8b01ec9fe21fef14bffd`.
Su código coincide con la versión revisada. Aplicación iniciada tras comprobar
cuenta, hash, fuente y CI exacta; resultado aún pendiente en este corte.
Después: migrar estado bootstrap a su clave S3 separada, configurar ventana
UTC del ensayo, arrancar up y revisar el plan antes de aprobar su aplicación.

Recibos locales sin secretos: `.work/master-rehearsal/merge-receipt-20261025.json`,
`develop-ci-20261025.json`, `aws-preflight-20261025.json`,
`bootstrap-reviewed-plan-20261025.json` y `bootstrap-apply-receipt-20261025.json`.
Los apartados siguientes conservan cortes anteriores; las esperas de acceso
y autorización de merge del siguiente apartado ya están resueltas.

## Inicio del primer ensayo y renovación de acceso — 25/10/2026

Origen: «Preparar despliegue en AWS», chat `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
El usuario solicita ahora realizar el primer despliegue en AWS y pregunta si
el token del día anterior sustituye las credenciales. Destino único conservado:
Economicon del máster `323188184300`. Esta petición sustituye la restricción de
no desplegar del hito anterior; no elimina las verificaciones del ensayo.

El token GitHub almacenado en Secrets Manager sirve a la comprobación de CI;
no autentica AWS. Se reutiliza el perfil SSO `economicon-master-audit` mediante
`AWS_CONFIG_FILE=.work/aws-access/master-audit-config`, sin claves estáticas.
STS devuelve `Token has expired and refresh failed`. Renovación iniciada con
`aws sso login --profile economicon-master-audit --no-browser` y abierta en el
navegador integrado; pendiente de que el usuario complete el acceso. No guardar
URL OAuth, códigos ni tokens en documentación.

GitHub vuelve a confirmar todos los checks SUCCESS del head `e4ac8461`, sin
reviews, comentarios ni cambios solicitados. El merge normal fue rechazado por
el ruleset de develop: exige una aprobación de otra cuenta y aprobación del
último push. Se ha pedido autorización explícita para el bypass de administrador
de ese commit, amparado en la excepción de agentes; respuesta pendiente. No se
ha integrado ni cambiado ninguna regla. Tras integrar, esperar CI push del SHA
exacto de develop y regenerar las solicitudes con ese SHA y la ventana UTC.

DNS público verificado a las 12:42:58 Europe/Paris: 1.1.1.1 y 8.8.8.8 devuelven
los cuatro NS de la zona del máster. Recibo sin secretos:
`.work/master-rehearsal/dns-preflight-20261025.json`. El código del bootstrap
local coincide por SHA256 con `infra/aws-bootstrap/main.tf`; el plan del 24/10
no se reutiliza sin refrescarlo y revisarlo. El próximo paso, tras renovar SSO,
es confirmar identidad, cuotas y prerrequisitos, generar/revisar el plan actual
y ejecutar el bootstrap y ensayo autorizados. Aún no se han creado recursos,
iniciado builds/pipelines AWS ni desplegado la aplicación en esta fase.

## PR161 reconciliada y aceptación offline renovada — 25/10/2026

Origen: «Preparar despliegue en AWS», chat `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
Autorización: reconciliar PR161 con `0edd11ef`, conservar ApiError/pin, CI verde
y configuración del ensayo en la cuenta del máster; sin despliegue.

La rama `feat/JUP-131-atlas-ecs` incorpora la base aprobada mediante merge
`0ddd59f5`. ApiError vuelve al blob aprobado
`a5ff184e4729d2248a3ff12c3001f3076f2ccdff`; se retira la regresión exclusiva de
la corrección mutable y se conserva `starlette==1.9.0`. Carrusel/viñetas y
Atlas/Grafana/carga aditiva se mantienen. El conflicto del índice se reconcilia
preservando los temas de ambas ramas.

`da13f069` tiene CI PR `40187165537`, push de rama `40187163124` y SQL
`40187165282` **SUCCESS**, comprobados el 25/10. Backend 2732 PASS/369 SKIP,
processor 2674 PASS/150 SKIP, frontend 1427 PASS y Azure 81 PASS. PostgreSQL
real: 45 controles vectoriales + 8 operacionales/Atlas; Grafana real con TLS,
19/1688, tres dashboards y reinicio correcto. Las omisiones, avisos, enlaces y
límites están en [aceptación offline](../evidence/JUP-131-pr161-reconciliation/application-acceptance.md).
La receta conserva las cinco evidencias históricas y añade ese recibo; huella
de `apps/`: `5e19f3f4ff0db6039ebc42b2733d9dd4266e94b55c6fc8fac741c21876461e70`.
No acredita imágenes finales, Cognito/Bedrock real ni disponibilidad AWS.

La excepción de agentes de PR161 se implementa en `JUP reviews` con alcance
exacto de PR/repositorio/autor/ramas/roles, dos informes con hashes y candidato
común; cualquier delta posterior fuera de la publicación documental exige
revalidación. El coordinador corrigió el primer ID ambiguo del título; la
revisión independiente detectó roles duplicados por mayúsculas, también
corregidos y probados. Las solicitudes de cambios de GitHub siguen bloqueando;
no se fabrican reviews humanas ni se cambian branch protections. Candidato de
cierre `812697387918c25e905a240fa35573091d9fdc16`; informes y estado de publicación
en [evidencia de reconciliación](../evidence/JUP-131-pr161-reconciliation/README.md).

Cuenta única `323188184300`. La política `master-account-authorized-2026-10-24`
retira exclusivamente para ella el requisito de 30 EUR, según autorización
humana previa. No declara saldo ni límites de Pontia; conserva estimación,
caducidad, cuotas, identidad, aceptación y CI exacta. Otras cuentas mantienen
la guarda de presupuesto verificado. AWS Budgets existente no se modifica.

`.work/master-rehearsal/` contiene configuración/solicitudes regeneradas,
`regeneration-receipt.json` con SHA/hash de artefactos y `preflight-summary.json`.
El recibo `.work/pr161-reconciliation/final-ci-status.json` registra la consulta
de CI del head publicado; distinguirlo de los runs anteriores. No iniciar las
solicitudes: falta integrar PR161 con autorización, CI push del SHA exacto de
develop y fijar la ventana UTC (máximo 8h) al autorizar el ensayo. El futuro
bootstrap/control necesita revisar/aplicar su plan; roles actuales sólo trust.
Token/modelos, IAM, cuotas y DNS se vuelven a comprobar en el preflight real.
Los prerrequisitos AWS/DNS mantienen la fecha de lectura del 24/10; esta labor
no accedió a AWS, secretos, inferencias, builds/pipelines ni apply/destroy.

## Versión aprobada de aplicación y conciliación con ECS — 25/10/2026

**Histórico previo; reconciliación realizada en el hito superior.**

Origen: «Preparar despliegue en AWS», chat `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
El usuario aprueba expresamente `0edd11eff3458683553bd4c36f3011b77c1d3de4`.
GitHub confirma [PR162](https://github.com/EconomiconFinOps/tfm-economicon/pull/162)
MERGED, con ese squash como punta actual de `develop`. Incluye el carrusel
adaptable, las viñetas violetas y `starlette==1.9.0` en la API simulada de Azure.
El blob de `ApiError` es idéntico al de la base `ffb5d307`:
`a5ff184e4729d2248a3ff12c3001f3076f2ccdff`.

Verificación por lectura de GitHub el 25/10:

- [CI push de develop](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40137719699)
  SUCCESS sobre el SHA aprobado; el log del job Azure `121002689815` confirma
  Starlette 1.9.0 y `81 passed, 1 warning`.
- [SQL de la PR](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40136533801)
  SUCCESS sobre su head `b4781b9738a43eeaa6b8843dc411595e15fd7cee`; distinguir
  ese corte de la CI del squash anterior.
- La excepción de agentes y el bypass puntual de reviews constan en el
  [comentario de integración](https://github.com/EconomiconFinOps/tfm-economicon/pull/162#issuecomment-6390181431).
  `JUP reviews` quedó fallido en esa PR; su integración está confirmada y no se
  presenta el bypass como un check superado.

Atlas, Grafana ECS y la carga aditiva siguen en **PR161**, abierta sobre
`30d4370a` y pendiente de integración. Esos archivos no existen en `0edd11ef`.
Una simulación `git merge-tree --write-tree --name-only HEAD origin/develop`
detecta un único conflicto textual en `docs/continuidad/README.md`, sin tocar
el checkout. Aunque se fusiona automáticamente, el cambio de `ApiError` de
PR161 contradice la versión aprobada: al reconciliarla se debe conservar el
pin de PR162 y retirar el delta anterior de `errors.py` y su prueba asociada.
Los informes de ese delta se conservan como históricos, no como requisito de
la nueva versión. No se ha modificado ni integrado PR161 en esta actualización.

Cuenta destino única `323188184300`. La selección aprobada y sus evidencias
quedan en `.work/master-rehearsal/approved-source.json`; el resumen de
preflight y su README se actualizan. `config.json` y las solicitudes de
arranque todavía corresponden a e730 y **no se deben ejecutar**: primero
reconciliar y validar ECS con esta base, fijar el candidato final, actualizar
su aceptación/digest y regenerar las solicitudes con su CI y ventana.
No se ha iniciado ningún recurso, build, pipeline ni despliegue AWS.

## Destino único: cuenta del máster; seguimiento original cancelado — 25/10/2026

Origen: «Preparar despliegue en AWS», chat `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
El usuario indica que se descarte la cuenta original y que el despliegue se
realice en la cuenta recibida el día anterior: **Economicon `323188184300`**.
La preparación continúa allí, con aplicación en Irlanda (`eu-west-1`) y
control CI/CD en París (`eu-west-3`). Las cuotas de 6 vCPU Fargate y 30 builds
concurrentes corresponden a las comprobaciones del 24/10; no se han vuelto
a consultar en esta actualización.

Se elimina mediante la herramienta de automatizaciones el seguimiento
`vigilar-respuesta-aws-y-cuota-fargate-irlanda` de `605600557607`, con resultado
confirmado `deleteStatus=deleted`. No solicitar más login de esa cuenta ni
comprobar su caso `179267775500075` o su cuota como condición del ensayo.
La pestaña de inicio de sesión creada para ese seguimiento queda cerrada.
El estado local se conserva como cancelado, con sus últimos datos históricos;
esto no implica aprobación ni cierre del caso en AWS. Recibo sin secretos:
`.work/aws-access/fargate-monitor-cancelled-20261025.json`.

Esta decisión fija el destino; no inicia un despliegue ni modifica recursos
AWS. Se mantienen pendientes la aceptación/integración de PR161 y la
regeneración de la configuración del ensayo con el candidato y ventana finales.

## Monitor de la cuenta original: sesión requerida — 25/10/2026 00:03 Europe/Paris

**Histórico, superado por la decisión superior: ya no se requiere intervención.**

Origen: «Preparar despliegue en AWS», chat `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`,
automatización `vigilar-respuesta-aws-y-cuota-fargate-irlanda`.
Las consultas web al caso `179267775500075` y a la cuota `L-3032A538` de Irlanda
redirigen a AWS Sign-In. No se ha obtenido un valor actual de cuota ni leído
una respuesta nueva. Estado actual **desconocido**, conservando como histórico
0 vCPU confirmado el 24/10 a las 21:59:37 Europe/Paris y el último mensaje AWS
del 22/10 a las 16:12:03. La CLI original continúa sin renovación y no se usó.

Hace falta iniciar sesión en la cuenta original `605600557607` en el navegador
integrado; la pestaña de cuota queda preparada para ello. La cuenta del máster
`323188184300` y sus 6 vCPU no sirven como prueba de esta solicitud. Se registra
un aviso por este nuevo episodio de autenticación y se suprimen repeticiones
mientras siga igual. Sólo lecturas; sin despliegue ni cambios en AWS.
Estado: `.work/aws-access/fargate-monitor-state.json`; recibo sin secretos:
`.work/aws-access/fargate-monitor-auth-required-20261025.json`.

## Excepción PR161, presupuesto retirado y Jarvis local — 24/10/2026

Origen: «Preparar despliegue en AWS», chat `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
El usuario retira expresamente el requisito operativo de30EUR para la cuenta
del máster; ya no se pide conciliar ese techo ni verificar el correo Budgets
como condición del ensayo. La existencia de límites de Pontia sigue sin
acreditar. No se inventa saldo: controlador/configuración publicados todavía
contienen la guarda anterior y requieren adaptación antes de ejecutarlos.
Los presupuestos AWS existentes no se han eliminado ni modificado.

El usuario autoriza documentar una excepción y lanzar dos agentes para suplir
los dictámenes humanos de PR161. Agentes lanzados: `/root/pr161_code_review`
(`Revision JUP-131`) y `/root/pr161_validation` (`Validacion JUP-131`), ambos
sobre `e730dc15fb3feb45a3b346fc9e48332c4608b049`, base `ffb5d307772f697cffb8b1e73e6330250e093601`.
Excepción en [evidencia](../evidence/JUP-131-pr161-agent-exception.md), AGENTS,
CONTRIBUTING, descripción de [PR161](https://github.com/EconomiconFinOps/tfm-economicon/pull/161)
y [Trello JUP-131](https://trello.com/c/NtiH8R4Z), conservando historial/columna.
El revisor aprobó la corrección del único P2 (métricas Grafana públicas) y el
ajuste posterior de `ApiError` para Starlette. El validador comprobó PostgreSQL,
Grafana y retirada de recursos propios; reprodujo RED/GREEN de rutas (14 mocks
Terraform) y del traceback (siete fallos originales, 82 pruebas Azure PASS).
Los informes preservan candidato y deltas por hashes; se publican en
[PR161 agentes](../evidence/JUP-131-pr161-agents/README.md). Sin atribuirlos a
Lucía/Paris, sin aprobación ficticia ni merge/despliegue autorizado.
Recibos locales en `.work/pr161-agent-exception/`.

CI histórica e730 verde a las 12:45 UTC; el run posterior `40133534310` de las
21:17 UTC detectó el fallo de `ApiError` con Starlette actual. Se corrigió la
dataclass congelada y se añadió una regresión. Commit publicado
`30d4370aca3903cf764111e451153ae2ed83510c`: a las **23:47 Europe/Paris** se
confirmaron SUCCESS de [CI PR](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40135283687),
[CI push](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40135279467)
y [SQL](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40135283678).
El [check JUP reviews](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40135283703)
sigue FAILURE exclusivamente porque faltan las dos reviews de cuentas GitHub;
la PR figura OPEN/REVIEW_REQUIRED. Los informes de agentes están publicados,
pero no se ha modificado ese mecanismo ni forzado una aprobación. Recibo:
`.work/pr161-agent-exception/final-ci-status.json`. Tampoco se modificó la
aceptación histórica de la receta: tras el delta Azure, el digest calculado
de aplicación es `415625fdff2cb998a3716a726a1b4a5b7f46852a6adba99fda56872fcde8733d`.
La configuración local del ensayo todavía fija e730: hay que regenerarla tras
la aceptación/integración del candidato y definir la ventana, antes de ejecutar.

Corrección humana del destino DNS: **Jarvis de este equipo, host `local`**,
`C:/Users/DanteInferno/Documents/Neon Bastion`, chat `01a14bba-2515-7672-8bb3-ce01b4b54e4b`.
La copia en Mother tiene el mismo ID, pero otro host. Se retiró allí el encargo
y se envió la petición concreta al local. Éste confirmó autorización humana
consultada y sesión Cloudflare válida; conservaba los cuatro NS antiguos y
26 registros totales. Tras confirmación humana final, el **24/10 a las 23:25
Europe/Paris** comunica cambio guardado y verificado: los cuatro NS nuevos,
TTL Auto, otros 22 registros idénticos y NS del padre conservados. Verificó
ambos autoritativos de Cloudflare y los resolutores 1.1.1.1 y 8.8.8.8. Una
consulta independiente a Google DNS a las **23:26** confirma los cuatro NS
de la cuenta del máster. La delegación queda resuelta; no acredita aplicación
disponible ni todas las cachés mundiales. Recibos locales sin secretos:
`.work/master-prerequisites/jarvis-local-dns-receipt.json` y
`.work/master-prerequisites/dns-after-jarvis-20261024.json`.
Evidencia original en el proyecto Neon Bastion:
`outputs/dockerserver-infra/economicon-delegacion-master-20261024.json`.
La necesidad anterior de login en Mother queda superada.

No hay daemon Docker local disponible. Para la validación independiente se
comprobó DockerServer por SSH:4CPU,~17GiB disponibles y115GiB libres. Sólo se
autorizan pruebas desechables propias y aisladas, con retirada por identidad,
sin tocar servicios existentes; no AWS ni modelos. Pruebas realizadas allí,
con cero puertos publicados y limpieza verificada por identidad: 10 contenedores,
tres tags propios y tres volúmenes anónimos ausentes. El servidor descargó la
fuente pública e730 y verificó sus 2603 blobs; no se transfirió el checkout local.

## Cuenta del máster: prerrequisitos preparados, ensayo bloqueado — 24/10/2026

Hito anterior al cambio de instrucciones superior: sus requisitos de30EUR,
dictámenes humanos y destino Mother quedan sustituidos por ese apartado.

Origen: «Preparar despliegue en AWS», chat `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.
Autorización humana: preparar todo para un ensayo en Economicon `323188184300`;
GitHub completado por el usuario. Corte AWS general de lectura 24Oct22:47
Europe/Paris; metadatos del secreto GitHub verificados de nuevo a las23:03.
No se ha arrancado aplicación, modelo, build ni pipeline. Este hito sustituye
la ausencia de prerrequisitos observada en la auditoría anterior.

- Cuotas efectivas confirmadas de nuevo: Fargate Irlanda `L-3032A538` =6vCPU;
  CodeBuild Medium París `L-2DC20C30` =30. Son de la cuenta nueva; el caso y
  monitor de `605600557607` siguen separados.
- Boundary creada `arn:aws:iam::323188184300:policy/economicon-runtime-boundary`:
  Access Analyzer0hallazgos y15simulacionesPASS. Cuatro roles
  `economicon-defensa-{build,deploy,pipeline,expiry}` con trusts revisados,
  todavía **sin políticas de identidad**. Sus importaciones Terraform están
  planificadas; no se han aplicado ni importado al estado.
- Conexión `economicon-github` **AVAILABLE**, comprobada por API después de la
  autorización humana. ARN París:
  `arn:aws:codeconnections:eu-west-3:323188184300:connection/e312ee17-b315-4e34-97b8-a42499df90ae`.
- Zona pública `Z08694913EM6SGJ47MEXG`, `economicon.danteinferno.es`, creada y
  responde SOA; sólo contiene NS/SOA. Destinos: `ns-1596.awsdns-07.co.uk`,
  `ns-238.awsdns-29.com`, `ns-547.awsdns-04.net`, `ns-1366.awsdns-42.org`.
  DNS público23:03 todavía devuelve los cuatro NS de la cuenta anterior,
  TTL21600; sin DS ni A/AAAA/CNAME en el apex. Usuario autorizó expresamente
  el cambio por Jarvis. Petición enviada a «Jarvis» en Neon Bastion,
  chat `01a14bba-2515-7672-8bb3-ce01b4b54e4b`, host Mother. Jarvis confirmó
  NS antiguos en ambos autoritativos Cloudflare y SOA/NS nuevos en Route53,
  pero **no ejecutó el cambio**: sesión Cloudflare caducada y no pudo leer
  nuestra autorización humana desde Mother. Requiere intervención en su chat
  para recuperar acceso/confirmar el cambio. No mezclar ambos conjuntos de NS.
- Secretos de control París: `economicon/bootstrap/mq-admin` tiene AWSCURRENT,
  generado en memoria, sin copiar su valor a disco; `economicon/bootstrap/github-checks`
  era un contenedor sin versión en el corte22:47. A las23:03 el usuario confirma
  haberlo guardado y `DescribeSecret` verifica exactamente una versión
  **AWSCURRENT**, sin borrado programado, en la cuenta323188184300. Último cambio
  a las23:00:02 Europe/Paris. No se leyó el valor ni se validó su JSON o
  autenticación. El formato indicado al usuario fue JSON con clave `token`,
  sin copiar la credencial local de gh. Reautenticación
  GitHub completada. La orgEconomiconFinOps no figura como propietaria admisible
  para este usuario: no generar con la selección All repositories por defecto.
  API confirma repositorio público; ambas consultas reales del runner
  (Actions run40095219997 y comparación con develop) responden200 sin autenticar.
  Formulario ajustado a **Public repositories,0permisos de cuenta**, caduca31Oct;
  lectura pública solamente, sin acceso privado ni escritura. No está limitado
  exclusivamente a este repositorio, como tampoco lo está la lectura pública
  implícita de cualquier token. Generación/entrada en AWS realizadas por el
  usuario; comprobación del agente sólo de metadatos. Si el repo se privatiza,
  revisar acceso. Caducidad/permisos reales del valor guardado no inspeccionados.
- AWS Budget nuevo `economicon-defensa-2026-control-30usd`:30USD acumulados
  01Oct–01DicUTC, toda esta cuenta, impuestos incluidos y créditos/reembolsos
  excluidos; avisos de gasto real >50/80/100%. Destinatario autorizado cotejado
  por API; **consola confirma0/1correos verificados, pendiente**.0,00USD mostrado
  no acredita saldo disponible ni ausencia de cargos retrasados. Sin apagado.

Plan bootstrap local protegido `.work/master-bootstrap/bootstrap.tfplan`:
**4importaciones,23altas,4actualizaciones,0eliminaciones**. Actualizaciones de
roles sólo descripción/tags; trusts idénticos. Terraform1.13.3/provider6.13.0,
validatePASS. Hash del plan
`9d463b86ca725660e9bc6d46dd114ad84e7c26116b485e4afb92f49533c75fda`.
No aplicar todavía: crear CodePipeline puede iniciar una ejecución inicial.
Revisión asistida de la preparación: dosP2 de validación/idempotencia del
presupuesto corregidos,8pruebasPASS;15simulacionesPASS. Cinco controles de
rechazo de receta obsoleta PASS; el primer intento falló por permisos del
directorio temporal del sandbox, repetición con permisos normales sin cambios
de código PASS. No se atribuyen esos fallos de entorno a la aplicación.

Paquete local `.work/master-rehearsal/`: configuración de cuenta nueva,
`start-up.json`, `start-down.json`, `readiness.json`, `preflight-summary.json`
y escenarios de coste. **aws_deployable=false**: saldo restante desconocido,
ventanaUTC por fijar, CI push del SHA integrado en develop y aceptación offline
completa pendientes. No modificar el digest histórico sólo para obtener READY.
La CI técnica/SQL del candidato `e730dc15` sigueSUCCESS, PR161OPEN/REVIEW_REQUIRED;
lectura23:03:22checksSUCCESS,1SKIPPED y sólo `JUP reviews`FAILURE, sin reviews
publicadas. Faltan los dos dictámenes humanos. Este corte no cambia código ni ejecuta CI.

Techo humano30EUR vigente. Catálogo22Oct y supuestos IVA21%/margen20%:
un ciclo2h23,40EUR; dos ciclos/3h totales29,15EUR; dos/4h31,41EUR;
tres/3h32,65EUR. La cifra29,15 deja margen insuficiente sin reconciliar gasto
previo y tiempos de alta/retirada; no acredita viabilidad de ensayos y defensa
dentro del techo. Asignación del máster desconocida. No rellenar saldo ficticio.

Recibos sin valores secretos en `.work/master-prerequisites/`:
`resources.json`, `final-readback.json`, `bootstrap-plan-summary.json`,
`dns-public-readback.json`, validación/simulaciones IAM y plan de preparación.
Hito23:03: `github-secret-metadata-20261024T210300Z.json`,
`dns-public-readback-20261024T2104.json` y `ci-readback-20261024T2104.json`.
Lectura final confirma ECS0clusters, CodeBuild0proyectos y CodePipeline0pipelines.
Pendiente humano: verificar correo Budgets, dictámenes PR y acceso
Cloudflare en Jarvis; pendiente técnico: verificar cambio DNS, aceptación candidata,
integración/CI develop y conciliación de presupuesto/ventana antes de autorizar
bootstrap y ensayo. La revisión automática bloqueó el botón de recuperar el
secreto por riesgo de mostrarlo; la entrada se entrega al usuario y la
comprobación del agente queda limitada a metadatos.

## Antecedente: auditoría de lectura de la cuenta del máster — 24/10/2026

Origen: este chat, `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`. Alcance autorizado:
comprobar compatibilidad de la cuenta alternativa, sin despliegue ni cambios
de recursos. Corte de comprobación: 24Oct2026, aproximadamente22:20 Europe/Paris.
La identificación inicial como Academy/Learner Lab queda superada: el acceso
real es el [portal SSO de Pontia](https://pontia.awsapps.com/start/#/), cuenta
AWS **Economicon `323188184300`**, perteneciente a una organización. No se ha
acreditado un crédito, saldo o vencimiento de Learner Lab.

Consola y STS confirman esa cuenta. Perfil CLI aislado `economicon-master-audit`,
configuración no secreta `.work/aws-access/master-audit-config`; login SSO
completado tras autorización humana explícita del alcance de las dos cuentas
asignadas al portal. Todas las consultas se limitaron a Economicon; no se
inspeccionaron recursos de la otra cuenta. Sin claves estáticas nuevas.

| Requisito | Resultado confirmado y límite de la evidencia |
| --- | --- |
| Fargate Irlanda | Cuota **aplicada6vCPU**, `L-3032A538`, por consola y `get-service-quota`; utilización visible0. Cumple el mínimo6 del controlador, incluido rolling Atlas5.5. |
| CodeBuild París | Cuota **aplicada30** ejecuciones Linux/Medium, `L-2DC20C30`; requisito1. |
| Regiones y red | Irlanda, París, us-east-1, Frankfurt y Estocolmo habilitadas sin opt-in; tres AZ disponibles en Irlanda. Cuotas VPC5, NAT5/AZ, EIP5, ALB50. VPC por defecto presente; no se creó red. |
| IAM | Rol `AWSReservedSSO_AdministratorAccess_6ee990f52d2ca1f5`, política AWS `AdministratorAccess`, sin boundary ni inline; máximo de sesión del rol43200s, no prueba de duración efectiva de la sesión SSO. Simulación33acciones `allowed`, incluyendo roles/PassRole y creación de componentes. |
| Restricciones de organización | `ListPoliciesForTarget` y `ListParents` denegados. La simulación no aportó `OrganizationsDecisionDetail`: no acredita ausencia de SCP ni garantiza el resultado de futuras escrituras. |
| PostgreSQL y RabbitMQ | Catálogo regional admite PostgreSQL16.9 `db.t4g.medium`, gp3, cifrado y Multi-AZ; cuota RDS40 instancias/usadas0. MQ admite RabbitMQ3.13 `mq.m5.large`, `CLUSTER_MULTI_AZ`, en las tres AZ. La consulta de cuotas MQ no devolvió entradas; no se inventa un límite aplicado. pgvector y arranque reales pendientes. |
| Bedrock | Titan Text Embeddings V2 y Nova Micro `AUTHORIZED`, acuerdo/entitlement/región `AVAILABLE`; perfil `eu.amazon.nova-micro-v1:0` `ACTIVE`. Titan On-Demand6000peticiones/min y300000tokens/min; Nova cross-region400peticiones/min y400000tokens/min. No se invocó ningún modelo. |
| Componentes y preparación | Lecturas de ECS/ECR/RDS/MQ/Cognito/KMS/Secrets/Cloud Map/Route53/ACM/WAF/CloudFront/S3/CodeConnections/CodePipeline/CodeBuild/Scheduler/DynamoDB accesibles. No aparecen recursos del proyecto en los ámbitos revisados; conexiones GitHub, zona DNS y roles `economicon*` ausentes. CloudFront0 distribuciones. Disponibilidad de API y simulación no sustituyen la prueba de creación. |
| Presupuesto | **Techo humano30EUR vigente**. Consola AWS Budgets de esta cuenta muestra la pantalla inicial sin presupuestos configurados; CLI `DescribeBudgets` devuelve salida vacía, no un saldo0. Presupuesto/avisos30USD de `605600557607` no se trasladan. Crédito, asignación del máster, gasto acumulado y fecha de disponibilidad todavía desconocidos; no hay corte automático de30EUR acreditado. |

Conclusión: las cuotas que bloqueaban la cuenta original están resueltas **en
esta alternativa** y la arquitectura resulta viable según las lecturas. No
equivale a aceptación del despliegue ni autoriza a ejecutarlo. Faltaría confirmar
asignación de gasto/disponibilidad con el máster, establecer el control de coste
en esta cuenta, preparar bootstrap/roles/GitHub/secretos y DNS/certificados con
sus nuevos identificadores, y renovar configuración/ventana/estimación del ensayo.
Conservar techo30EUR; los escenarios Atlas de abajo siguen siendo estimaciones,
no una asignación de crédito. También siguen pendientes revisión humana e
integración de PR161 y aceptación del candidato completo.

Fuentes locales de requisitos: `tools/aws_demo/{control,runner}.py`,
`infra/aws-bootstrap/main.tf`, `infra/aws-reference/{variables,data,edge}.tf`.
Recibos locales sin secretos: `.work/aws-access/master-account-readonly-receipt.json`
y `master-account-followup-receipt.json`; captura `master-fargate-applied-6.png`.
No se crearon/modificaron recursos, permisos IAM, modelos, builds ni despliegues.
No cambiar la delegación DNS de la cuenta anterior antes de preparar el destino.

El monitor Fargate conserva la cuenta original `605600557607` y su caso
`179267775500075`: **no registrar estas6vCPU como aprobación de ese caso**.
La sesión de consola actual pertenece a `323188184300`; comprobar identidad
antes de cualquier lectura del monitor. La CLI original no se ha renovado.

## Atlas integrado en la preparación de ECS — 24/10/2026

Origen: este chat, tarea `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`; autorización
humana para integrar Atlas/Grafana/carga aditiva, CI verde y techo30EUR, sin
desplegar. Checkout `tfm-economicon-aws-cicd`, rama `feat/JUP-131-atlas-ecs`,
[PR161](https://github.com/EconomiconFinOps/tfm-economicon/pull/161) contra develop.
PR146 ya integrada; esta ampliación parte de `ffb5d307772f697cffb8b1e73e6330250e093601`.

Implementado: SQL Atlas byte a byte y19 informes canónicos revalidados aquí;
bootstrap privado aditivo, repetible, conserva histórico adicional y aborta
conflictos atómicamente. Lector de evaluación sin escritura/DDL y propietario
independiente para metadatos Grafana, ambos en el RDS vectorial existente.
Grafana/Prometheus comparten una tarea privada0.5vCPU/1GiB, secretos separados,
TLS verificado y ruta `/grafana/` por CloudFront/ALB. Tres dashboards intactos.
Prometheus limitado a24h/256MB y loopback; métricas efímeras, metadatos en RDS.
Máximo rolling agregado5.5vCPU; se sigue exigiendo cuota efectiva6. Landing/vídeo
siguen fuera de ECS en el flujo de HAL, sin nueva comunicación a otros chats.

Verificación propia24Oct: PostgreSQL16 real6PASS más manifiesto; controlador87OK
(7 opt-in, SQL aparte); Terraform13PASS; OpenSpec92PASS; Grafana aislado PASS con
TLS,401 anónimo, tres dashboards,19/1688, cookie segura, Origin público/Host de
backend distintos, origen ajeno403 y preferencia persistida tras reinicio.
Revisión asistida de `a7341d79` pidió corregir CSRF y limpieza de bootstrap
monitoring huérfano; ambos reproducidos RED→GREEN. Revalidación asistida del delta
`a7341d79..0f1522e6`: APPROVE, sin nuevos hallazgos; focal de limpieza repetido por
el revisor PASS, smoke verificado por el implementador. CI anteriora7341d79
[push40094121176](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40094121176),
[PR40094206962](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40094206962)
y SQL40094206943 SUCCESS. CI definitiva de `e730dc15fb3feb45a3b346fc9e48332c4608b049`
confirmada SUCCESS: [push40095219997](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40095219997),
[PR40095225030](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40095225030)
y [SQL40095224920](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40095224920).
Incluye todas las baterías de aplicación y los nuevos controles PostgreSQL/Grafana.
Un fallo intermedio de `terraform fmt` quedó corregido sin cambio semántico en
e730dc15. `JUP reviews`40095224907 sigue FAILURE por ausencia de los dictámenes
humanos `Revision JUP-131` y `Validacion JUP-131`; no se modificó la política.
PR161 lista para revisar, sin merge. La revalidación asistida no sustituye a las personas.
Detalles y límites: [evidencia](../evidence/JUP-131-atlas-ecs.md),
[plan](../planning/2026-10-24-jup131-atlas-ecs.md) y [runbook](../deployment/aws-defensa.md).

Presupuesto vigente30EUR: rechaza saldo/estimación desconocidos y exceso.
[Escenarios Atlas](../planning/costes-aws/atlas-resultados.json), catálogo22Oct,
IVA supuesto21% y margen20%: un ciclo2h23,40EUR; tres ciclos2h39,42EUR. El programa
de varios ensayos y defensa necesita ajustar duración/saldo antes de autorizarlo.
AWS Budgets30USD es alerta, no apagado ni límite garantizado; última lectura
anterior24Oct tenía correo pendiente de confirmar y0,60USD visibles.

Preparación local separada `.work/atlas-prep/` no ejecuta AWS. La configuración
original `.work/ensayo1/config.json` conserva SHA/ventana históricos y saldo0;
no se ha sustituido por una aprobación nueva. La receta mantiene digest de
aceptación histórica distinto del árbol actual: esta prueba de Atlas no acredita
aceptación completa PostgreSQL/Cognito/Bedrock/demo del candidato integrado.
Pendiente: dictámenes de PR e integración, aceptación completa,
cuota efectiva6, saldo/estimación/ventana vigentes y bootstrap de control antes de
un despliegue expresamente autorizado. Cloud Map/CloudFront/RDS reales no probados.
Sin recursos AWS creados/modificados, modelos ejecutados ni despliegue.
Recibo local sin secretos `.work/aws-access/atlas-ecs-preparation-receipt.json`;
contenedores desechables de prueba retirados. JUP-131 actualizado por integración
autorizada DockerServer, con historial/roles/columna conservados y enlaces CI.

## Antecedente: paquete Atlas recibido, antes de integrar — 24/10/2026

Origen: transferencia de HAL 9000, chat `01a1270c-e332-7462-9c90-706d49ade92c`,
con indicación humana de trasladar la parte útil al chat AWS. Recibida como
entrada documental; no amplía autorización para desplegar, SQL, IAM, cuotas,
presupuesto, modelos ni comunicaciones externas. Acuse en este chat.

Paquete [Drive](https://drive.google.com/file/d/1Ynfqp3-eefkm56ewwgNVINH7mp0U5lwH/view),
copia local en `C:/Users/DanteInferno/Documents/Economicon/materiales/07-evidencias/landing-publicacion-paris-20261024/atlas-package.zip`
y carpeta hermana `atlas/`. ZIP SHA256
`c4eb723006f5a83518b4791b4177bd26d8f61e14f975e208d5acc49d78411f14`.
Leídos instrucciones, guía, manifiestos y comprobación local. Revalidados aquí
ZIP, 13 entradas SHA256SUMS y 12 archivos/tamaños del manifiesto; no ejecutados
scripts, SQL ni inferencias. HAL acredita adicionalmente 19 hashes canónicos
de informes contra `ffb5d307772f697cffb8b1e73e6330250e093601` (PR159/160), según
`atlas-verification.json` junto al ZIP; esa comprobación no se repitió aquí.
Recibo propio `.work/aws-access/atlas-handoff-receipt.json`.

La guía presupone Compose, mientras el ensayo usa ECS/release inmutable.
[Adaptación documentada](../deployment/aws-defensa.md#entrada-atlas-del-24102026-adaptación-pendiente-para-ecs):
reconciliar versión antes de cambiar el SHA/digest/CI; preparar importación
aditiva y privada del SQL (19/1688 declarados) sin importador destructivo;
resolver Grafana, ausente en Terraform/receta actuales, antes de añadir servicios,
cuota/coste, lector o ruta. UID `economicon-assistant-evidence`, cinco secciones,
otros dos dashboards e histórico adicional deben conservarse. COMPROBACION-LOCAL
es evidencia del autor en entorno desechable, no verificación del AWS real.

Según HAL, la landing se publica por su flujo existente Pages
`economicon-landing`, `https://landing-economicon.danteinferno.es/`; no hemos
verificado su publicación en este chat. App existente `https://demo-jupiter.danteinferno.es/`
y Grafana `/grafana/` no cambian el dominio AWS preparado `economicon.danteinferno.es`.
No crear `landing-demo-jupiter`, ni contactar a Jarvis por esta entrega.
MP4 original21094149bytes, SHA256
`7e9bdfb148cee61acb2e96837f041a5014f3f7048bf2a244a5cb20128f080292`;
manifiesto `8f55e48b9a02d6a0d3c80d35ddde4263605bce46f4139bd7b8cb5991cb328c1f`.
Medios conservados fuera del repo e imágenes; variables runtime de Compose no
se trasladan a Pages/ECS sin adaptación. Sin cambios de código/infra, SQL, build,
despliegue, nuevos subdominios o mensajes a HAL/Jarvis/Discord.

## Presupuesto creado y monitor reanudado — 24/10/2026

Origen: este chat, tarea de preparación AWS, identificador
01a15abb-d5f3-7fd3-a622-ea9e73b0db18. Usuario autoriza control de gasto30EUR
para evitar recursos olvidados y proporciona destinatario para los avisos.
Consola confirma creado `economicon-defensa-2026-control-30usd`:30USD,
periodo único01Oct–01Dic2026 (fin exclusivo indicado por UI), toda la cuenta,
todos los servicios/regiones, costes sin combinar. USD obligatorio en formulario;
30USD es umbral conservador nominal, no conversión exacta de30EUR ni tope de
facturación garantizado. Avisos reales >50/80/100%=15/24/30USD, un destinatario,
SIN acciones IAM ni apagado. Contabilizado visible0,60USD; puede haber retrasos.
**Correo pendiente de verificación (0/1): el operador debe confirmar el enlace
recibido de AWS Budgets; hasta entonces no recibirá avisos.** No almacenar email
en continuidad. Recibos locales `.work/aws-access/budget-30usd-created.{json,png}`.
Configuración local de ensayo `.work/ensayo1/config.json` budget_eur=30; no
estimaciones nuevas inventadas, builds ni despliegues. La estimación anterior
con techo60EUR queda histórica: revalidar duración/coste total antes del ensayo.
AWS Budgets sólo avisa y puede retrasarse; no garantiza detener cargos. El
presupuesto vence01Dic: revisar/remover remanentes antes, no asumir vigilancia
posterior. https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html

Tras login humano, lectura de cuota aplicada Fargate Irlanda confirma0vCPU
(defaultAWS6 NO asignado). Caso179267775500075 sin nueva respuestaAWS;
últimaAWS22Oct16:12:03Europe/Paris, propio seguimiento23Oct12:24:37 ya conocido.
Monitor sigue ACTIVE; restablecidos checks válidos y auth_block_notified=false.
Recibo `.work/aws-access/fargate-console-status-latest.json`, estado monitor
actualizado. El bloqueo de sesión descrito abajo queda resuelto para este corte;
CLI no renovada. Sin solicitudes duplicadas ni despliegue.

## Monitor bloqueado por autenticación — 24/10/2026 13:10 Europe/Paris

Tras reinicio del runtime/pestañas ausentes, consulta de consola de cuota Irlanda
redirige a AWS Sign-In. No se puede confirmar cuota actual ni nuevas respuestas
del caso. No confundir con cuota0: último efectivo confirmado0vCPU el23Oct21:07
Europe/Paris; últimaAWS conocida22Oct16:12. CLIya caducada, sin nueva prueba ni
lectura de credenciales. TabIAB1 de login conservada para intervención humana.

Primer aviso de renovación registrado en fargate-monitor-state.json
(auth_block_notified=true); no repetir en cada ejecución mientras siga el mismo
bloqueo. Recibo .work/aws-access/fargate-monitor-auth-required-20261024.json.
Seguimiento permanece activo, sin despliegues ni mensajes aAWS. Siguiente paso:
usuario inicia sesión y avisa para reanudar comprobaciones de sólo lectura.

## Seguimiento automático autorizado — 23/10/2026

El humano solicita aviso cuando AWS responda al caso o asigne cuota Fargate,
sin desplegar. Creada automatización heartbeat activa en este chat, cada hora:
`vigilar-respuesta-aws-y-cuota-fargate-irlanda`, nombre «Vigilar respuesta AWS y
cuota Fargate Irlanda». Herramienta confirma creaciónACTIVE y tarjeta de consulta.
No se encontró monitor previo equivalente en automations antes de crear éste.

Sólo lectura del caso179267775500075 ycuotaaplicada L-3032A538/eu-west-1.
Estado/deduplicación `.work/aws-access/fargate-monitor-state.json`: baseline
aplicada0,6solicitadas; últimaAWS22Oct16:12:03 ypropioseguimiento23Oct12:24:37
ya conocidos. No avisar del mensaje propio ni repetir avisos si nada cambia.
Avisar por respuestaAWSnueva/cambio efectivo/denegación/cierre relevante o
intervención humana. Si caduca sesión avisar una vez y distinguir desconocido0.
Continuar tras respuestas intermedias, finalizar tras confirmar efectiva>=6.
No reenviar seguimientos ni abrir chat/llamada, nuevas solicitudes/recursos,
modelos, credenciales, apply/destroy/builds/pipelines/despliegue uotrosmensajes.

Necesita equipo encendido y aplicación de escritorio activa porque usa sesión
de navegador yarchivoslocales; sesiónAWSdebecontinuarválida. Límite explicado
al usuario según documentaciónoficialOpenAI de tareas programadas. No cambia
el estado de la cuota por haberse configurado este monitor. Futuras ejecuciones
deben releer continuidad vigente antes de decidir qué es una novedad.

## Seguimiento Fargate enviado por web — 23/10/2026 12:24 Europe/Paris

Autorización humana expresa: enviar seguimiento por web en caso179267775500075
para pedir prioridad, sin desplegar. Borrador y canalWeb releídos en UI y envío
único realizado; correspondencia visible confirma autorDante_Inferno y fecha
23Oct12:24:37+02:00 con texto exacto preparado. No contactos adicionales ni adjuntos.
Solicitud de priorización6vCPU/Irlanda por defensa29Oct/ensayos y detalles de
capacidad/rolling ya descritos abajo. No aprobación ni nueva respuestaAWS observada.

Recibos `.work/aws-access/fargate-support-followup-sent.json` y captura `.png`;
borrador original conservado como antecedente, ya no pendiente de envío.
TabSupport5 marcado para conservar confirmación. Sin chat/llamada, solicitud
duplicada, upgrade de soporte, recursos nuevos ni despliegue. Próximo paso:
respuesta del caso y cuota efectiva antes de cualquier ensayo; no inferir
aprobación por haber publicado el seguimiento ni reenviarlo por inercia.

## Seguimiento preparado para agilizar Fargate — 23/10/2026

Usuario pregunta cómo agilizar antes de defensa29Oct. Lectura del caso existente
179267775500075 en Support confirma planBásico y respuesta automática AWS del
22Oct16:12:03Europe/Paris: procesamiento puede tardar hasta96h; no es aprobación
ni plazo garantizado. Referencia temporal desde mensaje:26Oct16:12París.
Correspondencia inicial sólo contiene región/cuota6 y texto genérico ServiceQuotas;
no había uso académico ni fecha de defensa. Cuota aplicada sigue0 en vistaFargate.

Preparado borrador exacto en `.work/aws-access/fargate-support-draft.txt` y en
campo Responder del caso (IAB5), SIN pulsar Enviar. Solicita priorizar6vCPU,
explica defensa29Oct ydosensayos previos,6tareasLinuxx86 de0,5vCPU/1GiB=3vCPU
estables/6para rolling, sesiones temporales con teardown; pide información
adicional necesaria yfecha estimada de resolución. Sin credenciales, archivos
privados, gastos comprometidos ni datos del evaluador. Captura local
`.work/aws-access/fargate-support-draft.png`; tabs conservadas para revisión.

Formulario ofrece Web/Chat/Teléfono. El soporteBásico admite cuotas según
https://repost.aws/knowledge-center/get-aws-help y documentación oficial
https://docs.aws.amazon.com/awssupport/latest/user/create-service-quota-increase.html.
No hace falta contratar soporte de pago para presentar seguimiento de cuota;
no se ha probado disponibilidad efectiva de agenteChat/llamada ni se ha iniciado
contacto. No duplicar solicitud ni cambiar región/cuota por inercia.

Pendiente autorización humana expresa para enviar mensaje aAWS en su nombre;
la pregunta de opciones no se convirtió en permiso de comunicación externa.
Sin envío, nueva solicitud, upgrade, despliegue ni cambioIAM/DNS. Si autorizado,
releer borrador/UI y enviar sólo en este caso; comprobar correspondencia publicada.

## Fargate verificado en consola — 23/10/2026 08:36 Europe/Paris

Tras login humano en IAB4, consola cuenta605600557607/Irlanda eu-west-1,
Fargate On-Demand L-3032A538 muestra cuota aplicada0vCPU, predeterminadaAWS6.
Historial muestra solicitud22Oct por6vCPU en «Caso abierto». No confundir el
default6 con capacidad asignada; ensayo aún bloqueado. Consulta sólo lectura,
sin nuevas solicitudes ni despliegue. Evidencia local de lectura visible
`.work/aws-access/fargate-console-status-latest.json`,06:36:51UTC,URL
https://eu-west-1.console.aws.amazon.com/servicequotas/home/services/fargate/quotas/L-3032A538.
Esto supera la imposibilidad de lectura de08:33; no se ha renovado CLI ni se
afirma fecha nueva de actualización administrativa del caso. Tab marcado para
conservar la vista del resultado.

## Comprobación bloqueada por sesión caducada — 23/10/2026 08:33 Europe/Paris

Petición humana de reconsultar Fargate Irlanda. Ambas lecturas CLI (cuota efectiva
y solicitud) fallan por sesión expirada, sin dato nuevo de cuota. Recibo
`.work/aws-access/fargate-status-latest.json` registra fallos06:33:37UTC; no
interpretar resultados ausentes como0. Último efectivo confirmado22Oct23:33París:
0vCPU/CASE_OPENED. Consola tampoco tiene sesión: tabIAB4 abierto en SignIn AWS
para ServiceQuotas Irlanda, marcado handoff. Necesita inicio de sesión humano
antes de consultar. No credenciales leídas/renovadas, ni solicitudes o despliegue.

## Nueva comprobación Fargate — 22/10/2026 23:33 Europe/Paris

Por petición humana, lectura ServiceQuotas Irlanda eu-west-1: L-3032A538 sigue
efectiva0vCPU; solicitud6vCPU sigue CASE_OPENED, caso179267775500075, última
actualización administrativa22Oct16:02:40+02:00. No aprobación efectiva ni cambio
de cuota observado. Recibo `.work/aws-access/fargate-status-latest.json`, corte
21:33:36UTC. Sin solicitud duplicada, cambios AWS ni despliegue. Fargate continúa
bloqueando el ensayo. No se han reconsultado otros servicios por esta petición.

## Evaluador dado de alta con fecha aclarada — 22/10/2026

El humano confirma30Nov2026, incluido. Supera la espera de fecha inválida del
corte anterior. Alta IAMautorizada para Carlos: economicon-evaluador-carlos,
política arn:aws:iam::605600557607:policy/economicon-evaluador-carlos-hasta-20261130
como identitypolicy y boundary iguales, hash349e33182367be171bbe6652b8c51331966a074816a9be1474ca77436f8bbf27.
Consola con contraseña inicial/reset obligatorio,0accesskeys/0grupos/0inline,
1política adjunta. No contraseña/correo personal en continuidad.

MFAobligatorio antesdelectura; excepción inicial acotada a contraseña/MFA propios.
DenyAll desde2026-11-30T23:00:00Z=01Dec00:00Europe/Paris incluso conMFA/sesión.
IAMusuario/loginprofile no se eliminan por esa condición: bloqueo de permisos,
retirada posterior pendiente cuando finalice la revisión. Lectura de metadatos
infraestructura; algunos listados de cuenta son globales/enregiones proyecto,
sin contenidoS3/secretos/DB/logs ni cambios/modelos/costes deejecución.
Guía y alcance exactos [runbook](../deployment/aws-defensa.md).

AccessAnalyzer0findings,23casos simulados conformes (MFA/fecha/región/cambios/
secretos/objetos/credenciales/identidad ajena), readback de política/boundary y
configuración de usuario conforme. Recibo .work/aws-access/evaluator-access-receipt.json,
6simulaciones adicionales del principal IAM real con su boundary conformes;
recibo evaluator-principal-simulations.json (sin operaciones reales de despliegue).
política/validación/simulaciones homónimas. Contraseña sólo en archivo privado
.work/aws-access/private-evaluator/acceso-carlos.txt, ignorado porGit yACL verificada
únicamente Windowsoperador/SYSTEM. Sin contraseña en comandos/logs/chat ni email
enviado; entrega privada aCarlos por el humano pendiente. Payloadtemporal deperfil
eliminado, no borrado de otros archivos. Loginreal/MFAdeCarlos aún no verificados.
No despliegue ni acciones sobreinfra/control/DNS/cuotas;altaIAMdeevaluador sí realizada.

## Acceso del evaluador pendiente de fecha válida — 22/10/2026

El usuario facilita nombre y correo del evaluador Carlos (correo solo en chat,
no duplicado en documentación) y solicita vigencia «31 de noviembre». Esa fecha
no existe; pregunta async enviada para elegir30Nov2026 o31Oct2026. Pendiente
respuesta, sin asumir fecha por selección predeterminada ni crear acceso.

Preflight de lectura19:56UTC: cuenta correcta; Organizations describe devuelve
AWSOrganizationsNotInUseException (cuenta fuera de organización). No se activó
Organizations/IdentityCenter ni se listaron instancias después de esa respuesta.
La modalidad IdentityCenter que asigna cuentasAWS requiere organización; la
instancia de cuenta aislada para apps no resuelve esta entrada a consola.
IAM get-user de economicon-evaluador-carlos devuelveNoSuchEntity, no se creó.
Recibo `.work/aws-access/evaluator-access-preflight.json` sin credenciales.

Alternativa propuesta: usuario exclusivo de consola, sin access keys, lectura de
infraestructura, MFA/autogestión limitada y bloqueo de permisos por fecha explícita.
No alta, contraseña, políticas/permisos nuevos ni comunicación al evaluador.
Siguiente: fecha válida, definir/verificar política y entrega privada de acceso;
mantener prohibición de desplegar. No reutilizar credenciales del operador.

## Seguimiento de cuotas y DNS y acceso del evaluador — 22/10/2026

Orden humana: enviar estimación a HAL para Lucía y comprobar cuotas/DNS, sin
desplegar; asesorar acceso de un evaluador. Envío a HAL9000 confirmado por tool,
chat01a1270c-e332-7462-9c90-706d49ade92c, con informe/rutas/cifras/supuestos y límites.
No se afirma entrega de HAL a Lucía ni se envió Discord desde aquí.

Lecturas AWS19:36–19:37UTC: FargateIrlanda L-3032A538 efectiva0, solicitud6
CASE_OPENED caso179267775500075. CodeBuildMediumParís L-2DC20C30 efectiva15
(necesaria1), solicitud1 aún CASE_OPENED caso179267775900317. Primera lectura
del casoCodeBuild falló429 en OAuth; repetida secuencialmente conforme. No se
renovaron sesiones manualmente ni se generaron credenciales/solicitudes nuevas.
Recibo `.work/aws-access/quota-status-user-check.json` conserva ambos intentos.

Jarvis terminó delegación (turno01a16474-8996-7651-8cd9-2afd2ec524bd,
cursor e562b468-2871-4183-921d-db03cf94a54b:7). Informa4NS TTLauto, preservados
20registros yNS padre. Comprobación propia19:36UTC:1.1.1.1/8.8.8.8 devuelven
4NS esperados; ns-54.awsdns-06.com devuelveSOAserial1. ConsultasdirectasWindows
a diva/salvador devuelven error DNS; no afirmar verificación completa de los
autoritativos por este chat. Recibo `.work/aws-access/dns-status-user-check.json`.
Esto supera el estado anterior DNSpendiente/cuotas0/0. DNSyaobservable público;
CodeBuildcapacidaddisponible; Fargatecontinúabloqueando, ademásdelrestodeprerrequisitos.

Usuario confirma evaluador con cuentaAWS propia: propuesta de rol entrecuentas
temporal de lectura acotada a recursos del proyecto. PedirIDcuenta12dígitos,
ARNusuario/rolconcreto,fecha fin yalcanceconsola/CLI. Requiereautorización
sts:AssumeRoleensuorigen y trustacotadoenproyecto. No crear acceso todavía ni
solicitarclaves/contraseñas/root. Fuentes oficiales IAMbest-practices ytutorial
cross-account-with-roles consultadas22Oct. Sin despliegue ni cambios AWSenestecorte.

Estimación mensual del 22/10/2026: [costes AWS](costes-aws.md). Plantilla HA
730h ≈1150EUR/mes sinIVA; cálculo público/offline separado del presupuesto de
60EUR para ensayos. No modifica autorización, readiness ni estado de las cuotas.

## Roles, zona y conexión preparados por autorización expresa — 22/10/2026

Usuario autoriza preparar roles, DNS y GitHub mientras aprueban cuotas, sin
aplicación. Posteriormente pide delegar DNS a Jarvis en Neon Bastion y confirma
paso GitHub completado; Cloudflare pendiente. Solo estos prerrequisitos AWS se
han creado ahora, superando el estado previo de solo solicitudes de cuota:

- Zona pública economicon.danteinferno.es ID Z0908169205CKOWLEJ2DZ. SOA responde
  directamente desde ns-54.awsdns-06.com; no equivale a delegación pública.
- CodeConnection París economicon-github, ARN
  arn:aws:codeconnections:eu-west-3:605600557607:connection/df45512d-c3c4-44ca-93ca-c4ae399eb637.
  AVAILABLE tras intervención del usuario, comprobado por API.
- IAM policy arn:aws:iam::605600557607:policy/economicon-runtime-boundary,
  SHA del fichero b56e0aae9910112997055b1bd821eed04a5efff38a2c508079e8e2b715bb00a6.
  Access Analyzer0findings,15simulaciones conformes, review técnica independiente
  favorable sin P1/P2/P3. Ceiling solo ensayo*/defensa*, no default reference.
- Roles economicon-defensa-{build,deploy,pipeline,expiry}, trusts iguales a
  plantilla y verificados por GetRole;0políticas inline/adjuntas. Son base IAM,
  no permisos efectivos de despliegue. La boundary es para futuros ECS, no
  está adjunta a los4roles de control. Antes del bootstrap hay que importarlos
  a aws_iam_role.{build,deploy,pipeline,expiry} del estado infra/aws-bootstrap.
  No se aplicó Terraform ni se crearon proyectos/pipelines/buckets/secretos/apps.

La sesión CLI root de la cuenta correcta se usó solo para el alcance de preparación
expresamente autorizado. No claves permanentes, credenciales en archivos ni
cambios a roles/recursos ajenos. Artefactos públicos locales y readback:
.work/aws-prerequisites/{resources.json,runtime-boundary.json,boundary-validation.json,
boundary-simulation-results.json,verification-summary.json} y scripts de estas
operaciones. Recibo del alcance/importación/servicios en docs/deployment/aws-defensa.md.
Coste previsto de la zona0,50USD/mes+consultas, sin prorrateo; factura/saldoEUR
no verificados. Presupuesto total60EUR se mantiene, coste completo pendiente.

Petición enviada con autorización humana a «Jarvis», Neon Bastion, host local,
chat01a14bba-2515-7672-8bb3-ce01b4b54e4b. Solo cuatro NS en Cloudflare con nombre
economicon y TTLauto: ns-1509.awsdns-60.org, ns-2005.awsdns-58.co.uk,
ns-995.awsdns-60.net, ns-54.awsdns-06.com. Conservar padre y otros registros;
comprobar conflictos/DS antes de sustituir nada, sin A/AAAA/CNAME de app.
Petición enviada y reiterada al finalizar su turno anterior; snapshots aún
muestran a Jarvis con la incidencia SSH de Mother. DNS consultado directamente
en diva.ns.cloudflare.com devuelve NXDOMAIN: delegación aún no aplicada/visible.
No se vuelve a enviar para evitar duplicados; comprobar su respuesta en siguiente paso. No interpretar entrega de mensaje como ejecución o aceptación.
NS padre comprobados: diva.ns.cloudflare.com y salvador.ns.cloudflare.com.

Cuotas efectivas reconsultadas al terminar: FargateIrlanda0/CodeBuildMediumParís0.
Ensayo1 actualizado con zoneID real pero aws_deployable=false; coste/restante0,
DNS delegado, políticas/control, secretos, reviews/CIpushdevelop y ventana aún
pendientes. Trello actualizado mediante DockerServer, readback conforme y columna intacta,
sin Discord. No despliegue de aplicación. Candidato PR8e879dae y su CI intactos;
actualización operativa/documental local, sin nuevo push ni merge.

## Petición de primera prueba y preflight actualizado — 22/10/2026

Usuario pregunta si podemos realizar una prueba de despliegue AWS. Comprobación
actual de solo lectura: sesión CLI válida, cuenta605600557607, identidad root.
La primera consulta sin región devuelve NoRegion; repetida con eu-west-3 da STS
conforme, sin modificar el perfil ni renovar/extraer credenciales.

- Fargate Irlanda cuota efectiva0, necesaria6; solicitud CASE_OPENED, caso179267775500075.
- CodeBuild Medium París efectiva0, necesaria1; CASE_OPENED, caso179267775900317.
- IAM no devuelve roles con prefijo economicon; Route53 no devuelve zonas.
- CodeConnections París sin conexiones; Secrets Manager París sin referencias
  cuyo nombre coincida economicon. No se leen valores de secretos ni se infiere
  ausencia de otros secretos globalmente.
- PR146 sigue OPEN/borrador en8e879dae, sin merge. Única review lmatsan mantiene
  CHANGES_REQUESTED y no hay Validacion; CI técnica continúa SUCCESS.

Ensayo bloqueado por capacidad y prerrequisitos. No iniciar bootstrap de pago,
apply ni pipelines mientras las cuotas sigan0. Siguiente: aprobación efectiva
6/1 por AWS, preparar roles/boundary, conexión/secretos y DNS/delegación, resolver
reviews/integración develop, coste completo y ventana antes del ciclo. No repetir
solicitudes abiertas. Evidencia pública .work/aws-access/trial-readiness-20261022.json.
No recursos creados/modificados ni ensayo iniciado en esta comprobación.

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
repite controlador68PASS/1SKIP y backend142PASS. Candidato publicado
8e879dae3f23d52f46ea2b625ca1f2eebd22cd4a; CI final verificada SUCCESS. Receta/evidencia renovada y validada offline:
apphash8a47bf3d8f88fbc45652bdcbe5ecb7f71c036c3e9d3bfc0b51bb556d36cd633d.

Cierre verificado del SHA8e879dae: [CI push39800901608](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39800901608)
SUCCESS (8jobs técnicos) y [CI PR39801651320](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39801651320)
SUCCESS (8técnicos+JUPpolicy). SQL39800911469 SUCCESS. Ediciones de cuerpo
cancelaron PR39800911163/39801234155; no fueron fallos de código. Evidencia
ignorada .work/aws-review-fixes/ci-{push,pr}.json. ZIP limpio8e879dae valida
receta/evidencias. .work/ensayo1 actualizado a este SHA, aws_deployable=false,
cuenta/motores reales, DNS REPLACE y coste/restante0 deliberados; el SHA debe
integrarse en develop y elegirse su CIpush antes de regenerar para lanzamiento.

Gate JUP reviews39801651793 falla únicamente por falta Validacion JUP-131 y
CHANGES_REQUESTED de lmatsan; logs leídos, no eludido. Roles actuales consultados
en integración Trello DockerServer: Alejandro liderazgo, Victor pairing, Lucia
revisión, Paris validación; cuerpo PR reconciliado con la asignación vigente.
PR146 sigue borrador, sin merge. Trello actualizado por integración DockerServer
con readback exacto y columna intacta; sin Discord. Recibo y pruebas no inventan
aceptación humana. Cierre CI conservado en continuidad local sin nuevo commit
para mantener el SHA probado8e879dae; solo README/tema de continuidad modificados.

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
