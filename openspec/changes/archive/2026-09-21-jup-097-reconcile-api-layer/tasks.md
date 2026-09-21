> Cada grupo termina en un punto parable: la aplicación arranca y la batería pasa. Al cerrar cada
> grupo se propone commit antes de empezar el siguiente. Ciclo Red/Green con Vitest en los grupos que
> tocan código de producto (2, 3, 4). Sin `any` nuevo ni `@ts-ignore` (ADR-0003).

## 1. Auditoría de contratos

- [x] 1.1 Levantar el backend (`docker compose up -d backend`) y confirmar `GET /health` desde fuera
      del navegador, dejando constancia del comando exacto.
- [x] 1.2 Extraer de `apps/backend/app/api/routes/` y `apps/backend/app/schemas/` la referencia real
      de los 10 contratos: dirección, método, cuerpo esperado y `response_model`.
- [x] 1.3 Comparar cada una de las 10 operaciones de `services/api.ts` con esa referencia y anotar
      dirección, método y cuerpo. Registrar el resultado operación por operación.
- [x] 1.4 Obtener una respuesta real de cada contrato contra el backend en ejecución (seed
      `operator@example.com` / `secret`) y contrastar su forma con `services/contracts.ts`, campo a
      campo. Es el paso que detecta la deriva que la lectura de código no ve (decisión 1).
- [x] 1.5 Consolidar la auditoría en `review.md`: tabla operación → contrato → veredicto. Dejarla
      escrita aunque el resultado sea cero desviaciones.
- [x] 1.6 Contrastar `apps/frontend/README.md` con el resultado y anotar qué haya que corregir allí
      (el backend manda sobre el README, decisión 1).

## 2. Corrección de las desviaciones encontradas

- [x] 2.1 **Red:** escribir las pruebas que fijan, en el límite HTTP (`fetch` sustituido), la forma
      correcta de cada operación desviada en 1.3/1.4. Demostrar el estado Red.
- [x] 2.2 **Green:** corregir `services/api.ts` y/o `services/contracts.ts` hasta que esas pruebas
      pasen, sin tocar el diseño de `fetchJson` (non-goal).
- [x] 2.3 Si alguna desviación solo puede corregirla el backend, **no corregirla aquí**: registrarla
      como finding nuevo en `openspec/findings/backlog.md` con la capacidad nombrada.
- [x] 2.4 Aplicar al README las correcciones anotadas en 1.6.
- [x] 2.5 Si la auditoría no encontró ninguna desviación, dejar este grupo explícitamente cerrado en
      `review.md` con esa constancia, en vez de marcarlo sin explicación.

## 3. RF-090-003: conectar `fetchProfile`

- [x] 3.1 **Red:** prueba de que, con sesión persistida y token válido, el armazón expone la
      identidad **devuelta por el servidor** y no la guardada en `localStorage`. Demostrar Red.
- [x] 3.2 **Red:** prueba de que, con sesión persistida cuyo token el servidor rechaza, se limpia la
      sesión y se redirige al acceso por el camino de fallo ya existente (`handleLogout`).
- [x] 3.3 **Green:** invocar `fetchProfile` en `SessionGate` al arrancar con sesión recuperada y usar
      su respuesta como identidad del `Outlet context`, respetando la frontera de la decisión 2: sin
      tocar login, persistencia, guard ni semántica de logout.
- [x] 3.4 Verificar que la petición se emite junto al bootstrap de tenants y no en serie después
      (decisión 2, coste aceptado).
- [x] 3.5 Ejecutar mutación sobre lo tocado y remediar los mutantes supervivientes con más pruebas.
- [x] 3.6 Actualizar `RF-090-003` en `openspec/findings/backlog.md` a `Fixed`, citando la decisión 2
      del `design.md` como motivo.
- [x] 3.7 **Parada de control:** si conectar `/me` exigiera rediseñar la sesión, detenerse y
      reconsiderar con Victor antes de continuar (riesgo declarado en el diseño).

## 4. Capa de acceso única

- [x] 4.1 Enumerar todo punto del frontend que emita peticiones de red y confirmar que todos
      pertenecen a `services/api.ts`. Registrar el comando y su salida.
