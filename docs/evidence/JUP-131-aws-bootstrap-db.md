# JUP-131 — bootstrap privado de bases

Verificado el22/10/2026 en el worktree de PR146. Cambios locales posteriores a
`3e543b6f`, todavía sin publicar ni cubiertos por su CI. No se han ejecutado
operaciones de cuenta AWS, apply, tareas ECS o despliegues.

## Implementación

`tools/aws_demo/bootstrap.py` comprueba contexto CodeBuild, config local ligada
por SHA256 a ConfigKey, SHA de fuente, caducidad e identidad del deploy role.
Valida imágenes/digests, referencias, subredes y rol antes de preparar secretos.
El script no construye clientes SDK durante importación ni ejecución local
ordinaria; rechaza entradas incompletas antes de desplegar tareas.

Genera un bundle privado en Secrets Manager que conserva las contraseñas y
claves aleatorias de todo el ciclo. Los secretos runtime se derivan de ese
bundle, de modo que un reintento tras escritura parcial no genera credenciales
incompatibles. DescribeSecret verifica propiedad por ARN/etiquetas; valores
existentes distintos se rechazan sin sobrescribirlos. Los inputs públicos de
las tareas contienen ARNs y endpoints, sin contraseñas. El bundle adicional
debe incluirse en la estimación pendiente del ensayo.

`tools/aws_demo/private_tasks.py` registra definiciones temporales, lanza tareas
Fargate privadas y espera STOPPED con exitCode entero0. Public IP desactivada,
usuario no root de las imágenes, raíz de solo lectura y volumen efímero `/tmp`.
Ante timeout intenta parar la tarea y retira la definición; si falla la retirada,
registra CLEANUP_FAILED y devuelve error. El manifiesto se escribe atómicamente
y el runner lo conserva en el bucket privado al terminar el comando, incluso
si este falla. Nunca limpia ARNs devueltos fuera del ciclo/cuenta/familia esperados.
Down también busca definiciones activas huérfanas del prefijo bootstrap antes de
destruir el cluster: exige cuenta/familia y etiquetas de ciclo/fuente exactas para
retirarlas. El inventario separa definiciones INACTIVE de recursos activos y
mantiene explícitamente cost_zero_verified=false.

Los comandos en las imágenes son `python -m app.aws_bootstrap database`:

1. Backend ejecuta sus migraciones como propietario y concede permisos DML.
2. Processor migra el esquema operativo y pgvector, con dimensión nativa
   explícita, y concede los permisos de aplicación.

`app/aws_bootstrap_common.py`, idéntico en ambas imágenes, exige ECS explícito y
la identidad STS del rol bootstrap del ciclo. Lee únicamente referencias
permitidas. Los DSN de aplicación deben coincidir con endpoint/base/usuario del
stack y usar verify-full. El administrador se conecta con la CA RDS empaquetada.
Las contraseñas de roles se convierten en verificadores SCRAM antes de ejecutar
el DDL; los valores no aparecen en argumentos de comandos ni salida de éxito/error.
Se rechazan roles elevados, membresías y objetos propios inesperados. Las
aplicaciones reciben DML y no CREATE/TEMPORARY en las bases de aplicación.

Processor incorpora modo `PROCESSOR_SCHEMA_MODE=verify`: comprueba ledger y
tablas/columnas requeridas sin migrar. Mantiene la comprobación de dimensión del
vector legacy. Terraform fija verify en ambos servicios, enlaza backend con el
pool/client Cognito y separa rol/SG del bootstrap. Solo ese SG accede a RDS5432
y administración MQ443; no se abre ingreso público.

## Evidencia reproducible

- `python -m unittest discover -s tools/aws_demo -p 'test_*.py' -v`:
  **43PASS/1SKIP**, este último requiere opt-in PostgreSQL. Incluye pruebas de
  reintento de secretos, rechazo de snapshots ajenos, lifecycle ECS, timeout,
  errores de salida, barrido de definiciones huérfanas e inventario acotado.
