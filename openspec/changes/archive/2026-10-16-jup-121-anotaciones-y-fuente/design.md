JUP: JUP-121 · ADR: [ADR-0022](../../../../docs/adr/ADR-0022-assistant-evaluation-results-in-grafana.md)

## Context

Dos correcciones pequeñas del dashboard de `jup-121-assistant-evaluation-dashboard` tras la segunda validación de Paris y el comentario de Lucia sobre JUP-071 (PR #132). Todo se resuelve en el JSON del dashboard y en la guía.

## Decisiones

- **D1. Anotaciones en la latencia.** La capa «Cambios de configuración» es una anotación de Grafana con filtro por paneles (`filter.ids`, modo inclusión). Pasa de `[7, 8]` a `[7, 8, 24]`. La consulta de la capa no cambia: las marcas salen de `evaluation.config_changes`, que ya devuelve el cambio entre ejecuciones consecutivas de la misma fuente. Las pruebas localizan los paneles por título, no por id, para no depender de la numeración.
- **D2. Estado de los casos solo de JUP-070.** La consulta añade `r.source = 'JUP-070'`, igual que ya hace el resumen de la última campaña. No se cambia el título ni la descripción, que ya decían JUP-070. Una ejecución de otra fuente con grupo y métrica `cases` deja de aparecer ahí.
- **D3. Las gráficas de evolución siguen sin filtrar por fuente.** Son genéricas a propósito: cualquier fuente con series comparables entra. Lo que impide que una proporción que depende del resultado de un caso entre en «métricas automáticas» es que quien emite las filas las marque bien, no un filtro del panel. Queda escrito en la guía como contrato para JUP-071: `pass`/`fail` de casos y las tasas derivadas del resultado de un caso (`pass_over_total`, `pass_over_evaluated`) y los marcados de revisión (`reduced_coverage`) son `human`; las comprobaciones que decide una regla (`numeric_checks`) son `automatic`; y no se reutilizan los grupos de las familias de JUP-070 (accuracy, relevance, grounding, latency, robustness, availability), que varios paneles toman sin filtrar por fuente.
- **D4. Panel de robustez.** No se toca: su lectura (nombres, traducciones, categorías) depende del informe de JUP-071 y se hará en su rama.
- **D5. Orden de lectura de la sección A.** Las tablas «(detalle)» (exactitud y latencia por fila) pasan al final de la sección, tras la robustez, y las evoluciones suben justo detrás de la matriz. Se reordenan `gridPos` y la lista de paneles; no se pliega ninguna fila (una fila plegada anida sus paneles y las pruebas de conciliación recorren los paneles de primer nivel).
- **D6. Títulos de la sección C.** Los paneles de un tercio de ancho llevan títulos de 40 caracteres como máximo: «Consultas al asistente por minuto», «Latencia p95, todas las rutas» y «Tasa de error del backend». «Tráfico real» y el alcance (no es la latencia del asistente) quedan en la descripción y en el rótulo de la sección.
- **D7. Fecha de la matriz.** La cabecera de columna pasa a `AAAA-MM-DD hh:mm · tipo`, como el resto de tablas, porque `DD-MM` se lee como mes y día.
- **Diferido a una tarjeta de pulido** (propuestas de Lucia): depurar columnas repetidas, quitar las referencias JUP del texto visible, reescribir las descripciones de los ⓘ, traducir calibración y benchmark, sección C sin duplicar el técnico y gráficas para la sección B y la calibración. Cambian muchos títulos, descripciones y columnas que las pruebas fijan.

## Riesgos

- La prueba congelada que exige que la capa de anotaciones cubra exactamente los paneles a5 y a6 deja de ser cierta; se actualiza con un parche que aplica el usuario (el hook de congelación impide editarla).
