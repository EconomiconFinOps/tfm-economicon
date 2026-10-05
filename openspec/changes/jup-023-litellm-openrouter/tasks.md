## 1. Preconditions

Enmienda F1 del 2026-10-02 aprobada por Paris, implementada y comprobada:
simulacion 25/25 controles, contador virtual positivo y bloqueo sin upstream.
Unico embedding real de repeticion PASS: SpendLogs, contador y delta oficial
coinciden en 0,000000240 USD. Revision tecnica y QA local PASS; gates humanos
y autorizaciones externas pendientes.

Estado 2026-10-02: implementacion offline disponible; saneamiento comprobado
en la integracion simulada, conservando las 10 filas del escenario base.
Python 3.12: 433 passed, 57 skipped. Controles simulados de presupuesto,
revocacion y caducidad comprobados; no equivalen a gasto real contabilizado.
Paris confirma el acuerdo del equipo. Clave upstream verificada: 0,40 USD sin
reinicio. Smoke real y llamada adicional de diagnostico: HTTP 400 en chat,
sin retries ni embeddings; ultimo diagnostico identifica limite de gramatica. Evidencia y
limites en [JUP-023-validation.md](../../../docs/evidence/JUP-023-validation.md).
Ocho peticiones de chat y tres de embedding al gateway; sin PR ni cierre.
Captura temporal autorizada: ExportLimitError, mas de 262144 estados intermedios
al compilar la gramatica del schema en GLM; campo causante no identificado.
La propuesta de simplificar schema no esta aprobada. Prioridad acordada: buscar
endpoint compatible del mismo modelo manteniendo el schema estricto intacto.
Paris aprueba `deepinfra/fp4` via OpenRouter: routing aplicado, 7/7 checks de
config, 19 controles Docker y dos mutantes detectados. Un chat real supera
FinOpsResponse; otro fue rechazado por validacion local (regla no retenida).
Ultimo smoke real PASS: FinOpsResponse valido, vector finito de 1536 dimensiones
persistido y trabajo completed (estado SQLite temporal, vector pgvector real).
Uso oficial acumulado 0,002591548 USD; reservas conciliadas y caps intactos.
La correccion posterior acredita gasto positivo y contador virtual en real;
rechazo por presupuesto comprobado en simulado. Revision tecnica/QA local PASS.

- [x] 1.1 JUP-023 validar OpenSpec/trazabilidad y obtener gate humano pre-code sobre el plan y archivos previstos, incluido `core/config.py`; Paris aprueba el 2026-10-02 la fase offline con la condicion registrada en proposal.md.
- [x] 1.2 JUP-023 completar compatibilidad Docker (config, API, auth, claves virtuales, privacidad y retries) con upstream simulado: Paris autoriza el 2026-10-02 el pin 1.103.2 y Docker local aislado sin gasto segun [ADR-0016](../../../docs/adr/ADR-0016-litellm-version-pin.md), aun Proposed. Compatibilidad simulada comprobada con los limites de la evidencia; revision de 17 advisories, digest e imports no acredita firmas verificadas. No ejecutar 1.82.6.
- [x] 1.3 JUP-023 antes de uso real, resolver pendientes ADR-0002/privacidad, verificar acceso de modelos y claves limitadas; comprobar precios, conversion conservadora y techo total 0,50 EUR con margen y stop ante coste desconocido. Acuerdo confirmado por Paris, limites/precios/ZDR comprobados; smoke y conciliacion agregada pasan con limites documentados. No sustituye aprobaciones individuales ni el estado formal de los ADR.

## 2. Offline Implementation After Pre-Code Approval

- [x] 2.7 JUP-023 tester reutiliza pruebas de config y test/fixture Docker opt-in para fijar solo el principal a `deepinfra/fp4` mediante OpenRouter (`provider.only`, `require_parameters: true`); schema/modelo/privacidad/limites intactos, 7 checks de config y 19 controles Docker pasan; dos mutantes detectados. Config/README implementados bajo aprobacion registrada en proposal.md.

