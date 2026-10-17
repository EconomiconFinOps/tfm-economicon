# JUP-123: candidato local y validación conservada

### Reproducción presupuestaria corregida tras la validación de PR140 — 17/10/2026

La N5 final usó los operadores externos currency api-step-v2/v3/v4, que elevaron
de20 a30 USD ambas instancias importadas de budget/admisión y ledger. No ejecutó
la nueva opción versionada `authorized_cap_usd`; tampoco corresponde a las
políticas de las campañas N3/d965 anteriores citadas en los cortes históricos.
Los originales y los497 archivos congelados siguen intactos, con sus hashes.

La herramienta actual conserva20 por defecto y admite hasta30 sólo mediante
una opción explícita por admisión/reserva, previa autorización ajena a este módulo.
[Reproducción y límites](../evidence/JUP-123-budget-reproduction.md) y
[procedencia exacta de los tres segmentos](../evidence/JUP-123-budget-provenance.json).
Las pruebas usan importes agregados e identidades sintéticas; no modifican la
cuenta, los1744 asientos, las reservas ni las claves reales. El producto medido
`f3ec760d`, el plan y la N5 conservan su identidad: no se reetiquetan como campaña
del nuevo HEAD ni se mide otra combinación de corpus/modelo/prompt.

### Resultado final de las pruebas B — 17/10/2026

La nueva N5 del producto `f3ec760d3c483e8798df2be32ea90bb901ebe36d` terminó: **140 respuestas
completadas y conformes; 825 comprobaciones PASS** (545 del banco y 280 de
calidad). Se cumplen C1, C2 asistido y C3 en el alcance local acordado. Revisor
y validador separados emitieron PASS sobre el mismo informe final, por la
sustitución expresamente aceptada por el usuario; no es revisión humana oficial,
un juez calibrado ni evaluación ciega. El banco conocido se utilizó para corregir
el sistema, por lo que no se afirma generalización o superioridad del modelo.

Modelo configurado: DeepSeek V4.1 Flash / DeepInfra FP8; banco1.0.1,
plan `3fd573f5cc55a4d50cbc83b65d1af6a1b414102edfeb21a173f2b0352ec4b776`, corpus sintético54, temperatura0 y razonamiento
desactivado, ZDR sin fallback. La ruta está configurada y vigilada; no hay traza
independiente del proveedor upstream. La corrección024 conserva monedas separadas
y solicita destino, tipo autorizado/dirección y fecha. Pruebas focales Linux y
Windows:106 processor+4 backend;2 builds y226 archivos verificados. No se repiten
ni atribuyen suites históricas a este commit.

Se conservan tres segmentos:84 completadas;35 recogidas más la operación120
completada en SQL; recuperación120 exclusivamente GET sin nueva generación;
y20 no enviadas desde009r5. Las interrupciones URLError e historia Dockerexec
quedan registradas sin atribuir una causa no demostrada. Ninguna muestra fue
repetida o sustituida. Los fallos de campañas anteriores permanecen intactos.

Contabilidad: 138 costes nuevos observados,
`0.1435598696 USD`; 2 máximos nuevos
desconocidos íntegros (`0.16155264 USD`). Todas las
reservas desconocidas: `15.04040862 USD`. Cota conservadora
`23.117520366/30 USD`, no factura ni atribución exacta a B. Ledger
1744 filas SHA `b26c247dd81a6abb759cb211b7c1070907f029e33ce6119382214a1bc07e849e`; prefijos1604/1688/1724 y355 historias
congeladas intactos. Cero operaciones activas, propios3 parados, datos/imágenes
conservados y otros servicios intactos. Sin claves nuevas, renovación, reset o
liberación de reservas.

Evidencia:

- [Informe final](../../../materiales/07-evidencias/PR121-local-evaluation/currency-024-final-results-v1.md).
- [Auditoría final](../../../materiales/07-evidencias/PR121-local-evaluation/currency-024-api-final-audit-v3.json),
  SHA `3eb85e58c96c8d1ef577a95330d355105d9ab0bdc1e5f7abbd72a160a94e0ba5`.
- [Paquete reproducible](../../../materiales/07-evidencias/PR121-local-evaluation/currency-024-f3ec760d-n5-full140-frozen-v1/manifest.json):
  497 archivos, manifest SHA `4838711dac437ce7f63f5e68aa382dc9e8dd0343c4e8f3024579d39346c32984`.
- [Comparación descriptiva](../../../materiales/07-evidencias/PR121-local-evaluation/currency-024-vs-d965-descriptive-v1.json)
  con139 pares semánticos y una pareja técnica histórica; sin inferencia causal.

**Las pruebas locales B han terminado.** Integración la realiza otro agente;
no se publica, integra, activa permanentemente ni marca Done desde este chat.
Los siguientes cortes son históricos y conservan sus fechas originales.

Los cortes anteriores que siguen son históricos y no sustituyen este estado.

Verificado el 17/10/2026. Origen: chat
`01a1270c-e332-7462-9c90-706d49ade92c`.
**Código preparado para revisión; B no aceptada, publicada ni activada de forma permanente.**

### Continuación tras fallo técnico — 2026-10-17 12:26 UTC

