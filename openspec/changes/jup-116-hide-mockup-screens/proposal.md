JUP: JUP-116
Trello: https://trello.com/c/IPB2nGxa

## Why

Una auditoría del frontend con el stack completo (2026-10-12) comprobó que Coste Detallado (`/operational`), Corte Global (`/cuts`) y Recomendaciones (`/recommendations`) no hacen ninguna petición al backend, enseñan siempre las mismas cifras inventadas y no avisan de que son de demostración (`RF-104-004`). No tienen spec ni tarjeta que las respalde: necesitarían multi-cloud, objetivos de recorte y un motor de recomendaciones que no existen (`RF-091-003`). Con la entrega y la defensa cerca, desvían la atención de lo que sí funciona y pueden confundirse con costes reales. El equipo dio su conformidad en Discord el 2026-10-12, con la condición de ocultarlas sin borrar lo hecho.

## What Changes

- Quitar de `routeConfig` las rutas `/operational`, `/cuts` y `/recommendations` y sus tres entradas del menú. Las pantallas, sus datos de demostración (`src/data/demo/`) y sus pruebas **se conservan** en el repositorio, sin ninguna ruta que las monte.
- Quitar del menú la entrada «Overview», que repite lo que ya muestra Coste Global. Su ruta `/overview-legacy` **se mantiene** como ruta puente sin enlace: alrededor de 35 usos en 8 archivos de pruebas la emplean como vehículo de una petición autenticada, y la spec vigente exige que el resumen de facturación conserve dirección propia. Retirar la ruta queda para la tarjeta que cierre `RF-105-001`.
- Una dirección no publicada (las tres ocultas o cualquier otra desconocida) lleva a la pantalla inicial en lugar de a la pantalla de error por defecto del enrutador.
- El menú pasa a ser una sola lista: desaparece el separador que distinguía demostración de datos reales, porque la única pantalla de demostración que queda (Anomalías) está rotulada.
- Actualizar la documentación que cuenta o nombra esas pantallas: tabla «Rutas» del README del frontend (único recuento), mapa de carencias de JUP-097, guía de la demo de JUP-107 y los findings afectados.

**Fuera de alcance:** construir las capacidades que esas pantallas necesitarían (trabajo futuro, JUP-110); borrar su código o sus datos; retirar `/overview-legacy`; arreglar el envío de mensajes del asistente sin el stack de IA; unificar el idioma de los rótulos del menú.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `frontend-navigation-shell`: una dirección no publicada lleva a la pantalla inicial; la vista heredada del resumen de facturación queda exenta de tener enlace en el menú; ninguna pantalla alimentada solo por datos de demostración se publica en el MVP.

## Impact

- Código: `apps/frontend/src/routes.tsx` y `apps/frontend/src/layouts/Layout.tsx`.
- Pruebas: `Layout.test.tsx` y `routes.integration.test.tsx` (usan Coste Detallado como pantalla de ejemplo) y pruebas nuevas de ocultación; las de las pantallas ocultas siguen ejecutándose montando el componente directamente.
- Documentación: `apps/frontend/README.md`, `docs/planning/JUP-097-frontend-data-gap-map.md`, `docs/demo/JUP-107/` y `openspec/findings/backlog.md` (`RF-104-004`, `RF-095-002`, `RF-091-003`, `RF-105-001`); continuidad en `docs/continuidad/`.
- Sin cambios en backend, API, base de datos ni dependencias. Sin ADR: es reversible y no fija una arquitectura duradera; la revisión lo dejará anotado.
- Afecta a la demo: dejan de verse tres pantallas y un enlace, y las direcciones antiguas redirigen.
