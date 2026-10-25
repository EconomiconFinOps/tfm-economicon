# JUP-131: verificación de retirada con AWS CLI y ECS

Verificado el 25/10/2026. Base `1c4eda8a70ddd9412238f0c2b4fdef8073a9e10d`.
Trello: https://trello.com/c/NtiH8R4Z.
OpenSpec: `openspec/changes/jup-131-aws-cicd-defensa/`.

## Fallo observado y cambio

En la cuenta del máster 323188184300, el build de retirada de ensayo2
`f38dfed9-87dc-4808-b29b-e848f93f29ff` dejó el estado Terraform vacío y falló
después al comprobar residuos. AWS CLI devolvía el error exacto
`InvalidSecurityGroupRuleId.NotFound` de `DescribeSecurityGroupRules`, precedido
por `aws: [ERROR]: `. La expresión anterior sólo aceptaba la cabecera sin prefijo.

El verificador admite ambos formatos conservando la coincidencia exacta del
código y la operación. No interpreta AccessDenied, otra operación, un nivel
WARNING ni texto citado dentro de otra línea como prueba de ausencia.

La auditoría por SDK también encontró servicios INACTIVE y tareas
STOPPED aún visibles por etiquetas. El controlador los comprueba mediante sus
API autoritativas y exige cuenta, región, ciclo, ARN y clúster exactos. Sólo
retira de la lista activa servicios INACTIVE con desired/running/pending=0,
tareas con desiredStatus=lastStatus=STOPPED o una respuesta MISSING exacta.
Las respuestas vacías ambiguas, identidades distintas y errores fallan cerradas;
DRAINING, tareas en transición o contadores no nulos siguen activos.

## Verificación local

- El caso de prefijo produjo el RuntimeError esperado antes del cambio.
- Los casos ECS reprodujeron las referencias falsamente activas y la falta de
  comprobación del ciclo antes del cambio.
- `python -m unittest tools.aws_demo.test_retirement -v`: 12 métodos PASS,
  incluidos rechazo de denegaciones, operaciones distintas, identidad incorrecta,
  estados de transición y actividad residual.
- `python -m unittest discover -s tools/aws_demo -p 'test_*.py'`: 116 pruebas,
  107 PASS y 9 omitidas. Python 3.14; ejecución fuera del sandbox por las ACL de
  sus directorios temporales de Windows. Ninguna prueba llama a AWS ni a modelos.
- OpenSpec estricto, trazabilidad JUP, higiene del repositorio y
  `git diff --check`: PASS. El comprobador de higiene necesitó acceso a crear
  procesos Git fuera del sandbox (EPERM inicial).

## Cierre real y límites

El 25Oct a las19:00:19 UTC una auditoría de sólo lectura comprobó 58 referencias
etiquetadas, todas retiradas o pendientes de borrado programado, y estado vacío.
La consulta anterior de las18:54 tenía62; las etiquetas de recursos retirados
desaparecen de forma eventual. Tras revisión independiente favorable del cierre
(113 comprobaciones offline), se retiraron Scheduler y lease del ciclo. La
política temporal de su zona privada quedó ausente a las19:00:43 UTC. La zona
pública y el bootstrap se conservan. El build original sigue FAILED: fue un cierre
operacional asistido, no una ejecución automática correcta del verificador.

La inspección posterior confirmó ausencia de namespace, zona privada, snapshots
y backups retenidos. Los dos grupos RDS indicaban0 bytes, pero sus streams tenían
metadatos de eventos; se conservaron al no poder afirmar que estuvieran vacíos.
KMS/Secrets Manager mantienen borrados programados. No se afirma coste cero.

Recibos sin secretos bajo `.work/master-rehearsal/ensayo2/`:
`final-retirement-error-public.json`, `authoritative-residual-audit.json`,
`control-closeout-review.json`, `control-closeout.json`,
`temporary-policy-closeout.json` y `retirement-inspection.json`.

Este cambio no modifica aplicaciones, ApiError ni starlette==1.9.0. No demuestra
aceptación pública, salud AMQP ni un nuevo despliegue; requiere integrar el
candidato y repetir el ensayo. No extiende la excepción de reviews de PR167.
