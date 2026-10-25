# JUP-035 - Contexto ampliado y compresion coordinada

Fecha: 2026-10-11. Diseno funcional aprobado por Paris en este chat:
aprovechar el contexto disponible, conservar los originales y bloquear el envio
solo en la conversacion durante su compresion. No implementado por este documento.

## Hechos comprobados

- OpenRouter anuncia 1048576 tokens de contexto para GLM-5.2 en DeepInfra/fp4.
  Fuente publica consultada: https://openrouter.ai/api/v1/models/z-ai/glm-5.2/endpoints
  Metadatos del proveedor, no ensayo extremo ni garantia de latencia.
- El chat limita a 8192 tokens variables y cuatro pares recientes.
- El resumen se dispara por historial elegible >6144 o presion >=8192; cada
  lote admite 4096 tokens incluidos schema y margen, salida 800 y payload 768.
- El transporte privado de resumen limita el cuerpo completo a 1048576 bytes;
  el chat tiene limite de cuerpo de 2097152 bytes. Bytes y tokens no equivalen.
- La cola de resumen actual vive en RAM, mientras historial y resumen son SQL.
  Deshabilitar un boton no protege otras pestanas, procesos ni un reinicio.

## Presupuesto propuesto

Mantener las protecciones de bytes existentes. El maximo util es el mayor
conjunto de pares completos que cumple simultaneamente los limites de contexto
del modelo, bytes del sobre serializado y reservas de instrucciones, esquema,
salida y margen. No convertir bytes a tokens mediante una constante aproximada.
El techo de tokens puede reducirse por configuracion; backend y processor deben
acreditar el mismo contrato antes de admitir solicitudes. No fijar 8192 como
techo artificial ni elevar automaticamente los limites del proveedor.

Conservar el mayor sufijo de pares completos que cabe junto con la pregunta,
evidencias verificadas y memoria disponible. Los pares ya cubiertos por un resumen
no se duplican automaticamente como historial. No truncar mensajes ni evidencia
esencial para aparentar que una solicitud cabe.

Planificar compresion antes de necesitar descartar historial no resumido. Cada
lote se construye contra tokens y bytes reales del sobre completo. Conservar
salida y validadores actuales inicialmente; la calidad de resumir mucho texto en
un payload pequeno requiere un ensayo especifico y no queda acreditada por los
metadatos del modelo. Si no cabe un solo par, devolver un limite explicito.

## Coordinacion propuesta

La admision de nuevas generaciones y el inicio de compresion deben compartir
una exclusion atomica por tenant, usuario y conversacion en el servidor. El
control debe ser durable y recuperable, no un booleano local del navegador.
Reutilizar la fila de conversacion y su transaccion cuando sea compatible;
concretar el esquema/versionado del estado antes de implementarlo. No editar
migraciones historicas ni introducir una migracion implicitamente.

La transicion de final de chat a compresion necesaria no deja una ventana para
admitir otra pregunta con memoria antigua. Solicitudes idempotentes y lectura
de resultados existentes siguen disponibles. Otras conversaciones no se bloquean.

Frontend conserva el borrador, deshabilita envio (incluido Enter) y muestra
Actualizando memoria mientras la conversacion esta ocupada. Recupera el estado
desde servidor al abrir o recargar; el boton no constituye la barrera de seguridad.

Exito significa resumen validado e instalado, no solo respuesta HTTP 200.
Error o plazo agotado conserva historial y ultimo resumen valido, publica estado
visible y permite recuperacion explicita. No liberar una reserva remota por el
mero vencimiento de un reloj si su ejecucion sigue siendo incierta. En ese caso
mostrar recuperacion pendiente y reconciliar/cancelar antes de aceptar conflicto.
No continuar silenciosamente perdiendo contexto ni reintentar sin limite.

## Comprobaciones requeridas

1. Contexto mayor de 8192 y lotes mayores de 4096, sin superar tokens ni bytes.
2. Pares completos, evidencia esencial y periodos del servidor conservados.
3. Dos envios simultaneos y dos pestanas no atraviesan la barrera; otra
   conversacion funciona. Repetir tras reinicio/recuperacion del servidor.
