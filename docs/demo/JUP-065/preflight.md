# Preparación y comprobaciones previas

## 1. Fijar la ejecución

Responsable de preparación: liderazgo/pairing de JUP-065. Validador: Victor según Trello; pendiente ejecución humana. Usar una instancia desechable dedicada, nunca los volúmenes de otro trabajo. Registrar SHA de aplicación, SHA del paquete, imágenes, URLs y nombre Compose en `registro-ensayo.md`. El commit de preparación no implica que el MVP completo esté integrado.

La aplicación integrada elegida debe tener las correcciones necesarias para modelo real, retrieval y citas. Consultar su README y configuración vigente: este paquete no crea secretos ni cambia el despliegue. Proveer por canal seguro las variables de BD, RabbitMQ, sesión y gateway; para seed demo establecer `DEMO_SEED_ENABLED=true` y una `DEMO_PASSWORD` externa no heredada. La cuenta creada es `operator@example.com`, con tenants `tenant-core` y `tenant-growth`.

Para una instancia local desechable se requiere el opt-in `RUNTIME_ENVIRONMENT=development` y `ALLOW_INSECURE_LOCAL_DATABASE=true`. Fijar puertos libres para frontend/API/processor/Azure/BD/broker. Un nombre Compose diferente aísla volúmenes, pero **no** evita choques de puertos. No imprimir `docker compose config` con valores resueltos ni adjuntar `.env`.

Ejemplo PowerShell, desde la raíz del checkout **del MVP elegido**, después de completar su archivo de entorno:

```powershell
$demoProject = 'jup065-demo-ensayo01'
$demoEnv = '<ruta-absoluta-al-env-privado-del-ensayo>'
docker compose --env-file $demoEnv -p $demoProject config --quiet
docker compose --env-file $demoEnv -p $demoProject up -d --build
docker compose --env-file $demoEnv -p $demoProject ps
```

Los marcadores se rellenan con el despliegue elegido; no son credenciales ni comandos ejecutados en esta preparación. Exigir healthchecks correctos de backend, processor, Azure simulada, BD y broker, y probar el frontend con un navegador real, CORS sin bypass. Verificar que frontend y backend apuntan al mismo entorno. No confundir salud HTTP con integración funcional.

## 2. Cargar y repetir los costes

La imagen Azure debe usar el CSV exacto de `generado/sources/fixtures/azure-cost/EA-Cost-Actual.sample.csv`. Su hash está en `procedencia.json`. Configuración de escenario normal y tamaño de página 10. El comando existente sin `--definition-file` coincide con `generado/consulta-costes.json` en la base fijada; verificar esa igualdad si se cambia de versión.

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

En `/` introducir exactamente las fechas del guion (el valor inicial es el mes actual, que no tiene esta muestra). Verificar Growth vacío. No basar la comprobación de jobs pendientes en `open_ingestions`: en la base examinada cuenta todos los jobs, aunque su nombre sugiera otra cosa; comprobar el estado individual de los jobs.

## 3. Cargar el corpus y comprobar el chat

Ejecutar la validación offline de JUP-069 indicada en README. Las copias indexables están bajo `generado/sources/docs/assistant-corpus/` y aparecen en `manifest.yaml`; el corpus incluye FinOps, reglas, glosario y contexto de producto. No indexar `rubricas-privadas.json`, `prompts.json`, la batería JUP-069 ni este paquete de demo.

En el flujo existente `/ingest`, para cada documento permitido: seleccionar Core Finance, Source `assistant-corpus`, Artifact URI igual al path del manifest y Text content igual al documento íntegro. Guardar job/documento/chunks y esperar `completed`, no solo «encolado». Conservar el alcance declarado en manifest: la carga manual al tenant demo no prueba la implementación del enrutado global/dataset. En esta base la integración automática del manifest es un residual documentado.

Antes de la sesión pública comprobar que la pregunta JUP-069-004 recupera el documento FinOps y que la cita abre evidencia pertinente. Si el contrato integrado requiere una carga distinta, registrar su comando validado en el ensayo. La preparación del corpus está hecha; la carga y compatibilidad de embeddings/modelo quedan por ejecutar en el MVP.

Registrar proveedor/modelo exactos de **consulta y embeddings**, dimensión y versión de índice, chunking, configuración de generación, commit y hash del corpus; no guardar tokens. Comprobar el proveedor realmente usado por `/assistant` mediante trazas seguras. Si queda un mock, indicar `blocked` para el ensayo de IA real. No comparar únicamente textos idénticos: aplicar todos los `required`, ningún `forbidden` y las tolerancias de `numbers` de cada rúbrica.

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
