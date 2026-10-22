# JUP-131 — fixtures y comprobación del ensayo

Verificado localmente el 22/10/2026 en la rama de PR146. Cambios posteriores al
SHA publicado `3e543b6f`, aún sin publicar. Sin llamadas a la cuenta AWS,
despliegue, cambios DNS o gasto de inferencia. Esta evidencia no acredita AWS.

## Carga repetible

`apps/processor/app/resources/rehearsal-v1.json` contiene un conjunto explícito
sintético, versión `aws-defense-v1`: Core/Compute 12,50 EUR y Growth/Storage
999,99 EUR en octubre de 2026, más un documento por tenant. El segundo documento
contiene una marca para detectar filtraciones. No son facturas reales.

`app.aws_bootstrap_fixtures` guarda la identidad de ciclo/SHA/hash de fixture en
las ejecuciones de costes y comprueba los registros existentes antes de insertar.
Un importe, asociación o contenido cambiado aborta; no se sobreescribe. El corpus
usa Titan V2 nativo1024 y un espacio con identidad de modelo/región/tokenizador.
El vector nativo se conserva en cache antes de publicar el documento; construir
y activar la generación reutiliza esa cache. La reejecución conserva las
generaciones y no vuelve a inferir. No se rellenan dimensiones ni se etiquetan
vectores mock como nativos.

El bootstrap ejecuta ahora cinco tareas privadas secuenciales: bases backend,
bases processor, MQ, identidad backend y fixtures processor. La fase de fixtures
conserva el motor owner con su configuración TLS; siempre lo cierra. Su exit0
sigue indicando solo bootstrap correcto, `application_ready=false`.

Pruebas `test_rehearsal_fixtures_pgvector_jup131.py` y
`test_aws_bootstrap_jup131.py`: **6 PASS**, incluidas dos pruebas con PG16/pgvector
real desechable. Prueban reintento, cantidades por tenant, generaciones nativas,
cache sin nuevas llamadas, retrieval real del backend y rechazo sin sobrescribir.
Solo el SDK de inferencia está simulado. La migración operacional usa una ruta
absoluta porque los tests aíslan el directorio actual. Bases UUID retiradas.

## Checker implementado, aceptación AWS pendiente

`tools/aws_demo/checks.py` comparte la admisión CodeBuild/config SHA256/identidad
STS/caducidad del bootstrap. En el futuro ensayo comprobará:

- Tres servicios con dos tareas, despliegues completos y configuración nativa;
  dos targets ALB sanos y distribución CloudFront desplegada.
- Login administrativo Cognito del usuario marcado, `/me` vinculado por sub,
  listado solo Core, 401 sin token y 403 al seleccionar Growth.
- Resumen de costes esperado, admisión/upload S3/confirmación/cola/extracción
  real de un Markdown sintético con identificador único.
- Chat habilitado, generación persistida y respuesta conforme al schema público,
  cita del documento recién ingerido, ausencia de la marca Growth y contadores
  de uso positivos/coherentes. Configuración Bedrock comprobada en ECS;
  no se inventa identidad de modelo resuelto ni coste monetario.

HTTP usa TLS, destino fijo, límites de bytes/tiempo y ninguna redirección. El PUT
prefirmado solo admite el endpoint regional y prefijo staging del bucket esperado;
no recibe el bearer de la aplicación. El observador SSE obtiene operation_id y
continúa por consultas de estado; cerrar la observación no cancela la operación.
El informe privado `acceptance.json` contiene etapas, IDs y contadores, no tokens,
contraseñas, URLs prefirmadas ni conversaciones. El runner lo sube aun si falla
y no escribe READY hasta que todos los checks terminan.

Controlador completo: **49 PASS/1 SKIP, 50 casos totales**. Los cinco nuevos tests
del checker incluyen un recorrido HTTP simulado y diez fallos funcionales, más
cuatro fallos SDK/configuración, admisión local sin AWS, URLs ajenas y transporte
sin redirects. Esto prueba el instrumento, no sustituye ejecutarlo sobre AWS.
CI instala su lock de SDK+jsonschema, reutilizando pins/hashes existentes de las
imágenes; validar instalación final Linux junto a las imágenes definitivas.

