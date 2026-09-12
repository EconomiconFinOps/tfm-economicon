## ADDED Requirements

### Requirement: Contador de fallos de ingesta

`apps/processor` SHALL exponer un contador Prometheus dedicado que se incrementa cada vez que un job de ingesta termina en estado `failed`, independiente del contador genérico de requests HTTP.

#### Scenario: Un job de ingesta falla

- **WHEN** un job de ingesta se marca como `failed`
- **THEN** el contador de fallos de ingesta del processor se incrementa en 1

#### Scenario: Un job de ingesta se completa con éxito

- **WHEN** un job de ingesta se completa con éxito
- **THEN** el contador de fallos de ingesta del processor no se incrementa

### Requirement: Regla de alerta provisionada como código

El proyecto SHALL incluir una regla de alerta de Grafana Unified Alerting, provisionada desde archivos versionados en el repositorio, que pase a estado `Firing` cuando el contador de fallos de ingesta supere un umbral definido en una ventana de tiempo.

#### Scenario: Grafana arranca con la regla de alerta ya disponible

- **WHEN** se levanta el servicio `grafana` del compose por primera vez
- **THEN** la regla de alerta de fallos de ingesta está definida y activa sin pasos manuales de configuración

#### Scenario: Los fallos de ingesta superan el umbral

- **WHEN** el número de fallos de ingesta en la ventana de tiempo configurada supera el umbral definido
- **THEN** el estado de la alerta pasa a `Firing` y es visible en el dashboard de Grafana

#### Scenario: Los fallos de ingesta no superan el umbral

- **WHEN** el número de fallos de ingesta en la ventana de tiempo configurada está por debajo del umbral
- **THEN** el estado de la alerta permanece en `Normal`

### Requirement: Sin receptor externo en esta iteración

Esta capability SHALL limitarse a la visibilidad del estado de la alerta dentro de Grafana. No SHALL integrar ningún receptor externo (Discord, email, Slack, webhook) en esta iteración.

#### Scenario: La alerta se dispara sin notificación externa

- **WHEN** la alerta de fallos de ingesta pasa a `Firing`
- **THEN** no se envía ninguna notificación fuera del stack de Grafana
