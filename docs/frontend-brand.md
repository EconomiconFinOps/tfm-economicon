# Identidad visual del frontend — JUP-112

Fuente: [tarjeta JUP-112](https://trello.com/c/XTZU3vj3), contrastada el 2026-10-10.
Implementación propuesta sobre `develop` `c2995a1`; aceptación humana pendiente.

## Materiales originales

Dossier de marca existente en el workspace de coordinación:
`materiales/05-marketing/economicon_dossier.pptx`, diapositivas 5–7.
SHA-256 `4918795d9041fe3b704cd3f9d8b5538fc033758660d53843b221667c1fa10dce`.
`materiales/05-marketing/INFORME.md` explica su autoría/proceso. No se copia el
dossier completo ni se atribuye una aprobación nueva a sus autores.

Los assets en `apps/frontend/src/assets/brand/` son los bytes originales del PPTX:

| Archivo | Entrada ZIP original | SHA-256 |
| --- | --- | --- |
| economicon-primary.png | ppt/media/image2.png | 3d642d739a7550827c60f32d281b8ad4d79df0fab9d1a5e683ae0bd96085d93e |
| economicon-inverse.png | ppt/media/image1.png | bb7aa6b5158edc020ccf92eec77a322a231efa3ac60dd8ca52806404cc61062e |

Mantener proporciones y espacio de seguridad; sin efectos, sombras sobre el logo
ni recoloración. La versión inversa se reserva a fondos oscuros de marca, sin
introducir un modo oscuro de la aplicación.

## Uso compartido

- `src/styles/theme.css`: única fuente de color. Índigo `#2B2359`, violeta CTA
  `#5B4FE8`, lila `#E4E1FB`, coral `#FF8A5B`, texto `#14121F`, base `#FAFAFC`.
- Inter para cuerpo/UI/datos; Space Grotesk para títulos y nombre. Fuentes
  empaquetadas con licencia OFL y alternativas del sistema. Ver ATTRIBUTIONS.
- El coral sobre blanco roto da aproximadamente 2.23:1: se usa como acento o
  superficie con texto oscuro. Blanco sobre CTA violeta da aproximadamente 5.63:1.
- Los tamaños de pantalla se adaptan a móvil; la tarjeta permite criterio de
  diseño sobre los tamaños orientativos del dossier. No confundir puntos
  tipográficos de presentación con píxeles CSS obligatorios.
- Usar colores semánticos de estados y gráficas con etiquetas, iconos o leyendas.
  El violeta de CTA no se reutiliza como color genérico de gráficas o navegación.

## Contrato con tareas simultáneas

JUP-056/JUP-058 conservan lógica de dashboards y consumen estos tokens y los
componentes compartidos. JUP-089 reutiliza la marca/tipografías, sin otra paleta.
La integración de sus ramas requerirá comprobar las clases solapadas; no se ha
probado código aún no integrado ni se declara coordinación humana realizada.

La evidencia de ejecución y límites vive en [JUP-112-validation.md](evidence/JUP-112-validation.md).
