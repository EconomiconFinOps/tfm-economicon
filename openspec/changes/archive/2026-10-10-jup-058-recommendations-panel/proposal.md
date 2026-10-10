JUP: JUP-058
Trello: https://trello.com/c/kU8swHK1

## Why

El ingeniero necesita clasificar recomendaciones por tipo, ahorro estimado y
dificultad. La vista actual usa ejemplos AWS estáticos, estadísticas ajenas al
listado y un botón Implementar sin acción; no permite priorizar ni consultar
la evidencia que respalda una propuesta.

## What Changes

- Panel interactivo con filtros combinables, ordenación, estados y detalle accesible.
- Procedencia visible y cifras coherentes con la fuente; coste observado,
  ahorro potencial y ahorro conseguido permanecen conceptos distintos.
- Adaptación de los contratos propuestos JUP-033 y JUP-034, con dobles explícitos
  mientras esas dependencias no estén integradas ni verificadas extremo a extremo.
- Pruebas funcionales, evidencia visual y guía de limitaciones para revisión.

## Capabilities

### New Capabilities

- `recommendations-panel`: clasificación y consulta de recomendaciones FinOps con evidencia.

### Modified Capabilities

Ninguna capacidad de backend cambia.

## Impact

Frontend en `/recommendations`, sus datos de demostración, contratos de lectura
y pruebas. Se conserva el tema existente. No se implementa el motor JUP-033,
el evaluador JUP-034, acciones sobre Azure ni el rediseño JUP-112.
Roles Trello contrastados el 10/10/2026: Lucía Mateo liderazgo, Paris Arcos Martin
pairing, Victor Mendez revisión y Alejandro Aguado validación. Su asignación
no acredita participación realizada, pairing o aprobación.
