## 1. Línea base y consulta al equipo

- [x] 1.1 Crear `docs/evidence/JUP-105-validation.md` con la cabecera (fecha, enlace a Trello, rama,
  commit base de `develop`) y registrar las medidas de partida con el comando de cada una: valor de
  `allowJs`, archivos JavaScript en `src/` y `tests/`, enlaces relativos rotos (66 en 26 archivos),
  menciones a configuración local con el patrón de `RF-099-001` (42 en 11 archivos) y número de
  hallazgos de la épica en `Open` (21). Incluir en la evidencia el texto del recorrido de enlaces,
  para que se pueda repetir sin nada que no esté en el repositorio. Hecho: sección «Línea base» de
  la evidencia. La medida corrigió una cifra de la propuesta: las menciones son 42, como decía la
  tarjeta, y no 41.
- [x] 1.2 Pedir a Alejandro y a Paris que ejecuten `corepack pnpm exec pnpm --version` y
  `corepack pnpm lint --force` desde la raíz de `develop`, en una consola externa, y que indiquen
  sistema operativo y resultado. Lo envía Victor. Anotar en la evidencia la fecha de la consulta.
  Hecho: Paris contestó el 2026-10-09 (el fallo no se reproduce en su máquina, sin haber necesitado
  `corepack enable`); Alejandro no contestó y figura como «no confirmado». `RF-093-001` no pasa a
  `Fixed` (se registra en 6.4).

## 2. Endurecer `allowJs`

- [x] 2.1 Cambiar `"allowJs": true` por `"allowJs": false` en `apps/frontend/tsconfig.json`, sin
  tocar ninguna otra línea. Hecho: diff de una línea.
- [x] 2.2 Ejecutar `corepack pnpm --filter @finops/frontend typecheck`, `lint`, `build` y
  `test -- --maxWorkers=1` y guardar la salida real de cada uno, con el número de pruebas. Si alguno
  falla por el cambio, revertir 2.1 y registrar con precisión por qué no puede endurecerse todavía.
  Hecho: los cuatro en verde; 53 archivos y 629 pruebas con un worker.
- [x] 2.3 Control positivo: crear un archivo temporal `.js` en `apps/frontend/src/` importado desde
  un `.ts` también temporal, ejecutar `typecheck`, comprobar que termina con error y guardar el
  mensaje; borrar los dos archivos y comprobar con `git status` que no queda rastro. Anotar el límite:
  un `.js` que nadie importa no lo detecta el compilador. Hecho: `TS7016` con `allowJs: false` y
  salida 0 con `true`; sin rastro.
- [x] 2.4 Anotar en la sección de seguimiento de `docs/adr/ADR-0003-frontend-typescript.md` que
  JUP-105 ejecutó el endurecimiento, con fecha y enlace a la evidencia. No editar el texto de la
  decisión. Hecho: viñeta «Hecho en JUP-105» tras la de F5.

## 3. Recuento de pantallas y textos vivos que nadie más toca

- [x] 3.1 Recontar las rutas contra `apps/frontend/src/routes.tsx` y, para cada una, comprobar en su
  página de dónde salen los datos y si la interfaz muestra un rótulo de demostración. Guardar la
  tabla y los comandos en la evidencia. Resultado esperado: 9 rutas bajo sesión más `/login`; 5 con
  datos del backend, 4 de demostración, 3 de ellas sin rótulo. Hecho: coincide con lo esperado;
  tabla en «Recuento de pantallas» de la evidencia.
- [x] 3.2 `apps/frontend/README.md`, sección «Rutas»: añadir las columnas de origen de datos y de
  rótulo de demostración, la fila de `/system-health` y la línea con fecha y commit de verificación.
  Revisar que las notas del mismo archivo sobre las pantallas de demostración coinciden con la tabla.
  Hecho: la nota de «Notas» ya coincidía y ahora remite a la tabla.