4. Borrador conservado; envio bloqueado hasta instalar resumen; error,
   cancelacion y trabajo remoto incierto no provocan perdida ni bloqueo opaco.
5. Historial original identico; nueva respuesta acredita usar el resumen nuevo.
6. Mutaciones focalizadas: retirar barrera del backend y retirar cada limite
   deben ser detectadas. No nuevas suites masivas de producto.
7. Ensayo real acotado con contenido sintetico; no llenar un millon de tokens
   solo para probar el techo. Extremos con transporte simulado y tokenizer real.

## Gate pendiente

La aprobacion funcional ya existe. El mecanismo concreto propuesto a continuacion
requiere autorizacion de la migracion aditiva antes de codigo o pruebas nuevas.
Este documento no autoriza ampliar limites de bytes, modificar el gateway
compartido ni publicar cambios.

## Concrecion de persistencia y concurrencia

### Aprobacion posterior al gate historico

El 11/10/2026 a las 13:05:16 Atlantic/Canary, el encargo directo del Tech Lead
transmite la aprobacion expresa de Paris en el chat Autonomo: migracion aditiva,
implementacion y pruebas exclusivamente aisladas; presupuesto por tokens y bytes,
mayor historial completo y exclusion de envio por conversacion durante compresion.
Autoriza progresion condicionada de pruebas Red a Green y mutacion, con checkpoints
y rutas separados. No autoriza servicios reales, publicacion ni operaciones Git.
El gate anterior se conserva como referencia historica y queda satisfecho para
este alcance local. No se atribuyen revisiones o validaciones a personas.

Propuesta: agregar una columna nullable `dialogue_compaction JSONB` en
`conversations` mediante una migracion nueva. No modificar 001/002/003 ni
reescribir `dialogue_history` o `dialogue_summary`. NULL significa que no existe
una compresion pendiente; no requiere backfill de mensajes ni resumenes.
El numero definitivo de la migracion se asignara tras comprobar colisiones.

Reutilizar `ChatRepository._transaction`: bloqueo de fila por identidad y
transaccion SERIALIZABLE. No mantener una transaccion SQL abierta durante una
llamada al modelo. El campo operacional queda separado del resumen derivado,
cuyo esquema cerrado actual y hashes no deben contaminarse con leases.

El documento operacional versionado conserva estado (pending, running,
reconciling, failed), revision de control, revision del historial, hash del
resumen padre, identificador de trabajo/intento, identificador del processor,
propietario temporal de ejecucion, vencimiento y causa saneada. No contiene
credenciales, prompts ni respuestas. La generacion de control impide que un
ejecutor antiguo instale o libere una compresion posterior.

Al completar un chat con memoria habilitada, guardar el estado pending en la
misma transaccion que el par de mensajes, antes del evento final. El planificador
comprueba si procede comprimir: si no procede, limpia pending bajo la misma
exclusion; si procede, adquiere el trabajo mediante compare-and-swap. Esta fase
de comprobacion tambien bloquea brevemente el envio y es visible al cliente.

La admision comprueba el campo antes de trabajo caro y de nuevo dentro de reserve.
La segunda comprobacion incluye revision de historial y hash del resumen usados
para ensamblar contexto: un contexto construido antes de una instalacion reciente
debe reconstruirse, no admitirse con memoria obsoleta. Las repeticiones idempotentes
de operaciones ya existentes no se convierten en nuevas generaciones.

Al instalar el resumen, actualizar su estado derivado y el control operacional
en una transaccion; limpiar el bloqueo solo al terminar los lotes necesarios para
el presupuesto acordado. Nunca liberar por haber recibido HTTP 200 sin validar.

En arranque, recuperar registros pendientes/inciertos. Un lease caducado permite
coordinar la recuperacion, pero no demuestra que el proveedor haya terminado:
consultar/cancelar el mismo job antes de permitir otra ejecucion incompatible.
Conservar las garantias de settlement existentes. Mientras no se pueda confirmar,
mostrar recuperacion pendiente; no prometer un desbloqueo seguro por timeout solo.

En un fallo confirmado, conservar historial y ultimo resumen valido, mostrar
error y ofrecer reintento explicito. El borrador permanece editable. No enviar
automaticamente omitiendo historial; una opcion de continuar sin compresion
requeriria que el contexto completo necesario cupiera y una decision explicita.

