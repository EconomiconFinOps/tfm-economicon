# Preparación y comprobaciones previas

Antes de preparar cualquier entorno, ejecutar las comprobaciones del README
sobre los artefactos publicados. La regeneración opcional se hace en un destino
temporal distinto; no reemplazar `generado/` antes de validar su integridad.

Aplicar primero las [puertas de entrada del ensayo integrado](ensayo-integrado.md). Estos comandos son instrucciones para una ejecución futura autorizada; no se han ejecutado como ensayo en esta preparación.

## 1. Fijar la ejecución

Elegir el ensayo JUP-065 de la [decisión de datos/alcance](README.md): muestra junio de 2024,Core cargado,Growth vacío,
perfil demo apagado y `COST_REFERENCE_DATE=` vacío. JUP-107/119 con fecha simulada
30/10/2026 requiere otro proyecto,volúmenes y registro;no alternar ambos datasets
dentro de esta instancia. Registrar variante de presentación:7 min o 9 min con
[tramo JUP-036](guion.md).


Responsable de preparación: liderazgo/pairing de JUP-065. Validador: Víctor según Trello; su ejecución de f27eb7f con mock del 11/10 es histórica y no valida este nuevo entorno. Usar una instancia desechable dedicada, nunca los volúmenes de otro trabajo. Registrar SHA de aplicación, SHA del paquete, imágenes, URLs y nombre Compose en `registro-ensayo.md`. El commit de preparación no implica que el MVP completo esté integrado.

La aplicación integrada elegida debe tener las correcciones necesarias para modelo real, retrieval y citas. Consultar su README y configuración vigente: este paquete no crea secretos ni cambia el despliegue. Proveer por canal seguro las variables de BD, RabbitMQ, sesión y gateway; para seed demo establecer `DEMO_SEED_ENABLED=true` y una `DEMO_PASSWORD` externa no heredada. La cuenta creada es `operator@example.com`, con tenants `tenant-core` y `tenant-growth`.

Para una instancia local desechable se requiere el opt-in `RUNTIME_ENVIRONMENT=development` y `ALLOW_INSECURE_LOCAL_DATABASE=true`. Fijar puertos libres para frontend/API/processor/Azure/BD/broker. Un nombre Compose diferente aísla volúmenes, pero **no** evita choques de puertos. No imprimir `docker compose config` con valores resueltos ni adjuntar `.env`.

Requisitos de arranque incorporados por **A / JUP-122 (PR130)**:

- `CHAT_HMAC_FILE`: ruta absoluta a un archivo privado del operador, al menos
  32 bytes y legible por el UID 10001 del contenedor. Se monta sólo lectura en
  backend/processor; no imprimirlo, incluirlo en evidencias ni rotar uno existente.
- Elegir `CHAT_PRIVATE_SUBNET` libre y `PROCESSOR_CHAT_PRIVATE_IP` dentro de ella;
  el puerto privado 8003 no se publica. El nombre de proyecto no evita solapamientos.
- Mantener `CHAT_ENABLED=false` durante la preparación sin inferencias. A integrada
  no implica aceptación de **B / JUP-123**. Sólo tras esa aceptación y autorización
  explícita del entorno/proveedor/presupuesto, fijar `CHAT_ENABLED=true` en el
  archivo privado del ensayo y recrear backend y processor con la misma configuración.
- `backend-migrate` debe terminar con código 0 antes del backend, que verifica el
  esquema. No exigir que ese servicio de una sola ejecución permanezca running.
  El processor conserva sus migraciones, incluidas las vectoriales.
- El build obtiene el tokenizer fijado y verifica revisión/tamaño/SHA; requiere
  acceso HTTPS a las fuentes del build. El arranque no descarga ese recurso.
  Seguir [la configuración de chat del README raíz](../../../README.md).

Para un recorrido parcial mock usar `AI_EXECUTION_MODE=development`,
`LLM_PROVIDER=mock`, `EMBEDDING_PROVIDER=mock`, `EMBEDDING_DIMENSION=8`; no mezclar
ese índice con el ensayo real. Para IA, seguir la [configuración de gateway](../../../infra/litellm/README.md)
y el overlay `infra/litellm/compose.ai.yml`, con proveedores `litellm`, dimensión
compatible y clave de resumen independiente mediante `SUMMARY_API_KEY_FILE`.
Los comandos base siguientes no configuran ni activan por sí solos el gateway.
No se concede autorización de consumo mediante este documento.

