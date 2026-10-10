# Deteccion de anomalias de coste — JUP-030

Verificacion: 2026-10-10. Encargo: «Implementa JUP-030 — Detectar anomalias de coste».
Origen conocido: despacho desde chat `01a1248a-4e9e-7963-a891-5d8cb49345a6`;
identificador del chat de implementacion no suministrado.

- [Tarjeta](https://trello.com/c/ScxJi1TO), P1 Valor FinOps. Descripcion y roles
  contrastados el 10/10 mediante `DockerServer:/home/danteadmin/economicon-collaboration`.
- Rama propia `feat/JUP-030-cost-anomalies`, worktree `tfm-economicon-jup030`,
  base `origin/develop` `c2995a118d419dfe725247bac9c6f219a3f0ea77`.
  Checkout compartido y trabajo previo de otras tarjetas preservados.
- Liderazgo Lucia Mateo; pairing Paris Arcos Martin; revision Victor Mendez;
  validacion Alejandro Aguado. Asignaciones conservadas, sin acreditar participacion.
  La contribucion tecnica automatizada no sustituye ninguno de esos dictamenes.

## Alcance y decisiones

POST autenticado `/billing/anomalies/evaluate`: reglas configurables por
importe absoluto o aumento frente al periodo anterior de igual duracion,
con divisa explicita, grupos y pruebas. Reutiliza billing v2; no introduce
otra consulta SQL ni modifica el panel demo de JUP-057.

El resultado entrega candidatos y evidencia versionada para JUP-038:
costes, periodos, reglas, calidad, identificador estable y huella de evidencia.
La causa permanece `not_established`. Comparar agregados no demuestra anomalia
estadistica, causalidad, ahorro ni integridad temporal de la ingesta.
No se convierten divisas ni se rellenan datos ausentes con ceros.

Contrato y ejemplos: [cost-anomalies.md](../api/cost-anomalies.md).
OpenSpec: [jup-030-cost-anomalies](../../openspec/changes/jup-030-cost-anomalies/proposal.md).
La regla diaria del contrato JUP-084 (`>20%` y `>100 EUR/day`) es diferente:
no se declara implementada por este evaluador de periodos configurables.

## Verificacion y siguientes pasos

La evidencia tecnica por criterio se registra en
[JUP-030-validation.md](../evidence/JUP-030-validation.md).
150 pruebas focales pasaron sin omisiones, incluidas dos nuevas contra
CockroachDB v24.1.11. Regresion backend: 997 PASS, 21 integraciones externas
omitidas; compilacion PASS. OpenSpec 56/56; gobernanza 89 tests PASS.
Entorno exclusivo Linux eliminado al terminar; los intentos Windows lentos
interrumpidos no se cuentan como evidencia favorable.
Pendientes: participacion real, review y validacion independientes, integracion
del consumidor JUP-038, alertas persistentes/notificaciones y conexion del panel.
Mantener esos limites al evaluar el cierre de la tarjeta; no marcarla Hecho
por la sola existencia de la contribucion tecnica. No se enviaron mensajes Discord.
