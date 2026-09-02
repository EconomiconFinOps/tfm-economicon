# Evidencia JUP-080

- Fecha: 2026-08-26.
- Trello: https://trello.com/c/yNNs74Vn
- Rama: `docs/JUP-080-delivery-roadmap`.
- Base: `develop` en `e3889cc`.

## Fuentes verificadas

- Guion oficial `materiales/01-requisitos/Guion-proyecto-Jupiter.pdf`, cuatro
  paginas inspeccionadas visualmente y mediante extraccion de texto.
- Trello completo: 47 tarjetas P0; 33 Backlog, una Preparada, cuatro En revision
  y nueve Hechas; ninguna tenia fecha limite al iniciar JUP-080.
- Discord en modo lectura: el 11/08/2026 Alejandro comunico como base del equipo
  entrega documental 23/10/2026, defensa 29/10/2026, freeze documental 16/10 y
  estabilizacion tecnica una semana antes. El PDF no confirma estas fechas.
- Repositorio y PR abiertos: `develop` esta en `e3889cc`; JUP-048 permanece en
  PR #12 pendiente de revision humana, con CI en verde.

## Trazabilidad con el guion

El roadmap reserva hitos explicitos para IA generativa, pgvector/RAG, API de
modelo fundacional, MVP funcional, CI/CD, Docker, logging/monitorizacion,
arquitectura, negocio, evaluacion, contribucion individual, memoria de hasta 20
paginas y defensa de 10-20 minutos por los cuatro integrantes.

Tambien refleja el peso de evaluacion: entregables 80 % y presentacion 20 %, con
10 % negocio, 20 % diseno, 30 % implementacion y 20 % DevOps dentro de los
entregables. El video demo de 5-10 minutos se mantiene opcional.

## Decisiones de planificacion

- Reconciliar primero las capacidades ya implementadas para no ejecutar dos
  veces 33 tarjetas P0 aparentes.
- Congelar cambios funcionales el 09/10 y memoria/evaluacion el 16/10.
- Mantener un WIP maximo de dos implementaciones y una linea documental.
- Mantener P2 fuera del MVP y condicionar P1 a terminar M4 sin riesgo.
- No aplicar fechas a las otras tarjetas hasta que el equipo apruebe el plan.
- No publicar comunicaciones externas sin autorizacion previa de Alejandro.

## Validacion ejecutada

- Roadmap: 5/5 pruebas; fechas ordenadas, 47 P0 unicas, requisitos Jupiter,
  limites de alcance y activacion controlada verificados.
- Workflow/rulesets: 7/7; politica de PR: 11/11; trazabilidad JUP: 7/7.
- JUP-080 y las 12 changes JUP activas validas.
- OpenSpec estricto: 15/15 items.
- Higiene: 6/6 pruebas y 301 archivos aceptados.
- Servicios: Azure API 58, backend 10 y processor 126 pruebas superadas.
- Build completo del monorepo y frontend de produccion superados.
- Pull request: https://github.com/EconomiconFinOps/tfm-economicon/pull/13
- Primera ejecucion remota completa:
  https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/32984910871;
  los seis checks obligatorios terminaron correctamente.

Pendiente: registrar la revision del equipo y, tras aprobar, aplicar las fechas
a las demas tarjetas de Trello.

## Cierre posterior de estado — 2026-08-28

El PR #13 fue fusionado en `develop` mediante el commit `d45178e`. La evidencia
anterior conserva deliberadamente la fotografia tomada durante la ejecucion de
JUP-080; ya no describe el estado actual de JUP-048 ni del PR.

La reconciliacion M1 creo JUP-085, JUP-086 y JUP-087 como P0. JUP-088 actualiza
la captura versionada de 47 a 50 tarjetas, las asigna a M1 y hace que el test
derive la cobertura desde `JUP-080-milestones.json`. La aprobacion del calendario
y la confirmacion institucional de fechas continuan pendientes.

## Contraste de alcance — 2026-09-02

La lectura del tablero mediante la integracion de `DockerServer` encontro 52
P0: las 50 de la captura del 28/08 mas JUP-090 y JUP-091. Ninguna de las dos
tarjetas nuevas indica hito ni fecha limite. El roadmap registra el desfase y
la tarea 4.5 mantiene pendiente acordar su asignacion; las pruebas del JSON
acreditan solo la cobertura de las 50 P0 historicas. JUP-088 es coordinacion
de M1 (04/09), no una P0 adicional. No se han modificado fechas en Trello.
