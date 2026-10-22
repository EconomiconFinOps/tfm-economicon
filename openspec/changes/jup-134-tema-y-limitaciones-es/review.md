JUP: JUP-134
Trello: https://trello.com/c/zg2LSCjb/126-jup-134

# Revisión del change `jup-134-tema-y-limitaciones-es`

Documento en curso: se completa grupo a grupo durante el apply.

## Grupo 1: selector de tema con el tema activo (tareas 1.1 a 1.5)

### Resultado

El botón de tema muestra «Tema claro» con el tema claro activo y «Tema oscuro» con el oscuro, sin `aria-pressed` y con un `title` que describe la acción al pulsar. No cambia `useTheme`.

### Evidencia Red / Green / mutación

- **Red** (commit `69b4527b`): `ThemeToggle.test.tsx` (nuevo, 18 casos) y los ajustes de `useTheme.test.tsx` (de 11 a 13 casos) y `brand-spec.guard.test.tsx`. Con el producto antiguo fallaban 22 casos y pasaban 20. Entre estos, 6 de `ThemeToggle.test.tsx` que ya pasaban son guardas de no regresión (iconos `aria-hidden`, valor guardado inválido, `data-theme` y persistencia, y los casos que coincidían con el texto antiguo).
- **Excepción del candado `lock-committed-tests`**: las tareas 1.1 y 1.3 reescriben dos tests ya commiteados, que el hook impide editar. El tester preparó las versiones nuevas fuera del repo y generó un parche; lo aplicó la persona responsable de la rama con `git apply`, con aprobación expresa, y el commit Red incluye ese resultado. La Red se probó con copias temporales de esos ficheros, ya borradas.
- **Green** (commit `021dc931`): solo cambia `apps/frontend/src/components/ThemeToggle.tsx` (texto según `isDark`, `aria-pressed` fuera, `title` con la acción). 42 de 42 casos en verde en los tres ficheros.
- **Mutación** (Stryker 10.0.0, solo `ThemeToggle.tsx`, con los tres tests del selector): 9 mutantes, 9 muertos, 0 supervivientes, 0 sin cobertura. Puntuación 100 %. Se ejecutó con una configuración temporal de Vitest acotada a esos tests, ya eliminada.

### Comprobaciones

| Comprobación | Resultado |
| --- | --- |
| Pruebas del selector (`ThemeToggle.test.tsx`, `useTheme.test.tsx`, `brand-spec.guard.test.tsx`) | 42 de 42 |
| Frontend completo (vitest) | 1400 pruebas en 93 ficheros, OK |
| `lint` del frontend | 0 errores y 1 aviso previo (`ChatPresentation.tsx:101`, `react-hooks/exhaustive-deps`) |
| `typecheck` del frontend | OK |
| Escaneo de secretos del DoD | OK |
| Backend (pytest, venv `.venv-tfm`) | **No ejecutable completo en esta máquina**: 210 fallos y 102 errores por `tokenizer.json`, un artefacto generado que solo existe tras construir la imagen y que no está en el repositorio. Este grupo no toca ningún fichero de `apps/backend`; lo ejecuta la CI. Las pruebas de anomalías (`test_anomaly_explanations.py`, 75) pasan |
| Procesador (pytest) | **No ejecutable en esta máquina**: falta el módulo `markdown_it`. No se toca `apps/processor`; lo ejecuta la CI |

El DoD (`check-dod.mjs`) queda en rojo en local solo por los dos puntos anteriores, que son del entorno y no del cambio.

### QA

Veredicto del agente `qa`: **accept**. Reprodujo las pruebas, el lint y el type-check; revisó que cada escenario de la spec del control de tema tiene un test y que el parche a los tests existentes no pierde ni debilita cobertura (cada `aria-pressed` pasó a comprobar texto y ausencia del atributo). Comprobó la sensibilidad con cinco cambios manuales en `ThemeToggle.tsx` y los revirtió:

| Cambio manual | Casos que fallan |
| --- | --- |
| Textos de las dos ramas invertidos | 27 |
| `title` invertido | 3 |
| `aria-pressed={isDark}` reintroducido | 6 |
| `aria-label="Tema"` añadido | 25 |
| `aria-hidden` quitado del icono de la luna | 1 |

No hubo hallazgos. Quedó sin comprobar en esa pasada: la mutación Stryker (se reprodujo en este documento por quien orquesta), la suite completa del frontend y la comprobación en navegador (tarea 4.1).

### Pendientes detectados

- `apps/frontend/README.md:131` menciona el botón «Tema oscuro»: tarea 3.1.
- `docs/continuidad/identidad-marca-frontend.md`: revisar si describe el botón con ese literal: tarea 3.2.