DeepInfraV2 terminó023r2 tras4intentos sin stream completo: EOF y logs existentes500;
causa raíz no atribuida.50respuestas conformes/296PASS y6noevaluables del fallo
conservadas, sin inventar respuesta/RAG. V2 restauró own3/old6/shared,0activas.
V3ACTIVO PID505182/start5164432, controlador5bc0e333/política57bc0de3, continúa
sólo89noenviadas desde024r2. Protege1515filas SHA037bee6e/167artefactos/146SQLids;
51recogidas(50completed+1failed) intactas.12focalesPASS y revisión02dccff3;
launcher concreto revisadodc0f7bdc, sin nuevas claves/reset/prórroga.
Corte56:55conformes/324PASS+1técnica/6noevaluables. Otro técnico detiene para
evaluar. Mismafuente/modelo/ruta/plan/corpus/imágenes; no se relaja C1/C3.

Cuatro máximos0.08077632 retenidos; cota22.560164661/30USD a1521filas, no factura.
Claves6/.1 hasta17oct15:59:59UTC intactas. Auditores140completed/825PASS previos
inaplicables. Nuevo auditor TÉCNICO139+1 sólo preparado: C1/C3strict/ReadyFALSE,
con15gatesfocalesPASS; revisión incremental en curso, sin ejecución.
Handoff `B-route-api-handoff-v3.json` SHA15a1477c52eb0747f250e3d6d10f9f12c8f5c1a891191c2d22b1b192bfdbc9a5.
ObservarV3 con `observe-B-route-api-v3.py`/watchreadonlysesión68463; no relanzar.
Integración/PR131 fuera de alcance; no publicación ni aceptación.

### Histórico — 17oct11:52UTC

Actualización17oct11:52UTC: el humano ordenó terminar sólo las pruebas B,
excluyendo integración. N5 separada DeepSeek/DeepInfraFP8 del mismo producto d965,
plan a12e5d1a, activa en V2PID222945/start4979124:16completed,13conformes/75PASS
revisados. Las95CoreWeave se conservan y no rellenan esta campaña.
V1 terminó/restauró tras13por ambigüedad del contador, no fallo de generación.
012/013 mantienen cadauno0.08077632 completos; no se atribuye el exceso a un
cargo anterior. Retención revisada/14focalesPASS, política63db9f9f protege1477filas
SHA1177cc4f/49artefactos/108SQLids y sólo permite continuar014–140 con mismos
contenedores/código/ruta. Revisor APPROVE y10focales de continuaciónPASS;
conciliación futura estricta, cap30/reservas íntegras. No N5 completa ni aceptación.
Handoff `B-route-api-handoff-v2.json`/SHA98805de8 en la evidencia externa.
El corte bloqueado08:33 siguiente es histórico frente a esta nueva instrucción.

Objetivo confirmado `blocked` a17oct08:33UTC tras tres turnos de upstream429.
Auditoría38381c87 y observación remota actual: V12terminado/PIDausente,
95recibos/1460filas,0activas; no inferencias nuevas ni recuperación verificada.
Este bloqueo no hereda los tres turnos del antiguo0% de disponibilidad.

### Histórico — 17/10/2026, 08:29 UTC

V12 terminó011r4 por4HTTP429 upstream de CoreWeave, sin Retry-After, pese a900s
de espera ypreflightPASS. Sin respuesta final/RAG de011 para evaluar.95recogidas:
91completed conformes538PASS,4técnicas/21checks no evaluables,45sin despachar.
Ledger1460SHAc34e5ca2/prefijo1459intacto;4máximos0.0889632retenidos,
desconocidos14.34637330USD/cota22.11767032de30USD(conservadora,no factura).
Auditoría parcial095 verifica terminal/PIDausente/parkingexit0/0activas/old6sanos;
los diagnósticosv2 conservan elerrorreal. No campaña pagada viva ni relanzamiento
por tiempo/catálogo saludable. Nuevo impedimento429, distinto del histórico0%.
C1/C3sin cumplir; cierres anteriores noaplican a4fallos, no se relajan etiquetas.
Hardware24GB/RAMdisponible14GB/swaplibre; raíz225G55libres/disco400GiB visibles.
Detalles en `../continuidad/chat-evaluacion-local.md`; mismo producto d965.
Dictamen095JSON3a68e2b1/21noevaluables y paquete248archivos/manifest6c8e658d
congelados; notasd495/91juicios intactos. Trello07510638 actualizado por puente,
sin alterar lista/miembros/fechas. No significa aceptación o fin de la N5.

### Histórico: corte de reanudación — 17/10/2026, 08:27 UTC

V11 reanudó010r4 tras recuperación de la ruta, pero terminó por HTTP429 de
CoreWeave: limitación temporal upstream sin Retry-After. Se conservan sus4intentos,
la reserva máxima0.0889632 y el borrador parcial; no hay respuesta final evaluable.
Corte094:91completed conformes/538PASS,3técnicas/16noevaluables; paquete239archivos
manifest7ec1b677, ledger1459SHA7b3dffd0 y desconocidos14.25741010USD intactos.
V12 vivoPID3295534/start3740953/prepared713aee87 continúa sólo desde011r4:
900s desde cierreV11, separación60s trascompleted, mismos4intentos internos,
stop ante siguiente técnico. Preflight08:26:51PASS;1460filas/94recibos/011en curso.
No declarar recuperación real del modelo por metadatos públicos o por esa espera.
Revisión73e0e029 yvalidaciónf7705652 independientes conformes al arnés, no al resultado
futuro. Cadenas finales estricta y técnica de2fallos ahora inaplicables; C1/C3sin cumplir.
Hardware verificado24GB,disco400GiB/raíz225G55libres, sin resize por este agente.
Cap30/mismasclaves4.5/.1hasta17oct18París/sin liberar reservas/publicar B.
Detalle y siguientes acciones en `../continuidad/chat-evaluacion-local.md`.

