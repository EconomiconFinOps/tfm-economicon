## Corte vigente para archivo — 11/10/2026

Paris autoriza archivar y preparar la PR. Véase [entrega y límites](archive-delivery.md): E5, resumen real y consumo posterior, Compose y reconciliación tienen evidencias posteriores. Los estados y casillas anteriores son históricos; no se borran fallos ni se atribuyen al nuevo árbol ensayos antiguos.

JUP: JUP-035

## Estado actual verificado — 11/10/2026

Implementación en curso; E5 y la aceptación final siguen pendientes. Las aprobaciones humanas del diseño general (09/10/2026 23:23:27), JSONB (10/10/2026 09:15:41) y proyección del esquema de resumen (11/10/2026 02:17:13) autorizan los cambios locales correspondientes, que ya están implementados. La propuesta de diagnóstico de la respuesta principal, formalizada en design.md el 11/10/2026, está validada y pendiente de aprobación humana previa al código.

El alcance actual comprende frontend, backend y processor, historial JSONB/migración local003, recursos, pruebas y documentación aprobados. La aprobación no concede publicación, gestión Git, archivo o aceptación final. Los apartados de investigación siguientes y las frases «producto no autorizado», «sin implementación» o «únicamente OpenSpec» describen sus fases históricas del 09–10/10, sustituidas en ese alcance por las aprobaciones anteriores; no describen la implementación vigente. Los resultados históricos NOT_RUN, FAIL y SKIP conservan su significado.

La operación durable, esperas, streaming, cancelación/retry, persistencia JSONB, ámbito y compresión técnica tienen evidencia local de fases separadas. La proyección del proveedor omite dos uniqueItems y mantiene el esquema local v2 y el rechazo de duplicados: 112 pruebas processor y171 backend pasan, con cuatro mutaciones funcionales detectadas. El esquema local permanece 72404e66533f03268bf53727e7ed01cad00a71c31ad483f823ee4c3c8e06783e; la proyección es ec92ca50508a0fe0b94ef08ef81c3b1f330973d5b9266d22a53c9b1ca4b8e5ac. Referencia técnica RGM: fc641f15fac704766163bd815a5e7f04cf7c561d62776376b0f1e07139e98e9e.

El trigger real y su único retry autorizado terminaron failed/provider_error antes de completed; conservan los26 mensajes previos y no activaron el resumen. No hay todavía resumen real corregido instalado ni consumer validado. La pérdida del candidato/excepción deja la causa concreta sin identificar: el diagnóstico propuesto registra clasificación/campo/tipo/regla cerrados, sin contenido ni credenciales, y no debilita validación. Referencia del retry: 9667a394627f31feac5b2c16dd52f71840abfdfa6174c0c626f7ea431118c76b. La incidencia E4 de carga inicial de costes permanece abierta; su Retry manual no prueba reparación.

Controles finales actuales: backend1283PASS/52SKIP y processor694PASS/63SKIP, cinco controles de gobernanza/OpenSpec y build real de raíz4/4PASS. Las suites completas por componente no son una ejecución satisfactoria del wrapper test de raíz: su equivalencia con el inventario de tareas se está contrastando, conservando el fallo de preparación original. Referencia de entorno/equivalencia: 58ea7f0302c522dd3828cadf4ac341b3a1fe89c46bee23194699545c22216807. El fallo original del control administrativo de información completa y su limitación conservan la calificación operativa documentada; no sustituyen el guard independiente del PM.

Quedan diagnóstico y prueba real de memoria/consumer, revisión y validación independientes, aprobación final humana y archivo/publicación específicamente autorizados. No se marcan esas actuaciones como realizadas. Las tareas15/41/46/47 reflejan despacho y ejecución técnica completados;42/48/51 conservan trabajo o demostraciones pendientes, y16/49/50 conservan controles independientes y cierre pendientes. La coordinación histórica22/28/31 distingue el subgate pre-code ya satisfecho de los hechos externos no confirmados. El presupuesto vigente procede del PM, conserva costes desconocidos y reserva personal; los límites de llamadas son planificación operativa, no una autorización de gasto adicional.

