JUP: JUP-061
Trello: https://trello.com/c/qXoHFxyy

## Why

Las decisiones están repartidas entre ADR, diseños y evidencias. El índice no las
enumera y varias referencias apuntan a cambios archivados. La memoria y el tutor
necesitan distinguir justificación, aprobación e implementación verificable.

## What Changes

- Ampliar el índice canónico docs/adr/README.md con fechas, estado, responsables,
  alternativas y evidencias; enlazar ADR de PR abiertas sin copiar sus contenidos.
- Reparar enlaces y fechar las notas de reconciliación sin reescribir aprobaciones.
- Documentar para ratificación las justificaciones existentes de pgvector,
  autenticación demo y Compose; reservar 0011/0012 ya usados en PR #51/#54.
- Enlazar la especificación architecture-decisions y añadir requisitos del registro.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- architecture-decisions: inventario trazable y distinción de evidencia/aceptación.

## Impact

Solo documentación. Sin cambios de runtime, dependencias, presupuestos ni despliegue.
No se redacta otra copia de la memoria ni se concede aprobación en nombre del equipo.

## Participación prevista

Liderazgo Alejandro Aguado; pairing Lucia Mateo; revisión Paris Arcos Martin;
validación, pruebas y documentación Victor Mendez, según Trello consultado el 01/10.
La asignación no acredita actividad realizada. Aceptación documental pendiente.

## Reconciliación autorizada — 02/10/2026

El usuario autorizó resolver el conflicto con develop y diagnosticar/revalidar el
fallo de CI. Se conserva el alcance de registro documental y se añade una
corrección de sincronización al test heredado JUP-098 de historial de sesión:
esperar a que el router haya consumido la marca antes de observar el recorrido
hacia atrás. No cambian el componente de login ni su contrato. La validación de
este incremento incluye frontend y dos controles de mutación del test existente.

## Cierre documental — 04/10/2026

La participación prevista del 01/10 arriba es histórica. Roles vigentes:
Alejandro liderazgo, Victor pairing previsto, Paris revisión, Lucía validación.
PR #60 integrada y validación publicada; fuentes en
[evidencia](../../../../docs/evidence/JUP-061-validation.md).
No consta pairing realizado. El archivo y la promoción cierran el registro
documental; no aceptan ADR Proposed ni completan condiciones de otros cambios.
