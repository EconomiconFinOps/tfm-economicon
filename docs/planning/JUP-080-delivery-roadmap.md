# JUP-080 - Roadmap hasta la entrega y defensa

- Trello: https://trello.com/c/yNNs74Vn
- Fecha de corte inicial: 2026-08-26.
- Reconciliacion de cobertura P0: 2026-08-28.
- Entrega documental de trabajo: 2026-10-23.
- Defensa de trabajo: 2026-10-29.
- Estado de las fechas: base comunicada por el equipo en Discord; debe
  contrastarse con campus o tutor antes del 2026-08-28 porque el guion no
  contiene fechas de calendario.

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

## Diagnostico de partida

La captura inicial contenia 47 tarjetas P0. Tras la reconciliacion M1 del
27/08/2026, Trello contiene 50 tarjetas P0: JUP-085, JUP-086 y JUP-087 cubren
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

La asignacion completa y procesable esta en `JUP-080-milestones.json`.

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
