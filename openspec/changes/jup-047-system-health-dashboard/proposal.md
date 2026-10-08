JUP: JUP-047
Trello: https://trello.com/c/iMXH0o3a

**Decisión vigente de retención y ciclo visible — 08/10/2026**

Paris autorizó «ok dile al TL que haga los cambios», según PM 08/10/26 10:09:29 transmitido por TL 10:11:38. Esta decisión sustituye la caducidad automática de 60 s y el ciclo exclusivamente manual/apertura descritos en fases anteriores: el resultado real se retiene hasta otra observación, y OpenRouter se comprueba al abrir y cada 10 minutos solo con el panel abierto y visible. Un timeout nuevo produce unknown con historia conservada. Azure sigue siendo explícitamente SIMULADO; LiteLLM conserva liveliness real no generativa. Las fechas válidas hasta 1000 ms futuras inclusive reciben tolerancia de presentación, sin modificar su valor.

Esta fase es solo análisis/diseño en seis OpenSpec, sobre HEAD 6fa3ef75674734bcc5198c1f8fb760d43ee2d0a6 y base LOCAL origin/develop 2f9a5f530c9fe3b60007ba5060c189133e353bf6; frescura remota no acreditada. Los registros E12/E13 y las aprobaciones históricas inferiores conservan literalmente hechos/decisiones de su revisión. No validan el comportamiento nuevo. Las menciones históricas a TTL60 o ausencia de periodicidad pagada quedan supersedidas por el contrato nuevo; el cooldown financiero de 60 s permanece.

La autorización funcional no activa gasto: ledger6 intacto, certificado6/6 agotado/caducado y techo0,20 EUR acumulado. Sin nuevos envíos, credenciales, configuración, servicios, commits, archivo o publicación en este diseño. Autenticación, tenant, modelo/coste informativos, ruta, reservas H/U/P, contadores, M5 externo y móvil diferido permanecen. Las fases Red/Green/mutación requieren despachos separados tras coherencia TL.

## Cambio aprobado — retención y comprobación visible

El estado inicial es unknown/no verificado hasta recibir datos. Una observación real no se convierte en stale por antigüedad: conserva resultado y fecha. El intento posterior reemplaza el resultado actual; si termina en timeout, muestra unknown y conserva por separado la última respuesta funcional válida. El tiempo de un GET no certifica otra inferencia.

El panel inicia una comprobación al abrir una entrada de navegación autenticada y visible, y otra al cumplirse600000 ms desde el último intento despachado mientras esa entrada siga abierta/visible. Pestaña oculta pausa los temporizadores; reentrada/remount del mismo episodio no equivale a nueva apertura. Actualizar manualmente comparte exclusión/deduplicación y reinicia el plazo. El GET periódico sigue siendo no generativo. El diseño de lifecycle, rechazo y coexistencia se fija en design.md.

El simulador Azure conserva su salud propia con procedencia SIMULADO y no certifica Azure real. Las diferencias temporales pequeñas no invalidan una sonda LiteLLM saludable. Se admite una fecha UTC real hasta 1000 ms posterior al reloj de recepción/render fijado para esa observación; se rechazan formatos inválidos y futuros superiores. No se altera el dato para ocultar un desfase.

Impacto: servicio backend de observación e idempotencia, hook/página/contratos frontend, pruebas focales y README/runbook en fases posteriores. Sin nueva dependencia, ADR, monitor, infraestructura ni estado financiero. expires_at queda presente y nullable por compatibilidad, se emite null y no determina caducidad del nuevo cliente. Los datos ya existentes no se fabrican ni se migran.

Aceptación del diseño: tabla de escenarios y cinco criterios oficiales en acceptance-map.md, rutas exhaustivas por fase y pruebas/mutantes en design.md. E13 acredita la revisión anterior, no este cambio. Pendientes: Red significativo, Green, mutación, revisión/validación afectadas, control PM y decisión final; M5, CI y gates humanos conservados.

