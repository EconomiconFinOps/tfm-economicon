# ADR-0004: Adopción de shadcn/ui como sistema de componentes del frontend

- Estado: Accepted
- Fecha: 2026-09-07
- Tarjeta Trello: [JUP-094](https://trello.com/c/Yqg2iZsj/86-jup-094-reconciliar-packagejson-del-frontend)
- OpenSpec relacionado: `jup-094-reconcile-package-json`
- Sustituye a: ninguno
- Sustituido por: ninguno

## Contexto

El inventario de [JUP-091](../planning/JUP-091-economicon-source-inventory.md) clasificó 48 de las 61
dependencias del origen como `DESCARTAR`, entre ellas **26 primitivos `@radix-ui/*`** y 7 librerías de
apoyo a shadcn/ui, porque **ninguna pantalla del origen renderiza esos componentes hoy** — la
clasificación refleja uso real en el origen, no un veredicto sobre lo que el destino debería adoptar.
`RF-091-002` lo dejó explícito como "entrada para F2, no decisión de esa HU".

Las pantallas del destino renderizan hoy sus primitivos como HTML plano estilizado con Tailwind:
8 `<button>`, 6 `<label>`, 5 `<input>`, 2 `<textarea>` y 1 `<select>`, sin ninguna capa de composición
compartida. [JUP-094](../../openspec/changes/jup-094-reconcile-package-json/design.md) evaluó primero
mantener ese patrón (design.md, decisión 1 original), pero el equipo revirtió esa posición durante el
`apply`: F3 va a construir o reconciliar varias pantallas (login, selector de tenant, ingesta, chat del
asistente) que necesitan primitivos consistentes y accesibles — selects, labels, separadores, y al
menos un patrón de diálogo/tooltip para ingesta y chat —, y hacerlo a mano en cada pantalla traslada el
coste de accesibilidad y consistencia a cada componente futuro, uno por uno.

## Decisión

Se adopta el patrón de componentes de **shadcn/ui**, respaldado por primitivos de **Radix UI**, para
`apps/frontend`, en lugar de seguir construyendo cada primitivo de formulario o superposición a mano
con HTML plano y Tailwind.

**Alcance acotado a la necesidad conocida del destino, no al conjunto del origen.** Se instalan 6
paquetes, no los 26 del origen: `@radix-ui/react-label`, `@radix-ui/react-select`,
`@radix-ui/react-slot`, `@radix-ui/react-separator`, `@radix-ui/react-dialog`,
`@radix-ui/react-tooltip`. Esta decisión cubre **la dependencia**, no su uso: instalar los paquetes es
JUP-094 (reconciliar `package.json`, sin tocar `src/**`); **copiar el código fuente de cada
componente** a `src/components/ui/`, siguiendo la convención de shadcn/ui de no consumirlo como
librería opaca, ocurre en F3, componente por componente, cuando la pantalla que lo necesita se
construye — así solo el primitivo realmente usado entra al repositorio y al bundle.

Las 48 dependencias `DESCARTAR` del inventario de JUP-091 —incluidos los otros 20 primitivos Radix
del origen— **no se reinstauran en bloque**. `RF-091-002` se cierra con esta resolución: se adopta un
subconjunto deliberado, elegido para el destino, no heredado del `ui/` muerto del origen.

## Consecuencias

**Se vuelve más fácil:**

- Componer selects, diálogos y tooltips con foco, navegación por teclado y ARIA correctos sin
  reimplementarlos por pantalla.
- Que las pantallas de F3 compartan un vocabulario visual y de interacción común, en vez de HTML ad
  hoc por página.

**Se vuelve más difícil:**

- `apps/frontend` gana una superficie de dependencias de sistema de diseño (6 paquetes Radix más las
  convenciones de shadcn/ui) que no tenía hasta esta decisión.
- Quien contribuya debe conocer el patrón de "copiar al repositorio" de shadcn/ui: los componentes
  viven en el código propio, no se actualizan con `pnpm update` como una librería normal.

**Se vuelve más arriesgado:**

- Elegir un subconjunto de 6 paquetes antes de que F3 escriba una sola pantalla es una apuesta sobre
  qué primitivos hacen falta de verdad. Si F3 necesita un séptimo (p. ej. `@radix-ui/react-tabs`), es
  una instalación pequeña de seguimiento, no una reapertura de este ADR. Si `dialog`/`tooltip`
  resultan innecesarios, quedan como peso muerto hasta que se retiren — el mismo tipo de riesgo que
  ADR-0003 ya aceptó para `allowJs`.

## Alternativas consideradas

- **Seguir con HTML plano + Tailwind por pantalla** (posición original de `design.md` en esta misma
  tarjeta, antes de revisarse). Más barato de empezar, pero traslada el trabajo de accesibilidad y
  consistencia a cada componente nuevo, uno por uno, durante toda F3.
- **Adoptar el `ui/` completo del origen (26 primitivos Radix)**. Descartada: 20 de ellos no tienen
  consumidor identificado en las pantallas conocidas del destino (`RF-091-002`) — es exactamente la
  abstracción para un futuro hipotético que ADR-0003 ya rechazó para `packages/shared-config`.

## Evidencia y seguimiento

- Inventario de JUP-091: confirma que ninguna de las 48 dependencias `DESCARTAR` tiene consumidor real
  en las pantallas renderizadas del origen; ese hallazgo es sobre el uso real del origen, no un
  veredicto sobre la adopción del destino.
- `RF-091-002` (`openspec/findings/backlog.md`): se cierra con este ADR y JUP-094, con la resolución
  "adoptar el subconjunto de 6 paquetes Radix listado arriba, no los 26 del origen".
- Seguimiento: las tarjetas de F3 que construyan pantallas con estos primitivos deben citar este ADR
  en su `design.md`, misma convención que estableció ADR-0003.
