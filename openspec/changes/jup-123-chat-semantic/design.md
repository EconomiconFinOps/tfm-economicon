JUP: JUP-123

## Context

B preserva el flujo que ya recupera documentación en servidor y genera draft/final
sin herramientas nativas. Retirar tools no es una nueva solución pendiente.
El scorer previo conserva 253 juicios históricos y nueve incertidumbres.

## Decisions

1. Reconciliar A por bloques usando la base Paris f63c150 para adiciones paralelas;
   mantener semántica B y controles de activación, cancelación y fecha de A.
2. N=3 inicial, N=5 de confirmación según criterios obligatorios y presupuesto.
   Sin selección del mejor intento ni omisión silenciosa de fallos técnicos.
3. Identidad por campaña, caso y repetición; banco y corpus inmutables. Conservar
   commit, hashes, entradas, fragmentos realmente usados, parámetros y costes.
4. Contabilidad viva y reserva conservadora antes de inferencias. Tope acumulado
   de 2 USD, incluyendo intentos fallidos y servicios auxiliares facturables.
5. Las coincidencias de palabras/números son diagnósticos, no veredictos semánticos.
   Citas requieren soporte de la afirmación, no sólo solapamiento léxico.
6. Las correcciones se evalúan contra la misma rúbrica congelada. Ninguna media
   compensa una regresión obligatoria; umbrales aún pendientes de revisores.

## Risks and open questions

El entorno compartido anterior no demuestra procedencia del candidato nuevo.
Falta colector actual, medición real y acuerdo de criterios. No afirmar cierre
por superar pruebas unitarias o por completar un plan NOT_RUN.
