JUP: JUP-087
ADR: [ADR-0003 (JUP-092), TypeScript aceptado](../../../docs/adr/ADR-0003-frontend-typescript.md); una sustitucion del stack de pruebas fuera del baseline actual requiere su decision correspondiente.

## Context

Vite construye la aplicacion React actual. ESLint encuentra 49 infracciones
`react/prop-types` en nueve archivos y el script de tests es un placeholder. El
frontend ya contiene login, seleccion de tenant, dashboard, creacion de ingesta
y conversaciones, pero carece de una red de regresion automatizada.

El [inventario JUP-090](../../../docs/planning/JUP-090-frontend-migration-baseline.md)
precisa la paridad de login, tenant y dashboard que debe conservarse durante la
migracion. Ese guion positivo no sustituye los casos de error, ingesta y
conversacion exigidos aqui. RF-090-001 (Docker) y RF-090-003 (consumo de `/me`)
siguen abiertos en sus lineas de reconciliacion; JUP-088 no los da por resueltos.

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

### Los contratos de props siguen la decision TypeScript aceptada

ADR-0003 (JUP-092) fija TypeScript con `strict: true`, type-check obligatorio en
CI y `allowJs: true` durante la migracion (`false` al cerrar F5). F2 instala el
tooling y desactiva `react/prop-types` solo para `.ts`/`.tsx`; los nueve `.jsx`
actuales siguen sujetos a la regla. RF-082-002 permanece abierto hasta que F3
(o el cierre de F5) migre esos componentes o sus sustitutos a `.tsx` con cobertura
real de sus props. No se exige corregir manualmente las 49 infracciones antes de
esa migracion, ni se considera suficiente desactivar la regla en F2.

JUP-087 conserva lint sin errores y pruebas reales de los recorridos criticos
como puerta de calidad. Una desactivacion global de la regla sobre JavaScript
sin cobertura equivalente de tipos no satisface este cambio. El tooling y la
migracion siguen las tareas separadas de F2/F3/F5 del ADR; JUP-088 solo reconcilia
este contrato documental.

### Red y almacenamiento se aislan en pruebas

Las pruebas usan un entorno DOM, interceptan `fetch` y limpian `localStorage` y
la cache entre casos. No dependen de servicios Docker ni de credenciales reales.

## Risks / Trade-offs

- [Tests acoplados al markup] -> consultar por roles, labels y resultados visibles.
- [Mocks ocultan errores de contrato] -> fixtures alineadas con schemas backend y
  al menos una validacion integrada posterior.
- [Migracion tipada crece de alcance] -> seguir ADR-0003 y las tareas separadas de F2/F3/F5; un cambio de decision requiere otro ADR.
- [Lint verde por excepciones] -> test de configuracion que rechaza la anulacion global.
