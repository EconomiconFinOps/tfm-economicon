# Procedencia de assets — JUP-089

Verificado el 10/10/2026. Los assets del proyecto se seleccionan expresamente; no
se copia la carpeta de materiales al artefacto público.

| Archivo público | Fuente original y uso |
| --- | --- |
| `economicon-mark.png` | `materiales/05-marketing/economicon_dossier.pptx`, `ppt/media/image2.png`, diapositiva 5: monograma índigo del equipo. Copiado sin modificar. |
| `dashboard-concept.png` | Mismo dossier, `ppt/media/image6.png`, diapositiva 8. Concepto visual no interactivo; la diapositiva 12 y `INFORME.md` lo declaran simulación. Cifras, previsión, recomendaciones y persona son ilustrativas, sin ahorro real acreditado. Copiado sin modificar y etiquetado en página. |
| `executive-cost-test.png` | `materiales/07-evidencias/JUP-099-validacion-2026-10-01/visual/head-final/executive-cost.png`. Prueba histórica de 01/10, commit `f914d68`, API simulada y usuario/tenant ficticios. No captura de producción ni del frontend actual. Archivo intacto; CSS recorta la miniatura y un enlace abre el original completo. |
| `Inter.woff2` | Inter variable, Latin, servido originalmente por Google Fonts, v20; [proyecto Inter](https://github.com/rsms/inter), licencia `Inter-OFL.txt`. |
| `SpaceGrotesk.woff2` | Space Grotesk variable, Latin, Google Fonts v22; [proyecto Space Grotesk](https://github.com/floriankarsten/space-grotesk), licencia `SpaceGrotesk-OFL.txt`. |

Los paths `materiales/` se refieren al workspace Economicon que contiene este
repositorio. No son enlaces web ni parte del build. La identidad y el dossier se
atribuyen a Lucía según `materiales/05-marketing/INFORME.md`; reutilizarlo no
acredita su revisión de esta landing. Las capturas proceden de la validación
histórica JUP-099, no de una nueva validación funcional del producto.

SHA-256 de los PNG seleccionados:

```text
8c0c1c80a461ada9468262a2ded5302be3f544fa3477245a553fbe647e13f234  dashboard-concept.png
3d642d739a7550827c60f32d281b8ad4d79df0fab9d1a5e683ae0bd96085d93e  economicon-mark.png
d38ca6ba4b4fb572c39ac37e434b25171e27b0cf392ff8b2a44ee336904022c5  executive-cost-test.png
```

Fuentes WOFF2 autoalojadas, sin llamadas de runtime a Google ni transformación
local de sus glifos. Descargadas el 10/10/2026 del CSS oficial para rangos
Inter 100–900 / Space Grotesk 300–700:

- [Inter Latin WOFF2](https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2).
- [Space Grotesk Latin WOFF2](https://fonts.gstatic.com/s/spacegrotesk/v22/V8mDoQDjQSkFtoMM3T6r8E7mPbF4Cw.woff2).
- Licencias originales de [Inter](https://github.com/google/fonts/blob/main/ofl/inter/OFL.txt) y [Space Grotesk](https://github.com/google/fonts/blob/main/ofl/spacegrotesk/OFL.txt).

## Vídeos: fuente revisada parcialmente, publicación pendiente

`materiales/05-marketing/Economicon_anuncio.mp4`, atribuido a Víctor en el informe:
12.452.036 bytes, 1940×1080, duración 13,975465 s; SHA-256
`ed0eca23ed4225ec90ef8f8a1698890c5eca02508b90011b76a2b5ba5a0d8926`.
Cinco fotogramas revisados y reproducción local completa silenciada en Chromium
149: `ended=true`, `error=null`. No prueba reproducción desde hosting. El audio
no se ha auditado, no hay pistas de subtítulos (`textTracks=0`); no se publica el
MP4 en esta entrega. Rotulación prevista: pieza promocional de concepto creada
con IA, no demostración funcional.

El vídeo largo `economicon-finops.mp4` (15.922.277 bytes, 109,632 s) también es
conceptual. Sus afirmaciones de previsión y detección de desperdicio no se
reutilizan como evidencia. El contrato `PUBLIC_VIDEO_URL` permite enlazar una
versión editorialmente aprobada después de verificar audio/subtítulos y destino.
