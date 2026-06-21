# Configuración del harness SDD

Este directorio contiene los contratos y la configuración versionada del harness. No contiene estado efímero de sesiones ni memoria de agentes.

## Contenido

- `config.yaml`: rutas, versiones y convenciones globales.
- `policies/workflow.yaml`: máquina de estados aprobada en la Fase 0.
- `policies/workflow.approval.yaml`: aprobación y hashes del contrato.
- `schemas/manifest.schema.json`: contrato estructural `2.0.0` de cada `manifest.yaml`.
- `schemas/command-input.schema.json` y `schemas/command-output.schema.json`: contratos Draft 2020-12 del CLI público.
- `schemas/catalog.yaml`: catálogo versionado de contratos de manifiesto, artefactos y skills.
- `schemas/artifacts/`: contratos de front matter y secciones Markdown para los ocho tipos de artefacto.
- `schemas/skills/`: contratos comunes y específicos de entrada y salida de las siete skills previstas.
- `templates/`: plantillas versionadas para los ocho tipos de artefacto.
- `fixtures/contracts/`: matriz y payloads de compatibilidad válidos e inválidos.
- `commands/orchestrator.yaml`: contrato declarativo del CLI y sus exit codes.

## Validación

```powershell
pnpm sdd:validate-manifest -- SPEC/examples/HU-000-fixture/manifest.yaml
```

El comando valida primero la aprobación de la Fase 0 y después el schema y las reglas semánticas del manifiesto.

## Orquestador

```powershell
pnpm sdd -- init --title "Nueva historia" --change-type feature --component backend --affected-data jobs --affected-flow ingestion --write-path "apps/backend/**"
pnpm sdd -- validate --story HU-001
pnpm sdd -- status --story HU-001
pnpm sdd -- approve --story HU-001 --artifact user-story --decision APPROVED
pnpm sdd -- evidence record --story HU-001 --condition no_open_functional_questions --evidence SPEC/HU-001/prd.md
pnpm sdd -- next --story HU-001
pnpm sdd -- run --story HU-001 --task TASK-001 --to RUNNING --executor-type agent --executor-id implementation-agent
pnpm sdd -- contract validate --schema artifact/prd@1.0.0 --input SPEC/HU-001/prd.yaml
pnpm sdd -- recover --story HU-001
```

Los artefactos Markdown usan front matter YAML normativo y cuerpo legible. Cada entrada del manifest declara su `schema_version`; las versiones desconocidas se rechazan. Los contratos de skills son declarativos y no ejecutan skills ni agentes en esta fase.

Los comandos read-only nunca recuperan ni reconcilian estado. El primer comando mutante posterior aplica cualquier transacción pendiente o invalidación y detiene la acción solicitada para que el estado reconciliado se revise explícitamente.

El harness detecta, bloquea e invalida cambios fuera del alcance declarado. La prevención física de escritura se aplicará mediante permisos de agentes en la Fase 5.
