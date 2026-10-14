# Evaluación local de JUP-035

## Autorización vigente — 14/10/2026, ampliación a5USD

El usuario respondió «Amplia a5$» a la solicitud de presupuesto. Máximo acumulado
actual5USD; supera el tope2USD de los cortes históricos siguientes. No reinicia
histórico ni ledger. Lectura nueva15:59UTC conserva upperbound1.683584087USD;
clavesB backend0.00014362/0.02 yprocessor0.566091115/0.88, vigencia15/10 08:02UTC.
CAP del runner pasa5; pruebas presupuesto11PASS yledger6PASS. Primer intento
ledger con Python3.14 falló por TEMP/sandbox; segundo3.12 con temporal encheckout
fue rechazado porcontrato; tercero usa temporal externo autorizado y pasa.

Continúa preparación del candidato actual para nueva N3; no reanudar la campaña
e94 antigua como si validara código nuevo. Recuperar sólo runtimeB autorizado,
memoria/cacheSQL limitadas y gasto preservado; ampliar límites de claves exclusivas
únicamente dentro de5USD sin extender caducidad. Criterios de revisores siguen
pendientes; ampliación económica no equivale a aceptación semántica.

## Estado vigente — 14/10/2026, 11:15 UTC

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
