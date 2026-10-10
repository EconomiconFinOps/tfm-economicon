# Showback por unidad — JUP-027

Verificación: 2026-10-10. Encargo «Implementa JUP-027 — Implementar showback por unidad organizativa»; chat `01a124a4-4e5d-7772-95bd-4eae859a903c`. Tarjeta: https://trello.com/c/W6gAiOWt.

## Alcance y decisiones

Copia aislada `tfm-economicon-jup027`, rama `feat/JUP-027-showback`, base `origin/develop` c2995a1. Checkout compartido y JUP-028 sin editar. Descripción completa y roles contrastados mediante DockerServer:/home/danteadmin/economicon-collaboration el 10/10: Paris liderazgo, Victor pairing, Alejandro revisión, Lucia validación. Son asignaciones, no participación acreditada.

Se añade GET /billing/showback con owner/project/application/cost_center y período UTC. Reparto directo del 100%, importes exactos por moneda, sin asignar con motivo y reconciliación; reglas y limitaciones en [contrato API](../api/showback.md). Se conservan controles de tenant, run completed, suscripción y solapamiento; no se cambia ingesta, resumen billing, UI ni JUP-028.

Contrato de JUP-015 consultado en su copia activa, solo lectura: sintaxis economicon-minimum-v1 compatible. Adaptador provisional explícito; catálogo/mapeo organizativo no integrado ni certificado. No se bloquea el reparto directo por ausencia de catálogo; la respuesta advierte ese límite mediante campos de contrato.

## Evidencia y próximos pasos

Consultar [evidencia por criterio](../evidence/JUP-027-showback.md) y [OpenSpec](../../openspec/changes/jup-027-organizational-showback/proposal.md). 80 pruebas JUP-027 aprobadas (48 servicio, 23 HTTP y 9 SQL real en CockroachDB v24.1.11 efímero vía túnel a DockerServer), 82 controles de gobernanza/CI y OpenSpec 56/56. Backend compila. Sin datos de producción ni catálogo organizativo integrado.

Pendiente enlazar PR draft y recibo Trello. La contribución usa la cuenta Iber1to/Alejandro para Paris: Alejandro figura como revisor asignado, pero no puede revisar independientemente su propia contribución. El equipo debe regularizar participación y revisión antes de promover el draft, sin reasignación automática. Pairing real, Revision JUP-027, Validacion JUP-027 y merge pendientes. No se modifica prioridad, fecha ni lista por inferencia y no se envía Discord.
