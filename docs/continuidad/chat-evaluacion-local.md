# Evaluación local de JUP-035

Origen: [JUP-123 / JUP-035B](https://trello.com/c/TqtcumIN), chat
`01a1270c-e332-7462-9c90-706d49ade92c`.

Evidencia y operadores citados sin otro prefijo: `../materiales/07-evidencias/PR121-local-evaluation/`
desde la raíz del proyecto. El entorno remoto aislado está bajo
`/home/danteadmin/economicon-jup123-20261014` en DockerServer.

## Estado actual — 16/10/2026

Análisis y justificación de modelos para el TFM: [memoria-modelos.md](memoria-modelos.md).
Contribución preparada para JUP-063/JUP-109, sin duplicar tareas. DeepSeek es la
elección local vigente; la ventaja histórica de calidad de GLM y sus fallos se
conservan. No se modifica la memoria compartida o el modelo del gateway común.

### N3 completa; claves ampliadas 24 horas — 16/10/2026

Respuesta humana real: «Amplia las claves 24 horas». Se amplió únicamente la
caducidad de las MISMAS dos claves hasta el **17/10/2026 a las 18:00 de París**;
límites processor4.5/backend0.1USD, contadores y reservas conservados. Prueba
`allocation-deepseek-expiry-24h-20261017-v1.json`. Sustituye la solicitud19:00
pendiente del corte anterior; no hay permiso pendiente de caducidad.

Continuación externa explícita, política990a7df0, protegió1361asientos/80recibos
y recogió SOLO025–028r3, sin repetir80 ni enviar embeddings. Controller-v3
PID4170005/start76793587 TERMINADO COLLECTED; no relanzarlo. La política histórica
ca97550b y la fuenteCAP20 permanecen intactas; cap30 aplicado en admisión y ledger.

**84/84 completed y verificadas; 84 respuestas conformes en revisión local
provisional, 495comprobaciones (327banco/168calidad), 28/28 por cada ronda.**
Los cuatro resultados finales se contrastaron contra pregunta, respuesta y RAG
real; la herencia de etiquetas sólo usa identidad exacta de respuesta completa
y contexto dentro de esta campaña. 012,015,017,020 y027 pasan3/3. Sin fallos o
incertidumbres locales nuevos. No adjudicación independiente ni aceptación.

Fuentea7f9502d/banco1.0.1/corpus54/plan5f3186da; DeepSeekV4.1Flash/CoreWeaveFP8,
ZDR/sinfallback/temp0/razonamientodesactivado. No se atribuye la mejora a un solo
factor ni superioridad general; respuestas variables en005/007/016/023/024.
No se heredan N3/N5de5119 ni la parcialGLM. N5 del candidato nuevo NOejecutada;
criterios obligatorios y alcance final con revisores siguen pendientes.

Ledger1365/SHAeb664308fb3b8aceed0c2493a6d167d3afa51a7b96b2c990da7e8ba7fb10e1f5; prefijos1281/1307/1361 y80recibos intactos.
84costes observados:0.176265160USD (cuatro finales0.007430496USD, redondeados9decimales).
Reservas desconocidas anteriores13.99052050USD intactas, incluidas ambas0.01de
embeddings. Cota conservadora de cuenta21.448811463/30USD;
NO factura ni atribución exacta. Ningún handle pendiente o reserva liberada.

B anterior restaurado sano, mismosIDs/imágenes, demás servicios y proxy
compartido sin cambios; backend/processor/proxy/frontend temporales parados.
Navegador003/012/027/historial/recarga/1280/390px ya conforme sin generaciones;
no se repitieron suites/builds/UI ni se cambió producto durante esta continuación.
Las imágenes derivadas ejecutadas se distinguen de las estándar no activadas.

Auditoría `allocation-deepseek-api-n3-final-audit-v2.json`, SHA07d33e8b61affeb07b62ede7a7010920a1b96f08b30eddf72f4b15a9bc4cc06f.
Paquete NUEVO `allocation-deepseek-n3-frozen-v1`:203archivos,
manifestSHA996304903e99d2a7449e8378dc605ae80a041f090b0e78f475866e1d79f43c3c.
Parcial80/185archivos y paquetes históricos preservados, sin sobrescribirlos.
Procedimientos y siguientes pasos en `allocation-012-handoff-v8.json`.
B preparada localmente; no publicada, integrada, activada permanentemente o
aceptada. No GitHub/Discord/Done. PR131 permanece independiente.

El corte80 siguiente es histórico, anterior al permiso de24horas y al cierre.

### Corte conservado: 80 de 84 respuestas conformes — 16/10/2026

La N3 separada de DeepSeek V4.1 Flash/CoreWeave FP8 terminó su vigencia de
admisión en 80/84: todas completed, verificadas, con coste observado y conformes
en la revisión local provisional. Son 473 comprobaciones: 313 del banco y 160
de calidad. Faltan exactamente JUP-069-025,026,027,028 de la repetición3.
No se declara N3 completa ni aceptación humana. 012,015,017 y020 pasan3/3.
La fuente sigue siendo a7f9502d, banco1.0.1 y plan5f3186da; no se hereda N5de5119.

Controller-v2 PID3585894/start76242235 TERMINADO por corte de seguridad17:50París;
no relanzarlo. Restauró el B anterior sano, mismos IDs/imágenes, demás servicios
sin cambios. 024r3 ya se había generado: se recogió por GET/SQL tras el corte y
se contrastaron todos sus cargos, sin nuevos POST de generación/embeddings.
Sólo se activó brevemente el backend propio con margen fresco de RAM; processor y
proxy siguieron parados. Los79recibos y1360asientos previos quedaron idénticos.
Después volvió a quedar parado; el B anterior permaneció sano durante esa lectura.

Ledger1361/SHAbea760b6a50b30103264d22050f085e634c28436dce05a79ce9b927d1e8a24cf,
80costes observados, ningún handle pendiente. Primeras26respuestas y prefijo1307
intactos. Coste nuevo observado0.168834664USD; reservas desconocidas anteriores
13.99052050USD intactas. Cota de cuenta21.375932853/30USD: conservadora, no factura
ni atribución exacta al trabajo. Ambas reservas de embeddings0.01USD se mantienen.

UI003/012/027 conforme: texto, fuentes, fechas, historial y recarga;1280/390px sin
overflow del documento. CeroPOSTgenerativos. Frontend temporal parado y túnel
propioPID6600 cerrado comprobando identidad. Dos fallos previos del arnés de espera
del botón y el incidenteSSH recuperado se conservan; no implican cambios de producto.

Solicitud de ampliar sólo la caducidad de las mismas claves hasta HOY19:00París
PENDIENTE: no respuesta humana al corte, no aplicada ni archivo de permiso creado.
Vigencia actual hastaHOY18:00, límites4.5/0.1USD; no inferir prórroga del presupuesto.
Procedimiento preparado: extend-allocation-existing-expiry-1900-prepared-v1.py.
No hay trabajos pagados vivos. Sin permiso nuevo, no inferencias ni nueva pregunta.

Auditoría allocation-deepseek-n3-partial-audit-v1.json; paquete inmutable de185
archivos allocation-deepseek-n3-partial-frozen-v1, manifestSHA
bb42a50daf7f4cd29a083cf4d8ad96bb25a5e35436db920f3f756cde497aaaca.
No sobrescribirlo al continuar. Handoff vigente allocation-012-handoff-v7.json.
OpenSpec estricto75PASS en el CLI instalado; pnpm intento previo no ejecuto
la validacion y rechazo reinstalar dependencias compartidas, sin cambios de producto.
Con permiso real y vigente: nueva política/continuador externos protegiendo1361 y80
recibos; empezar sólo por025r3, mismo código/modelo/prompt/banco/ledger, ZDR sin
fallback. La política antigua de caducidad18:00 y sus hashes no se modifican.
No repetir suites/builds/UI ya conformes sin cambio nuevo. Criterios y adjudicación
independientes siguen pendientes; B no publicada, integrada ni aceptada.

Los cortes inferiores son históricos y quedan superados por el anterior.

### SSH recuperado y navegador conforme — 16/10/2026 15:33UTC

IncidenteSSH transitorio conservado en allocation-deepseek-ssh-access-loss-v1.json.
Se recupero el acceso sin reiniciar ni reenviar nada; mismoPID3585894/ticks76242235.
Ultimo corte remoto15:32UTC:52completed/52costes observados. Local49revisadas,
290checksPASS;020r2 verificada por derivacionRAG normal, sin nueva inferencia.
UI003/012/027PASS: texto, fuentes, fechas, historial/recarga,1280/390px.
NingunPOSTgenerativo. Frontendpropio parado/tunel6600 exacto cerrado.
Dos fallos previos del arnesUI por espera del boton conservados; producto intacto.

Se solicito ampliar SOLOcaducidad de las mismas claves deHOY18:00a19:00Paris
si hace falta acabar; SINRESPUESTA al corte, procedimiento preparado NOejecutado.
No crear permiso, renovar o prolongar controlador por silencio. Proceso actual
sigue dentro de vigencia18:00/corte17:50Paris,30USD/reservas intactas.
Auditoria/paquete full84 preparados pero NOejecutados; N3 no es completa.
Handoff vigente allocation-012-handoff-v6.json; estado posterior solo por observacion.

### N3 DeepSeek reanudada sin repetir las 26 primeras — 16/10/2026

Semilla54 cargada una sola vez con el segundo permiso; ambas reservas0.01USD
intactas. GLMparcial4 congelada (2respuestas/2tecnicas429), no es N3completa.
Productoa7f9502d/banco1.0.1 y corpus nuevo no heredan la N5de5119.

DeepSeekV4.1Flash/CoreWeaveFP8, ZDR sinfallback, temperatura0/razonamientodesactivado:
la primera ejecucion termino en26completed,26costes observados. Processor512MiB
OOM provoco parada ANTESde reservar027; fallo y restauracion conservados.
Mismo contenedor/imagen ahora768MiB, margen completo fresco436MiB>=384.
Continuador unico PID3585894/start76242235, controllerSHA9c3a85bc, desde027r1:
plan5f3186da, mismas claves/contadores y30USD; NO repetir26 ni relanzar por timeout.
Prefijo1307/SHA720de4c900ff601d422ca916a696d2f58eee7036acf736d1b12b40fa0b12bda6
y26recibos protegidos. Viejo controlador3333099 terminal; no relanzarlo.

Corte15:13UTC:29completed/29costes observados, segunda ronda iniciada.
Revision local de26:153requisitosPASS;012 separa tags/asignacion sin inventar
optionalidad deowner;017 limitesestrictos y020riesgocondicional conformes en r1.
027r1/028r1 ya leidas, etiquetas pendientes al corte. Ninguna aceptacion humana
o superioridad general; repeticiones restantes, auditoria y UI nuevas pendientes.
Frontend propio preparado pero parado; no validacion UI nueva aun.

Entorno propio economicon-jup123-ds-a7f9502d, SQLjup123_ds_a7f9502d,
vectoresjup123_alloc_a7f9502d reutilizados. Proxy compartido sin cambios.
Backend/processor viejos pausados con permiso humano y restauracion al terminar.
Reservas desconocidas anteriores13.99052050USD intactas; maxoperacion0.0889632USD.
Claves existentes4.5/0.1 hastaHOY18:00Paris; no prorroga/nuevasclaves/resets.
Handoff `allocation-012-handoff-v5.json`; evidencia externa no contiene secretos.
B local, sinGitHub/Discord/merge/Done; adjudicacion independiente pendiente.

El corte siguiente conserva el estado anterior, no el actual.

### Corpus cargado y N3 alternativa en curso — 16/10/2026

Permisos humanos de segundo envío y pausa/restauración recibidos. Semilla
`baec863e-4786-40a4-9b21-f5d060456224` confirmada:3documentos/54fragmentos.
Se conservan tanto el primer intento fallido como las dos reservas0.01USD;
NO volver a ejecutar semillas. Fuentea7f9502d/banco1.0.1, prompt/contrato intactos.

GLM/DeepInfra se detuvo en4muestras:001r1 y004r1 técnicas porHTTP429,
002r1/003r1 completadas y revisión local11checksPASS. Todas mantienen sus
máximos íntegros0.319952USD por intentos sin facturación completa. Campaña parcial
congelada `allocation-glm-partial4-frozen-v1.json`; nuncaN3completa ni relabelar.
Controladores3058425/3110888/3163823 terminados; no relanzar. Si algún día se
retomaGLM sería005r1, separado del nuevo modelo. No hay prueba de caída global.

Dentro del permiso de elegir modelo del pool se prepara DeepSeekV4.1Flash por
CoreWeave/fp8, ZDR/sinfallback,temp0/reasoningdisabled, en runtime PROPIO
`economicon-jup123-ds-a7f9502d`, API29857/processor29858/gateway44003.
Misma fuentea7 e imágenes derivadas verificadas; SQL nueva `jup123_ds_a7f9502d`,
54vectores reutilizados de `jup123_alloc_a7f9502d`, sin nuevo envío de semilla.
Proxy compartido sin cambios de ID/imagen/inicio/rutaGLM; proxy propio usaMISMAS
claves y DBdecontadores, con DISABLE_SCHEMA_UPDATE=true. Sin resets/nuevas claves.
Preparacionesv1/v2 fallidas preservadas;v2OOM512MiB. Runtimev3 sano con límites
512/512/768MiB y margen fresco384MiB, no ambos juegos antiguos/nuevos activos.
Antiguos backend/processorB pausados con permiso; el controlador los restaura.
Frontend NO arrancado ni validado en este runtime.

NuevaN3DeepSeek84 en curso: PID3333099/start76020386, controllerSHAe2ff5498,
planSHA5f3186da, políticaSHAca97550b. Al corte3completed/3costes observados;
no juicio semántico todavía, no aceptación. El launcher tuvo KeyErrorDESPUÉS de
Popen; se recuperó el proceso exacto porargv/ticks, NO se relanzó. Rootremoto
`allocation-deepseek-api-v1`; observer `observe-allocation-deepseek-api-v1.py`.
Exportadores/scorer y procedimientos exactos en `allocation-012-handoff-v4.json`.

Prefijo1281/SHA3e679f6859027616965218c25f762d71f35e2e938f6ee8861702be0682208dcc
protegido bytea byte. Reservas desconocidas anteriores13.99052050USD intactas;
operaciónDeepSeek máximo0.0889632USD, sólo nueva contabilidad correspondiente.
Máximo30USD acumulados; claves4.5/0.1 vencenHOY18:00París, sin prórroga.
Cota de cuenta conservadora, no factura ni atribución exacta. No repetir N5de5119,
Sonnet/Sol/DeepSeekhistórica; no atribuirlas a este nuevo corpus/modelo.
B sigue local, sin publicación/merge/Discord/Done; criterios y adjudicación
independientes pendientes. Siguiente: observar proceso existente, revisar respuestas
nuevas contra fuentes reales, auditar cierre y luego UI/historial. No permiso pendiente.

### Semilla fallida; arnés corregido, nuevo envío pendiente — 16/10/2026

El humano autorizó la pausa/restauración (`call_f2605a9419c44e8cbaab12cd84945b74`).
Se reactivaron los contenedores DERIVADOS exactos, sin cambiar imágenes/datos.
El intento único de semilla PID2884330/start75596562 terminó con TypeError:
`original.open(request,timeout)` pasó90.0 como cuerpo de urllib, en vez de timeout.
Se enviaron cabeceras, sin cuerpo del corpus; no respuesta ni corpus cargado.
Contadores proveedor idénticos antes/después. Corrección sólo del arnés a
`timeout=timeout`,6pruebas offline PASS, producto intacto. No se reenvió el POST.

Se conserva íntegra la reserva0.01USD, request `adcab9d6-83e2-4a41-92c7-ff7ed1ff275c`,
con estado original `EXTERNAL_SEED_DISPATCHING`/`COST_UNKNOWN_RESERVED`.
Ledger1276/SHA`4b4f41a3704c7f7d1a18f46ee7f6a2501e0a88a8958637d99f145ef5ad4e3cb5`;
prefijo1275/hash0e861c4 intacto. Reservas desconocidas12.70071250USD, no factura
ni liberación; máximo30USD. Corpus y chat nuevos0filas. Antiguo B RESTAURADO sano,
mismos contenedores/imágenes; demás servicios sin cambios, nuevo entorno parado.
Claves hasta hoy18:00París, sin prórroga. Nueva N3 sigue NOT_RUN.

Se preguntó UNA VEZ si autoriza otro intento único, mismo payload/destino, otra
reserva0.01USD conservando la anterior; pendiente. No repetir pregunta ni deducir
permiso del silencio. Handoff vigente `allocation-012-handoff-v3.json`;
`allocation-failed-seed-collected-v1.json` y `allocation-failed-seed-park-audit-v1.json`.
La exportación local se guardó bien; sólo su impresión inicial falló por cp1252,
sin repetición del trabajo remoto. `allocation-seed-installed-v2.py` demuestra la
corrección de una línea, pero NO es un continuador listo: guarda1275 lo rechazaría.
Un nuevo intento necesita política/identidad propias protegiendo1276 y luego N3
adaptada a la segunda semilla; conservar los originales, no alterar historial.
Trello actualizado por puente, SHAe4bc7bf8,16088caracteres, metadatos intactos.

Los cortes siguientes son históricos; no reemplazan este estado.

### Corte anterior: permiso de embeddings recibido; pausa entonces pendiente — 16/10/2026

El humano respondió «Sí, autorizo este envío de embeddings» a la pregunta
`call_24868e3f710e4e9992e7d832b25b888b`. Permiso real registrado localmente y en
DockerServer para body1a375375/manifest5b9b, una petición,30USD y reserva0.01.
**No se ha enviado ni reservado.** Una nueva revisión automática rechazó la
reactivación antes de ejecutar el comando: pausar el backend y processor del
entorno anterior B contradice la restricción previa de no interrumpir servicios.
Se solicitó permiso específico para esa pausa temporal y restauración; pendiente.
No reenviar la pregunta ni buscar una vía indirecta. No cambió ningún servicio.
Lectura fresca:1275filas/hash0e861c4 intactos, antiguo B sano, nuevo parado y sin
handles de semilla. Claves vencen hoy18:00París; ningún permiso recibido amplía
vigencia. Handoff vigente `allocation-012-handoff-v2.json`; se conserva v1 como
corte anterior, y `allocation-reactivation-review-stop-v1.json` registra el rechazo.


### Corrección012 posterior a la N5 — 16/10/2026

Candidato local `a7f9502d6da0e080560f028dfc260f77f729c937` en el checkout
integrado. Separa ausencia del tag, conformidad desconocida y una regla de
asignación inequívoca declarada. Política completa/autorizada y citas literales;
negaciones, contradicciones o evidencia incompleta no producen allocated.
Gramática acotada, no comprensión general ni verificación del tenant. Prompt y
contrato público intactos; manifiesto actualizado por el compilador nuevo.

213PASS Windows(209processor+4backend) y213identidades Linux PASS, sin omisiones
ni herencia;52pruebas del archivo nuevo. Replay offline167contextos(139RAG reales
históricos+28sinRAG):161esquemas intactos, sólo012cambia; sus cinco contextos se
resuelven en el replay con regla/citas recibidas, sinRAG se abstiene. No se cambian
las respuestas ni etiquetas históricas. Paridad backend/processor en167contextos
y carga en frío en56por servicio. `allocation-native-final-audit-v1.json`,
`allocation-counterfactual-proof-v2.json`, `allocation-resource-parity-v1.json`.

Dos builds estándar del MISMO commit ya PASS,224hashes verificados, sin cambiar
código o pin; frontend127sin cambios. `allocation-standard-build-final-audit-v1.json`.
La primera descarga del tokenizer no cumplió el pin; nueva lectura pública y el
build posterior sí lo cumplen. Se conservan fallo y anteriores imágenes derivadas;
no atribuir una activación o campaña a los builds nuevos. Source archive SHA
`3f71a7ad1930c54f0c1908415d5dcc3bfc9a5f6ff8556f8d2309b05094b229e6`.
PlanN3 `allocation-a7f9502d-n3-plan-v1.json`,84NOT_RUN, SHA
`fcc98f62902551820745deaa693e27036137b0e25b0a41f5ed5187b6e62bcc8b`.

Entorno separado preparado y **ahora parado**, bases SQL/vector
`jup123_alloc_a7f9502d`, cola `processor:jup123-alloc-a7f9502d`, red10.232.123.0/24,
API29757/processor29758/frontend29760; límites768+768+128MiB. Los contenedores
preparados conservan imágenes DERIVADAS: las estándar están construidas pero NO
activadas. Si se eligen las estándar para la campaña, registrar nueva activación
y actualizar las guardas con identidades reales antes de llamar al proveedor.
**Antiguos backend/processor B restaurados: mismos contenedores/imágenes, sanos**;
datos y demás servicios conservados. `allocation-runtime-parked-v1.json`.
No arrancar ambos juegos sin margen de memoria; no repetir builds/SQL/UI/tests
ya conformes sin motivo nuevo. Checkout5119/banco1.0.0 intocable para sus recibos.

**Intervención pendiente:** revisión automática rechazó enviar54fragmentos de los
3documentos sintéticos al modelo de embeddings OpenRouter/openai/text-embedding-3-small:
exige autorización explícita de payload/destino, además del permiso de validación.
Solicitud originalmente pendiente; APROBADA por el humano más tarde (ver corte superior). No reenviar la pregunta ni
interpretar silencio,30USD o este seguimiento como aprobación. Cuerpo al gateway SHA
`1a375375f5463989bb304250d3e2d4c9c60d54500e437adbf3367d1a8c9ed31e`;
manifest SHA`5b9b1e0588e6b66097fb0d161ec0810620953fe53b37baec7aa92784e25333b8`.
**No se ejecutó la petición ni se escribió su reserva**; nuevo corpus sigue vacío.

Arnés preparado, no instalado/ejecutado: `allocation-api-harness-prepared-v1.json`,
17controles de cobertura/contabilidad y8de semilla PASS. Política externa30
`allocation-validation-policy-v1.json`, SHA
`57df5302874fb538ac8b0d27f56595f2b310fa1650025636700b430f4e57ee88`,
protege1275filas; fuente presupuestaria20 permanece intacta. Semilla propuesta:
una petición, sin reintentos, reserva0.01USD ANTES del POST; nunca reenviar un
resultado incierto. Ledger1275/SHA0e861c4 y reservas12.69071250USD íntegros.
Última cota de cuenta consultada19.998613446/30USD, no factura ni atribución aB.
Mismas claves processor4.5/backend0.1 hasta16/10a18:00París; no renovación/reset.

Siguiente sólo tras permiso explícito: documentar la respuesta real, reactivar
recursos propios con guardas de memoria/identidad, preflight fresco y semilla
única; auditar corpus/ledger y preparar controlador antes de nueva N3. Si caducan
claves, la aprobación del payload no las renueva. Criterios/adjudicación y nueva
validación siguen pendientes; B no publicada ni aceptada. Trello preserva lista,
miembros y fechas; descripción verificada SHA
`e3bbb4022ff197fb329855f9c23474b31f520ed2de0676e24da7920790da6e53`,16041caracteres.
Paquetes N5final310/parcial250,560archivos, nuevamente comprobados intactos.

**N5 terminada, auditada y congelada:140/140 muestras**, fuente5119e330,
banco1.0.0 y GLM5.2/DeepInfraFP4 sin cambios durante las cinco rondas.
139operaciones completed/1failed técnico010r3;140snapshots verificados.
Revisión local:138conformes/1fallida de calidad012r5/1técnica; ningún juicio
pendiente entre las respuestas completadas. Banco original542PASS/3no evaluables
por el fallo técnico; calidad276PASS/2FAIL de una respuesta/2no evaluables.
No140éxitos ni aceptación independiente.012r5 repite la preferencia normativa
no sustentada de owner: clasificación allocated correcta; dos checks, un grupo.
023r5pasa pidiendo datos autorizados, sin pedir conexión; la duda023r3deN3 persiste.

Auditoría `period-api-n5-final-audit-v2.json`, SHA`6981d89bcdf3760cd3680d0a0517f65ce3c5b9760ed6c355119c8e28c0499406`.
Paquete final `period-n5-full140-frozen-v1/`,310archivos, manifest
SHA`db463ef190e19bc063784f0ef44ecaee329f9bb99b0b2a0f04ece9d4327f3bdd`. Paquete parcial112/250archivos
conservado íntegro, no sustituido. Los112recibos y1247filas iniciales permanecen
byte a byte; ledger final1275filas SHA`0e861c496853a687f9053f2d0a212829cfd25a53752e4889cff0c6059f9751b9`.

El usuario autorizó30USD acumulados el16/10 («Ampliar a30»). Quinta ronda sólo
desde001r5:28completed,27conformes/1fallida012r5, cero técnicos nuevos y
0.110671422USD observados. N5 total137costes observados:0.622073267USD
(totales redondeados a9decimales; auditoría conserva los originales).
Tres máximos desconocidos propios íntegros; reservas pendientes de todo el
historial12.69071250USD, sin liberar ninguna. Cota final conservadora
19.893051732/30USD, no factura ni coste exacto atribuible al trabajo.

Controlador803686/start73577006 **terminado** con COLLECTED; no relanzar.
Política externa `period-n5-resume-prepared-v4.json`, SHA de política
fda1c54dbac9914a737a8670688b30506e433088420ed50cff8891f1f574611f;
fuente/plan/modelo/prompts intactos y admisión fresca por operación. Claves
existentes processor4.5USD/backend0.1USD hasta16/10a18:00París, sin renovación,
nuevas claves, reinicios o cambios de límites en esta continuación.

Comparación emparejada N3/N5:487PASS→PASS,2FAIL→PASS,1incierto→PASS;
324PASS→PASS originales. Mismo candidato: variación, no mejora causal.
56muestras r4/r5 sin par, incluida012r5fallida; los pares no la borran ni
borran012r1fallida/023r3dudosa deN3. No juezLLMcalibrado/testciego ni
adjudicación independiente. Pendientes012, criterios con revisores y corpus
integrado nuevo. B no aceptada/publicada, Trello noDone.

**Modelo elegido para continuar: GLM 5.2 / DeepInfra FP4**, temperatura 0 y
reasoning desactivado, ZDR y sin fallback. No es aceptación de la versión medida.
La comparación congelada terminó: GLM **82 conformes provisionales y 2 fallidas**;
DeepSeek **77 conformes, 6 fallidas y 1 dudosa**. GLM tiene una regresión obligatoria
en 014r2 y un defecto adicional de soporte en 002r3; no se compensan con la media.
DeepSeek es más rápido y barato: 0.176012028 USD frente a 0.3470654625 USD;
p50 de generación 5.54 s frente a 11.66 s. Se priorizan menos defectos medidos y
conservar la ruta ya configurada en B. No se aísla el efecto del proveedor ni se
declara superioridad estadística con N3. Juicio local, sin adjudicación independiente.

Evidencia final inmutable: `matched-model-comparison-final-v1.json`,
`model-selection-final-v1.{json,md}`. GLM snapshot
`glm-matched-v1-collected/snapshots/snapshot-1792104887937.json`; revisión
`glm-matched-v1-collected/reviews/snapshot-1792104887937-688694c5.json`.
84 respuestas válidas por modelo, 168 fases por modelo con coste observado y
ninguna reserva desconocida nueva en esas dos campañas finales. Sonnet/Sol y
DeepSeek v1/v2 conservan todos sus errores y sus reservas, sin repetirlos.

Cierre comparativo: 1051 filas, 883 anteriores intactas, **11.73085650 USD** de
reservas desconocidas anteriores conservadas; cota **17.8056386105 / 20 USD**,
no factura. Cada inferencia posterior requiere admisión fresca. Las mismas claves
siguen autorizadas hasta el 16/10 a las 18:00 de París; no se han cambiado límites,
contadores, credenciales ni reservas anteriores en este trabajo.

**Candidato local 5119e330d87519ce8afff227e6c5cc248656fa70:** corrige 002/014 con
terminales del servidor para declaraciones completas de comparación mensual y
forecast/acumulado/presupuesto. 258 pruebas locales conformes, incluidas 57 nuevas.
Se conserva el error de colección inicial por un parámetro reservado de pytest;
se corrigió sólo el nombre del parámetro. Banco, prompt y contrato público intactos.
Backend/processor concuerdan en 56 contextos cargados en frío. El contrafactual
frente a 9513 conserva 52 esquemas y cambia sólo 002/014 con y sin RAG; no es una
validación del modelo corregido. `period-regression-v2.xml`,
`period-schema-counterfactual-proof-v1.json`, `period-resource-parity-v1.json`.
Nueva identidad
`jup-035.chat.v3:194f7d2b6419c64662a83c90dffe814cff4164c117daa6a0c936e9ebc34695c8`,
assembler `319757c04e39f35a621ff5ce76065732172a5d11fbf1542911379bce7e569127`,
manifest SHA `e6b713ddd70c2cb4a839c3ecf4d4400560dee74e40ced3bb7ebe77ffcb5ed218`.

Transferencia versionada autorizada, archivo SHA
`c20f988cbd522ebdee7cedca4628c2b372e57e22a202bda122aeea49dc5f9d00`,
sin credenciales locales. Regresión Linux terminada: **356 pruebas nuevas únicas
conformes, cero fallos, errores, omisiones o resultados heredados**. Evidencia
`period-native-final-audit-v1.json` y exportación `period-native-collected/1792106202903/`.
Build terminado y fuentes verificadas; exportación `period-build-collected/1792106278187/`.

Backend y processor propios activados y sanos; fuentes verificadas: 117 archivos
backend, 106 processor y 127 frontend. Imagen backend
`sha256:6a0f8388b3ce7fba19c97b5f41f05f49a3e0fe17f8acd152a9b9f3ce34af2104`;
processor `sha256:e70ed24c44f8470113422dc1d2d16d2fd472df4372a4d3832e90c39b507c2380`.
Frontend y seis servicios auxiliares conservados. Activación sin inferencias ni
cambios de las 1.051 entradas del ledger: `period-activation-result-v1.json` y
remoto `period-5119e330-activation-v1/complete.json`. El processor ya está activo;
la parada por OOM anterior queda como antecedente, no como estado actual.
Descriptor firmado y recursos comprobados: `period-5119e330-live-readiness-v1.json`.

La preparación de la nueva N3 por API detectó antes de inferir una lectura con
codificación predeterminada de Windows en el plan v1. Se conserva ese intento,
sin entradas ni llamadas nuevas. Plan v2 reconstruido desde el banco inmutable
con UTF-8 explícito: SHA `3441119f09c63b3aab5719689f5033294eb3ce968e79f193cc28646712eb4535`.
El arnés externo v2 verifica el prefijo completo de 1.051 entradas históricas y
todas las operaciones adicionales contra SQL y el orden del banco. Las llamadas
directas comparativas siguen contando, con sus reservas. Preflight sin inferencias
conforme, incluidas 12 guardas contables (`period-api-prepared-v2.json`).

**N3 real por API terminada y congelada**, candidato 5119: **84/84 completed**, cero
fallos técnicos, 84 snapshots verificados y 84 costes conciliados. Revisión local:
**82 conformes, 1 fallida (012r1) y 1 dudosa (023r3)**. Los **327 requisitos
originales están conformes**. Rúbrica adicional: **165 conformes, 2 fallos de una
respuesta y 1 incierto**. No es aceptación ni adjudicación independiente.
`period-api-n3-final-audit-v2.json` (SHA
`fe5db9bbb23b034044a8686726325d97ca0116ddf50ce9eb51c1220336f34541`),
revisión `period-api-v2-reviews/review-2dac64f187f84f00ab8dd95480ad5268c6c49f8820c746e4aafcf4797aa6e8e2.json`.
Finalizaron el controlador PID 1760267/start 70572777 y sus 84 conversaciones únicas;
no relanzarlos. Se verificaron fuentes activas, hashes de originales y derivados,
RAG real, paridad pública/historial, operaciones SQL y reportes de cada intento.
La recuperación de RAG tardío usa suplementos SQL con hashes exactos y guarda
los recibos originales: no se presenta como recogida exclusivamente pública.

002 y 014 conformes 3/3. Comparación semántica emparejada con el replay GLM:
3 FAIL→PASS, 2 PASS→FAIL de calidad en 012r1 y 1 PASS→incierto en 023r3;
326 PASS→PASS y 1 FAIL→PASS del banco original, sin regresión original observada.
Métodos de recogida distintos: es descriptiva, no causal ni una baseline API fingida.
`paired-replay-f0cd88662ed9d57e4737dfa77b5f37203a3ac9af0334015d239cfbbb93956709.json`.

012r1 clasifica allocated correctamente, pero confunde la preferencia de owner
por equipo frente a persona con que la clave sea preferente/no exclusiva; dos
fallos de calidad, un grupo causal. 012r2/r3 no repiten esa afirmación. En 023r3
se niega acceso real, pero se pide al usuario una conexión al tenant además de
una fuente: posible insinuación de capacidad o solicitud externa genérica,
pendiente de adjudicar. Los dos cambios de juicio local se conservan explícitos:
`period-012-rubric-discrepancy-v1.json` (requisito original FAIL→PASS por coherencia
con la rúbrica previa; calidad sigue fallando) y `period-023-rubric-discrepancy-v1.json`
(consistencia PASS→incierto al distinguir pedir conexión de pedir una exportación).
No se reetiquetan las campañas anteriores ni se relajan criterios para cerrar.

N3 añadió **0.4066383825 USD observados**, sin reserva desconocida nueva.
Al cierre: **1135 filas**, prefijo original de 1051 intacto y reservas antiguas
**11.73085650 USD** íntegras. Cota **18.212276993/20 USD**, no factura.
Ledger N3 SHA `dba497b32b13188d2b6fc93159589d091ed373e42b39a495c6cd1f3c9dc4af84`.

**Corte histórico112, superado por la N5final140 anterior:** detenido por presupuesto en5119,
cuatro rondas y28 ausentes (001–028r5). **111 conformes y1fallo técnico**;
433 requisitos originales conformes/3no evaluables;222checks de calidad conformes/
2no evaluables. No N5 completa ni aceptación.109costes conciliados suman
0.511401845USD;3 máximos desconocidos íntegros suman0.959856USD. Prefijo1135intacto,
1247filas totales SHA72328e57bd9137af50d803bd4d6692b26f032df14c3470eb6053280acce1188f.

Auditoría `period-api-n5-budget-stop-audit-v1.json`, SHA
30557789c152f64369446950e4376caf72780f965059e8d575c968235220d04f.
Verifica recibos originales/derivados, fuentes, RAG/SQL/historial, costes o máximos,
y rechazo fresco de la siguiente reserva sin despacharla. Cota al cierre
19.683534838USD; siguiente cobertura20.003486838USD >20. Conserva todos los máximos
anteriores11.73085650 y nuevos0.959856:12.69071250USD desconocidos, no factura.
Lectura posterior sin nuevas inferencias:19.741856785USD y siguiente20.061808785USD,
mismo ledger. No atribuir esa variación de cuenta a un consumidor concreto.

Paquete local inmutable `period-n5-budget112-frozen-v1/`,250archivos, manifest SHA
`a34817a826b8c41a1ebc4d518573d7faf002065c225299e616cc25c6cd903d88`.
Congela auditoría,112vistas,111contextos, juicios y pruebas. Algunas vistas conservan
una nota de reserva pendiente al momento de exportarlas; la disposición contable
final está en la auditoría, no en esa nota temprana. Originales remotos intactos.

Comparación con N3: `paired-n3-7bded583c52288f43ab3165080c4485017293951eda11edca62e646e8f8690c3.json`:
487PASS→PASS,2FAIL→PASS y1incierto→PASS;324PASS→PASS originales, técnico aparte,
28muestras adicionales sin par. Mismo candidato: no prueba mejora causal ni borra
012r1fallida/023r3dudosa de N3. No regresiones originales observadas entre respuestas
evaluables; no equivale a evaluar ausencias o aceptar. No juezLLM calibrado ni
adjudicación independiente. Partición histórica ya usada para selección/correcciones,
no generalización ciega. Banco/prompt/producto no cambiaron durante N3/N5.

Retenciones:016r2completed y027r3completed tras intentos incompletos;010r3failed.
Cada operación conserva0.319952USD. Scripts de retención y lanzamiento ya aplicados,
no reejecutarlos. `period-n5-016-full-bound-retained-v1.json`,
`period-n5-failed010-full-bound-retained-v1.json`,
`period-n5-027-full-bound-retained-v1.json`. Controladores original/v1/v2/v3 terminados.
Último PID2645352/start71279410, `resume-v3/complete.json` STOPPED step126/phase2.
**No relanzar ni reenviar las112 muestras.** Próxima001r5, sólo tras autorización
presupuestaria nueva y admisión fresca; prefijo1247 debe quedar congelado.

Diagnóstico `period-n5-transport-diagnostics-v2.json`:010r3HTTP520 en transport;
027r3EOF en envelope antes de recuperarse. No identifican definitivamente el
servicio causante ni prueban razonamiento incorrecto. Para016 no hay diagnóstico
estructural equivalente, no inventar causa. El extractor v1 no encontró eventos
por el envoltorio de logging; v2 lo decodifica sin contenido, URLs o credenciales.

`period-n5-cap21-continuation-proposal-v1.json` es una **propuesta no autorizada ni
activada**, con ensayo puro en memoria:20rechaza la siguiente y21la admitiría,
sin claves, límites efectivos, fuente, prompts o ledger modificados. Consulta al
La consulta histórica de21USD quedó superada por la respuesta humana30USD del16/10.
No utilizar este corte para decidir la siguiente operación.
No garantiza completar28si hay más costes desconocidos. Máximo vigente sigue20.

**Integración local2339 con develop53b43**, GitHub comprobado otra vez el16/10:
checkout `tfm-economicon-jup123-integration`, rama `fix/JUP-123-develop-integration`.
Merge1f1b20e7e6787c5818aaeb187f093fdc508d96d3 conserva B e incorpora JUP-036/JUP-120;
A apps/tools idéntica a8ea5a0c4 ya integrada.36conflictos resueltos por igualdad
contra A; dos ficheros incorporan036 y el índice conserva ambos temas.
`period-develop-local-resolution-proof-v1.json`. En2339cce805ef387a0ea826ec267a1ae79fae7792
no cambian aplicaciones respecto a1f1: herramientas, fixture histórico y docs.

163backend localesPASS y14SQLomitidas al principio; cubiertas en29SQL realesPASS
(14+15de fecha),192identidades backend únicas.18frontendPASS, tipos/build conformes,
lint0errores/1advertencia anterior;95arnésPASS/17evaluadorPASS;75OpenSpec estrictos,
corpus/banco/trazabilidad/higiene conformes. Primeros intentos por permisos/
PYTHONPATH/memoria o procedencia del banco se conservan; sin relajar aserciones.
Banco1.0.1 sólo cambia versión y hashes de fuentes, no28casos/109requisitos.
Pin15afb8db2605288d90a70761c5a8daf6787809aae13726618fcf05d98181e684; se rechaza
un plan antiguo antes de reservar/despachar. El banco1.0.0 auténtico queda como
fixture para los recibos12/10, que no se reetiquetan. Primera ejecución16errores
por procedencia incompatible conservada; después17PASS, no relajación de hash.

SQL `period-integration-sql-final-audit-v2.json` y `period-integration-sql-collected/v2/`:
Cockroach24.1.11/volumen exclusivos,29pruebas únicas y todos los JUnit/hashes
verificados. V1 no arrancó por memoria; v2 serializó con cero operaciones activas,
parada temporal sólo del processor propio y restauración del mismo contenedor/
imagen sano. Otros servicios conservaron ID/imagen/arranque. Sin proveedor ni
despliegues compartidos. No se presenta como nueva suite histórica completa.

Tres builds2339 terminados y verificados **sin activar**, evidencia
`period-integration-build-final-audit-v1.json`, SHA
87039e888654d543e2f995bb789a7cf8562aa6d4f212d2a898633f8277302602.
Backend118/processor106/frontend127 archivos verificados por hash. Imágenes:
backend8af31280ddbcbdb881b4163b96ab1e46cd296f4454019c029097af7a68face29,
processor012901a444335842910fc863f8039c55f3e957052ab4d580825dbde209d335fd,
frontend860140fa2ecc55ea14fe2f401633cd3680871fb22f8b618917fc85286524a78b.
ControllerPID2727323/start71343285 terminó; no relanzar. Parada temporal del
processor propio y restauración sana del mismo contenedor/imagen; su hora de
arranque cambió, los otros servicios no.1247filas idénticas y cero inferencias.
Archivo2339 SHA3b065878c73eb74f9927466121a1ae0fcb24e7cea33c22920c008c596ea71703.

**HTTP/UI de integración2339 comprobados sin modelo**, 16/10/2026.
Previsualización desechable con base `jup123_ui_2339_v1` y cola propias;
backend2339 y frontend de la misma fuente,127archivos verificados, API29757/UI29760.
Ambas fases `CHAT_ENABLED=false/true` pasan por HTTP y navegador. Se verificaron
133.33EUR y9.75USD separados, fechas/corte10/10, exclusión de un registro sin fecha,
ausencia de datos futuros/de otro cliente,2días observados, desglose e historial
tras recarga, rechazo de fechas invertidas antes de POST y presentación a1280/390px
sin desbordamiento horizontal del documento. Panel B abre/cierra con el flag activo;
no aparece desactivado. Sin errores de navegador ni solicitudes generativas.
No se sometió una generación: no hay claves de modelo ni transporte privado;
no acredita respuestas del nuevo corpus, streaming vivo o aceptación.

`integration-ui-final-audit-v1.json`, SHA`6b6d98a50c49c5ecaf429f9222ec09891be5a2d1727d54d9e69cf09aa165042d`,
y `integration-ui-collected-v1/` conservan prueba y controlador ejecutado.
Arnés v1/v2 falló por sincronización/selector; v3 pasa sin cambios de producto.
La etiqueta sintética del operador HTTP sufrió decodificación Windows; no se
presenta como prueba de entrada UTF-8. Las fuentes de las imágenes se verificaron
independientemente. Base/cola/contenedores de preview retirados; túnel propio cerrado.
Processor anterior restaurado sano con mismo contenedor/imagen; otros servicios
intactos.1247filas del ledger con el mismo SHA; cero inferencias/gasto nuevo.
No activación permanente ni modificación de despliegues compartidos.

**Impacto del corpus comprobado offline**, sin búsqueda ni modelo:
`integration-corpus-impact-v1.json` (SHA`43f60ff5b4905e39d30f730873e98bbb3de5bb08c946e428013b34ad9f7dd191`) y su tabla `.md`.
Los111contextos N5 completados se verificaron contra el manifest inmutable;
1018apariciones de fragmentos reproducen exactamente la fuente histórica con el
chunker real500/50. En el corpus integrado914conservan texto/índice,100ya no
conservan el texto completo y4conservan texto pero cambian frontera. Afectan a
10casos: 003, 006, 007, 013, 014, 016, 017, 018, 023, 028. Los18restantes conservan los fragmentos observados,
no una búsqueda nueva: no se demuestra ranking, metadatos, prompt o generación
equivalentes. No se reasignan ni se invalidan los recibos históricos por esta
comparación. Los28casos/109requisitos siguen idénticos; el banco no añade cobertura
de los nuevos estados, impacto acumulado o navegación de anomalías. Esto precisa
el alcance pendiente, sin crear un criterio nuevo o atribuir aceptación ajena a B.

**Campaña del nuevo corpus aún no ejecutada.** Plan
`integration-2339cce8-n3-plan-v1.json` NOT_RUN84preparadas, no ejecutadas.
Main jup035-local conserva5119/banco1.0.0 para posible continuación: no moverlo
al corpus nuevo haciendo que sus revisiones lean otra procedencia.
El candidato integrado está en
[`JUP-123-local-review.md`](../validation/JUP-123-local-review.md).
B no publicada/aceptada, Trello noDone; criterios, adjudicación y confirmaciónN5
siguen pendientes. ColectorPR131 independiente; no trasladar reviews/CI de A o
del colector a B ni afirmar CI nueva verde. No Discord enviado.

Para cubrir N5 se amplió **sólo el máximo de la misma clave processor de 3.5 a
4.5 USD**, después del cierre N3 y de comprobar margen bajo los 20 USD acumulados.
`period-existing-key-budget-extension-v1.json`: material, modelos, expiración,
contadores, 1135 filas y reservas idénticos; no nuevas claves, compras ni reinicios.
Backend conserva máximo 0.1 USD. Vigencia de ambas: **16/10 a las 18:00 de París**,
sin renovación automática. N5 pasó 12 guardas contables y preflight sin inferencias
antes de su lanzamiento; su prefijo completo de 1135 filas es inmutable.

**Navegador conforme** en 002/014, escritorio/móvil/recarga y texto exacto de esta
campaña, cero escrituras del asistente y errores del navegador; capturas inspeccionadas,
`period-5119-r1-ui-v1-result.json`. **9 lecturas SSE terminales conformes** de
002/014/017 con UTF-8 estricto en bloques de 1/7/4096 bytes,
`period-terminal-sse-proof-v2.json`. Arnes v1 esperaba snapshot al reconectar una
operación terminada, cuyo contrato es started/final: error conservado, expectativa
corregida sólo en el arnés. **SSE vivo real observado** en 019r3 por GET a una
operación ya prevista: active→snapshot→delta→final→resultado exacto, secuencia,
revisión y offsets UTF-16 correctos; `period-live-sse-proof-v2.json`. No creó ni
reanudó inferencias y no acredita render incremental del navegador ni TTFT del
proveedor. El observador v1 agotó la espera de una operación posterior sin capturar
ni generar; el v2 admitió observar la operación actual activa.

Regla de trabajo: `period-validation-stopping-rule-v1.json`; terminar la medición
congelada y separar requisitos originales de calidad adicional. No exigir perfección
inventada ni abrir otro parche por una sola observación. La partición histórica se
conserva para trazabilidad, pero sus familias ya son conocidas y se han usado en
selección/correcciones: no son un test ciego de generalización. Banco, prompt y
producto no han cambiado durante N3/N5. B sigue local, sin publicar ni cerrar Trello.
Pendientes: completar/congelar N5 y sus costes, perfilar fallos/dudas sin ocultarlos,
informe y candidato local para revisión, acuerdo de criterios y adjudicación humana.

Corte N5 `2026-10-16T00:24:16.656977+00:00`: 9/140 completadas, 9 costes observados,
1145 filas con las 1135 anteriores intactas. Cota 18.57397328800000000000/20 USD,
incluye la llamada actual reservada; las reservas antiguas siguen íntegras.

**Colector PR131**, independiente: af8388d0 publicado con bloqueo del formato
legado cuando falta distancia. 33 pruebas, contrafactual del scorer y 87 fixtures /
521 GET conformes. CI backend falla6 pruebas de salud del árbol base sin cambios:
headers creados al recolectar caducan a los5min. Mecanismo confirmado con reloj
sintético; no hay tiempos JWT completos del log ni una reejecución que lo oculte.
`pr131-ci-auth-diagnosis-v1.json`; CHANGES_REQUESTED y validación humana pendientes.
No se han enviado mensajes Discord. Trello123 conserva lista/roles/fechas.

## Cortes previos del 16/10 — superados por el estado anterior


Avance del 16/10, corte GLM47: **46 conformes provisionales y 1 fallida**,
014r2. Falla una parte del requisito compuesto (omisión del gasto acumulado actual)
y añade política documental de alertas sin soporte visible. Se conservan respuesta,
etiquetas y dos defectos por esa única muestra. No afirmar 47PASS ni ganador.
Revisión `glm-matched-v1-collected/reviews/snapshot-1792103685609-8e1fe988.json`.

Corrección local sin medir: terminal forecast_budget para declaración completa y
fechada de acumulado/forecast suministrado/budget. 179 pruebas locales conformes,
incluyen 28 nuevas; fuente compartida idéntica en ambos servicios. Paridad fría
56 contextos por servicio, identidad
`jup-035.chat.v3:bc02542a0b8b2afddb70d9aaee007d9544e7b3099677058f36f98da4ec552db4`,
assembler d7251d01b1f52591a5908f5a8a4f54c28108c151be2e7433b9f2eb39dc5a216f,
manifest SHA2ce4cb08ddad64d0bbadc56017a54b0ab44fd893cdf2a09f803e136bebc83bf0.
Prompt, banco y contrato público no cambian. `forecast-regression-v1.xml` y
`forecast-resource-parity-v1.json`; Linux y API/UI nuevos pendientes.
Se canceló únicamente el build9513 aún en espera, antes de crear recursos:
`wire-build-superseded-v1.json`. Su preparación y las 139 pruebas anteriores
siguen conservadas, pero no validan esta lógica nueva. Activador preparado
`activate-wire-candidate-v1.py` queda superado y no se ejecuta sobre9513.
GLM sigue en la imagen congelada original; ninguna muestra se reenvía.

CI PR131/af8388d0: **backend falla 6 pruebas de salud**, no verde global; los demás
checks técnicos actuales pasan y JUP reviews sigue fallando por review pendiente.
Backend idéntico por árbol Git en base53b43bb1, anterior5cae4942 y af8388d0.
Tres headers JWT se crean al recolectar, con5min de vida+5s de margen; las seis
pruebas se ejecutan tras ese plazo. Se confirmó el mecanismo con reloj sintético
a311s; no había JWT completos disponibles para leer tiempos exactos en el log.
No se modifica backend ni se relanza la CI para ocultarlo. Diagnóstico
`pr131-ci-auth-diagnosis-v1.json`, captura `pr131-ci-1792104105972.json`.
La corrección propia del colector mantiene33PASS y el contrafactual del scorer.

Avance 00:30 París: GLM comparable alcanza 39/84 respuestas válidas y conformes
provisionales, sin errores técnicos; 45 aún no ejecutadas en este corte. Cota
17.7024580655/20 USD incluye una fase en curso; reservas anteriores intactas.
Construcción aislada en espera del fin de GLM: PID1261672/start70137538,
`wire-9513-build-v1`, sin activar servicios ni inferencias. No elegir ganador
antes de cerrar las repeticiones y contrastar los resultados.

En paralelo se detectó una review nueva del colector PR131. Se leyeron revisión
de Víctor, comentario de Paris y ausencia de inline; corrección publicada en
af8388d0a87cf08184472c84f79247e7974c961b, rama independiente del colector.
Corpus sin distancia bloquea el scorer legado de JUP-071 sin perder evidencia.
33 pruebas conformes; contrafactual con evaluador original: fail→blocked sin
distancia, pass con distancia real. 87 fixtures/521 GET repetidos, sin gasto.
Guía, OpenSpec y separación de números/palabras corregidos. Fuente y continuidad
propias en `../tfm-economicon-jup123-collector`; pruebas externas
`collector-pr131-scorer-fixtures-v1/proof.json`. CI nueva aún en curso y
CHANGES_REQUESTED sigue vigente; no se publica B ni mensajes Discord.
Trello123 actualizado por el puente autorizado, sin modificar lista/roles/fechas:
`jup123-model-progress-updated-v1.json`, descripción SHA
939cb99ce7a7add38fdabc6316f557cd02768ed46e12a247da7b2c9ad818611e.

Autorización vigente: elegir el mejor modelo de los probados, añadir DeepSeek y
terminar JUP-123 en local. Máximo acumulado **20 USD**, sin liberar ninguna
reserva anterior ni reiniciar contadores. Mismas claves hasta 16/10 a las 18:00
de París. No publicar B ni mensajes de Discord. Criterios y reviews humanas
siguen pendientes; la selección técnica no los sustituye.

**DeepSeek v3 terminado:** 84/84 respuestas técnicamente válidas, 0 errores.
Revisión local provisional: **77 conformes, 6 fallidas y 1 dudosa**; 327/327
requisitos del banco original conformes, rúbrica adicional 160 conformes,
7 fallidos y 1 incierto, agrupados en 6 fallos causales. No es aceptación ni
validación API/UI. 002r1/r2 y 014r1/r2 añaden metodología/políticas sin soporte
visible; 012r3 aplica al costcenter un catálogo que la fuente exige a environment;
024r1 niega agosto de 2026 aportado; 023r1 mantiene duda de alcance real/simulado.
Evidencia inmutable: `deepseek-v3-collected/final/report-v1.{json,md}`. Su snapshot
SHA es abb6f33b1b326c5cd7a5c2153813839a1c51d5d3064d1772782e6a1b31b44779.
Coste comunicado de esta campaña 0.176012028 USD, 168 fases con coste observado,
0 reservas desconocidas nuevas. Las 715 filas previas siguen intactas; 883 filas
totales. Cota conservadora al cierre **17.458573148 / 20 USD**, incluyendo
**11.73085650 USD** de reservas anteriores desconocidas íntegras. No es factura.

**Regresión incremental del esquema terminada:** 139 identidades únicas
conformes, 104 processor y 35 backend, 0 fallos/errores/omisiones. Producto
b76b6fd980242518e5b520d09a81e4a42cc35194; HEAD 9513e930 corrige únicamente la
expectativa de una prueba para usar el esquema wire nuevo. No modifica código
de producto. Pruebas heredadas verificadas por identidad y SHA de JUnit: 122;
17 restantes en contenedores fríos individuales v5. Auditoría local independiente
`wire-native-final-audit-v1.json` confirma unión exacta de las 139 identidades.
No se afirma una nueva ejecución de las 1793 pruebas históricas del chat.
Se conservan los intentos fallidos: dependencia nativa sobre /tmp noexec en v2,
una expectativa antigua de esquema en v3 y un lote v4 terminado sin JUnit
(causa no confirmada). La reparación del arnés usa /testdeps exec aislado y
contenedores individuales con red deshabilitada; no debilita aserciones.

**GLM comparable en curso:** z-ai/glm-5.2, DeepInfra FP4, temperature 0 y reasoning
desactivado, mismo contexto/prompt/corpus y esquema wire que DeepSeek. 56 capturas
offline verificadas antes de lanzar; no cambia producto activo. Directorio remoto
`/home/danteadmin/economicon-jup123-20261014/glm52-deepinfra-matched-wire-v1`,
PID 1231753/start 70111630, plan SHA
61417a5ef30c22ca6893ae6f1dc84683295509488cb7dd330b51e7fb72b89965.
Baseline 883 filas/SHA ea71842b9ab47b861a58324d077349dd14fde5439c0d646436528ba1355bbd9a.
Se observa mediante `glm-matched-operator-v1.py observe/export`, nunca relanzar
ni reenviar muestras. Recogida prevista 84; cada fase verifica precio, caducidad
y admisión con todo el ledger. No hay ganador todavía.

Processor B sigue parado por el OOM propio ya documentado; restantes servicios
propios activos. Mantenerlo parado durante GLM porque la guarda exige su estado
congelado. Tras terminar, verificar nuevamente SQL/colas y recuperar sólo el
entorno B; después construir/activar el candidato y validar API/UI reales.
El alias compartido economicon-chat sigue siendo GLM; el alias DeepSeek ya
existente es V4 Pro, **no Flash 4.1 probado**. No sustituirlos sin equivalencia.

Próximos pasos: completar y revisar GLM; comparar requisitos/repeticiones con
DeepSeek; seleccionar configuración elegible; corregir los defectos medidos y
validar el candidato local completo dentro del presupuesto. N5 obligatoria,
adjudicación independiente y criterios/reviews mantienen su estado pendiente.

## Cortes históricos del 15/10 — superados por el estado anterior

## Estado actual y autorización — 15/10/2026

### Autonomía para seleccionar modelo y terminar B — corte21:02UTC

Último corte21:42UTC:DeepSeekv3 alcanza64/84respuestas técnicamente válidas,
0errores técnicos; NO64PASSsemánticos. Al corte revisado52:41PASSprovisionales,
3FAIL(002/014mezclan política documental en prosa sin soportevisible;
024niega el períodoagosto2026aportado) y8pendientes(incluye023con duda sobre
promesa condicionada de analizar datos reales). Los cálculos de002/014soncorrectos;
no se inventa que el contenido de la metodología sea falso. RevisorCodexlocal,
no adjudicación independiente. `deepseek-v3-collected/reviews/snapshot-1792100297177-9b23f0b4.json`.
Herramienta `review-model-replay-v1.py` verifica respuesta contra fase original,
requestSHA,entrada yRAGreal;hereda juicios sólo por identidad exacta de respuesta
completa ycontexto. Juiciosmanuales anteriores congelados en judgment-history/.

Integración local b76b6fd980242518e5b520d09a81e4a42cc35194:gateway y ambos dueños
de recursos usan esquema equivalente;metadatos y admisión cuentan el wire real.
Helper backendcopiado deprocessor con hash exigido por manifiesto (deuda de
duplicación general NO resuelta). Utilidad045d0f0f corrige dos interseccionesnull
y equivalencia1/1.0enums:4fallos de prueba conservados y35PASSposteriores;con
paridadstream/final y rechazo de fuente forjada,41PASS. Dependenciajsonschema sólodev.
`wire-resource-parity-v1.json`:56contextos por cada servicio,cargados en frío,
schemas/tokens/reservas/identidad iguales. `wire-campaign-equivalence-v1.json`:
101schemas capturados producen exactamenteel mismo wire conffdfyB76;no afirma
validaciónAPI ni prueba universal. Prompt y contrato público sin cambios.
Nuevaidentidad `jup-035.chat.v3:6ea3ece9c1b35717aea95e652bbc472bd4d3d11e728832468d529b0317733459`,
assembler660b39a78480ce8990b3c225a514db262294cb0a6494c692577c2327fe852c69;
manifiestocanónicoSHA3e67a4e5c54ea863743d661b70940852a2b91375f15e8b2dc9be750847c8458c.
N3actual sigue usando imagen/contexto congeladosd9b y adaptadorffdfenarnés;
no confundir con una N3API del candidatoB76.

RegresiónlocalWindows89PASS/9FAIL sobre98;los9de red local se reproducen
íntegros en commit anterior045d0f0f(`wire-windows-counterfactual-v1.json`).
No se relajan aserciones para Windows. Linux pendiente:supervisor1006467/start69907972,
`/home/danteadmin/economicon-jup123-20261014/wire-b76b6fd9-offline-v2` espera
terminación deDeepSeek antes de iniciar pruebas;no competir por memoria.
Imagenes nativas pytest previas,sourceb76 por gitarchiveSHA
9379e323cd7436b029f4e82db0aa034f314631308dbcbe429b77422cab54ca85,
ruedas de pruebas con hashes,networknone,768MiB y6tests por contenedor+GC.
Primerpreflightv1rechazó por margen RAMsin crearrecursos;v2prepara y espera
dependencia,exige1550MiBaladmitirtests. `observe-wire-linux-v2.py --export`.
No reiniciar processorB durante replay oregresión;recuperación posteriorpendiente.

Contabilidad21:42:845filas,prefijo715intacto,11.73846710USDreservadoincluyefase
encurso,cota17.438660674/20USD;no facturado exacto. Todas las reservas previasíntegras.
Lecturagateway `gateway-model-routing-readonly-v1.json`:economicon-chat=GLM5.2;
alias yaexistenteeconomicon-chat-deepseek=DeepSeekV4Pro(NOFlash4.1probado).
ClaveBprocessor sólo permitechat+embedding,3.5máximo/spend2.85175;sin cambios.
No sustituir modelo por esealias sin prueba ni alterar desplieguecompartido.
Selección final de modelo todavía pendiente de la N3 y sus defectos.

Último avance21:17UTC:v2 también termina4fallos400enfinal;constantes no eran la
única incompatibilidad.715filas,prefijo707intacto,11.73085650USD desconocidos
retenidos,cota17.282561120USD. `deepseek-v2-collected/snapshots/snapshot-1792098845392.json`.
Utilidad ampliada en ffdfdfaf:objetos exactos y eliminación de definiciones
inaccesibles mediante arrays maxItems0 y referencias locales transitivas.
29tests de equivalencia/rechazo PASS; aún NO integrada en gateway/API. V3pruned
en curso PID875058/start69795740;planSHA
cd0707ff3bca45ec741845d467e90dc7689bf4818ec4e55896e56666e1f4e4bb;
baseline715SHA20ce8310809f5224b3993c3e1f75d2f2f978777a9c816fadcc53c238ed0d0f1f.
56capturas offline sinred antes de lanzar,mismas entradas/prompts/modelo/ruta;
conversión equivalente y recuento de contexto convertido sólo en arnés.
No inferir compatibilidad/semántica antes del resultado. Si persiste400,
congelar causa y comprobar otra ruta DSfijaZDR antes de más rediseño especulativo.
`deepseek-operator-v3.py observe/export` observa mismohandle,sin repetición.

Inspección Breadonly21:17:`b-recovery-readonly-1792099050057.json`:572operaciones
completed+24failed,0jobs y0mensajes RabbitMQ. Processor900MiB detenido porOOM;
resto propio activo. Reinicio sólo de ese processor pendiente al terminar replay
y volver a revisar estado; no reiniciarlo mientras guard espera estadofalse.
Documento externo `model-selection-jup123-current.md` conserva criterio de decisión;
datos21:12históricos, complementar con este corte. Seguimiento único actualizado.

Avance21:07UTC:DeepSeekv1 detenido automáticamente tras cuatro fallos técnicos
consecutivos:4borradores200válidos,4finales400«JSON schema contains features not
supported by xgrammar». No respuestas ni elección por calidad. Snapshot
`deepseek-v1-collected/snapshots/snapshot-1792098428621.json`,8fases inmutables;
707filas,699previas intactas;11.68276675USDreservas desconocidas retenidas,
cota17.228956042USD. Versiónv2 en preparación, mismo producto/contextos,
con conversión equivalente de constantes a objetos cerrados. Utilidad local
18e90f79:22pruebas de equivalencia/rechazo PASS con JSONSchema independiente;
no integrada aún en gateway ni activa en API. Dependencia jsonschema sólo de
pruebas; no runtime nuevo. Primera ejecución pytest no llegó a probar por permisos
del temporal global;22PASS usando temporal propio. No afirma compatibilidad
del proveedor por equivalencia offline. No modificar campañas anteriores.

El usuario autoriza elegir entre los modelos probados, añadir DeepSeek después
de esta comparación y continuar hasta terminar JUP. Supera la limitación anterior
de sólo recopilar/no decidir. Permanecen máximo20USD acumulados, todas las
reservas pendientes y mismas claves hasta16/10a18:00París; sin publicaciónB/Discord.

Decisión: cerrar la comparación actual tras la primera ronda completa, por fallos
obligatorios de contrato, conservando margen para DeepSeek y validación del candidato.
Proceso602367 confirmado terminal con56/168:Sonnet28errores;Sol25errores y3respuestas
finales sin adjudicar.112repeticiones NO ejecutadas; no equivale a N3 ni elección
de ganador por calidad. Prueba `model-comparison-first-round-stop-v3.json`.
Exportación `model-comparison-v3-collected/snapshots/snapshot-1792098119928.json`:
85fases inmutables,0activas.699filas,614previas intactas; reservas desconocidas
11.634464USD(4.247848nuevas),coste observado nuevo1.7680265USD. Cota conservadora
17.173804092USD a21:02UTC, NO gasto facturado. Ver `model-comparison-v3-inspection-1792098131476.json`.

DeepSeekV4.1Flash canónico20260910/rutaCoreWeaveFP8 elegido para la siguiente
medición por soporte anunciado de structured_outputs/ZDR y precio0.15/0.65USDporM.
No ganador todavía. Preparación aislada offline en curso;56capturas previstas,
temperature0 y reasoning desactivado (diferencia explícita respecto a defaults
obligatorios de Sonnet/Sol). Producto,esquemas,prompts y contextos sin cambios;
plan nuevo compartiendo ledger completo y reservas, sin repetir intentos previos.
No inferencias DeepSeek confirmadas en este corte. `deepseek-prepare-v1.py` y
`deepseek-catalog-readonly-v1.json` conservan procedimiento y catálogo fechado.
Processor B sigue detenido por OOM propio anterior; recuperación sólo de B pendiente
tras terminar replay y revisar colas. API/UI no revalidadas. Seguimiento único
actualizado a autonomía; criterios de revisores y aceptación siguen pendientes.

### N3 con rutas ZDR autorizadas — en curso desde20:36UTC

El usuario autoriza «Usar esas rutas sólo para N=3» y después «Continua».
Campaña nueva v3:Sonnet5.5 por google-vertex/global,Sol6.1 por azure,alias
max_completion_tokens en Azure con mismos1000/2200. Sólo recopilar,no corregir
producto/esquema ni elegir modelo.112capturas offline completas verifican los
28contextos×2modelos×2fases,0red/credenciales reales,sólo rutas/alias cambian.

Proceso602367/start_ticks69546080 en
`/home/danteadmin/economicon-jup123-20261014/model-comparison-sonnet55-sol61-v3-zdr-routes`.
PlanSHAae59b3a7ac57bd96bfa981ec064859448c9a0635e27a7a507fe1eb01cc1e02c4;
worker73755b1b8191dfd3757c09fab9e69415def8c007ac76c7bb18f19da3081b95c9.
Workers desechables512MiB/CPU1/readonly por fase usan imagen643e42d4,sin tocar
servicios existentes. Precios2/10porM y contabilidad se verifican antes de cada
envío. Baseline614filas SHAc5228fad557448e422395d1d4228965d97845c6f623550ae842e6b2745ae578d;
7.386616USD retenidos iniciales íntegros,todo en MISMO ledger,máximo20USD.

Corte20:40UTC:9/168;Sonnet5errores(4truncados/1inválido),Sol4borradores válidos
pero4HTTP400enfinal por invalid_json_schema del proveedor. Azure rechaza
combinadores en raíz o falta de type en answer;no se cambia el esquema para pasar.
0respuestas finales en ese corte,ninguna conclusión semántica.628filas,reservas
8.031950,cota12.086210592/20incluyendo ejecución en curso. No confundir con gasto
liquidado. Consultar evidencia fresca y observar MISMO controlador,sin relanzar.

Incidente:primer intento offline en processor B provocó OOMKilled137 a20:29:57UTC.
Se corrigió el arnés con aislamiento/memoria limitada y limpieza explícita;112
capturas después completadas en contenedor propio,retirado. El processor B
original sigue detenido;no se reiniciaron servicios. Código/config intactos,
pero NO afirmar despliegue B íntegro o API/UI operativas. N3 es replaygeneración.

Evidencia externa:`model-comparison-results-v3.md`,`model-comparison-offline-routes-v3.json`,
`model-comparison-prepared-v3.json`,`model-comparison-launch-v3.json` y
`model-comparison-v3-collected/`(fases inmutables,snapshots,JSON/CSV estructurales).
Operadoresinspect/export/report/watchv3. Seguimiento actualizado a observarv3
sin duplicar ni reparar resultados. V1/v2 congeladas aparte,16errores conservados.
Sin publicación B/GitHub/Discord,no reanudar GLM/v7 ni liberar reservas.

Consulta del usuario sobre si la inestabilidad procedía del modelo:contraste
histórico confirmado en a545full84,caso027:juicio provisional PASS/FAIL/PASS.
Los tres contextos RAG son iguales,incluido orden/contenido de4chunks:
SHA78545e6f16a6ec6e54c0cc05e74da7851ef2c0a41e1ae86ff8f7f4f717f7eedd.
La respuesta r2 revisada efectivamente etiqueta+200EUR/+20%del gasto total como
variación de coste unitario,aunque concluye−40%correctamente. Es indicio de
variabilidad de generación,no causalidad exclusiva del modelo:los inputs completos
incluyen fechas/contexto de ejecución y no se probó igualdad byteabyte de todo el
request.429del servicio,400de esquema y límites de salida son causas distintas.
No se recomienda ni selecciona modelo. N3 continúa sin cambios;al20:52UTC37/168,
Sonnet19errores,Sol15errores/3respuestas recogidas sin adjudicar,cota15.039416USD.
Exportación posterior39/168:Sonnet20errores,Sol16errores/3respuestas,capturas
inmutables59fases y020Solr1draft en curso. Snapshot1792097570147SHA
02326273025803dbb06157d0963f2e5bb94ecb724dac14fa5f70ac9780f5cb23.
Conservar schema400deGoogle:«Schema type 'const - complex' is not supported»
en015final;no es un fallo de razonamiento. Proceso sigue vivo,usar mismohandle.

### Adaptación del arnés autorizada y ejecutada — corte20:25UTC

El usuario confirma «Adaptar sólo el arnés y ejecutarN=3». Se aplicaron únicamente
las dos omisiones propuestas:temperature y reasoning.enabled;exclude:true y los
defaults de cada modelo permanecen.4capturas offline de draft/final verifican
que no cambió ningún otro parámetro;producto/gateway/prompts/corpus/banco intactos.
Campaña aparte `model-comparison-sonnet55-sol61-v2-defaults`,planSHA
64dd4b26b54f630ae6c69cadb3af1b2745032a6e46f5c9754a855bdf935927b5.

**Nueva recogida:4/84por modelo,8HTTP404antes del draft,0respuestas**;001–004r1.
El error ahora explicita DataPolicy excluyendo anthropic/openai. Detenida ante
rechazo estructural;proceso528616/start_ticks69474003 confirmado terminal.
N3 sigue incompleta:80pendientes/modelo. No se relajan políticas o selecciona
otro proveedor/modelo. Los8errores previos de v1 permanecen aparte e intactos.

Preservadas606filas previas SHAsemántico
e9e8ce38dcf6998c87e3cefae21b6c15601087ea935aca07144f5a31d5d44488 y6.733852retenidos.
8fases nuevas:614filas,total retenido7.386616USD,cota11.221203103/20USD a20:25UTC.
No se ha liberado ninguna reserva ni cambiado claves,contadores o vencimientos.

GET de previewZDR20:26UTC enumera rutas candidatas para los modelos exactos:
Sonnet por google-vertex/global y Sol por azure,2/10USDpor millón. No se han usado
ni se ha probado acceso;Azure anuncia max_completion_tokens como alias de salida.
Propuesta concreta sólo de rutas/alias preparada pero NO aplicada,pendiente de
confirmar por la restricción de no decidir y la autorización previa de dos campos.
No sustituir Sol por Pro,relajar ZDR o incrementar salida para hacer pasar tests.

Evidencia externa en `materiales/07-evidencias/PR121-local-evaluation/`:
`model-comparison-results-v2-defaults.md`,snapshot
`model-comparison-sonnet55-sol61-results-v2-defaults/`,capturas/preparedv2,
`model-comparison-zdr-routes-v1.json` y `model-comparison-zdr-routing-proposal-v1.md`.
No publicación B ni comparación de calidad. No reanudar GLM/v7:su auditor debe
seguir rechazando una historia ampliada hasta reconciliarla íntegra.

### Prueba solicitada de Sonnet5.5 y Sol6.1 — corte20:17UTC

El usuario pide sólo recopilar tests sin modificar producto ni decidir modelo;
confirma28casosN=3,84/modelo. Replay externo con los contextos exactos de9e2,
leídos de canonical_input y contrastados con sus hashes, más el RAG original.
No es API E2E. Se conservan parámetros efectivos del despliegue, incluyendo
temperature0, reasoning desactivado y require_parameters; sólo cambia modelo
y ruta nativa por petición. Sin cambios de producto/gateway/prompt/banco/corpus.

**Resultado:4/84ejecuciones por modelo,0respuestas.** Casos001–004r1:las8devuelven
HTTP404 «No endpoints found that can handle the requested parameters» antes
del draft. Recogida detenida ante rechazo estructural;80pendientes/modelo.
N3 y comparación semántica NO completadas. El error no aísla un parámetro causal;
no se ha quitado temperatura ni adaptado razonamiento para forzar compatibilidad.
Proceso476718/start_ticks69423548 confirmado detenido.

Las598filas previas y6.081088USD retenidos están intactos. Ocho nuevas fases
de replay se registraron en el MISMO ledger:606filas,0.652764USD adicionales
desconocidos retenidos, total6.733852. Sin liberar reservas o asumir404gratuito.
Cota conservadora fresca10.568439103/20USD; no es gasto atribuido liquidado.
Las filas nuevas no son operaciones del backend: el auditor GLM anterior
rechaza esta historia ampliada; no omitirlas para reanudar ni lanzarv7.
Seguimiento16Oct08:00 actualizado para no inferir, reparar ni reanudar GLM
sin instrucciones nuevas. Claves/vencimientos originales permanecen intactos.

Evidencia fuera de Git, raíz del workspace:
`materiales/07-evidencias/PR121-local-evaluation/model-comparison-results-v1.md`
y `model-comparison-sonnet55-sol61-results-v1/`:respuestas HTTP originales,
requests, duraciones, ledger, prueba de preservación/cierre y manifest con hashes.
Sin publicación B/GitHub/Discord ni decisión sobre qué modelo utilizar.

**Contraste posterior20:20UTC,sin inferencias:**el catálogo público declara
razonamiento mandatory:true en ambos modelos;esfuerzo predeterminado highSonnet,
mediumSol. Ninguna de sus rutas anuncia temperature. Las peticiones actuales
envían temperature0/require_parameterstrue/reasoning.enabledfalse:incompatibilidades
concretas según metadata y documentación oficial, sin ensayo por eliminación.
Proceso otra vez confirmado detenido;8ejecuciones históricas intactas.
Evidencias `model-comparison-parameter-audit-v1.json` y
`model-comparison-reasoning-metadata-v1.json`. Propuesta externa
`model-comparison-compatibility-proposal-v1.md` NO aplicada:quitar sólo temperature
y reasoning.enabled del transporte de pruebas,conservar exclude y usar esfuerzos
predeterminados explícitamente distintos. Pendiente aclarar la restricción
del usuario «no hagas modificaciones ni tomes decisiones»;no inferir permiso.
No reiniciar campaña,adaptar producto ni liberar reservas mientras tanto.

### Máximo acumulado ampliado a20USD — autorización posterior del15/10

El usuario indica «Amplia el gasto a20$». Sustituye el máximo10USD sin reiniciar
contabilidad, claves, intentos o campañas, y sin liberar reservas. Herramientas
locales de admisión y planes nuevos actualizadas a20USD:94pruebas offline PASS,
incluida la admisión del siguiente máximo conservando6.081088USD retenidos.
Transferencia/activación completada posteriormente: herramientas8de0aae8 en
`evaluation-tools-8de0aae8`,94pruebas LinuxPASS y admisión20 ensayada sin envío
en `cap20-authorization-applied-v1.json`; cota entonces9.903101435USD. Configuración
separada SHA9cf2d9eb1bab78ab293ee41fb4ca66fda310bf166917935d32c99a5b3c31b9a1.
No se modifica el árbol medido9e2, su plan histórico ni sus imágenes. V7 preparado
pero NO ejecutado: la prueba de modelos posterior sustituye esa reanudación.
El límite monetario efectivo de OpenRouter leído es25USD, con21.198014901USD
disponibles; no se ha cambiado ese límite ni se le atribuye la causa del429.

**Estado verificado tras reanudaciónv6:**51/84recibos:47completed conformes y4
fallos técnicos020r2/021r2/022r2/023r2. Faltan33desde024r2. La última operación,
`245b22f4-6432-4544-94ec-fca4912f9a16`, tuvo cuatro429 en draft sin uso informado.
Su máximo0.319952sigue íntegro:598filas,597anteriores y50recibos previos sin
cambios,45costes observados y6máximos desconocidos. Controladorv6/PID323114,
start_ticks69272802, terminó; ninguna nueva inferencia tras023r2 en este corte.
Los cuatro errores recientes vuelven a ser RateLimitError/openrouter/vendor_rate_limit,
sin campos de presupuesto cumplimentados. El catálogo público devuelve status0
para deepinfra/fp4 y telemetría reciente nula; no acredita que nuestra cuenta
pueda generar ni identifica la causa concreta del rechazo.

**Contabilidad19:52UTC:** cota conservadora9.89489863USD, formada por
máximo(contador3.81381063,histórico0.957927619+settled2.813385973)+6.081088retenidos.
Otro máximo exigiría10.21485063USD: excedía10, cabe bajo la nueva autorización20
si la lectura fresca y las demás guardas lo confirman. No es gasto real liquidado.
Claves mismas, límites0.1/3.5 y vencimiento16/10a18:00París intactos.

Snapshots nuevos, sin reemplazar partial50:
- Remoto `candidate-9e2a49a2-partial51-cap10-v1`:239ficheros, manifestSHA
  `ed1aefb773a15a8daf112804f72967b5a44af9a29ef7b23fd6fa4f88e3405e6e`.
- Local `candidate-9e2a49a2-partial51-review-frozen-v1`:107ficheros, manifestSHA
  `93936e1206ad9925ff71798e4fcaff8f74e19d283731d0aec9144775be0edb7a`.
  Juicio provisional47PASS/4técnicas,278requisitos conformes/24no evaluables,
  comparación parcial271PASS→PASS y1incierto→PASS. Sin aceptación ni N3 completa.
Los sufijos cap10describen el corte congelado anterior a ampliar; no se reescriben.
Evidencia adicional: `b-live-quota-readonly-1792093790.json`,
`b-live-provider-route-1792094186.json`, retención023r2 y contabilidad1792093936.

### Reutilización del colector para JUP-071 — consulta del 15/10/2026

Actualización posterior autorizada: extracción publicada en
[PR131](https://github.com/EconomiconFinOps/tfm-economicon/pull/131), inicialmente
borrador y después abierta por instrucción explícita del usuario, con revisión
solicitada a Lucía (`lmatsan`) y confirmada por GitHub; cabeza5cae4942,
rama independiente `feat/JUP-123-response-collector` desde develop53b43bb1,
commit técnico0bd494ba. Sólo tools/pruebas/guía/OpenSpec/CI, sin aplicaciones,
prompts, bancos o corpus de B.31tests nuevos,110regresión y97gobernanza PASS;
OpenSpec74/74. Evaluador071/81ceafc6 acepta tres exportaciones29casos tras87fixtures
y521GET locales;0POST/0inferencias. No es campaña real ni validación humana.
Guía en `docs/validation/chat-collector.md` de esa rama; continuidad propia
`docs/continuidad/colector-chat.md`. Trello123/071 enlazados por DockerServer,
listas/descripciones intactas. CI/reviews pendientes al publicar; solicitar la
revisión no acredita su emisión. B permanece
en50/84, sin nuevo gasto, proveedor modificado ni reservas liberadas. La lectura
actual de develop confirma A integrada por cf821570/#130, sustituyendo aquí la
suposición histórica de que sólo estaba en una rama. No revalida su despliegue.

Confirmado por lectura local: `tools/chat-eval-collect.py` existe desde
`b6208ea6`; recoge por GET operaciones terminales, resultado/historial/contexto
y evidencia, conserva errores y hashes, sin iniciar inferencia. Sus nueve pruebas
se han ejecutado de nuevo con Python3.12 (`-B -m unittest discover -s tools
-p test_chat_eval_collect.py`):9PASS. No acredita compatibilidad desplegada con A.
El corte de A8ea5a0c4 sí contiene los endpoints y metadata utilizados.

La referencia local `origin/test/JUP-071-robustness` contiene16variantes y13
originales (29casos), herramienta `assistant-robustness.py` y formato de resultados
propio. Esta referencia no es una consulta actual de GitHub. El colector aislado
no fija IDs del banco; el planificador/runner de B sí exige el banco original
de28casos. Por tanto se puede extraer colector, pruebas y guía sin el rediseño
semántico, pero la ejecución de los29casos y su conexión al scorer071 requieren
adaptador y comprobación explícitos. No prometer integración directa de todo B.
El suplemento `chat-eval-retrieval.py` verifica el RAG posterior al contexto
inicial cuando existe snapshot exacto; copiar sólo el colector no lo resuelve.

La consulta inicial de viabilidad no publicó nada; la publicación posterior
autorizada se describe arriba. No se ha enviado el mensaje de Discord citado.
B y la campaña de pago permanecen separadas de la entrega del colector. La
solicitud anterior de aumentar límite del proveedor no ha cambiado su cuota de
capacidad: la API expone límites monetarios con saldo disponible y no se ha
encontrado un ajuste de capacidad para esta cuenta compartida. Fuentes oficiales:
https://openrouter.ai/docs/api_reference/limits y https://openrouter.ai/pricing.
Ampliar el máximo del trabajo a20USD no resuelve por sí solo los429; no se ha
cambiado modelo, proveedor, plan comercial o créditos.

El usuario amplió explícitamente el máximo acumulado a **10 USD** el15/10:
continuar desde009 usando la corrección contable, sin repetir las ocho muestras
anteriores ni liberar reservas pendientes. Sustituye los máximos anteriores;
no reinicia gasto, ledger, intentos ni caducidad. B sigue sin publicar.

### Corte anterior50 — 15/10/2026, 19:16 UTC

**027 y 020 corregidos en producto d9b1aae9, corte versionado 9e2a49a2.**
287 pruebas incrementales Linux PASS/0 FAIL/ERROR/SKIP; módulos compartidos idénticos,
loaders y descriptor HMAC verificados. Replay offline de83contextos anteriores:
sólo020/027 seleccionan las rutas nuevas, seis respuestas. La primera ejecución
real de cada uno es conforme; **aún no hay N3 completa ni aceptación de B**.

La campaña nueva está detenida en **50/84 muestras: 47 conformes, 3 fallos técnicos y 34
pendientes**. Primera ronda 28/28 conforme. Fallos actuales 020r2/021r2/022r2:
cuatro HTTP429 por muestra, sin uso informado. El gateway los clasifica como
`RateLimitError`, proveedor`openrouter`, categoría`vendor_rate_limit`. Los campos
de presupuesto del error estánvacíos: la hipótesis inicial de error de presupuesto
se retiró al comprobar que el buscador había coincidido con nombres estándar
`error_budget_*`. No se conoce plazo de recuperación ni detalle adicional: mensaje
redactado por logging seguro. No afirmar agotamiento de presupuesto o fallo
semántico con esos datos. Tres fallos consecutivos, último después de10min de
descanso; no más inferencia en este corte.

Revisión local: 278 requisitos conformes / 18 no evaluables por fallos técnicos,
0 fallos de contenido agrupados entre las 47 respuestas observadas. Comparación
parcial con a545: 271 PASS→PASS y 1 incierto→PASS; técnicos y muestras ausentes
separados. No prueba ausencia de regresiones en las 34 pendientes. 020 sólo tiene
r1 conforme y r2 técnica; 027 sólo r1 medida. Juicios históricos inciertos de 020 y
fallo 027r2 anterior permanecen intactos. N5/criterios y adjudicación humana pendientes.

**Contabilidad 19:16 UTC:** máximo(contadorOpenRouter3.81381063,
histórico0.957927619+settled2.813385973)+retenido5.761136
=**9.57494663/10USD**. Es cota conservadora, no coste real liquidado de B.
Los4.161376 históricos siguen íntegros; cinco máximos nuevos0.319952 cada uno:
003r1/019r2 completadas con intentos previos desconocidos y020r2/021r2/022r2 fallidas.
No se liberó ninguna reserva ni se trató un429como gratuito. Claves mismas huellas,
límites0.1/3.5USD y contadores conservados; vigencia ampliada24h hasta16/10a18:00París.
Antes de cada continuación se requiere lectura fresca y cubrir otro máximo0.319952;
si la cota aumenta puede no caber otra operación, aunque la llamada media sea barata.
Entre las lecturas de19:08y19:16 el contador superior aumentó mientras las dos
claves de B y el ledger no cambiaron; no atribuir esa diferencia a nueva inferencia
de este trabajo. Recibo`accounting-covered-readonly-1792091796.json`.

**Snapshots inmutables:**
- Remoto`candidate-9e2a49a2-partial50-cap10-v1`:232ficheros, manifestSHA
  `b24168a27441b92475dbb66d34ac8b2dd532ada52caf3610dd865c21c3ef273d`;
  597filas,50recibos originales/derivados y reservas;547filas anteriores intactas.
- Local`candidate-9e2a49a2-partial50-review-frozen-v1`:106ficheros, manifestSHA
  `ef7447202cd63f774f30e5c0807cb8ae67ef70eeb1abbd3b52a2a9b731c97a96`;
  50vistas públicas,47contextos realmente recibidos, juicios y comparación.
- Auditoría confirma252recibos de las tres campañas anteriores íntegros.
  Evidencia en`materiales/07-evidencias/PR121-local-evaluation`, fuera de este repo.

UI de020/027r1 de historial/recarga PASS en1280/390px, texto idéntico a recibos,
0errores/0escrituras del asistente y sin inferencias. Dos capturas inspeccionadas;
no demuestra streaming ni UI de84muestras. Túnel propio cerrado, servicios intactos.
002r2 incluye jerga de implementación innecesaria, observación de presentación
registrada en el juicio; conserva200EUR/25% y no se convierte en regresión de contenido.

**Continuación preparada, no ejecutada:**`resume-9e2a49a2-n3-v6.py`, SHA
`742e216fe09d8dfe523e90cc6cc2700d53896a4777715c4be5d103c77dfe7b94`.
Ensayo de sólo lectura conforme:597filas/50recibos iguales al snapshot, mismas
huellas y runtime. Siguiente023r2, mismo plan; no repetir las50anteriores ni borrar
los tres fallos. Último controladorv5/PID22568/start_ticks68977026 terminó;
v6aún no lanzado. Comprobar estado real antes de actuar, no confiar sólo en este PID.
Ejecutar operadores desde la carpeta de evidencia con
`C:/Users/DanteInferno/AppData/Roaming/uv/python/cpython-3.12-windows-x86_64-none/python.exe`.
No volver a ejecutar un operador que ya creó un recibo; inspeccionar primero su resultado.

Seguimiento único creado en este chat: `retomar-validaci-n-jup-123-b`, ACTIVE,
programado16/10a08:00París. Registro`jup123-followup-20261016-0800.json` en evidencia;
requiere equipo y Codex abiertos. Permite una reanudación guardada, sin gastar si
faltan margen/vigencia y sin encadenar más reanudaciones si reaparecen429/uso
incompleto. No modifica límites ni vence más tarde que la autorización. Sin GitHub
ni Discord; Trello sólo por la integración de DockerServer. El objetivo de B sigue
incompleto por la medición pendiente y los criterios de revisión, no se da por logrado.
Trello actualizado por esa integración, con lectura exacta y lista sin cambios:
descripción SHA`95977c5d31601f080dd294bfda1c8884519933aabb9bc76ceb51fd95f5c0f387`.

Los apartados siguientes conservan la historia necesaria de este corte y de los
candidatos anteriores; sus fechas y resultados no son nuevas comprobaciones.

### Correcciones027/020 y nueva medición — 15/10/2026, 18:10 UTC

**Trabajo posterior autorizado el15/10:** corregir027, revisar020 y medir de nuevo,
con máximo acumulado10USD y sin liberar reservas. Las mismas dos claves se han
ampliado24h desde su vencimiento anterior, hasta16/10a18:00París
(15:59:59.260/.292UTC). Recibo `existing-key-expiry-extension-20261016-1800.json`
en la carpeta de evidencia establecida; claves, límites, contadores y ledger
comprobados intactos al ampliar. Lectura17:54UTC: cota7.912911256/10USD,
incluyendo4.161376USD de máximos retenidos. No equivale a coste real liquidado.

Corrección implementada:027 usa un terminal de comparación gasto/volumen
que calcula cada métrica con su etiqueta;020 añade consejo documental acotado
con riesgo condicional explícito y validación previa, sin actuar ni garantizar
ahorro. Las etiquetas antiguas de020 siguen inciertas; no se reescriben.

Producto `d9b1aae94784eea88927045347e399151b8992d1`, corte de prueba/archivo
`9e2a49a2dab34bb2cb7379590fdcd7b16b5bdc2d` (sólo actualiza fixture y documentación).
Archivo SHAfbcbdf0ae42fb10c1ecc29bbd979cb3d6c76d5b401f8654a218a9a8d4d0ec562;
plan N3 SHA405add52ee1100faf0fd98d570b1bba3d655c0bb276637ae7d2c20b159aadf5e.
287pruebas LinuxPASS,0FAIL/ERROR/SKIP; prueba técnica SHA46e92f871b71be74facbf1807c815c89d9962ec60e47cf006f3935bbdbf838c4.
1793identidades de regresión anteriores conservan su fecha y alcance; las58nativas
no se repiten al no cambiar SQL/producer. Dos imágenes construidas y verificadas
contra369ficheros del plan más tokenizer; frontend y bases intactos.

Activado sólo B;547filas y mismas claves intactas antes/después. Descriptor HMAC
conforme a prompt`jup-035.chat.v3:ce0ec0e17b2c2b8b35e3a9cbd3eafe68e16e6ebf64da6c2f0fe89529208d031e`.
N3 nueva de84muestras iniciada desde001r1, sin sustituir ni repetir muestras de
campañas anteriores. ControladorPID3851790/start_ticks68672404;
`candidate-9e2a49a2-n3-controller-v1.py`, ledger/planes históricos conservados,
retención íntegra de costes desconocidos y máximo10USD. No hay resultados
semánticos nuevos certificados en este corte documental; revisar recibos y coste
antes de continuar una campaña detenida, sin relanzarla desde el principio.

**Actualización18:29UTC:** primera ronda completa28/28 respuestas conformes en
revisión local provisional,020/027 incluidos. Segunda ronda iniciada;29 muestras
recogidas/revisadas al leer sus vistas, sin fallos semánticos ni técnicos aún.
003r1 completó en segundo intento; el primero recibió429sinuso informado.
Máximo íntegro0.319952 retenido como `COST_UNKNOWN_RESERVED`, sin liquidarlo
parcialmente ni repetir la muestra; prueba `candidate-9e2a49a2-retention003r1-v1.json`.
Controladorv1 detenido y reemplazado porv2 desde004r1 después de auditar:PID3876702,
start_ticks68692083. Reservas desconocidas históricas4.161376 más nueva003r1
=4.481328USD; no se ha liberado ninguna. Auditoría confirma547filas y252recibos
históricos intactos. Cota18:29UTC8.573169059/10USD incluye además0.319952 de
operación activa; no es gasto liquidado. Trello actualizado mediante la integración
DockerServer, verificación exacta y lista sin cambios, SHA114f0fe4cfd3157cc020da2aa7b06d6a1319db21f8994b3650d1116e62a8b51a.
Sin nueva aceptación ni adjudicación independiente. Los snapshots completos y
UI del candidato nuevo se preparan al terminar84; no usar el snapshot anterior
como si cubriera esta campaña.

**Actualización18:50UTC:**47respuestas conformes y020r2 fallida técnicamente por
cuatroHTTP429, sin respuesta ni uso informado; no sustituir esa muestra por otra.
019r2 respondió en tercer intento tras dos429. Ambas operaciones se han auditado
y retienen cada una0.319952 íntegros; junto a003r1 son tres máximos nuevos retenidos.
Total desconocido5.121232USD, incluidos4.161376 históricos sin cambiar.
Recibos y reservas previos conservados; retenciones`retention019r2-v1`/`retention020r2-v1`
en la evidencia. Controladorv4 retomado desde021r2:PID4148508/start_ticks68911905,
mismo plan y runtime. No son regresiones semánticas demostradas ni costes cero.

UI de020/027r1 PASS por lectura de historial,1280/390px y recarga, respuesta
normalizada idéntica a sus recibos y0errores/0escrituras del asistente; sin inferencia
de navegador. Dos capturas inspeccionadas. Prueba`9e2a49a2-r1-ui-v5-result.json`;
fallos previos del harness conservados (localizador de login recodificado y espera
de navegación): se ajustó sólo el test, sin cambiar aplicación. Túnel propioPID23624
cerrado tras verificar argumentos; servicios y otros túneles intactos. No implica
streaming ni UI de84muestras. La corrida por API continúa.

Primer corte `d9b1aae9`: archivo SHA1187a68c59d570d2306ca72fbe3ec069630326277ab6faa3f23b0092efa887e8,
plan SHAa2cc929022ccd0dc32ca5a05ec3f0d75ffc33dbba16d92960bbd04ddc18f23b0.
Transferido sin credenciales, sin activar. Build aislado se detuvo con231pruebas
de lógica conformes y fallo de fixture de contrato (503en descriptor): faltaba
incorporar los nuevos campos del contrato esperado en la prueba; no se relaja
la validación. Se conserva JUnit fallido y se prepara un nuevo corte versionado.
Replay offline de83contextos anteriores: rutas nuevas sólo020/027,6respuestas;
no modifica juicios históricos ni cuenta como campaña real.

### Resultado anterior congelado — 15/10/2026, 15:55 UTC

**003, 013, 015 y 025 pasan 3/3** en el candidato actual. La N3 original de28casos
terminó84/84 muestras:83respuestas completadas y1fallida. Revisión local provisional:
**80 conformes,1fallo de coherencia027:r2,2inciertas020:r1/r3 y1fallo técnico022:r1**.
Requisitos:486conformes/1fallido/2inciertos/6no evaluables por fallo técnico.
No es adjudicación independiente ni aceptación de B; N5 y criterios de revisores
siguen pendientes. Sin publicar en GitHub o Discord.

Producto medido `3059694203f5706ec9dd142565726211fb3b1619`, corte de evidencia
`a54582fb99272730b108d68ccd387a96ceb7c1bd`. Hereda las correcciones015/003/013
de producto d2f8a440 / corte72a2f767.025 usa una negativa determinista por capacidad
real del asistente ante órdenes directas acotadas; no generaliza requisitos de
rightsizing ni reconoce identificadores del banco. Fuera de esa gramática se
conserva la ruta general. Archivo versionado SHA
`c07ca5c09a9c3c883dc42cc6224e5c2db4fe969d595888ede239fefa284b99a3`, plan84 SHA
`abd605f60ef99e524e71815899f72fe0d9ce479ce71fc11a4078e9b17f2d64fb`.

**Pendientes confirmados o por adjudicar:**
- 027:r2 concluye correctamente10→6EUR/pedido y40% de reducción, pero etiqueta
 200EUR y20% del gasto total como diferencias del coste unitario. Un solo grupo
 `unit-cost-labels-bound-to-total-spend-expressions`. Comparación contra72:
 476PASS→PASS,3FAIL→PASS,2inciertos→PASS,1PASS→FAIL y2PASS→inciertos; técnicos
 separados. No demuestra causalidad con025. Reparación pendiente: vincular tipo y
 etiqueta de métrica a la expresión/semántica de operandos, con variantes de
 unidades, importes y periodos; no otra regla libre de prompt ni relajar scorer.
- 020:r1/r3 exigen validar y advierten del riesgo genéricamente; adjudicar si eso
 cumple «explicitar riesgo».020:r2 sí concreta deterioro de rendimiento/SLA.
- 022:r1 falló tras cuatroHTTP429, no por contenido. La respuesta posterior022:r2
 no lo borra.023:r1 respondió tras un429 con uso incompleto: su calidad es conforme,
 pero su coste sigue desconocido. Ambas conservan0.319952USD íntegros, sin repetición.

**Contabilidad y preservación:** cota final a15:53UTC
`max(3.514609539,0.957927619+2.5928883455)+4.161376=7.7121919645/10USD`.
El máximo compara contador global con histórico más costes conocidos para cubrir
el retraso del contador. No es gasto exacto atribuido. Todas las reservas previas
se conservan;4.161376USD retenidos, ninguna operación activa/reserva nueva pendiente.
Mismas claves y límites, caducidad autorizada18:00París, sin renovación posterior.
547filas idénticas al snapshot trasUI,463históricas intactas y252recibos derivados
de a545/72/7be verificados. No reiniciar la campaña por ver el estado COLLECTED.

**Pruebas y alcance:**238pruebas incrementales Linux PASS,0FAIL/ERROR/SKIP;
evidencia base1793con herencia explícita, no nueva ejecución monolítica ni repetición
de sus58nativas SQL/pgvector. SQL/producer no cambiaron; la nueva N3 sí verifica
el recorrido real API/worker/almacenamiento. Imágenes/fuentes y descriptorHMAC
verificados, protocolo server-documentation-v4, prompt45aa5103. Activación limitada
al entorno propioB, con bases/frontend/estados conservados. El primer build falló
antes de pytest por permisos del montaje; v2 pasó sin borrar ese fallo. La
reanudaciónv3 se corrigió antes de crear operaciones por referencia de snapshot
inexistente; inspección original conservada. Controladores terminales, no reenvíos.

UI003/013/015/025:r3:1280/390px, historial y recarga PASS, texto igual al recibo,
0errores/0escrituras del asistente y sin inferencias de navegador. Inspeccionadas
capturas013escritorio/025móvil. Túnel propio PID10776 cerrado tras verificar sus
argumentos; no se detuvieron servicios ni otros túneles. No es una nueva prueba
de inferencia o streaming en navegador.

Evidencia en `../materiales/07-evidencias/PR121-local-evaluation/` desde raíz del repo:
- `candidate-a54582fb-n3-complete-cap10-freeze-proof-v1.json`:361ficheros remotos,
 manifest SHA `c349db86edd1c73232f2a60f428f6c331c3b6aa3a529c14c3fe5df0d634f505f`.
- `candidate-a54582fb-complete84-review-frozen-v1/`:173ficheros, manifest SHA
 `d9f13bd004ea9457ce32ca9c842ecbbb8af5f7adfc4ad7dfb82e3ddb75165148`.
- `candidate-a54582fb-adjudication-packet-v1.json`:020:r1/r3,022:r1,027:r2,
 SHA `dcbc55c949dca20f209eb87ee4a48817fc3addba277a8e7ccbd5bab70796ae01`.
- `candidate-a54582fb-technical-export-v1.json`, `a54582fb-ui-result.json`,
 `a54582fb-ui-tunnel-closed.json`, `candidate-a54582fb-post-ui-history-proof-v1.json`
 y `accounting-covered-readonly-1792079598.json`.

Baseline72 preservada:84/84,79PASS/2FAIL025/2inciertas012y025/1técnica009,
003/013/015PASS3/3. Snapshot360ficheros SHA
`0842ab8d49666a4a8dbab3aade1433a845dcef9f08a66cf9af3bbd0fa08561d9` y revisión173
SHA `7d458b67212ff5091e486d175848c12705edafba24f97bd67a05b830ec54cc2c`.
Sus fallos no se reetiquetan por la corrección posterior.

TrelloJUP-123 sigue en curso, descripción actualizada y leída exactamente de vuelta,
SHA `c847ed6b14908696ad6cb88a0c40d1a8ccbb07bf8b87d59beb4a49b6296e0032`.
Siguiente: reparar027 mediante asociación tipada, adjudicar020 y acordar criterios/
N5 antes de aceptar. El objetivoB no está completo. No ampliar vigencia ni gasto
sin autorización aplicable; no liberar reservas para admitir otra campaña.

Los cortes siguientes son **históricos** y están superados por este resultado.

### Candidato corregido d2f8a440 / pruebas72a2f767 — 15/10/2026

**Trabajo reanudado por autorización15/10 a13:38UTC (15:38París).** El usuario
autoriza extender sólo la caducidad hasta18:00París. Aplicado a las mismas claves,
resto de política y contadores idénticos, ledger sin cambios y ninguna reserva
liberada: `existing-key-expiry-extension-20261015-1800.json`. Nueva N3 iniciada,
PID2017796/inicio67045446, controlador SHA
`99163a68ae88071f453accbc08e1007f2cfab91876053c7f8e0b02918d961a6c`;
`candidate-72a2f767-n3-launch-v1.json`. Verificar ese mismo PID/inicio/argv antes
de reanudar; un timeout de observación no autoriza reiniciar ni reenviar muestras.
El guard de lanzamiento verificó379 filas idénticas al snapshot7be y84 recibos
anteriores intactos. Cota inicial6.134754199/10USD; reservas históricas3.201520
retenidas. La reserva de la operación nueva en curso se suma aparte.
Primer corte:8 operaciones completadas,7 recibos reconstruidos/verificados y1
pendiente de reconstrucción/conciliación;7 respuestas/43 requisitos provisionales
conformes, sin aceptación.003:r1 conserva los siete pasos documentales y no exige
campos Anomaly. La comparación completa de las84 muestras sigue pendiente.

Corte posterior:52 recibos revisados,49PASS/1FAIL025:r1/1incertidumbre012:r2/
1fallo técnico009:r2.300 requisitos PASS/2FAIL/1incierto/5no evaluables por fallo
técnico; no aceptación.003/013/015 conformes en sus dos primeras repeticiones.
009:r2 terminó failed tras cuatroHTTP429, con uso incompleto de fases y una sola
fase observada; no es rechazo de aritmética. EntradaSQL y recibo verificados,
máximo0.319952 íntegro retenido, histórico415 filas y todos los importes intactos.
Reservas históricas más ese fallo:3.521472USD; la operación actual añade su propia
cota por separado. Lectura14:08UTC: contador3.085661269+cotas3.521472=
6.607133269/10USD; es un corte anterior, no saldo actual ni gasto exacto del trabajo.
Evidencias: `candidate-72a2f767-failed-009r2-inspection-v1.json` y
`candidate-72a2f767-retention009r2-v1.json`.

Controlador vigentev3 PID2249076/inicio67234545, SHA
`5712568d278c50d9151bcd1c766c2454d2cc5414ce48e636964e92a3a082c885`;
continúa010:r2 sin repetir009. `candidate-72a2f767-n3-launch-v3.json`;
observador `observe-corrected-72-n3-v1.py` selecciona el último handle por versión.
v2 falló antes de despachar por cerrojo padre/hijo, sin inferencias ni nuevas
filas, inspección conservada; v3 espera al cerrojo del padre antes de continuar.
No atribuir ese fallo del operador al producto ni reiniciar por un timeout de lectura.

UI sólo lectura de003/013/015r1 en1280/390px y recarga PASS, mismo texto de los
recibos y sin errores ni escrituras del asistente: `72a2f767-ui-result.json`.
Capturas inspeccionadas; túnel SSH propio cerrado con PID/argumentos verificados,
sin detener servicios/otros túneles: `corrected-72-ui-tunnel-closed.json`.

### Corrección local posterior025 — producto30596942, aún sin medir

Commit `3059694203f5706ec9dd142565726211fb3b1619`: la muestra025:r1 de72 amplía
indebidamente a cualquier cambio de producción los requisitos documentales de
rightsizing. `chat_resource_actions.py` reconoce órdenes directas por gramática
acotada y liga la negativa a la capacidad real de este asistente, sin inferir
prerrequisitos desde el corpus. No es un clasificador universal; preguntas,
negaciones/instrucciones citadas y formas fuera de la gramática conservan su ruta.
El servidor renderiza negativa y siguiente paso revisable, status refused y sin
citas/métricas/ahorros inventados. Sólo025 se selecciona entre los28casos originales.

Pruebas locales:108processor (49nuevas+42correcciones+17recursos),93regresión de
segmentos/decisiones y37backend (31nuevas+6anteriores), total238 ejecuciones PASS.
Recibos `resource-actions-{local,regression,backend}-v1.xml`. Cold-load de ambos
bundles y módulos compartidos idénticos, `resource-actions-cold-load-v2.json`;
el formato previopretty se conserva en prueba v1, mismo contrato/semántica.
Prompt de esa futura versión: jup-035.chat.v3:45aa510331c2b6fac42497b25e61728d6ba745259cd115136119e276e7623932.
OpenSpec estricto conforme. Sin transferir/construir/activar/medir305 todavía;
fuente/plan/runtime72 intactos mientras concluye su N3. Congelar la campaña actual
antes de activar otra versión. No cambiar banco, rúbrica ni etiquetas previas.

La sección siguiente conserva el bloqueo histórico, ya superado; el estado vigente
es la campaña72 en curso y305 sólo local.

Antecedente de bloqueo superado por esa autorización: revalidado15/10 a12:32UTC,
ambas claves seguían caducadas10:02UTC;
no hay extensión aplicada, controlador N3 nuevo ni recibos nuevos. Backend y
processor72 siguen healthy. Mismo bloqueo de vigencia durante tres turnos
consecutivos del objetivo; las pruebas, build, activación y preparación de la
medición ya están terminadas. Se marca el objetivo automático `blocked`, no
completado, hasta una autorización o cambio externo aplicable. No repetir
comprobaciones/campañas sin esa novedad. Evidencias externas
`candidate-72a2f767-validation-gate-1792067546.json` y
`candidate-7be57c05-expired-accounting-diagnostic-1792067528.json`.
Se conservan las evidencias históricas de ese bloqueo; ya no describe el estado
vigente. No sustituir la caducidad autorizada18:00 por otro plazo sin autorización.

Encargo vigente: corregir015/003/013 y volver a validar con máximo10USD,
sin liberar las reservas. Producto congelado
`d2f8a4405a6e782b8753d48f69fbbe58f19cae89`; corte de pruebas/build
`72a2f7672b6858448e93cfb41c047a47c9be402f`, mismos bytes de aplicación
verificados. Sustituye los cortes intermedios6a/ccf, sin borrar sus resultados.

015: recupera la definición completa de budget como sección complementaria,
incluidos seguimiento/alertas y ausencia de apagado por defecto; compila sólo
con cobertura completa del corpus autorizado.003: conserva el método literal
de investigación y pide parámetros de alcance/periodo, sin promover campos
del esquema a prerrequisitos.013: ruta tipada de desviación actual/presupuesto,
operandos exactos, precisión Decimal80, cero explícito y mes compatible.
Diagnóstico seguro de rechazo por campo/índice, sin guardar prosa privada.
No se conoce la frase exacta causante del fallo histórico013:r3.

**Técnica consolidada:1793 identidades únicas PASS,0FAIL/ERROR,0SKIP**:
1082processor/711backend. Se contrasta la colección actual con cada JUnit por
hash; herencia sólo de módulos de prueba idénticos y repetición de los ficheros
modificados. Los58SKIP offline están cubiertos por6pgvector y52CockroachDB
nativos del candidato. No es una ejecución monolítica. Se conservan el fallo
del antiguo fixture de policy, OOM/salidas137 sin JUnit y la colisión125 del
contenedor propio; la aserción de policy ahora exige la nueva cobertura completa,
no se elimina. Bases temporales propias retiradas; las pruebas no reiniciaron el runtime.

Prueba externa `candidate-72a2f767-technical-proof-v1.json`; colector
`audit-corrected-72-technical-v1.py`. Orígenes: `corrections-bdb6f574-v1..v4`,
`corrections-72a2f767-v2` y `native-72a2f767-v1` en DockerServer bajo
`/home/danteadmin/economicon-jup123-20261014`. Evidencias locales en
`../materiales/07-evidencias/PR121-local-evaluation` desde esta raíz de proyecto.

Dos imágenes construidas y365 hashes de fuente más tokenizer verificados antes
de activar: `candidate-72a2f767-built-source-verification-v1.json`. Frontend
reutilizado con fuente idéntica. Archivo versionado SHA
`3f71fc55290299fbaa85ee764f6042bcc79c23c9bcbefed26515db641ecbcd60`;
plan84 SHA `897f7d53616958ddca97e218757ba76c2bbd916d6d5c5da4e92695f7f7131ad8`.

**Activado sólo en B; sin nueva N3**. Activación del corte72 completada el15/10,
con365 hashes de fuente y artefactos generados verificados en ejecución.
`candidate-72a2f767-activation-v1.json` y
`candidate-72a2f767-activation-history-v1.json` acreditan
bases/frontend/estados de operaciones intactos, mismas379 filas y material de
claves idéntico. Bloqueo exclusivo de campaña durante la activación; no inferencias.
El verificador de recursos del backend acepta el descriptor HMAC del processor:
`candidate-72a2f767-live-readiness-v2.json`, protocolo server-documentation-v4,
prompt jup-035.chat.v3:7246753ac88a34ed35efe4c8f3551fe23a11eba42c0559b730c9257f68b5583a.
El comprobador v1 falló por atributos inexistentes en su propio script;
v2 usa verify_descriptor del producto sin modificar la aplicación.

Preparado `launch-corrected-72-n3-v1.py` con adaptador step-v2. Conserva379 filas,
84 recibos anteriores y reservas. La revisión sólo se reutiliza si coinciden
respuesta, citas y hash del contexto autorizado realmente recibido; si cambia
ese contexto, requiere contraste nuevo. No hay aceptación semántica nueva.

Lectura posterior12:29UTC: contador conservador2.933234199 +reservas/seed3.201520 =
6.134754199/10USD; mismas379 filas y contadores. No es gasto exacto atribuible
al trabajo. Sin nuevas inferencias B. Las mismas claves caducaron10:02UTC
(12:02París). Consulta pendiente para ampliar sólo su vigencia hasta18:00París;
no aplicada ni autorizada implícitamente por el nuevo máximo. No crear claves,
resetear contadores ni liberar reservas. Próximo: autorización de vigencia,
nueva N3 y comparación emparejada contra7be. Criterios/adjudicación independientes
siguen pendientes. Sin publicación B, cambios de otros despliegues ni Discord.

Trello JUP-123 actualizado por la integración obligatoria de DockerServer y
leído de vuelta exactamente, sin mover lista: prueba
`jup123-trello-corrected72-active-update.json`, descripción SHA
`61327f4f55d93a40e49e9b431c8cea84171bf4ea330ca4a0d3b5667bd790a4f6`.
El recibo técnico anterior permanece conservado; esta actualización sí refleja
la activación aislada posterior sin inferencia.

### Antecedente6a y preparación inicial — 15/10/2026

Producto final congelado `6a80a16a78aa5e614704e4e4aaf0deed8d00016d`, después
de bdb6f574 y la corrección de precisión. Archivo versionado SHA
`9b148765db0b96a83da6b585b975bd76bcad52713fdd734acae76c717d7c8afb`;
plan N3 de84 muestras SHA
`a0787990167273b6b8a5dcb9f7e7aec1bac7b0679785c7167478889e1c7012de`.
No se altera el corpus, banco, etiquetas anteriores ni snapshot84 de7be.

Se encontró un borde de la ruta nueva: `display` redondeaba operandos pequeños
a seis decimales y un porcentaje muy grande podía exceder la precisión Decimal.
6a conserva exactamente los operandos y calcula la visualización del porcentaje
con precisión80, indicando aproximación cuando corresponda.57 pruebas locales
de correcciones/recursos PASS; el fallo anterior del test usaba13 dígitos donde
la gramática admite12 y se conserva en `corrections-precision-v1.xml`.

Linux bdb: primer lote152PASS; siguiente proceso sin JUnit, salida aún no
clasificada como fallo de producto. Reinicio técnico v2 con casos que cargan
tokenizador separados; no reenvíos al proveedor. Originales y logs privados
preservados. El controlador final6a espera esa regresión, verifica que sólo
cinco archivos cambiaron (aritmética, manifiesto/pin y su prueba), repite sus
ficheros afectados y pgvector y construye las dos imágenes. Frontend se reutiliza
con fuente idéntica comprobada; no se activa ningún candidato intermedio.

Lectura11:18UTC: contador conservador2.933234199 +reservas/seed3.201520 =
6.134754199/10USD.379 filas y contadores de ambas claves sin nuevos consumos B.
No es gasto exacto atribuible al trabajo. Claves caducadas10:02UTC: sólo lectura,
sin inferencias. Se ha consultado ampliar únicamente su caducidad hasta18:00París
(16:00UTC), conservando claves/límites/contadores/ledger; pendiente de respuesta.
Procedimiento `extend-b-existing-key-expiry-1800-prepared.py`, no ejecutado.

Pruebas/build: `corrections-bdb6f574-launch-v2.json`,
`corrections-6a80a16a-launch-v1.json` en la carpeta externa de evidencias.
Sin publicación B ni Discord. Siguiente: concluir técnica/build, activar sólo B
ociosa con rollback y hash de fuentes, comprobar vigencia aplicable y ejecutar
la nueva N3 con cobertura de todas las campañas y reservas históricas.

### Implementación inicial de correcciones — 15/10/2026

Nueva instrucción del usuario: corregir los tres defectos y volver a validar,
manteniendo10USD y todas las reservas. Sin publicación B ni Discord autorizados.
Las mismas claves caducaron10:02UTC; no se amplía su vigencia implícitamente.

015: recuperación exacta de la sección complementaria Conceptos FinOps Basicos,
en el mismo snapshot/tenant/proveedor y sin otro embedding. La respuesta exige
definición completa de budget más política; si falta alguna no simula cobertura.
003: ruta documental conservadora de investigación sin cantidades aportadas ni
evidencia financiera; conserva literalmente el método completo y pide ámbito,
período, moneda, baseline y desglose sin convertir campos del esquema en requisitos.
013: terminal tipado de coste actual final frente a presupuesto con fórmula
explícita, unidades coincidentes y control de autoridad; cero denominador se
declara indefinido. No afirma conocer el texto que rechazó013r3. El rechazo de
clasificación conserva ahora sólo campo/índice permitidos, nunca prosa privada.

Pruebas locales:152 processor focales PASS (v4),17 backend PASS con tres casos
originales contra corpus real y fragmentación de ingesta (v2). Corrida previa
v3:195PASS con ahorros incluidos. Se conservan fallos previos: el fixture de
corpus no recortaba espacios como ingesta y se corrigió; tres fallos de recursos
por manifiesto desactualizado corregidos; nueve pruebas gateway Windows fallaron
en transporte antes de recibir contenido, pendientes de contrastar en Linux.
No atribuir esos fallos al proveedor ni afirmar que la validación real está hecha.
El mensaje inicial sobre fragmentos no prueban un defecto de producción: la
prueba de corpus pasó tras corregir la normalización del fixture.

Faltan regresión Linux/pgvector, build/activación aislada, vigencia aplicable de
las mismas claves y nueva N3 bajo guardas contables. Las84 muestras anteriores
se mantienen inmutables y no cambian de juicio por estas pruebas offline.

### N3 completa anterior, revisión provisional — 15/10/2026

Se completaron **84/84 muestras** del producto `7be57c05`, con el mismo plan y
ledger: 83 operaciones completadas y un fallo técnico conservado. Sin repetir muestras recogidas, cambiar prompt/banco ni
liberar reservas anteriores. Los ocho recibos iniciales y 302 filas históricas
siguen idénticos. El snapshot de 70 permanece inmutable. La ampliación explícita de
las mismas dos claves hasta las 12:02 de París se aplicó sin reset ni claves nuevas.

| Resultado local provisional | Cantidad |
| --- | --- |
| Respuestas conformes | 75 |
| Respuestas con fallo de contenido | 4 |
| Respuestas inciertas | 4 |
| Fallos técnicos conservados | 1 |
| Requisitos conformes/fallidos/inciertos/no evaluables | 480/5/4/6 |

No es aceptación independiente. El 015 omite seguimiento/alertas en 3/3; el 003:r2 eleva
campos conceptuales a prerrequisitos. El 013:r3 termina classification_unverified_prose
sin candidato/campo privado exacto conservado: no inventar la frase causante.
Incertidumbres 003:r3/012:r3/023:r2/025:r3 pendientes de adjudicación. En 025:r3 se
puede extender indebidamente la validación de rightsizing a cualquier cambio.
017/021/027 son conformes 3/3 en este candidato, sin sustituir fallos históricos.
El 020:r3 inserta una cita literal de commitments en rightsizing: selección de pasaje
defectuosa aunque el chunk citado sí soporta afirmaciones reales de la respuesta;
no equivaler conformidad bajo la rúbrica a presentación perfecta.

Comparación por requisito frente a c7: 457 conservan conformidad, 5 pasan de fallo
a conformidad, 12 de incertidumbre a conformidad, 3 de conformidad a fallo,
4 de conformidad a incertidumbre y 2 siguen fallidos. Los tres checks regresivos
se agrupan en dos respuestas: 003:r2 y 015:r3.
El fallo técnico 013:r3 se compara aparte. No se demuestra cero regresiones
obligatorias; B sigue sin aceptar, publicar ni integrar.

Contabilidad a las 09:40 UTC: contador conservador 2,910121466 USD + reservas
y seed 3,201520 USD = **6,111641466 / 10 USD**. No es gasto exacto atribuible
al trabajo. En la campaña hay 80 costes observados y 4 máximos íntegros retenidos.
El ledger conserva sus 379 filas, sin reinicio contable.

Snapshot privado: `candidate-7be57c05-n3-complete-cap10-v1`,
343 archivos, manifest SHA `79d0698702721c450b97c56ccee452aac3daffa92bd2bdafdb5eaf8d769d2415`.
Snapshot público/juicios: `candidate-7be57c05-complete84-review-frozen-v1`,
89 archivos, manifest SHA `27a3f2319f585a78b24d8a94022ba56889df8a7d59fc29264476ecae09b07841`.
Cada vista enlaza por SHA su recibo privado; logs/credenciales no exportados.
Evidencia externa: `candidate-7be57c05-n3-complete-cap10-freeze-proof-v1.json`,
`candidate-7be57c05-complete84-local-review-freeze-proof-v1.json` y
`accounting-final-readonly-1792057232.json` en materiales/07-evidencias/PR121-local-evaluation.

Siguientes pasos: corregir cobertura del 015 con evidencia autorizada que cubra toda
la pregunta; mejorar diagnóstico estructural del 013 antes de atribuir causa o relajar
validación; resolver el 003 y las dudas con adjudicación independiente y acordar criterios
con revisores. Después medir el candidato corregido y N5 según alcance/presupuesto.
La recogida 2.7 queda completa con costes desconocidos retenidos, no liquidados.
No iniciar otra campaña bajo claves caducadas ni renovar vigencia implícitamente.

### Reanudación tras ampliar sólo caducidad — 15/10/2026 09:30 UTC

El usuario autorizó expresamente ampliar las mismas dos claves hasta12:02 París
(10:02UTC). Aplicado09:29UTC: caducidad10:02:19UTC, material de clave idéntico,
contadores sin disminuir y modelos/límites/reset inalterados. Sin claves nuevas,
reinicios ni liberación de reservas. Prueba externa
`existing-key-expiry-extension-20261015.json`.

Lectura previa: contador conservador2.860663886 +reservas3.201520 =6.062183886/10USD.
No representa gasto exacto atribuible al trabajo. Se comprobaron365 filas idénticas
al snapshot70, origen365 hashes y70 recibos idénticos. Controladorv5
PID429838/start_ticks65550532 retoma015r3; ningún recibo anterior se reenvía.
`candidate-7be57c05-n3-launch-v5.json` y
`resume-b-after-approved-expiry-v5.py` documentan la reanudación. El primer intento
de comprobación se detuvo antes de lanzar por exigir liquidación de una reserva
histórica; se corrigió el guard para exigir sólo disposición de las70 muestras
actuales y conservar el ledger histórico íntegro. No fue una petición de modelo.

Esta reanudación terminó a las 09:40 UTC sin cambiar producto/prompt/banco.
El resultado completo figura arriba; los snapshots anteriores se conservan.

### Corte anterior70/84, detenido por caducidad — 15/10/2026 08:04 UTC

Máximo10USD aplicado y comprobado con herramientas5f32ea08/109PASS; producto7be
inmutable. Se continuó desde009r1 hasta014r3:70 recibos públicos verificados,
69 completed/1 failed,66 costes observados y4 máximos íntegros retenidos en esta
campaña.365 filas totales,302 anteriores idénticas; ocho recibos iniciales idénticos
por SHA. Controladorv4 PID4093158/start_ticks65025659 terminado sin admitir015r3.
Las claves originales caducaron08:02:20UTC; no se han creado, renovado ni ampliado claves.
La consulta de ampliar sólo su vigencia hasta10:02UTC sigue pendiente de respuesta.
No se toma el máximo10USD como permiso para cambiar esa vigencia original24h.

Revisión local provisional:63 conformes,3 fallidas,3 inciertas y1 técnica.
400 requisitos conformes,4 fallidos,3 inciertos,6 no evaluables del fallo técnico;
14 muestras ausentes (015–028r3). Los4 checks fallidos son3 grupos por respuesta:
015r1/r2 omiten seguimiento/alertas;003r2 eleva campos conceptuales a prerrequisitos.
Dudas para adjudicación:003r3 exige utilización/rendimiento/SLA para atribuir causa
en general;012r3 puede desplazar el sentido de preferentemente equipo del valor
de owner al uso del tag;023r2 atribuye confirmación a una captura de pantalla aunque
el arnés envía screen_context JSON sin imagen. No convertir incertidumbre en PASS.

013r3 conserva failed/1intento: diagnóstico estructural model_validation,
ValueError,finish stop,invalid_response,classification_unverified_prose.
Ocurrió antes de caducar claves: no atribuirlo a caducidad ni a un HTTP del proveedor.
No se conserva candidato privado exacto ni campo causante; no afirmar qué frase
lo produjo ni declararlo corregido con un caso artificial distinto. Su lookup404
no prueba coste0: máximo0.319952 íntegro, aunque el SDK registra0.0044258775.

014r3 completed tiene SDK completo0.003916005 pero delta de clave0.006045225:
diferencia0.00212922, igual a una fase gateway registrada del013r3. Es una hipótesis
de cargo tardío, no atribución contable exclusiva demostrada. Se retiene también
su máximo0.319952, sin liquidar el coste ambiguo ni liberar el013. Las364 filas
anteriores, todos los importes y70 recibos quedan intactos tras esa transición.
La frase sobre alertas de014 está en el fragmentoFinOps13 realmente recibido,
comprobado por hash del supplement; no se usa corpus ausente para justificarla.

Comparación parcial con c7:385 pass→pass,5 fail→pass,10 uncertain→pass,
2 pass→fail en003r2,3 pass→uncertain y2 fail→fail. Técnicos aparte:013r3 era completed
en c7 y ahora failed. No prueba causalidad ni ausencia de regresiones obligatorias.
001/004/009/010/011 conformes3/3;017 y027 conformes2/2, su r3 sigue pendiente.
007r3 repite diez veces una misma limitación: deuda mecánica de presentación,
no diez errores numéricos. No se cambió código/prompt/banco durante la medición.

Contadores sólo de lectura08:04UTC:2.858366129 del contador conservador global
+3.201520 de reservas/seed =6.059886129/10USD. No es coste exacto atribuible al
trabajo ni admisión con claves caducadas. Diez operaciones históricas con coste
desconocido conservan máximo, más seed0.002. Ninguna reserva pendiente liberada.

Snapshot privado287 ficheros con recibos originales/derivados, costes y ledger:
candidate-7be57c05-partial70-cap10-frozen-v1; manifest
c70c75a6ed9569bafcc8e67f4ba8a6f299431b296d994bebbbfc283f4e638084.
Snapshot local75 ficheros públicos/juicios provisionales:
candidate-7be57c05-partial70-review-frozen-v1; manifest
23a7d14a6a341ea6eeebf84eafcbf7523f740419ecb0635c61d82cad46272e09.
Fuentes de vistas contrastadas por SHA contra los70 recibos congelados; cuerpos
originales privados/logs/credenciales no exportados. No se reescribe el snapshot8.

Evidencias externas:partial70-{cap10,local-review}-freeze-proof-v1.json con prefijo
candidate-7be57c05; expired-accounting-diagnostic-1792051455.json,retention-v4.json,
014r3-accounting-clarification.json y014r3-authorized-evidence-v2.json con el mismo
prefijo. El archivo de aclaración matiza la atribución de la prueba originalv4;
no modifica su hash ni los importes. Reporte en validación/JUP-123-7be57c05-partial-N3.md.

Siguiente paso tras autorización temporal aplicable: ampliar sólo duración de las
mismas dos claves (sin reset,claves nuevas,modelos/budgets nuevos ni servicios),
comprobar contadores/identidades y retomar el mismo plan/ledger desde015r3.
Quedan14 muestras, comparación completa, correcciones medidas, criterios con los
revisores, adjudicación y N5 según alcance. B no aceptada ni publicada.

Procedimiento preparado en la carpeta externa de evidencia:
extend-b-existing-key-expiry-prepared.py (sólo ejecutar tras autorización expresa
de vigencia hasta15/10 10:02UTC; no crea claves ni resetea contadores). Después
crear un nuevo controlador sobre candidate-7be57c05-campaign-cap10-v2.json,
verificando prefijo70/365 filas y claves/contadores vigentes. No repetir la retención
v4 ni launch-v1, que sólo admite una carpeta vacía. freeze-final-b-cap10-n3.py sólo
se usa tras recoger84; el snapshot parcial70 ya existe y no debe reemplazarse.
El túnel UI propio PID16168 está cerrado tras comprobar comando/hora de creación;
otras sesiones SSH y todos los servicios remotos permanecen intactos. Prueba
final-b-ui-cap10-tunnel-closed.json. B sigue disponible para lectura/reanudación.

### Reanudación autorizada desde009 — 15/10/2026 07:12 UTC

Herramientas5f32ea0869aaf1e9ff00d5d0b0faa3fb676c364c: CAP10 y retención
completed con coste desconocido;109 pruebas PASS, log SHA
3ee6e28a23d6972cf492f11f1486abe777fa59dca6797880241ca440749df97d.
Archivo versionado transferido a directorio separado accounting-tools-5f32ea08,
SHA1a413055b970bc93ccb602d87f693bc4c9e20288cd5379863a8f28c6ddb7ae3d.
Producto7be,365 hashes, plan N3 original y adaptadorv7 permanecen inmutables.

Aplicada retain_completed_cost al recibo original008r1: completed sigue completed,
reserva íntegra0.319952 COST_UNKNOWN_RESERVED.303 filas;302 anteriores idénticas;
todos los importes y ocho recibos idénticos por SHA contra snapshot congelado.
Reservas desconocidas previas2.241664 USD sin liberar. Contador vivo07:10UTC
2.548894402; cota antes de0094.790558402/10USD. No es gasto exacto atribuible.

Controladorv2 PID3717406/start_ticks64724227 activo y009r1 OBSERVING comprobado.
Mismo ledger, mismo plan84, prefijo8 reutilizado; quedan76 muestras previstas.
Las repeticiones r2/r3 del plan no son reenvíos de los ocho recibos r1.
Claves actuales caducan08:02UTC, sin renovación automática. Admisión viva y
reserva completa antes de cada operación; detener ante ambigüedad o caducidad.
Pruebas externas candidate-7be57c05-cap10-retention-v2.json,
candidate-7be57c05-n3-launch-v2.json y observación1792048356756.
N3/revisión completa, criterios humanos y adjudicación todavía pendientes.

### Avance de la misma N3 — 15/10/2026 07:35 UTC

Primera ronda28/28 completed/verificadas: revisión local27 conformes y1 fallo
015r1 (omite seguimiento/alertas aunque incorpora investigación y no apagado).
No se rebaja el requisito compuesto. Código inspeccionado: la ruta budget_operation
compila sólo la sección Budgets Y Forecast de rules; completar esa lista no
equivale a cubrir el flujo de seguimiento/alertas que vive en otra sección.
Pendiente combinación de fuentes autorizadas, sin inventar frases ni cambiar el
banco. No se modifica producto7be durante la medición.

Segunda ronda en curso. Corte35 respuestas revisadas:33 conformes,2 fallidas;
205 requisitos conformes y3 fallidos, agrupados en2 respuestas.003r2 eleva los
campos conceptuales de Anomaly a requisitos previos para evaluar/clasificar,
incluyendo root_cause: dos checks del mismo grupo causal, provisional y sujeto
a adjudicación. c7r2 sólo decía contempla campos; no se cambió su etiqueta antigua.
Comparación parcial:195 pass→pass,3 fail→pass,7 uncertain→pass,2 pass→fail,
1 fail→fail. No atribuir causalidad a una repetición ni declarar cero regresiones.

018r1 completó en3 intentos,2 sin informes completos de coste. Controladorv2
se detuvo; diagnóstico1792048830 y retención íntegra0.319952 aplicados por la
misma corrección, con312 filas anteriores/todos importes y18 recibos intactos.
Controladorv3 PID3781874/start_ticks64776436 sigue desde019, mismo plan/ledger.
Reservas desconocidas retenidas2.561616; corte07:32:592.651207265 del contador
+2.561616 retenido +0.319952 activo =5.532775265/10USD conservadores.
No es gasto exacto atribuible.008 y018 no se reenvían ni se liquidan como gratis.

UI visible de009/010/011,016/017/018 y021/022/027/028:paridad de contenido con
recibos,1280/390px y recarga,cero errores/escrituras del asistente e inferencias.
No demuestra streaming de todas las muestras ni perfección de presentación.
Pruebas externas7be57c05-cap10-{first,boundaries,final-r1}-ui-result.json;
capturas inspeccionadas. Prosa repetida/citas residuales siguen siendo deuda.

Sólo se reutiliza un juicio provisional entre repeticiones si coinciden exactamente
pregunta,contexto,respuesta completa,auxiliares y fragmentos citados; SHA semántico
y de ambas vistas registrados en candidate-7be57c05-identical-review-carry.json.
Las otras muestras se revisan expresamente. Vistas anteriores a la recuperación
RAG se preservan en public-view-history antes de actualizar las derivadas;
igualdad de respuesta obligatoria y los ocho originales congelados no cambian.

Claves originales hasta08:02UTC. Procedimiento de ampliar sólo su vigencia
hasta10:02UTC preparado; consulta al usuario pendiente, sin ampliar aún.
No crea claves/counters/servicios ni cambia reservas. N3/aceptación pendientes.

### Corte histórico anterior: superado por la autorización y reanudación anteriores

### Corte vigente: técnico conforme, nueva N3 detenida8/84 — 15/10/2026

Aplicación7be57c05, pruebasfba415f2. Cobertura conjunta1747 chat conforme,
58 omisiones cubiertas con SQL real y216 ejecuciones Cockroach/pgvector conformes;
dos fallos previos y errores de preparación preservados, sin corrida monolítica
sin OOM. Frontend1354 PASS. Buildv7 terminó tres imágenes, hashes internos114/
103/127. B activo saludable con365 hashes/tokenizer comprobados, mismas bases
y operaciones previas. Sin otros despliegues ni publicaciones B.

Campaña PID1337284/start_ticks62376310 TERMINADA por conciliación incompleta
de008r1.8 respuestas completadas/verificadas,7 costes conciliados y1 reserva
íntegra0.319952. El008 necesitó dos intentos automáticos; su primera final terminó
EOF/error500, con UUID local y sin recibo upstream válido (consulta400). No se
reenviaron muestras manualmente ni se interpreta spend0 como gratuidad.
API analítica403, sin clave nueva. Ledger303 filas, ninguna borrada/modificada
por los diagnósticos. No se intentó009 ni se reinicia el controlador.

Última lectura1792025397: contador2.548894402 +reservas anteriores1.921712
+reserva0080.319952 =4.790558402/5USD. Otra cota0.319952 exigiría5.110510402,
por encima del máximo. Contador global no es gasto exacto del trabajo. Se
mantiene todo el importe reservado; ninguna inferencia adicional autorizada
por esa suma. Claves15/10 08:02UTC, sin renovación.

Revisión provisional8/8 conforme,49 requisitos; comparación parcial c7:
47 pass→pass y2 uncertain→pass. No demuestra tasa N3 ni cero regresiones del
conjunto; faltan76 muestras,017/027 en esta versión y adjudicación independiente.
UI Playwright visible001/006/007/008: escritorio/móvil/recarga con paridad, sin
errores ni escrituras del asistente; capturas inspeccionadas, sin gasto de UI.

Snapshot parcial privado31 hashes y ledger consistente en DockerServer:
candidate-7be57c05-partial8-frozen-v1, manifest
beebcd2e2a307de1e3dee1d10ce28f27c3f6a62951a350b57b7ade288b543e25.
Pruebas públicas derivadas y notas ligadas a SHA originales, sin logs/credenciales
exportados. Véase [informe del corte](../validation/JUP-123-7be57c05-partial-N3.md)
y candidate-7be57c05-partial8-freeze-proof-v1.json en la evidencia externa.

Trello reconciliado con este corte por integración DockerServer: lectura exacta,
lista intacta, SHAbce168d1742a0f0131aecfce5389d086a214edde5aaa739f5a87ff4cc63528db;
jup123-trello-completed-retention-update-v1.json (incluye la corrección local posterior). Sin mensajes Discord.

Corrección posterior sólo de herramientas:4d3f953eb56946cd1b3145243def261dc2dac5ac.
Ledger.retain_completed_cost y retained_cost distinguen una respuesta completada
de su consumo desconocido. Conservan0.319952 completos y el estado completed;
no fabrican un fallo ni un coste0. Se exige paridad/hash de recursos públicos;
compatibilidad con terminal_failure previa, identidad de operación/conversación
y rechazo de recibos modificados/coste ya conciliado. Runner y auditor aceptan
el prefijo documentado sin reintentar la respuesta, sujeto a la misma admisión.

109 pruebas de herramientas PASS, completed-retention-tools-v1.json/log SHA
484d429564b94bef51dafecce71db3ea9aaa81cb88cc490131578e57583a663f.
Ensayo offline con proyección permitida de303 filas/5planes:302 filas anteriores
y todos los importes intactos, completed008 con máximo íntegro y novena reserva
rechazada. completed-retention-real-rehearsal-v1.json. No se copió un ledger bruto
ni se escribieron datos del ledger real. Sólo se exportaron campos de control
contable e IDs sintéticos; el hash de filas originales es
b4951c8e3b2757408d05a9f8c3eee9d12c44409140b6b7f77c26bcf4fc67d775.

Herramientas4d3 locales, sin transferir/aplicar al candidato7be ni a la campaña
congelada; su plan365 hashes continúa inmutable. Antes de una eventual continuación
se debe registrar esta revisión de herramientas por separado, sin cambiar a
escondidas los ficheros fijados del plan. Última revalidación remota1792025965:
controlador terminado,8recibos,303 filas, recibo perdido400 y misma cota4.790558402.
Consulta de margen6USD enviada al liderazgo, pendiente; CAP efectivo sigue5USD.
Sin inferencias ni renovaciones. Objetivo no completado.

**Bloqueo confirmado en la revalidación1792026514:** el controlador sigue terminal,
hay8 recibos/303 filas, el recibo perdido sigue sin ID válido y la cota permanece
4.790558402. La nueva reserva exigiría5.110510402, superior a5USD. La corrección
local de herramientas ya está terminada y probada, pero no crea margen ni prueba
el coste del proveedor. No queda un proceso vivo que esperar o trabajo de
validación independiente pendiente de ejecutar con el alcance/presupuesto actual.
El objetivo automático se marca bloqueado por conciliación/margen; B no aceptada.
Para retomarlo hace falta evidencia contable nueva o decisión explícita del
liderazgo sobre el máximo. No tomar el silencio como autorización ni reiniciar.
Pruebas externas: candidate-7be57c05-n3-observation-1792026513503.json,
accounting-final-readonly-1792026514.json y
candidate-7be57c05-008r1-upstream-1792026516.json.

Siguiente paso: recuperar evidencia de coste o decisión explícita de margen,
conservar reserva y resolver tratamiento de una operación completada con coste
parcial antes de continuar el mismo prefijo desde009. No cambiar producto o
banco durante medición. Pendientes N3/comparación completas, criterios humanos,
adjudicación y N5 según alcance/presupuesto. Objetivo B no completado.

### Última medición semántica real completa: c7 N3 — 14/10/2026 20:37 UTC

#### Evidencia de base anterior a activación y N3 parcial — 15/10/2026

Producto congelado7be57c059ef740ae5f525d98ebe631271144f1fb, archivo versionado
SHA256 efe8c644e4fefb9e17fefaa55e3c5e2275c8195dae06ebe2b7923389ec2444ff.
Los commits posteriores hasta ef2958df son documentación. fba415f2220f5eb8945da75efd0496809e8c0755 cambia sólo dos pruebas; producto sigue idéntico a7be, con equivalencia de archivo y helpers comprobada antes de reutilizar evidencia.

**Regresión offline terminada:**1747 identidades únicas,1689 PASS/58 SKIP,
0 FAIL/ERROR. Las omisiones no cuentan como aprobadas. V5 ejecutó las189 últimas
una por proceso, reutilizando1558 resultados sólo tras comprobar JUnit/log SHA
y todos los bytes versionados. Tres OOM previos conservados (capacity, lote de
ocho context_budget y lote de ocho summary_context); no acredita una ejecución
monolítica sin OOM. Fuente y aserciones intactas, servicios B sin interrupciones.
Prueba pública derivada sólo con IDs/estados/hashes, sin mensajes o logs:
final-regression-7be57c05-public-proof.json, SHA256
6ec8444324f7d2cd1704d3e4eb8bcc802d7980d7f0a3293a21893d593a9b5f0e.
Originales completos permanecen en DockerServer.

**Pgvector terminado:**20 PASS/0 omisiones, fuente7be; incluye6 contratos de
política que cubren6 de los58 SKIP y14 pruebas del contrato existente, no sumarlas
como20 casos adicionales del chat. Recursos propios retirados, runtime B intacto.
final-pgvector-7be57c05-public-proof.json, SHA256
48e2fdc47392779000c84808d94a367a599136d5f4284a70f08bb72ada424a54.
En ese corte quedaban52 identidades del chat por comprobar con Cockroach y las141 omisiones
nativas del barrido de anomalías (distintas de la colección chat1747).

**SQL nativo original terminado:**v5 recogió196 ejecuciones,194 PASS/2 FAIL,
0 ERROR/SKIP. No es aceptación. Fallos conservados: anomalía de extremo a extremo
en línea118 por el conjunto de metadatos antiguo (faltaba generation); processor
deadline en línea58, al no observar la consulta activa antes de vencer0.35s.
El primero no alcanzó las aserciones numéricas; el segundo no prueba por sí solo
un defecto de cancelación. Buildv5 se detuvo antes de construir por esos fallos.
Corte final-validation-observation-1792023277417.json.

Corrección de pruebas fba415f2: exigir también generation.question_message_id;
permitir1s para preparar/observar la consulta, manteniendo cierre físico, SQLSTATE,
duración<3s y el ensayo separado de fallback real0.35s, y añadir HTTP504/código
summary_deadline. Sin cambios de aplicación. Archivo versionado SHA256
d34f355d2e2de156e9dc2e07b238beeb7d835a989b391d0358dc2887025301b9.
Repetición completa de ambos ficheros:17 nativas y8 offline, no sólo los dos fallos.
V6 no inició recursos por RAM insuficiente; v7 llegó al contenedor, sin JUnit por
permiso700 de la raíz de la copia pública. Sólo esa raíz se hizo755; usuario10001
y montaje de sólo lectura conservados. No son fallos nuevos de producto.
V8 pasó9 anomalías, pero las8 processor no ejecutaron por tokenizer generado
ausente; comprobado con frames de preparación en línea130. Se repuso el artifact
público ya aprobado desde7be, con SHA/bytes exactos, sin descarga ni añadirlo a Git.
V9 terminó:17 nativas PASS/0 SKIP/FAIL/ERROR y8 offline (2 PASS/6 SKIP), mismos
ficheros completos. DB y volumen propios retirados, B5 servicios con mismos IDs/
inicios, sin inferencias. final-native-sql-launch-v9.json y
final-validation-observation-1792024518361.json.

**Cobertura técnica conjunta conforme:** prueba pública
final-7be57c05-testfix-fba415f2-technical-proof.json, SHA256
36903ccf52f9469f4ea065d2ff2fadd81e62559815b392e8dac55a41d9c2f4b9.
1747 identidades chat conformes al combinar offline y todos sus58 SKIP probados
nativamente;196 ejecuciones Cockroach y20 pgvector conformes (216 ejecuciones,
no216 casos nuevos del chat). Se sustituyen exactamente17 identidades nativas y8
offline de ambos ficheros modificados. Resto de bytes de código/build y AST de
helpers importados iguales; todos los JUnit/log SHA revalidados. Dos fallos
originales y errores de preparación quedan preservados; no es selección de
mejores respuestas del modelo ni ejecución monolítica sin OOM. Revisiones
producto7be/pruebasfba explícitas. No aceptación semántica.

La cadena anterior se conserva: SQLv1 no llegó al preflight tras el OOM de
regresión; v2 se detuvo sin crear recursos por margen de RAM insuficiente; v3
se paró en readiness. Diagnósticos propios, vacíos y sin credenciales:
servidor384MiB solo arrancó, pero el CLI Go ejecutado dentro del mismo cgroup
reprodujo exit137/OOM. V4 sustituyó ese control por Python externo y llegó a pytest, pero agotó1200s
en la preparación: job de cambio de esquema con backfill al0% tras1040s, sin
JUnit completo. Se retiraron sus tres recursos y B siguió intacto. V5 conserva
ese intento y aumenta RAM/SQL; terminó con194 conformes y2 fallos de pruebas descritos arriba. La atribución
a un parámetro concreto no está aislada. Ver native-v4-schema-wait-metadata.json
y native-startup-diagnostic-v1.json/v2.json. El ejemplo de SQL128MiB y la relación
con la memoria del nodo se contrastaron en la [documentación v24.1](https://docs.cockroachlabs.com/docs/v24.1/cockroach-start-single-node),
sin convertir esa recomendación en prueba de aceptación. WSL local sin distribuciones;
no se instaló software ni se usó otro servidor.
Los errores de sintaxis de invocaciones locales no ejecutaron comandos.
Los intentos hasta7be conservaron las aserciones. fba modifica únicamente las dos pruebas descritas; B existente y despliegues ajenos siguen intactos.

**Buildv7 finalizado después:**tres imágenes, backend114/processor103/frontend127
hashes internos comprobados. Activación propia posterior saludable,365 hashes y
tokenizer verificados, bases intactas. final-build-launch-v7.json y
candidate-7be57c05-activation-result-v1.json. Los buildsv1–v6 no construyeron.

Lectura contable renovada1792024359: mismos295 registros y cota4.423039035/5USD
con1.921712 retenidos; accounting-final-readonly-1792024359.json. Trello actualizado
por integración DockerServer, SHA08396a1f972c5bd2af49765c195015fd5a06db0cf7d4da21dcc346adb12b8144,
lectura exacta y lista intacta; jup123-trello-testfix-progress-update-v1.json.

**Plan N3 preparado antes de la ejecución parcial descrita arriba:**84 muestras y365 hashes contrastados contra
el archivo exacto7be, incluso pin generado. El generador se ejecutó desde3064a68d
(sólo documentación posterior); no se intercambia un resultado entre commits.
candidate-7be57c05-n3-plan.json, SHA256
1316e2ffaa2cae57b99fd1ce3c282e972692c24a0f059ac671a1e9139957af52.
Compose privado validado, únicamente contextos/imágenes nuevos; parámetros,
puertos, volúmenes, secretos y servicios auxiliares anteriores conservados.
Prueba candidate-7be57c05-compose-preparation-v1.json; su contenido privado
permanece en DockerServer.

Operadorv7 vinculado al build exitoso y a sus tres imágenes reales antes de
leer secretos/gastar. Fixtures rechazan build no terminado e imagen anterior;
aceptan sólo el conjunto correcto hasta el siguiente control simulado.
candidate-7be57c05-final-adapter-safety-v7.json,
candidate-7be57c05-campaign-prepared-v7.json y n3-launch-v1 con el mismo prefijo.
La preparaciónv2 queda histórica y no debe ejecutarse.

Auditoría previa de contabilidad sin escritura:295 filas del ledger/293 operaciones
SQL sintéticas coincidentes, cuatro prefijos históricos completos y quinto plan
nuevo vacío. Seed/admisión413 intactos. Contador conservador2.501327035USD y reserva
desconocida1.921712USD =4.423039035/5USD; ninguna reserva liberada ni reinicio.
Claves vigentes hasta15/10 08:02UTC, sin renovación automática. Es un corte anterior,
no admisión para futuras llamadas ni garantía de acabar84 muestras. Antes de cada
operación se exige precio/contabilidad viva y reserva completa. Ver
accounting-before-7be57c05-readonly.json,
candidate-7be57c05-prepared-coverage-audit-v1.json y
final-evaluation-prior-campaign-index.json. No guardar secretos en esta documentación.

Trello actualizado por la integración oficial, hash previo y lectura exacta, lista
conservada: jup123-trello-offline-native-v4-update-v1.json, descripción SHA256
e01e94412e402389aef77658b402f1e9aafb603c5a659ef75ac9cab6f9bf714b.
No publicaciones B en GitHub ni mensajes Discord. La revisión automática rechazó
la variante que pausaba B y copiar logs sin filtrar; ninguna se ejecutó. Alternativas:
B activo, datos exportados con lista permitida y logs completos privados remotos.
OpenSpec estricto74/74 conforme tras actualizar proposal/design a la base actual;
no se modificaron criterios ni se atribuyeron reviews humanas.

## Antecedentes anteriores a la activación y N3 parcial

A avanzó a8ea5a0c4 sobre develop0543c5ee, que incorpora JUP-038/#128. B integra
ese develop por merge local; resuelve dos conflictos con los bloques ya reconciliados
en A y cinco adaptaciones de pruebas/fixture.39 archivos de aplicación idénticos
por blob a A8ea; módulos semánticos B intactos. Ver [entregas A/B](chat-entregas-a-b.md)
y `reconcile-A8ea-block-identity-v1.json` para el alcance y pruebas de identidad.

550 pruebas backend conformes,141 omitidas por SQL nativo; frontend completo1354
conformes sin omisiones. Tipos, lint y build correctos (avisos conservados). No
trasladar la evidencia propia de A ni el CI anterior. Ambas reviews oficiales
siguen solicitando cambios en la última consulta. Antes de inferencia queda
completar Cockroach, construir los tres servicios B y comprobar procedencia/tokenizer.
Runtime B aún c7,0 operaciones activas confirmado por SQL, sin llamadas nuevas.
Máximo5USD y reservas históricas intactos; falta admisión viva para cualquier gasto.

#### Calificadores004 y premisas022 — producto local2c79b32d, 15/10/2026

`chat_documentary_decisions.py` conserva definiciones completas de actual/amortized
cost, hasta la siguiente definición e incluyendo frases limitantes. No sustituye
«se aproxima»/«suele» por conclusiones categóricas ni promete reparto equitativo.
El consejo sobre commitments exige la sección completa, con definición, verificaciones
de rightsizing y consejo literal. Una excepción nueva o una gramática de política
no interpretada impide compilar sólo las frases favorables. La demanda futura se
conserva estable/inestable/desconocida, separada del estado de rightsizing; una
conjunción falsa no hace falsa la premisa desconocida. La respuesta aplica consejo
condicional, muestra las citas y pide datos sin inventar descuentos/plazos/ahorros.
No crea tarjetas con severidad/confianza financieras no evaluadas; otras preguntas
y escenarios conservan la ruta general. No hay autorización ni ejecución de compra.

468 pruebas focales processor y32 backend PASS, incluidas las nuevas con corpus
original y gateway simulado.51 pruebas nuevas Linux PASS sin omisiones/OOM
(49processor/2backend); dos contenedores propios sin red, fuente sólo lectura y
JUnit durable, retirados porID/etiqueta. IDs/imágenes del runtime B sin cambios;
no sumar las51 a las locales. Fallos iniciales del arnés preservados: parámetro
pytest reservado y fixture con espacios en límites de chunks, que correctamente
carecía de rangos. El fixture se normaliza como ingesta y exige rangos no vacíos.

Replay de84recibos sólo selecciona004/022r1/r2/r3; conserva literalidad, modalidad,
premisas y paridad streaming/final/público. No adjudica sus etiquetas históricas
ni prueba al proveedor. Producto2c79b32d62420e0ca0c2603ee87eb853bd85047d;
archivo sin.env transferido a DockerServer/candidate-2c79b32d bajo root B, SHA256
6b2d77021c05e90bf138ee9d95e8f644e24fa5626b0eb6acc2599c1d16ab395c.
Ambos loaders propios aceptan `jup-035.chat.v3:c43f48ad863e03e7227b51591af37ea69a1ee31a10ab352204ee163db5b49007`,
assembler4c5709d4c17b1cdce9538c10704d86865426ab924c90c17898524b560bf0b56a.
Evidencia externa `documentary-decisions-assessment-v1.json`,
`documentary-decisions-linux-2c79b32d/`, `documentary-decisions-replay-v2.json`
y`documentary-decisions-cold-load-v2.json`; cortes anteriores intactos.

Siguiente: congelar el candidato completo para regresión integral/build de los
tres servicios B, comprobar procedencia/tokenizer y medir bajo admisión viva5USD.
No se ha activado ni medido este candidato. Criterios, adjudicación independiente,
navegador yN5 siguen pendientes;3.1/3.2 abiertas. Contabilidad histórica20:37UTC14/10
4.423039035USD con reservas retenidas; no saldo nuevo ni liberación de costes
desconocidos. Claves sin renovar, caducidad15/10 08:02UTC. Sin inferencias nuevas,
publicación GitHub ni mensajes Discord.
Trello actualizado por la integración DockerServer, con lista conservada y lectura
exacta: `jup123-trello-documentary-update-v1.json`, descripción
SHA907b08ac4b1e5579258474b4c66906678651f1dbe42c8e5b562fe4005df9b230.
OpenSpec estricto conforme.

#### Etapas de ahorro021 — producto local1afa3815, 15/10/2026

`chat_savings_realization.py` conserva tres roles explícitos de ahorro y su unidad
común, y calcula la fórmula verificado/identificado×100 aportada en el escenario.
No presume monotonía entre etapas ni suma sus importes. Denominador cero queda
indefinido y redondeo se marca≈; no se recorta un resultado superior a100%. Roles
duplicados/incompletos, ámbitos añadidos, unidades distintas o evidencia financiera
del servidor conservan la ruta general. El resultado es hipotético y no acredita
ahorro real, causalidad ni comparabilidad. El esquema sólo ofrece el terminal ligado
a la entrada, status insuficiente y auxiliares vacíos: no genera ecuaciones libres.

419 pruebas focales processor/30 backend PASS. Incluyen seis recorridos completos
del gateway simulado, lectura1/7/8192bytes, terminal válido con paridad pública y
ecuación libre rechazada con la regla original.47 pruebas Linux PASS sin omisiones
ni OOM (44processor/3backend), en dos contenedores propios sin red y fuente sólo
lectura, retirados porID/etiqueta. Runtime B con mismos IDs/imágenes antes/después;
JUnit/logs durables recogidos con hashes. No sumar esas47 a las pruebas locales.
Primer cortev1 tuvo dos aserciones de texto que esperaban «no» frente a «No»
real: conservado; v2 corrige la prueba, no la lógica de división por cero.

Replay de84recibos sólo selecciona021r1/r2/r3 y entrega80EUR/mes realizado del
ejercicio y40%, con paridad streaming/final/público.021r3 permanece failed en el
histórico, su ecuación privada exacta sigue desconocida y la reserva0.319952USD
no se libera. El replay no es respuesta del proveedor ni aceptación de la campaña.
Producto1afa381548ddeeda5fcdb556974afb546fa54884; archivo versionado transferido
a DockerServer/candidate-1afa3815 bajo root B, SHA256
bb0b21894a51f9b92062fe25e5cd13cab4b2e271dbb1180d4e68b95184e41547.
Recursos de ambos loaders propios: `jup-035.chat.v3:7732ca7948a5d8fcf51e052d0233bd74921ceaa5fb35931ca1d87d1175f77903`,
assembler829c43a4617d08dc02219ecacf3033b3e9cba0c17c4b4e5542378b8f24020d5a.
Pruebas/hash/alcance en evidencia externa `savings-realization-assessment-v1.json`,
`savings-realization-linux-1afa3815/`, `savings-realization-replay-v1.json` y
`savings-realization-cold-load-v1.json`. Sin activación, inferencias ni gasto nuevo.

Siguiente: tratar las incertidumbres004/022 y después construir/verificar el
candidato completo, nueva admisión viva y medir las correcciones. Criterios,
adjudicación, navegador yN5 permanecen pendientes. Última cota4.423039035/5USD es
histórica (20:37UTC14/10); no libera reservas ni acredita saldo actual. Las claves
caducan15/10 08:02UTC y no se renuevan automáticamente.
Trello sincronizado por la integración DockerServer, con lista conservada y lectura
exacta: `jup123-trello-savings-update-v1.json`, descripción
SHAc31f7ea8da51b41c1b74ba88061d48a10a990ebefb16a29eca340a90194e6962.
OpenSpec estricto conforme; ninguna publicación GitHub/Discord.

#### Atributos001 y decisión shared009 — producto localb3528bcf, 15/10/2026

Verificación enUTC14/10 22:00 (fecha local15/10). `chat_cost_breakdown.py` conserva
período, suscripción, moneda y vista declarados en un desglose completo de hasta12
servicios únicos; agrega importes variables, máximos y empates. No verifica cobertura
ni facturación. Créditos se suman con signo y un total no positivo no genera una
participación del gasto. Porcentajes redondeados se marcan≈, también en cobertura011.
`chat_shared_allocation.py` conserva el importe compartido y equipos del escenario
que declara regla aprobada ausente y consumo desconocido. Exige coincidencia de
importe/moneda/activo, pide regla/base/datos y no asigna cargos por defecto. Usa
hechos del usuario: no selecciona pasajes generales para aparentar soporte de una
regla inexistente. Evidencia financiera del servidor impide sustituirla por estas
rutas hipotéticas. Otras formulaciones o datos contradictorios siguen la ruta general.

375 pruebas focales processor y27 backend PASS, con recursos reales cargados por
ambos loaders propios.93 pruebas Linux PASS sin omisiones ni OOM:50 de escenarios,
37 de cobertura y6 de sus contratos backend; no sumarlas a las locales. Cuatro
contenedores propios sin red, fuente sólo lectura, resultados durables recogidos
con hashes, retirados porID/etiqueta. IDs/imágenes del runtime B iguales antes/después.
Replay sobre84recibos sólo selecciona001/009r1/r2/r3, conserva coste actual y devuelve
total1000EUR/60%, o shared con solicitud de regla/base sin cita de tagging ajena.
Streaming/final/público coinciden; juicios históricos no alterados. Es replay de
compilación, no nueva respuesta del modelo ni aceptación semántica.

Producto b3528bcf695238ba8c1a7b8b7e6e10ad06292250; archivo versionado sin.env
transferido a DockerServer/candidate-b3528bcf bajo el root B, SHA256
cdb34464138f86706df34fc5aecfc6797be7587c21da3aae352367b67d9b196b.
Recursos: `jup-035.chat.v3:2bad1b2b07e3022f7c23c23130c8dd5ffe7b0c67b91a49e6974c7b707e19f651`,
assembler8568288010fa348c407e080db4cc1a6810b58862cd6d28cd9b49cd6c23dd505f.
Evidencia externa `scenario-accounts-assessment-v1.json`, `scenario-accounts-linux-b3528bcf/`,
`scenario-accounts-replay-v2.json` y`scenario-accounts-cold-load-v2.json`.
Versionesv1 conservan el corte anterior al formato≈; v2 prueba el producto final.

Sin build/activación, inferencia, gasto nuevo ni publicación. Siguen021 y dudas004/022;
la medición de todas las correcciones, navegador final, criterios, adjudicación yN5
permanecen pendientes. El saldo no se ha releído: cota histórica4.423039035/5USD,
no admisión actual. Antes de inferencia, comprobar contador, reservas y claves;
caducidad prevista15/10 08:02UTC, sin renovación automática.
Trello actualizado por la integración DockerServer, lectura exacta y lista conservada;
`jup123-trello-scenario-accounts-update-v1.json`, descripción
SHA852a0a6c53a72c3322534b9607d4a0a4ed64070433d38a58b705a8e995275030.
OpenSpec estricto conforme; sin mensajes Discord.

#### Cobertura de011 y diagnóstico de021 — producto local654298d4

`chat_weighted_coverage.py` liga los datos de una partición completa de recursos
conformes/no conformes y costes en moneda única. Calcula ambos denominadores y
porcentajes en servidor; en los tres recibos originales011 entrega10% por coste y
90% por recursos, con paridad streaming/final/público. El replay de84sólo selecciona
esas tres muestras. No cambia sus etiquetas históricas ni prueba al proveedor.
La gramática exige declaración completa, cuenta consistente y coste etiquetable;
otras formulaciones/ámbitos o evidencia financiera conservan la ruta general.
Coste total cero queda indefinido. No audita etiquetas ni convierte el escenario
en medición financiera. Terminal ligado al hash sólo admite auxiliares vacíos.

El parser/gateway ahora registra campo, modo, tipo e índices acotados de un rechazo
en answer, incluidos textos unidos; no guarda texto, ecuación ni hashes de prosa.
No se relaja el validador de ecuaciones libres.021 continúa pendiente: el diagnóstico
servirá para otra ejecución, no reconstruye el candidato histórico no conservado.

226 pruebas focales processor PASS,24 backend y6nuevas de fragmentación PASS.
Las49identidades nuevas también PASS en Linux sin omisiones/OOM, usando cuatro
contenedores propios sin red, fuente sólo lectura y JUnit durable. Retirados por
ID/etiqueta; IDs/imágenes del runtime B iguales antes/después. Sin activar candidato,
inferencia o gasto nuevos; no sumar las49repetidas a las pruebas locales.
Manifest/pin actualizados y ambos loaders propios aceptan versión
`jup-035.chat.v3:b6aa3330f1ea2f6d0cea1a12dc67ba17a1ce090cf19a99f97eba5b78a8b649c8`,
assembler7dcbcbc53754a50cc7758655884b82c74cd5ed0c2e7e4514e539b965c4b9896b.

Commit654298d4ddebc44909ca0ee100e210dd9cefcc66; archivo versionado transferido
SHA812151d811d25e90d6df05e28d9c5802294ae9c12ac265c76f642f758d475dc6 a
DockerServer/candidate-654298d4 bajo el root B, sin.env ni credenciales. Evidencia
externa `weighted-diagnostic-assessment-v1.json`, `weighted-linux-654298d4/`,
`weighted-coverage-replay-v1.json` y`weighted-coverage-cold-load-v1.json`.
Fallos de arnés/ruta, manifest inicialmente desactualizado, impresióncp1252
posterior a226PASS y ACL de tmp quedan preservados, no contados como aprobados.

Siguiente:001/009, resolución de021 y dudas004/022; luego build/activación propia
del candidato completo (incluido frontend de A), admisión viva y medición que
permita el máximo5USD. Última cota4.423039035 es del corte20:37UTC, no saldo nuevo.
Criterios, adjudicación independiente, navegador final y N5 siguen pendientes.
Trello sincronizado por la integración DockerServer, con lectura exacta y estado
conservado: `jup123-trello-weighted-update-v1.json`, descripción
SHA2a52f6e45840f359d5041d5f64627754b7e3cfb46f7b06965179def3f5148eb2.
OpenSpec estricto conforme. Ninguna publicación GitHub/Discord.

#### A/11f84334 incorporada y comprobada en B/ab66f90c

Descargado el commit exacto de A y aplicado su diff por bloques sobre la rama B.
20 archivos coinciden por blob con A; el esquema conserva sus79 líneas de diferencia
semántica y sólo añade ChatCapabilities. Nuevos endpoint/flag, frontend y CD
no sustituyen v4 ni expresiones/políticas. No se copiaron resúmenes/OpenSpec de A.
Prueba `reconcile-a11-block-identity-v1.json`; producto ab66f90c86a2095039331630aa167f5f17b910bd.

34 pruebas de backend,120 de frontend y58 de CD en Linux PASS, sin omisiones;
40 topología/workflow PASS. Tres typechecks y build correctos, lint sin errores y
un aviso previo. `init`/`prepare` y Compose reales renderizan ambos slots, con
subred/IP separadas, HMAC reutilizado444 en directorio700 y puertos privados.
La prueba de crear ambas redes no se ejecutó: pool ajeno172.30.0.0/16 existente.
No se modificó ni retiró esa red. Secretos sintéticos/root de render retirados;
servicios B mantienen IDs/imágenes, sin activación del candidato ni inferencias.

Ambos loaders propios conservan versióna4709b0622e7321221bd6923d6822e68f4651e5d452f659cfaeb14f1dab2d19b.
`reconcile-a11-assessment-v1.json` resume alcances, JUnit y hashes;
`reconcile-a11-linux-ab66f90c/` conserva prueba POSIX/render;
`reconcile-a11-frontend-build-checks-v1.json` ylogs registran tipos/lint/build.
No sumar los dos skips Windows a los58 Linux ni los3 Node iniciales a los40 finales.

Se cierra1.3 como reconciliación de código y comprobaciones de sus superficies
sobre el pin A/11f84334 y develop/c30a7d0. No significa aceptación de A, despliegue
viable en ese pool ocupado ni validación de navegador del candidato B completo.
Reconsulta `jup122-pr130-after-reconcile-a11.json`: misma cabeza/base, OPEN y dos
CHANGES_REQUESTED, sin aprobación nueva. Si A cambia de nuevo, revisar sus bloques.
Aceptación, navegador final, criterios, adjudicación y N3/N5 de B siguen pendientes.

#### Recuperación de políticas comprobada con SQL real

Producto local posterior `fb7d9ea0bcef30b7994451c74d5d1fb7f596a8f7` y pruebas
adicionales `ddb64eb513fef5d05badb2857a4e73ff421ed0ac` (sólo cambia un fichero
de tests entre ambos). Se recupera la sección solicitada por tenant y proveedor
en la misma transacción REPEATABLE READ, sin otro embedding. El máximo sigue
siendo20 fragmentos; la expansión de política admite como máximo6. Dos documentos
candidatos, un documento de más de65536 bytes, sección sin cierre o huecos no
ganan prioridad. La distancia se conserva, aunque la selección exacta de una
política esté fuera del umbral de similitud. Las omisiones por límite se declaran.

**46 pruebas Linux/pgvector PASS, sin omisiones**, con JUnit durable y nodos únicos:
6 nuevas SQL (presupuestos/tagging, aislamiento, ambigüedad, actualización concurrente,
tope6 y límite en bytes UTF8),14 de contrato pgvector y26 focales del contexto/
compilador/vecinos. La actualización concurrente prueba que textos, chunks y citas
leen la misma versión aunque otro escritor confirme una política distinta.
Dos primeras tandas acabaron43PASS y3PASS pero perdieron JUnit al terminar el
tmpfs; se conservan sus logs y el fallo de recogida. La tanda46 completa usa una
carpeta de evidencia propia para XML persistente; no sumar las repeticiones.

Se usaron PostgreSQL y runner desechables con red sin salida, datos en tmpfs y
fuente sólo lectura; sin credenciales de IA. IDs/imágenes de backend, processor
y pgvector del B vigente iguales antes/después; contenedores propios retirados,
sin OOM. No se activó el nuevo candidato. Archivo ddb SHA256
667d282f06cc4b97919a633d7133ff959aeb0eb41cd01123ccfe4b57b346bc7c; fuente
remota `/home/danteadmin/economicon-jup123-20261014/candidate-ddb64eb5`.
Pruebas/hashes: `policy-retrieval-sql-assessment-v1.json`,
`policy-retrieval-native-ddb64eb5-durable/` y `policy-retrieval-transfer-proof-v2.json`,
en la evidencia externa habitual. La prueba de presupuestos recupera y compila
«investigacion, no apagado automatico»; esto todavía no es aceptación LLM de015.

17 pruebas de recursos processor PASS y carga en frío independiente de ambos
servicios con versión `jup-035.chat.v3:a4709b0622e7321221bd6923d6822e68f4651e5d452f659cfaeb14f1dab2d19b`;
assembler3361ddbac0491efe050200a57c111a9a2ca48b8fe491a5dc32219799a7191872.
Evidencias `policy-retrieval-resource-tests-v1.{xml,log}` y
`policy-retrieval-cold-load-both-v1.json`. No prompt de sistema nuevo, inferencias,
consumo ni publicación. Runtime medido sigue c7; contabilidad histórica más abajo.

Nueva consulta de A: PR130 avanza a11f8433404f786c065ad35f13f673465fa26caf5,
añade red/IP por slot y capacidades autenticadas para ocultar el chat y comprobar
antes de crear conversación. Diff de27 ficheros respecto a28ee5b1c. Reviews siguen
las dos solicitudes de cambios; sin inline threads nuevos. CI de esta cabeza no
verificada: consultas por SHA devuelven listas vacías, no un PASS. En este corte previo faltaba incorporar
sus bloques a B y probarlos; superado por ab66f90c arriba. No sustituir nuestros resúmenes con la documentación
histórica de A. Recibos `jup122-pr130-current-11f84334.json` y
`jup122-pr130-11f84334-commit.json`, con reviews/conversación/inline leídos.

Siguiente tras reconciliar A: continuar001/009/011/021 y las incertidumbres
004/022. Ninguna casilla de aceptación de B se da por completada por este bloque.
Trello actualizado por la integración DockerServer, sin mover deEn curso,
concurrencia y lectura posterior exactas. Prueba `jup123-trello-policy-sql-update-v1.json`;
descripción SHA db910a52e222ce211de7cad1e61e7b3b5f811e8311818507f06fc7d90937a936.
Actualización posterior de A incorporada: `jup123-trello-a11-update-v1.json`, lectura
exacta y lista conservada; descripción SHA6618ad8fda3f0d44dd741653c552f3bf85872062c33f52ebd29b9720a25be75f.
Ningún mensaje Discord. OpenSpec estricto del bloque conforme.

#### Corte anterior: compilador de políticas (79e6a22d)

En este corte, aún sin medir ni transferir: compilador de secciones
completas `chat_policy_sections.py`, integrado en esquema privado, streaming y
renderer de ambos servicios. No cambia el runtime c7 ni sus recibos. Ver el
[diseño](../../openspec/changes/jup-123-chat-semantic/design.md#compilador-local-de-secciones-completas--2026-10-14).
Lee listas/tablas y conserva literalmente todas las reglas, valores y modalidades
del corpus autorizado; no copia las cinco etiquetas del banco a Python. Las
preguntas conceptuales de tagging y operación de budgets se enrutan por tema;
otros pedidos, negaciones, cálculos y consultas múltiples siguen la ruta general.

La compilación exige encabezado original, siguiente encabezado que cierre la
sección, rangos contiguos y coincidencia de solapamientos. Ambigüedad entre dos
documentos, huecos, tabla dañada o cita que no quepa íntegra en un fragmento no
producen un terminal autorizado. Su hash liga pregunta, sección completa y fuentes;
el proveedor sólo puede devolver ese terminal, sin añadir limitaciones o métricas.
Un contexto financiero de pantalla no desactiva la pregunta de política ni le
otorga autoridad financiera. No hay un parser semántico general ni una garantía
para formulaciones fuera de la ruta admitida.

Verificaciones finales del bloque:247 pruebas focales del processor PASS y dos
del backend con corpus real PASS; carga en frío propia de ambos servicios con
la misma versión de recursos. El verificador backend conserva su implementación
independiente; sólo avanza ASSEMBLER_SHA, no se sustituye por el loader processor.
Versión `jup-035.chat.v3:28d964a6749790021d80037a99905c6696f15bf25ab54b960585a6a7ae74d8b4`;
assembler13b1bf57d91e5ca5f64dff1dc809a86fc83dbced2a72fa42235570eec9674368.

Replay de selección sobre los84 recibos c7: la ruta nueva selecciona sólo las
tres muestras010, con once unidades literales completas, mismo streaming/final
y ensamblado público correcto. No es una nueva campaña ni reemplaza etiquetas.
015 sigue sin compilar por faltar su sección completa en los recibos originales;
con la sección completa del corpus, la prueba backend conserva investigación y
ausencia de apagado. Resta recuperar esa sección en el mismo snapshot SQL y
dentro del plazo y presupuesto existentes, antes de afirmar corregido015.

Evidencias externas `policy-sections-focused-final-v5.{xml,log}`,
`policy-sections-backend-final-v5.{xml,log}`,
`policy-sections-{resource-load,backend-cold-load}-v5.json` y
`policy-sections-replay-v2.json`. Fallos previos de arnés y el test negativo que
detectó una captura de cálculo quedan conservados. No cambió el prompt de sistema.
Sin inferencias, consumo nuevo, transferencia, despliegue ni publicación.
Resumen con hashes y alcance: `policy-sections-local-block-v1.json`. OpenSpec
estricto PASS e higiene1620 archivos PASS; estas comprobaciones no sustituyen
la medición pendiente ni las pruebas SQL/Linux del próximo bloque de retrieval.

Supera el avance 47/84 y la revisión sólo r1 descritos más abajo. Producto
c7e2d5616d3ba3d4e6fa467f27f272a05595a621: 84/84 recibos verificados,
83 completed/1 failed. Controlador 3607245 terminado COLLECTED/NOT_ASSESSED;
no reiniciar ni escoger nuevos intentos. [Informe completo](../validation/JUP-123-c7e2d561-N3-local-review.md).

Revisión local provisional: **70 conformes/7 inciertas/6 fallos de contenido/
1 técnico**. Comprobaciones: 470 pass/12 uncertain/7 fail/6 sin respuesta.
Fallos: 001r2 niega coste actual aportado; 009r1 cita ajena; 010r1 omite minúsculas;
011r3 no entrega 10% por coste; 015r1/r2 omiten investigación. Dudas en 004 las
tres veces, 011r1 y 022 las tres veces. 021r3 falla por ecuación libre en
provisional_answer: el parser sólo procesa answer, pero no se conservó el
candidato privado ni se conoce el segmento o ecuación exactos.
014/017/027 conformes 3/3; 003 también completa 3/3, con deuda de presentación.

Pares contra e23: 438 pass→pass, 7 pass→fail (seis respuestas; cinco
comprobaciones del banco y dos de calidad provisional), 7 uncertain→uncertain,
6 uncertain→pass, 2 fail→pass. 003r1/013r3 técnico→conforme; 022 técnico→incierto;
021r3 técnico→técnico. Originales reconsultados, etiquetas históricas intactas.
No causalidad ni aceptación por media; criterios/adjudicación siguen pendientes.

Snapshot externo candidate-c7e2d561-n3-complete-v2: 258 SHA verificados,
manifest 48de0d4b745a8640ae6540243691f1c4f91affd7ba55396f122daded26b65cbd.
Primer intento de congelación incompleto preservado y marcado: no puntuarlo.
56 filas anteriores y sus 168 archivos raw/derivado/coste idénticos.
score-c7e2d561-n3.py normaliza cada recibo con scorer sin cambios. Juicios/revisión
candidate-c7e2d561-n3-local-{judgments,reviewed}-v1.json; comparación paired-e23-v1
y assessment-v2. Este último corrige sólo la extracción de nonpass en el resumen,
sin cambiar etiquetas ni totales. Evidencia bajo materiales/07-evidencias/
PR121-local-evaluation del workspace padre; detalle en el informe enlazado.

Contadores finales: 2.501327035 USD + 1.921712 USD reservas = **4.423039035/5 USD
conservadores**. Seis costes fallidos desconocidos y seed retenidos; 021r3 añade
0.319952 USD íntegros. 404 upstream/spend0 no prueban gratuidad. No liberar reservas,
renovar claves ni lanzar otra campaña por el resto aparente. Claves exclusivas
mantienen vencimiento 15/10 08:02 UTC. Ninguna inferencia posterior a este cierre.

Trello actualizado sólo por puente DockerServer, concurrencia/lectura posterior
exactas; En curso sin mover. Prueba jup123-trello-c7e2d561-n3-complete-update.json,
descripción SHA 104c3afd285de429a669d413c2a3c16d126d4f1764f9088212bf37144e121e77.
Sin mensaje Discord ni publicación GitHub de B. La reconciliación final de A
conserva sus dos solicitudes; sus reviews no se reconsultaron en este corte.

Siguiente: cobertura explícita de hechos/reglas/resultados por servidor,
preservar premisas/modalidad y diagnóstico de campo sin contenido privado.
Contraejemplos offline antes de otra campaña; no más reglas de prompt por caso.
OpenSpec estricto del cambio validado con CLI instalada mediante Node directo;
el wrapper pnpm intentó resolver dependencias por red y abortó sin completar.
No se repiten las 1470 pruebas por cambios sólo documentales en este corte.

### Corte anterior: N3 de e23

**Recogida N3 completa del candidato e23e495b24fae76decacf7d030468b75cd52b5f8:**
84/84 recibos verificados,78 operaciones completadas y6 fallidas conservadas.
Controlador2878413 terminado conCOLLECTED/NOT_ASSESSED; último caso028r3 con
COST_OBSERVED. No volver a lanzar esta campaña ni escoger mejores intentos.
Herramientas de control e92628df; producto e23 congelado durante las tres rondas.

Snapshot final externo: `materiales/07-evidencias/PR121-local-evaluation/`
`candidate-cap5-n3-complete/` relativo al workspace padre. Contiene84recibos
originales(raw),84derivados,84pruebas de coste,backupSQLite consistente y agregado
sin ausencias;manifest registra257archivos porSHA256. No modificar el snapshot.
Contabilidad viva final: cota delcontador2.078111791USD + reservas1.601760USD =
**3.679871791USD** conservadores dentrode5. Hay5fallos conCOST_UNKNOWN_RESERVED
que retienen toda su cota, másseed0.002; no equivalen a coste0 ni gasto conciliado.
Claves exclusivasB mantienen vigencia15/10 08:02UTC; no renovadas.

Evaluación completa normalizada en `candidate-cap5-n3-unreviewed.json`.
Remapeadas13muestras desde el corte56 con hashes de evidencia/criterio iguales;
además se comprobó igualdad de la fila completa en las56muestras del corte
(incluye fragmentos autorizados y auxiliares). Prueba externa
`candidate-cap5-first56-to-full-row-identity.json`. Ese corte v2 fue ampliado:
la revisión local v6 cubre las78respuestas disponibles y queda68pass/8pending/
2fail/6technical_failure globales.445checks pass,13uncertain,2fail y35sinrespuesta
porfallo técnico; no sonPASS. Ver informe enlazado másabajo. Revisión local
provisional, no independiente ni aceptación final. Corrección de referencia:011 está soportado porFinOps10,
noRules2; la etiqueta mantiene su estado y razón corregida en el informe completo.

Trello JUP123 actualizado mediante el puente autorizado a recogida84/84 y cota
final, conservando historial, rol de revisores y aceptación pendiente. Prueba
externa `jup123-trello-n3-complete-update.json`; verificación previa de concurrencia
y respuesta confirmada. No se movió la tarjeta a terminada ni se publicó B.

Revisión local por requisito y comparación emparejada realizadas (v6); aceptación
pendiente. Las correcciones 014/003 están guardadas en c7e2d561; Linux/SQL pasan y resta su medición real,
incertidumbres mediante juicioindependiente, criterios/N5 ydependenciaA/PR130
(reviews yverificación delosbloques incorporados). No cambiar el
producto basándose en una sola repetición. Leer los límites de los contrastes
focales y la evidencia de UI real más abajo antes de declarar algo validado.

### Primera ronda c7 revisada; nueva dependencia de A — 14/10/2026

Campaña PID3607245 comprobada viva por `ps`, mismo argv/commit, sin reiniciarla.
Corte20:13UTC:47/84 recibos verificados,47completed/0failed;20r2 en observación.
Última admisión: cuenta2.306321630 USD + reservas retenidas/activas1.921712 USD =
4.228033630/5 USD conservadores. Incluye la reserva completa del paso activo;
no es gasto exacto ni saldo garantizado. Prueba externa
`candidate-c7e2d561-r1-review-progress.json`. No cambios de producto durante N3.

Congelados cortes21 y primera ronda28 en `candidate-c7e2d561-first21/` (65hashes)
y `candidate-c7e2d561-r1-frozen/` (86hashes): originales, derivados y pruebas de
coste. Todos comprobados tras transferencia. Los21 recibos son byte a byte los
mismos en ambos cortes; ningún mejor intento ni etiqueta de completed=PASS.
Scorer/banco/rúbrica/partición sin cambios. Adaptador offline normaliza cada
recibo por separado para conservar IDs al añadir muestras; prueba de identidad
de las21 filas completas en `candidate-c7e2d561-first21-to-r1-identity.json`.

Revisión local provisional de las28 respuestas/165requisitos terminada:
**22 conformes,3 inciertas,3 fallidas;157 requisitos PASS,5 inciertos,3 FAIL**.
No es adjudicación independiente ni aceptación N3. Evidencia versionada fueraGit:
`candidate-c7e2d561-r1-{judgments-v2,reviewed-v2,paired-e23-v1,assessment-v1}.json`
y `score-c7e2d561-r1.py`. Se mantienen los cortes previos, no se sobrescriben.

Fallos r1:009 selecciona una cita sobre minúsculas sin relación con el reparto;
010 omite explicar normalización de claves en minúsculas;015 omite investigación
al superar umbral. Incertidumbres:004 inferencias categóricas sobre actual/
amortizado;011 no explicita90% por recursos;022 afirma base actual no estable a
partir de rightsizing pendiente y usa un rationale definitorio de alcance dudoso.
006 repite diez veces una limitación: deuda de presentación, sin inventar una
infracción semántica del banco por esa repetición. 014r1 incluye200EUR/20% y
003r1 completa; faltan sus otras repeticiones para juzgar estabilidad.

Paresr1 contra e23 con los mismos hashes de criterio:146pass→pass,3uncertain→
uncertain,2uncertain→pass y3pass→fail (009/010/015).003 técnico→conforme y022
técnico→incierto, fuera del conteo de requisitos comparables. Se releyeron las
respuestas e23 de009/010/015 y sus etiquetas: las citas eran pertinentes y las
reglas omitidas ahora sí aparecían antes. No se ajustaron etiquetas históricas
para ocultar regresiones; tampoco se atribuye causalidad al cambio con sólo r1.

Consulta GitHub posterior: A/PR130 sigue28ee5b1c sobre develop/c30a7d0, pero hay
review oficial nueva de Víctor a18:58UTC con CHANGES_REQUESTED. Pide subred/IP
distintas por slot del CD (solapan al segundo despliegue) y UX correcta al estar
el chat desactivado. Sus cinco puntos anteriores se consideran resueltos/no
aplicables por él; no es aprobación de A. Lucía conserva su solicitud de cambios
anterior y aún no ha validado los criterios. Reviews, conversación e inline
leídos y guardados en `jup122-pr130-current-20261014-night.json` (sin publicación).
Se reabre1.3 para reconciliar las correcciones finales de A cuando existan;
las pruebas positivas propias conservan su alcance, no cubrían esos dos defectos.
No cambiar A ni el candidato medido mientras termina esta N3.

Trello consultado sólo por el puente autorizado: descripción mantiene criterios
propuestos; sin comentarios de esta tarjeta en las últimas100acciones del board.
Ese límite no prueba ausencia de comentarios más antiguos ni acuerdo externo.
Prueba `jup123-trello-criteria-readonly-20261014-night.json`; no hay criterio humano
aprobado que permita cerrar por tasa media. Siguiente: terminar N3, comparar por
requisito/repetición y sólo entonces seleccionar correcciones deterministas;
mantener la adjudicación independiente y el alcanceN5 pendientes.

Trello actualizado tras esta revisión parcial, con concurrencia y lectura
posterior verificadas por el mismo puente. DescripciónSHA
`f310531e21664def9c66a98aa099bb1a8f3c0a0d85a71bb582d7262eede04532`, prueba
`jup123-trello-c7e2d561-r1-update.json`; estado sin mover, ningún mensaje Discord.

### Candidato c7e2d561: transferencia y comprobaciones en curso — 14/10/2026

Commit `c7e2d5616d3ba3d4e6fa467f27f272a05595a621`, archive Git
SHA256 `0b18edaf6f256e4d2880a9322b5874ca079bb670276e0562fa640320a5e270d2`.
Transferencia y plan verificados en DockerServer bajo el root exclusivo B
`/home/danteadmin/economicon-jup123-20261014`. Plan
`candidate-c7e2d561-offline-plan.json`, SHA256
`280ae38fea4a7122dfb12be768e35bc54e7e34d1253ad4e9cabb1b7aab28fe26`:
84 muestras; el estado NOT_RUN pertenece al plan congelado y no se modifica:
la ejecución real posterior se registra en el ledger. No heredar la medición e23.

Primer preflight detenido al consultar una base antigua de fixtures; ningún
servicio detenido en ese intento. Corregido para derivar el nombre de base del
entorno efectivo del backend (`defaultdb`), con 193 completed/16 failed y cero
operaciones abiertas. Segundo intento conjunto Linux terminó OOM137 en processor
con 1500 MiB, sin JUnit final: no es PASS. Ambos intentos originales preservados
con 12 hashes en evidencia externa `candidate-c7e2d561-failed-attempts/`.
Los dos contenedores originales B fueron restaurados y comprobados por ID/imagen.

Regresión por archivo `regression-c7e2d561-per-file` terminó tras otro OOM137 en
backend/context_assembly: 41 archivos superados y un archivo incompleto, sin fallo
de aserciones demostrado. Servicios originales restaurados por ID/imagen.
SQL/build iniciales se detuvieron por su condición de dependencia, sin ejecutarse.
Ninguno de esos controladores sigue pendiente; no reiniciarlos.

Recuperación `regression-c7e2d561-recovery`, PID3536339, TERMINADA: reutilizó los
41 resultados íntegros por hash, ejecutó los 35 nodos exactos de context_assembly
en procesos distintos y los 28 archivos restantes. Mismas aserciones y fuente,
sin omitir casos ni elegir mejores intentos. Cobertura verificada: 70 archivos,
1470 identidades únicas; **1418 PASS, 52 SKIP nativos, cero FAIL/ERROR**. Los cuatro
symlinks que Windows rechazó pasan realmente en Linux. Contenedores sin red,
secretos ni escritura en fuente, UID10001/1500 MiB. Ambos intentos OOM permanecen
registrados y no se cuentan como PASS. Logs/JUnit y controladores copiados con
225 hashes a `candidate-c7e2d561-linux-evidence/manifest-unit.json`.

SQL `native-c7e2d561-v2`, PID3540297, TERMINADO: processor8/8, backend47/47 PASS,
sin omisiones ni OOM, en dos bases nuevas del entorno B. Las 52 identidades
omitidas offline están entre esas 55 (3 ya pasaban offline); total combinado
**1470 pruebas únicas PASS**, no sumar duplicados. Fixture processor deja cero
filas propias; servicios originales restaurados por ID/imagen. Pruebas de
cobertura `candidate-c7e2d561-{offline,native}-coverage.json`.

Build `build-c7e2d561-v2`, PID3540298, TERMINADO: backend/processor exit0, bundles
reales cargados en build. Imágenes backend
`sha256:bb84a117e36f7c8c7c052e5ace2c3b4caa542fe2b6b1ed938caef201889f6b5b`,
processor `sha256:55197cd8d9f811db577b5c301725347a226fd215921225685204deba3964162b`.
Activación exclusiva B terminada: `ACTIVE_VERIFIED_NO_INFERENCE` en su recibo de
activación, antes de iniciar la campaña. 340 hashes de fuente y tokenizer real de
ambos servicios verificados. Prueba `candidate-c7e2d561-activation.json` copiada
dentro de `candidate-c7e2d561-linux-evidence/`; 31 archivos adicionales de SQL,
build y runtime con `manifest-native-build-runtime.json`. No se modificó ningún
despliegue ajeno a B. Ese estado de activación es histórico, no niega el inicio
posterior de inferencias descrito debajo.
OpenSpec JUP-123 validado estricto nuevamente. La partición es una limitación del
entorno de pruebas; no acredita una ejecución monolítica Linux sin OOM.

Adaptadores específicos preparados sin dispatch: `candidate-c7e2d561-step.py`,
`candidate-c7e2d561-retrieval.py`; salidas propias y mismo ledger. Preflight nuevo
exige pins del tokenizer generado tras verificar ambos contenedores reales.
Prueba de preparación externa `candidate-c7e2d561-operators-proof.json`.
Adaptador actualizado antes de usarlo: SHA256
`363404e9c2f34ce0d938cb64fcae0410a36109f6dddd500e51d84fa4b21f2e4e`;
comprueba política viva DeepInfra/fp4, sin fallbacks, ZDR, sin recopilación de datos
y razonamiento desactivado antes de cada admisión. Versión previa preservada;
pruebas `candidate-c7e2d561-{routing-readonly,operator-routing-guard}.json`.
Contabilidad consultada a 19:26 UTC: contador 2.078111791 USD, reservas desconocidas
1.601760 USD, cota 3.679871791/5 USD; claves sin renovar, vigencia 15/10 08:02 UTC.
Evidencia `accounting-before-c7e2d561-readonly.json`. Releer antes de cada dispatch.

### Campaña c7e2d561 iniciada y UI comprobada — 14/10/2026

Controlador **PID3607245** en `candidate-c7e2d561-campaign/` del root remoto B.
`launch.json` conserva argv y hashes. Usa herramientas del archive c7, adaptador
SHA363404e9 y recuperación propia; `--retain-unknown-cost` conserva toda reserva
sin coste probado. Los tres planes previos conocidos siguen en la cobertura del
ledger, sin borrar intentos ni reiniciar contadores. Salidas nuevas
`candidate-c7e2d561-n3/` y `candidate-c7e2d561-raw-api/`.
**No iniciar otro controlador**: consultar PID, log, recibos y ledger antes de
cualquier recuperación. Sólo un dispatch a la vez; cada uno comprueba fuente,
proveedor, contabilidad viva, caducidad y admisión antes de reservar/enviar.

Último corte guardado en `candidate-c7e2d561-progress.json`: 18/84 respuestas
001–018r1 completed y VERIFIED_PUBLIC_SNAPSHOT; no aceptación semántica ni
comparación N3 terminadas. 003r1 ya completa sin el fallo técnico previo; no basta
para declarar corregidas sus tres repeticiones. Última admisión observada
19:52:58 UTC: cota de cuenta2.150134987 USD + reservas1.601760 USD =
**3.751894987/5 USD** conservadores en ese corte, no gasto exacto atribuible ni
saldo actual garantizado. Las reservas activas posteriores añaden su límite antes
del dispatch; el controlador se detiene si el siguiente paso no cabe o caducan
las claves. Sigue vigente15/10 08:02 UTC, sin renovación.

Trello actualizado exclusivamente por el puente DockerServer con verificación
previa de concurrencia y lectura posterior; descripciónSHA
`3c9bef7cabae5b772f2ca9a63b1e2a8d35248cbcb3697d5e2f0a6533fa30ea11`.
Prueba externa `jup123-trello-c7e2d561-update.json`. Tarjeta sigue En curso;
sin publicación B ni mensajes Discord. Criterios y juicio independiente pendientes.

UI real c7: login demo en memoria, lectura de conversaciones exactas001r1/003r1/
014r1, escritorio1280/móvil390 y recarga/reapertura. Contenido coincide con sus
recibos normalizando espacios y la presentación de marcadores de cita; hashes
de ambos en `c7e2d561-ui-result.json`. Cero escrituras del asistente intentadas,
todas bloqueadas por el test; no inferencia desde navegador. Capturas
`c7e2d561-ui-JUP-069-{001,003,014}-{1280,390}.png`; inspeccionadas visualmente las
dos014:200EUR/20% visibles, sin métricas reales inventadas. No es validación de
streaming visual, de todos los casos ni de calidad semántica completa.

agent-browser no estaba instalado; se usó skillPlaywright disponible. Se conservan
los errores de arnés (lector usaba campo inexistente y navegación antes de cargar
el cliente), sin atribuirlos al producto ni repetir inferencias. Ejecutor copiado
sin cambios a un temporal propio para no limpiar temporales de otros agentes;
clave nunca guardada ni impresa. Túnel local29657/29660 PID28688 cerrado tras
comprobar identidad; SSH del usuario y puerto28660 intactos.

Siguiente: observar el mismo controlador hasta cierre/parada, congelar todos los
recibos y costes con hashes, revisar por requisito y comparar las repeticiones
con e23/baseline sin cambiar etiquetas históricas. Conservar incertidumbres para
adjudicación independiente y acordar alcanceN5. No declarar PASS global por
completar operaciones ni cambiar el producto durante esta campaña.

### Correcciones014/003 locales y regresión00dc terminada — 14/10/2026

Windows00dc terminó: processor770PASS/6SKIP/2FAIL ybackend619PASS/46SKIP/2FAIL.
Los4fallos sonWinError1314, falta deprivilegio para crear symlinks; no se omiten
ni se llamanPASS. JUnit/logs binarios completos enregression-00dc2e0f-windows/.
Sesión49786 terminal, no volver aconsultarla comoviva. Falta comprobar enLinux.

Leída parcial durable003r1, sólo operación/tenant sintéticos:3918caracteres con
19repeticiones deun pasaje. La deduplicación local valida antesde suprimir copias
idénticas source_id/passage sólo enanswer; auxiliares/pasajesdistintos intactos.
Gramática delproveedor limitada a24bloques, límite público4000 yrender legacy128
conservados. Simulación delrender de parcialreduce3918→1410conparidadstream/final;
no prueba cierre real delmodelo ni recuperación de su privado completo. Comoel
recibo fallido no retiene su conjuntoRAG final, se usaron referencias delcorpus
inmutable conocido; no presentar esa simulación comoprocedenciaRAG de003r1.

014: helperderiva diferencia absoluta yporcentaje sobrepresupuesto cuandohay campos
forecast/budget explícitos, adyacentes ycompatibles enmodo hipotético. No cambia
facturación,fuentesfinancieras ni ruta general para datosambiguos; no es extractor
universal ni verificador deperiodos. Tres entradas014 delN3 producen200EUR/20%
offline; recibos/veredictos viejos intactos. coverage-014-003-offline-v1.json.

Nuevaspruebas:143processor focales(original141+2contraejemplos),65backendPASS;
selección amplia295PASS/2FAIL: dos404del fixture porplazo deSQL iniciado antesde
preparación; ajustado sólodel fixture a fenceexacto conclaim traspreparación,
sin relajar409/413. Repetición pertinente final50/50PASS, JUnit/log en
coverage-014-003-final-v2.{json,xml,log}. Código contrato24 validadoenfrío enambos
servicios: prompt_version jup-035.chat.v3:7bb89154fd095e91422cdb80ee4cf6066e557986efa4fb5cd890e17ce4024791;
assembler567aa36a17e455f61a7b9a9a8f3b29db54e7ea7d34669b486559d4e1122bfe77.
Sin inferencias reales nuevas; no heredar campañae23 a estecandidato.

Auditoría exclusivaB: backend497MiB/processor537MiB;193completed/16failed,
0operaciones abiertas. Host1545MiB disponibles enúltimocorte. ParaLinux esseguro
considerar detener temporalmente sóloesosservicios B inactivos yrestaurar mismos
contenedores/imágenes después; no se han detenido todavía. Ningún otrodespliegue
puede usarse para liberar memoria. Evidencia b-exclusive-idle-resource-audit.json.

### Regresión corregida en ejecución — corte histórico superado del 14/10/2026

Producto local00dc2e0fd768fd855175ddf92ee292e48cf4eab6: A reconciliada ymanifest
refrescado. Copia inmutablegitarchive usada para regresión Windowsmonolítica,
SHA115deee643bd7cda4d1551357cf204b79fb35fa75b75b928809664d9bc1eab34.
Sesiónexec49786 sigueejecutándose; PID18676, metadata/status/logs binarios yJUnit
porpaquete en materiales/07-evidencias/PR121-local-evaluation/regression-00dc2e0f-windows/.
Se retiraron credenciales delentorno deltest yse bloquearonproxies externos;
fixturessintéticos. Verificar mismasesión/PID yresultados, no reiniciar por silencio.
No resultadofinal todavía. LosintentosLinuxanteriores sonterminales ysiguen
preservados con24archivos/hash en candidate-a294f7e1-linux-attempts/.

Pendientes funcionales siguen014(excesorelativo) y003(presupuestotexto), pruebas
reales delcontrato nuevo, adjudicación/N5/criterios yreconciliaciónverificadaSQL/A.
No heredar N3e23 a00dc ni dar porresueltos guardrails porpasar comprobaciones
focales. Ninguna inferencia nueva; cota anterior3.679871791USD, máximo5USD.

### Reconciliación A y defecto de manifest corregido — 14/10/2026

Candidato a294f7e1a9904da2b9cd8b8a80e3ccececd0f8d4 transferido porarchiveGit;
SHA256dbd21808e38a67755d659cf52ffdbffd6cab15298e1080a4c8ffef8efe6bde2b.
338hashes fuenteverificados, tokenizer generado público idéntico. Planoffline
NOT_RUN SHA6527f8e9b554dce5277fe41c41b5ef9f91be5d93b39a03b9d4c0289ef109dda9;
no campaña pagada. Fuente remota candidate-a294f7e1 bajo rootB.

MonolíticoLinuxPID3206932 terminalOOM137 a768MiB, sinJUnit. PorarchivoPID3219856
terminal tras6archivos:151PASS,1FAIL ycontext_budget OOM137. Elfallo realde
battery_corrections fue Resource contract mismatch delbundle real; noes fallo
semántico delLLM. Windowsmonolítico sesión46457 se interrumpió expresamente
tras confirmar ese defecto; PID25048 e hijos ausentes, logsconservados sinPASS.
No reintentar esosprocesos ni presentar sus resultadoscomo regresióncompleta.

Corregido manifest real: provider_response_schema_sha256 cambia de69303e6c…
a d5774bc8e24164594523981ab077216c62f8a2c1aa0a38d09b6a14cd683e3ea2.
Assembler ypromptsinvariación. Cargaenfrío realPASS enbackend/processor, nueva
prompt_version jup-035.chat.v3:c0fc781abdfaa74f45a8232df2855bf5bfc7a5e539b259d3732598af7d1faaf4.
Pruebaque fallaba5/5PASS conJUnit (manifest-refresh-result.json yXML externo).
Pendiente nueva regresión durable sobreestehash, no heredar pruebas deA/e23.
Sin inferencias ni coste nuevo; runtimeB e23 sigueintacto.

### Revisión N3 completa y ajustes de contrato — 14/10/2026

Avance posterior: incorporados localmente losbloques deingeniería A/28ee5b1c
(tokenizer generado/build/CI/CD/fixtureSQL), conservando gatewayv4 ysemánticaB.
Planes nuevos incluyenpin deartifact generado yverificación delarchivo real
backend/processor; preflight incompleto bloqueaantes de reserva/inferencia.
86pruebas herramientasPASS,4tokenizerPASS,CD55PASS/2SKIP,51CI/topologíaPASS.
Ver chat-entregas-a-b.md. Pendientes regresión completa durable, SQL nativo y
build sobreestecandidato; no trasladar laCI deA ni las pruebas e23 como propias.

[Informe de resultados y pendientes](../validation/JUP-123-N3-local-review.md).
Revisión localv6 de78respuestas:68pass/8pending/2fail/6technical_failure globales;
445checks pass,13uncertain,2fail,35unreviewed porfallos técnicos sinrespuesta.
014r2/r3 omite20% excesorelativo(muestra120%ratioforecast/budget). Calibración
congelada antesderevisarreserva; reserva históricamente conocida,nocegada.
Comparaciónv6:48fail→pass y0pass→fail confirmados,pero9pass→uncertain y003r1
pass→technical_failure impiden afirmar ausencia deregresión obligatoria.
Baseline intacta;004/009 posible diferencia decriterio necesitaadjudicación.

Diagnósticos estructurados deDockerServer:022tresveces recommendation_documentary_support_required;
013r3/021r3 response_basis_authority;003r1 rendered_text_limit. Artefacto externo
candidate-cap5-failure-diagnostics-v1.json. No se leyó candidatoprivado ni llamó almodelo.
Ajuste local deesquema exige rationale documental literal yretira citasauxiliares
enuser_scenario/greeting. No relaja validadores.118pruebas focalesprocessor y69backend
PASS. Regresión completa deprocessor terminó,pero arnés perdiósalida por
UnicodeDecodeError destderrWindows; resultado noverificable, noPASS. Repetir con
salidabinaria/JUnit persistente. No transferido/desplegado; N3e23 no validaesteajuste. OpenSpec estrictoPASS. Trello actualizado yreadbackconforme
mediantepuente autorizado (jup123-trello-review-update.json).

Integridad posterior:257/257SHA del snapshot N3 coinciden, originalintacto;
candidate-cap5-post-review-integrity-v1.json. Los6diagnósticos enlazados con
operaciones ySHA depeticiones enpruebas deuso;candidate-cap5-failure-correlation-v1.json.
El código deinvariante no demuestra elcampo exacto delcandidato privadorechazado.

Artefactos externos: candidate-cap5-n3-local-{judgments,reviewed}-v6.json,
candidate-cap5-n3-paired-local-v6.json,candidate-cap5-n3-assessment-v1.json,
candidate-cap5-calibration-freeze-v1.json. Sin inferencias ni gasto nuevo;
cota anterior3.679871791USD conserva todasreservas. Próximo: corregir cobertura014,
limite003; verificar esquema/autoridad enreal con nueva admisión; acordarcriterios,
adjudicarincertidumbres,N5 ydependenciaA. ReconsultaGitHub18:28UTC: Aavanza a
28ee5b1c44389aa8643c1c4deca6c0c834c09f7d, tokenizerfueraGit yhelperbuild;
CItecnicaverde peroJUP reviewsFAILURE/CHANGES_REQUESTED. Evidenciaexterna
jup122-pr130-current-20261014-evening.json. Falta reconciliar nuevosbloques conB;
no atribuir resolución pendiente deltokenizer a uncódigoactual sinconsultarlo.

### Contraste 007–009 y trazabilidad de los juicios — 14/10/2026

Revisadas las tres repeticiones de007/008/009 contra respuestas completas,
auxiliares y fragmentos.007 conserva10.1%rojo, sin redondear;008 explica0/0
indefinido sin entregar0%válido ni verde y pide periodo con datos.009r2/r3 piden
regla y base;009r1 conserva incertidumbre en petición“regla o consumo” frente a
criterio conjunto, sin etiquetar un fallo inequívoco. No cambian banco ni rúbrica.

007r3 repite diez veces la misma limitación del denominador: observado como deuda
de presentación en `candidate-cap5-formatting-observations.json`, sin inventar un
criterio semántico de concisión ni modificar producto. No se compensan con ese
juicio las incertidumbres reales. v2 local suma22muestras revisadas; los restantes
juicios y la revisión independiente siguen pendientes. Sin nuevas inferencias.

### Reanudación tras conciliación de 013r3 — 14/10/2026

PID2642423 terminal tras 69 recibos:65completed/4failed,68verificados antes de
conciliar. Recuperador leído de nuevo sobre la misma operación
 a9555e3f-f2dd-4e3d-a8b7-c4518b5ec6f1 devolvió FAILED_RECONCILED,
0.0050725375USD. No se repitió inferencia ni adjudicó semántica de familiareservada.
Backend/processor running,OOMfalse. La primera parada no prueba coste0; nuevo
readback permitió la conciliación completa, conservando el fallo técnico.

NuevoPID2878413 live confirmado, logcandidate-cap5-campaign-resume3.log,
pidfilecandidate-cap5-campaign-resume3.pid. Continúa después de013r3 con e23 y
herramientase926,plan/ledger/cap5 iguales. Para futurasobservaciones usar este
PID, no2642423 ausente. Lecturas/juiciosprovisionales locales no cambian producto.

### Revisión provisional de fuentes y primeros requisitos — 14/10/2026

Contrastadas respuestas completas y chunks originales de 001/002 r1/r2 y 003r2.
33 etiquetas locales en5muestras: provisionalpass según banco y rúbrica escrita;
no adjudicación independiente. Artefactos candidate-cap5-first56-local-judgments-v1
.json y-local-reviewed-v1.json; informe parcial queda5pass/48pending/3técnicos,
297checks aúnunreviewed. No hay aceptación global ni evidencia sobre todasr3.

Precisado el hallazgo027: las afirmaciones sí están soportadas por FinOps2/3 en
losfragmentos autorizados.002r2 tiene su método en FinOps8/9. Evidencevisible[]
no prueba por sísolo contenido inventado/ausencia desoporte. Cuestiónseparada:
selección/visibilidad decitas y formato, pendiente criterio derevisores. Informe
candidate-cap5-documentary-support-clarification.json. Los juicios anteriores
“soporte pendiente” quedan precisados con esta lectura, no se declara fallo de
contenido basándose sólo en evidencevacío. Sin cambio del producto duranteN3.

### Informe parcial y005 con tres repeticiones — 14/10/2026

Agregado de56recibos congeladosr1+r2 yscoreoffline sinjuicios nuevos en
candidate-cap5-first56-aggregate.json y-unreviewed.json:53pending/3technical_failure,
330comprobacionesunreviewed,28muestrasfaltantes. No se heredanPASS deheurísticas
ni decampañas anteriores. Datasetreserva sigue sinadjudicar.

005r3completado: r1/r2/r3 cumplen todos loschecks focales de1000EUR/10%/amarillo,
sharedseparado yexcludedfuera. Informe005-n3-core-checks.json en
candidate-cap5-calibration-observed conSHArecibos; no verificaentailmentdecada
cita niadjudicaciónindependiente. ÚltimoPID2642423S:63/84verificados,
60completed/3failed,008r3active. Continúa el mismocandidato bajo5USD.

### Segunda ronda cap5 congelada — 14/10/2026

28/28recibosr2 congelados fuera deGit en candidate-cap5-r2-frozen conmanifestSHA;
27completed/1failed,28verificados. MismoPID2642423S/live;002r3active. r1+r2:
56recibos(53completed/3failed),r3encurso. Ningún intento seleccionado/repetido.

005/017/026 mantienenr2 checks correctos der1 (roles/umbral/100>100falso/gasto
desconocido); checksindividuales ySHA en candidate-cap5-calibration-observed.
028r2 coincide conreplay.027r2 calcula10→6/−40% pero vuelve a
explicar conceptoFinOps conevidencevacío; dosobservaciones, noPASSdocumental ni
cambioarquitectónicoantesdefinN3. Focal027/028provisional yr2summary externos.
Siguen pendientesr3,juicioindependiente ycriteriosderevisores.

### Trello e historial real del candidato — 14/10/2026

JUP123 consultada exclusivamente con integraciónDockerServer. Tarjeta aún no
registra acuerdo derevisores; criteriospropuestos siguen pendientes. Seactualizó
sólo párrafoEstado desfasado(N3NOTRUN/tope2) a baseline84recogida/candidatoN3encurso/
autorización5USD, conservandohistorial yroles; comprobaciónprevia evita sobrescribir
cambiosconcurrentes. Readback/update externos jup123-trello-criteria-readback.json
yjup123-trello-current-status-update.json. Corte de tarjeta39/84 es histórico.

Playwright visible contra API/backend real delcandidatoB:017/026/028r1 a1280px
y390px,6checks; textocoincide normalizandoespacios,0mutacionesbloqueadas/0pageerrors;
028sección Fuentesutilizadas presente. Capturamóvil028inspeccionada legible con
fuentedocumental. Informe real-ui-current-result.json y6capturasexternas. Túnel
SSHloopback usado sólo para B; autenticacióndemo legítima sóloenmemoria, sin
credencialespersistidas. No nueva generación,pruebastreaming niaceptaciónN3.

Primer selector omitíaprefijoJUP123; segundo mostró3títuloshomónimos entrecampañas.
Corregido usando IDdeconversación delrecibo yordinaldelAPI,verificando peticiónGET
aeseID; no basta seleccionarprimertítuloigual para validarproductonuevo.

ÚltimoPID2642423S:52/84verificados(49completed/3failed),025r2active. Corte
conservador1.915786191USD+reservas1.281808USD incluyeoperaciónactiva; próximo
preflight debe volveraleer. No confundirreservas concosteefectivo ni liberar003.

### Ruta del proveedor revalidada — 14/10/2026

Readback seguro de model/info:alias economicon-chat→openrouter/z-ai/glm-5.2,
onlydeepinfra/fp4,allowfallbacksfalse,requireparameterstrue; requestcodee23 fuerza
mismaorder/temperatura0/numretries0. Reciboexternocandidate-cap5-routing-readback.json.
No seleyeron claves ensalida ni cambióconfiguración. PID2642423S,36recibos
(34completed/2failed),009r2active. Este readbackactual no es elrecibodefacturación
de cada generación; nolevanta costesdesconocidos nirevisiónsemántica.

### Contrato de contabilidad reconciliado — 14/10/2026

OpenSpec proposal/design/spec actualizados a autorización5USD, baselineN3recogida
yN3candidataencurso. Escenario de fallo terminal exige retenercotaentera yfallo,
noinferirgratuidad ni repetición, bloquearactivo/evidenciainconsistente yavanzar
sóloconcontabilidadviva+reservascompletas. ValidaciónestrictaJUP123PASS.
Herramientas e926 mantienen81testsPASS previos; no cambio deproducto/runtime.
ÚltimaobservaciónPID2642423S:33/84recibosverificados,31completed/2failed,
006r2active. No sehaevaluado semánticaN3 ni levantadopendientesderevisores.

### Primera ronda cap5 congelada y027/028 — 14/10/2026

28/28recibosr1,26completed/2failed,todosVERIFIED_PUBLIC_SNAPSHOT, recursosSHA
verificados. Congelados fuera deGit en candidate-cap5-r1-frozen conmanifestSHA;
familiasreservadas013–015/020–022 sinadjudicar. MismoPID2642423S/live,
001r2active: quedan56muestras, no aceptarN3porr1.

028r1real coincide campoacampo conreplaydeterminista:showback, calidadallocation
noevaluada, sólocita finopschunk11.027r1 aritmética10→6EUR/pedido/−40%correcta,
pero textoatribuye afirmaciones aldocumentoFinOps con response.evidencevacío;
soportedocumental pendiente, noPASSsemántico. Informefocal-027-028-provisional.json
conhashes. No retocar arquitectura poruna sola muestra ni filtrar fallos.

###005/026r1 actuales contrastados — 14/10/2026

005r1real:1000EUR elegibles,10%unallocated,amarillo; distingue explícitamente
shared/unallocated yexcluded fuera dedenominador. Provisionalconforme a requisitos
básicos; entailment decitas no adjudicado.026r1real coincide campoacampo con
replaydeterminista previo (answer/status/evidence/metrics/auxiliares): no concluye
cero nipositivo, sin citas/métricasdecorativas, insufficient_data. RecursosSHA
verificados ypublichistoryparitytrue. Evidencia en candidate-cap5-calibration-observed
conrecibos ychecks. Faltanr2/r3 yadjudicaciónindependiente; no declararPASSglobal.

Última observación del mismoPID2642423S:26recibos,026costeconciliado; servidor
continúa sin cambios. Conteos previos22/19 son cortes históricos. Mantener5USD.

###017r1 actual contrastado — 14/10/2026

Recibo e23 actual017r1 establece100>100falso,25>20verdadero,ANDfalso;
inputmatchesbank/stablesnapshot/publichistoryparity/citationknown verdaderos.
Comprobación provisional porrequisito; faltanr2/r3 yjuicioindependiente. Archivo
candidate-cap5-017-r1.json y-check.json externos, hashresources verificado.
Primera captura local porstdoutSSH fue decodificada conWindowsCP yse conserva
como -encoding-invalid.json; recopiada desdeoriginalremoto inalterado conUTF8
explícito ychecksumcorrecto. No es un defecto delproducto ni se alterórespuesta.

Controlador2642423 confirmadoS/live al corte17/84(16completed/1failed), todos
recibosverificados. Últimopreflight17:12UTC conservador1.750741071USD más reservas
pendientes0.641904USD(incluye003y017aúnporconciliar eneseinstante), máspróxima
cota0.319952 dentrode5. Son cortes históricos, no gastoactualgarantizado.

### Reanudación actual de cap5 tras OOMbackend — 14/10/2026

Controladore92628df aplicado sin cambiardiffapps frente ae23.003r1 derivado
VERIFIED_PUBLIC_SNAPSHOT mediante entradaSQLdurable; continúa failed yreserva
0.319952USD en COST_UNKNOWN_RESERVED. Archivo externo
candidate-cap5-failure003-retained.json, herramientasySHA en
candidate-cap5-operator-transfer.json. No se repitió003.

PIDresume12311135 terminó tras014r1: backend exited137/OOMtrue al límite500MiB.
Últimoledger014COST_OBSERVED0.006513180USD, sin015reservado al diagnosticar.
Recuperado sólo backendB con1024MiB/sinswap, imagen/código/volumen iguales,
composepersistido; Cockroach800MiB/processor900MiB siguen healthy. Health200 y
hashes de los tres servicios verificados antes decontinuar. No atribuir OOM a
semántica ni ocultarlo como llamadafallida inexistente.

NuevoPID2642423 confirmadoS/live, logcandidate-cap5-campaign-resume2.log;
15/84recibos:14completed/1failed,15VERIFIED_PUBLIC_SNAPSHOT,016r1active.
Snapshot externo candidate-cap5-progress-after-oom contiene agregadoPARTIAL,
69ausencias explícitas, ledger/preflight/recuperación; reserva yfamiliasreservadas
sinadjudicar. AcceptanceNOT_ASSESSED. No reiniciar porobservación lenta; inspeccionar
mismoPIDylog. El estado vigente económico sigue5USDacumulados autorizado porusuario.

### Control de fallo terminal con coste desconocido — 14/10/2026

Herramientas de evaluación añaden COST_UNKNOWN_RESERVED: fallo terminal con
entrada durable verificada yrecibo ligado porSHA, reserva original íntegra,
contabilidad real UNKNOWN. No es COST_OBSERVED niPASS yno libera presupuesto.
Prefijo admite esa disposición explícita; runner valida SHA/identidad/fallo antes
deavanzar. Recuperador sólo ofrece opt-in para404 upstream tras validar operación,
SQL,preflight yconteo defases; errores deidentidad/u otrosHTTP siguen bloqueando.
El gastoindeterminado sigue sumándose completo al próximo preflight.

81pruebas del evaluador pasan; pruebas nuevas verifican retenciónreinicio,
rechazo deactivo/incompleto,reserva parcial oidentidadalterada yavance sinrepetir
POSTdelcasofallido. Primer intento encontró importjsonausente en test ylectura
Windows noUTF8; corregidos sin modificar recibos reales. Producto e23 permanece
congelado; controlador usará herramientas posteriores porcommit/hash registrado,
sinatribuir cambios deherramientas arespuesta semántica.

### Parada verificable de cap5 por contabilidad003 — 14/10/2026

PID2240955 ausente; logSTOPPED evidence/costreconciliation. 001/002r1 completados,
recibos VERIFIED_PUBLIC_SNAPSHOT ycostes conciliados.003r1 failed(provider_error),
1intento/2fases; borradorusage0.0021540075USD, finalsinusagecompleto. Gateway
finalgen-1791993967-mgywGTZfzoVwIlPsa5lU registrado0, pero OpenRoutergeneration404.
No asumir coste0: reserva original0.319952USD sigue retenida, sin nuevo POST.
Contadoresprocessor0.577984435/backend0.0001469. Informe externo
candidate-cap5-failure003-pending.json y snapshot3recibos/ledger en
candidate-cap5-progress. 003INCOMPLETE conserva fallo; no selección demejores.

La parada es terminal delcontrolador, no sólo timeout deobservación. Siguiente
paso: reconsulta sólo lectura de la misma generación/fallo para conciliar; si
sigueindeterminado, diseñar admisión que retenga la reserva completa sin convertir
faltadeusage en coste0. No reanudar automáticamente ni cambiar producto conN3
parcial. No declarar valoración semántica concluida (2completed/1failed,3/84).

### Arranque histórico de la campaña corregida — 14/10/2026, 18:07Europe/Paris

Candidato e23e495b24fae76decacf7d030468b75cd52b5f8;plan84/N3 físicoSHA
5345066d3b87733f59d796d2d877ef48fcbc9ae58f02bb2ba6a3e2ff15132e5b,
archivo ytransferencia en candidate-cap5-transfer.json fuera del repositorio.
Build secuencial backend/processorEXIT0, hashes fuente ycontenedores verificados
(candidate-cap5-runtime-verified.json). CockroachB recuperado sólo en proyecto
exclusivo:800MB/cache64MiB/sql128MiB;backend500MB/processor900MB,cpus1, sinswap.
VolumenB original yledger conservados; claves mismas, backend0.10/processor3.50,
spend/caducidad intactos; cap5-key-budget-update.json. No renuevan vigencia.

ControladorPID2240955 confirmadoS/live, logcandidate-cap5-campaign.log. Primer
recibo001r1 VERIFIED_PUBLIC_SNAPSHOT ycoste conciliado;002r1 active. NO reiniciar
ni repetir campañas por observación lenta. Directoriosnuevos candidate-cap5-n3
/raw-api; planbaseline, e94 ycap5 cubiertos porledger común/SQL deoperaciones.
Los41recibos e94 siguen congelados yno cuentan como resultados delcandidato nuevo.

Informe candidate-cap5-live-status.json es snapshot, no garantía de actividad
posterior. Inspeccionar mismoPID/log/operación antes decontinuar. Objetivo activo,
aceptación NOT_ASSESSED. Sin publicaciónGitHub/Discord. Conservar separación
entre recogida completa, criterios acordados yjuicios externos aún pendientes.

## Corte histórico superado — 14/10/2026, 11:15 UTC

JUP-123/B activa, sin aceptación final. Producto e94f6e54 en entorno B, hashes
verificados; herramientas8215a2b7, fixture1651b8fa. Regresión1282PASS/52SKIP y
43SQLPASS por separado; no equivalen a aceptación semántica.

Campaña candidata detenida, PID491260 terminó. Corte inmutable externo
`materiales/07-evidencias/PR121-local-evaluation/candidate-budget-stop-41/`
(relativo al workspace padre): 41/84 muestras,38completed/3failed,41 recibos
VERIFIED_PUBLIC_SNAPSHOT. Incluye r1 completa y001–013r2. Ledger y preflight
congelados; manifest con SHA256 por archivo. Reserva sin adjudicar.
013r2 falló y su coste quedó conciliado por lectura:0.004260287USD; no repetido.
Tras conciliación el paso auditado rechaza explícitamente
`Insufficient budget for worst-case operation`.
Contador conservador global1.683584087USD a11:14:48UTC (no atribución exacta a B).
Más seed reservado0.002 y cota por operación0.319952 da2.005536087USD > tope2.
No reiniciar campaña, renovar claves, rebajar la cota sin demostración ni generar
más llamadas pagadas. Continuar análisis y correcciones offline. N3 incompleta;
no presentar la campaña como validación final ni seleccionar mejores intentos.

Root remoto /home/danteadmin/economicon-jup123-20261014; logs
candidate-e94f6e54-campaign-resume1.log y anterior preservados. Plan84 congelado;
evaluation-ledger.sqlite común conserva baseline y candidato. Todo coste de las
operaciones concluidas conciliado; ninguna nueva generación tras rechazo.

### Presentación navegador de replays026/028 — 2026-10-14

Frontend local Vite127.0.0.1:29770 del árbol actual, Playwright visible, API
interceptada con sesión sintética y respuestas de los replays locales originales.
026/028 a1280px y390px conservan texto tras normalizar espacios DOM;4comprobaciones,
0mutacionesAPI. Capturas replay-ui-026/028-1280/390.png e informe replay-ui-result.json
externos. Captura028móvil inspeccionada: texto legible, citas literales conservan
marcadores markdown. Primer locator exacto multilínea falló por normalización;
segunda comparación normaliza sólo espacios, no palabras ni conclusiones.

Alcance: presentación del contenido en historial simulado; NO backend/persistencia,
streaming real,metadatos source_citations ni proveedor. No convertir esta prueba
en aceptación end-to-end. RuntimeB SQL sigue detenido; no nuevo consumo ni datos
reales. Script temporal playwright-test-jup123-replay.js, fuera del repositorio.

### Alcance de la evidencia y dependenciaA — 2026-10-14

Reconsulta gh pr view130 confirma cabeza318a56f/basec30a7d0,OPEN,
CHANGES_REQUESTED; no nuevo cambio de A para reconciliar. Matriz en design.md
actualizada con308Linux+43SQL de fa5e9527. Diff apps/frontend e94..HEAD vacío;
la prueba histórica017 conserva su alcance sobre ese frontend. No repetirla
sobre e94 para afirmar validación de respuestas026/028 nuevas. La verificación
pendiente en navegador debe usar el candidato actual y datos de salida actuales.
Sigue faltando aceptación repetida del proveedor y acuerdo/adjudicación externa;
no sustituirlos por más ejecuciones redundantes de pruebas locales ya aprobadas.

### SQL del candidato actual fa5e9527 — 2026-10-14

43PASS58.30s/exit0 en test_chat_cockroach_jup035.py contra nueva instancia
exclusiva jup123-sql-fa5e-db2; DB economicon_jup035_mock_fa5e9527. SQL800MB,
cache64MiB,sql-memory128MiB; runner600MB; sin swap,red interna sin puertos,
loopback compartido sólo por runner. Primer contenedor rechazó listen0.0.0.0;
segundo usó127.0.0.1. No reiniciado ni alterado Cockroach del runtimeB.

Registro externo candidate-fa5e9527-native-result.json. Tras PASS, docker stop
-t20 terminó auxiliar con137/OOMfalse; no afirmar apagado limpio. Volumen
jup123-sql-fa5e-data y bases preservados, sin carga activa. Los43PASS acreditan
contratos JSONB/transacciones/concurrencia/migraciones del candidato actual;
no navegador,fallo de red trasCOMMIT ni calidad del proveedor. Supera pendiente
SQL descrito abajo; runtimeB sigue detenido y navegador actual pendiente.

### Preflight SQL actual — 2026-10-14

La base exclusivaB economicon-cd-d29fd64fc938-a817382bfefb-cockroachdb-1
está exited137,OOMKilledtrue,fin2026-10-14T11:43:30.664485071Z. Sin límite
Docker de memoria/swap; comando no fija cache/sql-memory. Host2392MB disponibles,
swap97MB. No reiniciada ni modificada, volumen conservado. Esto confirma cierre
por memoria, no identifica qué carga provocó la presión. Backend/processor healthy
no prueban disponibilidad SQL. Registro candidate-fa5e9527-sql-preflight.json.

Siguiente paso seguro: instancia SQL exclusiva de pruebas con límites explícitos
de memoria/cache/SQL, sin reutilizar ni alterar el volumenB, y ejecutar contratos
Cockroach del candidato actual. No se ejecutaron aún;43PASS anteriores siguen
perteneciendo a e94. Browser actual también depende de recuperación del runtime.

### Linux del candidato actual fa5e9527 — 2026-10-14

Archivo versionado fa5e952716daed10d96024e2e5aee28bf69d3f40 transferido y
verificado SHA256 fceb53cf8f55c163c2646f1024b4e766098d6fb216d7141a8a32cfcb84d225f3.
Root remoto offline-fa5e9527 bajo el entorno exclusivoB. Capacidad previa:
load1min1.22,MemAvailable2302MB; pruebas secuenciales,1CPU/1400MB/sinswap,
networknone,user10001,capdropALL,código readonly; contenedores --rm finalizados.
Processor244PASS39.56s(exit0,sesión43980): terminales026/028,premisas,005,
gateway focal y existente,segmentos,intervalstream. Backend64PASS0.70s(exit0):
booleanos e intervalos. Informe externo offline-fa5e9527-complete.json registra
archivos e imágenes por SHA; transferencia en offline-fa5e9527-transfer.json.

Supera el pendiente Linux para estas superficies actuales; no acredita toda la
suite,SQL/browser actuales ni calidad semántica real. No gasto LLM ni cambios
en despliegues. Los pendientes históricos Linuxc76 se conservan como historia.

### Auditoría de la reserva presupuestaria — 2026-10-14

Recalculada offline la reserva desde tools/chat-eval-budget.py y los parámetros
conservados en jup123-live-step.py:4intentos ×(131072tokens entrada a0.5625USD/M
+3200salida a1.8USD/M)+0.002auxiliar=0.319952USD. El snapshot histórico
11:14:48UTC más seed0.002 y esa reserva suma2.005536087USD; exceso0.005536087.
No es una lectura nueva de gasto ni de precios. Informe externo
`materiales/07-evidencias/PR121-local-evaluation/budget-admission-audit-v1.json`
con SHA del preflight. Se conserva el bloqueo; ninguna llamada pagada.

La admisión de contexto reserva salida y margen1024 por fase, pero no se ha
probado una cota menor de tokens facturados por el proveedor. No sustituir esa
prueba por el promedio observado ni reanudar las43muestras pendientes del
candidato antiguo como si validaran el producto actual. Quedan validaciónLinux
actual y aceptación repetida del nuevo candidato. La autorización vigente no
amplía el tope ni reinicia la contabilidad.

### Auditoría de preparación para revisión9f52e2cd

OpenSpec design.md contiene matriz requisito/evidencia/pendiente, sin marcar
objetivo logrado. AncestrosA318a56f/developc30a7d0 comprobados por merge-base.
OpenSpec JUP123 estricto válido y jup-cleanup1609archivosOK. Primera invocación
OpenSpec no encontró binario local; usada CLI existente del checkoutauto. Higiene
requirió permiso de ejecución para git (sandboxEPERM inicial); control intacto.
Pregunta async pendiente sobre criterios realmente acordados con Víctor/Lucía
(tarea1.4), no petición de publicación ni mensaje a revisores.

Host DockerServer:4CPU,2.9GBMemAvailable,SwapFree97MB de4GB,load9.12/247/269,
pressure memoryavg60=1.56/full0.95. No iniciar más pruebas mientras la capacidad
no sea suficiente; no atribuir causa ni modificar servicios ajenos. Sin nuevas
llamadas/transferencias. Falta Linux actual, runtime/SQL/browser del candidato,
N3/N5 dentro del presupuesto, juicios independientes y cierre de dependenciaA.

### Gateway y Linux — verificación adicional

Pruebas Linuxc76 concluidas en las sesiones originales:46770 backend100PASS
883.60s/exit0;25679 processor111PASS845.11s/exit0. No reiniciadas. Registro
externo offline-c76e4423-complete.json supera pending.json (preservado). No
acreditan los commits posteriores026/028. SSH vuelve a responder; uptime
13:45:54 muestra carga48.50/350.91/301.12, causa no determinada. Evitar lanzar
más carga remota sin comprobar capacidad; no modificar servicios ajenos.

Nueva test_chat_premise_gateway_jup123.py:12PASS usando transporte sintético
retrieval→draft→final, esquema y ensamblado público.026/028 producen candidatos;
auxiliares contradictorios fallan sin publicar candidato.3tamaños de lectura,
una búsqueda y dos generaciones simuladas, sin herramientas/reintentos ni pago.
Regresión existente gateway/auto/segments dio87PASS/9FAIL al usar python del venv
Windows: ValueError Resolver ownership protocol, antes de llegar al HTTPsimulado.
Reproducción mínima127.0.0.1 falla con lanzadorvenv y pasa con Pythonbase3.12
usando las mismas site-packages. No debilitar checkPID ni atribuir a terminales.
Repetición completa con intérpretebase en sesión8822:108PASS40.83s/exit0.
Registro premise-gateway-regression-local-v1.json. Mantener lanzador directo
3.12 y mismas site-packages para pruebas HTTPWindows; no cambiar controlPID.

###026 — falta de cobertura, terminal local y replay

chat_missing_spend.py reconoce pregunta de gasto cero y escenario explícito
consulta vacía+ingesta incompleta para el mismo mes/año. Usa premisa gasto cero
DESCONOCIDA; no infiere gasto positivo ni cifra. Sin citas decorativas o métricas.
Coincidencia de periodo obligatoria, declaración completa sin negaciones extra,
hipótesis múltiples ni condiciones añadidas. Si existe evidencia no documental
(p.ej.cost_query), no la descarta para forzar este terminal. Fuera de gramática
se conserva ruta general; no se afirma resolver universalmente preguntas de gasto.

Streaming/final y esquema usan mismo terminal ligado a hash de pregunta. El
modelo no puede añadir conclusiones/citas/auxiliares en esta ruta. Requiere
insufficient_data. Próximo paso en el propio texto: verificar/completar cobertura
y consulta autorizada del mismo ámbito/periodo/moneda. Replay con entradas026r1
originales en missing-spend-026-offline-replay-v1.json, hash de recibo preservado.
33muestras completadas de calibración inspeccionadas por router: sólo026/028
activan rutas nuevas.003r1 sin historial se registra fuera de esa comprobación;
reserva no usada. Primer script encontró ese historial vacío y se detuvo; segundo
registra la exclusión técnica explícitamente, sin tocar recibos ni resultados.

134processor/64backend PASS; carga del manifiesto backend PASS. AssemblerSHA
8373a021a8558c43d9cf745cd3b88ecb4da6f468d2a448493353cc0c96575741.
No despliegue, transferencia nueva ni inferencia.026/028 corregidos en rutas
locales reconocidas; API/modelo, Linux actual, repetición y generalización aún
pendientes. DockerServer sigue con timeout de bannerSSH; sesiones antiguas no
se reinician ni se consideran completadas. Tope2USD intacto.

###028 — terminal de reporting local y replay

Nueva ruta chat_reporting.py en backend/processor; bind_segments expone un
terminal ligado al hash de pregunta+fuente. Sólo reconoce una declaración
completa de costes mostrados/asignados a equipos/unidades con/sin repercusión
contable y una pregunta de clasificación admitida. Requiere el bloque completo
de definiciones Showback Y Chargeback con procedencia; cambios/negaciones,
fragmentos parciales, escenarios múltiples y premisas adicionales conservan
la ruta general. Limitación deliberada de gramática; no solución universal de
implicación semántica. No se deriva calidad insuficiente de calidad no evaluada.

Renderer compartido genera conclusión, incertidumbre y citas literales pertinentes;
auxiliares del modelo deben estar vacíos, impidiendo rationale contradictorio.
Esto no elimina recomendaciones generales de otras rutas.21pruebas focales,
110processor con regresiones y64backend pasan; carga backend del manifiesto pasa.
AssemblerSHA55b67ccc895cd21457632a2a22b1f3cc34730f9b0a04a3e56cb702fe3fc19e12.
Replay offline de pregunta+authorized_evidence originales028r1 produce showback,
calidad no evaluada y sólo finops11. Artefacto externo reporting-028-offline-replay-v1.json
contiene hash de recibo y resultado. No es ejecución del modelo/API, no cambia
veredictos de campañae94.028 corregido en esa ruta local; aceptación real y
variantes fuera de gramática pendientes.026 sigue abierto. Sin consumo adicional,
transferencia o despliegue de este cambio. Pruebas Linuxc76 previas sin resultado.

### Integración numérica del motor de premisas — local

El evaluador trivalente se usa ahora en render_boolean de backend y processor.
Las premisas se construyen únicamente después de evaluar expresiones y límites
verificados por el servidor; no se aceptan valores de verdad del proveedor.
Referencias internas de comparación no añaden citas al corpus. La combinación
mantiene la semántica anterior: no atribuir a este refactor corrección nueva de
026/028. Ambos módulos permanecen idénticos byte a byte entre aplicaciones.

18pruebas backend y77processor pasan. Doce pruebas de streaming cubren AND/OR,
condición absoluta verdadera/falsa con relativa indefinida y chunks1/17/8192;
streaming=final y fuentes vacías para regla del usuario. Backend carga el nuevo
manifiesto. AssemblerSHA3117e0b8242344982399f4e2270c83fc5d460428a721eadb0cdad8da410a3423.
El núcleo ya está integrado en comparaciones numéricas, NO en premisas textuales
ni recomendaciones. No transferido/desplegado, ninguna llamada pagada. Las
sesiones Linux46770/25679 previas de c76 siguen sin salida final, no reiniciadas.

### Verificación Linux c76e4423 — observación pendiente

Transferido git archive c76e4423b52a405723568a47f68343867054a861 a
/home/danteadmin/economicon-jup123-20261014/offline-c76e4423; SHA256
bd0a3d91f002d4c6c96c0ca976eaeaa3b1a68afbde3e4f3a9378834eeb2de0e1.
Registro externo offline-c76e4423-transfer.json. Contenedores sin red/claves,
montaje sólo lectura, usuario10001,cap-dropALL,1CPU/2500m cada uno:
- jup123-offline-c76e4423-backend, sesión46770: interval_rules + summary_resources.
- jup123-offline-c76e4423-processor, sesión25679: premises,resolved_classification,
  interval_stream y resources.
Ambos emitieron progreso pero no resumen ni exit; no contar como PASS. Consulta
Docker stats sesión37837 también sin resultado. Nueva conexión SSH acotada
falló durante banner exchange. No se demuestra que los contenedores acabaran;
no reiniciar por timeout. Inspeccionar mismos handles al recuperar acceso.
Artefacto offline-c76e4423-pending.json preserva observación. No atribuir causa
al código, OOM o caída del host sin evidencia. No modificar otros servicios.

PR130 comprobada de nuevo:OPEN,head318a56f/basec30a7d0,CHANGES_REQUESTED;
la review mantiene tokenizer pendiente y no valida aún criteriosA. Sin nueva
base que reconciliar. Inspección de ChatContext.billing:verifica consulta y
pantalla, pero no acredita cobertura completa de ingesta. Diseño OpenSpec
actualizado para separar query_has_rows,queried_total_is_zero,coverage y gasto
del periodo.026 hipotético no puede acceder a autoridad financiera del backend.

### Núcleo inicial de premisas — antecedente previo a integración numérica

`apps/processor/app/core/chat_premises.py`: decisión trivalenteAND/OR/NOT,
procedencia obligatoria para hechos conocidos, desconocidos explícitos, árboles
acotados y rechazo de diccionarios del proveedor. Resultado inmutable conserva
premisas desconocidas y omite fuentes de hechos no consultados.30pruebas pasan.
Diseño/enlazador/renderizado pendientes detallados en OpenSpec design.md. Los
casos de prueba026/028 modelan sus premisas, NO reproducen todavía sus respuestas
por el gateway. No afirmar corregidos esos casos. No cambia manifiesto/runtime;
ninguna nueva llamada, transferencia o publicación. Siguiente paso: binder de
hechos/reglas con alcance y soporte semántico, después terminal compartido por
respuesta y recomendaciones y replay end-to-end. No aceptar verdad del LLM
ni confundir existencia de cita con implicación. El núcleo por sí solo no evita
las citas irrelevantes del chat actual ni sus contradicciones de prosa libre.

### Comparación parcial de41muestras — 14/10/2026

Artefactos externos candidate-41-{aggregate,calibration-judgments-v1,reviewed-v1,
comparison-v1}.json y candidate-41-review-freeze-v1.json con hashes. Etiquetasr1
remapeadas sólo al coincidir hashes de evidencia y criterio; r2 revisada contra
respuesta completa, auxiliares y fragmentos originales. Reserva sin adjudicar.
Calibración r2(001–012):9PASS/2pending(004,011)/1FAIL(005). La separación shared
sigue omitida en005r2 del candidatoe94; no contiene la corrección localf4c80ebf.
012r2 reconoce allocated de forma explícita; pedir la fuente como trazabilidad
no anula la conclusión hipotética.011 mantiene9de10 sin90%porrecursos explícito:
misma incertidumbre que r1, no modificar rúbrica para obtener un aprobado.
Total41:23PASS/11pending(incluye reserva)/4FAIL/3técnicos. Faltan43muestras.
Comparación emparejada con baselinev12:136pass->pass,29fail->pass,2fail->fail,
7uncertain->pass,8pass->uncertain,1uncertain->uncertain,1pass->fail(026r1).
003r1 sigue regresión técnica;013r1/r2 son fallos técnicos de reserva sin juicio
semántico.028r1 pasa de fallo técnico baseline a fallo semántico, no mejora plena.

026: cita finops3/Inform auténtica pero sin apoyo a conclusión de ingesta vacía.
028: rationale afirma calidad insuficiente mientras limitation declara no evaluada.
Código chat_claims sólo verifica literalidad/procedencia; chat_segments valida
estructura y soporte visible, no implicación semántica ni consistencia entre
premisas. No se han corregido026/028. No introducir un filtro de solapamiento
léxico como si probase pertinencia/consistencia. Próximo trabajo de producto:
representar premisas verificadas/desconocidas y conclusiones condicionadas, con
un contrato compartido por respuesta y recomendaciones; comprobar contra estos
recibos y casos contrarios antes de integrar una ruta determinista. Mantener
síntesis útil y no sustituir el objetivo por respuestas sólo extractivas.

### Corrección local posterior al corte — separación shared/unallocated

El renderer de la partición cerrada añade explicación de los roles: shared
pertenece al denominador elegible pero no al numerador unallocated; excluded
queda fuera por la política explícita del escenario. No se aplica a totales
explícitos sin partición ni cambia cálculo, umbrales o extracción. Prueba nueva
comprueba el contenido, igualdad streaming/final y ausencia fuera de la ruta.
Backend/processor sincronizados. Contrato interval_rules v4; assemblerSHA
`d4c1f8bb5f8aea98baccb1cf5d5144b2848b6cc68546b1d24dfdedca1b16d96e`.
Processor81PASS; backend98PASS/2fallos de entorno Windows1314 al crear symlinks
en pruebas de summary v2 (no comportamiento de producto). No se omiten ni alteran
las pruebas; su ejecución Linux sigue pendiente para este candidato. Primer ensayo tras cambio de contrato detectó3 fallos de
manifiesto desactualizado; actualizado y repetido81PASS. No transferido ni
validado con modelo: las41muestras siguen acreditando e94f6e54, no esta corrección.

### Navegador — historial sin inferencia

Skill Playwright, Chromium visible, entornoB loopback29660 por SSH. Login,
lista de conversaciones, apertura017r1, recarga y reapertura verificados.
Contenido idéntico antes/después;100>100false,25>20true,ANDfalse. La recarga
limpia selección pero no pierde el historial. Captura inspeccionada visualmente:
`candidate-browser-017-top.png` en raíz externa de evidencia. Las capturas previas
history/reopened conservadas; reopened quedó desplazada a la lista. Lista larga
hace scroll de página completa. No se validó streaming nuevo ni móvil; peticiones
noGET a conversaciones bloqueadas por el script. Sin consumo LLM de navegador.
Scripts temporales playwright-test-jup123-{history,reload,reopened,top}.js.

Pendientes: resolver026/028 y dudas, validar005local, pruebas offline,
validación real restante dentro de presupuesto demostrable, criterios revisores
y reconciliación A(tokenizer/reviews). No publicar. Historial inferior conserva
cortes anteriores, superados sólo en lo descrito aquí.

### SQL nativo del candidato — 14/10/2026

43PASS en44.60s, Cockroach24.1.11; test_chat_cockroach_jup035.py con producto
e94f6e54 y fixture1651b8fa. Base nueva economicon_jup035_mock_b_e94f6e54, prefijo
exclusivo de pruebas y scopes UUID; bases creadas conservadas para inspección.
Proceso523486 y contenedor jup123-native-e94f6e54 terminados0/OOMfalse, contenedor
eliminado. Sin claves ni llamadas modelo. Registro externo
candidate-e94f6e54-native-result.json contiene log y estado Docker. Verifica
transiciones JSONB, orden publicación/commit y concurrencia; no navegador ni
calidad semántica, ni pérdida de red tras COMMIT. No alterar el conteo1282/52 de
regresión offline: estas43 estaban omitidas allí, ahora verificadas aparte.

### Observaciones preliminares del candidato

r1 completa congelada en candidate-r1-frozen/ con ledger-snapshot.json y agregado
candidate-r1-aggregate.json (PARTIAL frente al plan84,56pendientes). Primera
agregación local rechazó hash porque read_text usó encodingWindows; repetida con
UTF-8 explícito y hash físico del plan c58dcd9d verificado, sin alterar archivos.
Juicios/score candidate-r1-calibration-judgments-v1.json y candidate-r1-reviewed-v1.json:
calibración22=14PASS/4pending/3FAIL/1técnico. Reserva6 sin adjudicar, incluida013failed.
02710→6EUR/pedido/-40%PASS, fuentesfinops2/3 contrastadas.028 requisito showback
cumplido pero consistencyFAIL: rationale afirma calidad allocation insuficiente
mientras limitations dice no evaluada. Fallos semánticos005/026/028; técnico003.
No afirmar cierre ni mejora estable con r1; restantes repeticiones en curso.


Revisados023–026r1, notas externas candidate-e94f6e54-preliminary-notes-023-026.json
vinculadas a recibos.023 sin gasto Azure inventado;024 no inventa FX ni suma divisas;
025 no ejecuta cambios y ofrece análisis revisable. Hay citas truncadas y frases
fragmentadas.026 mantiene conclusión correcta pero cita finops3/Inform irrelevante:
fallo grounding confirmado, no compensado por respuesta correcta. Persisten
problemas de pertinencia documental; no cambiar código durante campaña.


Último snapshot calibration16-v1 añade016–019r1:10PASS/4pending/1FAIL/1técnico.
016:150EUR/día,37.5%,ANDtrue e investigación.017:100>100false y25%>20true,
ANDfalse.018:200EUR/día,20>20false,ANDfalse.019:150EUR/día absoluto explícito,
relativo indefinido por base0 y petición de base comparable/recurso nuevo. Los
cuatro pasan preliminarmente con fuentes del usuario, sin citas sobrantes;
respuestas/auxiliares contrastados. Artefactos candidate-calibration16-* externos.
Son r1 únicamente; reserva013–015/020–022 permanece sin adjudicar ni usar para
corregir. No modificar producto hasta acabar esta medición.


Último snapshot revisado: first12-v1,6PASS/4pending/1FAIL/1técnico; notas/juicios
anteriores preservados.010 cumple tags+reglas, contraste literal rules1/2.011
mantiene duda9de10 vs90% explícito;012 duda por pedir confirmar regla ya estipulada.
Requisitos comparados:13fail->pass,36pass->pass,3uncertain->pass,5pass->uncertain,
1fail->fail,1uncertain->uncertain;003regresión técnica.010baseline r1 técnico no
se convierte en ganancia semántica cuantificada. Artefactos candidate-first12-*
externos;72muestras ausentes de este snapshot. Reserva013–015 sin adjudicación.


Comparación offline first9-v1 (sólo001–009r1):5PASS,2pending,1FAIL,1técnico;
45requisitosPASS,3uncertain,1FAIL,5sin revisar del caso técnico. Juicios vinculados
a hashes/criterios; preliminares locales, no adjudicación independiente.
Contra baseline:13fail->pass,30pass->pass,2uncertain->pass,3pass->uncertain,
1fail->fail.003pass->technical_failure cuenta como regresión técnica; no afirmar
sin regresiones por ausencia de transiciones pass->fail.75muestras faltan en
este snapshot, aunque campaña siga avanzando. Artifacts externos
candidate-first9-{aggregate,judgments-v1,reviewed-v1,comparison-v1}.json.
00710.1%rojo y008cociente indefinido verifican correcciones en r1; no N3 completo.


Notas externas candidate-e94f6e54-preliminary-notes-v1.json vinculadas a hashes de
recibos. 001/002 cumplen cálculos requeridos;003 fallo técnico preservado.004
contiene distinción conceptual, pero cita visible parcial y formulación categórica
requieren adjudicación.005 calcula1000EUR/10%/amarillo con reglas3/4, pero no
explica expresamente shared vs unallocated: no dar required-1 por cumplido por
aritmética solamente.006 muestra5%/verde y límite inclusivo. Una repetición no
acredita mejora estable ni aceptación. No tocar código durante esta campaña ni
usar reserva para afinar correcciones. Snapshots externos first4 y005-006.

## Historial de evidencia

13/10/2026. Rama `local/JUP-035-evaluation`, referencia preservada `fc0f4697`.
No hay publicación, despliegue ni cambios en el runtime compartido.

Primer commit local `5a2bc473` ajusta sólo seis fixtures de expresiones: declara
basis/user_scenario y usa segmentos inference para la explicación. Compara el
stream con `render_response`, conservando prefijo, Unicode, cálculo y denominador
cero. No cambia producto ni preguntas/criterios de aceptación.

Archivo completo `apps/processor/tests/test_chat_expressions_jup035.py`:38PASS
con Python3.12 nativo y dependencias existentes de la copia anterior. El primer
intento no ejecutó tests por ausencia del directorio temporal padre; se creó y
la ejecución posterior terminó correctamente. Recibo local externo:
`materiales/07-evidencias/PR121-local-evaluation/fixtures-expressions.log`.

Segundo hito local: [scorer y rúbrica](../validation/JUP-035-receipt-evaluation.md),
`tools/chat-receipt-eval.py`, 11 pruebas unitarias PASS. Reutiliza heurísticas de
JUP-070 sin convertir coincidencias en aceptación. Normaliza las dos full28
históricas, conserva etiquetas antiguas, bloquea juicios sobre evidencia distinta
y compara por requisito/caso/repetición con grupos causales por respuesta.
Banco original intacto (109 criterios), más56 controles transversales provisionales.

Partición por familias: reserva013–015/020–022 en ambas campañas. No es reserva
ciega: los informes ya se conocían. Primer error de implementación (`budget` por
`budgets`) detectado por prueba y corregido antes de adjudicación. No juez LLM.
Revisados79 controles de14 respuestas históricas:010/011/017/018/024 en ambas
campañas más006/008/028 donde hay respuesta. Tresjuicios008 quedan inciertos;
resto no revisado explícitamente pendiente. Recibos/juicios externos en
`materiales/07-evidencias/PR121-local-evaluation/` (directorio hermano del proyecto):
`judgments-first.json`, `judgments-second.json`, `historical-first.json`,
`historical-second.json`, `historical-comparison.json`, `scorer-tests.log`.

Confirmados:010 omite restricciones en primera campaña y las cubre en segunda;
011 cambia reglas añadidas sin soporte por omisión del contraste90%por recursos;
017 pasa de comparación estricta correcta a activar con igualdad;018 mantiene
matemática correcta y cita sobrante en ambas;024 introduce tipos ficticios en la
segunda. Ninguna diferencia N=1 se atribuye causalmente a una corrección.
La cita sobrante018 es fallo transversal, no un requisito numérico del banco.

Backend ingeniería:68PASS (metadata/operaciones, carreras y planificador),
1957advertencias; recibo backend-engineering.log. Sin SQLCockroach real.
Suite completa processor iniciada en checkout local; consultar recibo antes de
afirmar resultado. Docker Desktop local sin daemon accesible; contexto por defecto
apunta a DockerServer compartido. No se despliega ni se modifica ese entorno.
N=3 y N=5 NOT_RUN. Pendiente completar adjudicaciones, prueba de reserva e informe
de entrega. Último gasto confirmado0,957927619; no nuevas inferencias locales.
No afirmar que38PASS u11PASS equivalen a CI completa ni aceptación semántica.


Hito siguiente13/10/2026: [informe offline](../evidence/jup-035-local-offline-review.md).
Revisadas44respuestas completas/253controles,9inciertos.12fallos técnicos sin
respuesta no recibenjuicio semántico. Reserva revisada despuésde congelar
scorer/rúbrica ycalibración;sinajuste posterior. Corpus3/3hashesidénticos albanco.
Suiteprocessor terminada:1454PASS/13FAIL/4ERROR/96SKIP en400.51s.10incidencias
resueltas en repetición con intérpretevenv(10PASS/6SKIP),sin cambiarproducto;
2fallosporprivilegios symlinkWindows y5cancelación/capacidad resumen pendientes.
Cancelación reproducida aislada; shutdownsocket retornaéxito pero trabajador
siguebloqueado antesdecabeceras. No cerrar capacidad antesdelasalida física.
Siguiente:diagnóstico/corrección acotada e informe final;N3/N5siguenNOT_RUN.

Cancelación corregida en hito posterior13/10: sólo SummaryGateway usa lectura
directa del socket con polls100ms, cancelación ydeadlineabsoluto; conservaownership
deltrabajador.90PASS de tresarchivos (los5fallos previos incluidos),4PASSsocketpair
y3PASSprobesTLSrealesloopback. No cambiarprompt/evaluador ni reiterarcampañaLLM.
Informeoffline ampliado; productoya difiere defc0f469 sólo eneste transporte.
Suitecompleta no repetida; symlinksWindows aúnlimitados. Siguiente:paquete de
medición reproducible e informe/auditoría deentrega, manteniendo N3/N5NOT_RUN.


Entrega local preparada13/10/2026: [auditoría final](../evidence/jup-035-local-delivery-audit.md).
Commits97e8e043(cancelación) y5dce752e(planesrepetidos). Planes84/140entradas
NOT_RUN verificadoscontra banco y304hashes. Paquete localincluye parchesseparados,
juicios, comparaciónhistórica ylimitaciones. Esta sección sustituye pendientes
de diagnóstico/corrección anteriores: cancelaciónya resuelta en pruebaslocales.
Sin N3/N5real, sinLinuxsymlink niaceptaciónPR. Siguiente fase requiereentorno
aislado ycriteriosdeequipo; no sepuede usaruntimecompartido anterior comobase.


## Inicio de JUP-123/B — 14/10/2026

Objetivo activo por solicitud del usuario en la tarea 01a1270c-e332-7462-9c90-706d49ade92c
(título no disponible). Rama `feat/JUP-123-chat-semantic`, base local50e169fa.
[Trello B](https://trello.com/c/TqtcumIN) actualizado a En curso mediante la
integración oficial de DockerServer. Lectura actual: A #130 sigue OPEN,
REVIEW_REQUIRED, head318a56f3; develop sigue c30a7d0f. No merge ni publicación B.

Primer cambio: `tools/chat-receipt-eval.py` admite recibos con repetitions3/5
más repetition por fila, conserva las muestras fallidas, rechaza duplicados y
repeticiones ambiguas, enumera muestras ausentes y mantiene los identificadores
históricos N1. 15 pruebas correctas con unittest (incluidas cuatro regresiones
nuevas). Las muestras repetidas de prueba son fixtures, no inferencias reales.

Pendiente: reconciliar B con la ingeniería A y develop119, colector API actual,
procedencia del runtime y contabilidad viva, congelar baseline N3 y medir antes
de retocar arquitectura. Criterios de aceptación del equipo pendientes; no
atribuir aprobación a la división A/B. N3/N5 reales siguen NOT_RUN. Gasto nuevo0;
último gasto histórico0.957927619 USD, tope acumulado2 USD. El objetivo permanece
activo; este inicio no equivale a entrega validada.


### Reconciliación local con A — 14/10/2026

Avance confirmado: incorporación local de A318a56f3 y developc30a7d0f mediante
merge, usando f63c150 como base de contenido para adiciones paralelas. Se
conserva v4, prompt y cálculos B; se incorporan CHAT_ENABLED=false, bloqueo de
rutas desactivadas, fecha de referencia119, fixtures frontend y barrera de inicio
del cuerpo en pruebas de resumen. No se ha modificado el runtime compartido.

Validación: backend107PASS (disabled, operations, metadata, context assembly).
Processor: ejecución inicial128PASS/2FAIL en184s. Ambos fallos eran pruebas
heredadas del contrato A: búsqueda nativa (etapa finish frente a candidate_json
v4) y respuesta sin evidencia. Se retira exclusivamente la prueba de búsqueda
nativa que B no ejecuta; las pruebas de truncación v4 existentes se conservan.
Unicode se adapta a respuesta sustentada y sobreescribe read1, que es la lectura
real del transporte. Repetición focal3PASS (Unicode, length y truncated_length).
No declarar suite completa verde a partir de estas comprobaciones acotadas.
Los servidores de prueba Windows imprimieron ConnectionAbortedError al cortar
sockets; no causaron otros fallos de prueba. No hubo inferencias externas.

OpenSpec JUP-123 creado y trazabilidad correcta; validación estricta73PASS.
Pendiente completar verificación frontend y otras superficies reconciliadas,
colector y baseline. Objetivo activo; presupuesto y NOT_RUN sin cambios.


### Colector de operaciones existentes — 14/10/2026

`tools/chat-eval-collect.py` implementado: sólo GET sobre operación terminal,
contexto, evidencia, historial y resultado. Snapshot estable, entrada única,
paridad pública/JSONB y separación entre fuentes recuperadas y citadas; conserva
fallos y salidas exclusivas. No invoca generación/reintentos. 8 pruebas unitarias
PASS. Scorer ampliado para impedir aceptación de recogida incompleta:16PASS.
Aún falta prueba integrada del transporte/API, agregador, runner y reserva de coste.
No declarar N3 ejecutado ni procedencia validada a partir del colector.

Lectura actual de DockerServer mediante docker ps: continúan el despliegue develop
c30a7d0f en19257 y el entorno antiguo expression28 en28657; la lista no acredita
un runtime de B591b8e19. No se han cambiado contenedores ni consultado secretos.
Sin nuevas inferencias; gasto histórico0.957927619 USD, tope2 USD. Próximo:
verificación integrada del colector y admisión de coste, preparar candidato y
entorno aislado para medir baseline sin usar expression28 como sustituto.


### Agregación y admisión de presupuesto — 14/10/2026

`chat-eval-aggregate.py` agrega recibos del mismo plan, exige conversación y
operación distintas por muestra, conserva fallos y enumera ausencias. Rechaza
selección de reintentos favorables y cambios en recursos. COLLECTED acredita
cobertura, no aceptación. Pruebas con84 fixtures, ninguna inferencia real.
Colector probado con HTTP loopback real, autenticación sintética y redirects
rechazados; no equivale aún a prueba contra el backend completo.

`chat-eval-budget.py` calcula reserva conservadora de operación:4intentos (límite
confirmado en ChatRepository), cada uno con draft1000/final2200 y suma de entradas
messages/schema; coste auxiliar adicional obligatorio. Admisión exige snapshot
reciente <=30s, ámbito acumulado, gasto no inferior al histórico, y resta reservas
pendientes. No libera una reserva de resultado desconocido.18pruebas PASS entre
colector/agregador/presupuesto. Este módulo no es contabilidad real ni garantía
operativa hasta que el runner persista reservas y vincule snapshots verificados.

Pendiente adaptador contable, persistencia/recuperación, runner, procedencia y
runtime aislado; N3/N5 siguen NOT_RUN. Ningún gasto nuevo ni despliegue. El último
turno aporta implementación y prueba; no es espera ni bloqueo del objetivo.


### Reservas duraderas y recuperación — 14/10/2026

`tools/chat-eval-ledger.py` añade SQLite fuera del checkout, transacciones
BEGIN IMMEDIATE y synchronous FULL. Guarda reserva y request_id únicos por
plan/muestra, vincula conversación y confirma DISPATCHING antes del callback de
envío. Timeout/caída no liberan dinero ni habilitan un segundo POST. Un handle
recuperado por lectura se registra sin permitir cambio de operation_id.
La contabilidad de todas las campañas debe compartir el mismo ledger.

Cinco pruebas específicas PASS: reinicio, límite compartido entre planes,
persistencia anterior al envío, timeout sin reenvío, identidad y competencia
concurrente por saldo. Primera ejecución detectó conexiones SQLite sin cerrar
(WinError32 al limpiar); corregido con cierre explícito en finally. Conjunto
actual de herramientas23PASS y scorer16PASS. Sin llamadas externas, gasto nuevo0.

No hay todavía liberación/reconciliación automática de reservas: sólo se admite
cuando la contabilidad real pruebe el coste. Persistir snapshots declarados no
los autentica. El runner y el adaptador contable siguen pendientes; NO ejecutar
N3 usando sólo este módulo o datos históricos. Objetivo activo.


### Contabilidad real consultada — 14/10/2026 01:18 CEST

Consulta de lectura mediante el script histórico budget-inspect.py ejecutado por
SSH, sin mostrar credenciales ni llamar al modelo. Recibo externo:
`materiales/07-evidencias/PR121-local-evaluation/jup123-accounting-20261014.json`.
OpenRouter usage1.092818129 USD (clave superior, no atribución exacta a la tarea).
Claves de validación: backend0.00030238 y processor0.94782955 USD; ambas caducadas
13/10/2026 21:26 UTC. No renovadas, revocadas ni sustituidas. No reiniciar
contadores para recuperar presupuesto. El entorno antiguo tampoco es candidato B.

Bloqueo de inferencias confirmado por primera vez en esta fase: credenciales
caducadas. Sigue habiendo trabajo local útil (runner, comprobación de frontend,
procedencia). No marcar objetivo bloqueado ni completo. Antes de una campaña se
necesitan credenciales vigentes conservando contabilidad y entorno autorizado.

Adaptador puro accounting_snapshot añade comprobación de caducidad/ámbito de
ambas claves y construye una cota conservadora max(uso upstream, suma gateway,
suelo histórico), sin sumarlos dos veces ni afirmar atribución exacta. Sólo
es válido si todo el gasto autorizado usa la misma cuenta OpenRouter y el runner
verifica esa ruta.6pruebas de presupuesto PASS. No consultas de pago ni gasto nuevo.


### Frontend reconciliado y transporte de ejecución — 14/10/2026

Verificación frontend B:76PASS en7archivos chat (19.55s), más TypeScript de app,
configuración Node y tests sin errores. Dependencias con lockfile congelado:
instalación offline falló por metadatos ausentes; instalación normal pasó política
de paquetes pero devolvió ERR_PNPM_IGNORED_BUILDS para openspec/esbuild. No se
aprobaron scripts. Vitest y tsc instalados funcionaron directamente. Se restauró
únicamente el cambio automático de pnpm a pnpm-workspace.yaml (placeholders
allowBuilds); no hay modificación de dependencias versionadas.

`tools/chat-eval-api.py`: cliente POST conversación/generación con formato actual,
lectura del primer handle SSE/JSON y recuperación GET /assistant/requests por
conversation_id+request_id. Rechaza identidad inconsistente y no reintenta POST.
4pruebas HTTP loopback PASS. Su generate debe invocarse desde Ledger.dispatch,
tras reserva/procedencia: no constituye por sí solo un ejecutor autorizado.
Pendiente orquestación completa y adaptador de runtime/contabilidad. Claves
caducadas siguen impidiendo inferencias; no renovadas ni gasto nuevo.


### Ejecutor recuperable conectado — 14/10/2026

`chat-eval-runner.py` conecta plan, API, reserva y recogida en pasos acotados.
Exige banco completo original y N3/N5; antes de enviar compara commit, hashes y
restricción de proveedor con la salida de un adaptador de verificación. Dicho
adaptador aún no está implementado: no usar un JSON manual como prueba real.
La reserva persiste antes de crear conversación/enviar; si la contabilidad
caduca durante creación, se detiene conservando reserva. Reinicio observa el
mismo handle, o lo recupera por request_id; jamás reenvía por timeout. Operación
waiting permanece en observación. Recibos existentes deben coincidir con ledger
y hashes; una recogida incompleta requiere reconciliación, no mejor respuesta.

4pruebas específicas PASS; conjunto herramientas33PASS y scorer16PASS. Estas
pruebas usan API simulado/loopback, no son baseline. No CLI de pago expuesta.
Faltan adaptador real de procedencia y contabilidad, liquidación de reservas con
cobertura demostrada de todos los intentos, credenciales vigentes y runtime B
verificado. N3/N5 NOT_RUN; sin gasto nuevo. No declarar entrega completa ni
bloqueo total: existe trabajo local pendiente sobre esos adaptadores.


### Candidato portable y autorización pendiente — 14/10/2026

Preparado archive f06beb9e (SHA211db404ca315b967ed348299a0a2349571d3104a055c403bba3bbb6927b7748)
y plan84NOT_RUN. Se solicitó autorización asíncrona al usuario para transferir
ese candidato y correcciones posteriores con hash registrado, crear entorno B
con volúmenes propios y dos claves24h con máximo conjunto0.90USD, conservando
el límite acumulado2USD y contabilidad anterior. Sin respuesta al registrar este
hito: no transferir, desplegar ni crear claves basándose en tiempo transcurrido.
La pregunta explica que aprobaciones anteriores estaban delimitadas a commits
de PR121 y el objetivo actual condiciona despliegue a autorización aplicable.

Auditoría de procedencia encontró1hash distinto entre working tree y archive:
partición JSON CRLF frente a LF. Corregido freezer para hashes de bytes exactos
de git archive. Nuevo candidato ccc339a3b24fde194c1be6ab809d786d055637a6;
archiveSHA44a715f5862b2921e07db9c1e5d9fe5b718f6e8bd30cd5288aeba2f862beb69f.
PlanSHA3224518f33a5c8e8b5aa7d5dd25f35f0e2a55ad1f9b426fd8abbee8b9d5dfc8f;
317/317hashes contrastados con archive,0discrepancias. Banco/prompt/producto
no modificados por este ajuste. Plan anterior superado para ejecución Linux.
Archivos externos PR121-local-evaluation/jup123-{candidate-portable.tar,baseline-portable-plan.json}.
No inferencias, ningún gasto nuevo; baseline sigue NOT_RUN. Falta además conexión
real de procedencia/contabilidad y liquidación conservadora de reservas.


### Procedencia de contenedores y conciliación conservadora — 14/10/2026

`chat-eval-runtime.py` comprueba hashes del directorio fuente y archivos dentro
de backend/processor/frontend con docker exec de sólo lectura. Backend incluye
las copias del prompt/tokenizer/summary bajo /opt; comprueba proyecto Compose,
estado running, imageID y estabilidad entre dos inspect sin leer variables de
entorno.4pruebas de transporte simulado PASS; no se ha ejecutado en un runtime B.
No verifica por sí solo proveedor, parámetros efectivos ni corpus en BD.

`completed_attempt_cost` exige operación terminal y reportes chat_review_usage
completos de todos sus intentos, no sólo el último, antes de reducir reservas.
Ledger.reconcile_cost conserva el coste observado como reserva consumida aun
si el contador upstream ya lo incluye (doble cómputo conservador). Coste superior
a reserva o intento sin reporte obliga a detener/reconciliar. Costes auxiliares
requieren prueba independiente; no asumir0si faltan. Conjunto herramientas39PASS,
scorer16PASS del hito previo. Falta conectar lectura autenticada de esos logs.

La solicitud asíncrona de autorización de entorno/claves continúa pendiente.
No usar la continuación automática como aprobación. No nuevas transferencias,
claves, despliegues ni inferencias. Este turno aporta código/pruebas útiles;
objetivo activo y baseline NOT_RUN. Candidato portable ccc339a3 sigue archivado;
las nuevas herramientas requieren congelar otro candidato al ejecutarlas.


### Lectura real de informes y puerta de contabilidad — 14/10/2026

`chat-eval-usage.py` lee docker logs del processor verificado y extrae únicamente
campos de chat_review_usage, con hash de petición/fase y contadores observados;
no guarda logs completos ni contenido ajeno. Reportes idénticos se deduplican
con contador explícito; intentos distintos permanecen separados.43pruebas de
herramientas PASS. Runner exige COST_OBSERVED antes de pasar de un recibo a
la siguiente muestra; ausencia de adaptador retorna NEEDS_ACCOUNTING.

Prueba de lectura real por SSH sobre processor histórico expression28, ventana
2026-10-13T00:00:00Z:7operaciones,7reportes de intento,7completos,0duplicados.
Sólo conteos en salida; no se transfirieron archivos ni modificó runtime. Esto
valida formato de logs, no procedencia/coste de B ni una baseline nueva. Sigue
pendiente el adaptador de costes auxiliares y la comprobación efectiva de ruta
modelo/proveedor. Gasto nuevo0 y permiso asíncrono del entorno sin respuesta.


### Auditoría del objetivo y punto de bloqueo — 14/10/2026

Estado revisado: checkout limpio en4e6096fa antes de esta nota. No hay campaña
B ejecutándose ni resultados N3/N5 reales. La solicitud de autorización de entorno
ha permanecido sin respuesta durante más de tres continuaciones consecutivas.
No equivale a aprobación y las claves de validación consultadas siguen caducadas.
Se ha agotado el avance útil previo a verificar el entorno real: añadir más
adaptadores basados en supuestos no acreditaría procedencia, costes ni calidad.
Objetivo a marcar BLOCKED por autorización pendiente, no complete ni paused.

Auditoría de alcance:
- Reconciliación A/develop: código incorporado; backend107PASS, frontend76PASS y
  tipos, processor128PASS inicial y3focales tras corregir dos incompatibilidades.
  Verificación integral/SQL/runtime de B aún pendiente; no heredar CI de A.
- Evaluación/recogida: implementadas piezas y ejecutor local; herramientas43PASS,
  scorer16PASS, lector comprobado contra7reportes históricos. No es campaña real.
- Entorno/coste: falta conectar los adaptadores al entorno aislado aprobado,
  verificar proveedor/parámetros/corpus en BD y costes auxiliares por intento.
  Las comprobaciones de archivos y reservas no prueban esos elementos por sí solas.
- Línea base N3, correcciones semánticas basadas en ella, comparación y N5:
  NOT_RUN. No afirmar mejora de017/027 ni aceptación semántica.
- Criterios de revisores y9juicios históricos inciertos: pendientes, sin
  aprobaciones humanas inventadas. Candidato final para revisión no completado.

Reanudación tras respuesta del usuario: registrar autorización exacta, congelar
nuevo plan/archive con las herramientas posteriores a ccc339a3, construir entorno
B aislado y verificar317+hashes. Consultar nuevamente contabilidad, crear claves
exclusivas autorizadas sin reset del gasto histórico, terminar adaptadores contra
ese runtime y hacer prueba integrada antes de N3. Conservar techo2USD, todos los
intentos y reservas desconocidas. No activar producto compartido ni publicar B.
Gasto nuevo de esta fase0USD. Pregunta pendiente: entorno aislado+claves24h máximo
conjunto0.90USD, candidato y correcciones versionadas con hashes registrados.


### Autorización y entorno B construido — 14/10/2026

El usuario autorizó expresamente el entorno aislado, dos claves exclusivas B
de24h y máximo conjunto0.90USD, manteniendo2USD acumulados, además de futuras
transferencias de correcciones versionadas con hash. Queda superado el bloqueo
por autorización descrito arriba. Trello JUP-123 movido a En curso mediante
la integración obligatoria de DockerServer. Sin publicación GitHub/Discord.

Candidato transferido y verificado:06a889bcf598f62cd30f52c7b5b6878b17ea307d.
Archive SHA256:365eb027a38e6ce82c3de88c2fa8210b06b0940812bc4a1a2cd4bfaf2ec5588b.
Plan N3:980c0e07e034543f6685e893ef61fc545f4099bcec015ad936e7e929ad31b267.
Ambos en materiales/07-evidencias/PR121-local-evaluation, fuera del repositorio.
DockerServer:/home/danteadmin/economicon-jup123-20261014; proyecto
economicon-cd-d29fd64fc938-06a889bcf598, puertos loopback29652–29662,
subred10.231.123.0/24 verificada sin solapamiento Docker. Se descartó
172.30.123.0/24 por solapamiento antes de crear servicios.

Build de frontend/backend/processor/migraciones/azure-cost-api terminado.
Arranque aislado iniciado (startup.log); salud todavía pendiente de verificar.
Proveedores mock durante preparación; CHAT_ENABLED=true y SUMMARY_ENABLED=false
sólo en este entorno. No claves nuevas emitidas ni inferencias de pago.
Próximo: verificar salud, contabilidad viva, claves autorizadas, configuración
real y adaptadores; ejecutar N3. Las84muestras siguen NOT_RUN.

Verificación posterior del mismo hito: todos los servicios con healthcheck
Healthy y migrador Exited; hashes de319archivos de fuente verificados y
contenido ejecutado backend102/processor93/frontend116 conforme al plan.
Evidencia remota: runtime-verification.json. Contabilidad OpenRouter consultada:
usage1.093313029USD (global, no atribución exacta a la tarea); claves anteriores
caducadas y sin cambios de gasto. Aún no se han emitido las claves B.

Preparación N3: endpoint oficial OpenRouter de GLM5.2 confirma DeepInfra/fp4,
temperatura soportada, prompt0.0000005625USD/token y completion0.0000018.
Evidencia remota provider-endpoints.json. Se fija temperature=0 en draft/final;
12pruebas de flujo PASS. Primer intento de tests bloqueado por permisos tmp,
repetición con acceso autorizado pasa. Requiere nuevo candidato antes de N3.


### Entorno real B, corpus y primer rechazo de admisión — 14/10/2026

Turno previo clasificado progreso: entorno construido y hashes contrastados.
Candidato vigente a817382bfefb8ca9bd903d1c3d4d07cce8b2e272 (temperatura0);
archive e995d05f1cd7e910712cbc5fe474caefcd2f8c677ba78ac8eda9705505d61138,
plan28cf8170213a8fc546d7d565f12d75d5b7f5f93ff018e1ddc37bcceb668b7e56.
Build y hashes319/3servicios verificados en DockerServer; anterior stack B
mock detenido únicamente, otros despliegues intactos. Proyecto vigente
economicon-cd-d29fd64fc938-a817382bfefb, mismo root/puertos propios.

Claves B emitidas con autorización: backend0.02USD/processor0.88USD, caducan
2026-10-15T08:02:20Z. Referencias privadas bajo root remoto, nunca valores en
documentación. key-provision-evidence.json registra políticas y consumo
OpenRouter global previo1.093313029USD, referencia conservadora no atribuida
exactamente a tarea. Proveedores reales conectados sólo en este entorno.

Corpus original cargado: rules12, finops19, product9fragmentos (40total),
hashes documentales originales verificados, dimensión1536, tenant-core.
Una llamada embeddings,4808tokens, coste observado0.00009616USD; evidencia
seed-result.json y reserva persistente0.002USD en evaluation-ledger.sqlite.
No repetir seed: reserva corpus-original-jup069/seed-once permanece conservadora.

Dos incidencias previas a inferencia del chat:
1. Plan leído localmente sin encoding UTF8 provocó mojibake al serializarlo
para transferencia. Banco original intacto; validate_plan rechazó. Corregida
copia remota por bytes exactos; hash del plan verificado antes del siguiente envío.
2. Primer POST de generación respondió413: CHAT_CONTEXT_TOKENS32768 no admite
la reserva adicional32768 del draft más prompt/schema/output. Conversación
7f4b3b24-e9ce-4076-a7b7-5499b7ca3472; request
c59429db-b02b-48da-a4c6-9d159f083b6c. GET /assistant/requests no contiene
operación de esa conversación; first-admission-rejected.json y logs413.
Ledger conserva DISPATCHING sin operation_id, reserva0.172496USD. No rePOST
ni crear muestra nueva hasta conciliar explícitamente este rechazo; no fue
un fallo semántico del modelo. No liberar reserva por mera ausencia del handle.

Se corrigió configuración aislada a CHAT_CONTEXT_TOKENS65536 en backend y
processor; reinicio lanzado, comprobar context65536-startup.log y estado real.
Próximo: conciliación del rechazo con contabilidad/logs, reserva actualizada
para65536, conectar adaptador persistente de recogida/costes auxiliares y
ejecutar N3. Baseline0/84 recogidas; no inferencia chat realizada aún.
El plan original y todos los intentos previos se preservan, sin best-of.


### Primera muestra real y campaña secuencial activa — 14/10/2026

Reinicio65536 confirmado Healthy. Reconciliación del413: API volvió a confirmar
ninguna operación para la conversación; ledger conserva fila requestc59429db
como ADMISSION_REJECTED, sample_id terminado :admission413, original_sample_id
y evidencia dentro de reservation. No se borró el intento ni se liberó dinero:
reserva0.172496USD sigue retenida. No es una repetición semántica seleccionada.

Primera muestra JUP-069-001:r1 completada y recogida, operación
bb541fbe-81f4-4754-bdaf-ae0e4d31cd13, un intento/dos fases.
VERIFIED_PUBLIC_SNAPSHOT, respuesta1000EUR/VM600EUR/60%, hipótesis claramente
marcada; aceptación semántica aún no adjudicada. Coste chat0.005899560USD y
embedding backend0.00000138USD, total0.005900940USD. Informes por fase y
contadores de claves exclusivas coinciden; COST_OBSERVED persistido.
Contadores B tras esta muestra: backend0.00000138, processor0.00599572
(incluye seed0.00009616). Evidencia local fuera del repo:
materiales/07-evidencias/PR121-local-evaluation/jup123-first-real-evidence.json.

Harness operador reutilizable en esa misma carpeta: jup123-live-step.py.
Verifica hashes/servicios/modelos/precios/contexto antes de cada envío;
reserva máxima65536tokens/fase/4intentos0.319952USD. Costes auxiliares mediante
delta backend exclusivo, todas las fases mediante logs más delta processor.
No admitir siguiente muestra sin conciliación. Falta llevar este adaptador
a herramienta versionada general y cubrir fallos contables con pruebas.

Campaña remota iniciada: root/home/danteadmin/economicon-jup123-20261014,
campaign.py/live-step.py, campaign.log, PID3684299 confirmado vivo al cierre
de esta comprobación. No reiniciar por timeout de observación. Último estado:
1recibo completed/84; operación2 activa66448aa3-31bb-4d67-8587-0f72909712fb.
Bucle secuencial con pausas10s sólo de observación y parada ante cualquier
error/gate. No publica ni cambia despliegues ajenos. Revisar estado real, log
y ledger antes de retomar; si termina, diagnosticar antes de relanzar.

Limitación presupuestaria conservadora: ledger aún cuenta coste observado
además del contador upstream y retiene reserva del413 y seed; puede detenerse
antes de84aunque haya saldo real. No elevar límite ni borrar reservas para
forzar campaña. Implementar conciliación acreditada si ocurre, conservando
historial, sin asumir coste cero ni descargar cargos aún no observados.


### Retraso de contador y contexto RAG posterior — 14/10/2026

PID3684299 ya terminal/missing,2recibos completed: el contador gateway aún
no reflejaba todos los cargos al conciliar muestra2. Lectura posterior concilia
sin generación adicional. Harness distingue AccountingPending cuando delta
processor<coste de todas las fases; salida WAITING_ACCOUNTING sólo relee.
Exceso/discrepancia sigue siendo error. Reanudado PID3699466 tras confirmar
terminación anterior, conservando ambos recibos.

Se guardaron2recibos en materiales/07-evidencias/PR121-local-evaluation/
baseline-receipts y agregado/score baseline-partial-02*.json:2/84,82ausentes,
14requisitos sin adjudicar. No es aceptación ni N3 completo.

Hallazgo real de colector: GET operación/evidence devuelve contexto inicial
(canonical_input), no authorized_evidence añadido por tool_extension. El
manifest final sí guarda evidence_ids y tool_result.content_sha256/omissions.
Se recuperaron3snapshots exactos SIN nuevas inferencias: leer document_chunks
y knowledge_documents del tenant-core por los IDs ordenados del manifest,
comprobar hash del documento contra banco original, construir título y spans
con DocumentCitations y campos exactos de chat_context.retrieve; serializar
escaped({'evidence':corpus,'omissions':manifest.tool_result.omissions}).
Los3hashes resultantes coinciden exactamente con content_sha256 registrado.
Sidecars remotos root/retrieval-evidence/JUP-069-00N-r1.json. No se sustituyeron
recibos públicos ni se fingió que el endpoint devolviera esos fragmentos.

Última comprobación: PID3699466 missing, campaña detenida explícitamente con
NEEDS_EVIDENCE_RECONCILIATION en003:r1.3recibos completed; tercero INCOMPLETE
por citation_ids_known=false, demás verificaciones true. Sus citas finops
chunk9 y chunk14 SÍ figuran en snapshot RAG reconstruido y verificado.
No repetir la generación. Próximo: corregir colector/normalizador para admitir
snapshot suplementario validado por hash, conservando recibo inicial y trazando
derivación; pruebas de fuente manipulada/cita desconocida. Conciliar coste003
antes de reanudar desde su ledger. Campaña ahora detenida, no describirla activa.
También pendiente mejorar conciliación de reservas ya contabilizadas sin
eliminar evidencias ni superar2USD. Objetivo incompleto; no bloqueo externo.


### Recuperación trazable implementada y N3 reanudada — 14/10/2026

Commit local f129f8b8 añade tools/chat-eval-retrieval.py y6tests. Conjunto
herramientas49PASS. Sólo herramientas suplementarias transferidas a
root/evaluation-tools-f129f8b8, archive SHA256
493715063cc99e5bd3e36aaddf4bb159da707be529a657c34f949b349dfe765c.
Código del chat medido sigue a817382b y plan28cf8170; no se alteró el runtime.

Tres recibos derivados recuperados: originales íntegros en baseline-raw-api/,
vistas en baseline-n3/ con derivation/original_row_sha256/tool_sha256 y snapshot
suplementario. Recursos API originales inalterados. Coste003 conciliado sin
nueva inferencia, operación76acbb07-816a-42a0-ba1f-00d4f1ec79e0.
Harness local fuera del repo: materiales/07-evidencias/PR121-local-evaluation/
jup123-recover-retrieval.py; copia remota recover-retrieval.py. Consulta sólo
corpus sintético tenant-core, compara hashes documentales y payload final.
Actualmente exige evidencia inicial vacía (se cumple en estas muestras); si
aparece otro contexto, detiene y exige adaptar en vez de ignorarlo.

Tras verificar PID3699466 missing se reanuda PID3748498 desde cuarta muestra.
Bucle ejecuta recuperación antes de cada paso, parada en cualquier discrepancia.
Contadores eventualmente rezagados causan WAITING_ACCOUNTING, sólo lecturas.
Revisar proceso/log actuales antes de cualquier relanzamiento. Criterios
semánticos, N3 íntegro, comparación/correcciones y N5 siguen pendientes.

Comprobación posterior del mismo hito: PID3748498 estadoS (vivo),5/84recibos
recogidos; última acción WAITING_ACCOUNTING de005, sin nueva generación mientras
se espera el contador. No confundir recogida con aceptación semántica.


### Fallo010 y cargo upstream omitido en gateway — 14/10/2026

Turno previo fue progreso. PID3748498 confirmado missing/STOPPED tras10recibos:
9completed y010failed. Fallo real: diagnóstico processor rendered_text_limit
en provisional_answer; el proveedor terminó final por length (2200tokens).
No se repitió ni sustituyó el fallo. Operacióndb582481-85a6-403d-acf0-d7d909f8ad08,
intento d498348c-685c-4b37-8c4c-ad37916bf749. Reporte SDK parcial:2fases
intentadas/1reportada,0.0024870075USD; nunca se convirtió en reporte completo.

Gateway /spend/logs filtrado por clave exclusiva B proporciona IDs y ventanas:
draft gen-1791966533-LpyAz7eiQYp1VGQwp3kb,
final gen-1791966547-A2ZEJfg6TGC1GC7MtWy6. Gateway marcó final0USD al cortarse
stream, pero GET OpenRouter/api/v1/generation confirma0.005041027USD,
DeepInfra/z-ai/glm-5.2-20260616. Draft upstream0.002487007USD (redondeo);
se conserva mayor coste gateway0.0024870075. Auxiliar backend0.00000082USD.
Coste conservador total010:0.0075288545USD, retenido en ledger COST_OBSERVED
mediante upstream_reconciliation separado. Reservas/cargos anteriores intactos.
Evidencias remotas: gateway-spend-B.json (sólo campos seguros),
case010-upstream-cost.json, case010-durable-input.json. Sin credenciales.

El historial público omite preguntas fallidas: input_matches_bank era falso
por ausencia, no por pregunta distinta. Consulta SELECT acotada por
operation_id+tenant-core a chat_operations confirmó question_content exacto,
identidades, estado y único intento. Se preservó recibo original en
baseline-raw-api/JUP-069-010-r1.json y derivado con durable_input_supplement,
original_verification y accounting_supplement; estado failed intacto. Esto
verifica el fallo/entrada, no genera respuesta ni aceptación semántica.

Reanudación desde011: PID3804917; no relanzar sin comprobar proceso actual.
Si otros fallos interrumpen stream, no asumir cargo0 ni inventar tokens:
leer logs de clave exclusiva y confirmar generaciones en upstream. El gate
sigue usando gasto upstream y reservas conservadoras bajo2USD. Falta
generalizar y probar esta conciliación operativa de fallos en herramientas.


### Primera adjudicación por requisito y diagnóstico006 — 14/10/2026

PID3804917 verificado vivo al inicio (11recibos) y al final (estadoS,19recibos:
18completed/1failed,020:r1 activo d7c0874d-87d7-4ec5-b4ff-37357cfe3db1).
No relanzamientos ni nuevas llamadas manuales. Se descargaron12derivados
verificados a materiales/07-evidencias/PR121-local-evaluation/baseline-derived/.
Agregado baseline-derived-12.json, score, judgments y reviewed en misma carpeta.
No sobrescribir baseline-receipts/ anteriores, que conservan vistas previas.

Adjudicación preliminar local, no humana ni independiente, de006y011:4FAIL,
5PASS,1uncertain; los4FAIL pertenecen a UN solo grupo causal en006, no cuatro
regresiones independientes.010 sigue technical_failure; resto pendiente.
006 se abstiene afirmando necesitar regla completa, pese a recibir rules3/4
con formula y partición completa verde<=5/amarillo(5,10]/rojo>10. Ejecución
offline de documentary_rules sobre los fragmentos exactos devuelve1regla.
Reconstrucción de context_quantities con pregunta original+RAG verificado:
1regla aplicable, required_classification=True, numerador50EUR anclado
unallocated. chat_segments.py líneas150–158 mantiene CLASSIFICATION_ABSTENTIONS
aun cuando required_classification es true. Es una ruta permitida por esquema,
no ausencia del documento. No se modificó aún producto/prompt de baseline.
Próxima corrección debe cerrar decisión determinista cuando numerador Y
denominador estén inequívocamente fundados, conservando abstención en ambigüedad.
No basta con prohibir toda abstención porque required_classification sólo
prueba actualmente unicidad del numerador, no del denominador.

011 calcula10% por coste y dice9de10recursos;90% se atribuye correctamente al
gasto incumplidor. El requisito de contraste explícito por recursos queda
uncertain:9/10puede satisfacerlo semánticamente. No convertir diferencia de
redacción en fallo automático ni cambiar banco para mejorar nota. Fuentes y
campos auxiliares revisados; razones/hash de requisito/evidencia en judgments.
Campaña N3 sigue incompleta y no hay conclusión de estabilidad ni comparación.


### Umbrales017/018 y corrección UTF8 local — 14/10/2026

PID3804917 verificado vivo; corte final26recibos (25completed/1failed), siguiente
operación activa dd160be4-2e53-4eab-b395-b9d486f83997. No se relanzó campaña.
Contabilidad consultada en corte previo: OpenRouter global1.197967359USD,
backendB0.00002626/0.02 y processorB0.099588355/0.88; reserva conservadora
0.599006182 incluía operación en curso, cargos ya observados y413 retenido.
No atribuir contador global íntegro a B. Puede exigir conciliación antes de84;
no eliminar reservas ni subir tope para forzar ejecución.

Se descargaron23recibos derivados inmutables y generaron baseline-derived-23
(agregado,score,judgments,reviewed) fuera del repo. Juicios de006/011 trasladados
del agregado12 sólo tras verificar igualdad de evidence_sha256 y requisitos.
017:r1 y018:r1 adjudicados PASS preliminar local por requisito: comparadores
estrictos y AND correctos,100EUR/dia/25% y200EUR/dia/20%, sin citas ajenas ni
afirmar que no quepa investigar bajo otra regla. No generalizar a N3 o al
modelo por esta repetición. Resumen23:2PASS,1FAIL,1technical_failure,19pending;
18requisitosPASS,4FAIL(un grupo006),1uncertain,114unreviewed.

Defecto confirmado en notas deterministas: cinco literales de chat_segments.py
tenían mojibake (metricas/clasificacion/unicamente/seccion/formula/condicion/
numerico). Corrección local6017cb73 en backend y processor, copias byte-idénticas.
38pruebas existentes de segmentos PASS. No se transfirió ni desplegó la
corrección: runtime y baseline siguen a817382b. Preparada para candidato
posterior a baseline, manteniendo procedencia clara. No modifica comparadores,
esquema de decisiones ni reglas; corrige sólo texto visible fijo.


### Primera repetición íntegra y segunda en marcha — 14/10/2026

PID3804917 terminal confirmado:28recibos r1,26completed/2failed (010y028).
028 operaciónabd4513c-7aab-42d2-8ea5-278e7643846e, intento
990b4e5c-dca7-4147-bc68-070979d618e9; SDK2fases completas0.00454074USD.
SQL acotado confirma entrada exacta e ID del intento; current_attempt_id
público null se conserva, copia sólo para validar coste usa último ID durable.
Delta clave processor coincide; auxiliar0.00000084,total0.00454158USD.
Original028 guardado baseline-raw-api; derivado conserva failed y suplementos
de entrada/coste. No repetir fallo ni etiquetar completado semántico.

Reserva413 de0.172496USD conciliada a0 sólo después de SELECT count(*)=0
para client_request_id+tenant y prueba independiente: contadores exclusivos
antes del primer chat real eran backend0/processor0.00009616, exactamente el
seed ya registrado. Estado reserva VERIFIED_NO_DISPATCH_COST, importe máximo
anterior e historial intactos. Ningún gasto consumido se redujo o reseteó.

Primera repetición consolidada local:28recibos en baseline-derived y archivos
baseline-r1-complete{,-score,-judgments,-reviewed}.json en carpeta de evidencia.
El agregado conserva repetitions3,56muestras aún ausentes (no se finge N3).
Juicios23 anteriores trasladados únicamente con igualdad de hashes de evidencia
y requisitos:23pending,1FAIL006,2technical_failure,2PASS017/018.
027:r1 contesta10y6EUR/pedido,-40% y mejora unitaria, con límites expresados;
su adjudicación completa permanece pendiente, no extrapolar a repeticiones.

Segunda repetición reanudada PID3888175 y comprobado vivo estadoS. Último corte:
29/84recibos,002:r2 activo9a93a6ae-f387-4d4a-849f-077dbeca82e6. Mismo código
a817382b/plan/prompt/corpus;6017cb73UTF8 sigue sólo local. Techo2USD vigente.


### Segunda repetición y diagnóstico de operandos — 14/10/2026

Campaña PID3888175 comprobada viva; corte observado41/84recibos,013:r2
conciliado. Recogida posterior local42recibos en baseline-derived, preservando
los ya existentes. No se relanzó ni cambió el runtime a817382b.
Consulta remota: contador global OpenRouter1.28703508USD (incluye historial,
no atribuir íntegro a B); claves B backend0.00004834 y processor0.193221505.
Límite2USD y reservas conservadoras permanecen intactos.

Revisión preliminar local de024:r1 y027:r1 guardada en
baseline-r1-judgments-v2.json y baseline-r1-reviewed-v2.json, fuera del repo.
024 mantiene monedas separadas y pide destino/tipo/fecha.027 calcula10→6
EUR/pedido y−40%, sin equiparar eficiencia unitaria a gasto absoluto.
R1:4PASS preliminares(017/018/024/027),1FAIL006,2fallos técnicos010/028,
21pendientes; requisitos32PASS,4FAIL(un grupo causal006),1uncertain011,
128sin revisar. No son adjudicaciones humanas independientes ni aceptación.

006:r2 reproduce la abstención falsa sobre ausencia de regla, operación
4fee6392-9e8f-4289-aed6-497896382c68. Reproducción offline con su recuperación
exacta: documentary_rules detecta regla completa, applicable_rules una regla,
required_classification=True. El catálogo liga50EUR a unallocated, pero1000EUR
queda anclado a las palabras «escenario sintetico con», sin reconocer elegibles.
Confirmado problema adicional de extracción de denominador; no basta eliminar
la abstención del esquema. Próxima corrección debe demostrar numerador,
denominador elegible, moneda compatible y ausencia de ambigüedad antes de
forzar clasificación. No se ha implementado aún esa corrección semántica.


### Corrección local de006 y parada verificable en021:r2 — 14/10/2026

Implementado resolved_classification en chat_rules.py, igual en backend y
processor. Gramática cerrada para total elegible explícito en español/inglés;
exige regla completa única, numerador único, dos importes, moneda compatible,
0<=numerador<=denominador y denominador positivo. Cantidades repetidas,
monedas distintas, total sin etiqueta o componentes adicionales conservan
abstención. No suma componentes ni inventa denominadores. No es un parser
universal: otras formulaciones siguen por la ruta anterior.
Cuando se demuestra la vinculación, el esquema fija el árbol de clasificación,
retira la abstención y el renderer rechaza operandos alternativos/abstención.
La pregunta original se conserva sólo en el catálogo en memoria.

13pruebas nuevas y135focales PASS (expresiones, intervalos, documentos,
segmentos y nuevas salvaguardas). Pytest requirió ejecución fuera del sandbox
por permisos de carpetas temporales Windows; aviso conocido PydanticV1/Python3.14.
Reproducción offline con recuperación exacta de006:r2 produce50/1000*100=5%,
verde. Evidencia externa case006-resolved-offline.json con hashes de código y
recuperación. No es campaña del modelo ni sustituye los fallos de baseline.

PID3888175 ya ausente, log terminal STOPPED NEEDS_EVIDENCE_RECONCILIATION.
021:r2 operación47fc9d18-000e-415d-ac43-ef1b07060cc2 failed/provider_error,
current_attempt_idnull, input_matches_bankfalse porque historial omite fallos.
49muestras alcanzadas (r1completa+r2hasta021); no reanudado. Próximo paso:
consultar entrada/intento durable por SQL, conciliar SDK y coste upstream como
028, conservar fallo original y sólo entonces continuar. Runtime siguea817382b;
corrección006 únicamente local, sin transferencia ni llamadas adicionales.


### Conciliación021:r2 y verificador de fallos — 14/10/2026

021:r2 conciliado con SQL tenant-core: entrada exacta y único intento
35212c7e-9a2f-4425-884b-c95dbcb2844c. SDK incompleto2fases/1reportada.
Gateway final0, pero OpenRouter gen-1791968330-u3Tl6RQpMOGieFqtQsnW cobró
0.00175269USD. Draft gen-1791968325-oBA0RxyoAmcpNBIyyjCo se conserva al máximo
SDK/gateway0.0018723075. Auxiliar0.00000152; total0.0036265175USD.
Reserva COST_OBSERVED con reportes parciales originales y reconciliación
upstream separada. Recibo original preservado baseline-raw-api; derivado sigue
failed, sin falsear current_attempt_idnull ni reemplazarlo por una repetición.
Evidencias remotas case021-r2-{durable-input,usage,upstream-cost}.json.

Diagnósticos acotados:021:r2 calculation_free_numeric_equation_forbidden en
provisional_answer;028:r1 recommendation_documentary_support_required en
model_validation. provider_error público no demuestra caída del proveedor:
en estos casos identifica salida inválida para el contrato local. Mantener
validadores; corregir generación/esquema con evidencia, no suavizar criterio.

Nuevo tools/chat-eval-failed.py commit90e78975 verifica suplemento SQL scoped
a tenant e identidades, entrada literal, intentos y recursos públicos estables;
preserva failed y hashes, no concilia dinero ni certifica autenticidad de un
archivo arbitrario.6pruebas nuevas y55herramientas chat_eval PASS.
Aún no transferido/integrado en el adaptador remoto; próximo paso automatizar
recogida+conciliación segura para no repetir manipulación operativa por fallo.

Reanudado PID4003140 sólo después de conciliación021. Ahora PID ausente y log
STOPPED NEEDS_EVIDENCE_RECONCILIATION:022:r2 failed/provider_error operación
c08af9da-a6da-4e55-b692-77198d3d1de8, requesta8f0dd10-bbed-40d8-bd4d-640fd9586165,
conversación0f98356e-b2ff-4a0e-95cf-2b57c22097ea.50/84muestras alcanzadas.
Entrada faltante en historial, stable_snapshottrue y sin errores HTTP.
No reanudado después de022; falta su entrada durable, diagnóstico y coste.
Baseline siguea817382b y corrección006 locald6aba1b6 sin desplegar.


### Conciliación automática aislada y reanudación — 14/10/2026

Añadido tools/chat-eval-recover-failed-runtime.py: sólo última operación
exclusiva, terminal failed, un intento, fuente SQL tenant-core y hashes/IDs del
plan y reserva; verifica backend contra manifiesto antes de leer. Consulta
costes OpenRouter por cada request_id del gateway desde preflight; exige
DeepInfra/GLM, número de fases, delta de clave conciliado y cargo dentro de
reserva. Conserva máximo gateway/upstream, recibo original, fallo y SDK parcial.
No reenvía preguntas ni elimina cargos. Discrepancias detienen ejecución.
Primera ejecución paró antes de mutar por importes JSON float frente a contrato
Decimal string; corregido713c42dc.022:r2 conciliado0.005868985USD con prueba
failed-reconciliation-c08af9da-a6da-4e55-b692-77198d3d1de8.json en servidor.

Controlador versionado tools/chat-eval-campaign-runtime.py commitc484ba7c
recupera RAG y fallos antes de cada paso del runner. Transferencia git archive
SHA256000641ebce2ef93a2a7be8f9d1f9bb357e7017f2e00d28173b4ab4a204cdebdd
al directorio evaluation-tools-c484ba7c; producto baselinea817382b sin modificar.
Transferencias previas: b1ac1fc7 SHA097bc09c013a7dea070480c85c86cb17e35c000154be2f9307d12e6655aae879;
713c42dc SHA933e70519e5dd8212b11616923e11fb1ae909aa312633331297ac1771a430661.
Recibos locales failed-tools-transfer-*.json en carpeta de evidencia.

PID4055211 confirmado vivo estadoS:023:r2 recogido/conciliado,024:r2 activo
b377aa13-d749-45c5-8e64-5cc4343d0ccd.51recibos alcanzados; N3 incompleta.
Pruebas del controlador0f35402c: no despacho tras fallo de conciliación,
parada al terminar y orden de reconciliaciones antes de observar.58pruebas
herramientas PASS. No se han transferido nuevos cambios de producto ni tocado
límites; todavía falta finalizar baseline, adjudicación y comparación semántica.


### Citas de tablas y comparación preliminar r2 — 14/10/2026

Runtime permanece a817382b. Contador global consultado1.344617407USD;
claves backend0.00006366/processor0.24673444 (corte55recibos, no coste final).
PID4055211 vivo al último corte:008:r3 recogido y conciliado,64muestras
alcanzadas. Hubo WAITING_ACCOUNTING y después conciliación sin nueva generación.

Corte inmutable local snapshot-60 con agregado,score,judgments,reviewed:
60/84muestras,24faltantes. Juicios anteriores r1 trasladados sólo con hashes
iguales; r2 revisados006,010,017,018,024. Preliminar local:7PASS,3FAIL,
4technical_failure,46pending;54requisitosPASS,10FAIL,2uncertain,288unreviewed.
No aceptación ni estimación fiable de tasa global; faltan adjudicaciones.
006 vuelve a abstenerse;017/018 respetan comparadores estrictos y024 no inventa
FX.010 omite owner-equipo/PII y cita una frase ajena al etiquetado.

Causa parcial010 confirmada: chunk rules1 tiene la tabla completa de cinco tags,
pero passages() descartaba su bloque por encabezado/longitud y sólo ofrecía
una frase sobre funciones fuera del MVP. Corrección localb75b3cdb agrega filas
Markdown literales cuando un separador fija el número de columnas; rechaza
filas incompletas, anchos distintos y filas largas sin truncarlas. Backend y
processor idénticos.109pruebas focales PASS. Evidencia externa
case010-table-passages-offline.json: las cinco filas exactas quedan seleccionables.
Esto corrige disponibilidad, no garantiza entailment/selección del modelo.
Recuperación de reglas restantes (chunk2) y uso correcto de citas pendientes;
no presentar010 como resuelto. No transferido/desplegado cambio de producto.


### Admisión sin duplicar cargos conciliados — 14/10/2026

PID4055211 terminal confirmado tras008:r3 (64recibos). Gate anterior sumaba
contador global1.386110415 + reservas0.298203837 + próxima cota0.319952 =
2.004266252USD. Reservas incluían64COST_OBSERVED y seed0.002; no era gasto
real2USD ni un fallo de producto. Todo el historial permanece sin modificar.

Cambio6a90e65a opt-in complete_ledger_history en budget.admit: si el historial
completo está auditado, compara max(contador global,0.957927619 histórico+
cargos conciliados) + reservas no conciliadas + cota próxima. Ambos primeros
son límites superiores independientes del gasto de tarea; evita sumarlos.
No se afirma que el proveedor ya refleje cada cargo, no se ponen reservas a0,
no se borra dinero ni se modificaCAP2USD. Sin opt-in se conserva fórmula anterior.
Identidad del conjunto de request_ids y suelo histórico comprobados. Pruebas
cubren contador retrasado, identidad/suelo incorrectos, cargo retenido y reserva
desconocida completa;62pruebas herramientas PASS.

chat-eval-covered-step.py audita en cada preflight que el libro es prefijo
completo del plan, operaciones anteriores conciliadas, seed0.002 y413verificado
intactos, y conjunto de IDs igual a TODAS las operaciones tenant-core del backend
B aislado verificado. Esta auditoría más exclusividad de claves B sustenta el
opt-in; si se usa otra ruta/clave/historial debe invalidarse y detenerse.

Transferencia git archive6a90e65a SHA
14f612186e9b93a580dddbb591e3839787754f60eb038fc6ebbf7d262a414bdd,
directorio evaluation-tools-6a90e65a. Adapter original/producto no modificados.
Auditoría real superada y009:r3 iniciado d7da6808-df7f-4d74-9752-1595eefca665.
Nuevo controlador PID4127622 vivo confirmado estadoR, usa --covered-step.
Baseline producto siguea817382b. Recuperación de chunk2 para010 pendiente;
este turno resolvió primero el gate contable que impedía completar la batería.


### Continuidad documental bajo recorte y conciliación multiintento — 14/10/2026

Aclaración causa010:r2: tool_result.omissions declara4fragmentos omitidos por
context_budget de8recuperados; no era ausencia en búsqueda. Primarios precedían
a todos sus vecinos y el recorte de cola eliminaba continuación.1fe1ebb2 agrega
contiguous_priority: sólo reordena seleccionados autorizados, cada primario con
siguiente/anterior inmediato antes de restantes; sin nueva búsqueda, recursión,
ampliación de límites ni IDs adicionales. Mantiene conjuntos y unicidad.
Contrato assembler actualizado para ordenación y clasificación006; SHA
1239d94e0434e191a9aadcec85a23810fe735dc1cb3ad015de3a22ab708900e4.
Manifest v3, backend pin y fixture de contrato processor sincronizados.

Primer ensayo backend con Python3.14/tokenizers0.23.1:18fallos de contrato,
27PASS; no se rebajó la comprobación. Se reutilizó entorno existente
../tfm-economicon-jup035-auto/.venv/Scripts/python.exe (3.12,tokenizers0.22.1).
Resultado backend vecinos+ensamblado45PASS. Processor inicialmente detectó
fixture con identificadores anteriores; actualizados explícitamente a contrato
nuevo, recursos+presupuesto+clasificación+citas88PASS. Correcciones sólo locales;
no equivalen a revalidación real con modelo ni prueba SQL de recuperación completa.

Baseline llegó a020:r3 (76/84), PID4127622 ausente con parada verificable.
020operaciónec8b2c8b-2e14-4835-90a4-e878c9d6a13a tuvo2intentos:
3b464f09-acba-4ff4-afab-c752942e89a5 y4e89e6b2-70d1-4983-9c0f-30b01bf5d347.
Adaptador antes limitado a1 se detuvo correctamente.abe8b49a amplía conciliación
hasta4 exigiendo conjunto exacto de intentos y todas las fases/costes; faltantes,
duplicados, importes inválidos se rechazan.65pruebas herramientas PASS.

Transferencia versionadaabe8b49a SHA
2651cc8769cbf357c6f8c47d20d53b449ec675261658534ed34bbafda4d774e0
al directorio evaluation-tools-abe8b49a.020:r3 conciliado0.0141712045USD
(valor Decimal persistido0.01417120449999999999 por lectura JSON del contador),
con cuatro cargos upstream y recibo failed preservado. No se reejecutó muestra.
Nuevo controlador PID4193295 vivo confirmadoR con --covered-step para8restantes.
Producto runtime siguea817382b; HEADlocal1fe1ebb2, sin publicar ni desplegar.


### Línea base N3 completa y regresión amplia local — 14/10/2026

PID4193295 terminó con COLLECTED/NOT_ASSESSED y ya no existe.84/84recibos,
77completed/7failed; por repetición26/2,26/2,25/3. Fallos:010:r1,028:r1,
021:r2,022:r2,010:r3,020:r3,022:r3. Los84tienen recogida verificada (fallos con
suplemento SQL explícito) y84reservas COST_OBSERVED; no se sustituyó ningún fallo.
Archivos externos snapshot-84,ledger-snapshot-84.json,
baseline-n3-complete{,-score,-judgments,-reviewed}.json,completion-summary.
SHA agregado870a71617efd60b7d586522a0d0a4d437fcaf8fd3242cbf87529e165e0735a1a.
Cargos conciliados de84operaciones0.399209016USD. Histórico0.957927619+
operaciones+reserva seed0.002 da cota de tarea1.359136635USD; no es contador
OpenRouter global ni coste exacto de seed (reserva se conserva). Último contador
global consultado1.468513827 fue al corte78, no saldo final. CAP2USD intacto.

Juiciosprevios trasladados con hashes iguales, y001r1/r2/r3 y002r1/r2/r3
revisados completos.001 suma1000EUR,VM600/60%,periodo/moneda/escenario correctos.
002 calcula200EUR/25% con julio denominador; r1 grounding queda uncertain por
metodología adicional pendiente de contrastar. Guardados judgments-v2 y
reviewed-v2:12PASS preliminares,62pending,3FAILsemánticos,7technical_failure.
No se convierte cobertura84 en aprobación ni se infiere calidad de tests verdes.

Regresión de todos los test_chat*.py con Python3.12/tokenizers0.22.1:
backend terminó616PASS,46SKIP,3FAIL. Un fallo esperaba orden antiguo de citas;
fixture corregido621c6a78, archivo completo5PASS sin cambiar producto. Los otros
2fallaron al crear symlinks (WinError1314), no en el rechazo del loader: ejecutar
en Linux antes de afirmar cobertura. Logcandidate-1fe1ebb2-backend-chat.log.
Processor sigue ejecutándose en sesiónexec46175, último avance81% con fallos
visibles aún sin resumen; no interrumpido ni relanzado. Log externo
candidate-1fe1ebb2-processor-chat.log. Próximo paso inspeccionar salida terminal,
corregir fallos reales/fixtures aplicables, ejecutar pendientes Linux/SQL,
congelar candidato corregido y comparar dentro del presupuesto restante.


### Reproducción Linux de la regresión — 14/10/2026

La sesión Windows46175 terminó: processor558PASS,6SKIP,52FAIL. Los fallos
se concentran en resolución DNS/transportes y resúmenes sin despacho HTTP local,
además de2symlinks sin privilegios. La atribución al entorno es hipótesis hasta
contrastar Linux; no se cambian ni omiten las pruebas para conseguir verde.

Candidato621c6a78325029c93d5a94f4fa50a0ba07cc45d9 transferido mediante git archive,
SHA2567a9e2eb1142098373f34edb0c84d18277b31db4583fb2e9046546154969074f5,
a /home/danteadmin/economicon-jup123-20261014/test-621c6a78. Registro local externo
linux-test-transfer-621c6a78.json. Exclusivamente archivos versionados.
Imágenes de prueba independientes reutilizan dependencias de las imágenes B
backend9dc45286eb79 y processor2b80f3a8ded1, agregando pytest9.1.1,
httpx0.28.1 y PyJWT2.15.1. Ejecutan como10001, filesystem de sólo lectura,
/tmp propio, --network none, sin claves ni variables de los despliegues.
Iniciados35archivos backend y27processor (PID89988/89989); logs remotos
 test-621c6a78-backend-chat.log y test-621c6a78-processor-chat.log.
Resultado Linux pendiente de recoger. Sin llamadas al proveedor ni nuevo gasto.


Después de iniciar ambas pruebas, dos conexiones SSH acotadas terminaron con
«Connection timed out during banner exchange». Resultado y estado de los procesos
remotos desconocidos; no asumir que terminaron ni que falló el código. No se
reiniciaron servicios ni se lanzaron campañas adicionales. Próxima conexión debe
recoger los logs existentes antes de repetir pruebas. La causa de la indisponibilidad
SSH aún no está demostrada. La adjudicación local y preparación documental pueden
continuar sin el servidor; la validación real del candidato sigue pendiente.


### Linux con recursos acotados y adjudicación003 — 14/10/2026

SSH recuperado. Backend89988 observado vivo y avanzando hasta64%; processor89989
ausente y log sin resumen. No se obtuvo causa ni código de salida del processor;
no se cuenta como PASS ni fallo funcional. Host observado con6465/7940MiB usados
y3995/4095MiB de swap. Docker events no devolvió eventoOOM en ventana15min;
no afirmar OOM como causa. Ante nuevos atascos SSH se detuvo sólo el contenedor
propio4cdab045fd76, docker stop confirmado. La ejecución amplia inicial queda
incompleta y conservada.

Ensayo Linux focal processor DNS+summary_resources:54PASS, exit0,24.39s,
2026-10-14T09:55:49Z. Prueba --network none, memoria/swap1200m,CPU1,pids128,
filesystem readonly y tmpfs256m. Log remoto test-621c6a78-processor-dns-resources-bounded.log
más JSON de salida. Esto verifica en Linux esos fallos Windows, no toda la regresión.

Regresión completa secuencial por archivo iniciada sesiónexec97081, sobre mismo
archive621c6a78, mismas cotas y aislamiento. Directorio remoto
/home/danteadmin/economicon-jup123-20261014/test-621c6a78-bounded-regression.
results.json se actualiza tras cada archivo y complete.json sólo al finalizar;
logs individuales conservados incluso si exit!=0. Primeros3archivos processor
(auto,battery_corrections,calculations) exit0 confirmados. No relanzar hasta
consultar sesión y archivos; aún no hay resultado completo. Sin gasto de modelo.

Adjudicación preliminar003:r1/r2/r3 contra respuesta, auxiliares, entrada y chunks:
requisitos de pedir datos e investigar sin inventar causa cumplen en las3.
r1/r2PASS; r3uncertain en grounding/consistency por presentar campos conceptuales,
incluido root_cause, como necesarios para evaluar desviación, y cita truncada e`;
no se transforma duda en aprobación. Artefactos externos judgments-v3/reviewed-v3:
14PASS,60pending,3FAIL,7technical_failure;108requisitosPASS,5uncertain,
372sin revisar,10FAIL agrupados en4clusters. AceptaciónNOT_ASSESSED; no es revisión
humana independiente ni criterio pactado. Historial y artefactosv2 preservados.


### Diagnóstico005/007 y revisión004 — 14/10/2026

Continuación de sesión97081 verificada viva. Archivos processor hasta
summary_gateway terminaron exit0, excepto summary_capacity exit137 bajo límite
1200m (sin resumenpytest; no atribuir aún a fallo funcional). Hay que recoger su
log y reproducir aisladamente con recursos suficientes o por casos. El resto
continúa; no reiniciar el controlador ni modificar el runtime del modelo.

Revisión004:r1/r2/r3PASS: distingue actual/amortizado y showback; fuentes finops6/11
respaldan las afirmaciones.005:r1/r2/r3FAIL: abstención injustificada con fórmula,
partición y componentes explícitos; todos reciben mismo payloadRAG067c06eb…
con rules3/4 completos. Diagnóstico offline case005-unresolved-offline-621c6a78.json:
required=True, resolved=None. Catálogo reconoce700/200/100/50EUR y sus estados;
resolver actual sólo soporta total explícito, no composición y exclusión declarada.
Corrección006 no resuelve005; pendiente diseño determinista de suma con procedencia,
exclusión explícita y rechazo de escenarios ambiguos, sin reconocer IDs del banco.

007:r1/r2/r3 también abstienen en baseline y sonFAIL. El candidato actual sí resuelve
101/1000*100=10.1%, rojo, en replayoffline de los tres contextos originales,
guardado case007-resolved-offline-621c6a78.json. No equivale a ejecución real del
modelo corregido; conserva FAIL de baseline. Artefactos judgments-v4/v5 y reviewed-v4/v5
externos; último17PASS,51pending,9FAIL,7technical_failure;135requisitosPASS,
5uncertain,40FAIL,315sin revisar;10clusters por respuesta. No aceptación global.
008/009 respuestas leídas, todavía sin adjudicación final de grounding/auxiliares.
Sin nuevo gasto ni publicación. Próximo: recuperar regresión completa, resolver
summary_capacity y avanzar adjudicación antes de congelar comparación corregida.


### Regresión Linux parcial y adjudicación008/009 — 14/10/2026

Sesión97081 sigue viva. Corte45archivos: processor27archivos,589PASS/6SKIP,
summary_capacity exit137 sin resumen (sólo7puntos); backend18archivos,
242PASS/43SKIP, context_assembly también exit137 bajo1200m. Ningún fallo de
aserción informado en archivos terminados; esto no acredita los dos incompletos.
Esperar final, recoger todos los logs y repetir exclusivamente incompletos con
memoria suficiente y diagnóstico OOM/exit, manteniendo ejecución secuencial.
Los43SKIP backend corresponden a ausencia de servicios SQL en --network none;
la integración SQL permanece pendiente, no se cuenta cubierta.

008:r1/r3PASS preliminar: explica denominador cero y solicita periodo/datos.
008:r2 cumple banco peroFAILquality-consistency: next_actions exige tanto total
como unallocated positivos, aunque numerador cero es válido con denominador
positivo; clusterpositive-numerator-required. Formula/definiciones contrastadas
con rules3/finops12 realmente suministrados.009 conserva prohibición de reparto
inventado y pide regla/base; groundinguncertain en3repeticiones por pasajes
truncados de tagging ajenos al reparto dentro de chunks relevantes.009:r2 también
uncertain al no confirmar expresamente mantener shared pese a falta de regla.
No endurecer retrospectivamente rúbrica: estas dudas requieren adjudicación.
Artefactos externos judgments-v6/reviewed-v6:19PASS,48pending,10FAIL,
7technical_failure;163requisitosPASS,9uncertain,41FAIL,282sin revisar,
11clusters. SigueNOT_ASSESSED; no aceptación ni nueva campaña/modelocoste.


Regresión por archivos terminó REGRESSION_COMPLETE, sesión97081 exit0 del
controlador (no significa todos los archivosPASS). Los únicos archivos noexit0
son summary_capacity processor y context_assembly backend, ambos137. Reproducción
exclusiva secuencial iniciada sesión7467,2500m sin swap adicional,CPU1,sin red,
con docker inspect .State tras terminar para capturarOOMKilled/ExitCode. Logs
processor-retest-2500m.log y backend-retest-2500m.log conJSON acompañante dentro
del directorio bounded-regression. Contenedores propios jup123-retest-{app}-621c6a78
se eliminan sólo tras registrar estado; aún pendiente resultado. No lanzar otra
campaña ni repetición hasta recogerlo.

OpenSpec tasks2.1–2.3 actualizadas como completadas con alcance de recogida y
procedencia de baseline; design elimina la afirmación obsoleta de que falta
colector. Criterios de revisión, adjudicación y comparación permanecen abiertos.
git diff --check sin errores de whitespace (sólo advertenciasCRLF).


### Regresión Linux cerrada sobre621c6a78 — 14/10/2026

Sesión7467 terminó exit0. Repeticiones2500m: processor summary_capacity21PASS
(34.29s), backend context_assembly exit0; ambasState.ExitCode0/OOMKilledfalse.
Los estados Health unhealthy proceden del healthcheck HTTP heredado de imagen
servidor, mientras entrypoint ejecuta pytest sin servidor; no son fallospytest.
Los logs iniciales137 permanecen; no hay evidencia directa OOM de esos contenedores
--rm anteriores, así que no afirmar causa demostrada sólo a partir del137.

Totales sin duplicar repeticiones: processor610PASS/6SKIP/0FAIL en27archivos;
backend619PASS/46SKIP/0FAIL en35archivos. Todos los archivos test_chat*.py del
archive621c6a78325029c93d5a94f4fa50a0ba07cc45d9 cubiertos. Evidencia local externa:
materiales/07-evidencias/PR121-local-evaluation/linux-regression-621c6a78/summary.json,
logs individuales, results.json, complete.json y estados de repetición. Summary
registra SHA256 de cada log aceptado y referencias a fallos iniciales. Sin red,
sin modelo ni credenciales. SQL real, navegador y calidad semántica siguen pendientes.

Adjudicación016 completa3PASS: deltas150EUR/dia y37.5%, ANDtrue y petición de
investigar; mojibake ya conocido no cambia semántica, corregido sólo en candidato.
019r1/r3PASS; r2FAIL por omitir incremento absoluto: muestra150 como dato observado,
no como diferencia. Agrupados required-1/numbers-1 bajo absolute-delta-omitted,
sin aprobar por coincidencia numérica. Fuentes r3 contrastadas con finops9.
Juiciosv7/reviewed-v7:24PASS,42pending,11FAIL,7technical_failure;
200requisitosPASS,9uncertain,43FAIL,243sin revisar,12clusters. Preliminar local,
no revisión independiente ni aceptación. No nueva inferencia ni cambio de gasto.


### Adjudicación de alcance y equivalencias — 14/10/2026

023/025:r1–r3PASS preliminar (sin acceso real ni apagados inventados; fuentes
product1/finops0,1,15,17/rules0 contrastadas).026r1PASS; r2/r3FAILgrounding por
citas Inform/actual cost no pertinentes para ingesta incompleta; causalidad en
assumptions quedauncertain, sin reclasificar la conclusión correcta sobre ausencia
de datos. Juiciosv8 preservados.006r3 y017r3 trasladados desde r1 sólo tras verificar
igualdad exacta response/cited_chunks, mismo hash payloadRAG, entradas verificadas
contra banco, colección verificada y criterios iguales; prueba explícita en
baseline-n3-equivalence-v9.json. No son dictámenes humanos independientes.
Últimos artifacts judgments-v9/reviewed-v9:32PASS,31pending,14FAIL,7técnicos;
252requisitosPASS,11uncertain,49FAIL,183sin revisar,15clusters. Banco/campaña
inmutables; ningún coste nuevo. Pendientes calibración011/012/018r3/024r3/027/028,
dudas anteriores y reserva013–015/020–022, sin usar reserva para ajustar evaluador.


### Continuación de etiquetas de calibración — 14/10/2026

018r3PASS (20>20 falso, ANDfalse, delta200) y024r3PASS (100EUR/100USD separados,
sin tasa inventada).012r1–r3 cumple requisitos conceptuales; groundinguncertain
por cita de minusculas en apoyo de reglaowner aunque el chunk completo sí la
contiene, consistente con duda009.011r2/r3PASS:10% por coste y90% por recursos
explícitos; formula y advertencia contrastadas con rules5/finops10 suministrados.
Artifacts judgments-v10/v11 y reviewed-v10/v11 externos, sin sobrescribir anteriores.
Último36PASS,27pending,14FAIL,7técnicos;286requisitosPASS,14uncertain,49FAIL,
146sin revisar. AceptaciónNOT_ASSESSED. No inferencias, gasto ni publicación.


### Calibración preliminar congelada — 14/10/2026

027r2/r3PASS tras contrastar KPI opcional con rules5 y metodología con finops9;
028r2/r3PASS, finops11 contiene distinción showback/chargeback. Juiciosv12:
40PASS/23pending/14FAIL/7técnicos globales. Todos los requisitos de respuestas
completed de calibración están revisados:66muestras =40PASS,9pending por dudas,
14FAIL,3técnicos. Reserva18muestras (14completed/4failed) permanece sin adjudicar
para diseñar correcciones; no usar sus respuestas para afinar código/evaluador.
Freeze externo baseline-calibration-freeze-v1.json SHA256
7af862ac1a0122531e1d0296a14253fa7322ff0fc984d575948854be99f84c28 registra hashes
agregado/juicios/scoring e incertidumbres. No equivale a calibración de juezLLM,
adjudicación humana ni aceptación. Próximo: corregir005 con composición elegible
explícita y operandos con procedencia, abordar omisión de delta019 y contradicción
008 sin prompt gigante, comparar candidato; reserva se evalúa al cierre con rúbrica
fija. Incertidumbres de citas por pasaje y criterio011 siguen abiertas. Sin gasto.


### Composición determinista de coste elegible — 14/10/2026

chat_rules.allocation_denominator añade gramática cerrada de cuatro partidas
allocated/shared/unallocated/excluded con moneda única, anclas inequívocas y
política explícita de exclusión/remaindereligible. Suma las tres primeras; usa
unallocated como numerador y umbrales de regla documental, sin IDs/cifras del banco.
Valores negativos, divisas mezcladas, cantidades extra/repetidas, política ausente,
contradictoria o ambigua conservan fallback. No es parser universal de políticas.
Renderer exige AST fijado, muestra denominador calculado y usa≈ si redondeado.
Backend/processor byteidénticos. Manifest/pin/fixture interval_rules actualizados;
assembler SHAcef131e0295c709a5439cd14c1a490d6b0a95318a0e9f76347cad74bba264d91.
Pruebas:114PASS processor recursos/expresiones/intervalos antes de4pruebas nuevas;
archivo ampliado29PASS (incluye streaming1/11/8192bytes y redondeo);78PASS backend
intervalos/modos. Replay0053contextos resuelve10%,amarillo; artifact externo
case005-partition-resolved-offline-v1.json anterior a añadir nota del totalvisible.
El totalvisible1000 se deriva del AST; tests sintéticos comprueban total100 con
otras cantidades/umbrales. No revalidación con modelo, SQL ni navegador.
Baseline congelada permaneceFAIL; runtime siguea817382b, sin transferencia nueva.


### Variación con base cero completa en servidor — 14/10/2026

required_zero_change resuelve sólo petición simple de porcentaje/variación con
par explícito baseline/current, base0, unidades iguales y sin otras cantidades
con unidad. Pregunta compuesta, definición, negación, duplicados, divisas mezcladas
o base no cero conservan modos existentes. No usa valores del corpus. Nueva
respuesta tipada zero_change fija expresión; renderer incluye diferencia absoluta,
porcentaje indefinido, naturaleza hipotética y petición de base comparable.
Auxiliares vacíos obligatorios y statusinsufficient_data; sin citas fabricadas.
Schema, render final y streaming verifican operandos. Ambos módulos byteidénticos.

Pruebas134PASS processor segmentos/intervalos/recursos/clasificación, luego18PASS
archivozero tras añadir2casos de preguntas compuestas;48PASS backendboolean/modos.
Replay offline019 en3contextos originales devuelve diferencia150EUR/día y porcentaje
indefinido; case019-zero-baseline-offline-v1.json conserva salida y hashes módulos.
No llamada al modelo ni nueva validación integral. Manifest/pin/fixture actualizados,
assemblerSHA3ae4057abb4234acb8deb0305d2dc164e8a3f0e2269d10bc48a92809689daca8.
008 (cociente0/0 sin baseline/current) no queda cubierto por esta ruta; sigue pendiente.


### Cociente con denominador cero — 14/10/2026

008 corregido localmente: required_zero_percentage reconoce una petición simple
unallocated/total elegible con operandos explícitos del usuario, moneda única y
fórmula documental completa y verificada. No necesita inventar intervalos para
explicar que dividir por cero es indefinido. Ambigüedad, intención compuesta,
negación, otras cantidades o fórmula incompleta conservan el flujo existente.
Respuesta tipada zero_percentage fija el AST, insufficient_data y auxiliares
vacíos; servidor redacta la explicación y cita la fórmula. No exige numerador
positivo ni convierte 0/0 en 0%. Módulos backend/processor idénticos.

Verificación: 104 PASS processor en segmentos/clasificación/rutas cero;
51 PASS recursos/streaming; 94 PASS backend modos/intervalos/booleanos.
Replay de los tres contextos originales en case008-zero-denominator-offline-v1.json
(externo) produce cociente indefinido y pide período con denominador aplicable.
Assembler SHA256 63dcc4d3529256777bd52e1967b54d1060581ede875fbae7be235cda23b52f2e.
Estas pruebas son offline: no alteran etiquetas de baseline ni prueban aceptación
con modelo, SQL o navegador. Runtime sigue a817382b; sin gasto nuevo.

Siguiente: preparar comparación del candidato conservando el ledger de todas las
campañas, consultar gasto/validez de claves antes de inferencia y ejecutar sólo lo
que permita el techo acumulado de 2 USD. No resetear contabilidad ni renovar claves
sin autorización aplicable. Reserva continúa separada del ajuste del candidato.


### Cobertura contable de varias campañas — 14/10/2026

chat-eval-covered-step admite --additional-plan conservando obligatoriamente el
plan original. Valida hashes canónicos (misma identidad del runner), prefijos
ordenados por campaña, operaciones únicas y todos los costes observados. Mantiene
las dos reservas no-chat y el contraste con las operaciones SQL del entorno.
chat-eval-campaign-runtime propaga planes adicionales sólo con --covered-step.
No cambia el techo, la fórmula presupuestaria, las claves ni el ledger.

24 pruebas pasan (8 cobertura, 5 controlador, 11 presupuesto). Contraste de sólo
lectura con ledger real: 84 operaciones verificadas, 2 reservas adicionales
conservadas, coste observado 0.399209016 USD. DockerServer consultado a las
10:31 UTC; runtime B a817382b sigue activo. Sin inferencia ni gasto nuevo.
Pendiente adaptar/verificar el adaptador operativo del candidato, consultar
contadores vivos y ejecutar comparación; estas pruebas no autorizan ni acreditan
por sí solas una nueva campaña. Cambios aún locales.


### Candidato comparativo transferido y regresión en curso — 14/10/2026

Plan N3 congelado para e94f6e54f69eef7962249989222327c8378f3f9a, 84 muestras,
NOT_RUN; jup123-candidate-e94f6e54-plan.json fuera del repo, SHA256
c58dcd9db620eeae04eb53e1b31ef0b1d7c930573cc328dbefef622bf059dfed.
Archive transferido/verificado en DockerServer, candidate-e94f6e54 bajo el root B;
SHA256 e04453670fc655f47faad31f5ea55374b5b7a275a71bb704aaf4fdbc0b388205.
Registro externo candidate-e94f6e54-transfer.json. No modificación de despliegues.

Consulta viva de contabilidad: global OpenRouter1.492618162USD (cota conservadora,
no atribución exclusiva); claves B backend0.00009768/0.02 y
processor0.382437475/0.88, vencimiento15/10 08:02:20UTC. No gasto nuevo.
La admisión debe volver a consultar estos contadores antes de cada operación.

Regresión Linux iniciada en regression-e94f6e54 del root remoto, PID342286
confirmado vivo a10:34UTC. run.py ejecuta todos test_chat*.py de processor/backend
secuencialmente, contenedores sin red ni secretos, memoria2500m/CPU1, fuente sólo
lectura. results.json conserva estado/OOM por archivo y logs; complete.json será
la señal terminal. No reiniciar por timeout: inspeccionar PID y resultados.
Pendientes resultado integral, construir/verificar runtime corregido y adaptar
harness comparativo conservando ledger/baseline. Aún no aceptación semántica.


### Arnés separado y build condicionado — 14/10/2026

Herramientas cubiertas/controlador/recuperación de fallos admiten --adapter.
La recuperación usa PLAN_PATH, RECEIPTS_DIR y RAW_RECEIPTS_DIR declarados por el
adaptador; defaults antiguos conservados. Controlador exige recuperador documental
explícito si se cambia adaptador, evitando mezclar recibos de campañas con iguales
sample_id. 22 pruebas focales PASS (14 runtime/controlador, 8 cobertura).

Preparados remotamente candidate-e94f6e54-step.py y
candidate-e94f6e54-retrieval.py, plan congelado copiado/verificado. No ejecutados.
Comparten evaluation-ledger.sqlite; salidas candidate-e94f6e54-n3 y
candidate-e94f6e54-raw-api, archivos anteriores intactos. SOURCE apunta al archive
verificado. Proyecto Docker conserva nombre a817382b por continuidad de volúmenes;
la identidad de código se verificará por hashes del plan, no por ese nombre.

candidate-e94f6e54-compose.json privado conserva configuración/volúmenes/puertos
y sólo cambia build e imágenes de backend/processor. Controlador de build PID363983
espera complete.json sin fallos de regresión PID342286 (10archivos sin fallos en
última consulta); no inicia servicios. Logs candidate-e94f6e54-build.log y resultado
candidate-e94f6e54-build-result.json. Ante desaparición sin resultado o fallo de
regresión no construye. Pendiente verificar ambos procesos, transferir herramientas
versionadas nuevas y arrancar/verificar exclusivamente los dos servicios B antes
de cualquier inferencia. Runtime vigente conserva código baseline. Sin gasto nuevo.


### Herramientas y dependencia A contrastadas — 14/10/2026

Transferido tools del commit8215a2b74dcf7d0843aadc3001f76ffe1485083d a
DockerServer/evaluation-tools-8215a2b7 bajo root B. SHA256 archive
943beb5f89ce4eda1d3bb698fa779e4b4c996ae048d720bf41c427f5c6ed34ce.
22 pruebas focales también PASS en Linux. Registro externo
candidate-tools-8215a2b7-transfer.json. Runtime de producto sigue baseline;
regresión candidata PID342286 comprobada viva con25archivos sin fallos,
build PID363983 sigue condicionado al resultado integral. No inferencias nuevas.

A comprobada en GitHub: PR130 OPEN/CHANGES_REQUESTED, head318a56f3; CI técnica
SUCCESS pero JUP reviews FAILURE. Pendiente retirar tokenizer versionado y
validación funcional/revisión; ver chat-entregas-a-b.md y recibo externo de consulta.
No marcar1.3 completada ni atribuir a B la aceptación de A.


### Regresión candidata terminada; fixture SQLite — 14/10/2026

regression-e94f6e54/complete.json:64archivos,1archivo fallido. Build no iniciado:
controlador detuvo correctamente ante ese resultado. Fallo en
backend/test_chat_operations_jup035.py::test_required_tool_extension_validates_and_persists_only_recovered_sources:
409 operation_changed,21tests del archivo PASS. Repositorio/transiciones/fixture
sin cambios entre621c6a78 y e94f6e54; SQLite omite FOR UPDATE y su modo legacy no
abre transacción con SELECT, permitiendo revisiones obsoletas concurrentes.

Fixture ajustado para BEGIN IMMEDIATE después de migraciones/seed. Aplicarlo
antes de migraciones causaba22errores de setup y se corrigió. Las3pruebas de
arbitraje UNIQUE retiran expresamente el bloqueo del fixture para conservar sus
colisiones reales; no se relajaron expectativas. Archivo final22PASS en Windows.
No cambia código de producto ni demuestra bloqueo correcto en SQL nativo.
Pendiente repetir archivo corregido en Linux, conservar fallo original y resumir
regresión completa; sólo entonces habilitar build del producto e94f6e54.
No inferencias nuevas ni cambios del runtime existente.


### Candidato activo verificado — 14/10/2026

Fixture1651b8fa transferido SHA256
c876432f2dfd2555df871fc87707a51a2ef8406a04713dcce47eedbb58536852;
Linux22PASS, OOMfalse. Regresión resumida sin duplicar repetición:
processor663PASS/6SKIP (29archivos), backend619PASS/46SKIP (35archivos).
Logs, fallo original, repetición y summary.json copiados a evidencia externa
linux-regression-e94f6e54. Producto e94f6e54 sin cambios por el fixture.
Build backend/processor terminó0; resultado y log candidate-e94f6e54-build-verified.

Primer compose rechazado por auto-review por aislamiento no demostrado. Inspección
posterior acredita root B exclusivo,5volúmenes sin consumidores ajenos y puertos
loopback29657/29658/29660; segundo intento admitido se detuvo antes de compose por
BD no disponible. Cockroach B había salido7 a09:52UTC por disk stall (sync logs>20s),
OOMfalse,30GB libres. Se arrancó sólo ese contenedor conservando volumen. SQL
confirmó0operaciones abiertas; ledger86filas/84operaciones con costes observados.
Después compose up --no-deps --no-build backend processor terminó0 en el proyecto
B. Ningún otro despliegue modificado. No inferencias ni coste nuevo.

candidate-e94f6e54-runtime-verification.json confirma324hashes fuente y contenido
en contenedores backend102/processor93/frontend116. El nombre de proyecto sigue
incluyendo a817382b para conservar volúmenes; código ejecutado confirmado e94f6e54.
Plan N3 congelado sigueNOT_RUN. Siguiente: preflight/admisión viva con herramientas
8215a2b7, adaptador candidate-e94f6e54-step.py, recuperación candidata separada y
ledger común. Mantener2USD; no afirmar disponibilidad de presupuesto por saldo viejo.
