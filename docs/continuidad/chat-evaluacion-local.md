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
