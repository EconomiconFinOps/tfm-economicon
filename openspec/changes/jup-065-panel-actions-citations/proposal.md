JUP: JUP-065
Trello: https://trello.com/c/SZUFo4ol

## Why

El ensayo del RC f444ba11 detectó aclaraciones presentes en API pero ocultas en
el panel, frases con huecos numéricos confirmadas como completas y fuentes que
no podían abrirse. La corrección se entrega en una PR independiente de PR63.

## What Changes

- Mostrar next_actions de la respuesta persistida en panel e historial.
- Abrir un visor accesible del fragmento documental autorizado y persistido.
- Rechazar continuaciones narrativas incompletas detectables, sin inventar cifras.
- Versionar el contrato de renderizado y añadir regresiones sin consumo de modelos.

## Capabilities

### New Capabilities

- `assistant-panel-completeness`: acciones visibles, apertura de fragmentos y rechazo de huecos narrativos.

### Modified Capabilities

Ninguna.

## Impact

Frontend compartido por panel/historial, metadatos de cita del backend,
renderizador/streaming del processor y manifiesto de prompt. Sin migraciones,
proveedores nuevos, cambios en otras PR ni aceptación generativa por pruebas dobles.
Los roles existentes de JUP-065 se conservan; la excepción de agentes del ensayo
no se aplica a las reviews de esta PR.
