JUP: JUP-060
Trello: https://trello.com/c/alMIpBOQ

## Why

La arquitectura conservaba afirmaciones históricas de billing, aislamiento y
citas; faltaba una vista consolidada que separase código integrado, contratos
pendientes, evidencia de despliegue y propuesta cloud.

## What Changes

- Actualizar docs/architecture.md con componentes, datos, secuencias y despliegue.
- Separar chat síncrono, job documental, CLI Azure y objetivo tools/RAG/LLM.
- Enlazar auth/tenant, secretos, observabilidad, CI, ADR y evidencia fechada.
- Incorporar el esquema AWS del 10/10 y la plantilla Terraform validada localmente
  en docs/architecture-aws.md e infra/aws-reference; marcar EC2 del 09/10 como
  antecedente, con su interpretación operativa superada.
- Registrar verificaciones por criterio y cobertura del guion oficial; mantener
  la memoria compartida como fuente canónica conforme a docs/memoria/README.md.

## Capabilities

### New Capabilities

- technical-architecture-deliverable: vista consolidada, trazable y honesta del sistema.

### Modified Capabilities

- None.

## Impact

Documentación y código Terraform de referencia sin ejecución; sin cambios de
runtime, datos o infraestructura desplegada, presupuestos, prioridades, fechas
o roles. La plantilla fija sus herramientas de validación de forma aislada;
no modifica dependencias de las aplicaciones. No cierra el vertical generativo.
La memoria no se copia al repositorio ni se publica sin revisión humana.

## Participación registrada

Trello contrastado 10/10: Victor Mendez liderazgo; Alejandro Aguado
pairing/coautoría; Lucia Mateo revisión; Paris Arcos Martin validación.
La aportación asistida no acredita pairing entre humanos ni dictámenes.
