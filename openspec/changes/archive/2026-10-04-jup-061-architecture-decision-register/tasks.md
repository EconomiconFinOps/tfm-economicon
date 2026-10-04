## 1. Inventario y fuentes

- [x] 1.1 Leer tarjeta por el puente DockerServer y contrastar develop/PR abiertas.
- [x] 1.2 Inventariar los ADR existentes y las decisiones explicadas en otras fuentes.
- [x] 1.3 Enlazar fechas, alternativas, responsables de origen y aprobación o pendiente.

## 2. Reconciliación documental

- [x] 2.1 Reparar enlaces ADR a OpenSpec archivado y notas de evidencia superadas.
- [x] 2.2 Documentar razones faltantes para pgvector, auth demo y Compose sin atribuir aceptación.
- [x] 2.3 Vincular architecture-decisions a JUP-061 y definir el delta del registro.
- [x] 2.4 Enlazar la fuente canónica para memoria/tutor.

## 3. Validación y aceptación

- [x] 3.1 Validar OpenSpec estricto, trazabilidad, higiene y enlaces; registrar resultados.
- [x] 3.2 Publicar PR a develop y enlazar evidencia en Trello.
- [x] 3.3 Registrar revisión de Paris y validación de Lucia; dejar constancia del pairing no acreditado en la evidencia de cierre.
- [x] 3.4 Registrar el seguimiento de ratificaciones con sus responsables y separar ese proceso del cierre documental; no inferir aceptación de un merge.

### Delimitación del cierre — 04/10/2026

La tarea 3.3 queda satisfecha por las reviews de PR #60 enlazadas en
`docs/evidence/JUP-061-validation.md`. Victor tenía pairing previsto, pero no
consta evidencia atribuible de coautoría; su review del índice acredita revisión,
no pairing. No se declara realizada esa contribución.

La redacción anterior de 3.4 («Ratificar ADR propuestos ... antes del freeze»)
no se ha ejecutado. Se delimita como seguimiento documental: las ratificaciones
son decisiones humanas posteriores, fuera de la promoción de estos requisitos.
ADR-0013/14/15/16 y ADR-0005 conservan sus estados; sus responsables deben
ratificarlos o aclararlos en las fuentes originales. ADR-0002 se sigue en
[PR #71 / JUP-078](https://github.com/EconomiconFinOps/tfm-economicon/pull/71),
sin asumir aprobación por su apertura. El archivo no acredita ratificación,
pairing ni condiciones operativas pendientes de otros cambios.

## 4. Reconciliación autorizada 02/10/2026

- [x] 4.1 Reconciliar develop conservando las dos notas de ADR-0004.
- [x] 4.2 Corregir sincronización del test heredado y preservar detección de ambos mutantes.
- [x] 4.3 Validar frontend 437/437, lint/tipos/build, OpenSpec y enlaces; documentar límites locales.
- [x] 4.4 Verificar CI del head publicado y ausencia de conflicto remoto.
