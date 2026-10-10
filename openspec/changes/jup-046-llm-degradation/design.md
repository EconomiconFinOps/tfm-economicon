## Context

Trello mantiene prioridad P1 y roles: Lucía liderazgo, Paris pairing, Víctor revisión,
Alejandro validación. Criterios originales generales preservados; esta propuesta
concreta el comportamiento técnico sin atribuir aceptación o participación humana.

## Decisions

- Reutilizar registro Prometheus y provisioning Grafana (ADR-0005 y JUP-045).
  No se introduce un scheduler ni un estado de alerta en memoria de la aplicación.
- Contar una operación lógica tras validar el vector o FinOpsResponse, no cada
  intento HTTP. Un reintento recuperado es éxito y su tiempo forma parte de la latencia.
- Separar series por `job`, `instance`, `operation`; categorías acotadas y sin
  etiquetas de modelo, tenant, consulta, request_id, URL o credenciales.
  Los logs estructurados conservan la correlación existente fuera de las métricas.
- Ventana 5m, mínimo 5 operaciones, fallo estrictamente >20%, p95 estrictamente
  >10s para embeddings o >20s para generación, confirmación 2m, evaluación 1m.
  Son valores iniciales revisables, no conclusiones extraídas de la baseline JUP-070.
- Series ausentes: NoData; fallo de consulta: Error; pocas muestras o tráfico parado:
  no activación. Normal significa que la regla no detecta un incumplimiento suficiente,
  no un dictamen de calidad/salud. Ver volumen y panel de salud JUP-047.
- Reglas y panel sin configurar receptores. Las pruebas usan un entorno aislado sin
  canales externos. Un despliegue con políticas de notificación propias debe revisarlas.

## Risks and limits

Los histogramas aproximan p95. Los contadores viven en el proceso; `run_all` comparte
worker/API, pero procesos separados requieren otro scrape o multiprocess antes de
operar estas alertas. La primera muestra y operaciones iniciadas antes de un reinicio
pueden no contabilizarse en `increase`; no equivale a auditoría exacta. DNS síncrono
mantiene la limitación de los transportes existentes. Una llamada aún colgada no
produce una observación final; salud y métricas HTTP siguen siendo complementarias.
No mide corrección semántica: evaluación JUP-067/070 conserva su contrato y límites.

## Validation

Pruebas de fronteras Python con transportes dobles, métricas y privacidad; fixtures
promtool extraídos del mismo YAML de Grafana verifican comparación, mínimo, duración,
recuperación, reinicio e independencia. Evidencia y límites en
`docs/evidence/JUP-046-validation.md`.