**Estado final local — 08/10/2026; evidencia E13**

Resultado vigente comunicado por PM09:40:27/TL09:43:52 Atlantic/Canary: revisión técnica interna afectada favorable y validación funcional local acreditada. Hay **6 intentos reales acumulados**, sin reset: la sexta petición, iniciada manualmente desde «Salud del sistema», recibió HTTP200, JSON válido, una elección, finish_reason=stop y contenido exacto OK. La quinta conserva HTTP429 como caso de error; los cuatro anteriores no se convierten retrospectivamente en éxitos. GET/polling no genera inferencias.

La observación válida caduca contractualmente a los **60 segundos**: después se presenta unknown/stale conservando verified_at y check_id. Este comportamiento y el criterio funcional permanecen intactos. Modelo y coste siguen siendo informativos, con identidad y facturación upstream no confirmadas. Se conserva la reserva incierta histórica; la cohorte operativa terminó **6/6, sin envíos restantes**, y no se autoriza una séptima petición.

E13 acredita revisión interna con214 pruebas propias y validación afectada con214 PASS en cuatro ejecuciones completas (102+33+29+50); la ejecución conjunta sin resultado no cuenta como PASS. E12 conserva Red143 PASS/38 fallos significativos, Green214 PASS y15 mutantes detectados, con controles37/37. No se repiten suites de producto en esta consolidación documental.

Siguen pendientes DockerServer M5 con Alejandro, CI remota, aprobación humana final, archivo específicamente autorizado en la misma rama, PR vinculada y las dos reviews humanas. La asignación Paris/Víctor/Alejandro/Lucía no acredita participación efectiva. Los bloques siguientes, incluso cuando dicen «vigente» o «pendiente», son historia fechada de sus fases; E13 actualiza sus hechos de ejecución, no sus decisiones ni requisitos/escenarios. El techo humano sigue siendo **0,20 EUR acumulados incluyendo intentos anteriores**; no equivale a0,20 USD.

**Estado vigente tras implementación — 08/10/2026**

Fuente: PM03:31:30 transmitido por TL03:32:20 Atlantic/Canary: Paris autoriza las pruebas necesarias para completar JUP-047 hasta **0,20 EUR acumulados, incluyendo los intentos previos**. Sustituye el anterior presupuesto humano de 0,40 USD y el cupo humano de 13 llamadas. El contador verdadero sigue en **4 intentos reales**, sin reset ni éxito retrospectivo. La equivalencia conservadora fechada en USD corresponde al PM y no se calcula ni incorpora aquí. TL coordina cohortes operativas finitas dentro del techo; no se presenta un resto fijo de nueve ni un veto a la tercera llamada como autorización vigente. El contador y límite operativo de cada cohorte siguen siendo finitos y fieles, con admisión ordinaria, cooldown, frecuencia, cero retries/fallbacks y reservas intactos.

La autonomía local transmitida por PM03:34:40/TL03:35:12 permite pasos locales ordinarios dentro del alcance y proceso; no es aprobación funcional ni permiso de publicación, nuevos accesos remotos o cambios materiales. El cap diagnóstico de **0,03 USD** previamente aprobado permanece **sin aplicar** en esta consolidación; H=0.000031275 USD, U=0.008064 USD y P=0 se conservan. La captura cuarta no aporta un texto literal conocido ni respuesta funcional válida.

Los apartados y bloques anteriores conservados más abajo, incluso si usan «vigente», 4/13, dos envíos o 0,40 USD, son antecedentes fechados de su fase. Sus importes/cupos quedan sustituidos por esta nota; las aprobaciones históricas no se reescriben. No se modifica el criterio funcional, arquitectura, producto, pruebas, routing, privacidad o política de admisión.

