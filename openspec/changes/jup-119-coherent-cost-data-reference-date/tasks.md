JUP: JUP-119
Trello: https://trello.com/c/HtjtmPaJ

## 1. Sondeo y decisión

- [ ] 1.1 Sondeo con un nodo CockroachDB desechable y el stack aislado (`docker compose -p jup119`): servir con la API simulada un CSV mínimo que contenga cada caso límite de JUP-106 (cero, crédito negativo, dos monedas, importe mayor que `Number.MAX_SAFE_INTEGER`, servicio y grupo de recurso ausentes, grupos de recurso que solo difieren en mayúsculas, etiquetas ausentes) y cargarlo con la CLI de ingesta con una definición propia de septiembre y octubre de 2026. Registrar qué cruza y qué no, con la salida literal. Si la mayoría de los casos no cruza, parar y consultar a Lucia (D6).
- [ ] 1.2 Escribir `docs/adr/ADR-0021-demo-cost-data-single-path-and-reference-date.md` (plantilla `docs/templates/adr.md`) con la ruta única, la procedencia por etiqueta, el tope en la capa de lectura, el criterio de episodios, la fila sin fecha como prueba y las alternativas descartadas; enlazar ADR-0001 y ADR-0020 y añadirlo al índice de `docs/adr/README.md`.

## 2. Datos

- [ ] 2.1 Derivado del dataset público: generar `fixtures/azure-cost/derived/EA-Cost-Actual.shifted-2026-09.sample.csv` desplazando `Date`, `BillingPeriodStartDate` y `BillingPeriodEndDate` (2024-06-01 pasa a 2026-09-01) y añadir `dataset_origin=public-shifted` a las etiquetas; entrada de derivado en el manifiesto con fuente, desplazamiento, filas y checksum; comprobar con una prueba que el original no cambia, que solo difieren esas columnas y que el derivado es reproducible.
- [ ] 2.2 Generador determinista de la serie de costes (JUP-106 más la serie diaria sintética de 1/9 a 30/10) y de la serie de anomalías (1/9 a 21/9 idéntica a la anterior y 22/9 a 30/10 con al menos dos episodios nuevos), en formato de exportación de Azure con `dataset_origin=synthetic` y suscripciones con prefijo `synthetic-`. Manifiesto con tenant, suscripciones, origen, desplazamiento, filas y checksum.
- [ ] 2.3 Pruebas sin base de datos: cobertura continua del 1/9 al 30/10 por tenant (con los días vacíos documentados) y nada posterior al 30/10; totales por mes, moneda y origen recalculados con `Decimal`; las cifras de enero a julio de JUP-106 y del 1 al 21 de septiembre de JUP-107 no cambian; los esperados de `docs/demo/JUP-107/esperados-anomalias.json` ampliados con los episodios a 2026-10-31 y recalculados de forma independiente del backend; el cambio de un importe falla nombrando la cifra.

## 3. Carga

- [ ] 3.1 `scripts/demo_data.py` con `generate`, `apply`, `status` y `remove`: `apply` lanza la CLI del processor una vez por pareja tenant/suscripción con la definición del repositorio, es idempotente, se niega sin escribir si el tenant tiene datos ajenos o un estado parcial (código de salida 2) y no inserta filas por sí mismo; `remove` borra solo lo propio y, si el tenant queda sin otros costes, sus episodios y estado de detección.
- [ ] 3.2 Definición de ingesta de septiembre y octubre de 2026 por suscripción, perfil de demo en Compose (la API simulada sirve el CSV generado con `AZURE_COST_DATASET_PATH`) y `.env.example`.
- [ ] 3.3 Retirar `scripts/synthetic_costs.py` y `scripts/synthetic_anomalies.py` (o dejarlos como reenvío a `demo_data.py`), mover sus pruebas a las del nuevo flujo y mantener como prueba directa con CockroachDB real el caso de la fila sin fecha.
- [ ] 3.4 Prueba extremo a extremo con CockroachDB real: generar, servir con el proceso de la API, ingerir por la CLI, comparar los totales almacenados con los recalculados del CSV por tenant, mes, moneda y origen, repetir `apply` sin escrituras, `remove` que devuelve las tablas al estado previo, y lectura por billing y detección con la referencia en 2026-09-22 y 2026-10-31.

## 4. Fecha de referencia en el backend

