# Demo funcional — JUP-065

Actualizado: 2026-10-01. Origen: «JUP-065 — Preparar la demo funcional».
[Tarjeta](https://trello.com/c/SZUFo4ol).

## Alcance

El usuario autorizó preparar la demo antes del MVP integrado, publicar la PR y
solicitar formalmente revisión/validación. El paquete canónico compartido está en
[docs/demo/JUP-065](../demo/JUP-065/README.md); [OpenSpec](../../openspec/changes/jup-065-functional-demo/proposal.md)
conserva escenarios y tareas. La [evidencia](../evidence/JUP-065-validation.md)
distingue comprobaciones automáticas y pendientes humanos.

## Decisiones

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
