## Context

JUP-112. Ver `proposal.md` para la motivación. Estado actual: Tailwind v4 con tokens semánticos en `apps/frontend/src/styles/theme.css` ([ADR-0012](../../../docs/adr/ADR-0012-frontend-color-tokens.md), JUP-099). Hoy hay una sola paleta, oscura, y ningún color literal en pantallas, así que cambiar de paleta es sobre todo reescribir el tema. Lo que no es solo tema:

- Tonos que asumían fondo oscuro: textos `*-foreground` claros sobre rellenos `/20`, degradados `from-card to-accent`, sombras y `text-foreground` blanco sobre fondos de color.
- `chartTheme.ts` y las gráficas, con hexadecimales de series que no se verían bien en claro.
- El documento de impresión de `ExportButton` (excepción declarada en ADR-0012) y `Dialog` (`bg-black/50`).
- Marca: cabecera con icono genérico, `index.html` con título "FinOps Control Tower" y sin favicon.

Los materiales de marca (paleta, tipografías, monograma E primario e inverso) están en el dossier de marca del proyecto; los logos se extraen de sus recursos sin modificarlos.

## Goals / Non-Goals

**Goals:**
- Que la aplicación sea reconociblemente Economicon: paleta, tipografía y logotipo de la guía.
- Una paleta de estados y de gráficas con criterio de diseño que no compita con el coral ni con el violeta.
- Legibilidad comprobada con números (contraste) y a ojo (capturas en 1280 y 390 px).

**Non-Goals:**
- Modo oscuro, y cualquier segunda paleta.
- Cambiar estructura de pantallas, rutas, datos o lógica. Es un cambio de presentación.
- Rediseñar el contenido de las pantallas de otras tarjetas en curso (JUP-056, JUP-058, JUP-089): se consumen los mismos tokens.

## Decisions

**1. Mantener los nombres semánticos de ADR-0012 y cambiar sus valores.** Los consumidores (`text-muted-foreground`, `bg-danger-tint/20`…) no cambian de nombre; así el cambio se concentra en `theme.css` y en los pocos sitios que asumían oscuro. Alternativa descartada: renombrar tokens por la marca (`--indigo`): rompería el criterio "nombre por función" y obligaría a tocar todas las pantallas.

**2. Asignación de la paleta de marca a tokens.**

| Token | Valor | Uso |
| --- | --- | --- |
| `background` | `#FAFAFC` | fondo base |
| `foreground` | `#14121F` | texto principal |
| `card` | `#E4E1FB` al fondo de sección suave; tarjetas de datos en blanco puro sobre el base cuando el lila saturaría la pantalla (se decide al ver capturas) | tarjetas |
| `brand` (nuevo) | `#2B2359` | cabecera, texto de marca, encabezados |
| `primary` | `#5B4FE8` | solo botones y CTA |
| `saving` (nuevo) | `#FF8A5B` | ahorro e insights, con texto `#14121F` encima |
| `muted-foreground`, `border`, `muted` | tonos de índigo desaturado (derivados de `#2B2359`) | texto secundario y bordes |

`--primary` deja de usarse para navegación y selección: la navegación activa pasa a `brand` (borde inferior y peso). Alternativa descartada: violeta también en navegación activa; contradice "exclusivo para CTAs".

**3. Estados con criterio propio (valores iniciales, se ajustan con las capturas y el test de contraste).** Se elige un tono por estado separado del coral (naranja) y del violeta, pensando en que el coral es el único cálido de marca:

| Estado | Texto (sobre claro) | Relleno / gráfico | Nota |
| --- | --- | --- | --- |
| éxito | verde profundo `#0F6B4F` | `#1FA37A` | verde azulado, armoniza con el índigo |
| aviso | ámbar oscuro `#8A5200` | `#E5A100` | amarillo ocre, no naranja, para no parecer coral |
| peligro | carmesí `#B3243F` | `#D6334F` | rojo con matiz frío, distinto del coral |
| información | azul `#1F5FBF` | `#3B7DDB` | azul de hue distinto al violeta |
| neutro | gris índigo `#5A5670` | `#8B879F` | |

Los rellenos suaves se obtienen mezclando el relleno con el fondo (`color-mix`) a opacidad baja y el texto usa la variante oscura. `attention` (naranja actual) se elimina: sus usos pasan a aviso o a coral según signifiquen alarma o ahorro, para que el naranja signifique una sola cosa. Alternativa descartada: conservar los tonos Tailwind actuales aclarados; sobre claro sus variantes `-foreground` claras no llegan a 4,5:1.

