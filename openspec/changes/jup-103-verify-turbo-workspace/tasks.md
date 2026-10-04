## 1. Línea base: reproducir y registrar la causa (antes de corregir nada)

- [x] 1.1 Crear `docs/evidence/JUP-103-validation.md` con la cabecera (fecha, enlace a Trello, rama,
  commit base de `develop`) y registrar el entorno de la máquina afectada: sistema operativo,
  versiones de Node, corepack y turbo, `where pnpm`, `npm ls -g --depth=0`, `pnpm --version` dentro y
  fuera del repositorio, `corepack pnpm --version`, contenido de `C:\Program Files\nodejs` relativo a
  pnpm y orden de ese directorio y de `%APPDATA%\npm` en el `PATH`. Hecho: sección «Máquina donde se
  reproduce» de la evidencia.
- [x] 1.2 Ejecutar desde la raíz `corepack pnpm lint`, `corepack pnpm build`, `corepack pnpm test` y
  `corepack pnpm typecheck` y guardar la salida real de cada uno: tareas lanzadas, error de versión
  y código de salida. Hecho: 0 de 4 en `lint`, `build` y `test` y 0 de 1 en `typecheck`. La
  repetición de `lint` pasó por `cache hit` de turbo (falso positivo) y se repitió con `--force`:
  por eso 2.3 y 7.1 usan `--force`.
- [x] 1.3 Ejecutar `corepack pnpm exec pnpm --version` y guardar la salida: es la reproducción sin
  turbo y el comando de diagnóstico que se va a documentar.
- [x] 1.4 Ejecutar los mismos cuatro scripts sin `corepack` (`pnpm lint`, `pnpm build`, `pnpm test`,
  `pnpm typecheck`) y guardar la salida. Confirma la decisión 1 del `design.md` y separa los fallos
  ajenos al gestor de paquetes: anotar cada tarea que falle por otro motivo, con su causa. Hecho: con
  `--force`, `lint`, `build` y `typecheck` pasan; `test` falla por módulos de Python sin instalar
  (backend, processor) y por timeouts en el frontend, ninguno por pnpm.
- [x] 1.5 Redactar en la evidencia la causa (decisión 1 del `design.md`) apoyada en las salidas de
  1.1 a 1.4, incluidas las dos afirmaciones del hallazgo original que resultan inexactas.

## 2. Corrección en la máquina afectada

- [ ] 2.1 Ejecutar `corepack enable` desde una consola con permisos de administrador. Si no es
  posible, aplicar la alternativa del `design.md` (riesgos) y dejar escrito cuál se usó. Lo hace
  quien usa la máquina; la decisión de desinstalar además el pnpm global es suya.
- [ ] 2.2 Comprobar en una consola nueva: `where pnpm` muestra primero el lanzador de corepack,
  `pnpm --version` da `9.0.0` dentro del repositorio y `corepack pnpm exec pnpm --version` da `9.0.0`
  con código de salida 0. Guardar las salidas.
- [ ] 2.3 Ejecutar desde la raíz `corepack pnpm lint --force`, `corepack pnpm build --force`,
  `corepack pnpm typecheck --force` y `corepack pnpm run test` con `TURBO_FORCE=true` (`pnpm test`
  es un comando propio de pnpm y no admite `--force`; `pnpm run test` sí reenvía las opciones). Para
  `test`, con el entorno virtual de Python activo y por separado, porque el frontend con los workers
  por defecto da timeouts en esta máquina (`RF-098-004`):
  `corepack pnpm run test --filter=@finops/frontend -- --maxWorkers=1` y
  `corepack pnpm run test "--filter=!@finops/frontend"`. Guardar la salida real de cada uno. La clave de la caché de turbo no depende
  del gestor de paquetes: un `cache hit` daría un falso positivo, como pasó en 1.2. Comprobar que
  cada tarea figura como `cache bypass, force executing`. Criterio: ninguna tarea termina con
  el error de versión de pnpm. Cualquier otro fallo se anota por tarea, con su causa, y se compara
  con lo anotado en 1.4.
- [ ] 2.4 Ejecutar `corepack pnpm install --frozen-lockfile` y comprobar con `git status` que no
  modifica `pnpm-lock.yaml` ni ningún otro archivo versionado.

## 3. Verificar `dev` y el grafo de turbo

- [ ] 3.1 Ejecutar `corepack pnpm exec turbo run build lint test typecheck dev --dry=json` y
  registrar por paquete las tareas y sus dependencias. Criterio: `@finops/frontend` tiene las cinco
  tareas.
- [ ] 3.2 Comprobar en `turbo.json` que `build` declara `dependsOn: ["^build"]` y registrar por qué
  hoy ninguna tarea tiene dependencias (ningún paquete del workspace depende de otro).
