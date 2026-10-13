JUP: JUP-119 · ADR: [ADR-0021](../../../docs/adr/ADR-0021-demo-cost-data-single-path-and-reference-date.md) (nuevo en este change)

## Context

Ver `proposal.md` (Why) y las specs `demo-cost-data-single-path` y `demo-reference-date`. Estado de partida, comprobado en el código:

- La API simulada (`apps/azure-cost-api`) sirve el CSV que apunte `AZURE_COST_DATASET_PATH` (por defecto `fixtures/azure-cost/EA-Cost-Actual.sample.csv`) y exige columnas del mapa `docs/api/azure-cost-query-mapping.json`. `CostRepository._load_records` convierte `Date` con `%m/%d/%Y` y **rechaza la fila entera** si no tiene fecha válida: la API no puede servir una fila sin fecha.
- La CLI de ingesta (`python -m app.run_azure_cost_ingestion --tenant-id … --subscription-id … [--definition-file …]`) usa por defecto una definición con `timePeriod` 2024-06-01 a 2024-06-20, así que hace falta una definición propia para septiembre y octubre de 2026. La ingesta es idempotente por tenant, suscripción y definición.
- `scripts/synthetic_costs.py` (JUP-106, `tenant-growth`, enero a julio de 2026, con casos límite) y `scripts/synthetic_anomalies.py` (JUP-107, `tenant-core`, 1 a 21 de septiembre) escriben directamente en `azure_cost_records` y `azure_cost_ingestion_runs`, con su prefijo y la marca `synthetic` en la petición de la ingesta, y se niegan a cargar si el tenant ya tiene datos reales.
- El «hoy» se decide en `apps/backend/app/api/routes/billing.py` (periodo por defecto y `today` de la detección), `apps/backend/app/services/ownership_questions.py` (periodo por defecto y `queried_at`), `apps/backend/app/schemas/anomalies.py` (solo días cerrados) y en el frontend (`MessageComposer.tsx`, `lib/executiveCostDashboard.ts`, `Layout.tsx`). La detección ya recibe `today` como parámetro (`detection_window`).
- Las lecturas de coste del backend (`Database.fetch_billing_summary`, `fetch_tag_coverage`, la serie diaria de la detección) filtran por `usage_date >= :start AND usage_date < :end` y rechazan fuentes solapadas con `AmbiguousCostSource`.

## Goals / Non-Goals

**Goals:** una sola ruta de carga de los datos de demostración (generador → API simulada → CLI), un derivado honesto del dataset público, series sintéticas hasta el 30/10/2026 que conserven los esperados de JUP-106 y JUP-107, y una fecha de referencia configurable aplicada en un solo punto del backend y leída por el frontend.

**Non-Goals:** servicio de carga diaria, ejecución periódica de la detección y avisos (JUP-115), cambiar la fecha desde la interfaz, datos reales, conversión de moneda, cambios de esquema o de migraciones, cambiar el corpus del asistente.

## Decisions

**D1. Ruta única: generador de CSV → API simulada → CLI de ingesta.** `scripts/demo_data.py generate` produce un CSV con el formato de exportación de Azure y un manifiesto (tenant → suscripciones, origen de cada una, desplazamiento de fechas, filas y checksum). La API simulada lo sirve con `AZURE_COST_DATASET_PATH` y `apply` lanza la CLI del processor una vez por pareja tenant/suscripción con una definición del repositorio. Alternativas descartadas: (a) mantener los inserts directos y compartir solo el generador, porque deja dos caminos y la ingesta real nunca ve los datos de demo; (b) un endpoint de importación masiva en el backend, porque crea superficie nueva de escritura sin necesidad; (c) que la API sirva varios CSV a la vez, porque cambia su contrato para un uso de demo. Consecuencia: los casos límite que la API no puede servir salen del CSV (ver D6).

**D2. La procedencia viaja en los datos, no en la petición de la ingesta.** Hoy los scripts marcan `request.synthetic = true` en la ingesta; con la CLI esa petición es la definición. La marca pasa a ser el prefijo `synthetic-` de la suscripción (el alcance viene del path autenticado) y la etiqueta `dataset_origin` (`public-shifted` o `synthetic`) en la columna `Tags`, que la normalización conserva. Con ella `apply` distingue «datos de esta demo» de «datos ajenos» y `remove` borra solo lo suyo.

**D3. Un servicio de fecha de referencia y un tope en la capa de lectura.** `app/services/reference_date.py` resuelve `COST_REFERENCE_DATE` al arrancar (validación estricta con `date.fromisoformat` tras comprobar el formato de diez caracteres) y devuelve «hoy» llamando al reloj solo cuando el ajuste está vacío. El tope no se pone en cada ruta: se pone dentro de `Database` en un único punto (`_clamp_end`) que usan `fetch_billing_summary`, `fetch_tag_coverage` y la lectura diaria de la detección, de modo que ninguna ruta nueva pueda olvidarlo. Alternativas: filtrar en las rutas (se olvida en la siguiente) y una vista SQL (el tope depende de configuración, no del esquema). El tope se aplica al final del periodo pedido (`min(end, referencia + 1 día)`); las filas sin fecha conservan su tratamiento. La regla de fuentes solapadas se evalúa sobre el periodo ya recortado, así que un solape posterior a la referencia no bloquea.

