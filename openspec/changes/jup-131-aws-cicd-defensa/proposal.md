# CI/CD AWS para ensayos y defensa

JUP: JUP-131
Trello: https://trello.com/c/NtiH8R4Z

## Why

La arquitectura y Terraform JUP-060 carecen de orquestación de crear/destruir.
El usuario solicita implementar el plan, preparar dos ensayos y defensa29Oct,
sin desplegar todavía en AWS. Infra existente y crédito comunicado60€.

## What Changes

- Bootstrap de control separado en París y pipelines manuales up/down.
- Runner con SHA/config/plan, bloqueo, caducidad y recuperación de apply parcial.
- Perfil de retirada explícito que conserva topología y defaults protegidos.
- CI offline, paquete local del primer ensayo y runbook de operaciones.

## Capabilities

### New Capabilities

- `aws-defense-lifecycle`: creación/retirada controlada de un ciclo desechable.

### Modified Capabilities

Ninguna capacidad de producto cambia. Adaptaciones SQL/Cognito/IA y aceptación
cloud siguen como prerrequisitos; no se simulan ni se despliega en esta entrega.

## Impact

infra/aws-bootstrap, infra/aws-reference, infra/aws-cicd, tools/aws_demo y CI.
No se modifica el CD DockerServer ni la aplicación. Roles humanos pendientes
de asignación; ejecución asistida bajo Alejandro, sin atribuir pairing o reviews.