- [x] 3.3 `apps/frontend/src/routes.tsx`: corregir el comentario de cabecera. Debe decir que las
  pantallas ya no son «las 8 portadas», que `/overview-legacy` no es el único dashboard con datos
  reales y que la condición para retirarla ya se cumple, remitiendo a `RF-105-001`. Sin cambios en
  el código. Ejecutar `typecheck` y `lint` del frontend. Hecho: ambos con salida 0.
- [x] 3.4 `docs/planning/JUP-097-frontend-data-gap-map.md`: comprobar en
  `ExecutiveCostDashboard.tsx` qué datos muestra hoy `/` y actualizar sus filas, la nota del 27/09
  («pendiente de integración») y el resumen por capacidad. Enlazar al recuento del README. Hecho:
  la serie mensual (C1) y el desglose (C2) pasan a resueltos en `/`, el inventario (C7) a retirado y
  el ahorro a capacidad ausente en `RF-091-003`.
- [x] 3.5 `docs/evidence/JUP-095-validation.md`: añadir una nota fechada, sin reescribir las líneas
  25, 102 y 110, que diga que `Frontend tests` dejó de ser un check obligatorio el 19/09 y remita a
  `docs/governance/github-branch-protection.md`. Hecho: nota al inicio del documento, que añade las
  otras dos afirmaciones superadas (datos reales y CORS).
- [x] 3.6 Comprobar si `docs/architecture.md` y el `README.md` de la raíz afirman algo del frontend
  que ya no sea cierto (recomendación 7 del spike). Corregirlo o dejar escrito en la evidencia que no
  hay nada que cambiar. Hecho: `docs/architecture.md` tenía el recuadro de `GET /billing/summary`
  desfasado y se corrigió tras comprobarlo en el backend; el `README.md` de la raíz no necesita
  cambios.

## 4. Deuda documental: enlaces relativos (`RF-099-004`)

- [x] 4.1 Escribir el guion de un solo uso que aplica las dos correcciones del hallazgo (el nivel
  que falta dentro de `openspec/changes/archive/` y la ruta archivada desde fuera) y que comprueba
  que cada destino corregido existe. Guardar su texto en la evidencia. No se versiona como
  herramienta. Hecho: texto del guion y de su comprobación en la evidencia.
- [x] 4.2 Ejecutarlo sobre un árbol limpio y revisar el diff completo: solo cambian destinos de
  enlace, ningún otro texto. Repetir el recorrido de 1.1. Resultado esperado: de 66 a 2, y los 2 son
  los falsos positivos de `docs/evidence/JUP-099-validation.md` (líneas 505 y 793). Hecho: de 66 a
  2, los esperados; 64 líneas en 25 archivos y comprobación mecánica de que solo cambian destinos.
- [x] 4.3 Registrar en la evidencia el recuento por archivo de enlaces corregidos. Hecho.

## 5. Deuda documental: menciones a configuración local (`RF-099-001`)

- [x] 5.1 Sustituir las 42 menciones con las equivalencias que JUP-099 ya probó (ver `design.md`,
  decisión 6). En los registros archivados cambia solo la referencia, nunca un resultado, una cifra
  ni un veredicto. Hecho: 42 menciones en 11 archivos; donde no hay equivalente versionado la
  redacción es neutral y no se inventó ningún comando.
- [x] 5.2 `apps/frontend/vite.config.ts`: sustituir en el comentario la ruta local por una
  descripción neutral de la carpeta temporal del mutation testing. Ejecutar `build` y `test` del
  frontend. Hecho: `typecheck`, `lint` y `build` con salida 0; 53 archivos y 629 pruebas.
- [x] 5.3 Repetir la búsqueda de 1.1. Resultado esperado: 0 líneas con el patrón del hallazgo.
  Comprobar aparte que las menciones legítimas (el `review.md` de JUP-099 y la fila del backlog, que
  describen el hallazgo) siguen intactas. Registrar en la evidencia las líneas cambiadas por archivo.
  Hecho: 0 líneas; las 9 legítimas intactas; recuento por archivo en la evidencia.