## Antecedentes y decisiones conservados

Trello: https://trello.com/c/BJfABykd

# Interfaz web conversacional — diseño para revisión

**APROBACIÓN HUMANA DEL DELTA JSONB — Paris vía Project Manager 10/10/2026 09:15:41 (Atlantic/Canary): «si hazlo».** Aprobado `jsonb-history-design.md` entregado03:20:56: esquema por conversación, final conjunto pregunta/respuesta, alternativas sin duplicar pregunta, migración003/backfill conservador y tabla histórica sin rutas activas. Autoriza adaptación Red→Green→mutación y pruebas afectadas; ventana SIN escritores y migración únicamente LOCAL AISLADA. Sustituye el estado pendiente de ejecución de esta misma propuesta; no acredita implementación ni aceptación. Conservar IDs/citas/metadata/precisión, operaciones separadas y fuente JSONB única; retirada activa exigida a Revisor, Validador y cierre PM. Presupuesto compartido0,20EUR desde02:54:46 permanece, readiness/cota/reserva antes de gasto. No producción/remoto/Git/publicación/archivo/destrucción. Versión aprobada exacta y hashes conservados externamente por TL.


**CAMBIO VIGENTE DE HISTORIAL — Paris vía PM 10/10/2026 03:01:32, con control independiente añadido03:03:01 (Atlantic/Canary).** Historial canónico: un JSONB por conversación; pregunta y respuesta completa se añaden juntas al finalizar, sin cambios al enviar ni por deltas. [Contrato concreto y migración propuesta](jsonb-history-design.md). Sustituye el mecanismo de filas `messages`, su desempate temporal y la ausencia de backfill del diseño anterior; originales/decisiones históricas conservados. Preferencia JSONB aprobada; esquema003/backfill y reescritura material pendientes de validación/despacho, SIN implementación de este delta. Los demás contratos funcionales permanecen. Nueva autorización PM02:54:46 permite pruebas reales necesarias por ruta aprobada hasta0,20EUR acumulados compartidos, con coste acotado/contador antes de llamar; sustituye únicamente la prohibición de gasto anterior. No amplía Git/publicación/remoto/archivo.


**APROBACIÓN HUMANA PRE-CODE — Paris, vía Project Manager09/10/2026 23:23:27 (Atlantic/Canary): «pues aprobado».** Aprobado el diseño consolidado entregado23:17:59 y sus contratos/spec/tareas, incluidas esperas acumuladas, persistencia, seguridad, compresión LLM, concurrencia y UI. Autoriza desarrollo local y dependencias/migración definidas SOLO en entorno aislado de pruebas. Las menciones anteriores de propuestas/pre-code pendiente quedan como antecedentes fechados sustituidos por esta aprobación; no convierten hechos externos no confirmados en integrados ni resultados NOT_RUN en PASS. Sigue propuesta configurable/no medida la capacidad8, ahora autorizada para implementación/prueba en ese alcance. No autoriza nuevas inferencias con coste, publicación, gestión Git, archivo o merge; conservar guards y Red→Green→mutación separados. Versión exacta aprobada y SHA256 conservados fuera del repositorio por TL.


Estado de la fase histórica de investigación (09/10/2026): DESIGNS_DELIVERED_DECISION_REQUIRED_PRECODE_PENDING. Consolidación documental; producto no autorizado.
Fuente oficial: paquete PM transmitido por TL el 09/10/2026, ampliación humana
15:13:43 Atlantic/Canary. Proceso CONTRIBUTING 2026-09-30 / JUP-100.
Humanos: Paris líder; Víctor pairing; Alejandro revisión; Lucía validación.

## Why

La pantalla existente conserva conversaciones y recuperación documental, pero
su respuesta backend es una plantilla. JUP-035 necesita una interfaz natural
conectada a la vertical real 020–026 y datos 084/036/037, con evidencias,
estados comprensibles y aislamiento de tenant y usuario.