### Histórico: objetivo bloqueado por disponibilidad externa — 17/10/2026

Estado del objetivo confirmado `blocked` tras tres turnos consecutivos con la
misma ruta no disponible; no es el antiguo bloqueo presupuestario ni una pausa.
Verificación16oct23:21UTC:CoreWeave/fp8status-5/uptime5m0%/30m0%, proof71e6a4e7.
Observador actual confirma sinhandleV11,93recibos(91completed/2failed),1458filas,
91costes observados/2máximos retenidos y ningún proceso pagado vivo. Cadena técnica
preparada1e12a53a intacta, producto idéntico d965,47sin despachar; no criterio final
cumplido ni trabajo independiente pendiente. Auditoría de bloqueo
`B-role-n5-provider-blocked-goal-audit-v1.json` conserva los tres cortes y el alcance.
Seguimiento existente permanece activo para recuperación significativa, sin
inferencias/renovación de claves/campañas nuevas mientras falte disponibilidad.
Próxima010r4 con mismas guardas y30USD; claves sólo hasta17oct18París. No nuevas
preguntas ni documentación repetitiva ante estado idéntico. B local/noaceptada.

## Histórico:93 recogidas; ruta no disponible — 17/10/2026

N5 d965/plan8af94f71: **93/140 recogidas:91completed conformes y2failed técnicos**.
538PASS(356banco+182calidad),11comprobaciones no evaluables;47sin despachar desde010r4.
008r4:4timeouts;009r4:1provider_error/HTTP404. No son fallos semánticos adjudicados
ni éxitos. No repetirlas, heredar84a7, inventar respuesta/RAG o borrar reservas.
Siguiente batchsemántico013, notas/batches sólo por validador.

V9PID129964 yV10PID351043 TERMINADOS, ambos STOPPED_AFTER_NEW_TECHNICAL_FAILURE;
parkingexit0/new3parados/0activas, old6sanos sin pausarlos. No relanzar controladores.
Auditoría `B-role-n5-partial093-technical-stop-audit-v1.json`: ledger1458SHA
`60fdb0d3fbb7b69bc1d534717eaaf06efb41b3dd86aa134f3f69f0ab9e675492`, prefijos y
93recibos protegidos. Máximos008/0090.0889632cadauno íntegros; desconocidos totales
14.16844690USD. Cota conservadora21.909256304/30USD, no factura/atribución exacta.
Mismasclaves4.5/.1hasta17oct18París; no renovar, aumentar, resetear o liberar.

Catálogo público OpenRouter/CoreWeaveFP8 a16oct23:01UTC:status-5/uptime5m0% y
30m16.6667%, proof endpoint1792191713098677374/SHA73848e60. Evidencia externa de
indisponibilidad; no causa única probada del008 ni defecto semántico delmodelo.
V11preparación desde010r4 para47: gate público fresco antes del lanzamiento y de
cada admisión pagada, no durante observación activa. PolíticaSHA db731697 protege
1458/93/333artefactos. No inferencias mientras ruta no pase; mismo producto/modelo/
proveedor/prompts/banco/corpus. Hardware24032MiB verificado no es bloqueo actual;
huésped400GiB/root194G25libres, sin ampliar particiones/LVM/filesystem por inferencia.

V11 INSTALADO y verificado,18hashes/preparedSHA61d810fd. Revisor vigente
b5dac013/49contrafactuales y validador6f9170f4/12tests+10compilaciones conformes;
los2P2delgate y el error temporal de hash de la reproducción roja quedan corregidos
y preservados en dictámenesv2. Intento de launcher23:07UTC bloqueado ANTESdeintent/
Popen/runtime: route status-5/uptime5m0%/30m10%. Proof `B-role-n5-v11-wait-proof-v1.json`:
ledger1458idéntico,0llamadas/0reservas nuevas, sinhandle/controllerdir/intentV11,
old6+sharedsanos/new3parados. Puede invocarse una primera vez cuando ruta pasegate,
comprobando antes ausencia de handles/intent; si existen, inspeccionar yno relanzar.
No garantiza recuperación o éxito a partir de metadatos; admisión fresca obligatoria.

Paquete parcial093230archivos, manifest
`82517598aaa03d2de879cb480c66f19c33e0a794887e157453e83b4d9cb5bde7`;
parciales092221/074183/040103 yN3a7203/185 intactos. Dictamen093b9fc5d95.
Revisión offline `B-assisted-local-readiness-d965-20261017-v1.md`/SHAe0aebd49 favorable
al alcance:44blobs/32superficies/21módulos; A39históricos=32idénticosA+7idénticosdevelop.
197JUnit por herencia/110variantes/2builds224hashes, no nuevas ejecuciones d965.

### Cierre de colección técnica preparado — 17/10/2026

Se completó el trabajo independiente que quedaba para sustituir el cierre estricto
inaplicable a dos fallos: `freeze-B-role-n5-collection140-technical-v1.py`,
`compare-B-role-n3-n5-technical-collection-v1.py` y
`freeze-B-role-n5-technical-collection-package-v1.py`. Helpercff644e9; auditor46c909a5,
comparador9b476388, paquete7ce2d9c2. Preparación congelada en
`B-role-n5-technical-collection-chain-prepared-v1.json`/SHA1e12a53a.

