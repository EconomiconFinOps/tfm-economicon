JUP: JUP-117
Trello: https://trello.com/c/B4832TYk

## Why

El frontend mezcla español e inglés: pantallas como la de conversaciones, la ingesta, el acceso o el arranque de sesión muestran frases enteras en inglés junto a otras en español, y a veces dentro de la misma pantalla. La interfaz de Economicon es en español; el inglés llegará más adelante como segundo idioma. Homogeneizarlo ahora evita que cada pantalla nueva siga el idioma que le toque y deja un criterio único antes de internacionalizar.

## What Changes

- Pasar al español todos los textos visibles del frontend que estén en inglés: títulos, encabezados, botones, etiquetas, marcadores de campo, estados de carga, estados vacíos, mensajes de error, textos de ayuda, etiquetas de accesibilidad y el aviso de arranque de `main.tsx`.
- Mantener en inglés los términos técnicos sin traducción razonable o de uso habitual en español, y dejar cada excepción listada con su motivo en un glosario del frontend.
- Fijar en ese glosario un nombre único para cada concepto que hoy se escribe de varias formas (por ejemplo, tenant, owner, ingesta, dashboard).
- Ajustar las pruebas del frontend que comprueban textos cambiados.
- Añadir una prueba que falle si reaparece en la interfaz un texto en inglés de la lista de términos ya traducidos.

Fuera de alcance: internacionalización (selector de idioma, catálogos de traducción, inglés como segundo idioma), código, nombres de variables, rutas, claves de API y mensajes del backend que no se muestran a la persona usuaria, y cualquier cambio de diseño o de funcionalidad. No se traducen los valores que devuelve la API (por ejemplo, nombres de servicios de Azure o etiquetas de coste).

## Capabilities

### New Capabilities

- `frontend-spanish-ui`: la interfaz del frontend se muestra en español de forma coherente, con las excepciones técnicas justificadas en un glosario y una comprobación automática contra regresiones.

### Modified Capabilities

Ninguna. Los textos exactos que algunas specs de pantallas citan en sus escenarios se actualizan en este change si cambian (ver design).

## Impact

- Código: `apps/frontend/src/` (páginas, componentes, layouts y `main.tsx`) y sus pruebas.
- Documentación: nuevo glosario `apps/frontend/GLOSARIO.md` y referencia desde `apps/frontend/README.md`.
- Sin cambios de API, contratos, dependencias ni base de datos.
- Coordinación: JUP-116 oculta pantallas de maqueta y puede tocar los mismos ficheros; se resuelve en la rama que se integre en segundo lugar.