- [ ] 4.1 `app/services/reference_date.py` y el ajuste `COST_REFERENCE_DATE` en la configuración: vacío usa el día UTC real, un `AAAA-MM-DD` válido lo fija y cualquier otro valor detiene el arranque nombrando el ajuste. Pruebas de los valores válidos e inválidos de la spec.
- [ ] 4.2 Tope único en `Database` (`_clamp_end`) para `fetch_billing_summary`, `fetch_tag_coverage` y la lectura diaria de la detección; la regla de fuentes solapadas sobre el periodo recortado; filas sin fecha sin cambios. Una prueba con CockroachDB real que llama a las siete lecturas (resumen, cobertura de etiquetas, presupuesto, consulta de prueba de anomalías, detección, pregunta de responsables) con datos posteriores a la referencia y comprueba que ninguna los incluye; periodo entero en el futuro igual a periodo sin datos; día de la referencia incluido y siguiente excluido.
- [ ] 4.3 Sustituir las lecturas del reloj que deciden el día visible en `billing.py` (periodo por defecto y `today` de la detección), `ownership_questions.py` (periodo por defecto) y `schemas/anomalies.py` (días cerrados hasta la referencia); la respuesta del asistente incluye periodo y fecha de referencia usados. Prueba que busca `datetime.now`, `date.today` y `utcnow` en esas rutas y servicios y falla si aparecen; barrido del mismo patrón por `apps/backend/app` registrado en `review.md`.
- [ ] 4.4 Episodios: visibles solo si su último día visto es anterior a la referencia; mismo 404 para ocultos y desconocidos en lectura y cambio de estado; reaparecen al avanzar la fecha; la detección repetida con la fecha avanzada no duplica episodios. Pruebas con CockroachDB real del retroceso y del avance (spec `demo-reference-date`).
- [ ] 4.5 `GET /billing/reference-date` autenticado con `{reference_date, simulated}` y sin otros ajustes; 401 sin sesión.

## 5. Frontend

- [ ] 5.1 Proveedor de la fecha de referencia cargada tras el login; `defaultMonthSelection`, el compositor del asistente y la cabecera la usan en vez de `new Date()`; aviso «Fecha simulada: dd/mm/aaaa» solo cuando `simulated`; estado de error explícito si falla el endpoint, sin volver al reloj del navegador. Pruebas del componente con el reloj del navegador fijado en una fecha distinta, y actualizar los contratos de `services/contracts.ts` y el cliente.

## 6. Verificación en el stack real

- [ ] 6.1 Stack aislado (`docker compose -p jup119`, volúmenes nuevos): cargar la demo con `demo_data.py apply`, abrir dashboard, `/anomalies` y chat con la referencia en 2026-09-22, comprobar los tres episodios de JUP-107, avanzar a 2026-10-15 y a 2026-10-31 y comprobar los episodios nuevos; retroceder y comprobar que se ocultan; en cada paso verificar en la interfaz real (no solo en las pruebas) el aviso de fecha simulada y que no aparece ningún dato posterior. Registrar comandos y resultados; parar el stack y borrar los volúmenes.
- [ ] 6.2 Medir el tiempo de la carga completa y registrar si hay que subir el tamaño de página del perfil de demo.

## 7. Documentación

- [ ] 7.1 Actualizar las guías de demo `docs/demo/JUP-065`, `JUP-106` y `JUP-107` con los comandos de `demo_data.py`, la fecha de referencia que cada paso supone, el aviso de datos desplazados y sintéticos antes de la primera cifra, y la nota de que retroceder la fecha oculta episodios.
- [ ] 7.2 `docs/architecture.md` (flujo de carga único, fecha de referencia), `apps/azure-cost-api/README.md` (servir el CSV de demo), `docs/data/azure-sample-dataset.md` (derivado desplazado), `docs/api` del endpoint de la referencia, `.env.example`, nota de continuidad `docs/continuidad/` y su fila en el índice.
- [ ] 7.3 Revisión documental completa limitada a datos de demo y fecha de referencia, hecha al terminar 7.1 y 7.2: buscar en todo el repositorio cada mención de `synthetic_costs.py`, `synthetic_anomalies.py`, «datos sintéticos», `AZURE_COST_DATASET_PATH`, el dataset público y «hoy»/fecha por defecto, y comprobar que nada describe un comportamiento distinto del implementado, que no hay afirmaciones contradictorias, que los enlaces funcionan y que nada se presenta como hecho sin estarlo. Dejar en `review.md` la lista de ficheros revisados, lo corregido y lo registrado.

## 8. Cierre y verificación

- [ ] 8.1 Batería completa: pruebas de backend, processor, API simulada y frontend, pruebas con CockroachDB real en local (nodo desechable), `openspec:validate`, `jup:check:all`, `jup:cleanup:check`, `corepack pnpm lint` y `git diff --check`. Registrar comandos y resultados.
- [ ] 8.2 Revisión adversarial (agente `adversarial-reviewer`) hasta `accept` o aceptación explícita de Lucia, y `review.md` con la sección `## Adversarial Review`, el barrido de patrones, los riesgos y los hallazgos registrados.
- [ ] 8.3 Evidencia en `docs/evidence/JUP-119-validation.md` (el código de producto cambia) y bloque `## Human Approval` post-review de Lucia, con las dos preguntas abiertas de `design.md` resueltas.
- [ ] 8.4 Archivar el change en la misma rama, revisar la documentación posterior al archivo y abrir el PR a `develop`.
