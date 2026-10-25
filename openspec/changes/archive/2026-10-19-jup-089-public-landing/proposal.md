JUP: JUP-089
Trello: https://trello.com/c/fD7nJKRl

## Why

Economicon necesita una presentación pública separada de la aplicación autenticada. Paris aprobó el diseño de alta fidelidad el 19/10/2026; esta entrega conserva esa composición y sus simulaciones explícitas.

## What Changes

- Añadir apps/landing como aplicación estática independiente, sin dependencias de producción nuevas ni importaciones de frontend/backend.
- Conservar las siete secciones, marca original, fuentes locales, navegación móvil, perspectivas y demo ilustrativa de tres pasos aprobadas.
- Construir sólo archivos públicos permitidos; añadir servidor local limitado, 404, cabeceras y metadatos/robots/sitemap condicionados al origen HTTPS explícito.
- Añadir pruebas de frontera pública, operación/reversión y evidencia de responsive, accesibilidad, rendimiento y SEO.

Dominio, responsable de renovación, alojamiento, DNS/HTTPS público, destino real de demo y despliegue están pendientes de decisión humana. Se prepara su operación, sin afirmar esos criterios cumplidos por las pruebas locales. No se modifica la aplicación privada, su autenticación ni las API. No se añade vídeo inexistente, clientes, previsiones o ahorros acreditados.

## Impact

Nueva capacidad public-landing. App, lockfile workspace (importer vacío), job CI focal, documentación y continuidad. No migraciones ni cambios en servicios existentes. Roles propuestos por la tarjeta: Paris liderazgo, Víctor pairing, Alejandro revisión, Lucía validación; su asignación no acredita participación.
