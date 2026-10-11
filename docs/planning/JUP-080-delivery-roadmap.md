# JUP-080 - Roadmap hasta la entrega y defensa

- Trello: https://trello.com/c/yNNs74Vn
- Fecha de corte inicial: 2026-08-26.
- Reconciliacion de cobertura P0: 2026-08-28.
- Entrega documental de trabajo: 2026-10-23.
- Defensa de trabajo: 2026-10-29.
- Estado de las fechas: base comunicada por el equipo en Discord; debe
  contrastarse con campus o tutor antes del 2026-08-28 porque el guion no
  contiene fechas de calendario.

## Reconciliacion y recuperacion — 11/10/2026

Este apartado sustituye los recuentos y pendientes de asignacion de agosto y
septiembre; conserva los hitos originales como baseline historico. Consulta
del puente exclusivo DockerServer a las 15:12:03Z: **65 P0, 54 Hecho y 11
abiertas**. La captura reducida reproducible esta en `JUP-080-p0-snapshot.json`;
Trello sigue siendo la fuente del estado operativo.

Las 50 P0 historicas conservan su asignacion. Se añaden JUP-084 a M3;
JUP-090/091/092/093/094/095/098/099/103/104/105 a M4, como bloque de migracion
y validacion frontend; JUP-109/110/111 a M6. Cada una de las 65 aparece una sola
vez. La asignacion retrospectiva no acredita entrega en la fecha del hito.

La instruccion del usuario del 11/10 autoriza sustituir los roles humanos de
JUP-080 por subagentes. Liderazgo: agente principal; pairing: `/root/pairing`;
revision y validacion: subagentes independientes. Sus dictamenes se registran
en la evidencia de JUP-080 y la PR, sin atribuir aprobaciones a los cuatro
integrantes ni acreditar su contribucion academica. Esta excepcion solo cubre
JUP-080; no inicia ni cierra las otras tarjetas.

### Objetivos internos de recuperacion

| Objetivo | Fecha Europe/Paris | Puerta comprobable |
| --- | --- | --- |
| JUP-080 | 11/10 | Roadmap reconciliado, dictamenes y decision de calendario |
| JUP-035/036 | 13/10 | Vertical integrado con proveedor real, datos, citas y aislamiento por tenant |
| JUP-054/071 | 15/10 | Pruebas criticas y robustez sobre el mismo candidato; campaña final con instrumentos 067/069/070 |
| JUP-062/063/109/110 | 16/10 | Una linea documental secuencial: negocio, IA, evaluacion y conclusiones; memoria <=20 paginas y resultados trazables |
| JUP-065 | 20/10 | Candidato empaquetado y ensayo reproducible desde cero |
| JUP-066 | 27/10 | Guion y ensayo de 10 a 20 minutos; cuatro intervenciones reales |

Son objetivos condicionados a capacidad y dependencias, no estimaciones de
esfuerzo ni compromisos de personas ausentes. El JSON separa `recovery_plan`
de los hitos originales. No se asignan vencimientos retrospectivos a las 54
tarjetas Hecho ni se modifica su estado o evidencia.

Se conserva el WIP de dos implementaciones y una linea documental/evaluacion:
035/036 preceden a 054/071; 062 -> 063 -> 109 -> 110 comparten una linea. No se
inicia una cuarta tarjeta para compensar retrasos. M3/M4 y la aceptacion integral
de M5 no se consideran acreditados por los cierres individuales. En particular,
052 Hecho no demuestra que el candidato generativo final este desplegado; los
instrumentos 067/069/070 Hecho tampoco acreditan la campaña final.

El freeze funcional del 09/10 queda como objetivo historico incumplido para el
vertical pendiente: se admite terminar exclusivamente el P0 ya acordado, sin
ampliar funcionalidades. Se mantiene el objetivo 16/10 para memoria/evaluacion,
20/10 candidato, 23/10 entrega de trabajo, 27/10 ensayo y 29/10 defensa. La
confirmacion institucional sigue pendiente; aprobar el plan mediante subagentes
no sustituye evidencia del campus o tutor.

Revision de puertas: 13/10 recorrido integrado, 15/10 pruebas/evaluacion,
16/10 memoria, 20/10 paquete y demo. Si una falla, registrar evidencia faltante,
impacto y nueva decision en JUP-080; retirar primero P1 y mantener P2 fuera.
No reducir evaluacion, observabilidad ni requisitos de defensa para aparentar
cumplimiento. El 27/10 es el objetivo interno de ensayo conservado; una referencia
historica al 28/10 no lo modifica sin decision registrada.

