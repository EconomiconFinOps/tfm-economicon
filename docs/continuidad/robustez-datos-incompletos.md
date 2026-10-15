# Robustez ante datos incompletos — JUP-071

Actualizado el 2026-10-16. [Tarjeta](https://trello.com/c/H0woDubz), ID `69da46a3e4f93822c0236e87`. OpenSpec: `openspec/changes/jup-071-incomplete-data-robustness/`. Evidencia por criterio: [JUP-071-validation.md](../evidence/JUP-071-validation.md). Procedimiento: [JUP-071-robustness.md](../validation/JUP-071-robustness.md).

## Estado actual

- **Dónde está el trabajo.** Rama local `test/JUP-071-incomplete-data-robustness` sobre `develop`, sin publicar y sin PR. Parte de la contribución de Alejandro Aguado (PR #90, cerrado sin integrar el 2026-10-10), recuperada con sus commits y su autoría.
- **Qué hay.** Una batería de 29 casos (16 variantes y 13 referencias de JUP-069), el runner `tools/assistant-robustness.py` sobre el transporte y la comprobación numérica de JUP-070, un informe con los cuatro estados, las tasas y los denominadores, y un bloque `run` pensado para el dashboard de JUP-121. Dos mediciones de la plantilla (recuperación fija y vacía) dan 0 aciertos, 8 fallos numéricos y 21 casos sin juicio entre 29. Una prueba de extremo a extremo con el colector de JUP-123 (PR #131) contra un backend real con modelo simulado lee y exporta operaciones del chat. La rama pasó tres pasadas de revisión adversarial automatizada (`accept` en la tercera), una cuarta (`accept`) y una auditoría de trazabilidad (`changes-required`), cuyos hallazgos se resolvieron o se registraron.
- **Qué no hay.** Ninguna medición con un modelo real, ningún juicio humano, ninguna revisión ni validación de una persona sobre esta contribución. El chat generativo de JUP-035 entrega A (#130) está integrado en `develop` pero desactivado por defecto y se sirve por `/generations`, mientras el colector de esta rama usa `/messages`, que sigue respondiendo con la plantilla. `generative_robustness_accepted` y `model_execution_verified` son falsos en todos los informes.
- **Hueco detectado para medir el chat real.** Las evidencias de corpus del chat de #130 no traen `distance`. La versión actual del colector de JUP-123 bloquea (`blocked`) todas las filas con corpus para el evaluador de JUP-070, y su documentación asigna a JUP-071 adaptar su evaluador para usar `public_evidence`. Sin ese acuerdo entre las dos entregas, una campaña real no podría puntuar las respuestas con citas. Está registrado como tarea 6.6.
- **Cuándo se cierra.** No hasta que existan los juicios, una medición con modelo real (tres campañas iguales) y la revisión y validación humanas. Los ficheros de instrumento y de línea base están listos para revisarse.
- **Roles.** Según la tarjeta el 10/10: Paris lidera, Víctor pairing, Alejandro revisión y Lucía validación y documentación. Es una fotografía de ese día, no se ha vuelto a leer, y Alejandro no puede revisar de forma independiente su propia contribución. Nada de esto atribuye pruebas, pairing ni aceptación a nadie.

## Cronología

- **2026-10-10.** Contribución original publicada como PR #90 (draft) con commit técnico `d98d18d` sobre la base `c2995a11`. Nota en Trello `6ac9ebf65589a5a1741240c1` del 10/10 a las 07:40:38Z. En ese corte `AssistantService.answer` era una plantilla y JUP-035 estaba Preparado; la CI de ese commit tenía `JUP reviews` en FAILURE por falta de dictámenes humanos. El PR se cerró ese mismo día a las 18:02Z sin integrarse.
- **2026-10-13.** Recuperación sobre `develop`. Se añade el bloque `run` del informe y se corrigen los hallazgos de las tres primeras pasadas adversariales (alias de cifras, tasas y categorías en el informe, validación de la batería, rutas de salida, cobertura reducida, metadatos declarados). Primera recogida HTTP contra un servidor real (plantilla, sin modelo).
- **2026-10-14.** JUP-035 se divide: #130 (JUP-122, entrega A) y JUP-123 (entrega B, calidad semántica). Se detecta que el chat generativo no usa `/messages`.
- **2026-10-15.** `develop` integra #130 y otros cambios; la rama se actualiza con un merge y se actualizan las referencias de la batería al banco de JUP-069 `1.0.1`.
- **2026-10-16.** Prueba del colector de JUP-123 con nuestra herramienta; la cabecera `run` acepta su descripción de seis cadenas. Reconciliación de propuesta, spec y diseño, revisión adversarial cuarta y auditoría de trazabilidad.

## Siguiente paso concreto

1. Revisión y validación por las personas de los roles de la tarjeta, o por la excepción temporal vigente si el equipo la aplica.
2. Acordar con quien lidera JUP-123 cómo se puntúan las respuestas con citas del chat real (evidencia sin distancia) y quién genera las respuestas.
3. Con el chat activado con un modelo, un presupuesto de inferencia acordado y los juicios humanos, ejecutar las tres campañas iguales con el colector de JUP-123.
4. No cerrar ni archivar la tarjeta por tener verdes las pruebas del instrumento.
