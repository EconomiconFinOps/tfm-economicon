JUP: JUP-114

## 1. Backend

- [x] 1.1 Ejecución sin límite de días (D1): `detection_window` con el primer día observado del tenant, sin `MAX_DAYS_PER_RUN` ni `unevaluated_range`; pruebas de primera ejecución sobre toda la historia, días perdidos entre ejecuciones y equivalencia entre una pulsación y una por día; mutantes del nuevo límite inferior.
- [x] 1.2 La lista devuelve `last_evaluated_date`, `includes_synthetic_data` y `open_impact_by_currency` (D2) para cualquier `scope`; pruebas con CockroachDB real de nunca detectado, marca sintética por tenant (solo sintético, solo ingesta, mezcla, otro tenant), totales exactos por moneda y aislamiento.
- [x] 1.3 Actualizar ADR-0019, `docs/api/anomaly-episodes.md`, `LIMITATIONS` y `RF-114-006` (resuelto) por la eliminación del límite.

## 2. Datos de demo

- [x] 2.1 Rehacer `ROWS` de `scripts/synthetic_anomalies.py` con gasto diario del 1 al 21 de septiembre (D7) y `remove` que borra episodios y estado de detección del tenant; `status` con el número de episodios.
- [x] 2.2 `docs/demo/JUP-107/esperados-anomalias.json` con recuentos nuevos y la sección de episodios; prueba sin base de datos que recalcula de forma independiente sumas por periodo y regla diaria; pruebas con CockroachDB real de `remove` (solo su tenant, repetible) y de recarga y nueva detección; mutantes.

## 3. Frontend

- [x] 3.1 Cliente y contratos: `fetchAnomalyEpisodes`, `detectAnomalies`, `changeAnomalyEpisodeStatus` en `services/api.ts` y validadores en `services/contracts.ts`, con pruebas de respuestas válidas e inválidas.
- [ ] 3.2 Panel: resumen, tabla, filtros, leyenda, «Detectar ahora» con su aviso, «Revisado hasta», estados vacíos, carga, error, cambio de tenant y aviso sintético (D3, D4, D6); quitar `data/demo/anomaliesPanel.ts`; pruebas de cada escenario de la spec, incluidos doble pulsación, importes grandes sin pérdida de céntimos y monedas que no se suman.
- [ ] 3.3 Detalle con acciones (D5): investigación, cierre con motivo, confirmación y aviso de irreversible, errores 404/409/422, sin acciones en cerrados; pruebas de teclado y foco.
- [ ] 3.4 Exportación CSV/PDF con las columnas nuevas y nombre de fichero; prueba de que coincide con las filas filtradas.

## 4. Demo y documentación

- [ ] 4.1 Guion de 3 minutos (D8): paso de Anomalías tras el aislamiento, D7 opcional, paso de límites a 5 s, total 180 s; `preguntas.md`, `README.md`, preparación y `anomalias.md`; pruebas de la demo actualizadas.
- [ ] 4.2 Receta de navegador con el paso de Anomalías (aviso sintético, «Revisado hasta 20/09», Alta (P1) Compute primero, detalle abierto) y su control positivo.
- [ ] 4.3 Revisión documental limitada a anomalías y a la demo (mismo alcance que la 4.4 del change 1: drift, contradicciones, enlaces, nada presentado como hecho sin estarlo), nota de continuidad y hallazgos.

## 5. Cierre y verificación

- [ ] 5.1 Batería completa: backend con CockroachDB real, processor (incluidas las guardas de propiedad y las migraciones con CockroachDB real), frontend (`vitest`, `tsc`, build), suites de `scripts/tests`, `openspec:validate`, `jup:check:all`, `jup:cleanup:check`, `corepack pnpm lint` y `git diff --check develop`. Registrar comandos y resultados.
- [ ] 5.2 Validación con stack real aislado y volúmenes nuevos: preparación de la guía, ruta de 3 minutos con la receta de navegador y comprobación visual del panel en escritorio y a 390 px, incluido el tema oscuro; retirada de los dos conjuntos con el tenant sin episodios ni marca de agua.
- [ ] 5.3 Revisión adversarial (agente `adversarial-reviewer`) hasta `accept` o aceptación explícita de Lucia, y `review.md` con sus pasadas, el barrido de patrones, los riesgos y los hallazgos.
- [ ] 5.4 Evidencia en `docs/evidence/JUP-114-validation.md` por criterio de la tarjeta y bloque `## Human Approval` post-review de Lucia.
- [ ] 5.5 Archivar el change en la misma rama, rellenar el Purpose de `openspec/specs/anomalies-panel/spec.md` y revisar la documentación posterior al archivo. No se abre PR: los tres changes de JUP-114 van en un solo PR que se abre al terminar el último.