- [x] 5.4 Ejecutar `corepack pnpm jup:cleanup:check` y `corepack pnpm repository:governance:test`.
  Hecho: `[OK] 930 archivos` y 13 de 13.

## 6. Hallazgos de la épica (archivo compartido: después de traer `develop`)

- [x] 6.1 Traer `develop` a la rama (lo ejecuta Victor). Comprobar si se fusionaron #66 o #69: si
  es así, repetir 3.1 y ajustar 3.2. Repetir el recorrido de enlaces y la búsqueda de menciones por
  si la fusión trae deuda nueva. Hecho: `develop` (`ceb6520`, con #83, #76, #72 y #82) fusionado sin
  conflictos en `ce1a87d`; #66 y #69 no están, el recuento no cambia; enlaces en 2 y menciones en 0.
- [x] 6.2 Comprobar en `apps/backend` que `GET /billing/summary` ya no devuelve importes fijos y que
  el ahorro es `null`, antes de proponer el cierre de `RF-091-004`. Guardar la comprobación. Hecho:
  lectura de `database.py` y `billing.py`; no se ejecutó el backend.
- [x] 6.3 `openspec/findings/backlog.md`: aplicar la disposición de la decisión 7 del `design.md` a
  los 21 hallazgos. Los que se cierran pasan a `Fixed` con su evidencia; los que sobreviven reciben
  motivo y quién da el siguiente paso. Reformular `RF-091-003`, `RF-095-002` y `RF-104-004`
  enlazando al recuento del README. Cada fila conserva su descripción original. Hecho: 3 `Fixed` y
  18 `Open`; los responsables son categorías (decisión o tarjeta), no personas.
- [x] 6.4 Registrar con la respuesta de 1.2 el resultado de `RF-093-001` por persona. Pasa a `Fixed`
  solo si confirman los dos; quien no haya contestado figura como «no confirmado». Hecho: `Open`;
  Paris no reproduce el fallo y Alejandro figura como no confirmado.
- [x] 6.5 Añadir `RF-105-001` (retirar la ruta puente `/overview-legacy`, con el inventario de lo que
  arrastra), `RF-105-002` (módulos sin consumidor) y `RF-105-003` (no hay comprobación automática de
  enlaces relativos). Añadir cualquier otro hallazgo que haya aparecido durante la tarjeta. Hecho:
  los tres; los comentarios desfasados de `Layout.tsx` van dentro de `RF-105-001`.
- [x] 6.6 Pedir al líder las tarjetas de Trello que necesiten los hallazgos que sobreviven y anotar
  «tarjeta pedida» donde corresponda, sin inventar números. Hecho por indicación del líder
  (2026-10-09): la petición se hace en Trello de forma independiente y esta rama no la comprueba.
  Cuatro hallazgos (`RF-104-001`, `RF-103-001`, `RF-103-002` y `RF-098-003`) dicen «tarjeta pedida»;
  ningún número consta en el repositorio.

## 7. Cerrar el spike (archivo compartido)

- [x] 7.1 `docs/spikes/frontend-migration.md`, fases F1 a F5: enlazar los changes archivados de
  JUP-090, JUP-091, JUP-092 y JUP-095; corregir el estado de JUP-099, JUP-103 y JUP-104 con su pull
  request y fecha de fusión; marcar la casilla pendiente de JUP-092 con su comprobación. Hecho:
  enlaces añadidos (también el de la reconciliación de JUP-095 con `develop`); JUP-099 (#54,
  2026-10-01), JUP-103 (#75, 2026-10-07 UTC) y JUP-104 (#79, 2026-10-07); la casilla de JUP-092 se
  marca con la salvedad de que el `design.md` archivado de JUP-097 cita ADR-0003 pero no lo enlaza.
- [x] 7.2 Sustituir `jup-0xx-checks-y-archive` por `jup-105-close-frontend-migration` y marcar sus
  tres casillas según lo verificado; la que no se cumpla del todo lleva su explicación. Hecho: dos
  casillas marcadas con su comprobación; la de la batería queda sin marcar con su explicación y se
  marca en 8.1; la revisión del equipo no es una casilla, porque es la del propio pull request.
- [x] 7.3 Añadir una nota fechada a las afirmaciones históricas de que `/overview-legacy` es el único
  dashboard con datos reales (líneas 231, 464 y 481), sin reescribirlas. Hecho: tres notas (puntos
  JUP-097, 7 y 8).
- [x] 7.4 Añadir el punto 13 de «Próximos pasos» con el estado final de la épica: qué se migró, las
  dos tarjetas eliminadas, las tarjetas ajenas que cambiaron el frontend, qué quedó fuera y qué
  decisiones de producto siguen abiertas, cada una con su hallazgo. Hecho, con las fases y sus pull
  requests, los hallazgos, las limitaciones conocidas y qué haría falta para darla por completa.
- [x] 7.5 Comprobar que no queda ningún marcador `jup-0xx` de tarjeta pendiente ni ninguna casilla
  sin marcar sin explicación (`git grep -n -e "jup-0xx" -e "\- \[ \]"` sobre el spike) y revisar el
  resultado línea a línea: el «Checklist operacional» es una plantilla y sus casillas no cuentan.
  Hecho: queda `jup-0xx-verificar-docker-compose` (tarjeta resuelta, que nunca tuvo número y lo dice
  su texto), la casilla de la batería (con su explicación) y la plantilla, que ahora lo declara.

## 8. Revisión y cierre

- [ ] 8.1 Ejecutar la batería completa desde la raíz: `corepack pnpm install --frozen-lockfile`,
  `corepack pnpm lint --force`, `corepack pnpm build --force`, `corepack pnpm typecheck --force`,
  `corepack pnpm run test "--filter=!@finops/frontend"` y
  `corepack pnpm run test --filter=@finops/frontend -- --maxWorkers=1` con `TURBO_FORCE=true` y el
  entorno virtual de Python activo, `corepack pnpm openspec:validate`,
  `corepack pnpm jup:check -- --change jup-105-close-frontend-migration` y
  `corepack pnpm jup:cleanup:check`. Guardar la salida real y decir en la evidencia que `test` se
  ejecutó por mitades. Con el resultado: marcar en `docs/spikes/frontend-migration.md` la casilla de
  esos comandos (F5) y contrastar con la batería las cifras del punto 13 del spike (629 pruebas en
  53 archivos, 0 archivos JavaScript, 21 hallazgos con 3 `Fixed` y 18 `Open`).
- [ ] 8.2 Completar `docs/evidence/JUP-105-validation.md`: trazabilidad de los nueve criterios de
  aceptación de la tarjeta con su evidencia, tabla de antes y después, y lo que no se validó y por
  qué.
- [ ] 8.3 Escribir `review.md`: resultado, decisiones, hallazgos, la excepción del ciclo Red/Green y
  que no aplica ADR nuevo.
- [ ] 8.4 Comprobar que ningún documento de la tarjeta cita configuración local de herramientas de
  asistencia y que los comandos escritos se pueden reproducir tal cual.
- [ ] 8.5 Tras la aprobación post-revisión, archivar el change sincronizando la spec
  `frontend-typescript-tooling` y corregir en el mismo paso los enlaces relativos de la tarjeta, que
  bajan un nivel al pasar a `openspec/changes/archive/`. Añadir en el spike (F5) el enlace al change
  archivado de JUP-105, que no se puso antes porque su carpeta lleva la fecha del archivado. Repetir
  el recorrido de enlaces: deben seguir siendo 2.
- [ ] 8.6 Traer `develop` y reverificar, abrir el pull request hacia `develop` con los cuatro roles
  en la descripción y registrar en la evidencia el enlace al pull request y a la ejecución de CI.
