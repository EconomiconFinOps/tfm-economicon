# JUP-123: revisión local de N3

Verificación: 2026-10-14. Origen: chat `01a1270c-e332-7462-9c90-706d49ade92c`.
Candidato medido: `e23e495b24fae76decacf7d030468b75cd52b5f8`.
**Sin aceptación final ni adjudicación independiente. B continúa local.**

Se recogieron las 84 ejecuciones previstas (28 casos × 3), con 78 respuestas y
6 fallos técnicos conservados. No se repitieron fallos para elegir un resultado
favorable. El snapshot original permanece intacto. La revisión local por requisito
está terminada para las 78 respuestas disponibles.

| Conjunto | Conformes | Inciertas | Fallo de contenido | Fallo técnico |
| --- | ---: | ---: | ---: | ---: |
| Calibración, 66 ejecuciones | 58 | 7 | 0 | 1 |
| Reserva, 18 ejecuciones | 10 | 1 | 2 | 5 |
| Total | 68 | 8 | 2 | 6 |

Hay 445 comprobaciones conformes, 13 inciertas y 2 fallidas. Las 35 comprobaciones
sin revisar pertenecen a los seis fallos técnicos sin respuesta pública; no son
requisitos superados. Las etiquetas son del agente local y no sustituyen reviews.

## Hallazgos que impiden el cierre

| Caso y repetición | Resultado y siguiente acción |
| --- | --- |
| 014 r2/r3 | Omite el **20 % de exceso relativo**. Muestra 200 EUR y el forecast al 120 % del presupuesto; ese cociente no expresa la magnitud solicitada. Registrar cobertura numérica de la decisión sin completar la respuesta desde el evaluador. |
| 022 r1/r2/r3 | Diagnóstico `recommendation_documentary_support_required`: las recomendaciones no aportan su propio soporte documental visible. Corregir el contrato privado y medir el candidato corregido. |
| 013 r3, 021 r3 | Diagnóstico `response_basis_authority`. Se conoce la invariante rechazada, no el campo exacto del candidato privado. El esquema permitía citas auxiliares en modos que el renderer las prohíbe; corregido localmente, causalidad de esos intentos aún no demostrada. |
| 003 r1 | Diagnóstico `rendered_text_limit` durante respuesta provisional. No es prueba de caída del proveedor. Falta resolver la cobertura dentro del límite público, conservando paridad stream/final. |
| 004 r1/r2/r3 | Inferencias categóricas sobre actual/amortizado más fuertes que el fragmento breve. Adjudicar alcance de la inferencia; no etiquetar automáticamente como error financiero. |
| 009 r1 | Petición de regla **o** consumo frente a requisito conjunto de regla y base; suficiencia incierta. |
| 010 r2 | Búsqueda parcial no demuestra ausencia de un catálogo completo. Adjudicar afirmación de ausencia. |
| 011 r1/r2 | 10 % por coste correcto; no expresa 90 % como cumplimiento por recursos. r3 sí lo hace. Adjudicar si la distinción implícita basta. |
| 020 r3 | Pasaje de commitments sin aplicación a rightsizing; el mismo chunk sí soporta la recomendación principal. Adjudicar pertinencia por pasaje frente a fragmento. |

Los casos 005, 006, 007, 017, 026, 027 y 028 cumplen los requisitos revisados en
las tres repeticiones. Esto acredita estos escenarios, no generalización a toda
formulación. `insufficient_data` en cálculos hipotéticos corresponde al contrato
de ausencia de autoridad financiera, no a incapacidad de calcular el escenario.
Las repeticiones de limitaciones en 007r3/016r3 son deuda de presentación separada.

## Comparación y límites

Mismo banco, partición, scorer y reglas: 296 comprobaciones `pass→pass`,
48 `fail→pass`, 12 `uncertain→pass`, 9 `pass→uncertain`, 1 `fail→uncertain` y
2 `uncertain→uncertain`. No aparece `pass→fail` confirmado en pares adjudicados.
Eso **no acredita ausencia de regresiones obligatorias**: 003r1 pasa de respuesta
conforme a fallo técnico y siguen las incertidumbres. No sumar requisitos
correlacionados como ensayos independientes ni atribuir causalidad a estos conteos.
004/009 requieren revisar posible diferencia de criterio entre etiquetas históricas
y actuales. Se conservan las etiquetas originales de la baseline.

