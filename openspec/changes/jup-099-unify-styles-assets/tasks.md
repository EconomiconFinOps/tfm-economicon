> Cada grupo termina en un punto parable: la aplicación arranca y la batería pasa (salvo los tests
> guardianes, que se escriben en Red en el grupo 3 y van pasando a verde archivo a archivo en los
> grupos 4-8). Al cerrar cada grupo se propone commit antes de empezar el siguiente. Sin `any` nuevo
> ni `@ts-ignore` (ADR-0003). Refactor visual, no rediseño: cada token reproduce el valor exacto que
> sustituye (decisión 1 de `design.md`). Sin mutación de Stryker en los grupos de migración, por la
> excepción justificada en la decisión 5; se registra en `review.md` sin afirmar cobertura.

## 1. Línea base (antes de tocar producto)

- [ ] 1.1 Ejecutar la suite del frontend en la rama recién creada y registrar en `review.md` el conteo
      en verde como línea base (sustituto `corepack pnpm --filter @finops/frontend test` mientras
      RF-093-001 siga abierto; dejar constancia de cuál se usó).
- [ ] 1.2 Registrar en `review.md` el inventario de partida con los comandos de conteo exactos: 241
      hexadecimales en 14 `.tsx`, 4 en `src/data/demo/`, 229 utilidades de paleta en 16 `.tsx`, las 3
      menciones a `main.css` y los tokens de `theme.css`.
- [ ] 1.3 Preparar el proyecto temporal de captura fuera del repositorio (Playwright + Chromium +
      `pixelmatch`) y el guion de la decisión 6: build de producción, `vite preview`, viewport
      1440×900, API simulada con `page.route` desde `tests/fixtures.ts`, espera fija para Recharts.
- [ ] 1.4 Capturar la referencia "antes" de las 9 pantallas (`/`, `/operational`, `/cuts`,
      `/anomalies`, `/recommendations`, `/ingest`, `/assistant`, `/overview-legacy`, `/login`) y del
      aviso de sesión expirada, sobre `688fe2d`. Capturar dos veces seguidas y comprobar 0 píxeles de
      diferencia entre ambas pasadas (el guion es determinista) antes de dar la referencia por buena.

## 2. Arrastre de JUP-098 (documentación, un commit por tarea citando JUP-098)

- [ ] 2.1 Victor pregunta a Lucía, con el enlace al log del job "Frontend build", a qué se refería con
      "los tests del frontend no corren en CI". Registrar la respuesta en `review.md`.
- [ ] 2.2 Registrar `RF-098-004` en `openspec/findings/backlog.md`: fallos por el límite de 1 s de
      `findBy`/`waitFor` con suites en paralelo o máquina cargada (tenant-switching, ingestion,
      conversations, test 4.1 de JUP-098), que pasan en aislamiento y con
      `--poolOptions.threads.maxThreads=1`; arreglo posible `configure({ asyncUtilTimeout: 3000 })` en
      `src/test/setup.ts` como decisión de equipo. Sin afirmar nada sobre CI salvo lo que confirme
      la tarea 2.1. No se corrige aquí.
- [ ] 2.3 Sustituir las 9 referencias a configuración local del agente en
      `docs/evidence/JUP-098-validation.md` (líneas 93, 120, 126) y en
      `openspec/changes/archive/2026-09-27-jup-098-reconcile-auth-session/review.md` (líneas 34,
      48-52, 87, 95, 325) según la decisión 9 (Stryker sin archivo de configuración, lista real de
      comandos, redacción neutral). Verificar con búsqueda que no queda ninguna.
- [ ] 2.4 Corregir los 3 enlaces rotos por archivados (`docs/spikes/frontend-migration.md` líneas 185
      y 206; enlace a la review de JUP-085 en `openspec/findings/backlog.md`) para que apunten a
      `openspec/changes/archive/<fecha>-<change>/`, y eliminar la fila duplicada de `RF-090-003`.
      Verificar que todos los enlaces relativos del backlog y del spike resuelven.
- [ ] 2.5 Con autorización de Victor para editar tests protegidos, reescribir con redacción neutral
      los 10 comentarios de test que citan el hook o la configuración local del harness, sin tocar
      aserciones ni código. Restaurar la protección y confirmar que la suite sigue igual que en 1.1.

## 3. Tests guardianes en Red

- [ ] 3.1 **Red:** `src/test/color-tokens.guard.test.ts` (decisión 5): un caso por archivo de
      `src/**/*.tsx` y `src/data/**/*.ts` sin tests; falla con archivo y valor ante un hexadecimal de
      color o una utilidad de la paleta de Tailwind fuera de la lista de excepciones (el `<style>`
      del documento de exportación de `ExportButton` y el velo `bg-black/50` de
      `src/components/ui/dialog.tsx`, decisión 5). Demostrar Red en cada archivo con colores
      literales y verde en los que no tienen ninguno.
- [ ] 3.2 **Red:** `src/test/theme-palette.test.ts` sustituye a `src/test/index-html-dark-scope.test.ts`
      (con autorización de Victor): sin bloque `.dark`, cada token de color definido una vez, cada
      `var(--x)` de `@theme inline` apunta a un token definido, cada `--color-*` tiene consumidor en
      `src/` (caso separado, pasará a verde en el grupo 8) y `<html>` sin clase de tema. Demostrar
      Red.

## 4. Paleta única en el tema

- [ ] 4.1 **Green:** reescribir `src/styles/theme.css` con la tabla de la decisión 1: todos los tokens
      en `:root` con valores exactos (los `v4` copiados de `tailwindcss/theme.css` 4.3.3), alias con
      `var(--…)`, exposición en `@theme inline`, sin bloque `.dark`; `@custom-variant dark (&);`
      (decisión 2). Tokens no cromáticos y `@layer base` sin cambios.
