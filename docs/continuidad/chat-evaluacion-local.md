# Evaluación local de JUP-035

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
