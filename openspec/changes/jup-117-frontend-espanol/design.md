JUP: JUP-117
Trello: https://trello.com/c/B4832TYk

## Context

Los textos de la interfaz están escritos directamente en los componentes (`apps/frontend/src/pages`, `components`, `layouts`, `main.tsx`); no hay catálogo de traducción ni librería de i18n. Un primer barrido encuentra bloques enteros en inglés en `ConversationsPage`, `DashboardPage`, `IngestPage`, `LoginPage`, `SessionGate`, `MessageComposer` y `main.tsx`; el resto de pantallas ya está mayoritariamente en español, pero con términos que varían (tenant/cliente, owner/responsable, dashboard/panel). `index.html` ya declara `lang="es"`. Varias pruebas buscan textos concretos, y algunas specs de OpenSpec citan textos de pantalla en sus escenarios.

## Goals / Non-Goals

**Goals:**
- Que ninguna pantalla muestre texto propio de la interfaz en inglés salvo excepciones justificadas.
- Un vocabulario único y documentado.
- Una red de seguridad automática barata contra regresiones.

**Non-Goals:**
- Internacionalizar: no se introduce librería, claves de traducción ni selector de idioma. Esa tarjeta vendrá después y se beneficiará de tener ya los textos en español y un glosario.
- Traducir datos que vienen de la API o de la persona usuaria.
- Reorganizar componentes o cambiar diseño.

## Decisions

1. **Textos en línea, sin catálogo.** Se edita cada literal donde está. Alternativa descartada: extraer ahora todos los textos a un catálogo; sería la internacionalización completa, con más riesgo y más diff, y sin el criterio de idioma cerrado todavía. Mantener los literales en línea también reduce los conflictos con JUP-116.
2. **Glosario en `apps/frontend/GLOSARIO.md`.** Una tabla corta: concepto, nombre en la interfaz y, para los términos que se quedan en inglés, el motivo. Se rellena al inventariar, no antes. Criterio por defecto: se traduce todo lo que tenga equivalente de uso habitual en el sector (panel, ingesta, coste, etiqueta); se conserva lo que es nombre propio, marca o jerga FinOps/Azure sin equivalente corriente. Ante la duda razonable, se conserva y se anota.
3. **Prueba de regresión por lista de términos traducidos.** Una prueba de Vitest recorre `src/**/*.tsx` sin los ficheros de prueba, extrae el texto de nodos JSX y los valores de atributos visibles (`aria-label`, `title`, `alt`, `placeholder`, `label`) y busca una lista de frases y palabras inglesas que este change ha traducido. Alternativa descartada: detectar inglés de forma genérica con una heurística; da falsos positivos con términos técnicos y nombres propios y obliga a mantener una lista de permitidos enorme. La lista se limita a lo ya traducido, de modo que la prueba es exacta y se amplía con cada hallazgo futuro.
4. **Orden del trabajo: inventario exhaustivo primero.** El barrido heurístico inicial no ve cadenas con acentos mezcladas ni textos generados con plantillas. En la aplicación se hace un inventario completo por fichero (incluidos atributos de accesibilidad y mensajes de error construidos en servicios y hooks que acaban en pantalla) antes de editar.
5. **Cambios en las pruebas existentes.** Se actualizan solo las aserciones sobre textos cambiados. Si una prueba busca un texto en inglés que viene de la API, no se toca. Si alguna spec principal cita un texto que cambia, se añade un delta MODIFIED en este change.
6. **ADR.** No se necesita: el cambio es de contenido, reversible y sin arquitectura nueva. La decisión de internacionalizar con catálogo se tomará en su propia tarjeta.

## Risks / Trade-offs

- **Conflictos con JUP-116** (oculta pantallas de maqueta y toca ficheros de páginas) → la rama que se integre después hace el rebase; las pantallas de maqueta ocultas se traducen igualmente si siguen en el código.
- **Traducción inconsistente entre pantallas** → glosario único revisado en la revisión de PR.
- **Pruebas que dependen de textos** → se actualizan en la misma tarea que el texto, y la batería completa del frontend se ejecuta al final.
- **Falsos negativos de la prueba de regresión** (solo detecta lo ya traducido) → es una red de seguridad, no una garantía; la garantía es el inventario exhaustivo y la validación visual de cada pantalla.
- **Términos dudosos** → se conservan y se anotan, no se bloquea el change.

## Open Questions

- Ninguna bloqueante. Los términos dudosos se deciden durante el inventario y quedan en el glosario para revisión.