Logs ignorados: `.work/aws-application/fixtures-final.log`,
`fixtures-controller.log`, `checks-green.log`, `fixtures-checks-all.log`.

## Integración pendiente

La envoltura del schema Nova ya está implementada según la
[documentación oficial](https://docs.aws.amazon.com/nova/latest/userguide/tools-troubleshooting.html),
que solo admite type/properties/required en su raíz. La propiedad response
conserva anyOf/$defs y todas sus restricciones; las referencias locales se
reubican sin modificar el original, y las externas se rechazan. El lector retira
la envoltura incrementalmente y valida el resultado y la envoltura completa;
rechaza campos adicionales, claves duplicadas y truncamiento, conservando la
clasificación max_tokens. No se fusionan ramas ni se relajan las validaciones.
El recibo nativo conserva los tokens de ambas fases si todos se conocen; el
informe de precio sigue incompleto y no se inventa coste. **57 PASS** Windows
en schemas, protocolo Converse/stream, integración nativa, resumen y revisión
privada. Regresión Linux e integración v4 definitivas pendientes. No inferir
que los mocks acreditan el comportamiento efectivo de la cuenta. Se conserva
la [elección explícita de herramienta](https://docs.aws.amazon.com/nova/latest/userguide/tool-choice.html)
y el [perfil UE desde España](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-micro.html).

Dockerfiles de las tres apps declaran VOLUME /tmp y propietario del usuario de
aplicación con modo0700, siguiendo el [contrato de volúmenes ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/bind-mount-examples.html).
Pendiente comprobar las imágenes finales con volumen ordinario y raízRO;
los ensayos anteriores con tmpfs0777 no demuestran los permisos de Fargate.

Faltan integración develop/JUP-132 y colisión ADR,
receta/hashes definitivos, regresión y empaquetado Linux del conjunto, CI del SHA
final y revisión independiente. Cuenta/permisos/DNS/crédito/ventana siguen como
prerrequisitos externos. No se necesita todavía solicitar credenciales.

## Verificación del conjunto integrado — 22/10/2026

Sustituye los pendientes de integración anteriores: develop4567e8e7 incorporado,
recursos v4 compatibles (66PASS nativos), ADR AWS0027 y receta real preparados.
Tres imágenes Linux construidas; uid10001, raízRO y /tmp con volumen ordinario
privado comprobados. Backend completo2714PASS/369SKIP. Processor completo:
2666PASS/150SKIP y cinco fallos por expectativa ledger antigua; esperado005
corregido y siete casos focales PASS. No se atribuye una segunda ejecución
completa a esa corrección de prueba; la CI final ejecutará la batería de nuevo.
Fixtures SQL reales2PASS más4unitarios; Terraform referencia12PASS.
Controlador53casos,52PASS/1SKIP; el test SQL opt-in se verificó por separado.

Revisión técnica independiente del conjunto: un P1 en la guardia destroy, que
rechazaba aws_iam_role_policy.bedrock_chat[0]. Regresión RED reproducida, índices
enteros canónicos admitidos y nombres/tipos/acciones/tags conservados; negativos
para índices inválidos, módulos, nombres ajenos y reemplazos. Batería controlador
conforme tras corregirlo. Logs ignorados integrated-*-full.log,
migration-ledger-green.log y controller-review-green.log en .work/aws-application/.
CI del SHA definitivo y reviews humanas siguen pendientes en este corte.

Receta/evidencias comprobadas también desde un ZIP de git archive del candidato
68ced055, sin archivos generados locales. Revisión técnica incremental APPROVE
tras corregir destroy/count; no sustituye las dos reviews humanas. La prueba
de preparación bloqueada usa explícitamente account_id pendiente, sin depender
de que falte una receta. Nuevo contrato de receta integrado en CI.