- [ ] 4.2 **Green:** quitar `class="dark"` de `index.html`.
- [ ] 4.3 Verificar que los casos estructurales de `theme-palette.test.ts` pasan (el de consumidores
      sigue en Red) y que lint, typecheck, test (salvo guardianes) y build están en verde.

## 5. Migración del armazón y componentes compartidos

- [ ] 5.1 **Green:** `src/layouts/Layout.tsx` y `src/layouts/SessionGate.tsx` a utilidades de token
      (decisión 4).
- [ ] 5.2 **Green:** `src/components/{ExportButton,MetricCard,SectionCard,StatusPill}.tsx` a tokens;
      el `<style>` del documento de exportación queda como excepción declarada.
- [ ] 5.3 Extraer la constante compartida del `contentStyle` de los tooltips de Recharts con
      `var(--…)` (decisión 4), aún sin consumidores si las gráficas se migran en el grupo 7.
- [ ] 5.4 Eliminar las menciones a `main.css` de los comentarios de `MetricCard`, `SectionCard` y
      `StatusPill`, y comprobar con búsqueda que no queda ninguna referencia al sistema anterior en
      `apps/frontend`.
- [ ] 5.5 Guardián en verde para estos 6 archivos; resto de la suite sin regresión.

## 6. Migración de las pantallas conectadas al backend

- [ ] 6.1 **Green:** `LoginPage.tsx` (incluido el aviso de sesión expirada: `text-warning`),
      `IngestPage.tsx`, `ConversationsPage.tsx` y `DashboardPage.tsx` a tokens.
- [ ] 6.2 Guardián en verde para estos 4 archivos; las pruebas de sesión, ingesta, conversaciones y
      `/overview-legacy` siguen en verde sin editarse.

## 7. Migración de los dashboards de demostración

- [ ] 7.1 **Green:** `ExecutiveCostDashboard.tsx`, `OperationalCostDashboard.tsx`,
      `ExecutiveCutDashboard.tsx`, `AnomaliesPanel.tsx` y `RecommendationsPanel.tsx`: clases a tokens,
      `fill`/`stroke` a `var(--chart-*)`, tooltips a la constante compartida.
- [ ] 7.2 **Green:** `src/data/demo/executiveCostDashboard.ts` a `var(--chart-N)`.
- [ ] 7.3 Resolver `#8884d8` según la decisión 1 (eliminar si no se pinta; si se pinta, `chart-*`).
- [ ] 7.4 Guardián en verde en todos los archivos; ninguna excepción más allá de las declaradas en
      `review.md` una a una.

## 8. Verificación visual, propagación y tokens sin consumidor

- [ ] 8.1 Capturar las 9 pantallas y el aviso con el mismo guion de 1.4 y comparar con `pixelmatch`
      (umbral 0). Registrar en `review.md` los píxeles distintos por pantalla y explicar cada
      diferencia no nula; corregir las que no sean aceptables.
- [ ] 8.2 Demostración de propagación (criterio 2): cambiar temporalmente `--primary`, reconstruir,
      recapturar, registrar qué pantallas cambian y que ningún archivo de pantalla cambió; revertir.
- [ ] 8.3 Retirar los tokens sin consumidor (decisión 3) y dejar en verde el caso de consumidores de
      `theme-palette.test.ts`. Registrar en `review.md` qué se retiró y qué se conserva y por qué.
- [ ] 8.4 Registrar en `review.md` los pares de tonos casi iguales que no se consolidaron (`slate-400`
      v3/v4, `green-400`/`emerald-400`…) como candidato a tarjeta propia, y en el backlog si el equipo
      lo quiere como finding.

## 9. Licencias, ADR y documentación

- [ ] 9.1 Crear `apps/frontend/ATTRIBUTIONS.md` (decisión 7): aviso MIT de shadcn/ui verificado contra
      la licencia publicada, y por qué no aplican Unsplash, fuentes ni dependencias npm.
- [ ] 9.2 Redactar `docs/adr/ADR-0010-frontend-color-tokens.md` desde `docs/templates/adr.md` en estado
      `Proposed`, añadirlo al índice de `docs/adr/README.md` y enlazarlo desde el seguimiento de
      ADR-0004.
- [ ] 9.3 Actualizar `apps/frontend/README.md`: estilos y tokens (dónde viven, regla de no usar
      colores literales, test guardián) y `ATTRIBUTIONS.md` en la estructura.
- [ ] 9.4 Actualizar `docs/spikes/frontend-migration.md`: la tarjeta `jup-0xx-unificar-estilos-assets`
      pasa a `JUP-099` / `jup-099-unify-styles-assets`, carril `standard`, casillas marcadas con el
      alcance real.

## 10. Cierre

- [ ] 10.1 Verificar que `git diff develop...HEAD --stat` no contiene ningún archivo de
      `apps/backend/` ni de `apps/processor/`.
- [ ] 10.2 Ejecutar la batería: `openspec:validate`, `jup:check -- --change
      jup-099-unify-styles-assets`, `jup:cleanup:check`, lint, typecheck, test, build e
      `install --frozen-lockfile`, registrando resultados en `review.md`.
- [ ] 10.3 Crear `docs/evidence/JUP-099-validation.md` con el guion de captura completo, la tabla de
      píxeles por pantalla, la demostración de propagación, conteos Red/Green, la excepción de
      mutación y la verificación de los 8 criterios de la tarjeta uno a uno.
