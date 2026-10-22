# JUP-131 — preparación del runtime privado ECS

Verificación: 2026-10-22. Rama `feat/JUP-131-aws-cicd-defensa`,
[PR146](https://github.com/EconomiconFinOps/tfm-economicon/pull/146), cambios
locales posteriores al head publicado `3e543b6f`. Esta evidencia no declara
despliegue, permisos efectivos o aceptación funcional AWS.

## Contratos implementados

- `apps/{backend,processor}/app/aws_runtime.py`: adaptación explícita ECS antes
  de leer Settings. Extrae `CHAT_HMAC_KEY`, la retira del entorno del proceso y
  escribe el valor en un fichero0600 dentro de un directorio temporal0700. El
  backend recibe `CHAT_SERVICE_HMAC_KEY_FILE`; processor, `CHAT_SIGNING_KEY_FILE`.
  La ausencia/configuración incorrecta aborta sin mostrar el valor. El modo local
  conserva sus ficheros y no realiza peticiones de metadatos.
- Processor obtiene su dirección IPv4 de los metadatos de su contenedor; exige
  `awsvpc` y una sola dirección RFC1918. Endpoint fijo link-local, timeout2s,
  respuesta máxima64KiB, sin proxy ni redirecciones. Terraform añade DNS privado
  `processor`, registro ECS y conexión SG backend→processor8003; sin ingreso público.
- Ambos servicios empaquetan el bundle CA público de RDS España, con hash
  fijado en el módulo y procedencia en `app/resources/README.md`. ECS exige
  `sslmode=verify-full` en ambos DSN y configura `PGSSLROOTCERT`. No se amplía
  la lista de opciones DSN permitidas ni se descargan certificados en ejecución.
- Almacenamiento documental: modo `DOCUMENT_S3_AUTH_MODE=iam`, región/endpoint
  España explícitos y cadena de credenciales SDK del rol. Rechaza claves
  documentales estáticas mezcladas y endpoints alternativos. MinIO estático
  conserva su modo anterior. Presign real comprobado con credenciales temporales
  sintéticas: conserva el token de sesión, tamaño firmado y caducidad.
- Terraform concede a backend lectura/escritura/borrado de los prefijos
  `staging/` y `confirmed/`; processor lee `confirmed/` y limpia ambos prefijos.
  Permisos KMS ligados al servicio S3 regional; processor no obtiene PutObject.
  CORS de documentos permite PUT solo desde el origen HTTPS del frontend.
- Runner incorpora entorno público y permisos Titan/perfil al plan inicial,
  antes de los futuros trabajos privados. La fase validate compara metadatos
  GetInferenceProfile con identidad, estado, tipo y conjunto exacto de destinos
  EU revisados. El deploy role obtiene solo lectura de los dos perfiles fijados;
  la invocación sigue en roles ECS. La build frontend recibe los nombres reales
  de configuración Cognito usados por la aplicación.

## Verificación reproducible

Desde `apps/backend`, usando dependencias de desarrollo instaladas:

```sh
python -m pytest tests/test_aws_runtime_jup131.py tests/test_document_iam_jup131.py tests/test_document_uploads.py -q -p no:cacheprovider
```

**95PASS** en Windows/Python3.11 y Linux/Python3.12. La ejecución Linux usa una
imagen propia `economicon-jup131-aws:backend-tests`, usuario no root, `--network
none`, `--read-only` y tmpfs en `/tmp`. Comprueba también los permisos POSIX0600/
0700; los originales de carga documental pasan sobre SQLite. Las dos copias de
runtime y almacenamiento se prueban por separado. Los avisos SQLite sobre el
adaptador datetime pertenecen a Python3.12; no son fallos.

Desde `apps/processor`: `python -m pytest tests/test_chat_runtime_jup035.py -q`
→ **7PASS**, conserva el supervisor y el propietario único de recursos.

Desde la raíz:

```sh
python -m unittest discover -s tools/aws_demo -p 'test_*.py' -v
terraform -chdir=infra/aws-reference test
terraform -chdir=infra/aws-bootstrap test
```

Controlador **30PASS/1SKIP** (PostgreSQL real requiere opt-in explícito).
Terraform referencia **12PASS** y bootstrap **1PASS**, con proveedores mock,
sin credenciales ni recursos. Las pruebas nuevas reprodujeron primero falta de
adaptación IAM/HMAC/TLS/perfiles. Los overrides del contrato ECS se materializan
durante plan; no interpretar recursos simulados como recursos de la cuenta.
Logs locales ignorados: `.work/aws-application/{rds-green,linux-runtime-green,
processor-runtime-regression,runner-bedrock-green,runtime-terraform-green,
metadata-iam-green}.log`.

## Límites y siguiente trabajo

No se ejecutan peticiones AWS en estas pruebas. La descarga del certificado
público procede de PKI oficial, sin acceso a la cuenta. TLS real contra RDS,
resolución Cloud Map, permisos del rol, emisión de secretos y acceso a modelos
se comprobarán en el ensayo autorizado.

El avance posterior de tareas/migraciones/roles DB y modo verify de processor
está en [bootstrap DB](JUP-131-aws-bootstrap-db.md); sustituye ese pendiente de
este corte. Faltan MQ, fixtures/usuario Cognito/corpus, comprobaciones funcionales
y receta real. También están pendientes
integración de develop/JUP-132, compatibilidad de recursos de chat y CI del SHA
final. El paquete continúa bloqueado; no habilitar aplicaciones ni declarar READY
a partir de este documento.

Fuentes oficiales consultadas el22/10:

- [Metadatos de contenedor Fargate v4](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-metadata-endpoint-v4-fargate-examples.html).
- [TLS y CA RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html).
- [Verificación TLS PostgreSQL en RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Concepts.General.SSL.html).
