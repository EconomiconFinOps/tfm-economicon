# Memoria del proyecto: dónde vive y cómo se edita

La memoria del TFM es un entregable que se redacta fuera del repositorio. Este documento declara dónde está, quién escribe cada parte y qué reglas se siguen al tocarla. Trello sigue siendo el dueño de las asignaciones y las fechas (ver [AGENTS.md](../../AGENTS.md)); aquí no se duplican.

## Dónde vive

- La fuente editable es un documento compartido de Google Docs llamado `Memoria_Economicon`. Su enlace está en la tarjeta de Trello de JUP-062.
- No se copia a Git ni se mantiene una segunda versión canónica en el repositorio. Es una decisión del change `jup-062-business-memory`.
- Las exportaciones fechadas (PDF y Markdown) y su manifiesto SHA-256 se guardan en `materiales/06-entregables/`, fuera de Git, junto al resto de entregables finales. Una exportación registrada no se edita: si cambia el documento, se hace otra exportación.

## Qué apartado corresponde a qué tarjeta

| Apartado | Tarjeta de Trello |
| --- | --- |
| a. Introducción y resumen ejecutivo | JUP-062 |
| b. Caso de negocio | JUP-062 |
| c. Contribución individual | JUP-064 |
| d. Arquitectura técnica de la solución | JUP-060 |
| e. Diseño y desarrollo de la solución de IA | JUP-063 |
| f. Integración con herramientas DevOps | JUP-061 (por confirmar) |
| g. Uso de modelos preentrenados | JUP-063 |
| h. Evaluación de la solución | JUP-067 a JUP-071 y JUP-077 (sin tarjeta de documentación propia) |
| i. Conclusiones y trabajo futuro | Sin tarjeta propia (cierre de la memoria) |

La persona responsable de cada apartado es la que figura en su tarjeta.

## Reglas para editar

- Se sigue la guía de estilo que está al principio del propio documento: tono, marca, extensión máxima de 20 páginas entre todos los apartados, toda cifra trazable a su fuente y lo que aún no exista marcado como `[Pendiente]`.
- Cada persona redacta su apartado. Un cambio en el apartado de otra persona se propone como sugerencia o comentario, no como edición directa.
- Las fuentes externas se citan en el texto con su referencia.
- Las fechas de congelación del documento y de entrega están en [docs/planning/JUP-080-milestones.json](../planning/JUP-080-milestones.json), pendientes de confirmación institucional.

## Revisión y validación del entregable

- No son reviews de GitHub, porque la memoria no tiene diff en el repositorio. Se registran en comentarios del documento y en la tarjeta de Trello, indicando la versión exportada que se revisó por su fecha y su SHA-256.
- El check `JUP reviews` solo se aplica a pull requests.
- La evidencia versionada va en `docs/evidence/`, por ejemplo [JUP-062-business-memory-review.md](../evidence/JUP-062-business-memory-review.md). El cierre de cada change se hace con un pull request de documentación.

## Para herramientas y asistentes

- La memoria no está en el repositorio: no se busca ni se regenera desde Git.
- No se lee ni se modifica el documento sin autorización expresa de quien lo lidera. La autorización para leer no autoriza a modificar, y la de un apartado no se extiende a los demás.
- Ningún texto se publica en el documento sin que una persona lo revise.
- No se inventan cifras ni fuentes: lo que falte se marca como `[Pendiente]`.
- No se guardan en el repositorio copias del documento ni exportaciones.
