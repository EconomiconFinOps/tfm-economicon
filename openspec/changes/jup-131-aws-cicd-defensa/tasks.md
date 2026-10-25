# Tareas JUP-131

- [x] 1.1 Registrar tarea por puente Trello, aislar rama desde develop y conservar plan.
- [x] 1.2 Implementar bootstrap/state/roles y pipelines manuales.
- [x] 1.3 Implementar controlador con binding, lease, caducidad y retirada recuperable.
- [x] 1.4 Parametrizar perfil de retirada sin alterar arquitectura.
- [x] 1.5 Añadir pruebas locales/mock y CI sin credenciales AWS.
- [x] 1.6 Generar paquete local bloqueado de ensayo1 y runbook con entradas pendientes.
- [x] 1.7 Adaptar DSN/migraciones/consulta de costes a PostgreSQL y probar esquema completo, reejecución y tenant en PostgreSQL16 real; conservar contratos Cockroach.
- [x] 1.8 Integrar Cognito con frontend PKCE y verificación de identidad/tenant en backend; pruebas locales sin pool AWS.
- [x] 1.9 Integrar Bedrock y dimensión/reindexación coherentes en backend/processor.
- [x] 1.10 Implementar bootstrap privado, datos reproducibles y checks funcionales; completar receta/evidencia local sin simular aceptación AWS.
- [x] 1.11 Separar integridad de evidencia histórica y aceptación de aplicación en CI; conservar el bloqueo de despliegue por digest y acotar descargas APT del processor.
- [x] 1.12 Integrar Atlas aditivo privado, Grafana/Prometheus ECS, rutas, TLS y control de presupuesto30EUR; pruebas aisladas, sin AWS.
- [x] 1.13 Corregir la capacidad de chat de la receta a 5 y rechazar valores fuera de 5–8 o desalineados antes de planificar/aprovisionar; preparación local sin AWS y regresión contra el contrato real de arranque tras el fallo de ensayo2.
- [ ] 2.1 Completar cuenta/DNS/saldo/motores y aceptación de aplicación antes de ensayo real.
- [ ] 2.2 Obtener revisión/validación oficiales por roles humanos asignados.
- [ ] 2.3 Tras autorización futura, ejecutar ensayo1 y registrar tiempos/coste/retirada.

No hay autorización de despliegue en esta entrega. Las pruebas cloud y las
adaptaciones de producto no se marcan completadas por existir el pipeline.

Implementación local y revisión técnica incremental conformes el22/10/2026;
la CI del candidato se consulta en PR146. La aceptación AWS sigue pendiente.
