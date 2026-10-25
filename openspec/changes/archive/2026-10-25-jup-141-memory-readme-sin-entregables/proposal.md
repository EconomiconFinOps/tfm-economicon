JUP: JUP-141
Trello: https://trello.com/c/2b2K962A/133-jup-141

# README de la memoria sin la carpeta de entregables

## Why

`docs/memoria/README.md` describe una carpeta, `materiales/06-entregables/`, que no forma parte del repositorio ni de su flujo de trabajo. La guía no debe indicar una ubicación que el repositorio no controla ni puede comprobar, y el equipo ha decidido dejar de documentarla ahí.

## What Changes

- Se elimina de «Dónde vive» la viñeta sobre exportaciones fechadas, manifiesto SHA-256 y la carpeta `materiales/06-entregables/`.
- En «Para herramientas y asistentes», la viñeta sobre la memoria queda como «La memoria no está en el repositorio: no se busca ni se regenera desde Git.», sin la cláusula que equipara las exportaciones de esa carpeta con la memoria.
- El requisito de exportaciones de `project-memory-governance` deja de decir que se guardan «next to the other final deliverables», que era la referencia genérica a esa misma carpeta. Se conserva el resto: fechadas, fuera de Git, con SHA-256 en un manifiesto e inmutables (ver `design.md`).
- Quedan fuera los registros históricos que citan la carpeta (`docs/evidence/`, `docs/continuidad/`, los changes de OpenSpec y su archivo) y las menciones a «exportación» que no nombran la ruta.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `project-memory-governance`: el requisito «Dated exports are immutable and stay outside Git» deja de ubicar las exportaciones junto a los demás entregables finales; no cambian sus escenarios.

## Impact

- `docs/memoria/README.md` (dos viñetas).
- `openspec/specs/project-memory-governance/spec.md` (una frase de un requisito, vía delta).
- Sin cambios de código, de CI ni de dependencias.
- El README queda sin describir el régimen de exportaciones (fechadas, fuera de Git, SHA-256 en un manifiesto, inmutables), que la spec sigue exigiendo; el desfase se declara y se acota en `design.md`.

## Human Approval

- Change: jup-141-memory-readme-sin-entregables
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-10-25
- Carril: standard
- Source: aprobación en la conversación de trabajo tras elegir el delta MODIFIED del requisito de exportaciones
