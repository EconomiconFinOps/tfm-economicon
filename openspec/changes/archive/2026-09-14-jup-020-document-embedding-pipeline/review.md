# JUP-020: cierre del contrato de ingesta

## Revision e integracion verificadas

[Lucia Mateo aprobo PR #34](https://github.com/EconomiconFinOps/tfm-economicon/pull/34#pullrequestreview-5191430544)
el 2026-09-13 a las 17:01:45 UTC, sobre
`b97753917c93002a666502c294f8f7149489f176`. Registro una comprobacion
independiente de 263 pruebas del processor y 115 del backend, incluidos los
seis casos nuevos de regresion del contrato. El arreglo no se modifico
respecto a la entrega validada: la rama habia incorporado `develop`.

La misma revisora fusiono la PR a `develop` el 2026-09-13 a las 17:04:18 UTC
(19:04, hora de Paris), como
[`cfc6668bceb60c38045f72976b9de8e8b8337555`](https://github.com/EconomiconFinOps/tfm-economicon/commit/cfc6668bceb60c38045f72976b9de8e8b8337555).
[CI del head revisado: 7/7 correcto](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/34770303447).

## Validacion de Paris y procedencia de la confirmacion

El 2026-09-14 el usuario confirma la validacion funcional de **Paris Arcos
Martin** y solicita actualizar Trello/OpenSpec y cerrar JUP-020. Esta
confirmacion completa la tarea 2.5 junto con la revision ya registrada.
La fecha corresponde a la confirmacion recibida; no se inventa una fecha
de ejecucion ni se atribuyen a Paris los logs automatizados del 2026-09-10.

La evidencia funcional de la entrega se conserva en
[JUP-020-validation.md](../../../../docs/evidence/JUP-020-validation.md):
HTTP normal, mensaje RabbitMQ original recuperado sin alteraciones, dos
POST nuevos para tenants distintos, tres documentos, 57 fragmentos exactos,
57 embeddings de dimension 8, metadata en payload/resultado, correlacion
request_id y cola vacia. El entorno desechable se retiro tras conservar
evidencia. Las 34 pruebas especificas CockroachDB omitidas no se declaran
ejecutadas por esta confirmacion.

## Alcance del cierre

Se cierra la entrega de correccion del contrato backend/processor de PR #34
y RF-053-004, junto con el duplicado RF-045-001 identificado por Lucia en
[su comentario](https://github.com/EconomiconFinOps/tfm-economicon/pull/34#issuecomment-5654725777).
Se archiva este cambio y se promueve unicamente `document-ingestion-handoff`.

Quedan como trabajo posterior no implementado: proveedor real de embeddings,
carga completa/versionada del corpus, metadatos por fragmento e idempotencia/
reprocesado. Se conservan expresamente en la tarjeta cerrada de Trello;
no se convierten en capacidades completadas al cerrar esta entrega.
Los proveedores probados son mock. La carrera de arranque JUP-096 sigue
separada y no se da por resuelta.
