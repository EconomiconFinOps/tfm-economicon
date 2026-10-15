## 1. Contrato y batería

- [x] 1.1 Leer las referencias JUP-069/JUP-070, inspeccionar el servicio y contrato HTTP actuales, y documentar el límite generativo de la copia inspeccionada.
- [x] 1.2 Especificar el alcance, diseño y escenarios de `assistant-robustness-evaluation` con trazabilidad JUP-071/Trello.
- [x] 1.3 Añadir al menos 16 variantes incompletas o ambiguas con referencia JUP-069, rúbricas y baselines únicos, y validar IDs, fuentes, referencias y hashes.

## 2. Instrumento reproducible

- [x] 2.1 Implementar preparación del prompt y validación de la batería en `tools/assistant-robustness.py`, reutilizando las funciones pertinentes de JUP-070 sin alterar su banco.
- [x] 2.2 Ejecutar offline el servicio real de plantilla con un doble explícito de recuperación, sin red y con el nivel de evidencia visible.
- [x] 2.3 Implementar recogida HTTP mediante `collect_cases`, una conversación por caso, mensajes fieles y sin reintentos; errores de infraestructura separados de respuestas incorrectas.
- [x] 2.4 Generar hoja de revisión y puntuar comportamiento, requeridos y prohibiciones con juicios humanos; cifras por regla, doble revisión de críticos y modo provisional explícito.
- [x] 2.5 Producir resultados sin texto privado e informes por grupos, comportamientos y baselines/variantes con los cuatro estados, denominadores y límites de la ejecución.

## 3. Pruebas y evidencia

- [x] 3.1 Añadir pruebas de batería inválida y referencias/hashes alterados, baselines únicos y ausencia de claves de respuesta en los prompts.
- [x] 3.2 Añadir controles de ejecución offline/HTTP con dobles declarados, fallo de infraestructura, no reintento y separación de evidencia de modelo real.
- [x] 3.3 Probar juicios ausentes, dos nombres equivalentes, revisión crítica/provisional, desacuerdo, fallo numérico y denominadores sin ocultar `blocked`/`not_run`.
- [x] 3.4 Ejecutar la línea base disponible, registrar versiones, commit, resultados, limitaciones y comandos reales por criterio de tarjeta.
- [x] 3.5 Validar OpenSpec, trazabilidad, pruebas relevantes y limpieza del delta; actualizar metodología y continuidad.

## 4. Preparación para el dashboard de resultados y el colector de JUP-123

- [x] 4.1 Añadir al informe el bloque `run` con los campos de la cabecera de JUP-070 y un identificador único de ejecución, declarando la ausencia de modelo en las ejecuciones con plantilla; conservar los campos actuales y no alterar resultados ni denominadores.
- [x] 4.2 Probar que el bloque es obligatorio y válido, que dos ejecuciones se distinguen y que regenerar el informe con el bloque no cambia ningún resultado. Regenerar los informes de plantilla de `docs/evidence/`.
- [x] 4.3 Aceptar en el bloque `run` la descripción de seis cadenas del colector de JUP-123 (commit declarado de 7 a 40 hexadecimales y `generation` como cadena), con pruebas de lo que sigue rechazándose, y comprobar la cadena completa contra un backend real con el chat activado y modelo simulado.

## 5. Reconciliación y revisión final de la contribución

- [x] 5.1 Reescribir propuesta, spec y diseño para describir el comportamiento del código (alias y rivales, validación estricta, cobertura reducida, categorías, rutas de salida, metadatos declarados, cabecera de ejecución). La revisión de trazabilidad de 5.2 demostró que esa primera reconciliación contenía afirmaciones sin contrastar, que se corrigen en 5.3.
- [x] 5.2 Revisión adversarial automatizada de otra sesión del estado final (pasada 4, `accept` con 3 MEDIUM y 3 LOW) y auditoría independiente de trazabilidad entre spec, código, pruebas y documentación (`changes-required`). Ninguna sustituye a la `Revision JUP-071` de una persona.
- [x] 5.3 Corregir los hallazgos de 5.2 con ciclo RGR y barrido del mismo patrón, y repetir una revisión dirigida sobre lo cambiado: la pasada 5 dio `accept` con 2 MEDIUM y 3 LOW, que se corrigieron o se registraron. Esos arreglos finales no pasaron por otra revisión.
- [x] 5.4 Actualizar `review.md`, la evidencia y la continuidad con el resultado de la revisión final.

## 6. Verificación pendiente fuera de la línea base offline

- [ ] 6.1 Incorporar juicios reales de las personas correspondientes y mantener `not_run` donde falten; no atribuirles pruebas unitarias ni opiniones del agente.
- [ ] 6.2 Verificar el runtime generativo integrado de JUP-035 (entrega A, #130, ya integrada en `develop` con el chat desactivado por defecto; activarlo en local y esperar la aceptación en B) y documentar configuración y evidencia de generación antes de reclamar una medición con modelo real.
- [ ] 6.3 Realizar las tres mediciones finales con idéntica batería/configuración y conservarlas todas, con revisión semántica y limitaciones por ejecución.
- [ ] 6.4 Obtener revisión y validación independientes de la contribución, vincular la evidencia a la tarjeta por la integración autorizada y archivar el cambio sólo cuando corresponda a su cierre real.
- [ ] 6.5 Disponer de quien genere las respuestas del chat generativo y consuma el colector de JUP-123 (`/generations`) y acordar con quien lidera B el reparto del presupuesto de inferencia antes de cualquier campaña con modelo.
- [ ] 6.6 Acordar con quien lidera JUP-123 cómo se puntúan las respuestas del chat real cuya evidencia de corpus no trae distancia: su colector bloquea hoy esas filas para el evaluador de JUP-070 y su documentación asigna a este change adaptar el evaluador para consumir `public_evidence` sin inventar distancias. Hasta resolverlo, ninguna campaña real podrá puntuar respuestas con citas.