La API de estado de memoria expondra un estado saneado de bloqueo/recuperacion;
los intentos nuevos ocupados recibiran 409 conversation_compacting, sin crear
operacion ni gastar tokens. El frontend consulta el estado tras final/reconexion
y mantiene bloqueados boton y Enter. El control del servidor sigue siendo el
autoritativo, incluso cuando otra pestana muestra un estado antiguo.

## Ensayo de migracion propuesto

Instalacion limpia y actualizacion de la base desechable actual con registros;
comparar hashes de historial/resumen antes y despues. Probar pending atomico con
final, colision de dos generadores, contexto construido antes de instalar resumen,
dos recuperadores, reinicio en running y rechazo de un propietario antiguo.
No migrar bases del equipo ni borrar columnas como rollback automatico.

## Delta propuesto: salida de compresion independiente (11/10/2026)

### Estado y autoridad

Modo analysis-design. El encargo local transmite aprobacion de Paris para separar
la salida de compresion de la del chat. Este apartado propone el valor concreto
4096 y su aplicacion coherente; queda pendiente la evaluacion del padre antes de
codigo o pruebas nuevas. No aprueba aumentar payload, contenido, prefijo, tiempo,
capacidad, transporte o gasto desde este ejecutor. Las aprobaciones anteriores
se conservan literalmente y no convalidan este delta por anticipado.

Fuente observacional: informe externo al repositorio
`e5-context-compression-evidence/validation-local/report.md`. Dos intentos grandes
terminaron con 13153 tokens de prompt reportados, 800 de salida y finish_reason
length: correctamente no se instalaron. El intento menor termino con stop,
3622 tokens de prompt y 493 de salida, se instalo y fue consumido por chat.
Estos datos no prueban que 4096 baste ni explican por si solos la longitud.

### Cadena actual y propuesta concreta

El presupuesto efectivo esta en `core/context_budget.py` de backend y processor;
ambos publican/comparan el descriptor completo. Actualmente reserva 800 para las
dos operaciones. Hay ademas sumas literales de 800 en `SummaryResources.prepare_lot`
del backend, `SummaryResources.prepare_input` del processor y la comprobacion del
candidato SQL; `SummaryGateway._post` envia max_tokens=800 independientemente de
la configuracion general del chat. Cambiar solo esa llamada seria incoherente.

Propuesta minima, sin nueva variable de entorno ni dependencia:

1. Chat mantiene salida 800. Compresion usa salida 4096, fijada por tipo de
   operacion en ambos presupuestos efectivos. Mantener esquema del descriptor
   v1: su campo output_tokens ya representa esta diferencia. El matching estricto
   rechaza cualquier mezcla backend4096/processor800 antes de generar.
2. Planificador, autorizacion del processor, candidato de instalacion y gateway
   consumen ese mismo output_tokens efectivo, sin 800 literales para compresion.
   Mensajes completos, schema y margen 1024 mas reserva 4096 deben caber en
   SUMMARY_CONTEXT_TOKENS. La configuracion de compresion debe superar 5120;
   el minimo del chat no cambia. El maximo sigue siendo 1048576, no su disponibilidad
   garantizada por bytes. No cambiar llm_max_output_tokens general del chat.
3. Mantener seleccion del mayor prefijo contiguo de pares completos elegibles,
   resumen previo completo y cuatro pares recientes protegidos. Con contexto
   16384 quedan 12288 tokens para entrada medida incluyendo schema y margen;
   el lote observado de 14611 tokens locales ya no cabe entero. Seleccionar menos
   pares, no truncar textos ni referencias, y continuar por lotes conforme al
   control durable existente. Un primer par que no quepa conserva error visible.
4. Mantener transporte exacto 1 MiB compresion/2 MiB chat, limite de respuesta,
   plazo y capacidad actuales. Contar UTF-8 del envelope real, no caracteres ni
   solo payload. No ampliar frames/backpressure. La mayor salida podria agotar
   el plazo actual; debe ensayarse, no asumir permiso para aumentarlo.
