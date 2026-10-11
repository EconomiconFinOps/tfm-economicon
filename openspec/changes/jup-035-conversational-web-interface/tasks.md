# JUP-035 — tareas de investigación

## Estado actual verificado — 11/10/2026

Implementación en curso; E5 y la aceptación final siguen pendientes. Las aprobaciones humanas del diseño general (09/10/2026 23:23:27), JSONB (10/10/2026 09:15:41) y proyección del esquema de resumen (11/10/2026 02:17:13) autorizan los cambios locales correspondientes, que ya están implementados. La propuesta de diagnóstico de la respuesta principal, formalizada en design.md el 11/10/2026, está validada y pendiente de aprobación humana previa al código.

El alcance actual comprende frontend, backend y processor, historial JSONB/migración local003, recursos, pruebas y documentación aprobados. La aprobación no concede publicación, gestión Git, archivo o aceptación final. Los apartados de investigación siguientes y las frases «producto no autorizado», «sin implementación» o «únicamente OpenSpec» describen sus fases históricas del 09–10/10, sustituidas en ese alcance por las aprobaciones anteriores; no describen la implementación vigente. Los resultados históricos NOT_RUN, FAIL y SKIP conservan su significado.

La operación durable, esperas, streaming, cancelación/retry, persistencia JSONB, ámbito y compresión técnica tienen evidencia local de fases separadas. La proyección del proveedor omite dos uniqueItems y mantiene el esquema local v2 y el rechazo de duplicados: 112 pruebas processor y171 backend pasan, con cuatro mutaciones funcionales detectadas. El esquema local permanece 72404e66533f03268bf53727e7ed01cad00a71c31ad483f823ee4c3c8e06783e; la proyección es ec92ca50508a0fe0b94ef08ef81c3b1f330973d5b9266d22a53c9b1ca4b8e5ac. Referencia técnica RGM: fc641f15fac704766163bd815a5e7f04cf7c561d62776376b0f1e07139e98e9e.

El trigger real y su único retry autorizado terminaron failed/provider_error antes de completed; conservan los26 mensajes previos y no activaron el resumen. No hay todavía resumen real corregido instalado ni consumer validado. La pérdida del candidato/excepción deja la causa concreta sin identificar: el diagnóstico propuesto registra clasificación/campo/tipo/regla cerrados, sin contenido ni credenciales, y no debilita validación. Referencia del retry: 9667a394627f31feac5b2c16dd52f71840abfdfa6174c0c626f7ea431118c76b. La incidencia E4 de carga inicial de costes permanece abierta; su Retry manual no prueba reparación.

Controles finales actuales: backend1283PASS/52SKIP y processor694PASS/63SKIP, cinco controles de gobernanza/OpenSpec y build real de raíz4/4PASS. Las suites completas por componente no son una ejecución satisfactoria del wrapper test de raíz: su equivalencia con el inventario de tareas se está contrastando, conservando el fallo de preparación original. Referencia de entorno/equivalencia: 58ea7f0302c522dd3828cadf4ac341b3a1fe89c46bee23194699545c22216807. El fallo original del control administrativo de información completa y su limitación conservan la calificación operativa documentada; no sustituyen el guard independiente del PM.

Quedan diagnóstico y prueba real de memoria/consumer, revisión y validación independientes, aprobación final humana y archivo/publicación específicamente autorizados. No se marcan esas actuaciones como realizadas. Las tareas15/41/46/47 reflejan despacho y ejecución técnica completados;42/48/51 conservan trabajo o demostraciones pendientes, y16/49/50 conservan controles independientes y cierre pendientes. La coordinación histórica22/28/31 distingue el subgate pre-code ya satisfecho de los hechos externos no confirmados. El presupuesto vigente procede del PM, conserva costes desconocidos y reserva personal; los límites de llamadas son planificación operativa, no una autorización de gasto adicional.

## Antecedentes y decisiones conservados