- [x] 4.2 **Red/Green:** si 4.1 encuentra algún acceso fuera de la capa, cubrirlo con prueba y
      moverlo dentro de `services/api.ts`.
- [x] 4.3 Confirmar que ninguna dirección de backend queda fijada en el código de las pantallas y que
      la base sigue tomándose de `VITE_API_BASE_URL`.
- [x] 4.4 **Red/Green:** prueba de que una petición a un contrato autenticado transporta credencial y
      ámbito de cliente, y de que sin ámbito seleccionado no se emite petición a un contrato que lo
      exija.

## 5. Estados observables de las pantallas servidas

- [x] 5.1 **Red:** pruebas de carga, de fallo comunicado (no disfrazado de vacío) y de reconsulta al
      cambiar de ámbito, sobre `/overview-legacy`, la única ruta con datos reales. Demostrar Red.
- [x] 5.2 **Green:** ajustar `useDashboardData` y/o `DashboardPage` hasta que pasen, sin cambiar de
      origen de datos.
- [x] 5.3 Confirmar que en ningún instante se presenta el dato del ámbito anterior como propio del
      nuevo tras un cambio de ámbito.
- [x] 5.4 Ejecutar mutación sobre lo tocado y remediar supervivientes.

## 6. Mapa de carencias por pantalla

- [x] 6.1 Determinar, para cada una de las 5 pantallas de coste, qué capacidad de backend concreta
      necesitaría, apoyándose en `RF-091-003` y en el inventario de JUP-091.
- [x] 6.2 Ampliar el comentario "DATOS DE DEMOSTRACION (sustituibles)" de cada módulo de
      `src/data/demo/` nombrando esa capacidad ausente (decisión 3).
- [x] 6.3 Crear `docs/planning/JUP-097-frontend-data-gap-map.md` con la tabla pantalla → dato →
      capacidad ausente → finding relacionado.
- [x] 6.4 Actualizar `RF-095-002` en el backlog: refinado con el mapa, **permanece `Open`**,
      apuntando a la decisión de épica sobre `RF-091-003`.
- [x] 6.5 Confirmar que `RF-091-003` y `RF-091-004` siguen `Open` **sin cambio**: ningún archivo de
      `apps/backend/**` puede aparecer en el diff de la rama.

## 7. Limpieza de referencias obsoletas

- [x] 7.1 Corregir el comentario de `src/routes.tsx` que cita "JUP-096" como la tarjeta que conectará
      el Overview.
- [x] 7.2 Reafirmar en ese mismo comentario que `/overview-legacy` se conserva, con dueño explícito y
      la condición de retirada (que exista un Overview real que la sustituya).
- [x] 7.3 Sustituir en `docs/spikes/frontend-migration.md` el placeholder
      `jup-0xx-reconciliar-capa-api` por el slug real `jup-097-reconcile-api-layer` y marcar sus
      tareas según lo realmente hecho.
- [x] 7.4 Anotar en el spike que la primera tarea listada para esta tarjeta ("portar `services/api.*`
      a TS") la había cerrado ya JUP-095, para que el registro no quede engañoso.

## 8. Verificación y cierre

- [x] 8.1 Batería completa: `pnpm openspec:validate`, `pnpm lint`, `pnpm test`, `pnpm build`,
      `pnpm install --frozen-lockfile`. Registrar salidas.
- [x] 8.2 `pnpm jup:check -- --change jup-097-reconcile-api-layer` y `pnpm jup:cleanup:check`.
- [x] 8.3 Crear `docs/evidence/JUP-097-validation.md` con los comandos exactos y sus resultados,
      incluida la verificación directa contra el backend del grupo 1.
- [x] 8.4 Dejar declarado en la evidencia que el E2E en navegador **queda pendiente** por
      `RF-095-001`/`RF-087-001`, sin presentarlo como verificado (decisión 5).
- [x] 8.5 Cerrar `review.md`: auditoría, desenlace de `RF-090-003`, mapa de carencias, findings
      nuevos y constancia de que no se requiere ADR nuevo (decisión 6).
- [x] 8.6 Verificar que el diff de la rama no toca `apps/backend/**` ni `src/data/demo/**` más allá
      de los comentarios de 6.2.
- [ ] 8.7 Abrir el pull request hacia `develop` y solicitar revisión.
