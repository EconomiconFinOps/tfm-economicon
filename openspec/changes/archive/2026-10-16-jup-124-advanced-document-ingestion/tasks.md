# Tareas JUP-124

Registro retrospectivo del 16/10/2026. La implementación siguiente se completó
experimentalmente antes de crear el change; no representa OpenSpec pre-code.
Véanse [evidencia y límites](../../../../docs/evidence/JUP-124-validation.md).

## Implementación anterior registrada

- [x] 1.1 Extraer formatos admitidos y PDF digital/escaneado/mixto con OCR local y límites.
- [x] 1.2 Admitir un archivo, 20.000.000 bytes y reserva por usuario con concurrencia entre usuarios.
- [x] 1.3 Verificar autorización, tenant, tamaño/hash/formato reales y rechazos sin trabajo válido.
- [x] 1.4 Incorporar MinIO privado e inicialización/CORS al Compose general.
- [x] 1.5 Mantener estados, confirmación idempotente, outbox/cola, reintentos y checkpoint durable.
- [x] 1.6 Recuperar ejecución/limpieza conservando originales pendientes y normalizado.
- [x] 1.7 Preservar texto manual, pipeline/embeddings/retrieval/citas y aislamiento anteriores.
- [x] 1.8 Reutilizar estilos/temas/responsive sin opción visual de reprocesado forzoso.
- [x] 1.9 Registrar migración/configuración/docs y corregir provisión CD/puertos por ranura.
- [x] 1.10 Alinear fixtures/contrato local:doctor conservando negativos y saneamiento.

## Formalización documental actual

- [x] 2.1 Mapear los diez criterios oficiales a requisitos, escenarios y evidencia histórica identificada.
- [x] 2.2 Registrar diseño retrospectivo y ADR-0022 Proposed reutilizando decisiones existentes.
- [x] 2.3 Validar OpenSpec estricto, trazabilidad, enlaces y coherencia sin modificar producto/tests.
- [x] 2.4 Comprobar preservación de código y evidencias anteriores.

Evaluación documental local actual se entrega por separado al liderazgo. Roles
humanos asignados no significan aportaciones/reviews realizadas. Ratificación
del ADR, reviews humanas, aprobación final, archivo y publicación permanecen
separados: no se marcan completados por esta lista ni se archiva el change aquí.