La corrección offline está implementada: **Red 143 PASS / 38 fallos significativos; Green afectado 214 PASS; mutación nueva 15/15 KILLED; control original y restaurado 37 PASS cada uno**. No errores ni SKIP en el Green o controles. Guard conjunto de mutación con cero cambios y 852 fuentes/4 tests fijos; referencias originales intactas. Primer Green parcial con timeout y primer guard rechazado por interfaz se conservan como no satisfactorios; su corrección está descrita en E12. Cero nuevas llamadas, gasto, servicios o cambios de cap. Revisión y validación independientes afectadas siguen pendientes; E10 no las anticipa.

E12: `jup047-prompt-liveliness-implementation-20261008/delivery-handoff.json`, SHA256 `fb1a45b669d7ea9eda87baeac6f6157e78a464befe110d2d6a6f22721b2b12de`; índice de 151 artefactos `artifact-sha256.json`, SHA256 `b0c4491afde9637f92128b57c276cd6612d19d77f7be3d9cd2c74d819bb0e776`. Referencias externas entregadas al TL; no se copian recibos privados al producto. Rama `feat/JUP-047-system-health-dashboard`, HEAD `f0cacddb037dcb38878dd02de8adf5aff479d1b6`, cambios sin commit; Python 3.12 aislado Windows, transportes/procesos simulados y fixtures de denegación de red conservadas. No prueba remota ni aceptación por el Desarrollador. M5/Alejandro, CI remoto, aprobación final, archivo específico y reviews humanas permanecen pendientes.

## Estado vigente y corrección acotada — 08/10/2026

Fuente: TL03:13:52 Atlantic/Canary transmite PM03:13:09 y el mandato humano «arréglalo»: aclarar el prompt fijo conservando el criterio funcional y adaptar específicamente la respuesta no generativa de LiteLLM. Este despacho es analysis-design, únicamente estos seis documentos; después se requiere encargo Red separado. No se inventa otra aprobación humana ni se habilita código por este documento. Las decisiones y aprobaciones históricas se conservan verbatim; sus cifras de una/dos llamadas describen aquella fase, no el cupo vigente.

Ensayo acumulado verdadero: **4/13** solicitudes reales, sin reset; la ampliación a diez adicionales fue transmitida por PM02:48:58/TL02:50:08 del08/10. La cuarta fue despachada al Desarrollador para diagnóstico propio, no validación independiente. Su captura saneada demuestra HTTP200/JSON838bytes/una choice/finish_reason stop/ID válido y solo content_OK rechazado: cadena de3caracteres,2letras+1puntuación, sin cambio por strip. No se conoce el texto ni el signo y no se atribuye al tercer cuerpo. No es fallo por alias/coste ni PASS funcional.

El ledger privado conserva H=0.000031275USD, U=0.008064USD, P=0 y R=0.002016USD. Con el cap efectivo0.01 conservado al cierre, otra reserva exigiría0.010111275USD (exceso0.000111275). PM03:14:41 transmitido por TL03:17:15 acredita autorización humana específica para subir la MISMA credencial a0.03USD y actualizar su certificado ordinario; ejecución operativa pendiente de encargo separado, sin alterar H/U/P,4/13,routing/permisos/RPM/TPM/paralelismo ni límite global0.40. Registro privado PM jup047-diagnostic-cap-003-authorization-20261008.md. Esta autorización no se ejecuta ni habilita una quinta intención en estas fases. No se eleva el cap, concilia/libera U, renueva credencial ni se hace una quinta llamada en diseño/Red/Green/mutación. La limitación financiera no bloquea la corrección offline. Recibos/secretos/ledger completos permanecen fuera de Git; la autorización de aperturas no cambia el criterio ni los gates.

## Why

La operación diaria necesita conocer el estado de conectores, ingesta/jobs, base vectorial y API LLM desde la aplicación. Actualmente `/health` solo comprueba database, rabbitmq y vector_store; `/overview-legacy` muestra ese resultado junto a facturación. No existe una pantalla de salud dedicada, ni un contrato operativo para ejecuciones fallidas, Azure simulada, LiteLLM/OpenRouter, datos parciales o plazos de respuesta.

