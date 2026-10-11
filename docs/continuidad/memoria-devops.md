# Memoria: integración con herramientas DevOps — JUP-111

Verificado: 11/10/2026. Origen: «Implementa JUP-111 — Memoria de DevOps», chat
`01a12af2-8d4e-7252-a21a-55a3ddd92364`.

## Alcance y decisión vigente

Apartado f de la memoria, [Trello](https://trello.com/c/mnqNDpC0), P0.
El usuario autoriza sustituir los roles humanos por subagentes y registrar la
excepción como necesaria por estar fuera de plazo. El motivo se atribuye a su
instrucción; Trello no tiene due y el calendario institucional sigue sin confirmar.
[Excepción y atribución](../evidence/JUP-111-excepcion-plazo.md).

La excepción sustituye la puerta humana de JUP-111 por revisión independiente de
subagente; no cambia las reglas generales ni extiende el acceso a otros apartados.
Pairing `/root/pairing` realizado; revisión independiente favorable de propuesta,
validación documental 83/83 y OpenSpec61/61 correctos.
No atribuir esos trabajos a Paris, Lucía o Víctor.

## Entrega y evidencia

- Clon `tfm-economicon-jup111`, rama `docs/JUP-111-devops-memory`.
  Base reconciliada `c3eb665aff7b5cfa53a5ad6a3795bd8c5e6c27e3`;
  índice fusionado conservando filas de ambos lados.
- [PR #87](https://github.com/EconomiconFinOps/tfm-economicon/pull/87): cerrada
  sin merge el 10/10; reabierta draft el 11/10 por este encargo.
- [Evidencia vigente e histórica](../evidence/JUP-111-devops-memory.md) y
  [contrato activo](../../openspec/changes/jup-111-devops-memory/proposal.md).
- Propuesta nueva fuera de Git: `materiales/06-entregables/JUP-111-propuesta-2026-10-11/`
  relativa al workspace padre; apartado-f.md, cobertura-y-entrega.md y manifiesto.
  La propuesta del 10/10 se conserva inmutable y no es una exportación canónica.
- Recibos nuevos en `materiales/07-evidencias/JUP-111-devops-2026-10-11/`.
  Fuentes iniciales del 10/10 siguen en la carpeta homónima de esa fecha.
- Guion oficial: metadata del 11/10 conserva modificación 09/10 08:24:51.390Z;
  cobertura leída el 10/10 sigue aplicable. PDF original no contrastado.

CD actualizado: PR73 integrada en a0e9a56 el 11/10, run38136049444 y primera
promoción automática acreditados por [cierre publicado](https://github.com/EconomiconFinOps/tfm-economicon/pull/73#issuecomment-6108634067).
Lectura propia DockerServer 12:38:43UTC confirma current=c3eb665,
previous=a0e9a56, run38138774581, timer activo y journal Runtime verified.
El recibo identifica los SHA completos. Supera la afirmación del borrador del
10/10 de que CD seguía abierto; no reatribuye a este chat el smoke de JUP-052.
Reboot/producción permanecen pendientes, entorno mock privado. Ningún despliegue
ni gasto de IA se ejecutó para redactar esta memoria.

## Pendientes y siguientes pasos

1. Respuesta del usuario a lectura/exportación de la memoria completa para
   reconciliar sólo f y comprobar el límite conjunto de 20 páginas. Pregunta
   enviada; no leer el documento mientras esté pendiente. Sólo metadata consultada.
2. Dictámenes separados de subagentes conservados externamente; propuesta final
   hash2c75e1f6 y cobertura ca54f146. No acreditan incorporación/exportación.
3. Con el alcance de lectura resuelto: revisar contexto, incorporar f, verificar
   preservación de otros apartados y exportar PDF/Markdown fechados con hashes.
4. Completar aceptación, PR y Trello; mantener change activo y tarjeta En curso
   hasta resolver entrega canónica. No cerrar por entregar sólo propuesta.

Trello: excepción añadida a descripción y movimiento a En curso por integración
DockerServer el 11/10 12:37UTC. Sin mensajes Discord. Controles95/95 y
OpenSpec56/56 del 10/10 son históricos. Nuevos:83/83 gobernanza,61/61 OpenSpec,
trazabilidad/higiene1119 correctas, integridad y negativos documentales pasan;
resultados en evidencia vigente, sin pruebas nuevas de producto.
