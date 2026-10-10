## Context

JUP-112. Ver `proposal.md` para la motivación. Estado actual (Lucia decidió incluir tema claro y oscuro): Tailwind v4 con tokens semánticos en `apps/frontend/src/styles/theme.css` ([ADR-0012](../../../docs/adr/ADR-0012-frontend-color-tokens.md), JUP-099). Hoy hay una sola paleta, oscura, y ningún color literal en pantallas, así que cambiar de paleta es sobre todo reescribir el tema. Lo que no es solo tema:

- Tonos que asumían fondo oscuro: textos `*-foreground` claros sobre rellenos `/20`, degradados `from-card to-accent`, sombras y `text-foreground` blanco sobre fondos de color.
- `chartTheme.ts` y las gráficas, con hexadecimales de series que no se verían bien en claro.
- El documento de impresión de `ExportButton` (excepción declarada en ADR-0012) y `Dialog` (`bg-black/50`).
- Marca: cabecera con icono genérico, `index.html` con título "FinOps Control Tower" y sin favicon.

Los materiales de marca (paleta, tipografías, monograma E primario e inverso) están en el dossier de marca del proyecto; los logos se extraen de sus recursos sin modificarlos.

## Goals / Non-Goals

**Goals:**
- Que la aplicación sea reconociblemente Economicon en un tema claro (por defecto) y uno oscuro: paleta, tipografía y logotipo de la guía.
- Una paleta de estados y de gráficas con criterio de diseño que no compita con el coral ni con el violeta.
- Legibilidad comprobada con números (contraste, separación para daltonismo) y a ojo (capturas en 1280 y 390 px, en ambos temas).

**Non-Goals:**
- Más de dos temas, temas por cliente o personalización de colores por el usuario.
- Cambiar estructura de pantallas, rutas, datos o lógica. Es un cambio de presentación.
- Rediseñar el contenido de las pantallas de otras tarjetas en curso (JUP-056, JUP-058, JUP-089): se consumen los mismos tokens.

## Decisions

**1. Mantener los nombres semánticos de ADR-0012 y cambiar sus valores.** Los consumidores (`text-muted-foreground`, `bg-danger-tint/20`…) no cambian de nombre; así el cambio se concentra en `theme.css` y en los pocos sitios que asumían oscuro. Alternativa descartada: renombrar tokens por la marca (`--indigo`): rompería el criterio "nombre por función" y obligaría a tocar todas las pantallas.

**2. Dos paletas con los mismos tokens.** `:root` define el tema claro y `[data-theme="dark"]` redefine los mismos tokens. Ningún token existe en una sola paleta. La paleta oscura se deriva de la marca (índigo `#2B2359` como cabecera y base de tarjetas, casi negro `#14121F` como fondo) y no es una inversión automática.

| Token | Claro | Oscuro | Uso |
| --- | --- | --- | --- |
| `background` | `#FAFAFC` | `#14121F` | fondo base |
| `foreground` | `#14121F` | `#FAFAFC` | texto principal |
| `card` / `soft` | `#FFFFFF` / `#E4E1FB` | `#1F1A3D` / `#2B2359` | tarjetas y secciones suaves |
| `brand` (nuevo) | `#2B2359` | `#2B2359` | cabecera y texto de marca |
| `primary` | `#5B4FE8` | `#5B4FE8` | solo botones y CTA, texto blanco (5,63:1) |
| `saving` (nuevo) | `#FF8A5B` | `#FF8A5B` | ahorro e insights, con texto `#14121F` encima (7,96:1) |
| `muted-foreground`, `neutral` | `#524E6B`, `#5A5675` | `#B3AFCC`, `#ABA7C4` | texto secundario y neutro, legibles sobre fondo, tarjeta y acento |
| `border`, `input` | `#D9D5F2`, `#7F7A9C` | `#3A3470`, `#8A86A8` | borde decorativo y borde de campos (≥3:1 contra su fondo) |

