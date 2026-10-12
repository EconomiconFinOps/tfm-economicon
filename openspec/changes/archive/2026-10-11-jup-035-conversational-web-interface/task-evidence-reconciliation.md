# JUP-035 — Correspondencia de tareas con evidencia

Comprobación documental del PM: 2026-10-11. No ejecución nueva de tests ni aceptación humana simulada. Las rutas externas son relativas a la entrega de Autónomo e5-context-compression-evidence; los resultados conservan snapshot y entorno originales.

| Casilla marcada | Evidencia comprobada | Alcance y límites |
| --- | --- | --- |
| 22, 28, 31 | tasks.md, aprobaciones registradas en38/40 y diseño general09/10/2026 23:23:27; JSONB10/10 09:15:41; integration-readiness-plan.md y design-decision-matrix.md | Decisiones y aprobación pre-code cumplidas; no se atribuye integración futura de JUP-036. Ownership se preserva en la reconciliación con develop. |
| 52 | restart-20261011/delivery.md, tabla Red: backend13FAIL/1PASS, processor6FAIL/1PASS, frontend2FAIL/10PASS, recovery1FAIL/43PASS | Fases Red significativas conservadas, no se presentan como fallos actuales. |
| 53 | mismo delivery.md, primeros Green14/7/12; fortalecidos18/8; migration-native.log; native-backend-regressions.log y green-native-final.log | Migración004 aditiva, CAS, budgets y barrera UI; se conservan fallos históricos de fixtures/empaquetado, corregidos o atendidos en entregas posteriores. |
| 54 | mismo delivery.md, once mutantes focales detectados; logs mutations-backend, processor-strengthened, frontend y native-shutdown | Superviviente inicial de bytes reforzado y posteriormente detectado; copias desechables con restauración/hashes. |
| 55 | delivery.md; restart-20261011/review-2.md y entrega posterior recibida en PM | Implementación y evidencias entregadas; coordinación transferida a Autónomo por decisión de Paris. No se acredita un envío nuevo al TL ni guard original del PM. |
| 65 | chat-delete-browser-20261011.md, capturas de confirmación/resultado y deletion-delivery.md | Borrado de fixture vacío persistente tras recarga en Cockroach; nueve conversaciones ajenas preservadas. Borrado de historial poblado y rollback comprobados por tests, no por navegador. |
| 71 | restart-20261011/compose-chat/runtime/validation.md y ai-repeat-validation.md | Arranque mock, SSE y persistencia; evidencia IA posterior conserva sus propios límites y snapshot. |
| 76 | restart-20261011/summary-timeout/delivery.md, parent-integrity.md y compose-chat/runtime/ai-repeat-validation.md | Revisión independiente favorable comunicada; una recuperación real válida, tres pares y14 mensajes preservados tras reinicio. Guard del padre Autónomo, no creado por PM. |

## Entradas que no se marcan completas sin más referencia

- 16: agrupa cierre local, controles independientes y reviews humanas futuras. Archivo autorizado realizado; no se acreditan reviews humanas.
- 42: incluye todos los controles del diseño y guard PM previo a roles independientes; una entrega de implementación no demuestra esa condición completa.
- 48: hay pruebas de componentes JSONB, CAS, migración y recuperación; falta correspondencia íntegra de su matriz histórica, incluida concurrencia y commit ambiguo.
- 49/50: falta informe específico completo de retirada activa legacy y referencia original aplicable del PM; la revisión de compresión o guard de Autónomo no sustituye esas condiciones.
- 51: falta referencia de consolidación completa de criterios/límites; las entregas parciales no se atribuyen automáticamente al TL.
- 60: chat-titles-browser-20261011.md acredita renombrar, Escape y persistencia tras recarga; pendiente localizar decisión humana concreta que también exige esta casilla.