**4. Gráficas.** Serie de cinco tonos en la familia de la marca más estados, ordenada para que dos series adyacentes difieran en tono y no solo en luminosidad (índigo medio, azul, verde azulado, ámbar, rosa carmesí), sin violeta de CTA y con coral solo cuando la serie representa ahorro. Ejes y rejillas en `muted-foreground` suave. Alternativa descartada: monocromo índigo con luminosidades; no distingue series en leyenda.

**5. Contraste como contrato ejecutable.** Un test nuevo calcula la razón de contraste WCAG de los pares declarados (texto de estado sobre relleno suave, base y lila; texto de botón sobre violeta; texto sobre coral) y falla por debajo de 4,5:1 (3:1 para gráficos). Esto evita el riesgo ya medido: coral sobre blanco roto da ≈2,2:1, por eso el coral nunca lleva texto claro.

**6. Tipografía.** Dos paquetes de fuentes variables con licencia OFL, importados en `theme.css`/`main.tsx` y servidos con el bundle; `Space Grotesk` para `h1–h4` y nombre de marca vía `--font-heading`, `Inter` para `--font-sans`. Respaldo a la pila del sistema. Tamaños: los puntos de la guía son de presentación; se adaptan a píxeles CSS (títulos ≈ 36–44 px escritorio con reducción en móvil, secciones 20–24 px, cuerpo 14–16 px, notas 12 px) según criterio de diseño que la tarjeta permite.

**7. Logotipo.** Se copian los PNG originales del dossier a `src/assets/brand/` sin recolorear (primario `image2.png` sobre claro, inverso `image1.png` sobre índigo). Como ambos PNG tienen márgenes amplios, se muestran con altura fija y `object-contain` sin recorte ni filtro. Favicon: derivado por reescalado del primario, en `public/`. Se registra el origen (hash) en `ATTRIBUTIONS.md`/docs.

**8. Tests guardianes.** `color-tokens.guard.test.ts` sigue vigente; la excepción de `ExportButton` se mantiene (documento autónomo) pero su paleta de impresión se alinea con la marca. `theme-palette.test.ts` conserva "una paleta, sin `.dark`, un consumidor por token" y se actualiza a los tokens nuevos; se retira el token `attention-*` y los que queden sin consumidor. El `@custom-variant dark (&)` se mantiene para no editar primitivos shadcn (ADR-0004) pero con una paleta clara los `dark:` de los primitivos deben revisarse porque asumirían oscuro: se sustituye por `@custom-variant dark (&:where(.never-dark, .never-dark *))`, de modo que `dark:` no se aplica nunca. Esto exige comprobar que ninguna clase `dark:` de un primitivo es necesaria en claro.

**9. ADR.** Se enmienda ADR-0012 (no se crea uno nuevo): decisión 3 pasa de "solo oscuro" a "una paleta clara, sin modo oscuro", se retiran las alternativas que mencionaban el refactor sin rediseño y se enlaza JUP-112. Es una decisión duradera que obliga a tarjetas futuras (usar `brand`/`saving`, no usar `primary` para navegación).

## Risks / Trade-offs

- [Tests de pantallas que comprueban clases concretas fallen en masa] → se actualizan junto al token que cambia y se ejecuta la batería completa tras cada grupo.
- [Los rellenos suaves con `color-mix` se ven distintos a los `/20` de hoy] → se comparan capturas por pantalla y se ajusta la opacidad por estado, no por pantalla.
- [Dos tarjetas en curso (JUP-056/058/089) usan clases que cambian] → mantener los nombres de token reduce el solape; se avisa en el PR de qué tokens desaparecen (`attention-*`) y qué se añade (`brand`, `saving`).
- [Elegir "a ojo" los estados] → los valores iniciales de la tabla son una propuesta que debe aprobar Lucia con las capturas; el test de contraste acota lo objetivo y la aprobación lo subjetivo.
- [Fuentes empaquetadas aumentan el peso] → variables y solo los subconjuntos latino y latino-extendido.
- [Los PNG del logotipo son rasterizados y grandes (23–59 KB, 2000 px)] → se muestran en tamaño reducido; si se ve borroso en pantallas de alta densidad se pide una versión vectorial al equipo, sin vectorizarla por cuenta propia.
