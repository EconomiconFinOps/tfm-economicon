# Reevaluación de métricas tras el cambio de modelo — JUP-133

[Tarjeta](https://trello.com/c/Yv1ETc2G) · [Change](../../openspec/changes/archive/2026-10-22-jup-133-reevaluacion-metricas-modelo/) · [Informe antes y después](../validation/model-reevaluation-report.md) · [Evidencia](../evidence/JUP-133-validation.md).

Lucía lidera la tarjeta. Actualización documental: 23/10/2026. PR #150 se integró
el 22/10 a las 17:24 UTC; la mención anterior a PR abierto y merge pendiente queda
superada. Sus resultados siguen siendo provisionales.

## Tres repeticiones en DockerDevelop — 23/10/2026

**Recogida completa, resultados provisionales; ninguna campaña aceptada.**

El usuario autorizó expresamente el lanzamiento y respondió «Autorizo 10». Tope total del plan: 10 USD, incluyendo ≈0,077 anteriores; el límite global de la demo también es 10 USD, sin sumar ambos. Reserva nativa de 6,50 USD por operación y subcuotas conservadas. El bloqueo de 1,50/6,50 USD queda superado.

Se recogieron 171 operaciones en conversaciones independientes: JUP-070 A, 28 × 3; JUP-071, 29 × 3. Coste nuevo liquidado por el gateway: **0.5291594448 USD**; acumulado aproximado del plan: **0.6061594448 USD**. Incluye embeddings y reintentos internos; no se contrastó con la factura del proveedor.

| Campaña | Rep. | Completadas | Coste USD |
| --- | ---: | ---: | ---: |
| jup070-a | 1 | 27/28 | 0.0895823920 |
| jup070-a | 2 | 25/28 | 0.0879410520 |
| jup070-a | 3 | 25/28 | 0.0902780640 |
| jup071 | 1 | 27/29 | 0.0868489344 |
| jup071 | 2 | 26/29 | 0.1001381312 |
| jup071 | 3 | 28/29 | 0.0743708712 |

No se nombraron dos personas revisoras ni se recibieron juicios. Calidad humana `not_measured`, revisión `not_run`. Los estados numéricos de JUP-071 son comprobaciones automáticas del instrumento, no juicio semántico. Las operaciones fallidas se conservan como bloqueadas; no se repitieron para obtener un resultado favorable.

El agregador JUP-070 exige tiempos por etapa que el chat nativo no expone cuando falla una operación. Quedó `blocked` en las tres repeticiones; se publican aparte los costes, intentos, completadas y latencias totales realmente medidos. No se inventan valores para satisfacer el contrato.

Configuración: `openrouter/deepseek/deepseek-v4.1-flash`, proveedor `deepinfra/fp8`, declarados y no atestiguados. Final 10000 tokens, corpus de cuatro documentos y doce fragmentos, misma configuración comprobada durante las seis recogidas y sellada al terminar. El histórico usaba otra segmentación; las diferencias no prueban un efecto causal del modelo o de la infraestructura.

El commit `84b53b74` corresponde al evaluador. El commit exacto del producto desplegado no está acreditado y queda nulo en los rows-v1; las imágenes efectivas se identifican por SHA-256 en el sello final.

Carga verificada por contenido exacto y consultas de Grafana.

El paquete conserva las 17 ejecuciones y 765 resultados previos y añade seis ejecuciones; resultado preparado: 23 / 1284. El manifiesto de Git contiene 18 ejecuciones. La verificación exacta confirmó la conservación del histórico.

Informes: [comparación](../evidence/JUP-133/JUP-133-infra-comparison-report.md), [carga](../evidence/JUP-133/JUP-133-infra-load-report.md), [preparación histórica, superada](../evidence/JUP-133/JUP-133-infra-preflight-report.md). Los seis informes y rows-v1 están en `docs/evidence/JUP-133/`. Crudos, respuestas, recibos, fichas y hojas vacías de revisión quedan fuera de Git en `materiales/07-evidencias/JUP-133-campanas-infra-20261023/` del workspace.

Rama `test/JUP-133-campanas-infra-tres-repeticiones`, desde `develop` `84b53b74`. [PR #156](https://github.com/EconomiconFinOps/tfm-economicon/pull/156) contra `develop`, sin merge. Los papeles de revisión del PR no designan a las personas que puntuarán las respuestas.

Pendiente: dos personas revisoras deben completar sus juicios por repetición antes de valorar aceptación. La política de revisión del PR sigue pendiente; el check AWS demo offline observado falla por discrepancia del árbol de evidencia, fuera de este cambio documental. No se modifica el producto para ocultar estos bloqueos.

Regresión offline: 12 pruebas offline: 9 pasan y 3 fallan por expectativas fijas del manifiesto anterior (12 ejecuciones frente a las 18 actuales). El contrato rows-v1 y la conciliación independiente pasan; no se declara la integración en verde.

Origen: chat «Levantar Jupiter en dockerDevelop», `01a16421-03a0-7460-b110-24738407ccb1`. Verificación y actualización: 2026-10-23.

Ampliación solicitada después de la carga: publicar también el dataset Azure
con etiquetas usado en DockerDevelop. [Instantánea de 1.370 registros](../../fixtures/azure-cost/demo-tagged-20261023/README.md)
y [continuidad de datos](fecha-referencia-datos-demo.md), con CSV, procedencia y
checksum. Extracción de solo lectura y comprobación contra la fuente; no añade
inferencias, juicios ni cargas de base. Se incorpora al mismo PR #156.

## Qué quedó hecho

- Inventario de qué medidas dependen del modelo ([inventario](../validation/model-dependence-inventory.md)) y lista de cifras de la memoria afectadas ([cifras](../validation/model-change-memory-figures.md)). La memoria no se copia al repositorio.
- Identidad del modelo en cada ejecución del dashboard (`generation_model_id`, proveedor, cuantización y huella de la configuración del gateway): dos ejecuciones con el mismo alias y distinto modelo no comparten serie. `gateway-config-hash` calcula la huella.
- Reejecución con DeepSeek V4.1 Flash: campaña ligera de JUP-071 (29 casos, una repetición, una revisora, provisional), coste de IA y banco de 28 preguntas de JUP-069 con el chat real. Gasto total ≈ 0,077 USD de 1,5 USD autorizados.
- Las ejecuciones nuevas están en el manifiesto versionado y cargadas en Grafana (12 ejecuciones y 647 resultados); los 18 paneles con SQL responden contra una pila real.

## Qué hay que saber para leerlo

- Las comparaciones con GLM-5.2 de JUP-071 no se pueden leer como mejora o empeoramiento: cambiaron a la vez el modelo, los recursos del chat (v3 a v4), el método de recogida y la muestra.
- El banco de 28 preguntas no tiene medición anterior con el chat real: es una referencia nueva, con 10 de 28 casos aprobados (la mitad de los fallos, 9 de 18, son solo del lector numérico automático).
- La latencia, la disponibilidad y los fallos técnicos son de la máquina local de Lucía; la lista de las que hay que repetir en la infraestructura definitiva está en el [plan](../validation/model-reevaluation-plan.md#sensibilidad-a-la-infraestructura-local).
- No se repitió la batería N3/N5 de 84 ejecuciones (necesita el ejecutor de la campaña B y revisión por requisito).

## Pendiente

- Capturas de pantalla de Grafana (hoy verificado por API).
- Histórico superado: PR #150 ya está integrado. Su merge no equivale a dos juicios humanos por respuesta ni autoriza aceptar las nuevas campañas.
- Cifras de la hoja de hechos sin origen en el repositorio (latencia 22,5/40,8 s, campañas RAG A-D); el coste 0,1806 USD de 28 operaciones sale del informe del 19/10 de Paris (véase la lista de cifras): indicar fuente antes de mantenerlas.
