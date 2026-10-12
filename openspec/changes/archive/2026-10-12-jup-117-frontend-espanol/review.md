# Review JUP-117 — Interfaz del frontend en español

Fecha: 2026-10-12. Rama `feat/JUP-117-frontend-espanol`, desde `develop` en `3c6517b`. Trello: https://trello.com/c/B4832TYk

## Resumen

Los textos propios de la interfaz del frontend pasan a español en el acceso, el arranque de sesión, las conversaciones, la ingesta, el panel de resumen, el menú y el compositor de mensajes; el resto de pantallas ya estaba en español. «Tenant» pasa a «cliente» y «Dashboard» a «Panel». Se añade el glosario `apps/frontend/GLOSARIO.md` (nombre único de cada concepto y términos que se conservan en inglés con su motivo) y la prueba de regresión `apps/frontend/tests/spanish-ui.test.ts`, que falla si reaparece un texto en inglés ya traducido. Un escenario de `demo-auth-session` que citaba «Reset session» se actualiza con un delta MODIFIED.

## Decisiones

- Textos en línea, sin catálogo ni librería de internacionalización: eso es otra tarjeta y no se anticipa aquí.
- «Cliente» como nombre único del tenant, por ser lo ya dominante en las pantallas en español.
- Quedan fuera por decisión de Lucia (2026-10-12) los valores que devuelve la API y los mensajes de error que genera la capa de API y los hooks (`Request failed for…`, `Invalid response for…`, `Tenant required`).
- Etiquetas sobre valores cerrados de la API (rol del mensaje y estado de servicio del panel de resumen) en español con tabla cerrada, y el valor original si no está en la tabla. Se aplicó primero sin querer y Lucia confirmó mantenerlas el mismo día.
- Los datos de demostración fijos de las pantallas de maqueta (`src/data/demo`) y el formato de importes con `toLocaleString()` sin idioma quedan fuera de alcance. Las pantallas de maqueta las oculta JUP-116. **Pendiente de que Lucia lo acepte con sus palabras al aprobar.**
- ADR: no aplicable. Es un cambio de contenido, reversible y sin arquitectura nueva; la decisión de internacionalizar con catálogo se tomará en su tarjeta.
- Excepción temporal del 2026-10-11: sin revisión ni validación humanas de otras personas en GitHub; las sustituyen la revisión adversarial de este archivo y la evidencia de `docs/evidence/JUP-117-validation.md`.

## Validación

Comandos ejecutados el 2026-10-12:

| Comando | Resultado |
| --- | --- |
| Vitest del frontend (`apps/frontend`) | 796 de 796 en la ejecución final |
| `eslint src tests` y `tsc --noEmit` | sin avisos |
| `corepack pnpm build` | 4 de 4 tareas correctas |
| `python -m pytest scripts/tests` | 372 aprobadas y 15 omitidas (ya existían) |
| `corepack pnpm openspec:validate` | 66 de 66 |
| `corepack pnpm jup:check -- --change jup-117-frontend-espanol` y `jup:cleanup:check` | correctos |
| Recorrido con el stack real del acceso y las nueve pantallas del menú, en escritorio claro y oscuro y en móvil claro | sin texto propio en inglés, sin desborde horizontal y sin errores de página (ver evidencia) |

Pruebas intermitentes: ejecuciones completas de la suite del frontend fallaron de forma aleatoria (de uno a tres tests de `login-session-expired-notice*`, `auth-session` y `ownership-conversations`) por esperas agotadas bajo carga; sueltos pasan. Se conoce de JUP-061 y JUP-064. No se ha comparado con `develop`.

## Adversarial Review (pass 1)

Veredicto: changes-requested (3 HIGH, 4 MEDIUM, 3 LOW).

| ID | Gravedad | Resolución |
| --- | --- | --- |
| ADV-1 | HIGH | Títulos «Dashboard Ejecutivo/Operativo» → «Panel». Corregido |
| ADV-2 | HIGH | Errores de `api.ts` en inglés visibles. Fuera de alcance por decisión de Lucia (arriba) |
| ADV-3 | HIGH | «Close» para lectores de pantalla → «Cerrar». Corregido |
| ADV-4 | MEDIUM | Términos técnicos fuera del glosario. Añadidos al glosario con su motivo |
| ADV-5 y ADV-6 | MEDIUM | Prueba de regresión con falsos negativos y positivos. Endurecida y ampliada con casos |
| ADV-7 | MEDIUM | Fechas sin `es-ES`. Corregido |
| ADV-8 a ADV-10 | MEDIUM y LOW | Rótulo «Resumen», tratamiento y recetas de navegador. Glosario ajustado y receta actualizada |

## Adversarial Review (pass 2)

Veredicto: changes-requested.