`primary` deja de usarse para navegación y selección: la navegación activa, la selección y el foco usan `highlight` (índigo `#2B2359` en claro, lavanda `#BDB8F7` en oscuro), con borde y peso, no solo color. Sobre la cabecera índigo los controles usan `brand-foreground`, porque `highlight` en claro tiene el mismo color que ella.

**3. Estados con criterio propio, validados en los dos temas** con el validador de dataviz (`--pairs all`, con la superficie de tarjeta de cada tema) y con razón de contraste WCAG para el texto. El verde es azulado y el peligro un rojo frío, para que no se confundan entre sí (con un verde puro el rojo y el verde quedaban a ΔE 2,2 para daltonismo en oscuro) ni con el coral. `attention` (naranja) se elimina: sus usos pasan a aviso o a coral según signifiquen alarma o ahorro.

| Estado | Claro: relleno / texto | Oscuro: relleno / texto |
| --- | --- | --- |
| éxito | `#0B8A6E` / `#075340` | `#1AA68F` / `#5FD6BF` |
| aviso | `#BF8300` / `#6E4200` | `#BA8B1C` / `#E2B84C` |
| peligro | `#D03A3A` / `#8F1B1B` | `#F0566E` / `#FF9DAC` |
| información | `#3B7DDB` / `#174A99` | `#5A8BEA` / `#9DB8F5` |
| neutro | gris índigo, no se valida como categórico | gris índigo |

El relleno suave es el color de relleno con una opacidad de /10 a /30 sobre la superficie (nunca más del 30 %, lo comprueba un guardián); el test de contraste usa el 30 % como peor caso. El texto sobre ese relleno y sobre fondo, tarjeta y acento llega a 4,5:1 o más en los dos temas. La separación para daltonismo entre estados queda en ΔE 8,6 (claro) y 6,6 (oscuro, en zona de aviso del validador): solo es legal porque cada indicación de estado lleva icono y texto, que es un requisito de la spec. Alternativa descartada: conservar los tonos Tailwind actuales aclarados; no alcanzan el contraste de texto sobre fondo claro.

**4. Gráficas.** Cinco tonos por tema, ordenados para que dos series adyacentes difieran en tono, sin violeta de CTA y con el coral solo cuando la serie representa ahorro. Ambas paletas pasan los cinco chequeos del validador; en oscuro la separación entre rojo y verde azulado queda en zona de aviso (ΔE 6,7), legal porque cada serie lleva leyenda.

| Serie | Claro | Oscuro |
| --- | --- | --- |
| 1 | `#8E3B8A` | `#B565A9` |
| 2 | `#2F8BD9` | `#4A93E0` |
| 3 | `#BF8300` | `#BA8B1C` |
| 4 | `#1BA39C` | `#1CA89E` |
| 5 / pico | `#D6334F` | `#E8587A` |

La primera serie es un ciruela, no un índigo, porque un índigo se confundía con el violeta de botones (la distancia de color con `primary` se comprueba en un test). Ejes y rejillas en tonos apagados derivados de `muted-foreground`. Alternativa descartada: monocromo índigo con luminosidades; no distingue series en la leyenda.

**5. Contraste como contrato ejecutable.** Un test nuevo calcula la razón de contraste WCAG de los pares declarados, en cada tema (texto de estado sobre relleno suave, base y tarjeta; texto sobre violeta; texto sobre coral; series sobre tarjeta), y falla por debajo de 4,5:1 (3:1 para gráficos). La separación entre series para daltonismo se validó con el script de dataviz y se deja registrada en la evidencia; no se reimplementa en el test.

**6. Mecanismo de tema.** Atributo `data-theme` en `<html>`, fijado antes del primer pintado con un script mínimo en `index.html` para evitar el parpadeo: lee la elección guardada (`localStorage` dentro de `try/catch`) y, si no hay, `prefers-color-scheme`. Un hook pequeño y un botón en la cabecera alternan y guardan. El `@custom-variant dark` de Tailwind pasa de `(&)` a `(&:where([data-theme="dark"], [data-theme="dark"] *))`, de modo que las variantes `dark:` de los primitivos shadcn se aplican exactamente en tema oscuro y se conservan sin editarlos (ADR-0004). Alternativa descartada: `prefers-color-scheme` solo, sin control; el usuario no podría corregir el tema del sistema.

