# Diseño JUP-131

JUP: JUP-131
Trello: https://trello.com/c/NtiH8R4Z

Aplicar [plan](../../../docs/planning/aws-cicd-defensa.md) y
[ADR-0026](../../../docs/adr/ADR-0026-aws-defense-lifecycle.md).
Bootstrap separado; dos pipelines manuales sin trigger de cambios, un runner
serializado y lease de dominio sin TTL. Terraform mantiene la arquitectura de
JUP-060 y exige una boundary de roles ECS al ejecutar por CI/CD.

Config fuera de Git direccionada por SHA256, source COMMIT_ID y CI SUCCESS exacta.
Planes binarios y binding privados. Teardown acepta únicamente IDs/addresses del
state propio y detiene escritores antes del vaciado. Recuperación usa el mismo
state; un plan down invalida el up anterior. Caducidad funciona con sourcebundle
del mismo SHA y lockfiles. Secretos en entorno/Secrets Manager, fuera de logs.

La preparación local es libre de APIs AWS y produce readiness negativo cuando
faltan cuenta/DNS/motores/CI/aceptación. El runtime real no se habilita sin receta
y evidencias de adaptación asociadas al hash de aplicación. El runbook distingue
pruebas offline, campos pendientes y futuras acciones con coste.
