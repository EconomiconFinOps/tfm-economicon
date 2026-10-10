# Chat generativo — JUP-035

[Tarjeta](https://trello.com/c/BJfABykd). El backend conecta el chat con el
gateway existente de JUP-023/108. El processor conserva su configuración y su
contrato FinOpsResponse; el chat usa un contrato de afirmaciones con evidencia.

## Configuración

Sobre un stack ya configurado conforme al README, selecciona:

```dotenv
CHAT_PROVIDER=litellm
CHAT_MODEL=economicon-chat
CHAT_TIMEOUT_SECONDS=30
CHAT_MAX_OUTPUT_TOKENS=1600
```

`docker-compose.yml` inyecta `BACKEND_LITELLM_API_KEY` como `LITELLM_API_KEY`
en el backend. Debe ser una clave virtual autorizada con acceso al alias de
chat y, si corresponde, de embeddings; no uses la clave maestra ni la clave
upstream. La URL es `LITELLM_BASE_URL`. No se crean claves ni se modifican
presupuestos al activar este código. Para consultar documentos reales usa la
configuración JUP-022 de embeddings y el corpus reindexado. `LLM_PROVIDER`
continúa controlando solo el processor; no activa el chat.

El modo por defecto es `CHAT_PROVIDER=mock`, una plantilla claramente marcada
en la interfaz para desarrollo y pruebas sin consumo. Con `litellm` una clave
ausente o inválida no provoca fallback a la plantilla. Los fallos de generación
producen 503 con mensaje fijo; la aplicación no imprime la respuesta del
proveedor ni sus cabeceras. Una petición permite una sola generación, sin
reintento automático. El plazo es por generación, adicional al retrieval;
la resolución DNS mantiene la limitación del transporte JUP-022.

## Uso y comprobación

1. Entra con una sesión autorizada y selecciona tenant.
2. Abre Assistant, crea una conversación y pregunta sobre documentos ingeridos.
3. Cada afirmación aceptada incluye referencias que abren la fuente y el pasaje
   de apoyo. Sin contexto se muestra evidencia insuficiente sin llamar al modelo.
4. Para costes por aplicación/equipo/proyecto/etiqueta activa **Consultar costes
   por propiedad** y completa la selección. JUP-037 calcula de forma determinista
   antes de generar; el snapshot de coste completo conserva periodo, monedas,
   procedencia y limitaciones. El modelo no ejecuta SQL ni elige tenant.
5. Recarga la conversación: mensajes, citas y metadatos deben conservarse.
   Una sesión de otro tenant no puede acceder a ese detalle.
6. Ante error, el borrador permanece disponible. En el chat documental la
   pregunta ya está guardada; reintentar crea otro intento visible, no una
   operación idempotente. La consulta estructurada de costes falla antes de
   guardar mensajes si la generación falla.

La pregunta está limitada a 4.000 caracteres; cada fuente a 4.000, hasta 20
fuentes. Se conservan hasta ocho afirmaciones. No se usa historial como contexto
(JUP-041). No se habilitan ahorro, anomalías, ejecución de acciones o formato
ejecutivo/técnico. JUP-036 aún no está integrado en la base de esta rama:
no se afirma soporte generativo de su contrato por suscripción/servicio ni
selección automática de herramientas del catálogo completo de JUP-084.

## Verificación y límites

Desde `apps/backend`:

```text
python -m pytest tests/test_chat_generation.py tests/test_chat_generation_api.py -q
```

La prueba opcional CockroachDB usa `JUP086_COCKROACH_TEST_URL` y las barreras
de `tests/tenant_isolation_support.py`: base vacía desechable, loopback, puerto
no predeterminado y organización `processor-integration-tests`. Nunca la
dirijas a una base de datos de aplicación. Sin ella ese caso se omite.

El control de JUP-069 envía las 28 preguntas a la API en el escenario sin
contexto: acredita abstención, persistencia y ausencia de llamadas al modelo;
**no mide calidad generativa**. Para la campaña con proveedor real reutiliza
[JUP-070](../validation/JUP-070-evaluation.md), sus entradas versionadas y el
corpus: registra SHA, configuración, gasto y resultados sin versionar respuestas
crudas ni credenciales. Deben mantenerse separados los juicios humanos y los
resultados automatizados.

Las guardas comprueban formato, pertenencia de fuentes, citas literales,
signos/unidades y ausencia de nuevos tokens numéricos. No prueban equivalencia
semántica, causalidad ni resistencia universal a prompt injection. Pueden
rechazar un cálculo correcto o una cifra reformateada: los cálculos pertenecen
a herramientas deterministas. Una cita válida no acredita que el modelo haya
interpretado bien su contenido. La aceptación requiere evaluación de calidad.
