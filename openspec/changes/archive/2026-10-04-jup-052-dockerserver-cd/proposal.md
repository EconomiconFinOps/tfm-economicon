JUP: JUP-052
Trello: https://trello.com/c/q3TahHoj

## Why

JUP-049/050 permiten construir el stack, pero falta desplegar automáticamente
el entorno privado de desarrollo/validación con evidencia de runtime.

## What Changes

- CD para pushes integrados a develop, reutilizando todos los checks técnicos CI.
- Agente Linux de lectura saliente, lock, selección estricta del SHA elegible.
- Releases aisladas con puertos privados, secretos locales, smoke y rollback.
- Guía operativa y evidencia separando elegibilidad GitHub y éxito funcional.

## Capabilities

### New Capabilities
- `private-continuous-deployment`: promoción comprobada hacia DockerServer.

### Modified Capabilities
None.

## Impact

Workflows CI/CD, herramientas Python stdlib y systemd de usuario; reutiliza
Docker Compose y contratos JUP-050. No modifica servicios de negocio ni otros
stacks del servidor. Producción, dominio público, registry y rollback de datos
quedan fuera del alcance. JUP-051 permanece una PR independiente; únicamente
se añade workflow_call al CI actual sin trasladar sus cambios pendientes.