- [ ] 3.3 Con los servicios de aplicación de Docker Compose parados y la infraestructura que
  necesiten backend y processor levantada, y con el entorno virtual de Python activo (turbo usa el
  `python` del `PATH`), ejecutar `corepack pnpm dev` y registrar: que turbo inicia
  los cuatro procesos (frontend, backend, processor, Azure Cost API) y la respuesta de cada uno en su
  puerto (5173, 8000, 8001, 8002). Si alguno no queda sirviendo, anotar cuál y por qué, sin darlo por
  verificado.

## 4. Documentar el requisito previo en el repositorio

- [ ] 4.1 `README.md`: añadir `corepack enable` como paso por única vez en los requisitos de
  arranque, con la nota de la consola elevada en Windows, el comando de diagnóstico
  `corepack pnpm exec pnpm --version` y su resultado esperado, y qué hacer si hay un pnpm global de
  otra versión (incluida la salida de emergencia de invocar sin `corepack`).
- [ ] 4.2 `README.md`, bloque "Con Turborepo": sustituir `pnpm install` y `pnpm dev` por
  `corepack pnpm install --frozen-lockfile` y `corepack pnpm dev`. En "Comandos Principales", añadir
  una nota que remita al requisito previo e incluir `typecheck`, que falta en la lista.
- [ ] 4.3 Comprobar que el cambio de `README.md` no rompe los tests de gobierno del repositorio:
  `corepack pnpm repository:governance:test`, `corepack pnpm ci:check:test` y
  `corepack pnpm jup:cleanup:check`.

## 5. Confirmar con el resto del equipo

- [ ] 5.1 Pedir a Paris, Lucía y Alejandro que ejecuten `corepack pnpm exec pnpm --version` y
  `corepack pnpm lint` desde la raíz de `develop` y que indiquen sistema operativo y si tienen un
  pnpm global.
- [ ] 5.2 Registrar en la evidencia el resultado por persona, con fecha. Quien no haya contestado
  figura como "no confirmado"; no se da por validado.
- [ ] 5.3 Dejar escrito en la evidencia, en una frase, si el equipo tiene que hacer algo en sus
  máquinas y qué.

## 6. Cerrar el hallazgo y la fase F4 del spike

- [ ] 6.1 `openspec/findings/backlog.md`: pasar `RF-093-001` a `Fixed` con la causa, la corrección,
  las dos afirmaciones corregidas y el enlace a la evidencia. Si la corrección no funcionó en 2.3,
  dejarlo `Open` con la causa precisa y lo que se probó.
- [ ] 6.2 Registrar como hallazgos nuevos (`RF-103-NNN`) los fallos ajenos al gestor de paquetes que
  hayan aparecido en 1.4, 2.3 o 3.3 y sean del repositorio.
- [ ] 6.3 `docs/spikes/frontend-migration.md`, fase F4: marcar `jup-0xx-verificar-docker-compose`
  como resuelta por JUP-049 y JUP-050 sin tarjeta propia, sustituir
  `jup-0xx-verificar-turbo-workspace` por `jup-103-verify-turbo-workspace` con sus casillas marcadas
  según lo verificado, y dejar F4 como fase completa.

## 7. Revisión y cierre

- [ ] 7.1 Ejecutar la batería completa desde la raíz, sin sustitutos:
  `corepack pnpm install --frozen-lockfile`, `corepack pnpm lint --force`,
  `corepack pnpm build --force`, `corepack pnpm typecheck --force`, y `corepack pnpm run test` con
  `TURBO_FORCE=true` en las dos mitades descritas en 2.3, con el entorno virtual de Python activo, `corepack pnpm openspec:validate`,
  `corepack pnpm jup:check -- --change jup-103-verify-turbo-workspace` y
  `corepack pnpm jup:cleanup:check`.
- [ ] 7.2 Completar `docs/evidence/JUP-103-validation.md`: trazabilidad de los siete criterios de
  aceptación de la tarjeta con su evidencia, tabla de antes y después, lo que no se validó y por qué.
- [ ] 7.3 Escribir `review.md`: resultado, decisiones, hallazgos, la excepción del ciclo Red/Green
  (sin código de producto) y que no aplica ADR.
- [ ] 7.4 Comprobar que ningún documento versionado de la tarjeta cita configuración local de
  herramientas de asistencia y que los comandos escritos se pueden reproducir tal cual.
- [ ] 7.5 Tras la aprobación post-revisión, archivar el change y corregir en el mismo paso los
  enlaces relativos, que bajan un nivel al pasar a `openspec/changes/archive/`.
- [ ] 7.6 Abrir el pull request hacia `develop` y registrar en la evidencia el enlace al PR y a la
  ejecución de CI en verde (criterio 3 de la tarjeta).