5. Guardar en observations de cada nuevo artefacto el descriptor efectivo de
   ejecucion empleado (incluyendo reserva 4096), junto a conteos y uso observados.
   Es informacion de ejecucion, no parte nueva del contrato semantico cerrado.
   No escribir ni completar retrospectivamente observaciones de artefactos
   anteriores. No requiere migracion ni cambia CAS, leases o source hashes.
6. Una recuperacion consulta el mismo job incierto y no lo regenera para aplicar
   el presupuesto nuevo. Solo nuevas ejecuciones autorizadas utilizan 4096;
   un fallo remoto confirmado conserva el reintento explicito existente.

### Payload, prefijo y compatibilidad

Recomendacion para este delta: conservar payload canonico 768, contenido 512 y
prefijo de chat 768. Son limites del artefacto aceptado, distintos del maximo de
generacion del proveedor. El prompt permite omitir hechos con limitaciones, sin
falsear cobertura ni cortar citas. Por tanto un resultado compacto es posible;
no existe evidencia suficiente para afirmar que todos los lotes grandes puedan
producirlo. Las referencias opacas consumen una parte importante del payload.
Mas salida disponible no autoriza aceptar un JSON de mas de 768 tokens.

El prefijo real incluye UNTRUSTED_DIALOGUE_SUMMARY y escaping: payload<=768 no
implica prefijo<=768. La prueba de exito debe verificar consumo real del prefijo,
no solamente instalacion. Los rechazos actuales siguen vigentes, sin recortar
el artefacto para hacerlo pasar. Una correccion adicional de esta frontera, si
el ensayo la evidencia, debe volver con caso concreto y propuesta acotada.

Conservar intactos system.md, input.md, schema.json, manifest.json, sus pins y
summary_version. Los budgets del manifest v2 quedan identificados como perfil
historico inmutable del bundle (input4096/output800); NO son el presupuesto
efectivo de ejecucion, ya separado para entrada ampliada. El descriptor efectivo
es la autoridad para admision y max_tokens. Payload/content siguen siendo
restricciones semanticas del bundle. La observacion del descriptor evita atribuir
al artefacto nuevo una reserva historica que no se utilizo.

Esta separacion evita cambiar hashes y preserva resumenes previos, su lineage,
parent hashes, citas, cobertura y consumo, siempre bajo las mismas validaciones
de origen. No equiparar contratos distintos ni retirar comparaciones: hoy tanto
el repositorio del backend como valid_previous del processor comparan el contrato
exacto. Cambiar el manifest sin compatibilidad explicita haria perder reutilizacion
del resumen previo; no es una migracion aceptable por defecto.

Si se decide aumentar payload/content/prefix o modificar el prompt, hace falta
aprobar valores concretos y un nuevo bundle/pins/version. Ese segundo delta debe
retener el validador y bundle anteriores para lectura de artefactos existentes,
definir compatibilidad explicita por version en ambos servicios y conservar la
version real del artefacto al exponer memoria. No reetiquetar ni recalcular hashes
de resumenes guardados. No se propone implementarlo ahora sin esa decision.

### Archivos previstos y comprobaciones

Producto previsto exclusivamente para el delta minimo, sujeto a aprobacion:

- `apps/backend/app/core/context_budget.py`
- `apps/processor/app/core/context_budget.py`
- `apps/backend/app/core/summary_resources.py`
- `apps/processor/app/core/summary_resources.py`
- `apps/backend/app/db/chat_summary_repository.py`
- `apps/processor/app/clients/summary_gateway.py`

No se preven cambios de frontend, migracion, control durable, prompt, manifest,
gateway compartido o configuracion general del chat. Los tests focalizados se
ubicaran en las suites existentes de presupuestos, recursos, repositorio y
gateway de backend/processor. Rutas candidatas para el checkpoint Red:

- `apps/backend/tests/test_chat_summary_resources_jup035.py`
- `apps/backend/tests/test_chat_summary_lifecycle_jup035.py`
- `apps/backend/tests/test_chat_summary_context_jup035.py`
- `apps/processor/tests/test_chat_summary_resources_jup035.py`
- `apps/processor/tests/test_chat_summary_private_jup035.py`
- `apps/processor/tests/test_chat_summary_gateway_jup035.py`
- `apps/processor/tests/test_chat_context_budget_jup035.py`

