## Context

JUP-052 entrega un entorno privado desechable. DockerServer tiene Python 3.12,
Docker 29.6.2 y Compose 5.3.1; SSH accesible por LAN. El repositorio es público.
Roles Trello al comenzar: Victor líder, Alejandro pairing, Lucia revisión,
Paris validación. No se presume participación humana ni aprobación técnica.

## Decisions

ADR: [ADR-0017](../../../docs/adr/ADR-0017-private-dockerserver-cd.md), Proposed.
CD llama al workflow CI del mismo SHA mediante workflow_call. El agente acepta
solo el último run exitoso de cd.yml en develop, del repositorio canónico y con
SHA igual al head actual; verifica otra vez el head tras el fetch/preparación.
El agente instalado permanece fijado a una revisión revisada.

Se renderiza Compose sin imprimir secretos, se fuerzan todos los puertos a
loopback, se preservan los dólares escapados por el renderer Compose y se fijan
rutas absolutas a la release. Slot alternante y proyecto por SHA separan datos
de validación. El candidato pasa build, up --wait y cinco escenarios del smoke
antes de cambiar state.json. Fallo detiene candidato y conserva la versión
actual. Rollback prueba la anterior con --no-build y pausa el agente.

## Risks / Trade-offs

No cero downtime ni endpoint estable; túneles por slot. No rollback de datos.
El agente tiene permisos Docker: solo código integrado de confianza. Sin
credenciales GitHub, depende del acceso público y sus límites; errores fallan
cerrado. Releases/volúmenes consumen disco y requieren limpieza explícita.

## Migration Plan

Ensayo aislado desde esta rama; publicar PR para los roles asignados. Integrar
tras revisión y validación. Instalar agente/unidades y verificar lingering.
Primera ejecución CD real solo después de integración en develop. Conservar
evidencia del run id y del state.json; no declarar Hecho antes de ese contraste.