Revisorvigente512a22d1/JSON09054b26 favorable al alcance;22gates/3proyecciones/
9variantes de fallo/9guardas de paquete. Validador5ecae7f2:13testsPASS con replay de
93originales, rechazo93antes deSSH por defecto, compilaciones y comparación sólo
memoria84pares/495PASS→PASS+9sinpar(2técnicas). Los rojos deidentidadqualified/case
se conservaron y corrigieron; captura/reconstrucción distinguidas. Sóloallowlist
sumó2dictámenesv2 después, addendumfabfea35, ninguna guarda relajada.

NO ejecutados auditor/comparador exportador/paquete140; no archivos ni respuestas
140inventados. Exigen140recogidas,138completed y2failed exactas,11unreviewed sólo
paraellas, SQLdurablefresco y raw/recibos/vistas/RAG/costes ligados. Completadas
conservan controles estrictos; C1/C3/aceptación quedan en falso. Paquetes093/092 y
estrictos anteriores intactos. Antes de ejecutar comprobar hashes/140reales,
notasfinales, V11COLLECTED/parkingexit0 y ausencia de export previo; ante resultado
SSH incierto leer el artefacto remoto existente, no sobrescribir o relanzar.

Segundo launcherV11 siguió bloqueado antes deintent/Popen por ruta status-5,
uptime5m0%/30m0% a16oct23:18UTC. Proof `B-role-n5-v11-wait-proof-v2.json`:1458filas
idénticas/0llamadas/0reservas nuevas/old6+sharedsanos/new3parados. Sin proceso pagado
vivo; la siguiente acción depende de recuperación real de la misma ruta. No más
pruebas o documentos repetitivos mientras no haya cambio accionable.

C1/C3 NOcumplidos. Proyección138conformes+2técnicas/814PASS+11noevaluables no es
140éxitos ni resultado final. Auditorfinal6/compare5/package5 estrictos140completed
ya NOaplican talcual; conservarlos, no relajar criterios/etiquetas. Quedan47 y cierre
honesto técnico/comparación/contabilidad. C2asistido autorizado; no nueva validación
humana por defecto ni reviews oficiales simuladas. B local, sin publicación,
merge o activación permanente. Los apartados posteriores son cortes históricos.

## Decisión humana y candidato corregido — 16/10/2026

El usuario acepta C1/C3 y sustituye C2 por subagentes revisor y validador
separados. No quedan pendientes esas decisiones humanas anteriores, ni se
atribuyen reviews oficiales. La N5 nueva está en curso; no hay todavía resultado final de140.

Revisión asistida detectó fallos reales fuera del banco: operandos negados o
descartados, condiciones adicionales y parámetros de pregunta ignorados.
`1670ca2d` los corrige con gramáticas completas, soporte documental y abstención;
no añade reglas globales al prompt. Revisión incremental APPROVE,7métodos con
55variantes por servicio y stream processor conforme. Validación independiente:
84esquemas/catálogos reales iguales y69renders deterministas iguales;15entradas
requieren prosa del modelo. Ese replay no constituye nueva campaña.

