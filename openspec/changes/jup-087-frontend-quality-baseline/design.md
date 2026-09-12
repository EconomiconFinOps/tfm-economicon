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
actuales siguen sujetos a la regla. La condicion de cierre de RF-082-002 es
migrar esos componentes o sus sustitutos a `.tsx` con cobertura real de sus
props. El plan inicial situaba ese trabajo en F3/F5; JUP-087 lo ejecuta ahora
sobre la interfaz existente, antes del port visual de JUP-095. No se considera
suficiente desactivar la regla en F2.

JUP-087 conserva lint sin errores y pruebas reales de los recorridos criticos
como puerta de calidad. Una desactivacion global de la regla sobre JavaScript
sin cobertura equivalente de tipos no satisface este cambio. F2 proporciona el
tooling; F3 conserva el port visual y F5 la retirada final de `allowJs`. JUP-088
solo reconcilio este contrato documental; esta implementacion pertenece a JUP-087.

### Red y almacenamiento se aislan en pruebas

Las pruebas usan un entorno DOM, interceptan `fetch` y limpian `localStorage` y
la cache entre casos. No dependen de servicios Docker ni de credenciales reales.

## Risks / Trade-offs

- [Tests acoplados al markup] -> consultar por roles, labels y resultados visibles.
- [Mocks ocultan errores de contrato] -> fixtures alineadas con schemas backend y
  al menos una validacion integrada posterior.
- [Migracion tipada crece de alcance] -> seguir ADR-0003 y las tareas separadas de F2/F3/F5; un cambio de decision requiere otro ADR.
- [Lint verde por excepciones] -> test de configuracion que rechaza la anulacion global.

## Implementacion del baseline — 2026-09-08

JUP-087 ejecuta ahora el tipado de los componentes existentes previsto por
ADR-0003, antes de portar la interfaz de Figma Make en JUP-095. Se mantienen los
flujos, estilos y endpoints del destino; los contratos de respuestas HTTP y las
props pasan a TypeScript con `strict: true`. `allowJs: true` permanece como
decision de convivencia hasta el cierre de F5. No se relaja el rigor ni se
amplia el ambito de la excepcion ESLint para JSX.

Se adopta Vitest 3.2.7, compatible con Vite 5, con React Testing Library,
user-event, jest-dom y jsdom. El runner reutiliza `vite.config.ts`; `pnpm test`
ejecuta casos reales y termina con error si falla una prueba. Un proyecto
TypeScript separado verifica las pruebas sin añadir globals Node al codigo de
la aplicacion. JUP-095 puede reutilizar este runner al incorporar su interfaz.

La suite monta App con un QueryClient nuevo, desactiva reintentos para que los
fallos sean deterministas, intercepta fetch y rechaza solicitudes no previstas.
Los datos de prueba reflejan los schemas del backend; al terminar cada caso se
limpian DOM, almacenamiento, mocks y cache. Se cubren respuestas satisfactorias,
errores, carga y listas vacias en los recorridos del contrato. Un test ejecuta
ESLint sobre JSX sin contrato de props para impedir su desactivacion global.

El check obligatorio `Frontend build` ejecuta primero lint y pruebas mediante
los comandos del workspace filtrados al frontend. No requiere crear otro
contexto de proteccion: el fallo de cualquiera de esos pasos bloquea ese check.
Los tests de gobernanza verifican esta conexion. El build y el check obligatorio
de tipos conservan sus nombres y requisitos.

Las paginas de ingesta y conversaciones se montan de nuevo al cambiar de tenant.
La seleccion, borradores y estados de mutacion pertenecen asi al tenant de su
montaje, y una respuesta tardia del anterior no modifica el formulario actual.
Las solicitudes ya enviadas pueden terminar en su tenant original; no se
presenta este aislamiento de interfaz como cancelacion de operaciones backend.

Fuentes del runner: [Vitest 3](https://v3.vitest.dev/guide/) y
[React Testing Library](https://testing-library.com/docs/react-testing-library/setup/).