Ejemplo PowerShell, desde la raíz del checkout **del MVP elegido**, después de completar su archivo de entorno:

```powershell
$demoProject = 'jup065-demo-ensayo01'
$demoEnv = '<ruta-absoluta-al-env-privado-del-ensayo>'
docker compose --env-file $demoEnv -p $demoProject config --quiet
docker compose --env-file $demoEnv -p $demoProject up -d --build
docker compose --env-file $demoEnv -p $demoProject ps --all
```

No activar `--profile demo`, ni heredarlo en `COMPOSE_PROFILES`; no ejecutar `demo_data.py apply` en esta instancia. `DEMO_SEED_ENABLED=true` crea las cuentas/tenants, no equivale a cargar costes con el perfil `demo`.

Los marcadores se rellenan con el despliegue elegido; no son credenciales ni comandos ejecutados en esta preparación. Exigir healthchecks correctos de backend, processor, Azure simulada, BD y broker, y probar el frontend con un navegador real, CORS sin bypass. Verificar que frontend y backend apuntan al mismo entorno. No confundir salud HTTP con integración funcional.

## 2. Cargar y repetir los costes

La imagen Azure debe usar el CSV exacto de `generado/sources/fixtures/azure-cost/EA-Cost-Actual.sample.csv`. Su hash está en `procedencia.json`. Fijar explícitamente `AZURE_COST_DEFAULT_SCENARIO=normal` y `AZURE_COST_PAGE_SIZE=10` en el entorno privado. El comando existente sin `--definition-file` coincide con `generado/consulta-costes.json` en la base fijada; verificar esa igualdad si se cambia de versión.

```powershell
docker compose --env-file $demoEnv -p $demoProject exec -T processor python -m app.run_azure_cost_ingestion --tenant-id tenant-core --subscription-id 64e355d7-997c-491d-b0c1-8414dccfcf42
```

Esperado: `status=completed`, `row_count=38`, `persisted_row_count=38`, cuatro páginas con tamaño 10, sin reintentos en escenario normal. Guardar el `run_id` y el JSON de ejecución. No cargar CSV de costes mediante el formulario de texto documental `/ingest`: son flujos diferentes.

Repetir **el mismo comando y la misma definición**: debe conservar `run_id`, 38 registros y 0,06 USD, sin duplicar costes. No cambiar la agrupación o periodo en una segunda ingesta del mismo tenant; las fuentes solapadas pueden producir `409 ambiguous_cost_source`. Para mostrar un desglose, cambiar `group_by` en la consulta de lectura, no reingerir con otra definición.

Desde la sesión autenticada, comprobar:

```text
GET /billing/summary?start_date=2024-06-01&end_date=2024-06-20&group_by=resource_group
Authorization: Bearer <token solo en memoria>
X-Tenant-Id: tenant-core
```

Esperado: contrato 2, `available`, moneda USD, total `0.06`, conteo 38, ocho grupos según `costes-esperados.json`, sin dimensiones/fechas faltantes, ahorro `null`. Comparar grupos por valor/moneda y suscripción, sin exigir el mismo orden del JSON de referencia. DevTestLab/devtestlab se unifican en DevTestLab, ocho registros. El total se calcula antes de redondear: la suma de grupos mostrados puede diferir un céntimo. No inferir un ahorro de valores cero o de ausencia de datos.

En `/`, con el dashboard de JUP-055 integrado, seleccionar **Mes inicial `2024-06` y Mes final `2024-06`**. Ambos meses son inclusivos y la UI consulta `[2024-06-01, 2024-07-01)`; el valor inicial son los seis últimos meses completos UTC y no contiene esta muestra. La carga y el GET de referencia anteriores mantienen `[2024-06-01, 2024-06-20)`. En el CSV fijado, las 40 filas de esta suscripción terminan el 19/06 y producen 38 registros: ampliar la lectura hasta julio no añade filas. Confirmar esa igualdad en el despliegue elegido; no cambiar el periodo de carga ni presentar la muestra como factura del mes completo.

