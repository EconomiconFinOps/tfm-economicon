# JUP-131 — Bloqueo DynamoDB y dependencias DNS privadas

Verificado el25/10/2026. Origen: chat «Preparar despliegue en AWS»,
`01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.

El segundo intento del primer ensayo, ejecución
`2855d9da-f725-443f-94c2-e6287f7c71a5`, fuente `6851ec7a`, superó validación,
las cinco imágenes y la generación del plan. El plan162altas/0cambios/0bajas
se revisó y aprobó. Apply se detuvo antes de inicializar/aplicar Terraform:
DynamoDB devuelve ValidationException porque `cycle` es palabra reservada
en ConditionExpression. El bloqueo quedó PLANNED y no se creó estado de aplicación.

La corrección usa un alias de atributo para `cycle` tanto al cambiar la fase
como al liberar el bloqueo. Se conservan las cuatro condiciones atómicas:
ciclo, SHA, ConfigKey y fase esperada. La aplicación, ApiError,
Starlette1.9.0, arquitectura y esquema de datos permanecen intactos.

## Verificación

- Regresión offline primero roja:10 fallos de subcasos sobre cuatro pruebas,
  por atributo reservado en transiciones, concurrencia y liberación.
- Tras corregir:95 pruebas totales,88 PASS/7 SKIP de integraciones opt-in.
  Cubren todo el ciclo de fases, los cuatro cambios concurrentes de identidad/fase,
  rechazo de escritor obsoleto y liberación del bloqueo tras destrucción vacía.
- DynamoDB real, cuenta del máster323188184300, tabla de control existente:
  el código anterior reproduce ValidationException; el nuevo acepta una actualización
  PLANNED→PLANNED. Lectura consistente antes/después confirma bloqueo idéntico.
  No se creó infraestructura para probar. Los recibos no contienen secretos.
- Retirada controlada del intento fallido14:09:29 Europe/Paris: pipeline Failed,
  sin estado ni recursos etiquetados del ensayo en Irlanda/Virginia; se invalidó
  el plan aprobado pasando el bloqueo a TEARDOWN, se retiró su Scheduler y
  se eliminó condicionalmente el bloqueo con ciclo/SHA/ConfigKey/fase exactos.
  Bootstrap y artefactos conservados. No queda retirada programada de ese intento.

Recibos locales ignorados en `.work/master-rehearsal/`: `lease-live-red.json`,
`lease-live-green.json`, `lease-red.log`, `lease-green.log` y
`attempt2-control-retirement.json`. Configuración y evidencias previas en `attempts/2/`.

## Dependencias de Cloud Map detectadas antes del siguiente intento

La política del rol deploy permitía `servicediscovery:*`, pero faltaban cuatro
permisos dependientes de Route 53. La simulación IAM de la política realmente
adjunta reproduce cuatro rechazos: crear, consultar, buscar y eliminar la zona
gestionada por Cloud Map. No es un fallo observado durante apply: se detectó
en la comprobación preventiva, antes de crear infraestructura de aplicación.

Se añaden sólo `CreateHostedZone`, `GetHostedZone`, `ListHostedZonesByName` y
`DeleteHostedZone`, condicionados a llamadas delegadas de
`servicediscovery.amazonaws.com` mediante `aws:CalledVia`. La creación exige
una VPC de Irlanda y excluye la ausencia de VPC, por lo que no concede creación
de zonas públicas. El permiso directo de registros permanece limitado a la
zona pública aprobada. No se concede administración DNS directa general.

Referencias de AWS consultadas el25Oct2026:

- [Permisos dependientes](https://docs.aws.amazon.com/cloud-map/latest/dg/cloud-map-api-permissions-ref.html).
- [Ciclo de creación y eliminación de zonas](https://docs.aws.amazon.com/cloud-map/latest/dg/security_iam_id-based-policy-examples.html).
- [Cloud Map admite sesiones delegadas](https://docs.aws.amazon.com/cloud-map/latest/dg/security_iam_service-with-iam.html) y [condición CalledVia](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_forward_access_sessions.html).
- [Condición Route53 VPCs](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/specifying-conditions-route53.html) y [CreateHostedZone admite una sola VPC](https://docs.aws.amazon.com/Route53/latest/APIReference/API_CreateHostedZone.html).

La prueba opt-in `tools/aws_demo/test_cloudmap_policy.py` evalúa el documento
real renderizado por Terraform con `SimulateCustomPolicy`, sin adjuntar políticas
ni crear zonas. Cubre 14 escenarios de acceso permitido y denegado: Cloud Map,
llamadas directas, otro servicio, región incorrecta y zona pública. La política
anterior falla en los cuatro casos positivos; la candidata los supera todos.
El contexto FAS de esta simulación es suministrado: la llamada efectiva de
Cloud Map sigue pendiente del ensayo. No se presenta como despliegue probado.

Plan bootstrap: 0 altas, 1 actualización de `aws_iam_role_policy.deploy`,
0 bajas; aún sin aplicar. Terraform mock: 1 PASS. Suite offline ampliada:
96 pruebas,88 PASS/8 SKIP; la nueva integración IAM es opt-in. Recibos en
`.work/master-rehearsal/cloudmap-policy-{red,green}.log`,
`cloudmap-policy-review.json`, `cloudmap-bootstrap-plan.log` y
`pr165-offline-green.log`.

Para repetir la evaluación con credenciales de lectura autorizadas: exportar
sólo el documento IAM del plan a un JSON local; establecer
`AWS_CLOUDMAP_POLICY_TEST_FILE` a ese archivo y ejecutar
`python -m unittest tools.aws_demo.test_cloudmap_policy -v`. Nunca exportar el
plan completo de aplicación, que puede contener valores sensibles.

Pendientes: revisión independiente del delta DNS, CI remota, integración autorizada y reintento
con nuevo SHA/CI/ventana. Las excepciones previas de PR161 y PR163 no conceden
automáticamente bypass para esta corrección. No se ha validado aún la aplicación
funcionando en AWS ni el desmontaje de infraestructura real.
