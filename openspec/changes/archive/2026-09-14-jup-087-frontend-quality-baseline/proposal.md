JUP: JUP-087
Trello: https://trello.com/c/JHcidwiR

## Why

El frontend compila, pero el baseline heredado mantiene 49 errores
`react/prop-types` y su script de test no ejecuta pruebas reales. CI no puede
demostrar que login, tenant, dashboard, ingesta y conversacion sigan funcionando.

## What Changes

- Exigir lint con cero errores sin ocultar reglas de contratos de props.
- Configurar un runner frontend reproducible en local y CI.
- Definir cobertura minima positiva y de error para los recorridos criticos.
- Vincular RF-082-002 a JUP-087 y separar el residual funcional RF-083-002.

## Capabilities

### New Capabilities

- `frontend-quality-baseline`: puerta de calidad verificable para lint, tests y
  recorridos criticos de la interfaz del MVP.

### Modified Capabilities

- None.

## Impact

- Afecta configuracion ESLint/test, componentes React, scripts del workspace y CI.
- No autoriza un rediseño visual ni la migracion completa del frontend.
- JUP-035 conserva el residual de integrar la experiencia visual objetivo.
