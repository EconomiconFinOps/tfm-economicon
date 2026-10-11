JUP-105 — Cerrar la épica de migración del frontend. Carril `light`.

## Context

Motivación y alcance en [`proposal.md`](proposal.md). Aquí solo el estado que condiciona el enfoque,
verificado el 2026-10-08 sobre `develop` en `ff2ea6b` (la rama `chore/JUP-105-close-frontend-migration`
parte de ese commit).

**Lo que la tarjeta daba por pendiente y se confirma.**

| Punto | Comprobación | Resultado |
| --- | --- | --- |
| `allowJs` | `apps/frontend/tsconfig.json`, línea 24 | `true`, con `checkJs: false` e `include: ["src"]` |
| JavaScript restante | `git ls-files` sobre `apps/frontend/src` y `apps/frontend/tests` | 0 archivos `.js`, `.jsx`, `.mjs` o `.cjs`; el único del paquete es `eslint.config.js`, fuera del `include` |
| Endurecimiento en seco | `tsc --noEmit --allowJs false` y `tsc -p tsconfig.test.json --noEmit --allowJs false` | Código de salida 0 en los dos; `tsconfig.test.json` hereda de `tsconfig.json` y `tsconfig.node.json` no declara `allowJs` |
| Lint | `corepack pnpm --filter @finops/frontend lint` | Código de salida 0, sin violaciones |
| Rutas | `apps/frontend/src/routes.tsx` | 9 bajo `SessionGate`, más `/login` |
| Origen de datos por ruta | imports de cada página | Backend (5): `/`, `/overview-legacy`, `/ingest`, `/assistant`, `/system-health`. Demostración (4): `/operational`, `/cuts`, `/anomalies`, `/recommendations` |
| Rótulo de demostración | texto visible de cada página | Solo `/anomalies` lo muestra; `/operational`, `/cuts` y `/recommendations` no (`RF-104-004`) |
| Enlaces relativos rotos | recorrido de los `.md` versionados | 66 en 26 archivos: 53 en `openspec/changes/archive/` y 13 fuera (8 en la evidencia de JUP-085, 2 en la de JUP-097, 1 en la de JUP-013 y 2 falsos positivos en la de JUP-099, líneas 505 y 793, donde un ejemplo de código contiene un corchete y un paréntesis seguidos que no son un enlace) |
| Menciones a configuración local | búsqueda de los seis términos que enumera la fila `RF-099-001` del backlog, con sus mismas exclusiones | 42 líneas en 11 archivos: 36 en 7 archivos archivados (17 en el `review.md` de JUP-095), 5 en 3 evidencias y 1 en `apps/frontend/vite.config.ts`. Aparte, 9 menciones legítimas que describen el propio hallazgo (8 en el `review.md` de JUP-099 y 1 en el backlog) |
| Changes de la épica | `openspec/changes/archive/` | Las doce tarjetas archivadas (13 carpetas: JUP-095 tiene dos); ninguna activa |
| Hallazgos de la épica | `openspec/findings/backlog.md` | 21 en `Open`, todos con `Owner: Equipo Economicon` |

**Lo que difiere de la tarjeta o no estaba en ella.**

