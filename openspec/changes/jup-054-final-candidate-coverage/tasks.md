## 1. Candidato y referencia

- [x] 1.1 Comprobar `origin/develop` y fijar el SHA auditado (base de partida `e1c2a8f`). Abrir en
  `docs/evidence/JUP-054-validation.md` una sección nueva con fecha, rama, SHA auditado y enlace a
  Trello, después de las secciones de la primera pasada y sin modificarlas.
- [x] 1.2 Localizar la ejecución de CI del SHA auditado y anotar, por servicio, las pruebas
  aprobadas, fallidas y omitidas. Es la referencia de la decisión 4 del `design.md`.
- [x] 1.3 Anotar el entorno de medición: versión de Docker, digest de las imágenes `python:3.12` y
  `node:22`, y versiones fijadas de `pytest-cov` y del proveedor `v8` de Vitest.

## 2. Medición de cobertura

- [ ] 2.1 Preparar el contenedor de medición de Python con el árbol de `git archive <SHA>`, sin
  volúmenes compartidos con el repositorio y sin puertos publicados. Comprobar con `git status` que
  no deja nada dentro del repositorio.
- [ ] 2.2 Medir `apps/azure-cost-api` con cobertura de líneas y de ramas sobre `app`. Comparar
  aprobadas, fallidas y omitidas con la referencia de 1.2 y guardar el resumen.
- [ ] 2.3 Medir `apps/backend` del mismo modo y comparar con la referencia.
- [ ] 2.4 Medir `apps/processor` del mismo modo y comparar con la referencia. Anotar qué pruebas
  lanzan subprocesos, porque el código del proceso hijo no aparece en la medición.
- [ ] 2.5 Medir `apps/frontend` en el contenedor de Node: instalar con el lockfile congelado, anotar
  la versión resuelta de Vitest, añadir el proveedor en esa versión, volver a anotar la versión de
  Vitest y ejecutar la suite con cobertura sobre `src`, incluidos los archivos que ninguna prueba
  importa.
- [ ] 2.6 Para cada servicio cuya ejecución instrumentada no coincida con la referencia, repetirlo
  aislado una vez. Si sigue sin coincidir, anotar la diferencia y marcar esa cifra como no válida.
  No se cambia ningún plazo ni guard.
- [ ] 2.7 Escribir en la evidencia la tabla de cobertura por servicio (líneas y ramas) con los
  comandos exactos, y documentar esos comandos en `docs/testing/critical-flows.md`.

## 3. Auditoría de huecos

- [ ] 3.1 Confirmar con `git log 1f57f91..<SHA> -- apps` a qué tarjeta pertenece cada archivo
  añadido o ampliado después de la PR #93 y añadir a la matriz de `docs/testing/critical-flows.md`
  las áreas que falten (preguntas de ownership y cobertura de etiquetado, en backend y frontend),
  con su suite y sus límites reales o simulados.
- [ ] 3.2 Listar, por área de la matriz, el código que ninguna prueba ejecuta según la medición.
- [ ] 3.3 Cruzar esa lista con las pruebas omitidas de 1.2 y separar el código que solo ejercitan
  las suites opt-in con servicios reales.
- [ ] 3.4 Contrastar a mano las líneas que solo se ejecutan en subprocesos antes de llamarlas hueco.
- [ ] 3.5 Clasificar cada hueco restante con el criterio de la decisión 5 del `design.md`: crítico,
  aceptado con su motivo, o diferido.
- [ ] 3.6 Escribir en la evidencia la lista de huecos con su clasificación y el motivo de cada uno.

## 4. Aprobación de la lista de huecos

- [ ] 4.1 Presentar la lista de 3.6 y obtener la decisión sobre qué huecos críticos se cubren en
  esta pasada. Anotar en la evidencia la decisión y cualquier recorte. No se escribe ninguna prueba
  antes de este punto.
- [ ] 4.2 Desglosar el grupo 5 en una tarea por hueco aprobado, con el archivo de prueba de destino.

## 5. Pruebas de los huecos críticos

- [ ] 5.1 Backend: una prueba por cada hueco crítico aprobado, con componentes reales de la
  aplicación y los dobles externos declarados en la propia prueba. Comprobar cada una según la
  decisión 7 del `design.md`: romper a mano el comportamiento cubierto, ver que falla, revertir, y
  anotar qué se rompió y qué falló.
- [ ] 5.2 Processor: igual que 5.1.
- [ ] 5.3 Azure Cost API: igual que 5.1.
- [ ] 5.4 Frontend: igual que 5.1, con el árbol de rutas, los componentes y el cliente de API reales
  y `fetch` como único doble.
- [ ] 5.5 Si una prueba nueva falla contra el candidato sin modificar, parar: registrar el defecto
  como `RF-054-NNN` con su reproducción y decidir si la prueba se entrega como fallo esperado
  estricto o se deja fuera. No se debilita la aserción ni se toca el producto.
- [ ] 5.6 Comprobar con `git diff --stat` contra la base que no hay cambios en `apps/*/app/**`, en
  archivos de `apps/frontend/src/**` que no sean `*.test.*`, ni en dependencias o CI.

## 6. Verificación

- [ ] 6.1 Repetir la medición de los servicios con pruebas nuevas, sobre la rama, y anotar la
  cobertura antes y después de cada área cubierta.
- [ ] 6.2 Ejecutar la suite completa de cada servicio modificado, sin instrumentar, en el contenedor
  equivalente a CI, y anotar aprobadas, fallidas y omitidas.
- [ ] 6.3 Ejecutar `corepack pnpm --filter @finops/frontend lint`, `typecheck` y `build` si hay
  pruebas nuevas de frontend.
- [ ] 6.4 Ejecutar `corepack pnpm openspec:validate`,
  `corepack pnpm jup:check -- --change jup-054-final-candidate-coverage` y
  `corepack pnpm jup:cleanup:check`.
- [ ] 6.5 Comprobar `origin/develop` otra vez. Si hay commits nuevos que tocan `apps/**`, repetir la
  medición de los servicios afectados o anotar en la evidencia qué commits quedan sin auditar.

## 7. Registro y cierre

- [ ] 7.1 Registrar en `openspec/findings/backlog.md` los huecos diferidos y los defectos
  encontrados como `RF-054-NNN`, y revisar si `RF-096-004` necesita una nota con lo observado.
- [ ] 7.2 Completar la sección de la evidencia: tabla de criterios de aceptación con su prueba, lo
  que no se validó y por qué, y los límites que se conservan de la primera pasada.
- [ ] 7.3 Actualizar la matriz de `docs/testing/critical-flows.md` con el delta de esta pasada.
- [ ] 7.4 Actualizar `docs/continuidad/pruebas-unitarias-integradas.md` y su fila en
  `docs/continuidad/README.md`.
- [ ] 7.5 Escribir `review.md` en este change: resultado, comprobación de cada prueba nueva,
  hallazgos y la nota de que no aplica ADR.
- [ ] 7.6 Tras abrir la PR, enlazar en la evidencia la PR y la ejecución de CI del último commit.
