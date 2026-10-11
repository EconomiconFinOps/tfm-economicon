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