- **El spike tiene una tercera tarjeta con el estado desfasado.** Además de JUP-099 (línea 255) y
  JUP-104 (línea 320), JUP-103 figura como «implementada» (línea 299) y se fusionó el 07/10 (#75).
- **El spike repite la afirmación sobre `/overview-legacy` en registros históricos.** Las líneas 231,
  464 y 481 dicen que es el único dashboard con datos reales. Son anotaciones de lo que era cierto al
  cerrar JUP-095 y JUP-097.
- **La spec vigente `frontend-typescript-tooling` está desfasada.** Tiene un escenario que afirma que
  `src/` «hoy contiene únicamente archivos `.js` y `.jsx`», otro que fija la línea base de lint en
  «exactamente las 49» violaciones y otro que exige que ningún archivo fuente se haya renombrado a
  TypeScript y que `RF-082-002` siga abierto. Los tres describen el estado de JUP-093; el primero,
  además, contradice directamente el endurecimiento de `allowJs`.
- **Hay un segundo módulo sin uso.** Además de `src/data/demo/executiveCostDashboard.ts` (solo lo
  nombra `color-tokens.guard.test.ts`), `src/hooks/useCostKpis.ts` no lo importa ningún archivo.
- **`/overview-legacy` sigue en la navegación** (`Layout.tsx`, entrada «Overview») y es la ruta que
  nombran 30 líneas de 9 archivos de pruebas, la mayoría de sesión, expiración y cambio de ámbito
  que la usan como vehículo.
- **`RF-104-004` también quedó desfasado en una frase**: dice que `/` «rotula su sección de
  demostración», y JUP-055 retiró esa sección.

**Lo que ya está resuelto y no se repite**, solo se cita: la fila de `/` en el README (JUP-055), el
registro del check `Frontend tests` en `docs/governance/github-branch-protection.md`, el acceso de
demostración y la tarjeta de Docker en el spike (JUP-104 y JUP-103), `RF-087-002` en `Fixed` y los
tres ADR del frontend (0003, 0004 y 0012) en `Accepted`.

**Restricciones.** La batería de `test` desde la raíz se ejecuta por mitades (`RF-103-005`,
`RF-098-004`) y siempre con la caché de turbo desactivada. El spike y el backlog son archivos que
tocan casi todos los pull requests abiertos. Ni quien revisa ni quien valida suben commits a la rama.

## Goals / Non-Goals

**Goals:**

- Que cada afirmación corregida se pueda comprobar con un comando escrito en la evidencia, sin
  depender de herramientas que no estén en el repositorio.
- Que el recuento de pantallas viva en un solo sitio, de modo que la próxima tarjeta que cambie una
  pantalla tenga un único lugar que actualizar.
- Que la diferencia entre documentación viva y registro histórico quede respetada: lo vivo se corrige,
  lo histórico se anota.
- Que cada hallazgo abierto de la épica diga qué tiene que pasar para cerrarlo y quién da el
  siguiente paso.

**Non-Goals:**

- Retirar `/overview-legacy`, su página, su hook o sus pruebas, ni los dos módulos sin uso.
- Añadir una herramienta versionada de comprobación de enlaces o un test guardián de JavaScript:
  ambas son código nuevo con sus pruebas y sacarían la tarjeta del carril `light`.
- Reescribir el contenido de los registros archivados más allá de enlaces y referencias a
  herramientas locales.
- Tomar las decisiones de producto que la épica deja abiertas (`RF-091-003`, `RF-098-002`,
  `RF-104-001` y las demás): se enuncian con dueño, no se resuelven.

## Decisions

### 1. `allowJs` pasa a `false` cambiando solo ese valor, con un control positivo

Se cambia `"allowJs": true` por `"allowJs": false` y no se toca nada más del archivo. `checkJs: false`
se deja: no tiene efecto sin `allowJs`, pero la configuración con las dos líneas es exactamente la que
se probó en seco.

La verificación tiene dos partes. La primera es que `typecheck`, `lint`, `test` y `build` del frontend
siguen en verde. La segunda es un control positivo: crear de forma temporal un archivo `.js` en
`src/` importado desde un `.ts`, comprobar que `typecheck` termina con error y borrar los dos. Sin el
control, «sigue en verde» no distingue una opción que hace algo de una que no hace nada.

Límite que se deja escrito: el compilador rechaza un JavaScript **importado** desde TypeScript, no la
mera presencia de un archivo `.js` suelto en `src/`. Un archivo así no participa en la aplicación,
porque nada lo importa. El bloque de `eslint.config.js` para `src/**/*.{js,jsx}` se conserva: es el
que mantendría la validación de props sobre un JSX que alguien añadiera, como pide ADR-0003.

| Alternativa | Por qué no |
| --- | --- |
| Eliminar la línea `allowJs` (el valor por defecto es `false`) | El valor explícito documenta la decisión en el propio archivo, que es lo que ADR-0003 llama «endurecer». |
| Eliminar también `checkJs` | Limpieza sin efecto que amplía el diff de un archivo de configuración; no la pide nadie. |
| Añadir un test guardián que falle si aparece un `.js` en `src/` o `tests/` | Es código nuevo con su ciclo de pruebas. Cubre un caso (un archivo huérfano) que no llega a la aplicación. Si el equipo lo quiere, es una tarjeta propia. |

### 2. La spec `frontend-typescript-tooling` se pone al día en tres requisitos

El endurecimiento contradice el escenario «El JavaScript existente sigue siendo válido durante la
migración», así que la spec tiene que cambiar. Al tocarla se corrigen los otros dos escenarios que
describen el estado de JUP-093: la línea base de 49 violaciones y «Ningún archivo fuente migrado». El
delta está en [`specs/frontend-typescript-tooling/spec.md`](specs/frontend-typescript-tooling/spec.md).

La forma del delta la impone la herramienta: `openspec validate` no deja que un requisito modificado
pierda un escenario. Por eso los dos requisitos que tienen que perder uno (el del compilador y el de
arranque y build) se retiran y se sustituyen por otro con nombre nuevo, que conserva los escenarios
que siguen siendo ciertos. El de lint se modifica en el sitio: su escenario «La línea base de
violaciones no empeora» mantiene el nombre y pasa a exigir cero violaciones.

No se crea ninguna capacidad nueva: el cierre de una épica no es un comportamiento del sistema, y un
requisito inventado para «tener spec» sería justo el tipo de afirmación que esta tarjeta retira.

En el delta la referencia a ADR-0003 va como ruta desde la raíz y no como enlace relativo: el mismo
texto vive primero en la carpeta del change, después en `archive/` y finalmente en `openspec/specs/`,
tres profundidades distintas, y un enlace relativo solo resolvería en una.

Alternativa considerada: cambiar solo el requisito del compilador y dejar los otros dos. Se descarta
porque dejaría en la spec vigente dos afirmaciones que el propio cierre sabe falsas. Si en el gate
pre-código se prefiere el cambio mínimo, basta con quitar del delta el requisito de lint y el par de
arranque y build; el resto del diseño no cambia.

### 3. El recuento de pantallas vive en la tabla de rutas del README del frontend

`apps/frontend/README.md`, sección «Rutas», ya es la tabla que lista cada ruta con su pantalla. Se le
añaden dos columnas (origen de los datos y si la interfaz rotula la demostración), la fila de
`/system-health` y una línea con la fecha y el commit contra el que se verificó. El backlog
(`RF-095-002`, `RF-091-003`, `RF-104-004`), el mapa de carencias y el punto 13 del spike enlazan a esa
sección y no repiten cifras.

| Alternativa | Por qué no |
| --- | --- |
| Un documento nuevo en `docs/planning/` | Sería un cuarto sitio que mantener; el README es el que actualiza quien cambia una pantalla (lo hicieron JUP-055 y JUP-047). |
| El punto 13 del spike | El spike es un registro de la épica y deja de editarse al cerrarla; el recuento tiene que poder cambiar después. |
| La evidencia de JUP-105 | Una evidencia es una foto fechada; no debe ser la referencia viva. |

El recuento se repite justo antes de escribirlo y otra vez tras traer `develop`, porque #66 (JUP-017)
y #69 (JUP-036) pueden cambiarlo.

### 4. Lo vivo se corrige, lo histórico se anota

- **Documentación viva** (README, backlog, mapa de carencias, comentario de `routes.tsx`): se
  reescribe para que diga lo que es cierto hoy. Las filas del backlog conservan su descripción
  original y añaden la actualización fechada, como ya hicieron `RF-093-001` y `RF-091-004`.
- **Registros históricos** (evidencia de JUP-095, puntos 7 y 8 del spike): no se reescriben. Reciben
  una nota fechada que dice qué cambió después y dónde está el estado vigente. La de JUP-095 remite a
  `docs/governance/github-branch-protection.md`, que cuenta por qué `Frontend tests` dejó de ser un
  check.

El mapa de carencias de JUP-097 es documentación viva por decisión propia («envejece porque una
tarjeta lo actualiza»): se actualizan las filas de `/` y el resumen por capacidad, comprobando antes
en el código qué muestra hoy la pantalla principal.

### 5. `/overview-legacy` y los módulos sin uso no se retiran: se registran como hallazgos

La condición que JUP-095 puso para retirar la ruta puente («cuando exista un Overview real que la
sustituya») ya se cumple: `/` consume costes reales desde JUP-026 y JUP-055. Pero retirarla quita una
ruta, una página, un hook, una entrada de navegación y obliga a revisar las 30 líneas de 9 archivos
de pruebas que la nombran. Eso es un cambio de código con su ciclo de pruebas, no un cierre.

Se registran dos hallazgos nuevos y se corrige el comentario de `routes.tsx` para que diga lo que es
cierto: que la condición ya se cumple y dónde está el hallazgo.

- `RF-105-001`: retirar la ruta puente `/overview-legacy`, con el inventario de lo que arrastra.
- `RF-105-002`: módulos sin consumidor (`src/data/demo/executiveCostDashboard.ts` y
  `src/hooks/useCostKpis.ts`), con la referencia del test guardián que habría que ajustar.

Alternativa: retirarlos aquí. La tarjeta lo contempla y dice el coste: pasa a carril `standard`. Se
descarta salvo que el gate pre-código lo decida.

### 6. La deuda documental se absorbe aquí, en dos commits propios

Nadie abrió tarjeta para `RF-099-001` ni `RF-099-004` en nueve días y casi todos los archivos son de
esta épica. Se resuelven aquí.

**Enlaces (`RF-099-004`).** Un guion de un solo uso aplica las dos correcciones mecánicas que el
hallazgo ya describe (añadir el nivel que falta dentro de `archive/` y apuntar a la carpeta archivada
desde fuera), comprueba que cada destino corregido existe y no cambia ningún otro texto. El guion no
se versiona como herramienta: su texto y el del recorrido de comprobación quedan dentro de
`docs/evidence/JUP-105-validation.md`, de modo que quien valide pueda repetirlo. Resultado esperado:
64 enlaces corregidos y 2 falsos positivos sin tocar, identificados por archivo y línea.

**Menciones (`RF-099-001`).** Se sustituyen con las equivalencias que JUP-099 ya probó: la invocación
de Stryker sin archivo de configuración, la lista real de comandos `corepack pnpm --filter
@finops/frontend` en lugar del comprobador local, y redacción neutral para la excepción de las tareas
sin código y para la protección de las pruebas. El comentario de `vite.config.ts` se comprueba con
`build` y `test`.

**Regla para los registros archivados:** se cambia la referencia (una ruta o un comando que no se
puede reproducir), nunca un resultado, una cifra ni un veredicto. JUP-099 ya lo hizo con los
documentos de JUP-098. La evidencia lista por archivo cuántas líneas cambian.

**Prevención.** Que los enlaces vuelvan a romperse con cada archivado es un problema distinto de la
deuda ya acumulada. `RF-099-004` pasa a `Fixed` por la deuda y la falta de comprobación automática se
registra como `RF-105-003`. Esta misma tarjeta corrige sus enlaces al archivar, en el mismo paso.

Alternativa: dejar los dos hallazgos en `Open` con dueño y tarjeta pedida. Es válida según la tarjeta;
se descarta porque el coste de resolverlos es menor que el de volver a medirlos en otra tarjeta.

### 7. Disposición propuesta de los 21 hallazgos

| Hallazgo | Propuesta | Motivo |
| --- | --- | --- |
| `RF-093-001` | `Fixed` si confirman Alejandro y Paris; si no, `Open` con el nombre de quien falta | Solo espera esa confirmación desde JUP-103 |
| `RF-091-004` | `Fixed` | El dato codificado a mano ya no existe (JUP-026, #52; archivado en #78). Que no haya motor de ahorro es una capacidad ausente y pasa a `RF-091-003` |
| `RF-099-001`, `RF-099-004` | `Fixed` | Decisión 6 |
| `RF-091-003` | `Open`, reformulado | Quedan sin contrato las capacidades de las cuatro pantallas de demostración, más el cálculo de ahorro. Decisión de producto |
| `RF-095-002` | `Open`, reformulado | Pasa de cinco pantallas a cuatro y enlaza al recuento |
| `RF-104-004` | `Open`, con la frase sobre `/` corregida | Cambio de interfaz con sus pruebas |
| `RF-098-001` a `RF-098-004`, `RF-099-002`, `RF-099-003`, `RF-103-001` a `RF-103-005`, `RF-104-001` a `RF-104-003` | `Open` | Fuera del alcance de un cierre; cada uno recibe motivo y dueño |

El cierre de `RF-091-004` se comprueba antes en el código del backend (que `GET /billing/summary` no
devuelve importes fijos), no solo en la descripción del hallazgo.

**Dueño.** Trello es la fuente de verdad de los responsables, así que el backlog no asigna personas
por su cuenta. La columna `Owner` pasa de «Equipo Economicon» a decir quién da el siguiente paso: la
persona que aceptó el hallazgo en la revisión del pull request, o «decisión de producto del equipo»
cuando lo que falta es decidir y no ejecutar. Donde haga falta tarjeta, se pide al líder y se anota
«tarjeta pedida», sin inventar un número.

### 8. El estado final de la épica se declara en el punto 13 del spike

El punto 13 dice, en este orden: qué se migró (por fase, con su tarjeta); qué tarjetas se eliminaron
sin abrirse (CORS, resuelta por JUP-085; Docker del frontend, resuelta por JUP-049 y JUP-050); qué
tarjetas ajenas a la épica cambiaron el frontend mientras duraba (JUP-085, 026, 055, 057, 025 y 047);
qué quedó fuera; y qué decisiones de producto siguen abiertas, cada una con su hallazgo. Enlaza al
recuento de pantallas del README en lugar de repetirlo.

La casilla pendiente de JUP-092 («Enlazar el ADR desde el `design.md` de cada tarjeta de F2 y F3») se
marca con su comprobación: los `design.md` archivados de JUP-093, 094, 095, 097, 098 y 099 citan
ADR-0003.

### 9. ADR: no aplica uno nuevo

No se toma ninguna decisión de arquitectura. El endurecimiento de `allowJs` ejecuta la decisión 2 de
[ADR-0003](../../../../docs/adr/ADR-0003-frontend-typescript.md), ya aceptada, y se anota en su sección
de seguimiento, que es donde cada tarjeta ha ido dejando constancia. El texto de la decisión no se
edita. Los números de ADR siguen como estaban: el último en `develop` es ADR-0017 y el pull request
#73 reserva ADR-0018.

### 10. Sin ciclo Red/Green

La tarjeta cambia un valor de configuración, dos comentarios y documentación. No añade ni modifica
comportamiento que una prueba unitaria pueda cubrir. La verificación son los comandos reales con su
salida y el control positivo de la decisión 1. La excepción se deja escrita en `review.md`.

### 11. Orden de trabajo

1. Lo que tiene latencia primero: la consulta a Alejandro y a Paris sale al empezar.
2. Lo que nadie más toca: `tsconfig.json`, README del frontend, `routes.tsx`, mapa de carencias,
   evidencia de JUP-095 y los registros archivados.
3. Traer `develop`.
4. Los archivos compartidos al final: backlog y spike.
5. Batería completa, evidencia y `review.md`.

## Risks / Trade-offs

- [`allowJs: false` rompe una herramienta que lee `tsconfig.json` (Vite, Vitest, ESLint)] → La prueba
  en seco solo cubre `tsc`. El grupo de tareas ejecuta `lint`, `test` y `build` del frontend antes de
  seguir. Si algo falla, se revierte el valor y se registra con precisión por qué no puede
  endurecerse todavía, que es la salida que prevé el criterio 2 de la tarjeta.
- [El guion de enlaces corrige de más o cambia texto que no es un enlace] → Se ejecuta sobre un árbol
  limpio y se revisa el diff completo: solo deben cambiar destinos de enlace. Se compara el recuento
  antes y después (de 66 a 2).
- [Editar registros archivados altera la historia] → La regla de la decisión 6 limita el cambio a la
  referencia. El diff es el registro; la evidencia lo resume por archivo.
- [Alejandro o Paris no contestan a tiempo] → `RF-093-001` se queda en `Open` con el nombre de quien
  falta y la fecha de la consulta. No se da por confirmado.
- [`develop` avanza durante la tarjeta: se fusiona #66 o #69, o alguien toca el backlog o el spike] →
  Esos dos archivos se editan al final. Tras traer `develop` se repiten el recuento de pantallas, el
  recorrido de enlaces y la búsqueda de menciones.
- [El pull request toca muchos archivos (unos 40) y parece mayor de lo que es] → Commits separados por
  naturaleza: configuración, textos vivos, enlaces, menciones, backlog y spike. La descripción del
  pull request dice qué commits son mecánicos.
- [Cerrar `RF-091-004` puede leerse como «el ahorro está resuelto»] → La fila dice expresamente que lo
  resuelto es el dato ficticio y que el cálculo de ahorro sigue ausente, en `RF-091-003`.
- [Los hallazgos nuevos `RF-105-NNN` se quedan sin tarjeta, como les pasó a `RF-099-001` y
  `RF-099-004`] → Se piden al líder al abrir el pull request y el punto 13 del spike los enumera.
- [La batería de `test` no pasa con el comando literal desde la raíz] → Se ejecuta por mitades y con
  `TURBO_FORCE=true`, y la evidencia lo dice así; no se presenta como una ejecución única.

## Migration Plan

Cambio de configuración: un valor en `apps/frontend/tsconfig.json`. Se revierte con su commit, que va
separado de los de documentación. El resto son documentos y comentarios; se revierten por commit.

## Open Questions

- ¿Qué persona figura como dueño de cada hallazgo que sobrevive? Se resuelve con el equipo durante la
  tarjeta (decisión 7); mientras no haya respuesta, el hallazgo queda como «decisión de producto del
  equipo» o «tarjeta pedida». No cambia las tareas.
