# Evidencia técnica — JUP-068

Verificado el 2026-10-03. Base `origin/develop`:
`6410950315b0e3c22057d09015e11e38c5e455ab`.
Rama `feat/JUP-068-business-metrics`.
[Tarjeta](https://trello.com/c/JYaiGKKv).
Origen: chat «JUP-068 — Métricas funcionales de negocio»; identificador no disponible.

## Entregable y criterios

| Criterio mínimo Trello | Evidencia y estado |
| --- | --- |
| Resultado funcional verificable | CLI genera informe determinista de tiempo, allocation y potencial; ejemplo sintético reproducible |
| Pruebas necesarias verdes | 31 pruebas del instrumento; 257 pruebas Node de herramientas en total, todas correctas |
| Documentación y decisiones actualizadas | Protocolo, fórmula/unidades, objetivos propuestos, límites y OpenSpec versionados |
| PR revisado y vinculado | [PR #68 draft](https://github.com/EconomiconFinOps/tfm-economicon/pull/68) vinculado; revisión Lucía pendiente |
| Validación funcional y evidencia enlazadas | Aritmética/CLI probadas; validación Paris y piloto con observaciones pendientes |

## Comprobaciones

Entorno local: Windows PowerShell, Node.js 24.14.1, pnpm 9.0.0.

| Comando | Resultado |
| --- | --- |
| `corepack pnpm install --frozen-lockfile` | Correcto; lockfile sin modificar |
| `node --test tools/business-metrics.test.mjs` | 31/31 |
| `node --test tools/*.test.mjs` | 257/257 |
| `node tools/business-metrics.mjs validate docs/validation/JUP-068-example.json` | Correcto; procedencia synthetic |
| `node tools/business-metrics.mjs report docs/validation/JUP-068-example.json` | 360000 ms / 40 % ahorro temporal; cobertura asignada 70 %, gobernada 90 %; 14000 céntimos / 14 % potencial; solo fixture |
| `node tools/jup-check.mjs --all` | Diez changes enlazados correctamente |
| `node tools/jup-cleanup-check.mjs` | Correcto |
| `node tools/assistant-corpus.mjs validate` | Correcto; corpus no modificado |
| `corepack pnpm openspec:validate` | 41 correctos, cero fallos |
| `git diff --check` | Correcto |

El conjunto de pruebas cubre pesos por coste, shared/excluded, ausencia de medición,
denominador cero, cero ahorro conocido, ahorro temporal negativo, fallos/bloqueos,
duplicados, dinero inválido/desbordamiento, solapamientos, evidencia/owner/regla
ausentes, periodos inválidos, moneda/base mezcladas y uso de CLI desde otro directorio.
CI añade validación del fixture y pruebas del instrumento al job OpenSpec.

## Verificación remota — 2026-10-03, corte 23:20 Europe/Paris

Comprobado directamente en GitHub sobre
`ce7649264d6c67cb8df30aeac792c0001be3ce91`, PR #68 todavía draft.
[CI 37154246601](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37154246601):
**7/7 checks correctos**: JUP policy, OpenSpec, Python tests (azure-cost-api,
backend y processor), Frontend build y Frontend type check. Último job terminado
el 2026-10-03T21:13:26Z. Esta evidencia amplía las pruebas locales anteriores;
los tests Python y frontend se ejecutaron en CI, no localmente.

[JUP reviews 37154246600](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37154246600)
falla exclusivamente porque faltan `Revision JUP-068` y `Validacion JUP-068` de
personas distintas del autor, según el log. No indica fallo funcional del instrumento.
Reviews, comentarios de conversación y comentarios inline: ninguno en este corte.
Reproducción: `gh pr view 68 -R EconomiconFinOps/tfm-economicon --json headRefOid,isDraft,reviews,comments,statusCheckRollup`,
`gh api repos/EconomiconFinOps/tfm-economicon/pulls/68/comments --paginate` y
`gh run view 37154246600 -R EconomiconFinOps/tfm-economicon --log-failed`.

El snapshot autorizado `snapshot-20261003T212024Z.json` reconfirma roles y tarjeta
en Backlog. Pendientes concretos: Víctor contrasta método y objetivos; Alejandro
acredita pairing; Lucía publica revisión; Paris valida con evidencia por criterio;
el equipo captura el piloto con baseline homogénea y respuestas correctas. El
beneficio real continúa sin medir. La vinculación está en el comentario Trello
`6ac16f44d77096f07c03c5ac`; los enlaces de la descripción siguen sin actualizar.
Este añadido se conserva localmente, sin nuevo commit/push, para identificar
inequívocamente el head comprobado. No cierra la tarea ni sustituye las reviews.

## Reconciliación para entrega de coautor — 2026-10-10

Actualización de base desde el head publicado `ce76492` a develop
`412ae411c7f3a9b51f65407974962ac2b4545686`, autorizada por el usuario para
publicar la aportación de Alejandro en el PR #68, conservándolo como borrador.
Sustituye para entrega los candidatos locales anteriores de `ceb6520`/`c2995a1`.

Resueltos tres conflictos de integración en `.github/workflows/ci.yml`,
`package.json` y `tools/ci-workflow.test.mjs`, conservando los controles y scripts
de ambas ramas. Se incorpora el resto de develop sin cambios manuales de producto,
modelos o corpus. Instrumento, protocolo, fixture y tests de JUP-068 sin cambios.

Ejecutado sobre la integración: **56/56** tests Node (31 del instrumento y 25 de
CI/gobernanza), fixture sintético válido y **OpenSpec 58/58**. La CI del head
nuevo debe verificarse tras publicar; el verde del 03/10 es histórico.
No se repiten suites Python/frontend locales: las modificaciones de esos servicios
proceden de develop y su ejecución en este head se comprobará en CI.

Roles conservados: Víctor liderazgo, Alejandro pairing/coautor, Lucía revisión,
Paris validación. La entrega no acredita conformidad de Víctor: queda pendiente
su contraste o visto bueno explícito y atribuible en Trello, además de las dos
reviews separadas. Piloto/beneficio real sin medir; ejemplo offline/sintético.
Sin merge del PR, ejecución de LLM ni mensajes Discord. La nota anterior de
evidencia local no publicada describe únicamente el corte histórico del 03/10.

## Límites y pendientes

La comprobación técnica no acredita ahorro ni calidad del asistente real. No se
ejecutaron respuestas de LLM, Azure real, captura de tiempos de usuarios ni optimizaciones.
No se modificó runtime, por lo que no se ejecutaron tests Python ni build frontend
como validación local de esta definición; los jobs existentes de CI se conservan.
Los porcentajes usan punto flotante (presentar con redondeo sin alterar el registro).
El verificador comprueba referencias presentes; una persona debe inspeccionar su contenido.

Liderazgo Víctor, pairing Alejandro, revisión Lucía, validación Paris, según Trello
consultado por el puente DockerServer `snapshot-20261003T210000Z.json`.
Confirmación del método/objetivos, participación efectiva, reviews y piloto pendientes.
No se declara la tarjeta terminada ni se reasignan roles.
