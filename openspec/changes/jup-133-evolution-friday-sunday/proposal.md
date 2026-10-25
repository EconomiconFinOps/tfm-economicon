JUP: JUP-133
Trello: https://trello.com/c/Yv1ETc2G

## Why

La campaña del domingo25 tras PR164 no está versionada en el dashboard. El usuario
pide agregarla y ver la evolución frente al viernes23. No son un A/B ni dos
instrumentos semánticos idénticos: presentar una tasa única escondería sus límites.

## What Changes

- Versionar observaciones reducidas y dos proyecciones derivadas con denominadores explícitos.
- Añadir a la sección2 existente la comparación operativa de44casos (132/44operaciones)
  y el resultado completo de50consultas deldomingo, conservando datos y paneles previos.
- Generar SQL aditivo que aborta ante identidades con contenido diferente.
- Publicar procedencia, costes incompletos y limitaciones sin secretos ni conversaciones.

## Capabilities

### Modified Capabilities
- `assistant-evaluation-composition`: evolución descriptiva de dos protocolos distintos,
  separada de la comparación estricta existente y de la aceptación humana.

## Impact

Datos JUP-133, manifiesto, generador offline, cuatro paneles del dashboard y pruebas.
Sin cambios al asistente, servicios, accesos, permisos, modelos o cuotas. Sin nuevas
inferencias, despliegue, carga compartida o merge. Roles de JUP-133 conservados;
implementación de Alejandro como contribución, sin atribuir ejecución a otros miembros.
