# Demo funcional — JUP-065

Actualizado: 2026-10-05. Origen: «JUP-065 — Preparar la demo funcional».
[Tarjeta](https://trello.com/c/SZUFo4ol).

## Alcance

El usuario autorizó preparar la demo antes del MVP integrado, publicar la PR y
solicitar formalmente revisión/validación. El paquete canónico compartido está en
[docs/demo/JUP-065](../demo/JUP-065/README.md); [OpenSpec](../../openspec/changes/archive/2026-10-03-jup-065-functional-demo/proposal.md)
conserva escenarios y tareas. La [evidencia](../evidence/JUP-065-validation.md)
distingue comprobaciones automáticas y pendientes humanos.

## Corrección P2 de cobertura CI — 05/10/2026

Paris solicitó proteger los tres comandos de demo y el historial completo del
checkout de gobernanza en su [review sobre b77d596](https://github.com/EconomiconFinOps/tfm-economicon/pull/63#pullrequestreview-5408829450).
Se añaden cuatro pruebas en `tools/ci-workflow.test.mjs`: líneas ejecutables
completas para cada comando y `fetch-depth: 0`; se impide ignorar fallos de demo.
Workflow, runtime, paquete y fuentes fijas conservados.

Resultado: workflow 14/14; seis mutaciones rechazadas, con restauración byte a
byte; gobernanza afectada 97/97; verificador normal/optimizado 15/15, dos tests,
28 consultas/siete categorías; OpenSpec 45/45, diez changes, higiene 842 y diff
contra develop PASS. [Evidencia](../evidence/JUP-065-validation.md) actualizada.
Logs locales: `materiales/07-evidencias/JUP-065-proteccion-ci-2026-10-05/` en
el espacio Economicon, fuera del repositorio.

Solicitar revisión de Paris sobre el nuevo head (Approve levanta Request changes)
y revalidación afectada a Víctor. Su Comment favorable de `b77d596` es histórico
para este cambio. Pairing Lucía y ensayo integrado siguen pendientes; no se
implementa generación LLM. Sin merge ni cierre; Trello conserva etapa 50 durante
la corrección. Este corte sustituye los pendientes técnicos del 04/10 siguientes.

## Decisiones históricas

Actualización del 04/10: develop `c3aa9d6` aporta #62, #60 y #67. El conflicto
de CI se resuelve conservando comandos demo y retrieval, sin tocar el paquete
ni sus fuentes fijas. Nuevas comprobaciones: 15/15, dos tests/cuatro controles,
28 consultas, 140 pruebas de tooling, calibración 26 pass/una omitida, OpenSpec
45/45, diez changes trazables y diff check contra la base correctos.
La omisión de pgvector y la ausencia de runtime/modelo en esta actualización
se conservan como límites; #67 no acredita por sí sola el ensayo.

Paris confirmó la revisión incremental y Víctor validó `bf50073`; falta
confirmación incremental sobre la nueva combinación con retrieval antes de
integrar. El pairing de Lucía sigue sin acreditar o reasignar de forma acordada
en Trello y Participación. CI del head publicado y reviews se consultan en #63.
Sin merge ni cierre; ensayo integrado permanece pendiente. Las decisiones del
03/10 siguientes conservan el corte histórico previo a esas aprobaciones.

Paris publicó `Revision JUP-065` como Request changes el 02/10 sobre `e52853b`.
Los dos P2 se corrigen el 03/10: README verifica originales antes de regenerar
y la regeneración opcional va a un temporal; AGENTS recupera exactamente el
contenido de develop sin imponer una obligación general de continuidad. Estos
documentos técnicos se conservan. La convención común #64 se trata por separado,
sin dependencia de esta demo.

OpenSpec de esta preparación archivado en `2026-10-03-jup-065-functional-demo`
según CONTRIBUTING; las reviews, pairing y ensayo permanecen pendientes.

El material original se verificó y se ejecutaron sus controles negativos antes
de cualquier cambio. Sus quince hashes quedaron conservados. Se incorporó
develop `d6fc408` mediante merge sin conflictos, manteniendo `JUP reviews` y
`local:test`. La referencia de datos sigue fijada al commit original.

Base de fuentes `de0d62e7c0028f35a81c5087f531d19031a90e81`; lectura con `git show`,
hashes y licencia. Referencia: 40 filas, 38 registros, ocho grupos, 0,06 USD;
no equivale a un resultado observado del runtime. JUP-069-004/003 principales y
001/023/025 reservas. El caso 001 de 1.000 EUR es sintético y no pertenece al dashboard.

El guion no presume chat conectado a billing ni gráficos estáticos como datos
reales. Activar el gateway del processor no acredita el proveedor de `/assistant`.
Las rúbricas no entran en prompts ni en el índice documental. CI y el verificador
solo prueban preparación; plantilla de ensayo y runtime permanecen `not_run`.

## Reproducción y siguiente paso

Desde la raíz: `python docs/demo/JUP-065/verificar.py --repo .` y
`node docs/demo/JUP-065/generado/sources/tools/validation-questions.mjs validate`.
Con historial superficial, obtener primero el SHA indicado en el README.

Paris revisa; Victor valida la preparación; Lucia participa en pairing y
Alejandro lidera según Trello. No acreditar participaciones hasta su confirmación.
Tras integrar el MVP, fijar commit/proveedor/índice, ejecutar preflight y recorrido,
guardar evidencias y obtener reproducción independiente antes del cierre.

## Publicación

PR [#63](https://github.com/EconomiconFinOps/tfm-economicon/pull/63) hacia develop,
rama `docs/JUP-065-functional-demo`. Implementación inicial `d9b7c6a`;
la solicitud de revisión/validación y el CI del último head se consultan en la PR.
Solicitar a `ParisArcos` revisión técnica y a `Victorh1397` validación offline de
preparación. Los resultados locales son nuevos; no hay aceptación humana registrada.
