# JUP-131 — transición a Irlanda

Autorización del usuario22/10/2026: solicitar Fargate6vCPU Irlanda y CodeBuild
Medium1 París, adaptar configuración a Irlanda, SIN desplegar. Implementación
sobre rama aislada feat/JUP-131-aws-cicd-defensa; base41cace0d. Conservar cambios
locales de continuidad y requisitos humanos de CONTRIBUTING.

## Tareas

1. Comprobar historial y solicitar únicamente las dos cuotas autorizadas. Guardar
   IDs/estado y comprobar de nuevo al final. Solicitud no equivale a aprobación.
2. RED: fixtures AWS positivas Irlanda, rechazos cruzados España, schema/config,
   CA y cuatro destinos Bedrock. GREEN: apps nativas, TLS RDS público de Irlanda,
   S3/MQ/Cognito/DB privados y fingerprints; conservar modos de desarrollo.
3. RED/GREEN: controlador/runner/bootstrap/checker y Terraform IAM/profile,
   entradas de ensayo y release Irlanda. Mantener control París y edge Virginia.
   Destinos Nova son cuatro desde Irlanda, sin España. No flexibilizar guardas
   ni cambiar la arquitectura, los límites de tamaño o el ciclo de retirada.
4. Hashes y evidencias nuevos, pruebas focales Windows, Terraform mocks, imágenes
   Linux afectadas y CI del SHA exacto; revisión técnica independiente del delta.
   Regenerar paquete bloqueado: cuenta conocida, DNS/roles/conexión/secretos,
   presupuesto/ventana/reviews/aceptación cloud siguen pendientes. Sin apply.

## Interfaces y verificación

La región y ARNs deben coincidir en config, apps, tareas privadas, IAM, preflight,
evidencias y receta. Fuente de CA pública oficial con SHA256 de bytes fijado.
El fingerprint de embeddings incluye región: no reutilizar corpus español como
si fuese irlandés. Perfil Nova Micro verificado por metadatos en la cuenta, no
inferencia. Logs .work/aws-region-irlanda/; continuidad docs/continuidad/cloud-aws.md.
Expected: tests de admisión Irlanda fallan antes y pasan después; suite AWS
completa sin llamadas a cuenta, Terraform validate/test mock pasan; CI técnica
verde para bytes finales. Nunca presentar mocks como aceptación de AWS.
