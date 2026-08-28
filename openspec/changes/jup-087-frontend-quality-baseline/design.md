JUP: JUP-087
ADR: requerida solo si se adopta TypeScript o se sustituye el stack de pruebas fuera del baseline actual.

## Context

Vite construye la aplicacion React actual. ESLint encuentra 49 infracciones
`react/prop-types` en nueve archivos y el script de tests es un placeholder. El
frontend ya contiene login, seleccion de tenant, dashboard, creacion de ingesta
y conversaciones, pero carece de una red de regresion automatizada.

## Goals / Non-Goals

**Goals:**

- Obtener lint limpio con contratos de props explicitos o una migracion tipada aprobada.
- Ejecutar pruebas de componentes/recorridos en `pnpm test` y CI.
- Cubrir exito, carga vacia y errores de red/autorizacion en los flujos criticos.
- Mantener comportamiento y aspecto salvo cambios de testabilidad/accesibilidad.

**Non-Goals:**

- Desactivar globalmente `react/prop-types` para ocultar el baseline.
- Reemplazar la interfaz por el prototipo Figma Make.
- Completar las capacidades funcionales de JUP-035, JUP-054 o JUP-085.

## Decisions

### La puerta es comportamiento, no una cifra de cobertura aislada

Se exige al menos una prueba positiva y una de error para login/sesion, carga y
seleccion de tenant, dashboard, ingesta y conversacion. La cobertura numerica
puede añadirse, pero no sustituye esos escenarios.

### Los contratos de props se arreglan de forma explicita

En JavaScript se declaran PropTypes mantenibles; si el equipo adopta TypeScript,
debe hacerlo mediante la decision y alcance correspondientes. Una desactivacion
global de la regla no satisface JUP-087.

### Red y almacenamiento se aislan en pruebas

Las pruebas usan un entorno DOM, interceptan `fetch` y limpian `localStorage` y
la cache entre casos. No dependen de servicios Docker ni de credenciales reales.

## Risks / Trade-offs

- [Tests acoplados al markup] -> consultar por roles, labels y resultados visibles.
- [Mocks ocultan errores de contrato] -> fixtures alineadas con schemas backend y
  al menos una validacion integrada posterior.
- [Migracion tipada crece de alcance] -> ADR/tarjeta separada antes de cambiar tooling.
- [Lint verde por excepciones] -> test de configuracion que rechaza la anulacion global.
