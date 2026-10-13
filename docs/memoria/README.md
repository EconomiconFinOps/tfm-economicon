# Memoria del proyecto: dónde vive y cómo se edita

La memoria del TFM es un entregable que se redacta fuera del repositorio. Este documento declara dónde está, quién escribe cada parte y qué reglas se siguen al tocarla. Trello sigue siendo el dueño de las asignaciones y las fechas (ver [AGENTS.md](../../AGENTS.md)); aquí no se duplican.

## Dónde vive

- La fuente editable es un documento compartido de Google Docs llamado `Memoria_Economicon`. Su enlace está en la tarjeta de Trello «PROYECTO — Enlaces y coordinación».
- No se copia a Git ni se mantiene una segunda versión canónica en el repositorio. Es una decisión del change `jup-062-business-memory`.
- Las exportaciones fechadas (PDF y Markdown) y su manifiesto SHA-256 se guardan en `materiales/06-entregables/`, fuera de Git, junto al resto de entregables finales. Una exportación registrada no se edita: se vuelve a exportar al revisar o cerrar un hito, y el manifiesto lista la fecha y el SHA-256 de cada archivo, PDF y Markdown.

## Con qué criterio se corrige

- La memoria se corrige con el guion oficial del Proyecto Júpiter: define los apartados de la memoria, su extensión máxima y la ponderación de los entregables. Si el documento de la memoria dice otra cosa sobre la extensión o la ponderación, manda el guion.
- Quien redacta un apartado, o la herramienta que propone su redacción, lo contrasta con tres partes del guion: la descripción de ese apartado en la lista de entregables de la memoria, los requisitos técnicos y funcionales que le afectan (por ejemplo, el caso de negocio pide impacto, viabilidad y diferenciación, aunque eso no esté en su descripción) y el desglose de la evaluación en el que cae.
- La propuesta incluye una lista de cobertura: cada requisito del guion que le afecta, con el número del párrafo de la propuesta que lo cubre o `[Pendiente]` si no está cubierto. Si una de las tres partes no tiene nada para el apartado, la lista lo dice ("ninguno encontrado en esa parte") en lugar de quedarse en silencio.
- El guion no se copia al repositorio. La copia de referencia es `Guion_PJ.md`, una transcripción en Markdown guardada en la misma carpeta de Drive que el documento de la memoria, con su enlace en esa misma tarjeta. El PDF original lo custodia el equipo y no está en el repositorio. Leer el guion no exige la autorización que sí exige leer la memoria, pero se abre por su nombre, sin listar ni abrir otros ficheros de esa carpeta. Si la herramienta no tiene acceso a él, se lo pide a la persona, no lo sustituye por suposiciones y entrega como mucho un esquema marcado como no contrastado.

## Qué apartado corresponde a qué tarjeta

| Apartado | Tarjeta de Trello |
| --- | --- |
| a. Introducción y resumen ejecutivo | JUP-062 |
| b. Caso de negocio | JUP-062 |
| c. Contribución individual | JUP-064 |
| d. Arquitectura técnica de la solución | JUP-060 |
| e. Diseño y desarrollo de la solución de IA | JUP-063 |
| f. Integración con herramientas DevOps | JUP-111 (las fuentes son JUP-051, JUP-052 y JUP-061) |
| g. Uso de modelos preentrenados | JUP-063 |
| h. Evaluación de la solución | JUP-109 (los resultados salen de las tarjetas de evaluación JUP-067 a JUP-071 y JUP-077) |
| i. Conclusiones y trabajo futuro | JUP-110 |

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

- El enlace del documento y el del guion se buscan en la tarjeta de Trello «PROYECTO — Enlaces y coordinación», no en el repositorio.
- La memoria no está en el repositorio: no se busca ni se regenera desde Git, y las exportaciones de `materiales/06-entregables/` son la memoria y siguen las mismas reglas que el documento.
- No se lee ni se modifica el documento sin autorización expresa de quien lidera la tarjeta del apartado afectado. Para un apartado sin tarjeta propia, autoriza quien lidera JUP-062 hasta que Trello asigne a alguien. Si falta la autorización, la herramienta la solicita y no lee ni modifica nada.
- La autorización para leer no autoriza a modificar, y la de un apartado no se extiende a los demás: leer el apartado b no permite modificar el d. Leer el documento completo o una exportación completa exige la autorización de todos los apartados que contiene; con la de uno solo, la persona entrega a la herramienta el fragmento y no el fichero.
- Una herramienta con acceso de lectura al documento compartido y con autorización expresa para leer el apartado prepara una propuesta de redacción de ese apartado, con cada cifra y su fuente y con `[Pendiente]` donde falte, y se la entrega a la persona. Tener acceso sin la autorización equivale a no tener acceso: la herramienta la solicita, no lee nada y trabaja solo con el texto que la persona le dé, sin buscar el documento en otro sitio.
- Para dar contexto a un borrador hace falta además la autorización de lectura del otro apartado. El texto que la persona pega de otro apartado se usa solo para ese encargo y no se modifica.
- La propuesta la revisa y la incorpora la persona. La herramienta solo escribe en el documento con autorización expresa para modificar; si no puede hacerlo, entrega la propuesta a la persona.
- Ningún texto se publica en el documento sin que una persona lo revise.
- No se inventan cifras ni fuentes: lo que falte se marca como `[Pendiente]`.
- No se guardan en el repositorio copias del documento ni exportaciones.
