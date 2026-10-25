# JUP-131 — Alias de atributos en el bloqueo DynamoDB

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
ciclo, SHA, ConfigKey y fase esperada. No cambia la arquitectura, los permisos,
el esquema de datos, la aplicación, ApiError ni Starlette1.9.0.

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

Pendientes: revisión independiente, CI remota, integración autorizada y reintento
con nuevo SHA/CI/ventana. Las excepciones previas de PR161 y PR163 no conceden
automáticamente bypass para esta corrección. No se ha validado aún la aplicación
funcionando en AWS ni el desmontaje de infraestructura real.
