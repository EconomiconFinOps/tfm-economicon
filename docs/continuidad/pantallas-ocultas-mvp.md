# Pantallas de maqueta ocultas del MVP — JUP-116

Última actualización documental: 2026-10-13. Esta nota no repite el alcance de la tarjeta, que vive en [Trello](https://trello.com/c/IPB2nGxa).

## Estado

- PR #124 mergeado en `develop` el 2026-10-12 por squash (`0643e1b`) con la excepción temporal, después de JUP-117: los siete controles técnicos en verde y `JUP reviews` en rojo. Tarjeta en `70 — Hecho`. Rama creada desde `develop` en `3c6517b`. OpenSpec: `openspec/changes/archive/2026-10-12-jup-116-hide-mockup-screens/` (delta de `frontend-navigation-shell`).
- Origen: una auditoría del frontend con el stack completo (2026-10-12) comprobó que Coste Detallado, Corte Global y Recomendaciones no hacían ninguna petición al backend, enseñaban cifras inventadas sin rótulo y no tenían spec ni tarjeta. El equipo dio su conformidad por Discord, con la condición de ocultarlas sin borrar lo hecho.
- Integración: se mergeó después de JUP-117; los conflictos con `develop` (menú, test de rutas y continuidad) se resolvieron en la rama conservando el menú de una sola lista con las etiquetas en español. Las reviews publicadas fueron sobre el commit anterior y no cubren ese commit de integración. JUP-114 (PR #122, abierto) ya integró `develop` con esos cambios en `dc22c07`.

## Decisiones que no se deducen del código

- **Ocultar, no borrar.** Decisión de Lucia frente a un interruptor de configuración: se quitan rutas y entradas de menú y las pantallas, sus datos y sus pruebas se quedan en el repositorio. Reactivar una son dos líneas (ruta y entrada), descritas en el README del frontend, «Pantallas no publicadas».
- **`/overview-legacy` conserva su ruta.** Sale del menú porque repite Coste Global, pero 34 líneas de 9 archivos de pruebas la usan de vehículo y la spec exige dirección propia para el resumen de facturación. Retirarla del todo es `RF-105-001`.
- **Una dirección desconocida lleva a `/`.** Se añadió una ruta comodín con `replace`, de modo que los marcadores antiguos no acaban en la pantalla de error del enrutador y Atrás no vuelve a la dirección oculta.
- **Se retiró el token `--muted`.** Era un alias de `--border` cuyo único consumidor era el separador del menú; el guardián de tokens falla si un token no se usa.

## Qué tocar si cambia algo

- Reactivar una pantalla: `src/routes.tsx` y `navItems` de `src/layouts/Layout.tsx`; rotular antes sus datos como de demostración (`RF-104-004`) y ajustar `Layout.test.tsx` y `routes.hidden-screens.test.tsx`.
- Las capacidades de backend que esas pantallas necesitarían para tener datos reales están en `docs/planning/JUP-097-frontend-data-gap-map.md`.

## Pendiente

- JUP-114 (PR #122) sigue abierto; ya integró `develop` con esta tarjeta.
- Confirmar con el equipo que `/overview-legacy` se queda sin menú pero montada, que difiere de lo que decía el mensaje de Discord.
- No se comprobó el envío de mensajes del asistente (sin stack de IA) ni el tema oscuro.
