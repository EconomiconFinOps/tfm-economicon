JUP: JUP-120

## Context

El corpus (`docs/assistant-corpus/`, cuatro documentos) lo cargan el processor (troceado de 500 caracteres con solape 50) y el chat de JUP-035, que recupera fragmentos y los cita. Tres de los cuatro documentos están fijados por sha256 en la batería JUP-069 (`rules`, `finops`, `product`), y `tools/validation-questions.mjs` falla en CI si no coinciden. Las etiquetas de recuperación de JUP-022 repiten esas huellas y nombran secciones por encabezado. El glosario no está fijado.

Lo que dice hoy el corpus sobre anomalías frente a lo que hace el producto (ADR-0020, `docs/api/anomaly-episodes.md`, panel `/anomalies`):

| Corpus | Producto |
| --- | --- |
| P1/P2/P3 en «EUR/mes» | Sobre el impacto acumulado del episodio, no proyectado al mes |
| Estado `acknowledged` | No existe; los estados son `new`, `investigating`, `resolved` y `false_positive` |
| Solo la regla diaria | Episodio por tenant, moneda y servicio, con tolerancia de 3 días y estado «Ya no se observa» |
| Sin definir lo esperado | Media de los 7 días anteriores, o referencia anclada si hay un episodio en seguimiento |

La regla diaria (`relative_delta > 20 % AND absolute_delta > 100 EUR/day`) **no cambia**, y los casos 016 a 018 de JUP-069 la evalúan.

## Goals / Non-Goals

**Goals**
- Que el corpus no contradiga el producto en anomalías y explique el panel con el lenguaje de la pantalla.
- Que la cadena de huellas (JUP-069, JUP-022, calibración) quede consistente y verificable tras el cambio.
- No empeorar los casos de la batería que hoy responden bien (016 a 019, 003, 013 y 014).

**Non-Goals**
- Cambiar código, prompt, troceado o parámetros de recuperación.
- Reescribir el resto del corpus (tagging, presupuestos, recomendaciones) ni reorganizarlo en secciones nuevas.
- Documentar la fecha de referencia de JUP-119 ni el enlace «Explicar en el asistente» de JUP-038 mientras esos PR no estén en `develop`.

## Decisions

### D1. Editar los documentos en el sitio y volver a fijar las huellas

Decisión de Lucia (2026-10-13). Corrige el error donde está, de modo que el modelo no pueda recuperar la versión antigua. Coste: cambian la huella del corpus y la de la batería, y hay que volver a fijar y recalibrar.

Alternativas descartadas:
- **Documento nuevo sin tocar los fijados:** no cambia ninguna huella, pero el texto errado seguiría en las reglas y el modelo podría recuperar ambos.
- **Dos pasos (documento nuevo ahora, corrección después):** son dos PR y dos cambios de corpus, y mientras tanto convive la contradicción.

### D2. Qué dice el corpus (hechos y límites)

Solo lo que el producto hace hoy y consta en ADR-0020, sin implementación interna (el documento de producto prohíbe exponer endpoints, tablas, colas o despliegue):

1. **Episodio:** una anomalía candidata por cliente, moneda y servicio; se abre el día en que salta la regla y sigue siendo la misma mientras vuelva a saltar dentro de 3 días. Pasados 3 días sin saltar queda «Ya no se observa»; no se cierra sola.
2. **Lo esperado:** la media diaria de los 7 días anteriores, o la referencia anclada (media de los 7 días previos al inicio) mientras el episodio se sigue. Solo se evalúan días completos: el último día con datos se considera incompleto.
3. **Regla:** sin cambios; ambos límites son estrictos, de modo que exactamente 100 al día o exactamente 20 % no activan la regla. Esta frase va junto a la regla, antes del contenido nuevo.
4. **Severidad:** sobre el impacto acumulado del episodio (suma diaria de lo que supera la referencia), en la moneda del episodio: P1 mayor que 2.000, P2 de 500 a 2.000, P3 menor que 500. Umbrales nominales en EUR y USD, sin conversión; otras monedas no se evalúan. Sigue marcado como umbral interno y calibrable.
5. **Estados:** `new`, `investigating`, `resolved` y `false_positive`; cerrar exige un motivo y es definitivo. Se quita `acknowledged`.
6. **Servicio sin gasto previo:** el primer día no abre episodio. Desde el segundo día su referencia incluye ese primer día, de modo que un gasto nuevo y estable por encima de unos 116,67 al día sí puede abrir uno. No se afirma que un recurso nuevo cumpla o no la regla sin datos.
7. **Candidata:** una anomalía no tiene causa establecida, ahorro ni confianza estadística; hay que investigar y confirmar si el cambio era esperado. El panel no apaga ni cambia recursos.