**APROBACIÓN HUMANA DEL DELTA JSONB — Paris vía Project Manager 10/10/2026 09:15:41 (Atlantic/Canary): «si hazlo».** Aprobado `jsonb-history-design.md` entregado03:20:56: esquema por conversación, final conjunto pregunta/respuesta, alternativas sin duplicar pregunta, migración003/backfill conservador y tabla histórica sin rutas activas. Autoriza adaptación Red→Green→mutación y pruebas afectadas; ventana SIN escritores y migración únicamente LOCAL AISLADA. Sustituye el estado pendiente de ejecución de esta misma propuesta; no acredita implementación ni aceptación. Conservar IDs/citas/metadata/precisión, operaciones separadas y fuente JSONB única; retirada activa exigida a Revisor, Validador y cierre PM. Presupuesto compartido0,20EUR desde02:54:46 permanece, readiness/cota/reserva antes de gasto. No producción/remoto/Git/publicación/archivo/destrucción. Versión aprobada exacta y hashes conservados externamente por TL.


**CAMBIO VIGENTE DE HISTORIAL — Paris vía PM 10/10/2026 03:01:32, con control independiente añadido03:03:01 (Atlantic/Canary).** Historial canónico: un JSONB por conversación; pregunta y respuesta completa se añaden juntas al finalizar, sin cambios al enviar ni por deltas. [Contrato concreto y migración propuesta](jsonb-history-design.md). Sustituye el mecanismo de filas `messages`, su desempate temporal y la ausencia de backfill del diseño anterior; originales/decisiones históricas conservados. Preferencia JSONB aprobada; esquema003/backfill y reescritura material pendientes de validación/despacho, SIN implementación de este delta. Los demás contratos funcionales permanecen. Nueva autorización PM02:54:46 permite pruebas reales necesarias por ruta aprobada hasta0,20EUR acumulados compartidos, con coste acotado/contador antes de llamar; sustituye únicamente la prohibición de gasto anterior. No amplía Git/publicación/remoto/archivo.


**APROBACIÓN HUMANA PRE-CODE — Paris, vía Project Manager09/10/2026 23:23:27 (Atlantic/Canary): «pues aprobado».** Aprobado el diseño consolidado entregado23:17:59 y sus contratos/spec/tareas, incluidas esperas acumuladas, persistencia, seguridad, compresión LLM, concurrencia y UI. Autoriza desarrollo local y dependencias/migración definidas SOLO en entorno aislado de pruebas. Las menciones anteriores de propuestas/pre-code pendiente quedan como antecedentes fechados sustituidos por esta aprobación; no convierten hechos externos no confirmados en integrados ni resultados NOT_RUN en PASS. Sigue propuesta configurable/no medida la capacidad8, ahora autorizada para implementación/prueba en ese alcance. No autoriza nuevas inferencias con coste, publicación, gestión Git, archivo o merge; conservar guards y Red→Green→mutación separados. Versión exacta aprobada y SHA256 conservados fuera del repositorio por TL.


## Inicialización e investigación autorizadas

- [x] 1. Leer contrato/proceso, verificar contexto de rama, roles y límites del despacho.
- [x] 2. Inicializar propuesta, diseño pendiente y delta borrador con los siete puntos de Paris.
- [x] 3. Investigar localmente backend–processor, gateway/prompt/guardrails/retrieval y comparar transportes.
- [x] 4. Incorporar hechos PM de JUP-036/037 sin suponer integración y separar evidencia local/externa.
- [x] 5. Investigar persistencia/JSONB/tenant/usuario y controles de sesión/caché existentes; concretar arquitectura seleccionada assistant-ui + adapters/API/DB propia; Cloud descartado.
- [x] 6. Comparar assistant-ui y alternativas de UI Context Awareness; documentar spike proporcionado NOT_RUN.
- [x] 7. Preparar resumen para Paris, preguntas, matriz de validación futura y límites.
- [x] 8. Ejecutar validación nativa OpenSpec/trazabilidad/higiene y guard de retorno contra entrada conservada.
- [x] 9. Preparar entrega al TL con rutas, hashes, resultados y decisiones; STOP tras remisión.

- [x] 9.1. Integrar decisión humana PM15:24:08/TL15:24:35: assistant-ui + API/Cockroach propios; Cloud excluido.

- [x] 9.2. Registrar preview humano escritorio chat mitad derecha (~50%) con app visible y datos sintéticos, PM15:25:33/TL15:25:57.

- [x] 9.3. Planificar foco auto-scroll/scroll-to-bottom dentro punto1, PM15:27:52/TL15:28:23; fuentes de primitivas PM15:29:29 integradas; defaults/config por contrastar en spike.

## Corrección documental streaming — despacho PM15:47:28/TL15:48:23

