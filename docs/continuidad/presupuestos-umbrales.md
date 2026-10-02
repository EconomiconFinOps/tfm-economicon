# Presupuestos y umbrales

Verificado: 2026-10-01. Origen: JUP-029 — Presupuestos y umbrales,
chat `01a0f8e2-56cb-76a1-a247-b7adc60f8943`.

## Alcance y decisiones

El usuario pidio empezar por definir presupuesto, periodo y umbrales y probar
consumo/desviaciones. [Tarjeta](https://trello.com/c/pBICTDDh) consultada mediante
el puente exclusivo DockerServer `/home/danteadmin/economicon-collaboration`,
snapshot `snapshot-20261001T191353Z.json`. Roles: Alejandro liderazgo, Lucia
pairing, Paris revision, Victor validacion; no se atribuye participacion realizada.

Rama `feat/JUP-029-budget-thresholds` desde `origin/develop` de0d62e,
checkout `tfm-economicon-jup029`. Primer incremento: POST autenticado
`/billing/budget/evaluate` sin persistencia, con periodo [inicio, fin) UTC,
moneda unica y umbrales positivos ordenados. Default 80/100; comparacion antes
del redondeo. Desviacion = consumo - presupuesto completo, no forecast.

Reutiliza JUP-026 para costes exactos a centimos, permisos, separacion de monedas
y rechazo 409 de fuentes ambiguas. No convierte datos ausentes en cero; totales
parciales generan evaluacion provisional. [Contrato](../manuals/budget-evaluation.md),
[OpenSpec](../../openspec/changes/jup-029-budget-thresholds/design.md),
[evidencia](../evidence/JUP-029-validation.md).

## Pendientes

Pruebas confirmadas: backend 377 passed/18 skipped; presupuesto y billing con
Cockroach real 64 passed/0 skipped; OpenSpec 36/36, trazabilidad, higiene y
compilacion correctas. El primer intento de Cockroach fallo por ausencia de
tunel al Docker remoto; corregido y repetido con exito, sin cambios de producto.

[PR #61](https://github.com/EconomiconFinOps/tfm-economicon/pull/61) abierta contra
develop. Trello actualizado y releido: rama, PR, evidencia y alcance del primer
incremento enlazados; estado **30 — En curso**, criterios generales sin marcar.
CI iniciada; JUP policy correcto en la primera consulta, resto en curso.

Pendientes pairing/revision/validacion independientes de los roles
asignados. La tarjeta padre permanece abierta: persistencia, UI, integracion con
agente y alertas no forman parte de este primer incremento. No se envio Discord.

## Actualizacion y revalidacion — 2026-10-02

Por peticion del usuario, merge sin conflictos de develop `11d63ea` en
`5ee5862` (JUP-099, JUP-096, JUP-100). Backend 377 passed/18 skipped;
Cockroach aislado 64 passed/0 skipped; OpenSpec 38/38 y politica de revisiones
57/57. Sin cambios adicionales al producto. Evidencia actualizada.
Paris tiene solicitud formal en GitHub desde el 01/10; no hay reviews aun.
El nuevo flujo exige `Revision JUP-029` y `Validacion JUP-029`: primera
favorable Comment, segunda Approve si ambas satisfechas. No confundir esta
revalidacion automatizada con la validacion independiente de Victor.