Alcance trasladado desde la tarjeta por coordinación el 06/10/2026: dashboard funcional, pruebas y documentación, integrar/promover health-status, estados ok/degraded/failed/unknown, última actualización y despliegue en DockerServer M5. Paris pidió máxima continuidad visual con el resto de la app. Asignaciones recibidas: Paris líder, Víctor pairing, Alejandro revisión, Lucía validación; no acreditan participación realizada.

## What Changes

- Crear una ruta autenticada `/system-health`, accesible desde la navegación existente, con componentes, tokens, espaciado y controles de la aplicación.
- Añadir `GET /health/status`, autenticado y con tenant autorizado, para diagnósticos agregados de solo lectura. Conservar el contrato público `/health` y sus consumidores/healthchecks.
- Mostrar backend, CockroachDB, RabbitMQ, processor API, pgvector, Azure Cost API simulada, gateway LiteLLM y observación OpenRouter diferenciada. Añadir resumen de jobs e ingestas Azure del tenant, fallos de las últimas 24 horas y fecha de última ejecución/ingesta disponible.
- Distinguir comprobación actual, historial persistido y modos simulados/no verificados. No declarar sano el worker por tener una API viva ni OpenRouter por alcanzar el gateway. Comprobar OpenRouter con una llamada REAL al abrir panel y otra por acción manual Actualizar, sujetas a admisión segura; polling automático30s solo diagnósticos sin inferencia.
- Aclarar el mensaje sintético fijo para exigir dos letras OK sin puntuación, manteniendo la comparación normalizada vigente; adaptar únicamente GET LiteLLM /health/liveliness al literal JSON de la versión fijada, sin relajar otros probes.
- Acotar las comprobaciones y refresco; aislar errores por componente y respuestas tardías de tenant/sesión anterior; mostrar última comprobación UTC y obsolescencia.
- Preparar pruebas Docker locales aisladas equivalentes para los contratos comprobables. Mantener despliegue y evidencia en DockerServer M5 como requisito externo pendiente; la equivalencia local no lo sustituye.

## Capabilities

### New Capabilities

- `system-health-dashboard`: pantalla operativa coherente con la aplicación, actualización, estados y aislamiento de sesión/tenant.

### Modified Capabilities

- `health-status`: añadir contrato operativo de solo lectura; los requisitos existentes de `/health` y `checked_at` no cambian. Su promoción se hará en el archivo autorizado del cambio, no en esta fase.

## Impact

Implementación prevista: backend health/schema/servicio de diagnóstico, consultas acotadas de lectura y acción POST independiente para verificación real con admisión/idempotencia/reserva de coste; frontend contracts/api/hook/página/ruta/nav; documentación de configuración, pruebas y despliegue. Usar control de claves/gasto persistido del gateway existente, sin nueva dependencia de producción, migración o almacenamiento histórico del producto, scheduler, herramienta de monitoreo ni integración del código pendiente de JUP-055.

Las consultas leen las tablas ya disponibles `jobs` y `azure_cost_ingestion_runs` bajo tenant; no asumen propiedad de sus migraciones. Las conexiones de diagnóstico no cambian plazos ni comportamiento del tráfico de negocio. Cualquier necesidad de índice/migración/ADR o nueva dependencia deberá volver a decisión antes de implementarse.

## Scope decisions supplied on 06/10/2026

Paris exige comprobaciones reales de OpenRouter. La propuesta concreta es apertura del panel y Actualizar manual; el refresco30s no genera llamadas pagadas. Se fija el alias principal del proyecto, una petición sintética breve, cero retries/fallbacks y límites de tokens, concurrencia y frecuencia. Límite inicial autorizado de ENSAYOS JUP-047: **0,40 USD acumulados**, incluidas reservas de coste incierto, fallos y todas las repeticiones. No es1EUR ni crédito del panel desplegado. La contabilidad de ensayo queda fuera del producto/Git; no se ejecuta gasto durante diseño.