| ID | Gravedad | Resolución |
| --- | --- | --- |
| ADV-1 | HIGH | `scripts/tests/test_synthetic_cost_demo.py` seguía buscando «Ambito de cliente». Corregido; 40 tests pasan |
| ADV-2 | HIGH | Datos de demostración fijos en inglés. Fuera de alcance, declarado en proposal, spec y glosario (pendiente de aceptación de Lucia) |
| ADV-3 | HIGH | Lista de la prueba de regresión incompleta. Ampliada |
| ADV-4 y ADV-5 | MEDIUM | Parser: texto con `;` y `import()`/`===`. Corregido con pruebas |
| ADV-6 | MEDIUM | Errores de `api.ts` frente al escenario de conversaciones. Escenario aclarado («propios de la interfaz») |
| ADV-7 | LOW | «Espere»→«Espera», «…»→«...». Corregido |
| ADV-8 | LOW | `toLocaleString()` sin idioma en pantallas de maqueta. No se cambia: afecta a cómo se ven los números de cuatro cifras y rompe pruebas |
| ADV-9 | LOW | Pruebas intermitentes; ver arriba |

## Adversarial Review (pass 3)

Veredicto: **accept**. Sin hallazgos BLOCKING ni HIGH; ejecutó vitest completo (796), `pytest scripts/tests` (372) y `node --test` de `tools` (20 de 20).

| ID | Gravedad | Resolución |
| --- | --- | --- |
| ADV-1 | MEDIUM | La tabla de etiquetas heredaba claves de `Object.prototype` (`constructor`, `__proto__`). Corregido con `Object.hasOwn` y pruebas con `constructor` y `toString` |
| ADV-2 | MEDIUM | `StatusPill` pasa todo a minúsculas, así que un estado desconocido no se muestra intacto. Anotado en el glosario; no se cambia el componente |
| ADV-3 | LOW | Etiquetas duplicadas en dos pantallas y capitalización distinta del glosario. Anotado, sin unificar |
| ADV-4 | LOW | La prueba de regresión solo cubre una lista cerrada. Es su diseño; ampliar con cada hallazgo |

## Barrido de patrón

- Textos citados en el repositorio: la receta `docs/demo/JUP-107/receta-navegador.md`, la receta `docs/evidence/JUP-104-browser-recipe.md` y la prueba de Python se actualizaron. La evidencia de validación de otras tarjetas es histórica y se deja como está.
- Búsqueda en tablas de etiquetas con `?? valor` sobre objeto literal: el patrón vulnerable estaba en los dos sitios nuevos y se corrigió; `LABELS`, `REASONS` y `JOB_LABELS` de la pantalla de salud están acotados por tipo o por tabla.

## Riesgos

- La prueba de regresión solo detecta lo que está en su lista. No es una garantía de que la interfaz esté en español: eso lo cubren el inventario y el recorrido visual.
- No se recorrió en el navegador el flujo de error de red ni el de sesión caducada; solo las pruebas automáticas.
- Los errores de la capa de API pueden verse en inglés si el backend falla (aceptado por Lucia).
- Conflictos con JUP-116, que toca los mismos ficheros de pantallas: se resuelven en la rama que se integre en segundo lugar.

## Hallazgos registrados en el backlog

Datos de demostración fijos en inglés, formato de importes sin idioma, etiquetas de estado duplicadas, y lista cerrada de la prueba de regresión. Ver `openspec/findings/backlog.md`.

## Revisión propia posterior al PR (2026-10-12)

Por la excepción temporal, Lucia y el asistente revisaron el PR #123 antes de integrarlo, sin publicar una review en GitHub. Se leyó el diff de producción completo y se probaron mutantes sobre lo añadido: la tabla de roles (`Object.hasOwn`), el texto «Cerrar» del diálogo y el rótulo «Ingesta» del menú los detectan las pruebas existentes. Hallazgo: el formato `es-ES` de las fechas de conversaciones y de salud no tenía prueba (cambiarlo a `en-US` no rompía nada). Corregido con dos pruebas que fallan con ese cambio; vitest del frontend pasa en 797 de 797.

## Human Approval

- Change: jup-117-frontend-espanol
- Approval type: post-review
- Decision: approved
- Approver: Lucia
- Date: 2026-10-12
- Adversarial review: accept (pass 3) | accepted findings: datos de demostración fijos en inglés, formato de importes sin idioma en las pantallas de maqueta y errores de la capa de API en inglés (aceptados por Lucia el 2026-10-12, registrados en `openspec/findings/backlog.md`)
- Archive decision: archive
- Notes: revisión y validación humanas de otras personas sustituidas por la excepción temporal del 2026-10-11; la validación independiente por el rol de la tarjeta sigue sin hacerse. Falta confirmar en el PR la integración con JUP-116.