**D4. Episodios: se ocultan los que llegan más allá de la referencia.** Un episodio es visible si su último día visto es anterior a la referencia (es decir, anterior a «hoy»). Si se retrocede la fecha, los episodios posteriores se ocultan con el mismo 404 que un id desconocido y reaparecen al volver a avanzarla; no se recalcula el impacto «como habría sido». Es lo más simple, no deja ver impacto de días que no han llegado y no inventa un histórico. Para reproducir la demo desde el principio tras retroceder se usa `remove` y `apply` (que borra episodios y estado de detección). Alternativa descartada: recalcular el impacto hasta la referencia, porque obliga a guardar el detalle diario o a releer costes en cada listado. Pregunta abierta para Lucia más abajo.

**D5. El frontend lee la fecha del backend.** `GET /billing/reference-date` devuelve `{reference_date, simulated}` al usuario autenticado. Un proveedor de contexto lo carga una vez tras el login y se lo pasa a `defaultMonthSelection(now)` (ya acepta `now`), al compositor del asistente y a la cabecera, donde se muestra «Fecha simulada: dd/mm/aaaa» si `simulated` es verdadero. Si falla, estado de error explícito; no se vuelve al reloj del navegador. El nombre de la ruta es una decisión menor: va bajo `/billing` porque solo los costes la usan.

**D6. Casos límite que no pasan por la API.** Una fila sin fecha de uso la rechaza la API. Se mantiene como caso de prueba construido directamente (prueba de billing con CockroachDB real) y se documenta en la referencia del dataset por qué no está en el CSV. El resto de casos de JUP-106 (cero, crédito negativo, dos monedas, importe mayor que `Number.MAX_SAFE_INTEGER`, dimensiones ausentes, grupos de recurso que solo difieren en mayúsculas) sí caben en el CSV; la tarea 1.1 lo comprueba con un nodo desechable antes de seguir. Si alguno no cruza la CLI (por ejemplo por la normalización), se trata igual que la fila sin fecha y se registra en el ADR. Este es el punto de salida de emergencia: si la tarea 1.1 muestra que la mayoría de los casos no cruzan, se para y se vuelve a hablar con Lucia antes de seguir.

**D7. Dónde vive cada dataset.** `tenant-core`: la serie de anomalías (suscripción `synthetic-anomalies`, 1/9 a 30/10). `tenant-growth`: la serie de costes de JUP-106 (enero a julio, sin cambios) más una serie diaria sintética de 1/9 a 30/10 en euros, y el derivado del dataset público en su propia suscripción (1 a 19 de septiembre). La cobertura continua se exige a la serie diaria sintética de cada tenant; el derivado público, con 16 días en 19, queda como una suscripción más etiquetada, con los días vacíos documentados. Pregunta abierta para Lucia.

**D8. Extensión de las anomalías.** Del 22/9 al 30/10 cada servicio sigue su patrón y se añaden al menos dos episodios nuevos (por ejemplo, Storage con un salto sostenido a mitad de octubre y Tools con un salto aislado que no pasa la tolerancia), con cifras fijadas en `esperados-anomalias.json` por una prueba independiente. Las cifras del 1 al 21 de septiembre no cambian: con la referencia en 22/9 la detección da los mismos tres episodios de JUP-107.

**D9. ADR-0021.** Registra la ruta única, la procedencia por etiqueta, el tope en la capa de lectura, el criterio de episodios y la fila sin fecha como prueba. Enlaza con ADR-0001 (la API simulada pasa a servir un CSV de demo, no solo el público) y ADR-0020 (los episodios obedecen a la referencia).

## Risks / Trade-offs

- [El mayor alcance es la ruta única, no la fecha] → La tarea 1.1 es un sondeo con un nodo desechable antes de escribir nada; si falla, se para y se replantea.
- [El tope se olvida en una lectura nueva] → Un solo punto en `Database`, una prueba que llama a las siete lecturas con datos posteriores a la referencia y la prueba de «ninguna lectura del reloj» sobre las rutas y servicios afectados.
- [La demo de 3 minutos cambia al abrir en septiembre u octubre] → El guion declara la fecha de referencia que supone y las cifras de enero a julio no cambian; hay que re-ejecutar la receta del navegador.
- [Ocultar episodios al retroceder puede sorprender] → Documentado en la guía (retroceder oculta, `remove`/`apply` reinicia) y probado.
- [Los datos futuros existen en la base aunque no se vean] → Es una limitación honesta de la demo; la documentación lo dice. No es un control de acceso: quien lea la base directamente los ve.
- [Rendimiento de la carga: unas 500 filas por suscripción en páginas de 10 con reintentos acotados] → La CLI ya pagina; se mide en la tarea 6.2 y, si tarda, se sube el tamaño de página solo en el perfil de demo.
- [Cambio de nombre y de comandos de los scripts] → Los scripts antiguos se retiran y las guías se actualizan en el mismo change; la skill local del equipo no se versiona y se avisa a Lucia.

## Migration Plan

1. Sin migraciones de esquema. 2. `apply` sobre una base con datos de los scripts antiguos se niega (esas filas llevan otra marca): se documenta `remove` con la versión anterior del script (o limpieza manual del tenant en el stack local) antes de cargar con la nueva ruta. 3. Retroceso: volver al commit anterior y cargar con los scripts antiguos; el ajuste `COST_REFERENCE_DATE` sin valor deja el comportamiento de antes.

## Open Questions

- ¿El derivado del dataset público va en `tenant-growth` (propuesta) o en un tenant propio? Un tenant propio evita mezclar su dólar con el euro sintético, pero exige crear tenant y usuario en el seed.
- Ocultar los episodios posteriores a la referencia (propuesta, D4) o recalcular su impacto hasta ella.