Paris acepta Docker local primero y M5 pendiente de coordinar con Alejandro. Acceso/topología/secretos/TLS/rollout se concretan antes de desplegar; no bloquean presentar este diseño, pero el criterio/tarea/evidencia M5 siguen pendientes y la JUP no se cierra sin ellos. No reutilizar Compose local inseguro como configuración compartida.

La aprobación pre-code de este diseño consta en el registro del 06/10/2026 incluido a continuación. Los detalles técnicos y guardas de gasto están en [design.md](design.md); matriz completa en [acceptance-map.md](acceptance-map.md). Precio vigente, límites efectivos/contabilidad y credenciales se verifican por coordinación antes de cualquier llamada real; si no permiten garantizar el techo, no se llama y se consulta. Uso habitual requiere presupuesto finito y autorización de su responsable separados de0,40USD de ensayo. Código y Red requieren esa aprobación concreta y el despacho de su fase; la aprobación no acredita ejecución ni resultados.

## Corrección autorizada del criterio — 07/10/2026

Fuente: despacho TL del 07/10/2026 a las 22:49:38 Atlantic/Canary, que transmite el mensaje PM de las 22:47:49 y la decisión expresa de Paris: «pues cambia el criterio, creo que estamos dandole importancia a algo que no la tiene para nada». Se documenta como decisión transmitida, sin crear un registro humano adicional ni modificar la aprobación histórica del 06/10.

La disponibilidad depende de una respuesta funcional/HTTP válida de la comprobación admitida. El nombre devuelto es información y su identidad queda no confirmada; un alias, una versión o un nombre diferente no causan fallo por sí solos. El coste es información independiente y no prueba identidad ni disponibilidad. Esta decisión sustituye el gate de igualdad exacta del modelo y las propuestas anteriores de marcadores, flags o allowlists de identidad; no se implementarán esos mecanismos.

La aprobación transmitida cubre esta corrección si la especificación es válida. Se entrega diseño únicamente; Red, Green y mutación requieren despachos separados del TL, sin solicitar de nuevo la misma aprobación. Autenticación/autorización, aislamiento, configuración de modelos/routing, respuesta/formato/errores, límites de uso, admisión y contabilidad conservadora se conservan. La reserva incierta anterior no se libera ni se reinicia, y no se realiza otra inferencia.

Los campos informativos separan identidad no confirmada y coste del gateway no confirmado de la fecha de respuesta funcional válida. No se fabrica coste, concilia el ensayo anterior ni hace otra inferencia. Evidencia M5 disponible: simulación local; trabajo real en DockerServer M5 pendiente con Alejandro. El hallazgo móvil diferido no se reabre. Los detalles están en design.md, ambos deltas y tareas6/matriz.

## Reserva histórica no bloqueante — decisión de 07/10/2026

Fuente: decisión expresa de Paris «ok vamos a ello», registrada por PM el 07/10/2026 a las **23:23:23 Atlantic/Canary (22:23:23 UTC)** y transmitida por TL a las23:23:55. El prefijo PM23:20:00 fue corregido por TL; no es la hora de la decisión. La fuente durable privada es jup047-historical-reserve-nonblocking-20261007.md, conservada por PM fuera del producto. Sustituye la propuesta financiera excepcional one-shot y las cláusulas anteriores que exigían conciliar toda incertidumbre o certificar incertidumbre cero antes de una nueva comprobación.

Se conserva íntegro el historial y recibo de la primera llamada, sin convertir retrospectivamente su UI en PASS, borrar reservas, inventar conciliación/saldo/coste ni reiniciar contadores. Una reserva histórica registrada o la ausencia de conciliación no bloquean por sí solas otra comprobación expresamente autorizada: la admisión ordinaria y su certificado deben admitir estado incierto no cero y descontarlo íntegramente del margen. No hay excepción financiera por llamada ni certificado especial de incertidumbre cero.

