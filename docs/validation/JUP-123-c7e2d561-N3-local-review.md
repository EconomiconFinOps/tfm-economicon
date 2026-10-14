# JUP-123: revisión local N3 de c7e2d561

Verificación: 2026-10-14, cierre a las 20:37 UTC. Origen: chat
`01a1270c-e332-7462-9c90-706d49ade92c`. **B no está aceptada**: persisten
regresiones del banco, incertidumbres y dependencia de A. Juicios locales y
provisionales; no sustituyen revisión o adjudicación independientes.

## Procedencia y resultados

Producto `c7e2d5616d3ba3d4e6fa467f27f272a05595a621`, archivo SHA256
`0b18edaf6f256e4d2880a9322b5874ca079bb670276e0562fa640320a5e270d2`.
Plan SHA256 `280ae38fea4a7122dfb12be768e35bc54e7e34d1253ad4e9cabb1b7aab28fe26`.
Mismo banco, corpus, rúbrica, scorer y partición que e23; producto congelado
durante las tres rondas. OpenRouter/GLM-5.2 con DeepInfra/fp4, sin fallback.

84/84 recibos verificados: **83 operaciones completadas y 1 fallida**.
Controlador 3607245 terminado con `COLLECTED/NOT_ASSESSED`; ningún fallo
relanzado para elegir una respuesta mejor. `completed` no significa conforme.

| Ronda | Conforme | Incierta | Fallo de contenido | Fallo técnico |
| --- | ---: | ---: | ---: | ---: |
| 1 | 22 | 3 | 3 | 0 |
| 2 | 24 | 2 | 2 | 0 |
| 3 | 24 | 2 | 1 | 1 |
| Total | 70 | 7 | 6 | 1 |

495 comprobaciones: 470 conformes, 12 inciertas, 7 fallidas y 6 sin respuesta
por fallo técnico. Las siete fallidas afectan a seis respuestas; dos criterios
de 011r3 describen una misma omisión y se agrupan en una sola causa.

## Hallazgos que impiden aceptación

| Muestra | Hallazgo en la respuesta pública |
| --- | --- |
| 001r2 | Una limitación afirma que no se aportó actual/amortized, pero la entrada dice «coste actual». La aritmética 1000/600/60% es correcta. |
| 009r1 | Selecciona un pasaje sobre minúsculas de tags ajeno al reparto. Que otra parte del mismo chunk sea pertinente no lo corrige. |
| 010r1 | Enumera los cinco tags, owner/equipo y ausencia de PII, pero omite explicar normalización de claves en minúsculas. |
| 011r3 | Describe la fórmula y el 90% por recursos, pero no entrega el resultado 10% de cumplimiento por coste en ningún campo público. |
| 015r1/r2 | Niega apagado y explica alertas, pero omite investigar al superar umbrales. R3 sí lo incluye. Rules6 no llegó al retrieval: no es ausencia global de esa política. |
| 021r3 | Fallo técnico `calculation_free_numeric_equation_forbidden`, etapa `provisional_answer`. El parser sólo procesa answer; se conoce ese campo y la invariante, pero no el segmento ni la ecuación exactos. |

004 queda incierto las tres veces por inferencias sobre actual/amortizado más
categóricas que el fragmento. 011r1 no explicita el 90% por recursos, aunque sí
calcula el 10% por coste. 022 queda incierto las tres veces por modalidad
(«conviene» frente a «exige»), base no confirmada frente a inestabilidad afirmada
y, en r3, plazo plurianual no aportado. No convertir estas dudas en PASS por
citar una fuente ni en fallos definitivos sin adjudicación.

003 completa las tres rondas y 014 entrega 200 EUR/20% las tres veces. 017
distingue 100>100 como falso y 027 obtiene 10→6 EUR/pedido, reducción del 40%,
en 3/3. Citas introductorias solapadas y algunas limitaciones repetidas son
deuda de presentación separada, sin inventar infracciones del banco.

## Comparación emparejada con e23

