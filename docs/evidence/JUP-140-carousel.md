# JUP-140 — corrección del bucle responsive, 24/10/2026

[Tarjeta](https://trello.com/c/rXLyK4g4) · [Requisito vigente](../../openspec/specs/public-landing/spec.md) · [Continuidad](../continuidad/landing-publica.md).

## Alcance e identidad

Paris autoriza corregir la franja tras la integración de PR160, conservar diseño/contenido y presentar capturas antes de subir. Base y HEAD local: `ffb5d307772f697cffb8b1e73e6330250e093601`; rama `fix/JUP-140-landing-carousel`, cambios sin commit. El HEAD identifica el origen, no los bytes modificados. La corrección permanece local, pendiente de dos evaluaciones independientes y aprobación visual final; no autoriza archivo, Git de escritura, publicación o despliegue. Las excepciones de reviews de entregas anteriores no se trasladan a ésta.

Dos secuencias fijas no cubrían las pantallas grandes durante todo el desplazamiento. Ahora se conserva una secuencia semántica de tres tarjetas y se calculan copias decorativas según anchura, con dos periodos adicionales. Se desplaza exactamente un periodo (ancho del grupo más gap18), a `1014/34 ≈ 29,8235 px/s` independientemente de la pantalla. El cambio de tamaño conserva la fase relativa, incluida la pausa. No se cambian contenido, tamaños de tarjetas, separación, temas, vídeo, URLs, dependencias ni el servidor. El job existente de landing incorpora las siete pruebas del bucle.

La rama reducida cancela la animación, retira copias y distribuye las tres tarjetas mediante flex con salto de línea; también es el estado inicial sin JavaScript y el fallback si faltan las APIs de animación/observación. Las copias activas son `aria-hidden` e `inert`, sin IDs ni controles duplicados.

## Navegador real y evidencia temporal

Preview propia HTTP local, construida desde estas fuentes con el build/servidor nativos, mismo MP4 aprobado (SHA256 `7e9bdfb148cee61acb2e96837f041a5014f3f7048bf2a244a5cb20128f080292`) y destino `https://demo-jupiter.danteinferno.es/`. Las observaciones no visitan ni acreditan acceso a esa aplicación. Se miden rectángulos reales y tiempos de adquisición, sin adelantar ni acelerar animaciones. Las capturas son composiciones completas originales del navegador en ambos temas.

| Viewport solicitado | Muestras estables | Duración observada | Cruces final→inicio | Mayor separación entre tarjetas | Overflow de página |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1920×1080 | 54 | 118,319 s | 3 | 18,0001 px | 0 px |
| 2560×1440 | 49 | 104,373 s | 3 | 18,0001 px | 0 px |
| 3440×1440 | 49 | 104,779 s | 3 | 18,0001 px | 0 px |
| 390×844, repetición estable | 44 | 102,130 s | 3 | 18 px | 0 px |

El periodo es1014px en escritorio y879px en móvil; cada ventana observada supera tres periodos temporales. La velocidad muestreada estable ronda29,60–30,05px/s por discretización de frames/adquisición; el objetivo es29,8235px/s. Los márgenes de entrada/salida nunca exceden el gap nominal18px. La continuidad se sustenta en rectángulos sucesivos, repetición de la secuencia y desplazamiento de un periodo exacto; no se afirma inspección de todos los frames intermedios.

El primer registro móvil contiene una muestra durante la transición inicial del ResizeObserver: contabilizar toda caída de offset como vuelta daba cuatro cruces y una falsa velocidad máxima424,7px/s. Se conserva íntegro como transición, no se usa como evidencia estable, y se repitió sólo el recorrido móvil después del render. Las lecturas inmediatas de resize también conservan su estado anterior al callback; las lecturas tras observar el estado del navegador muestran grupos6/4/3/5/3 y fase≈0,506962 en3440→1920→320→2560→390, con overflow0. No se sobrescriben los primeros resultados.

Pausar mantiene exactamente el offset509,313263px en320 durante la captura; reanudar avanza a515,772888px. El árbol accesible nativo sólo expone las tres perspectivas originales; cada copia tiene aria-hidden/inert y cero controles. Vídeo real observado con readyState4, muted=true, paused=false, tiempo9,199891s. Su código, configuración y enlace, así como el único destino app, permanecen intactos respecto a la base.

[Registro temporal original](assets/jup-140-carousel/temporal-browser-original.json) · [Resumen medido](assets/jup-140-carousel/browser-summary-original.json) · [Resize y pausa, primeras y segundas lecturas](assets/jup-140-carousel/pause-resize-browser-original.json) · [Pausa y reanudación](assets/jup-140-carousel/pause-proof-original.json).

## Capturas completas

| Anchura | Tema claro | Tema oscuro |
| --- | --- | --- |
| 1920 | [composición](assets/jup-140-carousel/1920-light.jpg) | [composición](assets/jup-140-carousel/1920-dark.jpg) |
| 2560 | [composición](assets/jup-140-carousel/2560-light.jpg) | [composición](assets/jup-140-carousel/2560-dark.jpg) |
| 3440 | [composición](assets/jup-140-carousel/3440-light.jpg) | [composición](assets/jup-140-carousel/3440-dark.jpg) |
| 390 | [composición](assets/jup-140-carousel/390-light.jpg) | [composición](assets/jup-140-carousel/390-dark.jpg) |

[Borde320, tema oscuro y movimiento pausado](assets/jup-140-carousel/320-dark-paused.jpg).

## Pruebas y límites

- Landing Linux, Node22 en contenedor propio, red desactivada y fuentes RO:36PASS/0FAIL/0SKIP; incluye build, HTTP/runtime, medio, reproducción, llms y siete pruebas del bucle. La imagen preexistente sólo aporta el ejecutor Node; no es una imagen nueva del producto.
- Contrato CI:19PASS/0FAIL/0SKIP. Primer intento detenido por yaml no disponible en la copia; se usa un enlace ignorado a la dependencia2.9.0 ya declarada/instalada, sin instalación ni cambios en lockfile.
- Policy104PASS y gobernanza15PASS; OpenSpec estricto92PASS; trazabilidad activa, higiene y seis comprobaciones de sintaxis correctas. El build nativo produjo el artefacto cerrado usado por la preview. No se repiten suites globales sin impacto transversal.
- Primer ensayo Windows detenido por `Unsafe fixture cleanup`: TEMP con separadores no nativos discrepaba con el guard de seguridad. Una reproducción mínima con TEMP nativo pasa; los36 casos se ejecutaron después en Linux, sin modificar pruebas ni guardas. Todos los originales de preparación/fallo se conservan fuera del producto.
- **Movimiento reducido interactivo: NOT_TESTED.** La selección de la ventana propia para Rendering de Chrome agotó la aprobación nativa; no se activó emulación ni se cambió Windows. PM ratificó el24/10/2026 a14:42:20 la dispensa humana previa «olvídate de eso, es un TFM». Las pruebas unitarias del delta comprueban preferencia inicial/dinámica, retirada de copias, cancelación, vuelta al movimiento y respeto a pausa; no acreditan una emulación real ni convierten la dispensa en PASS.

Los dictámenes independientes y el retorno de las referencias originales PM deben identificar este candidato fijo y sus límites. Los roles humanos originales (Paris liderazgo, Alejandro pairing, Lucía revisión, Víctor validación) no se presentan como participación realizada. Esta evidencia local no certifica CI remota, reviews humanas, merge, hosting ni despliegue públicos.

Referencias técnicas del diseño: [Element.animate](https://developer.mozilla.org/en-US/docs/Web/API/Element/animate), [Animation.currentTime](https://developer.mozilla.org/en-US/docs/Web/API/Animation/currentTime), [ResizeObserver](https://developer.mozilla.org/en-US/docs/Web/API/ResizeObserver), [inert](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/inert).
