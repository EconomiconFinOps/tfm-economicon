## 1. Base: fuentes, assets y tema

- [x] 1.1 Añadir las dependencias de fuentes variables Inter y Space Grotesk (licencia OFL) y cargarlas con el bundle con tipografía de respaldo; comprobar en el build que no hay peticiones a terceros
- [x] 1.2 Copiar a `src/assets/brand/` los PNG originales del monograma (primario e inverso), generar el favicon por reescalado y declararlo en `index.html` junto con el título "Economicon"
- [x] 1.3 Reescribir `theme.css` con la paleta clara en `:root` y la oscura en `[data-theme="dark"]`, con el mismo conjunto de tokens (`brand` y `saving` nuevos, `primary` solo para CTA, estados y series según el diseño); retirar `attention-*` y tokens sin consumidor
- [x] 1.4 Cambiar el `@custom-variant dark` para que `dark:` aplique solo con `data-theme="dark"` y comprobar los primitivos shadcn en ambos temas sin editarlos
- [x] 1.5 Aplicar tipografía de marca a `h1–h4`, nombre de marca y cuerpo, con tamaños adaptados a píxeles CSS y a móvil

## 2. Armazón, marca y conmutador de tema

- [x] 2.1 Cabecera índigo con monograma inverso y "Economicon"; navegación activa con `brand` y borde, sin violeta
- [x] 2.2 Pantalla de acceso con monograma primario y botón primario en violeta
- [x] 2.3 Botones primarios de todas las pantallas en `primary` y comprobar que el violeta no aparece fuera de botones
- [x] 2.4 Script de `index.html` que fija `data-theme` antes del primer pintado (elección guardada o preferencia del sistema, con `try/catch` en el almacenamiento) y control accesible en la cabecera que alterna, guarda y indica el tema activo

## 3. Estados y gráficas

- [x] 3.1 Actualizar `StatusPill`, tarjetas de métrica, anomalías, salud del sistema y recomendaciones a los nuevos estados, con icono o texto en cada indicación
- [x] 3.2 Usar el coral solo en ahorro e insights y sustituir los usos de `attention-*` por aviso o ahorro según su significado
- [x] 3.3 Actualizar `chartTheme.ts`, las series de las gráficas y los datos demo con `var(--chart-N)`, leyendas y tooltips legibles
- [x] 3.4 Alinear el documento de impresión de `ExportButton` y el fondo del `Dialog` con la marca, manteniendo la lista de excepciones al día

## 4. Pruebas

- [x] 4.1 Test de contraste de los pares texto/fondo declarados en cada tema (estados sobre relleno suave, base y tarjeta; texto sobre violeta; texto sobre coral; series sobre tarjeta) con umbrales 4,5:1 y 3:1
- [x] 4.2 Actualizar `theme-palette.test.ts` (dos paletas con el mismo conjunto de tokens, uno por definición y con consumidor) y `color-tokens.guard.test.ts` a los tokens nuevos, y comprobar que el violeta de CTA solo lo consumen botones
- [x] 4.3 Test de marca: la cabecera muestra "Economicon" y el monograma, el título de la pestaña la contiene y no aparece "FinOps AI Platform" ni "FinOps Control Tower"
- [x] 4.4 Corregir los tests de pantallas afectados por clases o textos que cambian y ejecutar la batería del frontend completa
- [x] 4.5 Test del tema: arranque según la preferencia del sistema, elección explícita que prevalece y persiste, almacenamiento no disponible sin errores, y el control alterna sin recargar

## 5. Documentación

- [x] 5.1 Enmendar ADR-0012 (decisión 3: dos paletas con los mismos tokens activadas por atributo; nuevos tokens `brand` y `saving`; `primary` solo CTA) enlazando JUP-112 y este cambio
- [x] 5.2 Registrar fuentes y logotipo con su origen y licencia en `apps/frontend/ATTRIBUTIONS.md` y describir las reglas de uso de marca para quien toque el frontend
- [x] 5.3 Añadir el tema de continuidad de JUP-112 en `docs/continuidad/` y su fila en el índice

## 6. Cierre y verificación

- [x] 6.1 Capturas en 1280 px y 390 px, en tema claro y oscuro, de cada pantalla (con datos, carga, vacío y error) con Chromium real, revisadas a ojo contra los requisitos de legibilidad y de uso del violeta y el coral; comprobar que las gráficas se repintan al cambiar de tema; guardar la evidencia en `docs/evidence/JUP-112/` junto con la salida del validador de paletas
- [x] 6.2 Batería completa: `corepack pnpm build`, `lint`, `test`, typecheck del frontend, `openspec:validate`, `jup:check` para este cambio y `jup:cleanup:check`
- [x] 6.3 Revisión adversarial con el agente `adversarial-reviewer` hasta `accept` y registro en `review.md`
- [ ] 6.4 Sección `## Human Approval` posterior a la revisión, a cumplimentar por Lucia
- [ ] 6.5 Archivar el cambio en el mismo PR y abrir el PR contra `develop` desde `feat/JUP-112-brand-identity`, indicando en la descripción que el tema oscuro amplía el alcance de la tarjeta por decisión de Lucia