**7. Tipografía.** Dos paquetes de fuentes variables con licencia OFL, importados con el bundle; Space Grotesk para `h1–h4` y nombre de marca, Inter para el cuerpo, con respaldo a la pila del sistema. Los puntos de la guía son de presentación y se adaptan a píxeles CSS (títulos ≈ 36–44 px en escritorio con reducción en móvil, secciones 20–24 px, cuerpo 14–16 px, notas 12 px), según el criterio de diseño que la tarjeta permite.

**8. Logotipo.** Se copian los PNG originales del dossier a `src/assets/brand/` sin recolorear: el inverso (blanco) sobre la cabecera índigo y sobre fondos oscuros, y el primario (índigo) sobre fondos claros. Altura fija y `object-contain`, sin recorte ni filtro. Favicon derivado por reescalado del primario, en `public/`. El origen (hash del fichero del dossier) se registra en `ATTRIBUTIONS.md`.

**9. Tests guardianes.** `color-tokens.guard.test.ts` sigue vigente y la excepción del documento de impresión de `ExportButton` se mantiene, con su paleta alineada con la marca. `theme-palette.test.ts` pasa de "una paleta" a "dos paletas con el mismo conjunto de tokens, cada uno definido una vez por paleta y con consumidor"; se retira `attention-*` y los tokens huérfanos.

**10. ADR.** Se enmienda ADR-0012 (no se crea uno nuevo): la decisión 3 pasa de paleta oscura única a dos paletas con los mismos tokens activadas por atributo; se anota que la alternativa antes descartada ("conservar `:root` claro más `.dark`") ahora procede porque los dos temas tienen consumidores; se enlazan JUP-112 y este cambio. Obliga a tarjetas futuras: todo token nuevo se define en las dos paletas y `primary` no se usa para navegación.

## Risks / Trade-offs

- [Ampliación de alcance: la tarjeta pone el modo oscuro fuera de alcance y el liderazgo es de Paris] → se anota en el PR como decisión de Lucia pendiente de confirmar; si se rechaza, el tema oscuro queda aislado en un bloque `[data-theme="dark"]` y se retira sin tocar pantallas.
- [Doble verificación visual y de contraste (dos temas, dos anchuras)] → capturas con un recorrido fijo y los contrastes en un test, no a mano.
- [Parpadeo de tema al cargar] → script en `index.html` que fija `data-theme` antes del primer pintado.
- [Las gráficas de Recharts que leen `var(--chart-N)` pueden no repintarse al cambiar el tema] → comprobarlo en la verificación y, si no se repintan, forzar su remontaje al cambiar el tema.

- [Tests de pantallas que comprueban clases concretas fallen en masa] → se actualizan junto al token que cambia y se ejecuta la batería completa tras cada grupo.
- [Los rellenos suaves con `color-mix` se ven distintos a los `/20` de hoy] → se comparan capturas por pantalla y se ajusta la opacidad por estado, no por pantalla.
- [Dos tarjetas en curso (JUP-056/058/089) usan clases que cambian] → mantener los nombres de token reduce el solape; se avisa en el PR de qué tokens desaparecen (`attention-*`) y qué se añade (`brand`, `saving`).
- [Elegir los tonos a ojo] → los valores ya pasaron el validador y el cálculo de contraste; la aprobación estética de Lucia con las capturas reales cubre lo subjetivo.
- [Fuentes empaquetadas aumentan el peso] → variables y solo los subconjuntos latino y latino-extendido.
- [Los PNG del logotipo son rasterizados y grandes (23–59 KB, 2000 px)] → se muestran en tamaño reducido; si se ve borroso en pantallas de alta densidad se pide una versión vectorial al equipo, sin vectorizarla por cuenta propia.
