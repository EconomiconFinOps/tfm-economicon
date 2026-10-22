# CI/CD AWS y primer ensayo — JUP-131

Implementación preparada el21/10/2026. [Trello](https://trello.com/c/NtiH8R4Z),
[plan](../planning/aws-cicd-defensa.md), [decisión](../adr/ADR-0026-aws-defense-lifecycle.md).
**No se ha desplegado nada en AWS.** El ensayo1 está preparado localmente, pero
no es lanzable hasta completar sus entradas y la evidencia funcional pendiente.

## Corte de verificación — 22/10/2026

La [CI39681182813](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39681182813)
terminó SUCCESS para `3e543b6fd58283c5d942ce9899fa7a00faa1d985`: ocho jobs
técnicos conformes y JUP policy omitido en el evento push. Incluye PostgreSQL
real, controlador offline, backend/processor, frontend y OpenSpec. No valida los
cambios locales posteriores de Bedrock ni una ejecución en AWS.

La PR146 permanece en borrador, sin reviews publicadas. Tras fetch, develop
está en `4567e8e7`; merge-tree detecta un conflicto textual en
`docs/continuidad/README.md`. Además incorpora JUP-132 (modelo generativo y
recursos v4), que requiere comprobar compatibilidad con Bedrock antes de publicar
el conjunto. También coincide el número ADR-0026 de ambas ramas: resolver el
índice y numeración al integrar, conservando los documentos.

Reejecutado localmente: controlador Python27PASS/1SKIP (PostgreSQL necesita
opt-in), Terraform referencia10PASS con mocks y `git diff --check` conforme.
El contrato de perfiles Bedrock ya está conectado al preflight del runner;
no se ha ejecutado contra la cuenta. El hito posterior de runtime privado
S3/HMAC/TLS tiene95PASS Linux, controlador30PASS/1SKIP y Terraform13PASS mock;
ver [evidencia y límites](../evidence/JUP-131-aws-runtime.md). No cubre las tareas
de bootstrap/checks que siguen pendientes.
`prepare.py --allow-incomplete` conserva `aws_deployable=false` y
`aws_preflight_executed=false`. No se llama a AWS.

### Qué desbloquea el primer ensayo

| Bloque | Trabajo o dato concreto | Criterio para avanzar |
| --- | --- | --- |
| Código pendiente | Cerrar Bedrock, tareas privadas de bootstrap, fixtures y checks funcionales; conectar configuración/outputs y permisos runtime | Receta real `infra/aws-cicd/release.json`, scripts existentes, hashes y evidencias verificables; sin comandos REPLACE |
| Integración y aceptación | Reconciliar develop, probar los recursos de chat actuales, publicar el candidato y obtener revisión/validación según CONTRIBUTING | CI SUCCESS del SHA final; no reutilizar el run de3e543b6f para código posterior |
| Acceso a cuenta | ID12dígitos y acceso mediante identidad/rol autorizado; España habilitada y boundary aprobada | Preflight futuro verifica identidad, cuotas, AZ, versiones RDS/MQ y permisos efectivos |
| DNS | Zona pública Route53 o delegación de la subzona de `danteinferno.es`, con zone ID | Control de `economicon.danteinferno.es` y `origin.economicon.danteinferno.es` para certificados y registros |
| Conexión de fuente | ARN CodeConnections AVAILABLE en París para este repositorio | Instalación de GitHub completada; origen manual fijado al SHA revisado |
| Secretos y modelos | ARN de los secretos GitHub/MQ en París, boundary IAM; disponibilidad y permiso de los modelos elegidos | Solo referencias públicas en configuración; valores en Secrets Manager. Metadatos/permisos de modelo verificados en la cuenta, no inferidos del catálogo |
| Coste y ventana | Crédito utilizable real, estimación del ciclo completo, margen residual, caducidad UTC y horario de defensa29/10 | Coste compatible con60€ y ventana de ensayo acordada. El ejemplo23/10 18:00UTC debe confirmarse antes de usarlo |
| Lanzamiento | Preparación del bootstrap de control y paquete revisado; autorización futura de despliegue | No ejecutar apply ni iniciar pipelines hasta recibir esa autorización |

Los tres primeros bloques de código/integración se preparan en el proyecto;
las referencias de cuenta, DNS, conexión y crédito deben proceder de sus
administradores. No pedir ni guardar contraseñas o tokens en Git/chat. El primer
ensayo verificará arranque, aceptación funcional, retirada y residuos: esos
resultados no pueden acreditarse antes del despliegue autorizado.

## Componentes y uso local

- `infra/aws-bootstrap/`: control en París, state S3 privado/versionado, artefactos
  separados, lease DynamoDB del dominio, roles y dos pipelines manuales.
- `infra/aws-reference/`: arquitectura existente en España, edge en us-east-1;
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

1. Cuenta12dígitos y permisos de la identidad administradora. España debe estar
   habilitada (opt-in), con tres AZ utilizables y cuotas/motores/tamaños comprobados.
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
8. **Aceptación de aplicación:** completar PostgreSQL/Cognito/Bedrock y datos
   reproducibles, según las brechas de la guía original. Crear y versionar
   `infra/aws-cicd/release.json` a partir del ejemplo con hash del árbol `apps/`,
   evidencias en `docs/evidence/` verificadas por SHA256 y scripts Python reales
   en `tools/aws_demo/`. No rellenar hashes ficticios ni sustituir checks por true.

La entrega inicial de CI/CD no incluía esas adaptaciones. El trabajo posterior
incorpora [runtime privado](../evidence/JUP-131-aws-runtime.md) y
[bootstrap de bases](../evidence/JUP-131-aws-bootstrap-db.md). Todavía faltan
MQ/identidades/fixtures/checks y receta completa; su ausencia bloquea validate
ANTES de crear infraestructura demo. No hay aceptación funcional AWS.

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
inventario/costes en España, us-east-1 y París y registrar cada remanente. El runner
consulta recursos etiquetados del ciclo en España/us-east-1 y conserva el lease
si quedan activos; registra KMS/Secrets con borrado diferido. La
verificación independiente de facturación y recursos no gestionados es manual;
no se presenta como automatizada. Tras los tres ciclos, retirar bootstrap según
plan separado; el bucket de state tiene `prevent_destroy` y nunca se vacía por demo.

## Evidencia y límites

Ver [evidencia JUP-131](../evidence/JUP-131-aws-cicd.md). Pruebas locales/mock no
acreditan permisos/cuotas, soporte de versiones, duración, coste, DNS/TLS, build
Linux real, bootstrap SQL ni aceptación de la aplicación en AWS.
