# Arquitectura técnica — JUP-060

Verificado 10/10/2026. Origen: encargo «Implementa JUP-060 — Documentar arquitectura
técnica», chat 01a124a3-8135-7f53-8cf8-7d268a4caedd; delegado desde
01a1248a-4e9e-7963-a891-5d8cb49345a6. [Tarjeta](https://trello.com/c/alMIpBOQ).

## Alcance y conclusiones

Copia aislada tfm-economicon-jup060, rama docs/JUP-060-technical-architecture,
base c2995a118d419dfe725247bac9c6f219a3f0ea77. Checkout compartido preservado.
[Arquitectura](../architecture.md) sustituye descripciones obsoletas sin cambiar
runtime: billing lee costes; aislamiento y citas integrados; chat sigue plantilla
síncrona, no llama al processor. Job documental y CLI Azure son flujos distintos.
Tools FinOps son contrato; gateway/AgentRuntime no acreditan vertical generativo.

Compose: 9 servicios/5 volúmenes; ai 11/6. Apps publican sin loopback por defecto;
infra publica en loopback. Insecure local/Vite preview no son base productiva.
JUP052 no integrado en esta base; no inventario vivo ni despliegue nuevo.
[Propuesta AWS](../planning/aws-deployment-proposal.md) del 09/10 conservada como
antecedente con aviso de alcance operativo superado. El hash original
`5f5ade08941dab08edb7cd7704dc1691db364ae1920918400a6a0603c9d71855` es histórico,
anterior al aviso. El usuario confirmó alcance documental e incorporación de
[esquema AWS](../architecture-aws.md) y [Terraform](../../infra/aws-reference/README.md)
a esta PR. [Continuidad AWS](cloud-aws.md) distingue ambos cortes. Ningún
provisioning, gasto o llamada pagada; no se ratifica una migración de arquitectura.

## Gobernanza y evidencia

Trello oficial leído por DockerServer:/home/danteadmin/economicon-collaboration:
misma descripción/roles, P0, Backlog, actividad 09/10 18:46:52Z.
Victor liderazgo, Alejandro pairing, Lucia revisión, Paris validación. Identidad
GitHub Iber1to: aportación asistida propia, sin atribuir trabajo al resto.
Guion_PJ.md leído por su enlace de coordinación y contrastado en las tres partes;
no se abrió la memoria ni apartados ajenos. Fuente canónica y reglas:
[docs/memoria/README.md](../memoria/README.md).
[Evidencia por criterio](../evidence/JUP-060-validation.md).
[Change activo](../../openspec/changes/jup-060-technical-architecture-deliverable/proposal.md).

## Próximos pasos

[PR #92 draft](https://github.com/EconomiconFinOps/tfm-economicon/pull/92) publicada
contra develop. OpenSpec 56/56, gobernanza 89/89, higiene 6/6 y checker correcto;
72 enlaces sin error, ocho Mermaid renderizados con Chromium de pruebas.
CI inicial e8f951e: siete checks técnicos correctos; JUP reviews falla por los dos
dictámenes humanos ausentes. Ver informe para intentos fallidos de entorno y límites.
Propuesta d revisable fuera de Git en materiales/07-evidencias/JUP-060-arquitectura-2026-10-10/.
Nota Trello publicada y releída por integración oficial el 10/10 a las 07:48Z:
6ac9edb77c321c49fcc1f612, enlaza PR/evidencia y pendientes. Sin mover tarjeta.
Victor revisa e incorpora el apartado d en la fuente canónica con autorización
expresa y revisión humana; exportar versión/hash. Lucia/Paris emiten dictámenes
independientes. Solo después archivar/promover change, integrar PR y decidir
estado Trello conforme a CONTRIBUTING. No atribuir aceptación, pairing, merge o
cierre por esta documentación; no mensajes Discord.
