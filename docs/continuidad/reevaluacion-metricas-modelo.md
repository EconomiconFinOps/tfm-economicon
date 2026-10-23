# Reevaluación de métricas tras el cambio de modelo — JUP-133

[Tarjeta](https://trello.com/c/Yv1ETc2G) · [Change](../../openspec/changes/archive/2026-10-22-jup-133-reevaluacion-metricas-modelo/) · [Informe antes y después](../validation/model-reevaluation-report.md) · [Evidencia](../evidence/JUP-133-validation.md).

Lucía lidera la tarjeta. Actualización documental: 23/10/2026. PR #150 se integró
el 22/10 a las 17:24 UTC; la mención anterior a PR abierto y merge pendiente queda
superada. Sus resultados siguen siendo provisionales.

## Corrección de la suite tras PR156 — 23/10/2026

Usuario: «Adelante con el siguiente paso». Rama `fix/JUP-133-dashboard-ci` desde
`develop` `db8f69a`. Corregidas las expectativas del manifiesto 18/1670 y aislados
los escenarios históricos con un manifiesto explícito de doce informes. Ocho
pruebas nuevas concilian las seis campañas, sus nulos/juicios, paneles y anotación
contra PostgreSQL con rol de lectura. Altura de matriz 61 para 55 filas, sin solapes.
No se cambian resultados, dataset, accesos, cuotas ni presupuesto de 10 USD.

Validación Linux completa: **1998 PASS sin omisiones**, 111.227 s, sobre árbol
`38c43415042bc1e438a8d7b5f6961fac0982a511`. OpenSpec 92 PASS, contratos CI 19 PASS,
CD Node 3 PASS y Python 60 PASS/3 omitidas por entorno explícito; higiene conforme.
Revisión independiente de agente con hallazgos corregidos, sin reviews humanas
inventadas. [Informe](../evidence/JUP-133/JUP-133-dashboard-ci-fix-report.md).

Corte previo a publicación: CI remota y reviews pendientes. El PR va a develop;
CD sólo puede validar la promoción después de integrarlo. Ningún despliegue ni
carga compartida ejecutados. Las incidencias funcionales y las campañas
provisionales siguen sin aceptación integral. El diagnóstico siguiente conserva
su fecha y describe el fallo anterior a la corrección.

Origen: «Levantar Jupiter en dockerDevelop», `01a16421-03a0-7460-b110-24738407ccb1`.

## CI posterior al merge de PR156 — 23/10/2026

PR156 confirmado integrado por squash `db8f69ab5e2d4a42931cd6dc7412b99e855f0148`
el 23/10 a las 19:38:28 París. Quedan superadas las menciones históricas a este
PR en borrador o sin merge. `develop` seguía en ese SHA al comprobarlo a las 19:47.

CI `39996735445` y CD `39996735531` terminaron con fallo. Backend, processor,
Azure Cost API, frontend, landing y los dos jobs AWS pasan. El único job fallido
es OpenSpec, dentro de `evaluation-dashboard:test`: 1960 pruebas, 110 fallos,
30 errores y 2 omitidas. `openspec:validate` no llegó a ejecutarse. CD reproduce
el fallo y omite `DockerServer deployment eligible`; no acredita promoción de
este SHA. JUP policy se omite por ser un push de develop, no es un fallo nuevo.

Los logs y fuentes muestran expectativas antiguas (12 ejecuciones / 647 filas
frente a 18 / 1670), escenarios que ya no seleccionan la última campaña esperada,
29 errores en cadena por mensajes de montaje de permisos desactualizados y un
IndexError de IDs. Además, la prueba de altura de matriz exige 57 unidades para
51 filas y encuentra 52. No se debe reducir todo a sustituir contadores. El
resultado anterior de tres fallos focales era un subconjunto, no la suite completa.

[Diagnóstico y bloqueos](../evidence/JUP-133/JUP-133-develop-ci-report.md) y
[snapshot de jobs](../evidence/JUP-133/JUP-133-develop-ci-report.json).
Siguiente paso: reconciliar pruebas/fixtures, selección y presentación del
dashboard; reejecutar la suite afectada y confirmar CI/CD. Se mantienen aparte
003/004/025, las 13 operaciones bloqueadas y las métricas no medidas que impiden
aceptación integral. Este encargo sólo diagnostica: sin fixes, ensayos, cargas,
despliegues, cambios de acceso/cuotas ni gasto del gateway.

Diagnóstico guardado localmente en `docs/JUP-133-ci-tras-pr156`, sin nuevo PR ni
publicación. Logs y estados completos en el expediente privado `agent-review/`.
Origen: «Levantar Jupiter en dockerDevelop»,
`01a16421-03a0-7460-b110-24738407ccb1`. Verificación: 2026-10-23.

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

En el corte de recogida no se nombraron dos personas revisoras ni se recibieron juicios humanos. El suplemento posterior con juez IA se documenta abajo. Calidad humana `not_measured`, revisión `not_run`. Los estados numéricos de JUP-071 son comprobaciones automáticas del instrumento, no juicio semántico. Las operaciones fallidas se conservan como bloqueadas; no se repitieron para obtener un resultado favorable.

El agregador JUP-070 exige tiempos por etapa que el chat nativo no expone cuando falla una operación. Quedó `blocked` en las tres repeticiones; se publican aparte los costes, intentos, completadas y latencias totales realmente medidos. No se inventan valores para satisfacer el contrato.

Configuración: `openrouter/deepseek/deepseek-v4.1-flash`, proveedor `deepinfra/fp8`, declarados y no atestiguados. Final 10000 tokens, corpus de cuatro documentos y doce fragmentos, misma configuración comprobada durante las seis recogidas y sellada al terminar. El histórico usaba otra segmentación; las diferencias no prueban un efecto causal del modelo o de la infraestructura.

El commit `84b53b74` corresponde al evaluador. El commit exacto del producto desplegado no está acreditado y queda nulo en los rows-v1; las imágenes efectivas se identifican por SHA-256 en el sello final.

Carga verificada por contenido exacto y consultas de Grafana.

El paquete conserva las 17 ejecuciones y 765 resultados previos y añade seis ejecuciones; resultado verificado de esa primera carga: 23 / 1284; el suplemento posterior lo amplía a 1788 resultados. El manifiesto de Git contiene 18 ejecuciones. La verificación exacta confirmó la conservación del histórico.

Informes: [comparación](../evidence/JUP-133/JUP-133-infra-comparison-report.md), [carga](../evidence/JUP-133/JUP-133-infra-load-report.md), [preparación histórica, superada](../evidence/JUP-133/JUP-133-infra-preflight-report.md). Los seis informes y rows-v1 están en `docs/evidence/JUP-133/`. Crudos, respuestas, recibos, fichas y hojas vacías de revisión quedan fuera de Git en `materiales/07-evidencias/JUP-133-campanas-infra-20261023/` del workspace.

Rama `test/JUP-133-campanas-infra-tres-repeticiones`, desde `develop` `84b53b74`. [PR #156](https://github.com/EconomiconFinOps/tfm-economicon/pull/156) contra `develop`, sin merge. Los papeles de revisión del PR no designan a las personas que puntuarán las respuestas.

La revisión humana por dos personas sigue pendiente; el usuario autorizó cubrir la rúbrica con un único juez IA, presentado como provisional, sin otorgar aceptación. La política de revisión del PR sigue pendiente; el check AWS demo offline observado falla por discrepancia del árbol de evidencia, fuera de este cambio documental. No se modifica el producto para ocultar estos bloqueos.

Regresión offline: 12 pruebas offline: 9 pasan y 3 fallan por expectativas fijas del manifiesto anterior (12 ejecuciones frente a las 18 actuales). El contrato rows-v1 y la conciliación independiente pasan; no se declara la integración en verde.

Origen: chat «Levantar Jupiter en dockerDevelop», `01a16421-03a0-7460-b110-24738407ccb1`. Verificación y actualización: 2026-10-23.

Ampliación solicitada después de la carga: publicar también el dataset Azure
con etiquetas usado en DockerDevelop. [Instantánea de 1.370 registros](../../fixtures/azure-cost/demo-tagged-20261023/README.md)
y [continuidad de datos](fecha-referencia-datos-demo.md), con CSV, procedencia y
checksum. Extracción de solo lectura y comprobación contra la fuente; no añade
inferencias, juicios ni cargas de base. Se incorpora al mismo PR #156.

## Suplemento con juez IA — 23/10/2026

Petición expresa: usar un agente como juez para completar cobertura. Se revisaron
individualmente las **158 respuestas disponibles** y sus **720 puntos semánticos**
(618 pass / 102 fail); las **13 operaciones sin respuesta verificable** siguen
blocked. Un agente, cero personas revisoras; ninguna campaña aceptada. Los estados
de caso combinan rúbrica y reglas numéricas originales, con sus límites conocidos.

Las seis métricas semánticas de robustez tienen ahora resultados para cada una de
las tres repeticiones. Las mediciones ausentes (distancias, etapas, contrato de
salida y disponibilidad HTTP) siguen not_measured; no se rellenaron con juicio.
Ambos campos grp y metric_id llevan `agent_`, con judgment=automatic, para separar
las series de las humanas. Se conservaron las filas humanas sin medir.

Tras la confirmación «Autorizar carga y paneles en DockerDevelop», carga ejecutada
a las 17:24 UTC y verificada por contenido exacto: **23 ejecuciones / 1788 filas**,
**1284 anteriores intactas + 504 nuevas**. Sólo cambiaron seis report_sha256.
Las **29 consultas de Grafana** responden sin error; revisión visual y captura
acreditan los tres paneles «Juez IA». No se tocó DockerServer, accesos ni cuotas.
Sin generaciones nuevas ni gasto adicional del gateway; tope 10 USD conservado.
El coste de Codex no se midió, no se considera gratuito.

[Informe de revisión](../evidence/JUP-133/JUP-133-agent-review-report.md) y
[carga verificada](../evidence/JUP-133/JUP-133-agent-load-report.json).
Juicios, metodología detallada, crudos y captura permanecen fuera de Git en
`materiales/07-evidencias/JUP-133-campanas-infra-20261023/agent-review/` del workspace.
Los informes y rows-v1 se incorporan al PR156; sigue en borrador, sin merge.
La CI de ebe30d4 conserva OpenSpec y JUP reviews fallidos; AWS demo offline falla
en push y pasa en PR. El nuevo commit tiene sus propios checks pendientes.

Origen: chat «Levantar Jupiter en dockerDevelop»,
`01a16421-03a0-7460-b110-24738407ccb1`. Verificación: 2026-10-23.

## Integración del PR156 solicitada el 23/10/2026

El usuario pidió «Haz el merge de PR 156» después de la entrega del suplemento.
Se prepara el squash mediante el PR existente y el mecanismo administrativo
del repositorio, registrando la integración como excepción: no existen reviews
humanas ni se afirma que la CI esté íntegramente conforme. En el head 2be5edd,
JUP reviews y OpenSpec fallan; otros checks seguían ejecutándose al preparar
esta integración. La orden de merge no acepta las campañas ni convierte el juez
IA en revisión humana.

Reconciliado sin conflictos con develop `3d4e574` (PR154 y PR157). Las evidencias
JUP-133, el manifiesto y el dataset etiquetado quedan idénticos al head anterior;
el contrato oficial rows-v1 vuelve a producir 18 ejecuciones / 1670 resultados.
No se cambia DockerDevelop, DockerServer, los accesos o el límite de 10 USD.
No se añaden inferencias ni nuevas pruebas funcionales. El PR enlazado conserva
el estado y SHA definitivos del merge; el expediente privado registra el recibo
de GitHub. Las protecciones permanecen activas, sin pushes directos a develop.

Origen y fecha: mismo chat `01a16421-03a0-7460-b110-24738407ccb1`, 2026-10-23.

## Qué quedó hecho antes de las seis repeticiones

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

- Captura actual de los tres paneles JUP-133 guardada en el expediente privado; no revalida visualmente todas las campañas históricas.
- Histórico superado: PR #150 ya está integrado. Su merge no equivale a dos juicios humanos por respuesta ni autoriza aceptar las nuevas campañas.
- Cifras de la hoja de hechos sin origen en el repositorio (latencia 22,5/40,8 s, campañas RAG A-D); el coste 0,1806 USD de 28 operaciones sale del informe del 19/10 de Paris (véase la lista de cifras): indicar fuente antes de mantenerlas.