La investigación y evidencias anteriores se conservan. Spike visual/interacción aprobados por Paris vía PM09/10/2026 19:13:37 («me gusta aprobado»); integración y pre-code producto pendientes. [Propuesta técnica vigente](design.md).
No constituye diseño final, aprobación previa al código ni aceptación funcional.

## What Changes

Corrección humana de Paris del 09/10/2026, vía PM15:47:28 y TL15:48:23 Atlantic/Canary: «el streaming es obligatorio de hecho creo que está en los requisitos de la jup». Streaming real es obligatorio por esta instrucción; no se atribuye a Trello una mención que PM no ha verificado. No autoriza producto, ejecución, inferencias ni spike.

Decisión humana de Paris del 09/10/2026, transmitida por PM15:24:08 y TL15:24:35 Atlantic/Canary: «esta es la opcion: assistant-ui + nuestra API y base de datos, no nos vamos a casar con el cloud de otra empresa en un tfm». Arquitectura seleccionada: assistant-ui + API y Cockroach propios. No es aprobación del diseño técnico final, versión/dependencia, instalación, spike ejecutable o producto.

Encargo Paris PM09/10/26 16:16:04/TL16:16:57: conexión streaming directa
preferida; RabbitMQ solo ingesta. Cuatro decisiones técnicas propuestas de
cancelación/interrumpidas/persistencia/alias, pendientes de diseño final.

Documentación de investigación, preguntas, alternativas de integración, plan de spike y
escenarios futuros. Los siete puntos de Paris permanecen independientes:

1. Panel derecho en el estilo existente, botón/icono abierto–cerrado y historial ocultable superpuesto derecho, con selección que cierra barra manteniendo chat abierto y Nueva conversación; preview escritorio mitad derecha (~50%) con app visible en la otra mitad, confirmado PM15:25:33; referencia Codex pendiente para atajo/animación/móvil; foco auto-scroll y botón volver al final, sin arrastrar a quien está leyendo arriba (PM15:27:52).
2. Investigar assistant-ui sobre API/DB propias y preparar spike breve para concretar compatibilidad y adaptadores.
3. Conectar gateway→generador processor→backend→UI con streaming real obligatorio, auth/tenant/usuario, cancelación/fallo parcial, prompt/guardrails y retrieval.
4. Comprobar aportación de JUP-036 y JUP-037 P1; estado oficial por PM.
5. Reparar o sustituir historial solo según evidencia, tenant Y usuario y persistencia.
6. Definir JSON de pantalla preparado al recibir/cambiar datos y compresor mínimo QA mediante LLM, con resumen estable candidato a prefijo; pantalla fuera del compresor y memoria avanzada041 separada (PM21:33:08).
7. Demo sintética y aprobación de Paris antes de conectarla al backend.

## Capabilities

### New Capabilities

- `conversational-web-interface`: delta borrador de la conducta futura de
  JUP-035, sujeto a decisiones y aprobación; no se modifica ningún spec canónico.

### Modified Capabilities

Ninguna modificación canónica en esta fase. Se estudian compatibilidad con
frontend-navigation-shell, answer-citations, semantic-retrieval,
finops-response-guardrails y finops-agent-tool-contract.

## Impact de la investigación histórica — 09/10/2026

Únicamente `openspec/changes/jup-035-conversational-web-interface/**`.
Producto, pruebas, dependencias, configuración, Git y servicios quedan fuera del
despacho. Spike/demo ejecutados y aprobados en su alcance visual/interacción; ensayo gateway mínimo ejecutado. Integración, dependencia productiva y aceptación final PENDING; arquitectura humana seleccionada. No código de producto autorizado.

Alcance futuro: lenguaje natural y streaming real obligatorio, modelo real mediante 023, prompt/guardrails
024, contexto 022, citas 025, costes 084/036/037; estados vacío/cargando/error/
datos insuficientes/proveedor; accesibilidad y responsive; regresión real de
historial JSONB, tenant ajeno 404, aislamiento de usuario y batería 069.

