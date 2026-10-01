JUP: JUP-065
Trello: https://trello.com/c/SZUFo4ol

## Why

El equipo necesita preparar la demo antes de disponer del MVP integrado,
con datos fijos y resultados comprobables para evitar improvisar o presentar
capacidades simuladas como resultados reales.

## What Changes

- Publicar un recorrido de siete minutos, preflight, recuperación y registro de ensayo.
- Fijar muestra pública, corpus y cinco casos JUP-069 a un commit verificable.
- Reproducir offline referencias numéricas y prompts sin rúbricas; comprobarlos en CI.
- Separar aceptación de la preparación de ensayo integrado y cierre operativo.

## Capabilities

### New Capabilities

- `functional-demo-preparation`: contrato de preparación reproducible de la demo.

### Modified Capabilities

Ninguna.

## Impact

Documentación, fixtures pequeñas con licencia, scripts Python sin dependencias
nuevas y dos comandos en el job de gobernanza existente. No cambia runtime,
proveedores, bases de datos ni corpus indexable de la aplicación. El historial
completo se obtiene únicamente en ese job para leer el commit de referencia.
La autorización del usuario cubre publicar y solicitar revisión/validación de
esta preparación; no equivale a aprobación de revisores ni a cierre de JUP-065.
