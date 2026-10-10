# Memoria: integración con herramientas DevOps — JUP-111

Verificado el 10/10/2026. Origen: «Implementa JUP-111 — Redactar el apartado de integración con herramientas DevOps de la memoria». Encargo recibido del chat `01a1248a-4e9e-7963-a891-5d8cb49345a6`; identificador del chat de implementación no consultado.

## Alcance y entrega

[Tarjeta](https://trello.com/c/mnqNDpC0), P0, apartado f únicamente. Alejandro lidera, Paris pairing, Lucía revisión y Víctor validación según snapshot oficial del 10/10; asignación no equivale a participación realizada. Clon aislado `tfm-economicon-jup111`, rama `docs/JUP-111-devops-memory`, base `c2995a118d419dfe725247bac9c6f219a3f0ea77` de origin/develop. No se modificó el checkout compartido.

- [Contrato activo](../../openspec/changes/jup-111-devops-memory/proposal.md) y [evidencia por criterio](../evidence/JUP-111-devops-memory.md).
- [PR #87](https://github.com/EconomiconFinOps/tfm-economicon/pull/87) draft contra develop, entrega inicial `1eaa36f`. CI [38034787702](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38034787702) SUCCESS sobre ese commit; `PR reviews` pendiente/fallido por dictámenes aún ausentes. No equivale a aceptación editorial.
- Propuesta fuera de Git: `materiales/06-entregables/JUP-111-propuesta-2026-10-10/apartado-f.md`, relativa al workspace que contiene los clones. Cobertura y procedimiento en `cobertura-y-entrega.md`; identidad en `manifest-sha256.json` de esa carpeta. Es propuesta, no exportación de la memoria.
- Fuentes/recibos y resultados propios: `materiales/07-evidencias/JUP-111-devops-2026-10-10/`, fuera de Git.

La memoria editable sigue en el Google Doc localizado mediante la tarjeta PROYECTO — Enlaces y coordinación. No se leyó ni editó la memoria completa ni apartados ajenos. Se leyó íntegro el guion oficial enlazado, sin copiarlo a Git; su fidelidad al PDF original no está verificada.

## Conclusiones y decisiones

- CI, Docker, logging y métricas se contrastaron con el código de la base y evidencias fechadas. Los runs CI del 05/10 siguen siendo históricos; se releyeron sus jobs, no se volvieron a ejecutar.
- PR #73 de CD permanece abierta en `a75472d`, sin workflow CD en la base. La validación de Paris del 09/10 prueba build/arranque/smoke local mock 5/5, `run_id=null`. No demuestra primera promoción automática integrada, operación del timer ni reboot. Se conserva el pendiente explícito.
- El texto distingue la prueba estática de topología en CI del ensayo Docker real, observabilidad técnica de calidad de respuestas y estado Proposed de los ADR de implementación integrada.
- Por la [gobernanza de JUP-062](../memoria/README.md), «Ningún texto se publica en el documento sin que una persona lo revise». Se entrega primero contenido revisable; el encargo no acredita que alguien haya revisado este texto nuevo. La revisión automatizada no sustituye esa puerta humana.

## Siguientes pasos concretos

1. Alejandro revisa la propuesta y facilita el fragmento f y la guía de estilo para reconciliar texto existente sin leer otros apartados. No se sabe si f ya contiene aportaciones.
2. Incorporar sólo f tras revisión y autorización de escritura; registrar pairing real de Paris, revisión de Lucía y validación de Víctor. No inventar sesiones, coautorías ni aceptación.
3. Exportar versión revisada PDF/Markdown con las autorizaciones de lectura correspondientes, registrar fecha/hash en documento/Trello, comprobar paginación conjunta de 20 páginas y cerrar el change por PR documental.
4. Actualizar CD sólo con evidencia nueva de JUP-052; no desplegar para completar esta redacción. No se enviaron mensajes Discord.

El change permanece activo por publicación y aceptación pendientes; no declarar JUP-111 Hecho por entregar esta propuesta.

Controles propios del 10/10: gobernanza 95/95, OpenSpec estricto 56/56,
trazabilidad e higiene correctas, 40 enlaces y 16 fuentes fijadas comprobados;
dos hashes de propuesta y dos controles negativos de integridad correctos.
Primer intento Node/Git bloqueado por EPERM del sandbox, reintento autorizado
correcto. Detalle y comandos en la evidencia; no nuevas pruebas de producto.

Trello: nota `6ac9eb23166e2ecab90fd85d` del 10/10 07:37:07Z y paso a
`30 — En curso` por la integración DockerServer; roles, prioridad, criterios y
fechas conservados. Se enlazan PR y propuesta/hash sin cerrar criterios de
incorporación o revisión. Recibo externo `trello-readback.json`.
