# Glosario de la interfaz

La interfaz del frontend está en español. Este glosario fija el nombre de los conceptos que se repiten y lista los términos que se conservan en inglés con su motivo. Un término en inglés que no figure aquí es un fallo. El inglés llegará más adelante como segundo idioma; este documento servirá de base para los catálogos de traducción.

## Nombre único de cada concepto

| Concepto | Nombre en la interfaz | No usar |
| --- | --- | --- |
| Cliente (tenant del backend) | cliente, clientes | tenant, tenants |
| Pantalla de resumen general | Resumen (en el menú); el resto de pantallas de coste se llaman «Panel…» | dashboard |
| Carga de documentos o costes | ingesta | ingestion, ingestions |
| Trabajo de ingesta | trabajo de ingesta | ingestion job |
| Asistente de IA | asistente | assistant |
| Persona que accede | operador | operator |
| Iniciar / cerrar sesión | iniciar sesión, cerrar sesión | sign in, login, logout |
| Responsable de un grupo de costes | responsable (la clave de etiqueta `owner` se muestra tal cual, ver abajo) | owner como etiqueta de interfaz |
| Coste mensual | gasto mensual | monthly spend |
| Ahorro identificado | ahorro identificado | savings identified |

## Términos que se conservan en inglés

| Término | Dónde aparece | Motivo |
| --- | --- | --- |
| Economicon | marca | Nombre propio del producto. |
| FinOps | descripciones | Nombre de la disciplina; se usa así en español. |
| Azure, CockroachDB, RabbitMQ, S3 | ayudas técnicas | Nombres propios de producto. |
| `owner`, `application`, `cost_center`, `project` | etiquetas de coste | Claves literales de las etiquetas de Azure; se muestran tal cual porque la persona usuaria debe escribirlas igual. |
| UTC | fechas | Siglas estándar de la hora universal. |
| backend, gateway, endpoint, embeddings | ayudas técnicas y diagnóstico de salud | Términos de arquitectura sin equivalente de uso habitual en el sector; la persona que opera la plataforma los conoce. |
| Compute, Storage, Network | leyendas y categorías de los datos de demostración | Categorías de coste de Azure; se tratan como valores de datos. |
| ID | «ID del trabajo» | Abreviatura de uso corriente en español. |
| URI | «URI del artefacto» | Siglas técnicas sin equivalente. |
| Valores de la API | nombres de servicio, etiquetas, planes, títulos de conversación, mensajes del asistente | Datos del cliente: se muestran sin modificar. |

## Tratamiento

La interfaz tutea a la persona usuaria («Elige un cliente», «Inicia sesión»). Los puntos suspensivos se escriben con tres puntos (`...`).
