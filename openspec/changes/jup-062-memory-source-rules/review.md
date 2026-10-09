# Revisión — JUP-062 (gobernanza de la memoria)

## Resumen

Documento `docs/memoria/README.md` y una línea en `AGENTS.md` que declaran dónde vive la memoria del TFM, qué tarjeta corresponde a cada apartado, las reglas de edición, cómo se registran la revisión y la validación del entregable y las normas para herramientas y asistentes. Es documentación: no cambia código, configuración ni CI.

## Decisiones

- La memoria sigue en un documento compartido fuera de Git; el repositorio solo declara las reglas, no copia el contenido.
- El mapa de apartados enlaza con tarjetas y no copia personas ni fechas, que son de Trello.
- La autorización para leer o modificar la concede quien lidera la tarjeta del apartado afectado, por separado para leer y para modificar y por apartado.
- No se incluye la URL del documento en el repositorio; el enlace vive en la tarjeta.

## Adversarial Review (pass 1)

Revisor independiente, base `origin/develop`, solo lectura. Veredicto: revise, sin BLOCKING ni HIGH. Hallazgos contrastados con el texto del documento:

| ID | Sev. | Resolución |
| --- | --- | --- |
| ADV-1 | MEDIUM | Corregido: la fila de evaluación decía «sin tarjeta propia» y a la vez listaba tarjetas; ahora separa las dos ideas y dice que quién redacta se decide en Trello. |
| ADV-2 | MEDIUM | Corregido: la fila de DevOps ya no afirma una tarjeta firme; recoge que el propio documento duda entre JUP-061 y JUP-060 y que falta decidirlo en Trello. |
| ADV-3 | MEDIUM | Corregido: «quien lo lidera» era ambiguo. La spec y el documento fijan que autoriza quien lidera la tarjeta del apartado afectado, y añaden un ejemplo combinado (leer el apartado b no permite modificar el d). |
| ADV-4 | MEDIUM | Corregido: el documento dice ahora que, sin autorización, la herramienta la solicita y no lee ni modifica. |
| ADV-5 | MEDIUM | Corregido: las exportaciones son la memoria y siguen las mismas reglas que el documento; la spec añade un escenario de lectura de una exportación. |
| ADV-6 | LOW | Aceptado: la guía de estilo está al principio del documento compartido, que se leyó al redactar; el literal `[Pendiente]` lo usa esa guía. No se enlaza el proposal del change hermano para no dejar una ruta que cambiará al archivarse. |
| ADV-7 | LOW | Corregido: la exportación se repite al revisar o cerrar un hito, y el manifiesto lista fecha y SHA-256 de cada archivo, PDF y Markdown. |
| ADV-8 | LOW | Sin acción: `docs/adr` y `docs/planning` ya usan tildes, así que hay precedente mixto. |

Barrido del patrón: la ambigüedad entre «sin tarjeta propia» y una lista de tarjetas aparecía solo en la fila de evaluación; la referencia a JUP-061 en la fila de DevOps coincide con el proposal de `jup-062-business-memory`, que también la asigna. Tras las correcciones, `openspec:validate --strict` y `jup:check` siguen correctos.

## Adversarial Review (pass 2)

Revisor independiente sobre lo añadido tras la pasada 1 (el guion oficial como criterio de corrección y el flujo de propuesta de redacción para herramientas). Veredicto: revise, sin BLOCKING. Hallazgos contrastados:

| ID | Sev. | Resolución |
| --- | --- | --- |
| ADV-1 | HIGH | Corregido: el requisito nuevo decía «acceso de lectura» y el existente exigía «autorización expresa de lectura», lo que contradecía el caso de una herramienta con el conector pero sin autorización. Ahora hacen falta las dos cosas y tener acceso sin autorización equivale a no tener acceso: la herramienta la solicita y no lee nada. Escenario nuevo. |
| ADV-2 | HIGH | Corregido: la spec y el documento dicen quién autoriza el borrador (quien lidera la tarjeta del apartado), y que leer otro apartado para dar contexto exige también su autorización. El texto que la persona pega de otro apartado se usa solo para ese encargo. Escenario nuevo. |
| ADV-3 | MEDIUM | Corregido: el documento recoge que, sin acceso, la herramienta no busca el documento en otro sitio. |
| ADV-4 | MEDIUM | Parcialmente verificado: la existencia de `Guion_PJ.md` en la misma carpeta de Drive que el documento de la memoria y su contenido (nueve apartados, 20 páginas, ponderación) se comprobaron leyéndolo en Drive. El documento cita ahora el nombre completo del PDF que el repositorio ya referencia. Queda por confirmar con el PDF original que coincide con la versión Markdown. |
| ADV-5 | LOW | Corregido: el documento ya no nombra un producto concreto como ejemplo de conector. |
| ADV-6 | LOW | Corregido: el guion también está fuera de Git; leerlo no exige la autorización de la memoria y, si la herramienta no lo alcanza, se lo pide a la persona sin sustituirlo por suposiciones. Requisito y escenario nuevos. |

Barrido del patrón: la confusión entre «acceso» y «autorización» aparecía en el requisito, el escenario y el documento, y se corrigió en los tres. Tras las correcciones `openspec:validate --strict` y `jup:check` siguen correctos. No se hizo una tercera pasada: los cambios son de redacción de los mismos requisitos.

## Riesgos y hallazgos

- El contenido real del documento compartido y las tarjetas de cada apartado viven fuera del repositorio; el revisor no pudo contrastarlos y la fila de DevOps depende de una decisión pendiente en Trello.
- El directorio `materiales/06-entregables/` no existe en el repositorio por diseño, así que el manifiesto y las exportaciones no se pueden comprobar desde él.
- No hay hallazgos que registrar en `openspec/findings/backlog.md`.

## ADR

No se necesita un ADR: es documentación de proceso, no una decisión de arquitectura duradera. La elección de la fuente editable para el bloque de negocio ya consta en `jup-062-business-memory`.

## Human Approval

Pendiente de la aprobación posterior a la revisión de Lucía.
