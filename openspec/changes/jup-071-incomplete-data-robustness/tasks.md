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

## 4. Verificación pendiente fuera de la línea base offline

- [ ] 4.1 Incorporar juicios reales de las personas correspondientes y mantener `not_run` donde falten; no atribuirles pruebas unitarias ni opiniones del agente.
- [ ] 4.2 Verificar el runtime generativo integrado de JUP-035 y documentar configuración y evidencia de generación antes de reclamar una medición con modelo real.
- [ ] 4.3 Realizar las tres mediciones finales con idéntica batería/configuración y conservarlas todas, con revisión semántica y limitaciones por ejecución.
- [ ] 4.4 Obtener revisión y validación independientes de la contribución, vincular la evidencia a la tarjeta por la integración autorizada y archivar el cambio sólo cuando corresponda a su cierre real.
