# ADR-0027: ciclo AWS desechable y control separado para la defensa

Estado: Proposed. Fecha:21/10/2026. JUP-131 — https://trello.com/c/NtiH8R4Z.

El usuario autoriza implementar el [plan CI/CD](../planning/aws-cicd-defensa.md)
sin desplegar, con dos ensayos crear/destruir y unos diez minutos de presentación
el29/10/2026, saldo comunicado60€. La arquitectura AWS de JUP-060 se conserva.

Se separa control/bootstrap en París de la aplicación en España y el edge en
us-east-1. CodeConnections GitHub no está disponible en España según la fuente
enlazada en el plan. CodePipeline/CodeBuild llaman a Terraform desde París.
No crear otro stack de aplicación con CloudFormation ni cambiar AZ/servicios.

State remoto versionado y bloqueo S3; lease persistente por dominio; runner
compartido concurrente1. Dos pipelines manuales, SHA/config/plan vinculados y
aprobación manual. El down opera únicamente sobre IDs del state del ciclo.
Protecciones siguen activas por defecto; desbloqueo explícito de datos sintéticos
para el ensayo. Caducidad solicita limpieza desde el mismo código sin depender
de que el pipeline de creación termine correctamente.

El bootstrap sobrevive al down y requiere retirada independiente. Artefactos y
state no se publican; KMS/Secrets pueden quedar en borrado diferido. No se promete
coste cero con destroy ni disponibilidad por usar servicios gestionados.

Compatibilidad SQL/auth/IA y fixtures son requisito de release, no una consecuencia
del apply. Su aceptación se liga a bytes de aplicación y evidencia versionada.
Sin ella, se bloquea antes de crear recursos demo. Alternativas EC2 y GitHub OIDC
no se implementan: no son el alcance aprobado. Estado Proposed conserva la revisión
humana pendiente; autorización de implementación no acredita revisión oficial.