Fuera del alcance: ahorros 033/034, anomalías 030/038, memoria avanzada
041 (el mínimo QA entra como propuesta035 por PM21:07:33), formatos 040, medición formal 070 y elección de proveedor 078. Los contratos
generales de herramientas no amplían este alcance.

RF-083-002 figura Open en backlog local: integración visual con auth/datos.
RF-087-002 figura Fixed: conservar corrección y planificar regresión automatizada;
no se declara fallo actual. Véase [investigación](research.md) y
[resumen para Paris](summary-for-paris.md).


## Estado vigente del diseño — corrección PM21:33 / aprobación21:46 / contador21:54

Elegidos en diseño: compresor por llamada LLM exclusivamente QA; registro operacional durable y pregunta recuperable separados del historial; pareja completa atómica al final; inicial más tres retries máximo cuatro,120s cada uno y480s activos; JSON preparado al recibir/cambiar datos, Send solo copia/congela sin construir/refetch; resumen estable después de system como datos no confiables y antes de variables. Tokenizers0.22.1 y artefacto ZAI de revisión/hash fijados aprobados en diseño/futura implementación aprobada; sin instalación o ejecución ahora.

Mantener assistant-ui/API/DB propios, streaming real, tenant+usuario+conversación en todo, cinco chats privados concurrentes, límites aprobados1MiB/8192 y HTTP interno privado autenticado en un DockerServer/HTTPS externo. Framing, protección, dependencias y recetas fueron examinados durante elaboración del plan; pruebas de implementación siguen futuras. El hit3840/4053 del tercer intento cache satisface la condición confirmada PM20:20:45; no repetir ensayo.

[Matriz de decisiones](design-decision-matrix.md), [historial](history-persistence-design.md), [prompts/contexto](prompt-context-design.md), [resumen LLM](context-compression-extension.md) y [plan de integración](integration-readiness-plan.md). Propuestas retiradas: localextractivo, placeholder inicial messages, noautoretries/global120 y construcciónscreenenSend. Originales y hechos históricos preservados; sus autorizaciones conservan solo alcance fechado no sustituido.

Paris vía PM09/10/2026 23:05:12 aprueba dos presupuestos independientes ACUMULADOS POR SOLICITUD:120 s de espera automática por capacidad local y120 s de espera automática del proveedor. No se reinician por retry, resume ni recuperación de la misma operación. Máximo240 s de esperas automáticas, no plazo total hasta respuesta. Se mantienen120 s de ejecución por intento e inicial+3/max4, sin retries anidados. Sin plaza local se conserva operación waiting sin consumir intento; arranque automático con plaza dentro del saldo. Agotamiento local→paused visible, pregunta conservada/sin bucle automático; resume explícito con saldo agotado requiere plaza inmediata. Retry-After superior al saldo restante→paused visible/resume≥retry_at sin renovar presupuestos. Sustituye interpretación por intervalo22:37:04. Restante: detalle técnico cola/admisión, margen HTTP dentro de120s, resumen acumulativo/lotes/cobertura/reparto/schema, capacidad8 configurable propuesta y detalles keys/budgets/bind/secret/recursos; adaptación036/037 condicional por criterio. Aprobación pre-code completa pendiente; no implementación, migración, nuevas inferencias/spikes/gasto/config/Git/publicación.

Revisión oficial PM22:14:44: relaciones036037070 y «lo que integren036037». Diseñar con contrato036 referencia sin esperar merge;037 disponible/pertinente se integra por contrato y criterio confirmado, ausencia de paquete no bloquea automáticamente todo035. Timeout efectivo se alinea con restante del claim120s sin total30/idle20 ocultos; compresión recomendada conserva resumenanterior+QA nuevos con frontera y riesgo/pérdidas explícitos. No nueva elección humana de descartar memoria ni coste único para rebuild multillamada.
