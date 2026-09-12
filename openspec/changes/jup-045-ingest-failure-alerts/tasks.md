## 1. Contador de fallos de ingesta

- [x] 1.1 Test (RED): incrementar el contador de fallos de ingesta al marcar un job como `failed`
- [x] 1.2 Test (RED): no incrementar el contador cuando el job se completa con éxito
- [x] 1.3 Implementación (GREEN): añadir `ingest_jobs_failed_total` en `apps/processor/app/core/metrics.py` e incrementarlo en `JobsRepository.mark_failed()`

## 2. Regla de alerta de Grafana como código

- [x] 2.1 Crear `apps/monitoring/grafana/provisioning/alerting/` con la regla de alerta (umbral y ventana documentados en el propio YAML)
- [x] 2.2 Verificar en vivo (`docker compose up`) que Grafana carga la regla sin pasos manuales y que su estado es visible en el dashboard
- [x] 2.3 Verificar en vivo que forzar fallos de ingesta por encima del umbral dispara el estado `Firing`

## 3. Documentación y cierre

- [ ] 3.1 Documentar el contador y la regla de alerta en `docs/manuals/python-service-conventions.md`
- [ ] 3.2 Ejecutar suite completa de tests de `processor` en verde
- [ ] 3.3 Registrar evidencia de verificación manual (capturas o log de estados `Normal`/`Firing`)
- [ ] 3.4 Abrir PR, obtener revisión, mergear y archivar el cambio OpenSpec
