# Presupuestos y umbrales

Actualizado: 2026-10-02. [JUP-029](https://trello.com/c/pBICTDDh) —
[PR #61](https://github.com/EconomiconFinOps/tfm-economicon/pull/61).

## Alcance y decisiones

El usuario pidio empezar por definir presupuesto, periodo y umbrales y probar
consumo/desviaciones. [Tarjeta](https://trello.com/c/pBICTDDh) como fuente de
alcance y roles: Alejandro liderazgo, Lucia
pairing, Paris revision, Victor validacion; no se atribuye participacion realizada.

Rama `feat/JUP-029-budget-thresholds` desde `origin/develop` de0d62e,
base de la implementacion original. Primer incremento: POST autenticado
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
CI tecnica de `1eaf692`: [7/7 correcta](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37052113107).

Pendientes pairing/revision/validacion independientes de los roles
asignados. La tarjeta padre permanece abierta: persistencia, UI, integracion con
agente y alertas no forman parte de este primer incremento. No se envio Discord.

## Actualizacion y revalidacion — 2026-10-02

Por peticion del usuario, merge sin conflictos de develop `11d63ea` en
`5ee5862` (JUP-099, JUP-096, JUP-100). Backend 377 passed/18 skipped;
Cockroach aislado 64 passed/0 skipped; OpenSpec 38/38 y politica de revisiones
57/57. Sin cambios adicionales al producto. Evidencia actualizada.
Paris tiene solicitud formal en GitHub desde el 01/10; su review posterior
del 02/10 se recoge abajo y sustituye el estado anterior sin reviews.
El nuevo flujo exige `Revision JUP-029` y `Validacion JUP-029`: primera
favorable Comment, segunda Approve si ambas satisfechas. No confundir esta
revalidacion automatizada con la validacion independiente de Victor.

## Correccion de la revision documental — 2026-10-02

[Paris solicito cambios](https://github.com/EconomiconFinOps/tfm-economicon/pull/61#pullrequestreview-5396064751)
de alcance y referencias locales. Retirada de esta PR la obligacion global
de continuidad de AGENTS.md; eliminados identificador de sesion, ruta del
entorno y snapshot local de este resumen. Se conservan contrato, OpenSpec,
evidencia y decisiones tecnicas.

La convencion comun se trata en [JUP-101](https://trello.com/c/ReMOdXEK) /
[PR #64](https://github.com/EconomiconFinOps/tfm-economicon/pull/64), propuesta
separada aun pendiente de acuerdo. El endpoint no depende de su integracion.
Esta correccion es solo documental; no modifica producto, pruebas ni la base
integrada `11d63ea`. Las cifras de ejecucion anteriores conservan su fecha y
no representan una nueva ejecucion funcional ni una validacion independiente.

Pendientes: nueva revision de Paris para levantar Request changes, validacion
de Victor sobre la combinacion afectada por JUP-096 y pairing de Lucia.
El avance posterior de develop con JUP-050 requiere actualizar y comprobar
la combinacion antes de integrar; no se da por probado en esta correccion.


## Reconciliacion posterior a PR #61 — 2026-10-10

PR #61 fue integrada por Victorh1397 el 08/10/2026 a las 00:24:28 UTC en
`8cc5db0b8f96b7289f9b90dfed42527b76d0222d`. Esta entrega posterior incorpora
las dos regresiones propuestas por Victor: normalizacion del cero negativo y
maximos documentados/comparacion exacta con 26 digitos. El manual explica el
redondeo previo del total de billing v2. No cambia codigo de producto.

Las siguientes revisiones pertenecen a PR #61, no aprueban esta entrega:
- [Paris](https://github.com/EconomiconFinOps/tfm-economicon/pull/61#pullrequestreview-5408848343), sobre 0c9f6f0: 14 archivos, 12 enlaces y dos anclas, cuatro casos de configuracion y cuatro de calculo. Sin suite completa ni servicios reales.
- [Victor](https://github.com/EconomiconFinOps/tfm-economicon/pull/61#pullrequestreview-5407722492), sobre 0c9f6f0: backend estilo CI 626/29; presupuesto/billing 64/0 (8 Cockroach y 56 unitarios/SQLite); seleccion ampliada 250/0, adversarias 69 y 30 llamadas HTTP (corrige 31). Stack development/mock. Suite completa Cockroach sin conclusion por su entorno; managed_resolver no es hallazgo confirmado. Produccion/LiteLLM real no probados en Compose.

Las cifras historicas conservan fecha, SHA y autoria. La consulta del 10/10
no encontro nueva nota de conformidad de Lucia en Trello. El acuerdo operativo
06/10 admite aportaciones o visto bueno explicito mediante contraste asincrono,
registrado por la persona asignada en Trello; no exige sesion, commit coautor
ni repetir baterias. No se atribuye participacion no observada.

Pendientes: conformidad Lucia, archivo OpenSpec con actualizacion conjunta de
sus enlaces y reviews propias de esta entrega. Las tareas distinguen reviews
anteriores completadas del pairing pendiente. La tarjeta padre sigue abierta:
persistencia, UI, agente, forecast y notificaciones quedan fuera del incremento.
Las secciones anteriores son evidencia historica, no el estado actual.

Entrega posterior preparada desde develop412ae411: 50 pruebas correctas/1
omitida, OpenSpec57/57 e higiene correctos; comandos y limites en
[la evidencia](../evidence/JUP-029-validation.md). Rama docs/JUP-029-budget-closure;
publicacion en borrador, pendiente pairing y archivo.