- [x] 9.4. Registrar streaming real obligatorio por Paris, sin atribuirlo a Trello no verificado; preservar decisiones humanas anteriores.
- [x] 9.5. Comparar contratos streaming gateway→generador→backend→UI, SSE/fetch o NDJSON, cancelación/fallo parcial, guardrails/citas finales y rangos incluidos.
- [x] 9.6. Separar investigación backend/conexiones/historial de assistant-ui/auto-scroll, solo spike posterior; retirar simulación de respuesta completa como aceptación.
- [x] 9.7. Ejecutar checks documentales afectados y guard contra checkpoint fresco streaming-correction-entry, preservar recibos/referencias y preparar delta al TL; STOP tras remisión.

## Cuatro decisiones streaming — encargo PM16:16:04/TL16:16:57

- [x] 9.8. Comprobar solo alias/modelos/pin/config pública saneada; distinguir default/declarado/efectivo y soporte documentado vs combinación real pendiente.
- [x] 9.9. Proponer cancelación/interrumpidas/inicio-cierre/reload/reintento/idempotencia con aislamiento tenant Y usuario y pérdida parcial explícita ante crash.
- [x] 9.10. Limitar RabbitMQ a ingesta y retirar cola chat de alternativas vigentes, preservando comparación previa en registro histórico y entrada externa.
- [x] 9.11. Validar documentos afectados y guard streaming-decisions-entry; preparar propuesta/rutas/hashes al TL, conservar recibos anteriores y STOP tras remisión.

## Registro de aprobación funcional

- [x] 9.12. Registrar decisión de Paris vía PM09/10/26 16:48:09: Detener explícito best effort; ocultar no cancela; parcial incompleto fuera del contexto y reintento humano sin duplicar pregunta; inicio + terminal sin checkpoints, aceptando pérdida RAM ante caída completa y conservando pregunta/finales persistidos. No pre-code ni inferencias nuevas; compatibilidad real pendiente.

## Ensayo real y spike — autorización PM09/10/2026

- [x] 9.13. Ejecutar dos llamadas sintéticas reales, conservar negativa UNKNOWN y segunda PASS mínima; guardrails existentes, costes, configuración y controles originales preservados. Sin fiabilidad general inferida.
- [x] 9.14. Registrar RF-035-001 Open/fuera de alcance y consolidar evidencia del ensayo, sin repetirlo.
- [x] 9.15. Preparar diseño externo de spike assistant-ui real y dependencias concretas, guard original PASS; PM18:03:19 confirma instalación experimental cubierta por autorización Paris17:45:05.

- [x] 9.16. TL registra aprobación humana del spike y consolida propuesta pre-code con decisiones materiales pendientes; sin nuevo encargo Dev ni código de producto.

## Trabajo futuro condicionado — estado actualizado

- [x] 10. Confirmar compatibilidad experimental assistant-ui0.15.26/React18/Vite5 con tipos/build e interacciones observadas; integración productiva y disponibilidad oficial de costes siguen separadas.
- [x] 11. Paris aprueba adopción assistant-ui con API/DB propias PM19:23:15; versión compatible técnicamente, sin heredar override experimental. Transporte/framing y gate completo permanecen en14.
- [x] 12. Ejecutar spike externo assistant-ui/auto-scroll y ajuste de historial ocultable autorizado PM18:55:20; evidencia afectada PASS e integridad preservada. Sin backend/pago; no sustituye integración real ni aceptación.
- [x] 13. Paris ve demo45135 y aprueba spike/visual/interacción («me gusta aprobado»), PM09/10/2026 19:13:37. Sin aprobación de backend/dependencia productiva ni aceptación final.
- [x] 14. Aplicar decisiones vigentes PM21:33:08/21:46:22/21:54:52: LLMsummary, operación durable/pareja completa final, cuatro intentos y preparedscreen; conservar anteriores no sustituidas y concretar gate real alias+endpoint+pin stream/schema; preservar ensayo real mínimo ya ejecutado y concretar garantías no demostradas; consolidar diseño y delta definitivos; validarlos y obtener aprobación humana previa al código.
- [x] 15. TL despacha Red/Green/mutación separados y controles de integración/regresión del design.
- [ ] 16. Revisor/Validador independientes; aprobación final, archivo específicamente autorizado y revisiones humanas según proceso.


## Diseños concretos y ensayo de caché — 09/10/2026