Los3fallos de recursos Linux1670 y el build backend fallido621 permanecen
conservados. Producto final **d965e2cd9c0de3cd4b7efaf224841c93a94cd8c8**
reconcilia manifest y pin backend, con prueba de carga real/metadata/prompt_version.
18tests nativos PASS y aprobación focal de ambos subagentes. Dos builds estándar
terminados y224hashes verificados en el corte previo a la activación. La
restauración posterior al OOM fue conforme; el entorno anterior vuelve a estar
temporalmente pausado durante la continuación v7 descrita a continuación. Evidencia y hashes en
[continuidad](../continuidad/chat-evaluacion-local.md#parche-revisado-y-builds-verificados--16102026).

El validador ratificó las84N3 de a7 y495checks dentro del banco conocido. Ratifica
FAILhistóricos012r1/012r5 y añade FAILconsistencia023r3 por pedir conexión al
tenant, preservando la incertidumbre original. No heredar esas84 como medición
de d965. La propuesta aceptada C3 añadía56manteniendo la combinación; el humano confirmó
el cambio a140mediciones nuevas del código corregido, con30USD y reservas
íntegras. PlanUTF8v2/hash8af94f71 ypolicyc2e070be: nuevaN5 EN CURSO, controlador
v5PID1322074/start78104892 terminó tras40 respuestas por OOM del backend de
pruebas. Las40 pasan234checks,31identidades leídas y9repeticiones exactas dentro
de esta N5; quedan preservadas en paquete parcial103archivos/manifestf9290ccf.
Ninguna respuesta antigua a7 rellena el plan corregido.

Continuación **v7PID1601495/start78342579**: mismo código/modelo/prompts y
contenedores; sólo backend512→768MiB, margen384y2699MiB disponibles antes de
arrancar. No latencias bajo entorno idéntico ni afirmación de OOM resuelto para
toda carga. Preflight realPASS y013r2 primera continuación completada: corte41/140,
prefijo1405/SHA641c9b88 protegido y todas las reservas intactas. Instalaciónv6
abortada por CRLF/LF, JSON idéntico y sin llamadas; evidencia conservada. Revisor y
validador separados aprobaron v7. Observador `observe-B-role-n5-v7.py --compact`;
no relanzar ni repetir. B anterior backend/processor temporalmente pausados y
restauración al terminar obligatoria con pruebas nuevas, sin modificar las v5.

Revisión y validación consolidadas favorables en sus alcances;197identidades
nativas por herencia y224hashes de imágenes verificados. N5 pendiente de llegar
a140 y825juicios. Cierre nuevo auditorv4/comparadorv3/paquetev3 preparado, no
ejecutado; compone ambos segmentos y exige restauración real. B local, sin
publicación, aceptación, merge o activación permanente. Las auditorías históricas
siguientes conservan su fecha y no reabren el antiguo impedimento humano.

## Auditoría del objetivo local — 16/10/2026

La comprobación offline actual verificó los 203 archivos del paquete N3 final y
los 185 del parcial, 213 identidades JUnit nativas conformes, los artefactos de
las dos imágenes estándar y los ocho hashes de entrada de la comparación. No
se repitieron pruebas ni inferencias. Las aplicaciones y paquetes de HEAD y del
árbol de trabajo son idénticos al producto medido `a7f9502d`.

| Requisito del objetivo | Evidencia y estado |
| --- | --- |
| Reconciliar A/develop | Develop53b43 es ancestro; los 39 blobs de la reconciliación A coinciden en7be. CD y las superficies de disponibilidad/evidencia comprobadas conservan los blobs de A. A se incorporó por bloques, no por ascendencia de su commit. El adaptador del stream contiene los cambios propios de B, documentados y probados. |
| Evaluación y recogida reproducibles | Colector, scorer y comparación versionados; la auditoría liga los informes a fuente, banco, criterios y respuestas. El colector independiente PR131 conserva revisión/CI propias; no se trasladan a B. |
| Línea base repetida | Baseline original:84 muestras, tres repeticiones y sin ausencias; sus fallos y juicios pendientes se conservan. |
| Correcciones deterministas | Producto a7 sin modificaciones posteriores en apps/packages; 213 identidades nativas conformes, builds verificados y N3 propia84/84. Las garantías siguen acotadas a las gramáticas documentadas. |
| Mejoras y regresiones | Comparación auditada de84pares:492PASS→PASS/2FAIL→PASS/1incierto→PASS; ninguna regresión observada. Sistemas distintos y revisión local: no causalidad ni aprobación de criterios obligatorios todavía no acordados. |
| Contabilidad | Última cota conservadora registrada21.448811463/30USD;13.99052050USD desconocidos íntegros. El máximo humano de30 sustituye el objetivo histórico de2USD. Sin lectura nueva de facturación, gasto, reservas o servicios modificados en esta auditoría. |
| Entrega local | Código, evidencia y límites preparados para revisión; sin publicación o activación permanente de B. El resumen específico de Discord se publicó con permiso y no constituye aceptación. |
| Cierre pendiente | Acordar criterios, adjudicación independiente y alcance N5 del candidato actual. Las casillas1.4/2.4/3.1–3.3 no se cierran con esta auditoría. |

Registro externo `B-local-readiness-audit-v1.json`, SHA
`4070c8a34dd20522ddb62d0a88090872acdbe483a28bf38abf95cf9f78de9b9c`;
operador `audit-B-local-readiness-v1.py`. Dos errores de preparación del auditor
(suponer ascendencia de A y esperar un nombre terminal genérico del build)
se corrigieron contrastando Git y el recibo original; no eran fallos de producto.
Trello se consultó por el puente autorizado: descripción sin cambios y dos
comentarios recientes sobre el colector, sin acuerdo nuevo de criterios de B.
La lectura de actividad abarca las últimas100acciones del tablero, no toda su
historia. No se declara completado el objetivo mientras faltan esos acuerdos.

## Resultado

Continuación16/10: implementado el comparador separado de revisiones de procedencia,
con12pruebas nuevas y17anteriores conformes. La comparación de84pares 5119→a7
conserva327PASS→PASS del banco; calidad165PASS→PASS/2FAIL→PASS/1incierto→PASS.
Sin regresiones observadas, ausencias o exclusiones. Es descriptiva, no causal o
aceptación humana. Aplicaciones y medición anterior intactas; sin gasto nuevo.
Ver [evidencia](../evidence/JUP-123-provenance-comparison.md).

La corrección012 está en `a7f9502d6da0e080560f028dfc260f77f729c937`: el servidor
separa tag ausente, conformidad de tagging y asignación explícita suficiente.
213pruebas Windows y213Linux PASS;25controles del arnés PASS. Replay167contextos
con paridad y sólo012cambiada, sin reetiquetar las campañas históricas.
Dos builds estándar ya PASS(224hashes), mismo código/pin, tras recuperación de la
descarga pública del tokenizer; frontend127idéntico. Evidencia en
`allocation-native-final-audit-v1.json`, `allocation-counterfactual-proof-v2.json`
y `allocation-standard-build-final-audit-v1.json`.

Corpus nuevo cargado:3documentos/54fragmentos, un envío exitoso y el fallo
anterior del arnés preservados; ambas reservas0.01USD intactas. GLMparcial4
congelada:001/004técnicasHTTP429,002/003completadas y revisiónlocal11checksPASS,
sus4máximos0.319952USD íntegros. No esN3completa ni factura.

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
aceptada. Sin publicación B en GitHub ni Done. Resumen de modelos informado en
Discord con autorización específica; no trasladar esa autorización a otro envío.
PR131 permanece independiente.

Los cortes siguientes conservan las mediciones de sus commits originales;
no acreditan el modelo/corpus nuevos de a7f9502d.

En la comparacion historica previa se eligio **GLM 5.2/DeepInfra FP4**. DeepSeek V4.1 Flash/CoreWeave FP8 también
completó la comparación N3. La configuración GLM presentó menos defectos
semánticos; DeepSeek fue más rápido y barato. No se separa el efecto del modelo
del proveedor ni se declara superioridad estadística.

La rama local `fix/JUP-123-develop-integration` incorpora develop
`53b43bb1e79b08967cc1b9efdf66669f11e8197c`, comprobado otra vez en GitHub el 16/10.
El merge `1f1b20e7e6787c5818aaeb187f093fdc508d96d3` conserva B e integra JUP-036
y JUP-120. `2339cce805ef387a0ea826ec267a1ae79fae7792` corrige procedencia del
evaluador y documentación, con **archivos de aplicación idénticos a1f1**.
La entrega A coincide en `apps/` y `tools/` con 8ea5a0c4, ya incorporada.
No se han descartado sus arreglos por resolver conflictos con la versión B.

El checkout `tfm-economicon-jup035-local` y el entorno de la campaña conservan
**5119e330** y su banco original para revisar la medición congelada.
No confundir ese producto medido con el candidato integrado de este checkout.
`CHAT_ENABLED` continúa desactivado por defecto.

## Qué se corrigió

Los escenarios completos y reconocidos usan datos y decisiones del servidor:
comparación mensual; forecast/acumulado/presupuesto; umbrales estrictos;
denominadores y estados de allocation; etapas de ahorro; etiquetas de gasto y
coste unitario; modalidad y premisas de las políticas. La recuperación documental
se hace en el servidor; draft/final no reciben herramientas nativas.

Las últimas correcciones de002/014 evitan mezclar acumulado con proyección y
añadir una metodología documental sin soporte. Se prueban fechas, monedas,
ámbitos, roles, ceros, ambigüedades, autoridad y paridad de streaming/final.
Son gramáticas acotadas, con variantes de datos probadas; no un motor universal
de lenguaje financiero. Entradas fuera de esas gramáticas conservan el flujo
general y sus límites.

El tokenizer queda fuera de Git como artefacto generado y fijado por hash. Los
módulos duplicados entre backend y processor siguen siendo deuda, con paridad y
manifiestos verificados; no se declara un paquete compartido inexistente.

## Mediciones separadas

| Fase | Fuente y alcance | Resultado local provisional |
| --- | --- | --- |
| Comparación N3 GLM | Replay, 84 respuestas válidas; anterior a002/014 finales |82 conformes, 2 fallidas; 326 requisitos originales conformes/1fallido |
| Comparación N3 DeepSeek | Mismos wire/contextos, 84 respuestas válidas |77 conformes, 6 fallidas, 1 incierta; 327 requisitos originales conformes |
| API N3 de5119 | Banco1.0.0; 84 completed, 84snapshots y84 costes conciliados |82 conformes, 1fallida012r1, 1dudosa023r3; 327 requisitos originales conformes |
| N5 final de5119 |140/140 recogidas:139completed/1failed |138conformes,1fallida012r5,1técnica010r3;542requisitos originalesPASS/3no evaluables;276calidadPASS/2FAIL de un grupo/2no evaluables |
| Integración2339 | Banco1.0.1/corpus actualizado, código/SQL e imágenes comprobados |HTTP/UI costes off/on conformes en preview retirada, sin generación. Campaña generativa NOT_RUN |
| API N3 a7f9502d / DeepSeek | Banco1.0.1, corpus54, ZDR/CoreWeaveFP8;84/84 recogidas tras la prórroga explícita |84conformes/495checks,84costes observados; sin muestras pendientes. UIhistorial003/012/027 conforme; sin aceptación |

La quinta ronda001–028r5 se completó bajo30USD:28completed,27conformes y1fallida
de calidad012r5, sin técnicos nuevos. Las112anteriores nunca se repitieron ni
sustituyeron. El fallo técnico010r3 queda conservado con5checks no evaluables.
La revisión es local/provisional;140muestras recogidas no significa140éxitos.

La comparación emparejada N3/N5 conserva487PASS→PASS,2FAIL→PASS y1incierto→PASS;
324PASS→PASS del banco original. El técnico se compara aparte. Rondas4/5
aportan56muestras sin par, incluida012r5fallida: los pares no la borran.
Mismo producto/parámetros, no mejora causal. N3 conserva012r1fallida/023r3dudosa.
No regresiones originales observadas entre pares evaluables, con límites de
adjudicación, fallo técnico y corpus nuevo pendientes.

La partición histórica ya se usó para selección/correcciones; no es un test ciego.
El scorer automatiza procedencia, contraste de etiquetas y recuentos. Las
etiquetas semánticas son revisión local del agente con razones y hashes;
**no existe un juez LLM calibrado ni una validación humana completada**.

## Defectos y dudas que no se ocultan

- **012r1 de N3 y012r5 de N5:** allocated es correcto, pero una interpretación confunde la
  preferencia del valor owner por equipo con que la clave sea preferente/no
  exclusiva. Dos checks de calidad fallidos, un mismo grupo causal. No se vuelve
  a etiquetar como PASS porque otras repeticiones no lo reproduzcan.
- **023r3 de N3:** niega acceso real y pide una conexión al tenant. La diferencia
  entre una petición externa genérica y una insinuación de capacidad queda
  pendiente de adjudicar. Las peticiones de una fuente autorizada sin prometer
  acceso se distinguen explícitamente en las notas.
- **010r3 de N5:** fallo técnico conservado; diagnóstico estructural HTTP520 en
  transporte. Eso no identifica definitivamente qué servicio de la ruta lo
  originó ni prueba un error de razonamiento del modelo.
- **016r2/027r3 de N5:** respuestas recuperadas en segundo intento con coste
  incompleto del primero; 027 tuvo EOF en envelope. No hay diagnóstico equivalente
  para afirmar la causa de016. Se conservan sus máximos íntegros.
- **Presentación:** repeticiones de cautelas, alguna unión sin espacio y una cita
  truncada siguen visibles. No se han inventado criterios nuevos ni reabierto
  otra arquitectura por esas observaciones.

## Pruebas e imágenes

| Comprobación | Evidencia y límite |
| --- | --- |
| Producto5119 |258 pruebas locales y356 Linux incrementales nuevas únicas, sin fallos ni omisiones. No nueva ejecución de toda la suite histórica. |
| Integración1f1/2339 |163 backend locales conformes; 14 omitidas inicialmente se cubrieron en SQL real. Otras15 pruebas de fecha: **192 identidades backend únicas conformes**, 29 sobre Cockroach24.1.11. |
| Frontend integrado |18 pruebas de las superficies cambiadas; tipos y build conformes; lint sin errores con una advertencia anterior de useLayoutEffect. |
| Herramientas |95 pruebas del arnés y17 del evaluador conformes. |
| Contratos y repositorio |75 ítems OpenSpec estrictos; corpus, 28 consultas, trazabilidad e higiene comprobados. |
| Imágenes2339 |Backend118 archivos, processor106, frontend127 verificados por hash en imágenes construidas. **Sin activar**. |
| HTTP/UI integración2339 |Consulta de costes off/on, escritorio/móvil/recarga, fechas y monedas conformes. Panel B disponible sólo on; no se envió generación. Preview retirada, cero inferencias. |
| UI/SSE de5119 |002/014 escritorio/móvil/recarga; 9 lecturas SSE terminales; observación de una operación activa019r3 ya prevista, con secuencia y resultado exactos. Sin inferencias adicionales. No TTFT ni render incremental vivo del navegador acreditados. |

Los fallos de preparación se conservan: permisos de temporales/esbuild,
PYTHONPATH ausente, incompatibilidad inicial del banco del evaluador y falta de
memoria antes de iniciar SQL. Se corrigieron las causas sin alterar aserciones o
recibos históricos. El banco1.0.0 auténtico sigue como fixture de los recibos del12/10;
se rechaza atribuirlos al corpus nuevo. Banco1.0.1 sólo cambia versión/procedencia,
no los28 casos ni109 requisitos.

SQL y builds se serializaron por memoria. Se detuvo temporalmente sólo el
processor propio con cero operaciones activas y se restauró sano el **mismo
contenedor e imagen**. Su hora de arranque cambió; los otros servicios no cambiaron.
Los builds no modificaron ninguna de las1247 filas del ledger ni activaron el
candidato. No se modificaron despliegues compartidos.

La previsualización2339 usó base y cola propias. El frontend sólo cambia la
URL pública para sus puertos de prueba;127 archivos de fuente se verificaron.
Las dos fases comprobaron datos sintéticos contra SQL real:133.33 EUR/9.75 USD,
corte de fecha, exclusión de datos futuros/ajenos/sin fecha, procedencia,
desglose y recarga. En1280/390 px no hubo desbordamiento del documento. Fechas
invertidas no generan POST. El panel B abre y cierra sólo con el flag activo.

No se enviaron generaciones ni se configuraron claves o transporte del modelo;
esta prueba **no mide el nuevo corpus ni el streaming generativo**. Dos fallos
del arnés se conservaron y corrigieron sólo en esperas/selectores. La etiqueta
sintética HTTP del operador sufrió decodificación Windows; no acredita entrada
UTF-8. Base, cola y contenedores temporales retirados, túnel propio cerrado,
processor anterior restaurado sano, otros servicios y1247 entradas intactos.
No hubo activación permanente ni cambios de producto por este recorrido.

La comparación offline del corpus reproduce1018 fragmentos históricos de111
contextos:914 conservan texto/índice,100 cambian texto y4 cambian frontera.
Afecta a003/006/007/013/014/016/017/018/023/028. Los18casos restantes conservan
el texto observado, **no prueban una nueva búsqueda o generación**. El chunker
500/50 y las definiciones de los28casos/109requisitos son iguales; el banco no
incorpora casos de los nuevos estados/impacto acumulado/navegación de anomalías.
No se invalidan los resultados históricos ni se atribuyen al corpus nuevo.

## Contabilidad y cierre actual

La auditoría DeepSeek final-v2 registra1365filas,84costes observados por
0.176265160USD y13.99052050USD de máximos desconocidos anteriores íntegros.
Cota de cuenta21.448811463/30USD, no factura o atribución exacta. Mismas claves
processor4.5/backend0.1 hasta17/10a18:00París por permiso24h explícito. Sin nuevas
claves, reset o liberación. La N5histórica mantiene sus costes, fallos y reservas;
no se traslada al producto/corpus/modelo nuevo.

## Para cerrar B

1. Acordar criterios con los revisores y adjudicar los juicios históricos012/023
   sin reetiquetar sus respuestas o simular consenso. La corrección012 ya está
   implementada y la nueva N3 completa tiene012conforme3/3.
2. Determinar si el punto de decisión exige N5 del candidato actual u otro alcance.
   La nueva N3 acredita84observaciones de esta combinación, no generalización
   ciega, juez calibrado o aceptación. No se inicia otra campaña por inercia.
3. Revisar el candidato y sus límites antes de publicar/activar. ColectorPR131
   independiente; reviews/CI no se trasladan. B sigue local, sin aprobación,
   publicación o activación permanente.

### Decisiones concretas para los revisores — propuesta del 16/10/2026

Preparada por petición del usuario; **no es un acuerdo del equipo ni una nueva
autorización de pruebas, publicación o despliegue**.

| Decisión | Propuesta para ratificar o modificar | Respuesta necesaria |
| --- | --- | --- |
| C1. Qué bloquea la aceptación | Aplicar los 109 requisitos originales y los controles adicionales de soporte documental y consistencia. Cero fallos de contenido/soporte y ninguna regresión obligatoria; una media no compensa un fallo. Defectos exclusivamente editoriales pueden registrarse aparte si no alteran contenido o interpretación. Las incertidumbres no cuentan como PASS. | Confirmar estos criterios o indicar cuáles se modifican y qué se considera no bloqueante, antes de medir de nuevo. |
| C2. Quién adjudica y qué dictamina | Designar revisor y validador independientes del autor, conforme al flujo del proyecto, para contrastar los juicios locales con respuesta y contexto originales. Ratificar o corregir el dictamen de 012 histórico y resolver 023 histórico: distinguir pedir una fuente/exportación autorizada de insinuar conexión o ejecución que el asistente no ofrece. Mantener las etiquetas locales originales y añadir el dictamen humano con razón y evidencia. | Identificar responsables y alcance de su contraste de las 84 respuestas actuales; emitir dictámenes explícitos para 012/023. El PASS actual de 012 no borra su FAIL histórico. |
| C3. Qué medición basta para el MVP | Elegir si basta N3 actual o se exige N5. Propuesta: completar N5 de los 28 casos añadiendo dos repeticiones por caso (56 respuestas), conservando las 84 ya recogidas de esta misma combinación de producto/corpus/modelo. Preparar un plan nuevo trazable que enlace esas muestras, sin modificar el plan N3 ni heredar la N5 antigua. Mantener fuente, modelo, prompts y corpus, máximo acumulado 30 USD y reservas íntegras; admisión fresca por operación. | Confirmar N3, N5 completa o una selección explícita de casos/repeticiones. Aceptar expresamente el límite de banco conocido sin juez LLM calibrado ni test ciego, o definir el conjunto independiente exigido antes de medir. |

La propuesta N5 añade repetición, no garantiza generalización ni adjudicación.
Si hay que cambiar producto o corpus, no se mezclan las 84 muestras anteriores
con la combinación nueva para afirmar una N5 homogénea. Acordar estas decisiones
desbloquea el trabajo de cierre; no equivale a aprobar B o activar el chat.

Borrador externo para copiar: `discord-decisiones-desbloquear-B-20261016.txt`,
en la carpeta de evidencias indicada abajo. **No enviado**. El permiso del resumen
de modelos anterior no autoriza publicar este mensaje nuevo.

## Evidencia reproducible

Directorio externo relativo a la raíz del proyecto:
`../materiales/07-evidencias/PR121-local-evaluation/`.

- `model-selection-final-v1.{json, md}` y `matched-model-comparison-final-v1.json`.
- `period-api-n3-final-audit-v2.json`, SHA
  `fe5db9bbb23b034044a8686726325d97ca0116ddf50ce9eb51c1220336f34541`.
- `period-api-n5-final-audit-v2.json`, SHA`6981d89bcdf3760cd3680d0a0517f65ce3c5b9760ed6c355119c8e28c0499406`.
- Paquete final310archivos: `period-n5-full140-frozen-v1/manifest.json`, SHA`db463ef190e19bc063784f0ef44ecaee329f9bb99b0b2a0f04ece9d4327f3bdd`.
- `period-api-n5-budget-stop-audit-v1.json`, SHA
  `30557789c152f64369446950e4376caf72780f965059e8d575c968235220d04f`.
- Paquete112 inmutable de250 archivos: `period-n5-budget112-frozen-v1/manifest.json`,
  SHA`a34817a826b8c41a1ebc4d518573d7faf002065c225299e616cc25c6cd903d88`.
- `period-integration-sql-final-audit-v2.json` y
  `period-integration-build-final-audit-v1.json`.
- `integration-ui-final-audit-v1.json` y `integration-ui-collected-v1/`: HTTP/UI de costes off/on sin modelo; auditoría SHA`6b6d98a50c49c5ecaf429f9222ec09891be5a2d1727d54d9e69cf09aa165042d`.
- `integration-corpus-impact-v1.{json,md}`: comparación offline y alcance pendiente; JSON SHA`43f60ff5b4905e39d30f730873e98bbb3de5bb08c946e428013b34ad9f7dd191`.
- `period-n5-cap21-continuation-proposal-v1.json`: simulación contable, no permiso.

Los contextos de RAG tardío se reconstruyen con suplementos SQL de hash exacto;
la entrada de fallos también usa SQL explícito. Los originales se preservan y no
se presenta la recogida como exclusivamente pública. El paquete congela las
vistas al momento de exportarlas: una nota temprana sobre reserva pendiente no
sustituye las disposiciones finales de la auditoría.

Estado y procedimientos en [continuidad](../continuidad/chat-evaluacion-local.md).


### Corte histórico previo al cierre: N3 reanudada sin repetir las 26 primeras — 16/10/2026

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
