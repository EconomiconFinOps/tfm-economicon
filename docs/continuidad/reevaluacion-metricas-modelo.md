# Reevaluación de métricas tras el cambio de modelo — JUP-133

[Tarjeta](https://trello.com/c/Yv1ETc2G) · [Change](../../openspec/changes/archive/2026-10-22-jup-133-reevaluacion-metricas-modelo/) · [Informe antes y después](../validation/model-reevaluation-report.md) · [Evidencia](../evidence/JUP-133-validation.md).

Lucía lidera la tarjeta. Actualización documental: 23/10/2026. PR #150 se integró
el 22/10 a las 17:24 UTC; la mención anterior a PR abierto y merge pendiente queda
superada. Sus resultados siguen siendo provisionales.

## Nueva preparación en DockerDevelop — 23/10/2026

Encargo: repetir por separado JUP-070 A (28 preguntas) y JUP-071 (29 casos), tres
veces cada una, compararlas y preparar su carga. Rama
`test/JUP-133-campanas-infra-tres-repeticiones`, desde `develop` `84b53b74`.
[Informe y seis lotes previstos](../evidence/JUP-133/JUP-133-infra-preflight-report.md).

El usuario autorizó expresamente el lanzamiento, sustituyendo la confirmación
de Lucía, y amplió el tope de 1,50 a **6,50 USD totales**. Se conservan ≈0,077 USD
del plan anterior y el límite global de la demo de 10 USD. La reserva mínima del
colector es 6,50 por operación: **6,50 + ≈0,077 > 6,50**, por lo que la admisión
sigue bloqueada. La propuesta de 7,50 USD está pendiente de respuesta, no
autorizada. El CLI tampoco conecta aún la liquidación de todos los intentos;
ese adaptador y la extracción efectiva deben quedar verificados antes de gastar.

Preparados fuera de Git 28 prompts y un plan de 87 muestras de robustez. Validadas
entradas e identificadores, sin recoger respuestas. Referencia histórica de cinco
operaciones en esta infraestructura: 0,0192297384 USD; proyección media para 171
muestras: 0,65765705328 USD nuevos, sin garantía ni factura upstream. No se usan
sus juicios. No hay dos personas designadas: futuras campañas provisionales,
juicios humanos `not_run`. Costes nuevos `not_measured`/`null`.

Lectura de Grafana a las 13:20:02 UTC: 20 consultas SQL sin errores, 17 ejecuciones
y 765 resultados; no revisión visual ni carga nueva. El manifiesto versionado
conserva 12 ejecuciones. No reemplazar la base compartida sin preservar las cinco
incorporaciones locales y sin confirmación específica. No se añadieron entradas
de ejecución ficticias a `evaluation-runs.json`.

Material privado y scripts: respecto del workspace,
`materiales/07-evidencias/JUP-133-campanas-infra-20261023/`. Solo informes
sanitizados bajo `docs/evidence/JUP-133/`; las futuras respuestas, fichas, hojas,
crudos y juicios seguirán fuera de Git. Modelo declarado por el gateway:
`openrouter/deepseek/deepseek-v4.1-flash`, `deepinfra/fp8`, huella
`9b345f3017a142d5f2db605a8921ec6fc488b2d97977edb069733aeee670c4f8`; no atestigua
qué modelo respondió.

Siguiente paso: resolver reserva más acumulado, preparar la liquidación y
extracción, ejecutar seis recogidas con la misma configuración, puntuar sin
inventar juicios y solicitar la carga cuando exista un reemplazo revisable.
Origen: chat «Levantar Jupiter en dockerDevelop»,
`01a16421-03a0-7460-b110-24738407ccb1`.

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