- [x] 17. Desarrollador entrega history-persistence-design.md tras delegación Paris PM19:25:04; reserva atómica, índices/CAS, migración/runner y límites propuestos para revisión, sin ejecución.
- [x] 18. Registrar decisiones funcionales prompts/contexto aprobadas PM19:42:02 y diseño prompt-context-design.md, manteniendo processor generador, schema024 y seguridad interna explícita pendiente.
- [x] 19. Ensayo externo mínimo caché autorizado PM19:47:29: dos intentos consumidos≤0,01 EUR, INCONCLUSIVE (0/429sinusage), guard original PASS. No repetir.
- [x] 20. Diagnóstico documental TL del429 solicitado Paris PM19:59:56: fuentes OpenRouter, recibo sinbody/headers, causa/origen indeterminados; ninguna inferencia nueva.
- [x] 21. Consolidar documentos y escenarios con decisiones/diseños/evidencia fechadas; preservar originales y dictámenes Dev, guard TL documental y checks nativos. No pre-code ni aceptación inferida.
- [ ] 22. PM acuerda adaptación036 y capacidades037 según criterio/alcance condicional, sin gate037 automático, y detalles técnicos de cola/configuración restantes; admisión/esperas resueltas PM23:05:12 con dos presupuestos120s acumulados por solicitud; framing/protección/compatibilidad examinados durante diseño, implementación/pruebas aún futuras; Paris revisa materiales y otorga aprobación pre-code completa antes de14→15.

Matrices de tareas/pruebas futuras en ambos diseños; NOT_RUN excepto checks documentales y ensayos expresamente descritos. No se duplican como backlog operativo.


- [x] 23. Ampliación caché autorizada PM20:09:10: máximo10adicionales, techo0,01 EUR retirado soloensayo, parada tras1 hitpositivo3840/4053; contador3total y guard/recibos preservados. No extrapolar a todos los envíos.
- [x] 24. PM20:20:45 confirma cumplida la condición expresa de Paris de spikecache resuelto/conclusiones anotadas. Gate pre-code completo14 y dependencias22 siguen pendientes; no volver a pedir la comprobación de caché.


## Examen previo a aprobación del diseño — PM20:20:45

- [x] 25. Desarrollador inspecciona backend/processor/Compose y fuentes oficiales; entrega integration-readiness-plan.md con recomendaciones concretas, contrato036 publicado PM20:23:30 y límite037 no confirmado.
- [x] 26. TL revisa coherencia de entrega/finales grandes y duplicados; Desarrollador corrige bajo checkpoint fresco, preserva primera versión y originales. Plan definitivo y límites wire/GET verificados documentalmente, pruebas conductuales NOT_RUN.
- [x] 27. TL contrasta guard original y hashes, enlaza plan en diseño/resumen y registra condición cache cumplida; sin rehacer spikes, controles de producto o dictámenes Dev.
- [ ] 28. PM presenta recomendaciones/materiales a Paris; resolver detalles de migración/seguridad/topología y adaptación036/capacidades037 aplicables, sin gate universal por relación, antes de aprobación pre-code completa. Protocolo ya concretado en25, no ejecutar desde recetas propuestas.

## Ampliación QA, concurrencia y canal — decisiones PM21:07–21:17

- [x] 29. Desarrollador entrega compresor mínimo actual QA y corrige plan de integración: resumen local persistido, pantalla separada, scope completo y cinco chats concurrentes, límites aprobados y HTTP interno privado autenticado. Sin producto, migración, servicios o gasto.
- [x] 30. TL conserva originales, reconcilia documentos/delta spec, verifica controles documentales y entrega al PM para revisión de Paris.
- [ ] 31. Resolver detalles de columna/resumen y migración (elección operacional aprobada EN DISEÑO), capacidad/reparto/defaults/bind/secret y adaptación036/037 condicional; contador fijado aprobado PM21:54:52, prueba focal futura; validar diseño completo y obtener pre-code humano. Decisiones funcionales ya aprobadas no se reconsultan.

Pruebas focales futuras en delta QA y plan: cinco productores antes del primer final, negativos tenant/usuario en cada ruta, summaryCAS/offsets/omisiones/retry/fallo, snapshot por pestaña y red/listeners. NOT_RUN; cache/spike anteriores no sustituyen estas pruebas.

## Corrección humana vigente — PM21:33 / 21:46 / 21:54

Las tareas cerradas anteriores registran entregas históricas, no aprobación vigente de propuestas retiradas. Compresor local, placeholdermessages, cero retry funcional/global120 y construcciónscreenenSend se sustituyen.

