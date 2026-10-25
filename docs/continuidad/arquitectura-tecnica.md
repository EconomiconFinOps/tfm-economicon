# Arquitectura técnica — JUP-060

## Actualización JUP-138 — 22/10/2026

[Tarjeta](https://trello.com/c/WvzuP74W/130-jup-138). `docs/architecture.md`
pasa del corte `a0e9a56` (11/10) a `develop 03e97ce6` (22/10). Se incorporan
MinIO y la subida de archivos (JUP-124), el chunking y la recuperación
contextual e híbrida (JUP-125, JUP-127), el chat generativo bajo
`CHAT_ENABLED=false` y su red privada (JUP-122, JUP-123, JUP-132), la landing
pública (JUP-089) y, en versión mínima, el código y el pipeline AWS de JUP-131
sin despliegue. Los recuentos de Compose salen de `docker compose config`:
10 servicios de larga ejecución, 2 de un solo uso y 6 volúmenes por defecto.

No cambia código, pruebas, ADR ni sus estados. El inventario de fuentes, la tabla
de desfases corregidos y los hallazgos fuera de alcance están en el
[review del change archivado](../../openspec/changes/archive/2026-10-22-jup-138-actualizar-architecture/review.md).
La vista sigue sin acreditar calidad generativa extremo a extremo, un despliegue
vivo ni la aceptación del ensayo AWS. Desde aquí, quien integre un servicio de
Compose, una ruta o un flag de chat o RAG debería actualizar el documento en
el mismo PR: no hay ninguna comprobación automática que avise del desfase.

Verificado 11/10/2026. Origen «Implementa JUP-060», chat
`01a12ad8-69f9-75b1-9003-94d5e33386be`. [Tarjeta](https://trello.com/c/alMIpBOQ),
[PR92](https://github.com/EconomiconFinOps/tfm-economicon/pull/92).

## Alcance y decisiones

Copia `tfm-economicon-jup060`, rama local `docs/JUP-060-delivery`; entrega sobre
la rama existente de PR92. Checkout compartido preservado. Base reconciliada
`develop a0e9a56`, después de la contribución inicial `d523bc3` sobre `c2995a1`.
PR92 se encontró cerrada sin merge y sin feedback pendiente el 11/10.
[Arquitectura](../architecture.md) distingue chat documental determinista,
ownership SQL, job documental, CLI Azure, cobertura tags y objetivo generativo.
CD privado052 integrado, gateway078 con evidencia propia y métricas068 offline;
no se confunden elegibilidad, despliegue vivo, calidad IA o beneficio realizado.

[AWS](../architecture-aws.md) y [Terraform](../../infra/aws-reference/README.md)
son referencia documental. No apply, cloud, migración ni gasto. La propuesta
EC209/10 sigue como antecedente superado; [continuidad AWS](cloud-aws.md).

## Memoria y atribución

Trello oficial confirma apartado d incorporado y exportación publicada el10/10.
Se leyó solo d por rangos el11/10, sin otros apartados. Conserva corte histórico
c2995a1/d523bc3; la referencia del repo se actualiza a a0e9a56. PDF/Markdown/manifiesto
Drive y hashes en [evidencia](../evidence/JUP-060-validation.md). No nueva exportación
ni nueva comprobación de paginación:11 páginas y figuras6–9 son evidencia10/10.

Usuario autoriza expresamente sustituir roles humanos por subagentes en este
encargo. Ejecución bajo Iber1to; pairing `/root/pairing`, revisión `/root/revision`,
validación `/root/validacion`, revisión de memoria `/root/memoria`. Dictámenes
favorables con límites; P2 de orden persistencia ownership corregido/revalidado.
No se atribuyen aportaciones a Victor/Alejandro/Lucia/Paris por su asignación
anterior; no se inventan aprobaciones GitHub ni se alteran protecciones.
La excepción se limita a JUP060 y no acepta el MVP completo.

## Evidencia y siguiente lectura

95 pruebas gobernanza,60 OpenSpec antes/después archivo, Terraform fmt/validate,
6 mock tests y8 rutas correctos. Enlaces focales74 correctos; revisión amplia
107/109,2 enlaces heredados ajenos rotos en índice de develop. Dos diagramas
modificados renderizados/inspeccionados. Sin nueva prueba runtime ni AWS.
[Change archivado](../../openspec/changes/archive/2026-10-11-jup-060-technical-architecture-deliverable/proposal.md).

Consultar PR92/Trello para CI del SHA final, dictámenes publicados y resultado
de integración. La evidencia conserva fechas/limitaciones y la fuente canónica
sigue fuera de Git. No mensajes Discord. Las correcciones futuras parten del
corte integrado y mantienen el alcance exclusivamente documental de AWS.
