# Evidencia JUP-134 — Etiqueta del selector de tema y limitaciones de anomalías en español

- Fecha: 2026-10-22.
- Trello: https://trello.com/c/zg2LSCjb/126-jup-134
- Rama: `fix/JUP-134-tema-y-limitaciones-es`, desde `origin/develop` en `4567e8e7`.
- OpenSpec: `openspec/changes/jup-134-tema-y-limitaciones-es/` (propuesta, deltas de `frontend-brand-identity` y `cost-anomaly-episodes`, diseño, tareas y `review.md`).
- Estado: evidencia técnica de esta sesión. No sustituye la revisión ni la validación funcional de quienes tengan esos roles en Trello. Incluye comprobación en navegador real.

## Qué cambia

- El botón de tema de la cabecera muestra el tema activo («Tema claro» con el claro, «Tema oscuro» con el oscuro), sin `aria-pressed`, con un `title` que describe la acción.
- Las cinco limitaciones de los episodios de anomalía se redactan en español en el origen (`LIMITATIONS`) y la explicación del asistente reutiliza esa lista; desaparece `LIMITATIONS_ES`.

## Qué se comprobó y cómo

| Comprobación | Resultado |
| --- | --- |
| Pruebas nuevas en rojo antes de implementar | Selector: 22 casos fallaban y 20 pasaban. Limitaciones: 11 fallaban y 74 pasaban |
| Pruebas del selector (`ThemeToggle.test.tsx` 18, `useTheme.test.tsx` 13, `brand-spec.guard.test.tsx` 11) | 42 de 42 |
| Frontend completo (vitest) | 1400 pruebas en 93 ficheros |
| Pruebas del grupo de limitaciones (4 ficheros del backend) | 108 de 108 |
| Backend con `-k anomaly` | 555 en verde, 143 omitidas (CockroachDB opt-in) |
| Backend completo | 2278 en verde; 210 fallos y 102 errores idénticos a la base anterior al cambio (2268 en verde), todos por `tokenizer.json`, artefacto que solo existe tras construir la imagen |
| Mutantes del selector (Stryker, `ThemeToggle.tsx`) | 9 de 9 muertos (100 %) |
| Mutantes de las limitaciones (script con restauración por `git checkout`; `mutmut` no es viable en Windows) | 15 de 15 muertos; uno detectado por el QA en la primera pasada y cerrado con `test_anomaly_evidence_limitations_copy.py` |
| `corepack pnpm lint` y `corepack pnpm build` | 4 de 4 tareas cada uno; un aviso previo de ESLint en `ChatPresentation.tsx:101` |
| `typecheck` del frontend | sin errores |
| `corepack pnpm openspec:validate` | 89 de 89 |
| `jup:check` del change, `jup:check:test`, `jup:cleanup:check`, `jup:cleanup:test` | correctos (7 y 6 pruebas) |
| Navegador real (Chromium, stack aislado construido desde la rama) | 22 de 22 comprobaciones PASS (ver abajo) |
| QA independiente | Grupo 1: accept. Grupo 2: changes-requested en la primera pasada (mutante superviviente) y accept en la segunda |

## Evidencia por requisito de la spec

| Requisito del delta | Dónde se comprueba |
| --- | --- |
| Control de tema: texto del tema activo, nombre accesible igual al texto | `ThemeToggle.test.tsx`, `useTheme.test.tsx`, `brand-spec.guard.test.tsx` |
| El texto sigue al tema al alternar y al recargar | `ThemeToggle.test.tsx` (alternar, elección guardada, almacenamiento bloqueado, `matchMedia` ausente o roto) |
| Limitaciones del episodio en español, en orden | `test_anomaly_episode_limitations_es.py` (constante, `episode_payload` y lectura HTTP de un episodio) |
| Mismas limitaciones en el panel y en el asistente | `test_anomaly_episode_limitations_es.py`, `test_anomaly_explanations.py` |
| La evidencia no comparte la lista global | `test_anomaly_evidence_limitations_copy.py` |

## Comprobación en navegador

Stack aislado y desechable: `docker compose --env-file <fichero temporal fuera del repo> -p jup134-check --profile demo up -d --build --wait`, volúmenes nuevos, imágenes construidas desde esta rama, `RUNTIME_ENVIRONMENT=development`, `COST_REFERENCE_DATE=2026-10-30` y credenciales aleatorias locales. Chromium con Playwright (fuera del repositorio), ventana de 1280 px, tema del sistema claro, cuenta de demostración `operator@example.com` y cliente Core Finance. Sin interceptar peticiones.

| Comprobación | Resultado |
| --- | --- |
| Tema claro: el botón dice «Tema claro», con el sol, `title` «Cambiar a tema oscuro», sin `aria-pressed` ni `aria-label`, accesible por ese nombre y sin botón «Tema oscuro» | PASS (6) |
| Tema claro: sin atributo `data-theme` | PASS |
| Al pulsar: pasa a «Tema oscuro» sin recargar, con la luna, `title` «Cambiar a tema claro», `data-theme="dark"` y sin `aria-pressed` | PASS (4) |
| Recargar en oscuro conserva «Tema oscuro»; volver a claro y recargar conserva «Tema claro» | PASS (3) |
| Detalle de la anomalía de Compute (5851,57 EUR, Alta P1) tras «Detectar ahora»: cinco limitaciones, la primera «Es un candidato para investigar…» | PASS (2) |
| Ninguna limitación tiene palabras funcionales inglesas ni la redacción anterior | PASS (2) |
| Sin desplazamiento horizontal de la página a 1280 y a 390 px | PASS (2) |
| Sin errores de página durante el recorrido | PASS |

El primer intento del guion falló por defectos del propio guion (dos elementos `header` y una bandeja vacía a la que había que pedir «Detectar ahora»); se corrigió y se repitió el recorrido completo. Las capturas y el resultado del guion no se versionan.

## Sin comprobar
- **Backend y procesador completos**: no son ejecutables en local (falta `tokenizer.json` en el backend y el módulo `markdown_it` en el procesador). El diff no toca el procesador; lo ejecuta la CI.
- **Pruebas contra CockroachDB real**: omitidas por no haber URL de pruebas.

## Riesgo aceptado

Una anomalía sin cambios que se explica antes y después del despliegue obtiene otro identificador de evidencia, porque la fotografía del episodio incluye sus limitaciones. No tiene efecto visible: el identificador solo se muestra como texto, nadie lo busca ni lo compara, y las explicaciones guardadas no se reescriben. Detalle en `design.md`, «Risks / Trade-offs».

## Pendiente

- PR: pendiente de abrir contra `develop`.
- CI: pendiente de ejecutar.
- Reviews `Revision JUP-134` y `Validacion JUP-134`: pendientes.