- [x] 32. Desarrollador entrega cinco contratos reconciliados y matriz: llamadaLLM QA, operación durable/pareja final atómica, inicial+3 retries/120×4/480, pantalla ya preparada, prefijo de resumen y contador fijado aprobado. Inspección backend/processor/deps durante plan, sin nuevos ensayos.
- [x] 33. TL contrasta originales/guard/bytes y consolida seis padres/delta spec; checks documentales e informe al PM, sin aceptación ni código.
- [x] 34. PM revisa contenido completo y presenta decisión aprobada de dos esperas120s acumuladas y propuestas técnicas de cola/resumen acumulativo/margen120s/cobertura/reparto/detalleskeybudgetcapacidad y036/037 condicional por criterio para decisiones restantes y aprobación pre-code global. No reconsultar tres elecciones ni contador aprobados.

Planes Red/Green/mutación, mock/IA/Cockroach/UI/concurrencia/seguridad en integration-readiness-plan.md y matriz. Pruebas nuevas NOT_RUN; las recetas anteriores de seisDDL/noautoretries quedan retiradas.

## Revisión acotada PM22:14:44

- [x] 35. Desarrollador corrige cuatro documentos: presupuesto HTTP efectivo dentro de120s, recomendación de previo+QA nuevos por lotes/frontera y037 condicional según fuente oficial, sin nuevas pruebas/inferencias.
- [x] 36. TL preserva originales y reconcilia cinco padres afectados bajo guard documental, sin tocar spec/IDs/contador ni repetir checks/spikes no afectados; entrega compacta por punto al PM.

Detalles recomendados y políticas nuevas requieren revisión humana;120×4/LLM/contador anteriores aprobados no se reconsultan. Ninguna clave/budget nueva aprobada por arrastre.

- [x] 37. Registro histórico PM22:37:04 conservado; interpretación120s por intervalo sustituida por PM23:05:12 y tarea39, sin renovar presupuestos.
- [x] 38. PM presenta plan consolidado y obtiene aprobación humana pre-code completa de sus propuestas concretas antes de implementar; ninguna inferencia, gasto o migración ejecutada por esta entrega documental.

- [x] 39. Registrar PM23:05:12:120s local+120s proveedor acumulados por solicitud, waiting local sin consumir intento, paused visible al agotar saldo local/sin bucle automático y resume explícito sin reset, nunca antes de retry_at; consolidación documental focal.

## Implementación autorizada — PM23:23:27

- [x] 40. TL registra aprobación humana pre-code y conserva copia exacta/hashes de versión aprobada, checkout/plaza vigentes y contrato separado de fases.
- [x] 41. Desarrollador ejecuta primer bloque de operación durable/esperas/claim/final atómico con Red significativo, Green y mutación separadas; smoke Compose mock temprano en entorno aislado.
- [ ] 42. Completar el resto del diseño aprobado y controles aplicables, entregar al TL; revisión/validación independientes requieren guard PM previo a cada una.

No se reinicia la aprobación del mismo diseño. Acuerdos/fuentes036 y capacidades037 siguen sujetos a hechos reales y criterio, sin inventar integración; prueba real con coste queda pendiente de autorización específica y no bloquea trabajo mock independiente. Tareas históricas22/28/31 conservan detalles de coordinación/ejecución aún por demostrar; su subgate pre-code queda satisfecho aquí.

## Delta material JSONB — PM10/10/2026 03:01:32 y03:03:01

