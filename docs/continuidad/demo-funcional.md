# Demo funcional — JUP-065

Actualizado: 2026-10-03. Origen: «JUP-065 — Preparar la demo funcional».
[Tarjeta](https://trello.com/c/SZUFo4ol).

## Alcance

El usuario autorizó preparar la demo antes del MVP integrado, publicar la PR y
solicitar formalmente revisión/validación. El paquete canónico compartido está en
[docs/demo/JUP-065](../demo/JUP-065/README.md); [OpenSpec](../../openspec/changes/archive/2026-10-03-jup-065-functional-demo/proposal.md)
conserva escenarios y tareas. La [evidencia](../evidence/JUP-065-validation.md)
distingue comprobaciones automáticas y pendientes humanos.

## Decisiones

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
