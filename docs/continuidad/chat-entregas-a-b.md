# División de JUP-035 en A y B

Actualizado: 2026-10-14. Origen: chat 01a1270c-e332-7462-9c90-706d49ade92c.
El usuario confirma aprobación del equipo y autoriza actualizar Trello, publicar
A y cerrar #120/#121 sin integrar. No autoriza despliegue ni mensajes Discord.

El 14/10 Paris limita la adaptacion local a tres mejoras en
`codex/JUP-122-checkpoint-improvements`, base PR130 `318a56f`: tokenizer generado
con revision/SHA256 fijos, `.secrets` excluido de releases/contextos y fixture SQL
portable que espera limpieza real. Las pruebas focales y las imagenes offline
pasan; la tanda amplia backend conserva seis fallos por tokens de fixture JUP-047
caducados durante la espera. No se modifica esa fixture fuera de alcance.
Sin commit/push, activacion ni aceptacion semantica. Ver
[entrega local y limites](../evidence/JUP-122-checkpoint-improvements-20261014.md).

- Padre: [JUP-035](https://trello.com/c/BJfABykd), continúa pendiente.
- A: [JUP-122](https://trello.com/c/gFYKmcLT), ingeniería/base del chat.
- B: [JUP-123](https://trello.com/c/TqtcumIN), calidad semántica/evaluación.

A parte de develop c30a7d0, base chat Paris f63c150 y bloques de ingeniería
extraídos de PR121. Rama feat/JUP-122-chat-engineering. Chat apagado por defecto.
Se conserva required-documentation-v1; el rediseño server-documentation-v4,
expresiones y reglas de PR121 permanece en B. Esto no revierte v4 en B ni
justifica rehacer su eliminación de tools. Ver el [diseño](../../openspec/changes/jup-122-chat-engineering/design.md).

Las PR antiguas siguen siendo evidencia de autoría y findings. Sus requests
changes no se transforman en aprobaciones al cerrar: A requiere reviews propias.
No se borra ninguna rama. El candidato local de B 50e169fa se conserva intacto.

PR-A publicada: [#130](https://github.com/EconomiconFinOps/tfm-economicon/pull/130).
Primer candidato 2b55e1e2: SQL nativo54PASS y frontendCI favorable; resto de CI
en curso. Corrección adicional de aislamiento de flag en tests:27PASS.
Trello actualizado mediante la integración DockerServer; scripts y recibos en
materiales/07-evidencias/JUP-035-split, fuera del repo. Pruebas y publicación en
curso; no presentar los resultados de la extracción como CI del commit final.
Sin nuevas inferencias ni consumo. Último gasto histórico 0,957927619 USD / 2 USD.

Pendientes: CI final de A y UI, reviews de A; después colector, criterios
acordados y campañas N=3/N=5 de B. No activar ni integrar automáticamente.