438 requisitos `pass→pass`, 7 `pass→fail`, 7 `uncertain→uncertain`,
6 `uncertain→pass` y 2 `fail→pass`. Los siete retrocesos afectan a seis
respuestas: 001r2/009r1 son dos criterios de calidad provisional;
010r1/011r3/015r1/r2 suman cinco comprobaciones del banco, dos de 011r3
agrupadas. Se releyeron los originales, sin alterar etiquetas históricas para
ocultar regresiones. No atribuir causalidad ni compensarlas con una media.

003r1 y 013r3 pasan de fallo técnico a conformes; 022 deja de fallar técnicamente
en las tres rondas pero queda incierto. 021r3 sigue técnico con otra invariante.
Las transiciones técnicas se presentan aparte de las semánticas.

## Coste y evidencias

Contadores vivos finales: 2.501327035 USD de cota de cuenta más 1.921712 USD
de reservas retenidas = **4.423039035 USD conservadores de 5 USD autorizados**.
Incluye seis fallos de coste desconocido y la reserva inicial. No es gasto
exacto atribuible al trabajo ni permite gastar sin una nueva admisión.

021r3 conserva 0.319952 USD íntegros: dos fases intentadas y sólo una con usage
completo; consulta upstream 404. Ni 404 ni spend0 en el gateway prueban gratuidad.
Claves exclusivas sin renovar, vencen el 15/10 a las 08:02 UTC. Cada futura
operación necesita contador vivo y reserva completa de su cota.

Evidencia externa bajo `materiales/07-evidencias/PR121-local-evaluation/` del
workspace padre:

- `candidate-c7e2d561-n3-complete-v2/`: 258 SHA verificados; 84 raw, 84 derivados,
  84 pruebas de coste/reserva, ledger consistente, plan y agregado. Manifest SHA256
  `48de0d4b745a8640ae6540243691f1c4f91affd7ba55396f122daded26b65cbd`.
- `candidate-c7e2d561-first56-to-full-row-identity.json`: 56 filas anteriores
  completas idénticas y 168 archivos raw/derivado/coste sin cambios.
- `candidate-c7e2d561-n3-local-{judgments,reviewed}-v1.json`,
  `candidate-c7e2d561-n3-paired-e23-v1.json` y
  `candidate-c7e2d561-n3-assessment-v2.json`: juicios, comparación y tabla por caso.
- `candidate-c7e2d561-021r3-diagnostics-v1.json`: diagnóstico estructurado y
  prueba original de reserva. No contiene el candidato privado.
- `candidate-c7e2d561-regression-original-recheck-v1.json`: contraste adicional
  de los originales 001r2/011r3/015r2 de e23.

Primer intento de congelación incompleto por esperar una prueba de coste ordinaria
para 021r3; conservado como `INCOMPLETE_FREEZE_DO_NOT_SCORE`. El snapshot completo
es **v2**, con prueba de reserva desconocida. Assessment v2 corrige sólo la lista
de criterios no conformes del resumen v1; no altera recibos, etiquetas ni totales.

## Siguiente implementación

1. Diagnóstico de 021 con índice de segmento o agrupación acotado, sin guardar
   contenido privado ni relajar validadores. `SegmentAnswerJSON` sólo procesa
   answer en esa etapa; el código actual no demuestra qué ecuación concreta falló.
2. Separar extracción y cobertura: hechos tipados con procedencia y un conjunto
   cerrado de resultados/reglas aplicables que pueda completar el servidor.
   Priorizar 011, 010/015 y selección de pasajes de 009. No reconocer únicamente
   las preguntas del banco con nuevas expresiones regulares.
3. Conservar atributos aportados y calificadores documentales en respuesta y
   auxiliares: desconocido no equivale a falso ni «conviene» a «exige».
4. Contraejemplos, ámbitos/monedas, fuentes incompletas, streaming/final y
   persistencia antes de transferir o medir otro candidato.
5. Reconciliar correcciones finales de A y obtener criterios/adjudicación.
   N5 y aceptación siguen pendientes; no publicar B.

Las 1470 pruebas Linux/SQL, builds/runtime y lectura de UI001/003/014 conservan
su alcance sobre c7. No validan cambios futuros ni las dos solicitudes nuevas
de A/PR130 (red por slot y UX con chat desactivado).