No se editan tests ni producto durante esta fase de diseno.

Red posterior debe demostrar contra producto actual: salida/reserva 4096 en las
cuatro fronteras, chat800 inalterado, minimo de configuracion correcto, mismatch
de descriptor y seleccion de un lote menor cuando entrada+4096 supera el contexto.
Usar tokenizer real y transporte simulado, sin llamadas de pago del ejecutor.
Green debe incluir un resultado stop cuyo transporte usa mas de 800 tokens pero
cuyo JSON canonico cumple 768/512, y rechazar length incluso con JSON parseable,
payload excesivo, citas/referencias/negaciones alteradas y bytes excesivos.

Regresiones necesarias: resumen v2 anterior sigue siendo padre y memoria usable,
hashes del bundle permanecen identicos, nuevas observations registran 4096 sin
inventar consumo/coste, recuperacion incierta no duplica job, instalacion conserva
historial y consumo del prefijo completo. Mutaciones puntuales: devolver 800 al
gateway, retirar reserva del planner/processor/candidato, aceptar descriptor
discordante o truncado, e invalidar contrato previo por presupuesto de ejecucion.
No baterias completas nuevas sin una dependencia concreta.

Ensayo posterior del padre: repetir fixture grande a contexto16384 con lotes
recalculados, capturar max_tokens solicitado, stop, uso real y validacion/consumo
del resumen; comprobar bloqueo y conservacion del historial. No llamar exito a
HTTP200 ni a un mayor limite configurado. Si vuelve length, falla payload/prefijo
o vence el plazo, conservar evidencia y decidir el ajuste necesario antes de
ampliar el contrato. No existe prueba real de esta propuesta en esta fase.

## Delta aprobado: bundle v3 y limites ampliados (11/10/2026)

El encargo local transmite la aprobacion de Paris: "pues vamos con ello aumenta
los tamanos ... repite caso grande", seguida de "continua". Sustituye la propuesta
4096 anterior: generacion 10000, payload JSON canonico 8192 y contenido 6144 tokens.
Son maximos, nunca objetivos de longitud. Este ejecutor implementa y prueba sin
gasto; el padre prepara runtime y repite el ensayo real, con contexto 32768 en
ambas cadenas. Default de contexto 1048576, chat800, bytes 1MiB/2MiB, deadlines,
FinOpsResponse1.0 y controles factuales permanecen vigentes. Sin migracion,
dependencia, cambio del gateway compartido ni operaciones Git o externas.

Decisiones tecnicas dentro del alcance aprobado:

- Reserva efectiva summary10000 en ambos descriptores; exigir contexto >11024.
  Planner, processor, candidato y gateway consumen la misma reserva. Guardar el
  descriptor efectivo en observaciones de nuevos artefactos; rechazar mismatch.
- Bundle nuevo summary/v3 con pins propios de manifest/system/input y budgets;
  mantener SummaryResponse.v=2 y schema sin cambios. Bundle v2 queda inmutable.
- Resolver contratos anteriores por igualdad completa contra el bundle de origen
  cargado/verificado, nunca por prefijo de version ni fallback a limites nuevos.
  v3 acepta lectura v2; v2 no acepta v3. Conservar version expuesta, hashes,
  lineage y payload padre; no reescribir artefactos ni historial al leer.
- El prefijo de chat se mide completo, con etiqueta y escaping, dentro de las
  reservas y presupuesto real del chat junto a evidencia/pregunta/schema. No
  descartarlo por 768 ni cortarlo; si los esenciales no caben, limite explicito.
- Prompts piden concision, frases completas, citas literales y referencias
  conservadas. El embalaje debe incluir v2 y v3 sin reparar infraestructura ajena.

Secuencia autorizada: design/spec/traceability, Red focal, Green, mutacion focal
y regresion proporcional, con referencias SHA256 y guards frescos separados.
Probar lectura SQL v2, consumo de chat con version original, transicion a v3 con
lineage/hash padre intactos, rechazo v2 sobre limites origen, version desconocida,
payload/content excesivos, length, discrepancias, reservas y prefijo escapado.
No se atribuyen roles humanos no verificados ni aceptacion independiente.
