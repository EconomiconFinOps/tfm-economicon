# Diseño — JUP-069

## Contexto

El corpus del MVP contiene reglas de referencia suficientes para consultas
conceptuales y ejercicios aritméticos. El dataset Azure público no aporta por sí
solo budgets, forecasts, reglas de reparto o ahorro verificado para todos los casos.

## Decisiones

1. Usar un JSON versionado con contextos sintéticos independientes, claramente
   identificados. No modificar el dataset público ni atribuirle importes inventados.
2. Fijar fuentes locales por ruta y SHA-256 del texto con saltos LF. Un cambio
   de corpus exige revisar expectativas e incrementar la versión de la batería.
3. Guardar criterios positivos, negativos y valores numéricos con unidad y
   tolerancia. Evaluar significado y fundamento, no coincidencia literal.
4. Preparar inputs mediante lista explícita de campos permitidos: solo ID,
   contexto y pregunta. No indexar las respuestas de referencia.
5. Ejecutar checks estructurales offline en el job existente de gobernanza.
   Separar esos checks de la futura evaluación manual o automatizada del asistente.

## Riesgos y límites

Los ejemplos autocontenidos prueban razonamiento y reglas, no retrieval de costes
reales ni aislamiento de tenants. Las fuentes son el contrato curado del MVP, no
afirmaciones sobre documentación externa actual. Los hashes detectan deriva del
corpus, pero la corrección semántica de preguntas y rúbricas requiere revisión.
JUP-070 y JUP-071 registrarán respuestas, configuración, resultados y límites del
runtime. No se presume capacidad semántica por obtener éxito con un proveedor mock.

## Validación

Probar la batería completa y mutaciones que eliminan contexto, fuentes, categorías,
rúbricas o integridad numérica; verificar exportación determinista sin respuestas,
aritmética de referencia y ejecución CLI independiente del directorio actual.