La guía de usuario (en `product-architecture`) usa los textos de la pantalla: «Anomalías», «Detectar ahora», «Revisado hasta…», Alta (P1), Media (P2), Baja (P3), «Se sigue observando» y «Ya no se observa», más el aviso de datos sintéticos. Los textos exactos se leen del código del frontend al implementar, no se copian de memoria.

### D3. Estabilidad de los encabezados y de los fragmentos

Las etiquetas de JUP-022 nombran secciones por encabezado (por ejemplo `rules` / `Anomalias`) y los casos 016 a 019 esperan esa sección. Por eso:
- Se conserva el encabezado `## Anomalias` y la regla con su frase de límites estrictos al principio, dentro de los primeros 500 caracteres, para que el umbral no se separe de su encabezado al trocear.
- El contenido nuevo va después, en subsecciones con encabezado propio. Se evita alargar el texto que ya existe.
- Las secciones posteriores (`Recomendaciones`, `Modelo Conceptual De Datos`) cambian de número de fragmento. El impacto se mide con la calibración y las etiquetas, no se supone.

### D4. Orden para volver a fijar la cadena

Documentos y manifiesto, luego las huellas de las fuentes y `suite_version` de JUP-069 (la propia documentación pide incrementarlo y conservar los identificadores de los casos), luego las etiquetas de JUP-022 y por último la calibración. Cada paso se valida con las herramientas existentes (`assistant-corpus:validate`, `validation-questions:validate`, `retrieval-labels:validate` y las pruebas de calibración) antes de pasar al siguiente. Si cambia el texto de una pregunta de JUP-069 o sus puntos esperados, se rompe la regla de conservar la batería: este change no los cambia.

### D5. Los informes de JUP-070 quedan como histórico

Los informes `JUP-070-run-1` y `run-2` registran una ejecución concreta (commit, corpus y batería de ese momento). No se regeneran: se conservan tal cual y las notas de este change dicen que su huella ya no coincide con el repositorio. Se comprueba que ninguna prueba los vuelva a validar contra la batería actual.

### D6. Batería nueva de anomalías: pendiente de decisión del equipo

JUP-069 no pregunta por severidad, estados ni episodios, y no se modifica (la campaña de JUP-035 fija su huella). Hay dos caminos: una batería nueva y pequeña en otro fichero, o dejar esa parte sin cobertura. El change no la implementa; si el equipo la quiere, será una tarea posterior de esta misma tarjeta, con su propio fichero y sin tocar JUP-069.

## Risks / Trade-offs

- [Los casos 018 y 019 cambian de respuesta por el texto nuevo] → La regla y su frase de límites estrictos quedan al principio; el caso del servicio nuevo se redacta sin afirmar que cumple la regla; se comparan las secciones recuperadas por caso antes y después con la calibración.
- [Más texto de anomalías atrae esos fragmentos a preguntas de presupuesto (013 y 014)] → Se añade lo mínimo, sin repetir definiciones que ya estén en el glosario; se comprueba con la calibración y se recorta si aparece.
- [Cambia la huella de la batería y la campaña de JUP-035 deja de ser comparable] → Se acuerda el momento con Alejandro antes de integrar; el change no se integra hasta que se resuelva, y las ejecuciones anteriores se marcan como históricas.
- [La calibración con proveedor real necesita una clave y gasta crédito] → Se anuncia antes de ejecutarla; con el proveedor simulado se valida solo la mecánica, nunca la calidad. Si no se ejecuta la real, se registra como no ejecutada.
- [El texto de la guía se desfasa si #127 o #128 se integran antes] → Antes de cerrar se comprueba qué hay en `develop`; si ya están, se añaden la fecha de referencia y el enlace, y si no, se registra como seguimiento.
- [Las aclaraciones de severidad reflejan una lectura del ADR que sigue pendiente de confirmar con la responsable de las reglas] → El corpus lo dice como regla actual del producto y mantiene la nota de que los umbrales son internos y calibrables.

## Migration Plan

No hay migración de datos ni de código. Para revertir, basta con restaurar los documentos, el manifiesto y los ficheros de huellas desde `develop`. Los índices ya cargados en un entorno se actualizan con la reingesta existente del corpus cuando se despliegue; no se documenta un procedimiento nuevo.

## Open Questions

1. ¿Cuándo se integra este change respecto a la campaña de aceptación de JUP-035 (#121)? Pregunta enviada al equipo.
2. ¿Se añade una batería nueva de anomalías (6 a 8 preguntas)? Pregunta enviada al equipo.
3. ¿Se ejecuta la calibración con el gateway real? Depende de la clave y del crédito disponibles; se decide al llegar a esa tarea.