Verificar Growth vacío en el entorno dedicado. **JUP-119** sustituye la
herramienta antigua de JUP-106 por `scripts/demo_data.py`. El perfil `demo` o
`demo_data.py apply` carga Core y Growth; incluye la suscripción pública con
fechas desplazadas en Growth, además de datos sintéticos. No usar ese flujo en
este ensayo de la muestra original de junio de 2024. Ver [guía de datos](../../data/azure-sample-dataset.md).

Si se reutiliza un entorno propio donde ya se aplicó JUP-119, inspeccionar primero:

```powershell
docker compose --env-file $demoEnv -p $demoProject --profile demo run --rm --no-deps demo-data python scripts/demo_data.py status
```

`status` no carga costes. Requiere los servicios/imagen configurados y la BD
accesible; `--no-deps` evita arrancar dependencias incidentalmente. Si hay carga
previa, preferir **otro proyecto con volúmenes nuevos y puertos/subred libres**.
Como alternativa sólo sobre datos propios cuya retirada se haya autorizado:

```powershell
docker compose --env-file $demoEnv -p $demoProject --profile demo run --rm --no-deps demo-data python scripts/demo_data.py remove
docker compose --env-file $demoEnv -p $demoProject --profile demo run --rm --no-deps demo-data python scripts/demo_data.py status
```

`remove` actúa sobre todos los tenants del manifiesto; `--tenant` se rechaza.
Puede retirar episodios derivados cuando no quedan otros costes en el tenant;
no es un reset limitado a Growth. Conserva ingestas ajenas a las definiciones de
demo, incluida la muestra original: contrastar después billing de ambos tenants
con las expectativas de este paquete. No borrar datos de otros trabajos.
Registrar `COST_REFERENCE_DATE` vacío para esta ejecución (usa la fecha real); seleccionar
junio de 2024 explícitamente aunque JUP-119 cambie el periodo inicial de la UI.
No usar `open_ingestions` para inferir jobs pendientes; comprobar cada job por SQL.

## 3. Cargar el corpus y comprobar el chat

Ejecutar la validación offline de JUP-069 indicada en README. Las copias indexables están bajo `generado/sources/docs/assistant-corpus/` y aparecen en `manifest.yaml`; el corpus incluye FinOps, reglas, glosario y contexto de producto. No indexar `rubricas-privadas.json`, `prompts.json`, la batería JUP-069 ni este paquete de demo.

En el flujo existente `/ingest`, para cada documento permitido: seleccionar Core Finance, Source `assistant-corpus`, Artifact URI igual al path del manifest y Text content igual al documento íntegro. Guardar job/documento/chunks y esperar `completed`, no solo «encolado». Conservar el alcance declarado en manifest: la carga manual al tenant demo no prueba la implementación del enrutado global/dataset. En esta base la integración automática del manifest es un residual documentado.

Para obtener el estado sin depender de un endpoint de consulta de jobs, usar
CockroachDB del proyecto desechable. Rellenar el nombre de base (componente de
base de `DATABASE_URL`, no la URL completa) y el ID devuelto por `/ingest`.
Comprobar que el ID es un UUID antes de interpolarlo:

```powershell
$demoDatabase = '<nombre-de-base-del-ensayo>'
$demoJob = '<uuid-devuelto-al-encolar>'
$demoJob = ([guid]::Parse($demoJob)).ToString()
docker compose --env-file $demoEnv -p $demoProject exec -T cockroachdb /cockroach/cockroach sql --insecure --host=localhost:26257 --database=$demoDatabase --format=csv -e "SELECT id, tenant_id, status, artifact_uri FROM jobs WHERE tenant_id = 'tenant-core' AND id = '$demoJob';"
```

Este comando sólo corresponde al CockroachDB local desechable con opt-in
inseguro de §1; un entorno seguro requiere su conexión TLS autorizada. Esperado:
una fila, mismo ID y URI del documento permitido, tenant Core, `completed`.
Cero filas, `failed` o espera agotada bloquean ese paso. Adjuntar la salida
sanitizada por cada documento y los IDs/chunks de la recuperación posterior;
no inferir chunks ni éxito generativo del estado del job. No usar `local:smoke`
antes de la carga controlada, pues también ingiere datos y altera la línea base.