- [x] 43. Cerrar checkpoint seguro del bloque18 y contraste independiente; conservar producto/evidencia sin despliegue del arreglo por filas.
- [x] 44. Concretar diseño externo y documental del JSONB único/versionado/ordinals, retry y legado legítimo; incorporar requisito de retirada activa a spec/tareas y contratos independientes previstos.
- [x] 45. Validar/aprobar esquema003, backfill reanudable y ventana sin escritores SOLO aislada, y despachar contrato material revisado antes de producto/migración; preferencia JSONB ya aprobada, no reiterarla.
- [x] 46. Implementar documento/migración003/verificación y conservación lossless con Red/Green/mutación separados; no modificar001/002 ni borrar históricos, fallar cerrado ante datos/documentos inconsistentes.
- [x] 47. Adaptar escritores/lectores/resultados/retry/recuperación/contexto/compresión a fuente única; retirar SQLmessages y helper de empate18 de rutas activas, conservar APIs y pruebas funcionales ajustadas.
- [ ] 48. Probar envío/deltas sin modificación, final atómico una vez, rollback/Stop/deadlines/idempotencia/commit ambiguo, alternativas, scope y cinco productores; compresión desde originales/linaje/CAS; migración/restart sin pérdida ni escrituras paralelas.
- [ ] 49. Revisor independiente bajo guard PM: informe específico de rastros activos retirados y restos necesarios identificados, sin escritura de repositorio/Git.
- [ ] 50. Validador independiente bajo guard PM: flujos documentados y DB acreditan cada criterio JSONB/retirada/transición legacy con caso de error; informe específico, sin escritura de repositorio/Git.
- [ ] 51. TL consolida evidencia y coherencia; reutiliza sólo resultados vigentes/no afectados, identifica límite de crecimiento a medir sin agregar paginación/retención unilateralmente y eleva únicamente conflicto concreto036.

Este delta no está implementado ni aceptado; pruebas/recibos del mecanismo previo son históricos y no prueban JSONB. Pruebas reales necesarias comparten máximo0,20EUR desde PM02:54:46, sin llamadas hasta readiness/cota/reserva común.

## Ejecución JSONB autorizada — PM09:15:41

## Contexto ampliado y compresion coordinada - 11/10/2026

Fuente: context-compression-design.md y encargo TL con aprobacion expresa de
Paris de migracion e implementacion aisladas. Reinicio de fase autorizado con
referencia persistente nueva; incidente anterior conservado sin convalidarlo.

- [ ] 52. Red: barrera durable por identidad, final-pending atomico, fences de
  contexto, propietario obsoleto, recuperacion e idempotencia; tokens y bytes
  completos, mayor sufijo y estado de envio recuperable.
- [ ] 53. Green: migracion aditiva, control CAS, presupuestos configurables
  contrastados con descriptor y frontend con borrador editable y envio bloqueado.
- [ ] 54. Mutacion focal: retirar barrera y limites; comprobar deteccion y
  restauracion del producto propio mediante hashes.
- [ ] 55. Entregar evidencia de implementacion al TL y ceder antes de revision y
  validacion independientes; migracion y UI reales aisladas tienen evidencia aparte.

La aprobación concreta del delta queda satisfecha; TL encarga al único Desarrollador fases separadas tras contraste del checkpoint seguro. Tareas46–51 y comportamiento siguen pendientes de ejecución/evidencia/independientes; no otra confirmación del mismo esquema/backfill local aislado. El resto035 aprobado continúa sin repetir pruebas no afectadas.

## Nombres de conversaciones - delta autonomo autorizado 11/10/2026

Fuente: conversation-titles-design.md y autorizacion explicita del usuario para
PATCH sobre title existente, sin migracion ni llamadas adicionales al modelo.

- [x] 56. Disenar nombre inicial Unicode60 y edicion manual scoped sin cambiar titulos existentes.
- [x] 57. Red focal: contrato PATCH, aislamiento/validacion y nombre/editor frontend.
- [x] 58. Green: PATCH parametrizado y editor compartido de cabecera/historial; seleccion y nombres protegidos frente a callbacks tardios.
- [x] 59. Comprobar pruebas afectadas, typecheck/build y mutaciones focales en copias offline.
- [ ] 60. Comprobacion del padre en runtime aislado reconstruido y decision humana, sin inferir aceptacion de los resultados locales.

## Eliminacion individual - delta autonomo autorizado 11/10/2026

Fuente: conversation-deletion-design.md y aprobacion humana expresa de hard delete
sin migracion, modal exacto y comprobaciones offline con fixtures desechables.

- [x] 61. Inspeccionar relaciones, aprobar bloqueo/propiedad y confirmacion explicita.
- [x] 62. Red focal: DELETE, preflight, propiedad, bloqueos, rollback y modal/seleccion/callbacks.
- [x] 63. Green: transaccion scoped y modal Radix; conservar otras conversaciones y cambios previos de nombres/citas/scroll.
- [x] 64. Regresiones afectadas, ambos typechecks/build y mutaciones focales de compresion y resurreccion de celda.
- [ ] 65. Padre despliega backend/frontend y comprueba navegador/Cockroach aislados antes de decision humana; no borrar fixtures reales desde este ejecutor.