La reserva se evaluó después de congelar la revisión de calibración, sin modificar
producto o rúbrica entre ambos pasos. Era material históricamente conocido, no un
conjunto ciego. La baseline de reserva no tiene adjudicación: sus transiciones
`unreviewed→pass/fail` no son mejoras o regresiones demostradas. Ajustar producto
con estos hallazgos consume esta reserva para futuras decisiones; una validación
independiente necesita nuevos ejemplos o criterios acordados explícitamente.

## Correcciones posteriores a la medición

Este apartado conserva el corte de `06be1f1a`; los pasos posteriores están en la
[continuidad de B](../continuidad/chat-evaluacion-local.md). El candidato
`c7e2d561` ya añade cobertura determinista de desviación de presupuesto y
deduplicación de citas, con 1470 pruebas únicas Linux/SQL correctas en procesos
separados. Los OOM originales se conservan; no fue una ejecución monolítica
Linux completa. Sus imágenes se han construido y su contenido real se ha verificado
en B. **La campaña real de ese candidato está en marcha**, sin resultado N3 final:
estos resultados no cambian los veredictos de e23. UI001/003/014 comprobada en
escritorio/móvil y tras recarga, sin generar desde navegador.

El esquema privado exige una única selección documental literal como `rationale`
de cada recomendación; la interpretación sigue disponible en `action`. Si no hay
soporte documental seleccionable, no ofrece recomendaciones. Los modos
`user_scenario`/`greeting` ya no ofrecen citas auxiliares incompatibles con su
autoridad. No se relajan los validadores ni cambia el contrato público; no se
presentan estas correcciones como medidas en la campaña e23.

118 pruebas focales del processor y 69 del backend pasan offline. OpenSpec valida
el contrato estricto. La regresión completa del processor terminó, pero su arnés
perdió la salida al decodificar stderr de Windows como UTF-8; no hay resultado
final verificable y no se presenta como PASS. Se repetirá con salida binaria o
JUnit persistente. La medición real del nuevo candidato también queda pendiente. No se ha
transferido, desplegado ni publicado esta modificación local.

## Coste y evidencias

Último corte vivo de la campaña: 2.078111791 USD de cota de cuenta más
1.601760 USD de reservas íntegras = **3.679871791 USD conservadores**, dentro
del máximo autorizado de **5 USD**. No es gasto exacto atribuible al trabajo:
cinco fallos conservan coste desconocido. Esta revisión no generó inferencias.
Antes de cualquier campaña nueva se exige nueva admisión con contadores vivos.

Evidencias fuera del checkout, en
`../materiales/07-evidencias/PR121-local-evaluation/` desde la raíz del proyecto:

- `candidate-cap5-n3-complete/`: snapshot inmutable y manifest de 257 SHA.
- `candidate-cap5-n3-local-judgments-v6.json` y `-local-reviewed-v6.json`.
- `candidate-cap5-n3-paired-local-v6.json`: comparación completa, incluidos pares técnicos.
- `candidate-cap5-calibration-freeze-v1.json`: congelación anterior a la revisión de reserva.
- `candidate-cap5-n3-assessment-v1.json`: tabla de los 28 casos y hashes de evidencias.
- `candidate-cap5-failure-diagnostics-v1.json`: seis códigos estructurados, sin candidatos privados.

Siguen pendientes criterios/adjudicación de revisores, confirmación N5 según
presupuesto y dependencia de A/PR130. Consulta de GitHub a18:28UTC: nuevo head
28ee5b1c retira el tokenizer versionado e incorpora helper de build; CI técnica
SUCCESS, JUP reviews FAILURE y CHANGES_REQUESTED. Eso no acredita la validación
funcional ni la aceptación de A. Falta reconciliar sus bloques nuevos con B.
Ninguna de esas condiciones se da por resuelta por esta revisión local.