Paris autoriza pedir las evidencias existentes a Autónomo. Solicitud enviada el11/10/2026 19:53:22 Atlantic/Canary. No se solicita reconstruir referencias de integridad, repetir baterías ni nuevas llamadas.

## Cierre documental de entrega — 12/10/2026

Actualización TL autorizada por PM; conserva las decisiones y dictámenes
originales y las siete casillas sin marcarlas por inferencia. Fuente final:
feat/JUP-035-chat-delivery, checkpoint42e9ff073bcc3380aeb9b8bda1315a092cbbc4b0
con RAG/batería importados sobre2814403/develop8035a3d. No JUP-036.

| Casilla | Evidencia posterior disponible | Condición aún no acreditada / siguiente acción |
| --- | --- | --- |
| 16 | Archivo11/10 autorizado; batería25/28 más focales; REVIEW_PASS y VALIDATION_PASS010; PM original1130 y controles independientes comunicados | Reviews humanas de Alejandro/Lucía futuras. La revisión/revalidación de importación exige checkpoint final; no marcar todo como hecho. |
| 42 | Entrega unificada42e9ff0; consolidación técnica12/10; original1130 PASS antes de commit | Falta correspondencia completa de los controles históricos de diseño. Referencia nueva PM antes de lectores del checkpoint final; no reutilizar guard narrow010 como guard de todo el diseño. |
| 48 | Informe posterior remaining-validation/report-48-50.md leído completo:94focales+5deadline y4Cockroach reales; matriz íntegra asignada VALIDATION_PASS | Supera la falta de referencia del mapa11Oct previo. ACK postCOMMIT, concurrencia, rollback, CAS/linaje y migración acreditados en sus entornos; cinco productores son scripted/SQLite, no llamadas reales. Reutilización histórica no es nueva batería final. |
| 49 | Revisión conninfo/diagnósticos REVIEW_PASS y revisión incremental histórica archivada | No se localizó informe específico completo de retirada activa legacy y restos necesarios con original PM aplicable. Obtener referencia exacta mediante PM; no atribuir al review narrow010. |
| 50 | Informe específico48/50 VALIDATION_PASS e original PM d8aea18e... verificado; snapshot previo20:05:47UTC11Oct y guard de retorno20:42:23UTC registrado | Matriz asignada acreditada con límites nativos/offline explícitos. Tres skips nativos summary excluidos; no scope nativo adversarial nuevo ni cincoLLM.010 es evidencia adicional posterior, no sustituto de esta matriz. |
| 51 | TL consolida este índice y cierre versionado; separa evidencia vigente, histórica y límites;036 espera | Límite a medir identificado: tamaño del JSONB canónico y coste de lectura/actualización y render al acumular pares.010 no mide escala. No introducir retención/paginación ni integrar036. Conserva abierto el checklist amplio hasta correspondencia completa de las fuentes. |
| 60 | chat-titles-browser-20261011.md histórico: rename, Escape, recarga; archivo autorizado11/10 y aprobación focal posterior comunicada | Falta referencia humana específica del hito runtime/títulos exigido por esta casilla. La aprobación de RAG/batería12/10 no demuestra retroactivamente esa decisión; PM localiza referencia o consulta decisión concreta. |

«No localizada» significa falta de referencia en este corte, no prueba de que
el trabajo no ocurrió. Los encabezados anteriores que decían revisión o real010
pendientes conservan su fecha; el ensayo posterior los supera sólo en su alcance.
La bateríafull28 y los FAIL originales permanecen sin recalificación.
Para48/50 el mapa anterior quedó superado por informe específico posterior;
las casillas originales se conservan como registro histórico y esta matriz
acredita su disposición técnica. Originales PM SHA9ff66090... y d8aea18e...
verificados, creados20:05:46/47UTC11Oct (21:05:46/47Atlantic/Canary), no ahora.
Véase [cierre y checks del checkpoint](../../../../docs/evidence/jup-035-delivery-reconciliation-20261012.md).
