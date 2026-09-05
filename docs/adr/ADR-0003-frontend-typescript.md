# ADR-0003: Adopción de TypeScript en el frontend

- Estado: Accepted
- Fecha: 2026-09-02
- Tarjeta Trello: [JUP-092](https://trello.com/c/R5t2PL2F/84-jup-092-adr-de-adopción-de-typescript-en-el-frontend)
- OpenSpec relacionado: `jup-092-frontend-typescript-adr`
- Sustituye a: ninguno
- Sustituido por: ninguno

## Contexto

El spike de migración del frontend ([docs/spikes/frontend-migration.md](../spikes/frontend-migration.md))
fija la adopción de TypeScript en `apps/frontend` como su decisión número 1, calificándola de
"transversal y duradera" porque afecta tooling, build, lint y todas las tareas futuras del frontend.
[docs/adr/README.md](README.md) exige ADR para exactamente este tipo de decisión: patrones
compartidos que afectan a varios módulos o tareas futuras.

El punto de partida, verificado en JUP-090 y JUP-091 antes de esta tarjeta, no es el que el spike
supuso inicialmente:

- **El destino** (`apps/frontend`) es JavaScript con JSX. No declara `typescript` ni paquetes de
  tipos; no hay `tsconfig.json` en ningún punto del repo.
- **El origen** (Economicon) llega en TSX, pero **tampoco tiene verificación de tipos**: no declara
  `typescript` entre sus 61 dependencias (inventario de JUP-091) ni incluye `tsconfig.json`. Su TSX
  lo transpila esbuild sin comprobar nada.

Adoptar TypeScript no es, por tanto, "conservar lo que trae el origen": es **introducir verificación
de tipos donde no existe en ningún lado**, y sería el primer código tipado del repositorio en el lado
JavaScript — backend y processor están en Python.

Dos hechos adicionales, verificados directamente sobre el repo, condicionan la decisión:

- `apps/frontend` acumula **49 violaciones de `react/prop-types`** (recuento reproducido en esta HU
  con `pnpm lint`), el motivo por el que su lint no es check obligatorio de CI
  ([docs/governance/github-branch-protection.md](../governance/github-branch-protection.md),
  finding `RF-082-002` en `openspec/findings/backlog.md`). TypeScript sustituye a `prop-types` como
  mecanismo de validación de props.
- `apps/frontend` no tiene tests: su script `test` es un `echo` sin tooling real.

Sin esta decisión resuelta, la tarjeta de tooling de F2 (`jup-0xx-configurar-typescript`) no puede
instalar dependencias ni crear `tsconfig` sin saber qué nivel de rigor se exige, cómo convive con el
JavaScript existente durante la migración por slices, y qué ocurre con el lint actual.

## Decisión

Se adopta TypeScript en `apps/frontend` con las siguientes cuatro decisiones, aprobadas por el
equipo en el gate pre-código de JUP-092:

**1. Nivel de rigor: `strict: true` desde el inicio.**
El frontend se reemplaza por completo (estrategia de reemplazo total del spike); no hay deuda
JavaScript heredada que migrar de forma gradual. El momento más barato para exigir rigor es antes de
escribir el código nuevo, no después de portarlo sin tipos y retrofitear `strict` sobre él.

**2. Convivencia con JavaScript: `allowJs: true` durante la migración, `false` al cerrar F5.**
El spike prohíbe explícitamente el "big bang" y exige avanzar por slices verificables. Con
`allowJs: false` desde el primer commit, el primer slice migrado rompería el build de todo el
JavaScript aún sin portar. La tarjeta de cierre de F5 endurece la opción a `false` una vez no quede
JavaScript en `src/`.

**3. CI: type-check como check obligatorio; `RF-082-002` se cierra cuando los archivos afectados
migren a `.tsx`, no al terminar F2.**
El type-check debe correr en CI — de lo contrario `strict` es solo una anotación decorativa sin
consecuencia. Respecto a las 49 violaciones de `react/prop-types`: la vía elegida **no es arreglarlas
una a una**, sino que la regla deja de aplicar sobre los archivos ya tipados. `prop-types` es
validación de tipos en tiempo de ejecución; TypeScript la sustituye en tiempo de compilación con
garantías más fuertes. Mantener ambas sería redundante — pero solo una vez que TypeScript cubre
efectivamente ese archivo.

**Corrección de consistencia (revisión de PR, 2026-09-04):** las 49 violaciones reproducidas viven en
**9 archivos `.jsx`**. F2 desactiva `react/prop-types` únicamente para `.ts`/`.tsx` en
`eslint.config.js` — no renombra ni migra ningún archivo, así que esos 9 `.jsx` siguen sujetos a la
regla tras F2, y `pnpm lint` seguirá reportando las mismas 49 violaciones. Desactivar la regla también
para `.jsx` perdería la única validación de props que existe hoy, antes de que TypeScript la
sustituya de verdad. Por tanto: **`RF-082-002` permanece abierto hasta que F3 (o la tarjeta de cierre
de F5) migre esos 9 componentes concretos a `.tsx` y el type-check cubra efectivamente sus props.**
No se cierra como efecto colateral de F2.

**4. Ubicación del `tsconfig`: a nivel de `apps/frontend`, no compartido.**
`packages/shared-config` (`@finops/shared-config`) existe, pero hoy solo contiene un `index.js` con
metadatos del workspace. `apps/frontend` sería el **único** paquete TypeScript del repositorio —
backend y processor son Python. Extraer una configuración base compartida para un solo consumidor es
abstracción prematura. Si en el futuro aparece un segundo paquete TypeScript en el monorepo, se
extraerá entonces un `tsconfig.base.json` a `shared-config`; esta decisión no lo descarta, solo lo
pospone hasta que haya un segundo consumidor real.

## Consecuencias

**Se vuelve más fácil:**

- Detectar en tiempo de compilación errores que hoy solo aparecerían en runtime o en revisión manual:
  props mal pasadas, contratos de API mal consumidos, `null`/`undefined` no manejados.
- Refactorizar con confianza a medida que crece `apps/frontend`, con el compilador señalando cada
  punto que rompe un cambio de tipo.
- Documentar contratos de datos (props de componentes, forma de las respuestas del backend) de forma
  ejecutable, no solo en comentarios o en el README.

**Se vuelve más difícil:**

- El primer build con `strict: true` tendrá que resolver errores de tipo en código que nunca se ha
  verificado: tanto el JSX del destino como el TSX del origen. El volumen de ese trabajo es
  desconocido hasta que se intente.
- La curva de aprendizaje de TypeScript recae sobre un equipo que hoy trabaja en JavaScript puro en
  el frontend (backend y processor son Python, sin experiencia de tipado estático compartida).
- Mantener `allowJs: true` durante la migración exige disciplina: cualquier archivo `.jsx` nuevo debe
  tratarse como deuda temporal explícita, no como alternativa permanente al `.tsx`.

**Se vuelve más arriesgado:**

- El coste real de `strict: true` depende de una decisión que no es de esta tarjeta: `RF-091-002`
  (adoptar o descartar shadcn/ui en F2). Si se adopta, se tipa una superficie mucho mayor —del orden
  de 26 primitivos Radix— que si se descarta y se resuelve con los ~10 paquetes que hoy sostienen lo
  que renderiza el origen (inventario de JUP-091).
- Cerrar `RF-082-002` por obsolescencia, en vez de corregir las 49 violaciones, deja sin resolver
  cualquier problema real de props que esas violaciones señalaran. TypeScript debe cubrir
  efectivamente esos casos en F2/F3; si algún caso queda sin tipar, se pierde la única señal que hoy
  existía sobre él.
- Este ADR fija el criterio de escape: si el coste de `strict: true` desborda la tarjeta de F3, no se
  desactiva en silencio. Se documenta el desbordamiento y se redacta un ADR nuevo que supersede a
  éste, dejando trazabilidad de por qué cambió la decisión.

## Alternativas consideradas

- **Seguir en JavaScript, sin adoptar TypeScript.** Evitaría toda la curva de aprendizaje y el coste
  de tipar el TSX del origen. Descartada: el spike ya fija la adopción como decisión de la épica, no
  como algo a validar aquí; y renunciar a tipos en un frontend que va a crecer con auth, tenant,
  ingesta y chat del asistente deja sin red de seguridad justo las áreas con más superficie de error
  (contratos con el backend, estado de sesión).
- **JSDoc + `checkJs`, sin migrar a `.tsx`.** Permite type-checking sobre JavaScript existente sin
  cambiar extensión de archivo ni sintaxis, con menor fricción de adopción. Descartada como opción
  permanente: el origen ya llega en TSX y forzar su conversión a JSDoc sería trabajo adicional sin
  beneficio, mientras que JSDoc ofrece una experiencia de tipado más pobre (sin genéricos cómodos, sin
  inferencia tan fuerte) que TypeScript nativo para un frontend que va a crecer. Queda como opción
  válida únicamente para archivos `.jsx` temporales que convivan bajo `allowJs` durante la migración,
  no como estrategia final.
- **Adopción gradual con `strict: false` y endurecimiento progresivo.** Reduciría el volumen de
  errores que hay que resolver de golpe. Descartada como decisión de partida: al ser un reemplazo
  completo del frontend, no hay código productivo en producción que proteger de una migración
  disruptiva; el coste de empezar laxo y endurecer después —con más superficie ya escrita sin
  tipos— es mayor que exigir `strict` desde el primer archivo. El ADR reconoce en "Consecuencias"
  que este es el riesgo que más puede obligar a revisar la decisión.

## Evidencia y seguimiento

**Evidencia verificada en JUP-092:**

- Ningún `tsconfig.json` existe en el repositorio (búsqueda completa del árbol).
- `apps/frontend` acumula exactamente **49 violaciones de `react/prop-types`**, reproducidas con
  `pnpm lint` el 2026-09-02.
- `apps/frontend/package.json` declara `"test": "echo \"No frontend tests configured yet\""`: no hay
  tests reales que romper al introducir tipos.
- El origen no declara `typescript` entre sus 61 dependencias ni incluye `tsconfig.json`
  (`docs/planning/JUP-091-economicon-source-inventory.md`).
- `packages/shared-config` existe pero solo contiene `index.js` con metadatos del workspace; ningún
  otro paquete del monorepo usa TypeScript hoy.

**Seguimiento — tareas que ejecutan esta decisión:**

- F2, `jup-0xx-configurar-typescript`: instalar `typescript`, `@types/react`, `@types/react-dom`;
  crear `tsconfig.json` con `strict: true` y `allowJs: true`; migrar `eslint.config.js` al parser de
  TypeScript y desactivar `react/prop-types` para `.ts`/`.tsx`. Debe citar este ADR en su `design.md`.
- F2, `jup-0xx-reconciliar-package-json`: la superficie real a tipar depende de `RF-091-002`
  (adopción o descarte de shadcn/ui); este ADR no la prejuzga.
- F3, `jup-0xx-portar-codigo-fuente` y `jup-0xx-reconciliar-capa-api`: primer código que se escribe ya
  bajo `strict: true`; **debe migrar a `.tsx` los 9 archivos `.jsx` hoy señalados por
  `react/prop-types` (o los que los sustituyan)**, dado que la regla solo se desactiva para
  `.ts`/`.tsx`. Debe citar este ADR en su `design.md`.
- F5, tarjeta de cierre: endurecer `allowJs` a `false` una vez no quede JavaScript en `src/`;
  confirmar en ese punto que no queda ningún `.jsx` con violaciones pendientes.
- `openspec/findings/backlog.md`: `RF-082-002` se anota con la resolución prevista al aceptar este
  ADR y **permanece `Open`** hasta que F3 (o el cierre de F5) migre esos archivos a `.tsx` con
  cobertura real de tipos — no se cierra al desactivarse la regla en F2.

**Revisión:** si el coste de `strict: true` desborda la tarjeta de F3 (ver "Consecuencias"), este ADR
se supersede por uno nuevo; no se edita el aceptado ni se relaja la configuración sin ese registro.

**Aprobación:** las cuatro decisiones quedaron aprobadas en el bloque `Human Approval` del gate
pre-código de JUP-092 (`Approval type: pre-code`, `Decision: approved`, Victor, 2026-09-02), que
enumera cada una con su motivo. Ese registro se toma como la aprobación del equipo que exige
`docs/adr/README.md` para pasar de `Proposed` a `Accepted`.
