# JUP-131 — adaptación de aplicación para el ensayo AWS

Autorizada por el usuario el 21/10/2026. Complementa
[el plan de CI/CD](aws-cicd-defensa.md) y [el runbook](../deployment/aws-defensa.md).
No autoriza llamadas a AWS, despliegue, cambios DNS ni gasto cloud.

## Resultado y contratos

Conservar la arquitectura de `infra/aws-reference` y los modos de desarrollo.
La aplicación debe poder usar RDS PostgreSQL, Cognito y Bedrock mediante roles
ECS; el bootstrap debe preparar bases, secretos, identidades y datos dentro de
la red privada. Los checks deben probar aislamiento de tenant y el recorrido
de costes, ingesta/retrieval y respuesta del asistente. Una receta versionada
identifica exactamente el código y su evidencia; no debe declarar aceptación
AWS a partir de mocks ni de pruebas locales.

## Orden de ejecución y verificación

1. PostgreSQL: permitir el DSN operativo, usar tipos SQL comunes, ejecutar todas
   las migraciones backend/processor/vector en PostgreSQL real; comprobar
   reejecución, persistencia y consultas representativas. Conservar regresiones
   Cockroach y no modificar datos de ningún despliegue existente.
2. Cognito: modo explícito, validación RS256/JWKS/issuer/client/token_use/tiempos,
   vinculación por sub a usuario local y autorización de tenant desde DB; login
   local desactivado en ese modo. Frontend authorization-code/PKCE con state,
   callback, expiración y logout. Pruebas negativas de identidad y callback.
3. Bedrock: clientes con credenciales del rol, región/modelos explícitos,
   timeouts/límites, Converse y embeddings Titan V2 con dimensión coherente.
   Integrar ambos servicios y rutas del chat, sin fallback silencioso a mock.
   Pruebas de protocolo, fallos y recuperación/reindexación.
4. Arranque: tareas ECS privadas puntuales, rol de bootstrap separado y acotado,
   creación de usuarios DB/MQ, secretos y migraciones ordenadas; fixtures de coste,
   corpus y usuario Cognito. Esperar éxito de cada tarea; idempotencia y errores
   seguros. Extender outputs/permisos Terraform solo donde sea necesario.
5. Comprobación: salud y estabilidad, autenticación real, acceso permitido y
   denegado por tenant, costes esperados, ingesta y retrieval, respuesta Bedrock
   estructurada. Guardar evidencia sin secretos y fallar si falta un paso.
6. Integración: receta real, configuración pública y variables frontend desde
   outputs, pruebas offline y ensayo local completo, CI del SHA final, revisión
   técnica independiente. Mantener explícitos prerrequisitos externos pendientes.

## Evidencia y límites

Cada tarea comienza por una prueba que falle antes de implementar. PostgreSQL
se prueba con un contenedor desechable propio; nunca con los volúmenes de la
demo existente. Identidad e inferencia se prueban localmente con firmas y
respuestas de protocolo controladas. La comprobación real de AWS queda para el
ensayo autorizado: los tests locales no demuestran acceso a modelos, cuotas,
TLS/DNS o permisos efectivos.

Progreso reproducible en `.work/aws-application/progress.md` (ignorado);
resumen duradero en `docs/continuidad/cloud-aws.md` y evidencia JUP-131.

## Estado de implementación — 22/10/2026

Tareas1–5 implementadas y comprobadas offline; tarea6 con receta real, integración
de develop/v4, tres imágenes y revisión técnica independiente conformes. La CI
del candidato publicado se consulta en PR146; su resultado no debe extrapolarse
a una ejecución AWS. El paquete del ensayo conserva placeholders de cuenta y
crédito0 hasta verificar las entradas externas. No se ejecutó despliegue.
