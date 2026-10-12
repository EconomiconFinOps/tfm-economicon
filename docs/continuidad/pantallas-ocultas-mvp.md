# Pantallas de maqueta ocultas del MVP — JUP-116

Última actualización documental: 2026-10-12. Esta nota no repite el alcance de la tarjeta, que vive en [Trello](https://trello.com/c/IPB2nGxa).

## Estado

- Rama `feat/JUP-116-hide-mockup-screens`, creada desde `develop` en `3c6517b`. OpenSpec: `openspec/changes/jup-116-hide-mockup-screens/` (delta de `frontend-navigation-shell`).
- Origen: una auditoría del frontend con el stack completo (2026-10-12) comprobó que Coste Detallado, Corte Global y Recomendaciones no hacían ninguna petición al backend, enseñaban cifras inventadas sin rótulo y no tenían spec ni tarjeta. El equipo dio su conformidad por Discord, con la condición de ocultarlas sin borrar lo hecho.
- Pendiente de integración: esta tarjeta se mergea antes que la de JUP-114, que reescribió el README de rutas, el guion y los esperados de la demo, el mapa de JUP-097 y los findings; el conflicto lo resuelve quien mergee JUP-114 después.

## Decisiones que no se deducen del código

- **Ocultar, no borrar.** Decisión de Lucia frente a un interruptor de configuración: se quitan rutas y entradas de menú y las pantallas, sus datos y sus pruebas se quedan en el repositorio. Reactivar una son dos líneas (ruta y entrada), descritas en el README del frontend, «Pantallas no publicadas».
- **`/overview-legacy` conserva su ruta.** Sale del menú porque repite Coste Global, pero 34 líneas de 9 archivos de pruebas la usan de vehículo y la spec exige dirección propia para el resumen de facturación. Retirarla del todo es `RF-105-001`.
- **Una dirección desconocida lleva a `/`.** Se añadió una ruta comodín con `replace`, de modo que los marcadores antiguos no acaban en la pantalla de error del enrutador y Atrás no vuelve a la dirección oculta.
- **Se retiró el token `--muted`.** Era un alias de `--border` cuyo único consumidor era el separador del menú; el guardián de tokens falla si un token no se usa.

## Qué tocar si cambia algo

- Reactivar una pantalla: `src/routes.tsx` y `navItems` de `src/layouts/Layout.tsx`; rotular antes sus datos como de demostración (`RF-104-004`) y ajustar `Layout.test.tsx` y `routes.hidden-screens.test.tsx`.
- Las capacidades de backend que esas pantallas necesitarían para tener datos reales están en `docs/planning/JUP-097-frontend-data-gap-map.md`.

## Pendiente

- Integrar JUP-114 después y resolver sus conflictos de documentación.
- Confirmar con el equipo que `/overview-legacy` se queda sin menú pero montada, que difiere de lo que decía el mensaje de Discord.
- No se comprobó el envío de mensajes del asistente (sin stack de IA) ni el tema oscuro.