Antes de la sesión pública comprobar que la pregunta JUP-069-004 recupera el documento FinOps y que la cita abre evidencia pertinente. Si el contrato integrado requiere una carga distinta, registrar su comando validado en el ensayo. La preparación del corpus está hecha; la carga y compatibilidad de embeddings/modelo quedan por ejecutar en el MVP.

Para los prompts documentales usar **el panel lateral nuevo**, no la ruta de
consultas estructuradas `/assistant`. Con sesión Core, en `/`, pulsar
**«Abrir asistente» / «Asistente FinOps»**, **«Nueva conversación»**, escribir el
prompt completo en **«Pregunta»** y pulsar **«Enviar»**. El panel sólo aparece si
`GET /assistant/capabilities` responde `chat_enabled=true`. Con false está oculto
por diseño; registrar `blocked` para el tramo generativo, sin cambiar la variable
ni sustituirlo por la pantalla antigua para aparentar éxito.

La ruta `/assistant` sigue publicada, aunque ya no tiene entrada «Asistente» en
el menú. Sus modos Azure/propiedad/anomalía son estructurados y excluyentes; se
usan sólo para el tramo JUP-036. No aplicar al panel nuevo la instrucción antigua
de desmarcar «Consultar costes por propiedad»: pertenece a la otra pantalla.
Verificar selección de conversación, finalización (no texto provisional), cita
visible y persistencia al reabrir **«Historial»** después de recargar.

Registrar proveedor/modelo de consulta y embeddings, dimensión/versión de índice,
chunking, generación y hash del corpus. El corpus fijado en `generado/` conserva
su versión: no mezclarlo silenciosamente con el corpus actualizado por JUP-129.
Usar índice propio o documentar y revalidar un cambio de corpus antes del ensayo.
Comprobar mediante trazas seguras el proveedor realmente usado por el panel.
Con mock, indicar `blocked` para IA real. Aplicar todos los `required`, ningún
`forbidden` y las tolerancias `numbers`; una respuesta persistida no acredita calidad.

## 4. Controles para autorizar el ensayo

| Momento | Comprobación | Evidencia requerida |
| --- | --- | --- |
| Día anterior | Commit integrado y versiones fijadas; secretos y puertos configurados; servicios saludables | Identidad y recibo de arranque sin secretos |
| Día anterior | Primera carga y repetición idéntica; API coincide con referencia | Dos recibos de ingesta y respuesta de billing |
| Día anterior | Corpus completado; chat usa modelo real y dimensión compatible | IDs de indexación y traza de proveedor |
| Día anterior | JUP-069-004 con cita útil y recarga; 003 pide contexto; reservas 001/023/025 revisadas | Respuestas originales, rúbricas y capturas |
| Día anterior | Login, selección/cambio tenant, logout y ruta protegida | Registro de navegador |
| 30 minutos antes | Repetir health, login, muestra y una pregunta; sin cambios desde el ensayo | Hora, commit y resultado |
| 5 minutos antes | Pantalla legible, ventanas preparadas, reloj, plan alternativo identificado | Control del presentador |

Propuesta de aceptación del ensayo: todos los pasos principales `pass`, cero `fail`/`blocked`/`not_run`, duración objetivo siete minutos (hasta nueve con reserva) y reproducción por otra persona. Pendiente acuerdo/validación del equipo; no modifica criterios generales de JUP-070. Si un control obligatorio falla, solo se puede mostrar preparación o ensayo parcial identificado como tal.

## 5. Reinicio y recuperación

- Navegación/chat: cerrar sesión, volver a entrar, fijar Core y fechas; crear conversación nueva por caso. No reutilizar conversación con respuestas anteriores.
- Costes: repetir la misma ingesta; verificar que conserva conteo y total. Si hay solapamientos o contaminación, crear **otra instancia demo aislada con volúmenes nuevos y puertos libres**; conservar la anterior para diagnóstico. No borrar ni vaciar bases compartidas.
- Corpus: para repetir una carga completa sin acumular documentos, usar esa nueva instancia e indexar una vez cada documento del manifest. No hay reset destructivo automatizado en este paquete.
- Parada reversible al terminar: `docker compose --env-file $demoEnv -p $demoProject stop`. Conservar evidencias antes de cualquier limpieza futura. No se ejecuta `down -v` aquí.