Permanecen0,40USD acumulados y DOS envíos totales: UNO ya enviado y UNO adicional disponible sujeto a los gates ordinarios. Se conservan autenticación/tenant/aislamiento, una llamada activa, cooldown60s,6/hora,24/día, retries/fallback0, configuración de modelos/routing y privacidad. Coste/procedencia son información independiente de disponibilidad. La key upstream es compartida: no se exige exclusividad de esa key, acceso nuevo ni contabilidad del gasto de compañeros. La exclusividad de admisión/ledger se limita a la credencial diagnóstica y su ejecución autorizada.

Esta decisión ya cubre la corrección pre-code si la especificación es válida; no solicita repetir esa aprobación. En esta entrega solo cambia diseño. Los cuatro tests Red existentes siguen congelados hasta un NUEVO despacho Red que revise expresamente las expectativas de bloqueo por incertidumbre. No hay inferencia real hasta corrección revisada, controles independientes PM, preflight ordinario vigente y ejecución del Validador. No se autorizan servicios, claves, permisos, inferencia ilimitada, publicación, archivo ni merge.

Ver contrato ordinario, estado existente sin flags/fechas nuevos, desigualdad presupuestaria, preservación de contador/límites y alcance de llm-provider-routing en design.md; ambos deltas y tareas7/matriz se actualizan coherentemente. La propuesta excepcional externa anterior se conserva como evidencia supersedida, sin implementarla.

## Ajustes proporcionados aprobados — 07/10/2026

Paris aprueba, según transmisión PM23:31:51 Atlantic/Canary conservada privadamente en jup047-proportionate-validation-approval-20261007.md: preparación financiera mínima sin excepción especial ni nuevas garantías no comprobadas que impidan la prueba; reutilizar simulación local vigente; DockerServer queda comprobación externa de Alejandro, separada de entrega técnica local sin borrar ni aprobar el criterio; consolidar tareas acreditadas con resultados/entornos/revisión y repetir solo afectados o controles de proceso. No SSH, auditoría de gasto ni servicios/accesos nuevos. Se conservan controles comprobados, historial/reserva y límites. No supone aprobación funcional, publicación, archivo o merge. Las casillas consolidadas y referencias E1–E5 en tasks.md explicitan los límites, incluido Red actual y revisión/validación de la corrección pendientes.

## Aprobación humana pre-code — 06/10/2026

Paris Arcos aprobó expresamente el diseño actualizado en el chat Coordinador: «apruebo», registrado el 06/10/2026 a las 18:08:29 Atlantic/Canary.
Alcance aprobado: panel integrado con estilo/componentes existentes, estado de servicios y jobs/ingestas, OpenRouter real al abrir y Actualizar manual, polling sin inferencia; una llamada activa, cooldown60s, límites6/hora y24/día. Ensayos con máximo acumulado0,40USD y preflight operativo antes de gasto. Presupuesto habitual separado antes de activar; Docker local primero y despliegue compartido pendiente con Alejandro antes del cierre.
Esta aprobación autoriza la implementación mediante fases separadas del Desarrollador, empezando por Red. No autoriza publicaciones, archive, merge o despliegue compartido; no acredita comprobaciones aún no ejecutadas.


## Entrega técnica acreditada — E12

El despacho condicional TL03:22:56 separó Red, Green y mutación. La petición fija y la sonda LiteLLM están implementadas con el analizador funcional del proveedor intacto; el GET continúa no generativo. E12 acredita el delta local y sus límites; este documento ya no está esperando iniciar el Red de esa corrección. La consolidación posterior es factual, no otra ceremonia de diseño ni una nueva decisión humana. Antes de revisión independiente: original y control de PM, coordinación TL y estado final de fuentes. No publicación o archivo por este registro.
