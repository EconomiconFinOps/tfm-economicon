# Interfaz del frontend en español — JUP-117

Actualizado: 2026-10-13. [Tarjeta](https://trello.com/c/B4832TYk). Change archivado en `openspec/changes/archive/2026-10-12-jup-117-frontend-espanol/`. PR #123 mergeado en `develop` el 2026-10-12 por squash (`be4a4c1`) con la excepción temporal: los siete controles técnicos en verde y `JUP reviews` en rojo; revisión adversarial en `accept`. Tarjeta en `70 — Hecho`.

## Qué contiene

- Textos propios de la interfaz en español en acceso, arranque de sesión, conversaciones, ingesta, panel de resumen, menú y compositor de mensajes; «tenant» pasa a «cliente» y «Dashboard» a «Panel».
- Glosario `apps/frontend/GLOSARIO.md`: nombre único de cada concepto y términos que se conservan en inglés con su motivo.
- Prueba de regresión `apps/frontend/tests/spanish-ui.test.ts`, que falla si reaparece en la interfaz un texto en inglés ya traducido. Solo detecta lo que está en su lista: se amplía con cada hallazgo.

## Límites

- Los valores de la API y los mensajes de error de la capa de API (`api.ts`) no se traducen por decisión de Lucia; pueden verse en inglés si el backend falla.
- El formato de importes de las pantallas de demostración depende del navegador.
- Internacionalización (catálogos, selector de idioma, inglés) queda para otra tarjeta; el glosario sirve de base.
- Evidencia: `docs/evidence/JUP-117-validation.md`. No hay validación independiente por el rol de la tarjeta.
- Hallazgos abiertos en `openspec/findings/backlog.md`: datos de demostración fijos en inglés, importes sin idioma, etiquetas de estado duplicadas y lista cerrada de la prueba de regresión.