- [x] 2.1 JUP-023 reutilizar pruebas existentes y anadir casos focalizados que fallen para HTTP, limites 30/2/800, payloads y errores; no tocar ajustes Azure ni FinOpsResponse 1.0.
- [x] 2.2 JUP-023 conectar factorias/settings a adaptadores stdlib chat/embeddings, sin SDK, redirects ni fallback; validar contenido chat y vectores finitos de dimension exacta.
- [x] 2.3 JUP-023 clasificar solo fallos de salida de guardrails en ruta LiteLLM como ProviderError, preservarlo al marcar ingestion failed y manejar nack false en worker; conservar comportamiento mock y otros errores.
- [x] 2.4 JUP-023 comprobar logging saneado, uso/coste opcional, retries solo transitorios y errores de auth/request/invalidresponse sin retry; regresiones y mutaciones focalizadas registradas con sus limites en la evidencia. Suite existente repetida con Python 3.12: 433 passed, 57 skipped.
- [x] 2.5 JUP-023 verificar en la imagen 1.103.2 el callback publico y su orden previo a SpendLogs, incluida persistencia asincrona de fallos; saneamiento y preservacion de filas/metadatos/coste comprobados. Inicializador sin modulo aborta antes de crear router: prueba del inicializador, no ensayo HTTP de arranque. Sin monkeypatch ni parche del proveedor; un fallo del hook en runtime no tiene mecanismo automatico fail-closed, limite documentado y aceptado.
- [x] 2.6 JUP-023 implementar `infra/litellm/safe_logging.py`, montaje solo lectura y registro en config/Compose existentes, y documentar en README; sin SDK ni dependencias nuevas. Conservar fallos, estado/modelo/request ID/tiempo/duracion/tokens/coste disponibles; no activar `disable_error_logs`, borrar registros ni convertir coste desconocido en cero. Modulo ausente o import/registro fallido debe impedir servir trafico de modelos. Implementacion y replay simulados comprobados; inicializador sin modulo aborta antes de crear router, no es un ensayo HTTP de arranque.

## 3. Isolated Integration After Image Approval

- [x] 3.2b JUP-023 comprobar routing aprobado y parametros completos con upstream simulado reutilizando fixture existente; fallo incompatible no cambia ruta ni relaja schema/privacidad. Reservas previas conciliadas con evidencias registradas; margen acreditado bajo cap upstream 0,40 USD sin reinicio y techo agregado 0,50 EUR, sin aumento de caps.

- [x] 3.1 JUP-023 preparar Compose adicional opt-in, PostgreSQL propio para virtual keys, red aislada, admin loopback, health sin LLM y secretos externos; mantener defaults mock y schema existente de 8 dimensiones. Preparacion/arranque y privacidad simulada comprobados; acceso desde Windows probado mediante relay de fixture, no puerto publicado directo.
- [x] 3.2 JUP-023 verificar gateway contra upstream falso: alias JUP-078, parametros de privacidad, claves virtuales, limites y retries efectivos cero en gateway. Presupuesto preagotado, revocacion y caducidad rechazan sin llegar al upstream; 22 comprobaciones del replay final pasan. Presupuesto sembrado sintetico, no acumulacion de cargos reales. Sin OpenRouter ni garantia de privacidad fail-closed ante excepciones internas del hook; ver limite aceptado de 2.5.
- [x] 3.2a JUP-023 reutilizar test/fixture Docker opt-in para comprobar orden previo a persistencia y rutas normales de error: sentinels ausentes de DB y consola, 10 filas base con fallos y metadatos/costes conocidos conservados, exito sin regresion. Inicializacion fallida comprobada directamente, no mediante HTTP. Pruebas y mutaciones con limites en la evidencia; si falla el hook en pruebas, bloquear uso real. Sin mecanismos automaticos nuevos en runtime, perdida de registros ni mecanismos privados.
- [x] 3.3 JUP-023 ejecutar smoke real secuencial tras gate de uso/coste: principal FinOpsResponse, embeddings1536 y recorrido processor con texto sintetico y pgvector desechable. PASS, vector finito persistido, trabajo completed en SQLite temporal; no es E2E Cockroach/RabbitMQ. Sin secundario, fallback ni retries; limpieza completada.
- [x] 3.4 JUP-023 conciliar coste total incluidos fallos cobrados/retries, registrar SHA/config/digest/limites y resultados saneados. Total oficial 0,002591548 USD; tarifa de embedding derivada corroborada por delta oficial, SpendLogs y contador virtual positivo, no factura individual. Ver correccion y limites en evidencia.

## 4. Verification And Delivery Gates