- Backend: `tests/test_aws_bootstrap_jup131.py` y
  `tests/test_bootstrap_contract_jup131.py`: **11PASS** Windows. Junto al bloque
  S3/HMAC/TLS/cargas previo: **106PASS Linux/Python3.12**, sin red, raízRO y tmpfs.
- Processor: `tests/test_schema_verify_jup131.py`,
  `tests/test_aws_bootstrap_jup131.py`, `tests/test_chat_runtime_jup035.py`:
  **14PASS Windows**.
- PostgreSQL16/pgvector desechable: `tests/test_schema_verify_pgvector_jup131.py`
  **2PASS Windows y Linux**. El arranque funciona con un rol de solo lectura,
  rechaza un ledger incompleto y no ejecuta DDL. El bootstrap de roles se repite
  conservando login/DML; crear tabla normal, temporal o esquema resulta denegado.
  Combinados con los anteriores: **16PASS Linux**. El aviso de reflexión del tipo
  vector no afecta a la comprobación de nombres de columnas.
- Terraform referencia **12PASS** y control bootstrap **1PASS**, proveedores
  mock. Incluye identidad del rol/boundary, SG privados y configuración Cognito.
- El SDK del controlador reutiliza siete pins/hashes del lock de documentos del
  backend. Paridad comprobada con el SDK instalado en la imagen Linux; el venv
  Windows contiene una revisión posterior y su intento offline de instalar el
  pin anterior no es prueba del lock. CodeBuild instala su lock explícitamente.

Los tests PostgreSQL usan exclusivamente `economicon-jup131-native-vector-test`,
sin volúmenes, en DockerServer. Cada caso crea y elimina su propia base UUID;
los roles de prueba se retiran al terminar. El test Linux usa el puerto remoto
loopback25432; no accede a RDS ni a otros despliegues.
Logs locales ignorados en `.work/aws-application/`: `bootstrap-all-controller`,
`db-bootstrap-green`, `proc-bootstrap-green`, `schema-verify-pg`,
`linux-bootstrap-green`, `linux-bootstrap-sql-green`, `bootstrap-role-green`,
`bootstrap-control-terraform` y `backend-bootstrap-image`.

## Pendientes del objetivo completo

Ampliación local del 22/10: administración MQ e identidad Cognito/asociaciones
implementadas; 20 tests backend PASS incluyendo bootstrap DB, MQ e identidad.
Las llamadas MQ/Cognito son simuladas; asociaciones SQL con migración inicial
real en SQLite. Pendiente aceptación específica con PG y RabbitMQ real.
Comprobación posterior: también 20 PASS en Linux sin red y raíz de solo lectura;
`test_postgresql.py` PASS en PostgreSQL16 con asociación y rechazo de membresía
ajena. `test_bootstrap_broker_wire_jup131.py` PASS con RabbitMQ3.13 desechable:
reintento de bootstrap, publicación confirmada/consumo, denegación de otra cola
y de administración. Retirados broker/volumen y bases temporales. Estas pruebas
sustituyen esos dos pendientes locales; TLS/SDK de Amazon MQ y Cognito real
siguen sin comprobarse. Controlador final 44 PASS/1 SKIP, 45 casos totales.
Terraform referencia 12 PASS incluye marcador Cognito inmutable y auth
administrativa sin permitir USER_PASSWORD_AUTH público. El controlador de cuatro
tareas está probado con clientes simulados para éxito y fallo MQ, manifiesto y
retirada de definiciones; `test_bootstrap.py` 5 PASS. No implica aceptación AWS.

Faltan costes/corpus y vectorización reales, checks funcionales y receta completa,
integrar develop/JUP-132 y validar el SHA final en CI. No habilitar aplicaciones
usando únicamente este script ni interpretar exit0 como aceptación funcional.

La comprobación live de TLS, IAM, SDK, ECS, DNS, modelos y recorrido funcional
queda para el ensayo autorizado. El paquete mantiene aws_deployable=false.

Referencia de administración RabbitMQ:
[Amazon MQ: puertos y endpoints](https://docs.aws.amazon.com/amazon-mq/latest/developer-guide/working-with-rabbitmq.html).
