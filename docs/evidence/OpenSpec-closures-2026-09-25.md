# Revision de cierres OpenSpec — 2026-09-25

## Resultado y alcance

La observacion de [Lucia del 24/09](https://discord.com/channels/1477630870541303861/1477630871627370702/1552737274410700851)
es correcta: JUP-053, JUP-081 y JUP-084 estan en `70 — Hecho`, sus PR estan
aprobadas e integradas y sus cambios seguian activos en `origin/develop`
`3a1001d`. Esta rama propone archivarlos y promover sus requisitos a las specs
canonicas. No modifica codigo de producto ni supone un merge de este archivo.

| JUP | Integracion comprobada | Evidencia y limite |
| --- | --- | --- |
| [JUP-053](https://trello.com/c/2UCJTDhi) | [PR #33](https://github.com/EconomiconFinOps/tfm-economicon/pull/33), 10/09, `1ff8e071f83a58f630c496740d712e8c0e2cc443` | Victorh1397 aprobo el head integrado. CI final: siete checks correctos. [Evidencia](JUP-053-validation.md). |
| [JUP-081](https://trello.com/c/g91V6TXp) | [PR #15](https://github.com/EconomiconFinOps/tfm-economicon/pull/15), 02/09, `979acb19a9103d0865b5cb3f97b47782b9208f72` | Victorh1397 aprobo el head integrado. Seis checks correctos. [Evidencia](JUP-081-validation.md); tarea 3.4 pendiente de participacion atribuible. |
| [JUP-084](https://trello.com/c/m1i7iXBm) | [PR #17](https://github.com/EconomiconFinOps/tfm-economicon/pull/17), 02/09, `2f16be351f5a338b6d7e6c84f2bc61e9448d0ac7` | Victorh1397 aprobo el head integrado. Seis checks correctos. [Evidencia](JUP-084-validation.md); tarea 3.5 pendiente de participacion atribuible. |

Los tres commits son ancestros de la base inspeccionada. CI historica final:
[JUP-053](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/34501445459),
[JUP-081](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/33695218204),
[JUP-084](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/33696643437).
Los intentos fallidos/cancelados anteriores de JUP-053 siguen siendo historicos.

## Residuales que debe resolver la revision

Las descripciones de Trello del 08/09 ya documentaban la excepcion de
participacion y archivo para JUP-081 y JUP-084. No se encontro nueva evidencia
atribuible que permita marcar sus tareas 3.4 y 3.5. Se conservan sin marcar,
incluidas en el archivo propuesto. La aprobacion de Victor se registra como
suya; no acredita automaticamente pairing ni validacion de otras personas.
El mensaje de Lucia confirma el estado operativo, pero no certifica esos roles.

El PR se presenta como borrador: antes de integrar el archivo de JUP-081 y
JUP-084, el equipo debe aportar la evidencia pendiente o aceptar explicitamente
el archivo tecnico con ese residual. Esta auditoria no declara esa excepcion
aceptada ni inventa participacion.

JUP-053 conserva el alcance acotado y las excepciones de su QA historica.
RF-053-004 fue corregido por JUP-020 mediante PR #34; el cierre y la evidencia
posterior estan en [JUP-020](JUP-020-validation.md). El smoke FAIL historico de
JUP-053 no se reescribe. Tampoco se atribuyen nuevas rotaciones de credenciales,
validacion productiva, TLS o pruebas con proveedores reales.

JUP-084 entrega un contrato; promover sus requisitos no acredita que se hayan
implementado todas las herramientas, el bucle LLM o los proveedores reales.
Se conservan las condiciones de JUP-078 y los limites del dataset.

## Archivo y fuentes

- [JUP-053](../../openspec/changes/archive/2026-09-25-jup-053-secure-runtime-secrets/proposal.md): crea `secure-runtime-secrets` y modifica `demo-auth-credentials`.
- [JUP-081](../../openspec/changes/archive/2026-09-25-jup-081-collaboration-bridge/proposal.md): crea `controlled-collaboration-bridge`.
- [JUP-084](../../openspec/changes/archive/2026-09-25-jup-084-finops-agent-tool-contract/proposal.md): crea `finops-agent-tool-contract`.

Se utilizo `openspec archive <change> --yes`, manteniendo validacion y
promocion de specs. La herramienta advirtio una tarea incompleta en JUP-081 y
otra en JUP-084; se conservan expresamente para revision. Tambien aviso, sin
bloquear, del numero de deltas de JUP-084. Se corrigen enlaces relativos de
JUP-053 y el Purpose generado automaticamente, sin alterar sus requisitos.

Trello y Discord se consultaron exclusivamente mediante el puente desplegado
en `/home/danteadmin/economicon-collaboration` de DockerServer. `sync` completo
termino correctamente y genero `snapshot-20260925T093023Z.json`; el mensaje
de Lucia esta incluido. Los snapshots internos y las credenciales no se
versionan. No se publicaron mensajes en Discord ni se modificaron tarjetas.

La descripcion de JUP-053 en Trello aun contiene enlaces y checklist de
plantilla pendientes; no invalida el merge comprobado, pero debe reconciliarse
con la evidencia enlazada al aprobar el cierre documental.

## Validacion de esta propuesta

- `corepack pnpm openspec:validate`: 34 elementos correctos, cero fallos.
- `corepack pnpm jup:check:all`: 11 cambios antes del archivo, ocho despues;
  los tres cambios archivados pasaron la trazabilidad antes de moverlos.
- `corepack pnpm jup:cleanup:check`: 656 archivos aceptados antes de staging.
- `python -m unittest discover -s tools/collaboration/tests -v`: 12 pruebas correctas.
- Inspeccion de enlaces Markdown locales en los archivos movidos, informes y
  ADR afectados: 34 destinos existentes; no valida URLs externas ni anchors.
- Se corrigieron lineas vacias finales generadas por archive en las cuatro specs;
  `git diff --cached --check` sobre el resultado final: sin errores.
- El archivo de JUP-085 propuesto en PR #45 no modifica estas cuatro specs.

No se repitieron las suites funcionales completas ni pruebas de proveedores:
esta propuesta cambia exclusivamente documentacion y especificaciones.