- [x] 4.1 JUP-023 strict OpenSpec 37/37, trace 9, hygiene 727 archivos y diff check pasan; regresiones aplicables reutilizadas y pruebas afectadas repetidas segun evidencia. QA mapea criterios, errores y omisiones; no se afirma CI remoto ni suites ajenas ejecutadas.
- [ ] 4.2 JUP-023 antes de cualquier PR, incluido borrador, superar las pruebas reales 3.3 y registrar evidencia/coste 3.4; confirmar roles y obtener autorizacion explicita de publicacion. Obtener Revision y Validacion separadas segun proceso local JUP-100 y repetir las afectadas por cambios.
- [ ] 4.3 JUP-023 completar QA y aprobacion humana final; merge, archivo y actualizacion Trello solo con sus autorizaciones, coordinando capability con JUP-078 y orden de archivo pendiente. No atribuir veredictos de agentes a humanos.

## 5. Approved Embedding Budget Correction

- [x] 5.1 JUP-023 aprobacion explicita de Paris registrada en proposal.md: solo model_info del embedding a 2e-8 USD/token entrada y 0 salida, con max_price.prompt 0.02 USD/millon; tarifa no presupuesto, cap de clave intacto.
- [x] 5.2 JUP-023 Node RED 5/2 y GREEN 7/0; config/README y tres archivos de pruebas existentes actualizados, cero casos permanentes nuevos. Transmision max_price comprobada; dos mutantes detectados, sin cambio de modelo/schema/dimensiones/privacidad/imagen.
- [x] 5.3 JUP-023 simulacion PASS 25/25: gasto 0,000000240 por llamada, contador 0,000000480 tras dos; tercera HTTP429 budget_exceeded sin upstream. Sin gasto precargado. Observacion del test corregida para usar tipo estructurado, no mensaje saneado. Acumulacion asincrona, no reserva atomica ni garantia de no sobrepasar cap en vuelo.
- [x] 5.4 JUP-023 un embedding real HTTP200, sin chat/retry: vector1536 finito, SpendLogs/contador/delta oficial 0,000000240 USD. Total 0,002591548 USD bajo caps intactos; precio/ZDR/margen revalidados, secretos y recursos limpiados. No se repitio persistencia ni suites no afectadas.
- [x] 5.5 JUP-023 revision tecnica afectada REVIEW_PASS y QA local QA_PASS, guards sin cambios; F1/F2 cerrados y precision documental F3 corregida. Smoke previo y limites conservados. Aprobacion final humana, reviews humanas y autorizacion de publicacion siguen pendientes.

## 6. PR 65 Attempt Deadline Correction

- [x] 6.1 JUP-023 enmienda validada: OpenSpec estricto 38/38 y trazabilidad PASS. Aprobacion explicita de Paris "si" registrada en proposal; alcance local sin consumo ni publicacion.
- [x] 6.2 JUP-023 RED real loopback: cuatro casos de goteo cuerpo/cabeceras con retries 0/2 fallan y el control positivo pasa. 0,453-0,454 s frente a timeout 0,05 s; aserciones de elapsed, categoria, intentos y cierre. Solo cinco casos nuevos en test_agent_runtime.py. Evidencia registra comandos y limitacion DNS encontrada antes de Green.
- [x] 6.3 JUP-023 deadline HTTP implementado en app/clients/litellm.py: socket/TLS/cabeceras/cuerpo usan presupuesto restante; cierre por timeout, backoff e intentos acotados conservados. Sin resolver/subprocesos DNS, dependencias ni cambios ajenos. La limitacion DNS consta en la evidencia.
- [x] 6.4 JUP-023 GREEN: cinco regresiones pasan; processor 438 passed/57 skipped, tres mutantes detectados. Revision tecnica y QA local PASS, guards y DoD de etapa QA PASS. Evidencia registra tiempos, cierre, intentos, comandos y limitaciones; sin nuevas pruebas adicionales, OpenRouter ni DockerServer.
- [ ] 6.5 JUP-023 entregar resultados para nueva Revision de Alejandro y Validacion de Lucia bajo CONTRIBUTING 2026-09-30 (JUP-100); ambas solicitudes de cambios siguen pendientes hasta sus Approve. Mantener gate humano final, sin publicar reviews, commits, push, merge, archivo ni actualizar trackers en esta fase.
- [x] 6.6 JUP-023 revalidacion real autorizada tras correccion: chat FinOpsResponse valido y embedding1536 finito comprobados con cliente actual; ensayo parcial conservado y una repeticion de embedding autorizada por separado. Sin retries; consumo adicional de esa repeticion 0,000000240 USD conciliado, limpieza completa. No sustituye reviews humanas ni repite persistencia; ver evidencia.