Pairing, revision y validacion independientes son favorables al plan operativo
el 11/10; los dictamenes estan en `docs/evidence/JUP-080-validation.md`.
La activacion de fechas permanece pendiente de decision sobre el calendario.
Se aplicara solo el plan explicito a P0 abiertas, con comparacion de
estado previo, registro por tarjeta y lectura posterior. Cualquier cambio
concurrente se revisa antes de escribir. No se publican mensajes en Discord.

## Objetivo y restricciones

El guion exige un MVP funcional de IA generativa, base vectorial, API de modelo
fundacional, CI/CD, monitorizacion y logging. Tambien exige arquitectura y valor
de negocio documentados, contribucion individual de todos, codigo y contenedores
entregables, memoria de un maximo de 20 paginas y una defensa de 10 a 20 minutos
con participacion de los cuatro integrantes. El video demo de 5 a 10 minutos es
opcional.

La calificacion se reparte entre entregables (80 %) y presentacion (20 %). Dentro
de los entregables pesan caso de negocio (10 %), diseno tecnico (20 %),
implementacion (30 %) y ejecucion/DevOps (20 %). El calendario protege tiempo
para las cuatro areas; no concentra memoria y evaluacion en la ultima semana.

## Diagnostico historico de partida (agosto-septiembre)

La captura inicial contenia 47 tarjetas P0. Tras la reconciliacion M1 del
27/08/2026, la captura versionada del 28/08 contiene 50 tarjetas P0: JUP-085, JUP-086 y JUP-087 cubren
respectivamente el contrato de sesion demo, el aislamiento por tenant y la
calidad minima del frontend. La distribucion por listas cambia durante la
ejecucion y se consulta en Trello; el mapa JSON fija la captura de alcance, no
el estado operativo. El numero bruto exagera el trabajo restante porque el repositorio
ya contiene ingesta Azure, API simulada, Docker Compose, pgvector, pruebas, CI,
OpenSpec y documentacion que cubren total o parcialmente varias tarjetas antiguas.

La primera semana no reimplementa esas capacidades. Revisa criterios de
aceptacion y cierra la tarjeta cubierta o crea un residual concreto cuando falte
algo. Esta recalibracion es necesaria para obtener una ruta viable en ocho
semanas.

Contraste historico del 02/09/2026, superado por la reconciliacion del 11/10,
mediante el puente de Trello de `DockerServer`: el
tablero tenia 52 P0, al incorporar [JUP-090](https://trello.com/c/DtlNd0u0) y
[JUP-091](https://trello.com/c/pVfcfvhu). Ambas tarjetas pertenecian al inventario
de migracion frontend y no indicaban hito ni fecha limite; su asignacion quedaba
pendiente de reconciliacion en JUP-080. En aquel corte, el JSON y sus pruebas
verificaban las 50 P0 del 28/08. La reconciliacion del 11/10 resuelve el desfase.

## Hitos y puertas de salida

| Hito | Fecha | Resultado exigido | Puerta de salida |
|---|---:|---|---|
| M0 | 28/08 | Roadmap y alcance base | Fechas contrastadas o riesgo registrado; P0 congelado; WIP acordado |
| M1 | 04/09 | Backlog reconciliado | JUP heredadas contrastadas con codigo/evidencia; no quedan duplicados ambiguos |
| M2 | 11/09 | Runtime reproducible y secretos seguros | OpenRouter rotado fuera de chats/Git; Docker smoke reproducible; configuracion documentada |
| M3 | 25/09 | Vertical IA/RAG real | Corpus -> chunks -> embeddings -> pgvector -> retrieval -> LLM con citas; tests y coste medidos |
| M4 | 02/10 | Vertical funcional FinOps | Usuario consulta costes/KPI Azure desde UI y recibe respuesta trazable por tenant |
| M5 | 09/10 | RC1 desplegada | CI/CD, logging, metricas, trazas, dashboard de salud y pruebas criticas en dockerserver |
| M6 | 16/10 | Freeze de memoria y evaluacion | Memoria <=20 paginas, arquitectura, contribuciones, matriz de metricas y resultados cerrados |
| M7 | 20/10 | Candidato de entrega | Codigo, imagenes, scripts, memoria y demo ensayados desde cero; decision sobre video opcional |
| M8 | 23/10 | Entrega documental | Paquete entregado y checksum/tag de release registrado |
| M9 | 27/10 | Ensayo final | Presentacion de 10-20 minutos, cuatro intervenciones y ronda de preguntas cronometrada |
| M10 | 29/10 | Defensa | Los cuatro presentan, argumentan decisiones y justifican su aportacion individual |

Los checkpoints intermedios son 04/09, 11/09, 18/09, 25/09, 02/10, 09/10,
16/10, 20/10, 23/10, 27/10 y 29/10. Cada checkpoint actualiza Trello con
evidencia, riesgo y siguiente objetivo, pero cualquier mensaje externo requiere
autorizacion previa de Alejandro.

## Alcance por hito

La asignacion completa de la captura del 11/10, en formato procesable, esta en
`JUP-080-milestones.json`, junto con los identificadores de la captura historica
del 28/08. Las fechas originales no se reinterpretan como fechas de finalizacion.

[JUP-088](https://trello.com/c/RJjK2Z6L) coordina la reconciliacion documental de
M1 (04/09/2026) mediante la [PR #19](https://github.com/EconomiconFinOps/tfm-economicon/pull/19).
No es P0 y por ello no se añade a `p0_snapshot` ni a la asignacion de las 50 P0.
La consulta historica del 02/09 mantenia pendientes la aprobacion del roadmap y
la confirmacion institucional de fechas en JUP-080; el estado actual se registra
en el apartado de reconciliacion y en su evidencia.

- M1 cierra o divide el trabajo ya cubierto: JUP-013/014, JUP-019, JUP-048 a
  JUP-051, JUP-054, JUP-072 a JUP-079 y JUP-082/083; ademas formaliza el
  baseline heredado mediante JUP-085/086/087 antes de iniciar su residual.
- M2 prioriza JUP-053. Una credencial publicada en un chat se considera
  comprometida aunque tenga limite de gasto.
- M3 ejecuta JUP-020 a JUP-025 y JUP-036 como un vertical RAG real, no como
  componentes aislados.
- M4 entrega JUP-026, JUP-035 y JUP-055 como recorrido de producto minimo.
- M5 concentra JUP-042/043/044/047/052 y cierra cambios funcionales el 09/10.
- M6 mantiene documentacion en paralelo desde agosto y cierra JUP-060 a JUP-064
  y JUP-067 a JUP-071 el 16/10.
- M7 prepara JUP-065; M9 prepara JUP-066.

P1 solo entra si M4 termina en fecha y no amenaza M5/M6. P2 permanece despues
del MVP. Una desviacion no se compensa eliminando evaluacion, observabilidad,
documentacion o participacion individual: se reduce primero el alcance P1.

## Cadencia y limite de trabajo

- Maximo: dos tarjetas de implementacion P0 y una de documentacion/evaluacion En
  curso simultaneamente.
- Todo cambio pasa por rama JUP, PR, CI y evidencia Trello/OpenSpec.
- Cada tarjeta conserva cuatro personas distintas para liderazgo, pairing,
  revision y validacion. La asignacion no cuenta como participacion hasta que
  existe evidencia real.
- Los viernes se revisa avance, riesgos, coste de OpenRouter y cumplimiento de
  la puerta del hito. La memoria se actualiza semanalmente desde M1.
- A partir del 09/10 solo entran correcciones, pruebas, observabilidad,
  documentacion y preparacion de entrega.

## Rotacion de coordinacion por hito

Esta tabla coordina el hito; no sustituye los roles de cada tarjeta.

| Hitos | Liderazgo | Pairing | Revision | Validacion/documentacion |
|---|---|---|---|---|
| M0-M1 | Victor | Alejandro | Lucia | Paris |
| M2-M3 | Lucia | Paris | Victor | Alejandro |
| M4-M5 | Alejandro | Lucia | Paris | Victor |
| M6-M7 | Paris | Victor | Alejandro | Lucia |
| M8-M10 | Equipo completo | Equipo completo | Equipo completo | Equipo completo |

## Evidencia minima semanal

1. Tarjetas cerradas, abiertas y bloqueadas con enlaces a PR.
2. CI, pruebas y smoke de Docker relevantes.
3. Captura o datos reproducibles del vertical funcional.
4. Matriz de contribuciones actualizada con acciones reales.
5. Estado de memoria, evaluacion y riesgos contra las fechas de freeze.

Las fechas propuestas para las tarjetas no se aplican masivamente hasta que el
equipo apruebe este roadmap. Tras la aprobacion, el JSON actua como fuente
versionada para actualizar Trello sin reinterpretar el plan.
